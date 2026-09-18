import json
from pathlib import Path

from genia import make_global_env, run_source
from genia.http_transport import HttpTransportResponse
from genia.test_cli import discover_test_units, make_test_env
from genia.test_kernel import run_test_suite
from genia.values import GeniaOptionSome


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

    assert suite.get("total") == 4
    assert suite.get("passed") == 4
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
