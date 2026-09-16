import json
from pathlib import Path

from genia import make_global_env, run_source
from genia.http_transport import HttpTransportResponse
from genia.values import GeniaOptionErr, GeniaOptionSome


EXAMPLE = Path("examples/ollama_chat.genia")


def _run(expression: str):
    source = EXAMPLE.read_text(encoding="utf-8")
    return run_source(
        source + f"\n{expression}",
        make_global_env([]),
        filename=str(EXAMPLE.resolve()),
    )


def test_ollama_chat_sends_non_streaming_conversation(monkeypatch):
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


def test_ollama_chat_normalizes_non_success_status(monkeypatch):
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
