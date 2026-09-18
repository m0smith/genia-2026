import json
from pathlib import Path

from genia import make_global_env, run_source
from genia.configuration import (
    construct_provider,
    create_declassification_authority,
    get_secret_configuration,
)
from genia.http_transport import HttpTransportResponse
from genia.test_cli import discover_test_units, make_test_env
from genia.test_kernel import run_test_suite
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone, GeniaOptionSome, symbol


EXAMPLE = Path("examples/ollama_chat.genia")
NATIVE_TESTS = Path("tests/native/ollama_chat_example.genia")


def _run(expression: str):
    source = EXAMPLE.read_text(encoding="utf-8")
    return run_source(
        source + f"\n{expression}",
        make_global_env([]),
        filename=str(EXAMPLE.resolve()),
    )


def test_ollama_chat_native_behavior_tests_pass():
    env, _ = make_test_env()
    run_source(EXAMPLE.read_text(encoding="utf-8"), env, filename=str(EXAMPLE.resolve()))
    run_source(
        NATIVE_TESTS.read_text(encoding="utf-8"),
        env,
        filename=str(NATIVE_TESTS.resolve()),
    )

    suite = run_test_suite(discover_test_units(env))
    problems = [
        (result.get("name"), result.get("kind"), result.get("reason"))
        for result in suite.get("results")
        if result.get("kind") != "pass"
    ]

    assert suite.get("total") == 8
    assert suite.get("passed") == 8, problems
    assert suite.get("failed") == 0
    assert suite.get("errored") == 0


def test_ollama_chat_crosses_host_boundary_once(monkeypatch):
    captured = []

    def fake_send(request, transport=None):
        captured.append(request)
        return HttpTransportResponse(
            200,
            {"content-type": "application/json"},
            b'{"message":{"role":"assistant","content":"Hello from Ollama"}}',
        )

    monkeypatch.setattr("genia.http_client.send_http_request", fake_send)

    outcome = _run(
        'ollama_chat("http://127.0.0.1:11434", "llama3.2", '
        '[{role: "user", content: "Hello"}])'
    )

    assert isinstance(outcome, GeniaOptionSome)
    assert outcome.value == "Hello from Ollama"
    assert len(captured) == 1
    assert captured[0].method == "POST"
    assert captured[0].url == "http://127.0.0.1:11434/api/chat"
    assert json.loads(captured[0].body) == {
        "model": "llama3.2",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False,
    }


def test_direct_ollama_main_does_not_propagate_no_authority_marker(capsys, monkeypatch):
    prompts = iter(["smile", "/quit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(prompts))
    monkeypatch.setattr(
        "genia.http_client.send_http_request",
        lambda request, transport=None: HttpTransportResponse(
            200,
            {"content-type": "application/json"},
            b'{"message":{"role":"assistant","content":"Happy!"}}',
        ),
    )
    env = make_global_env([])
    result = run_source(
        EXAMPLE.read_text(encoding="utf-8")
        + '\napply_raw(main, [["--model", "llama3.2:3b"]])',
        env,
        filename=str(EXAMPLE.resolve()),
    )

    captured = capsys.readouterr()
    assert isinstance(result, GeniaOptionNone)
    assert result.reason == "nil"
    assert "Chat using ollama/llama3.2:3b; enter /quit to stop." in captured.out
    assert "assistant> Happy!" in captured.out
    assert "config-missing" not in captured.out
    assert 'none("ollama-needs-no-authority")' not in captured.out


def test_ollama_chat_preserves_http_status_error_as_outcome(monkeypatch):
    monkeypatch.setattr(
        "genia.http_client.send_http_request",
        lambda request, transport=None: HttpTransportResponse(404, {}, b"not found"),
    )

    outcome = _run(
        'ollama_chat("http://127.0.0.1:11434", "missing", '
        '[{role: "user", content: "Hello"}])'
    )

    assert isinstance(outcome, GeniaOptionErr)
    assert outcome.reason == "ollama-http-status"
    assert outcome.context.get("status") == 404


def test_groq_chat_declassifies_only_at_authorized_host_boundary(monkeypatch):
    captured = []

    def fake_send(request, transport=None):
        captured.append(request)
        return HttpTransportResponse(
            200,
            {"content-type": "application/json"},
            b'{"choices":[{"message":{"role":"assistant","content":"Hello from Groq"}}]}',
        )

    values = GeniaMap().put("GROQ_AUTHORIZATION", "Bearer test-secret")
    descriptor = GeniaMap().put("kind", symbol("values")).put("values", values)
    provider_result = construct_provider([descriptor], None)
    assert isinstance(provider_result, GeniaOptionSome)
    provider = provider_result.value
    authorization = get_secret_configuration(
        provider, "GROQ_AUTHORIZATION", symbol("chat_outbound")
    )
    authority = create_declassification_authority(
        provider, [symbol("chat_outbound")], lambda event: None
    )
    env = make_global_env([])
    env.set("groq_authorization_fixture", authorization)
    env.set("groq_authority_fixture", GeniaOptionSome(authority))
    monkeypatch.setattr("genia.http_client.send_http_request", fake_send)

    source = EXAMPLE.read_text(encoding="utf-8")
    outcome = run_source(
        source
        + '\napply_raw(chat, [{backend: "groq", base_url: "https://api.groq.com", '
        + 'model: "llama-3.1-8b-instant", authorization: groq_authorization_fixture, '
        + 'authority: groq_authority_fixture}, '
        + '[{role: "user", content: "Say hello"}]])',
        env,
        filename=str(EXAMPLE.resolve()),
    )

    assert isinstance(outcome, GeniaOptionSome)
    assert outcome.value == "Hello from Groq"
    assert len(captured) == 1
    assert captured[0].url == "https://api.groq.com/openai/v1/chat/completions"
    assert captured[0].headers["authorization"] == "Bearer test-secret"
