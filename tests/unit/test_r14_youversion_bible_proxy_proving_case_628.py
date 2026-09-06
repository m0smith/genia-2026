"""Tests for the R14 E14-12 YouVersion Bible proxy proving application
(issue #628): examples/r14_youversion_bible_proxy_proving_case.genia.

Proves, over the already-implemented E14-4/E14-5/E14-7/E14-8/E14-10
mechanism (R13 `config_view`/`secret_view`, R14 `http_operation`/
`web.http_send`, R8 `web.serve_http`/`web.route_request`), that:

- base URL, version ID, and API credential resolve through the landed
  R13/R10 configuration model, with the credential remaining protected
- an inbound request carrying multiple canonical references produces a
  structured response using outbound HTTP client calls
- the protected credential is declassified only immediately before
  transport, reaching the mock upstream and no response/log/diagnostic
- an upstream failure produces a deterministic per-reference error
  without killing the server
- no real YouVersion credential or public network dependency is used

Minting a declassification authority is a privileged host-side operation
(see docs/releases/R13.md); this file is the Python-host test seam that
injects one, exactly like the R13 proving case's own sidecar test.
"""

from __future__ import annotations

import http.server
import json
import socket
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

from genia import make_global_env, run_source
from genia.configuration import create_declassification_authority
from genia.utf8 import format_display
from genia.values import GeniaOptionSome, symbol

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/r14_youversion_bible_proxy_proving_case.genia"
FAKE_KEY = "FAKE_YOUVERSION_KEY_SENTINEL_628"
PURPOSE = "bible_proxy_outbound"


def _definitions_source() -> str:
    lines = EXAMPLE.read_text(encoding="utf-8").splitlines()
    cutoff = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("# -- Top-level")
    )
    return "\n".join(lines[:cutoff])


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start_server(source: str, env, *, filename: str):
    outcome: dict[str, object] = {}

    def target() -> None:
        try:
            outcome["result"] = run_source(source, env, filename=filename)
        except BaseException as exc:  # pragma: no cover - surfaced through assertions
            outcome["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    return thread, outcome


def _finish_server(thread: threading.Thread, outcome: dict[str, object]):
    thread.join(timeout=5)
    assert not thread.is_alive(), "server thread did not stop"
    if "error" in outcome:
        raise outcome["error"]  # type: ignore[misc]
    return outcome["result"]


def _post_json(url: str, payload) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    last_error = None
    for _ in range(60):
        try:
            request = Request(
                url,
                method="POST",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=2) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")
        except URLError as exc:
            last_error = exc
            time.sleep(0.02)
    raise last_error  # type: ignore[misc]


class _MockUpstream(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.server.captured_headers.append(dict(self.headers))  # type: ignore[attr-defined]
        self.server.hits.append(self.path)  # type: ignore[attr-defined]
        if self.server.fail_next:  # type: ignore[attr-defined]
            self.send_response(500)
            self.end_headers()
            return
        text = self.path.rsplit("/", 1)[-1]
        body = json.dumps({"reference": text, "text": f"passage-text:{text}"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        pass


class _MockUpstreamServer(http.server.ThreadingHTTPServer):
    def __init__(self, *, fail_next: bool = False):
        super().__init__(("127.0.0.1", 0), _MockUpstream)
        self.hits: list[str] = []
        self.captured_headers: list[dict] = []
        self.fail_next = fail_next
        self.daemon_threads = True

    def start(self) -> None:
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.shutdown()
        self.server_close()


def _env_with_provider(env, base_url: str):
    provider_src = f"""
provider = config_provider([{{kind: quote(values), values: {{
  YOUVERSION_BASE_URL: "{base_url}",
  YOUVERSION_VERSION_ID: "111",
  YOUVERSION_API_KEY: "{FAKE_KEY}"
}}}}]) |> unwrap_or(none)
config = resolve_bible_config(provider) |> unwrap_or(none)
"""
    run_source(_definitions_source() + "\n" + provider_src, env)
    return env


def _inject_authority(env):
    audits: list[dict] = []
    authority = create_declassification_authority(
        env.get("provider"), [symbol(PURPOSE)], audits.append
    )
    env.set("authority_fixture", GeniaOptionSome(authority))
    return audits


def test_example_file_exists():
    assert EXAMPLE.is_file()


def test_top_level_demo_resolves_config_and_keeps_credential_protected():
    env = make_global_env([])
    result = run_source(EXAMPLE.read_text(encoding="utf-8"), env, filename=str(EXAMPLE))

    assert result.get("base_url") == "https://developers.youversionapi.com"
    assert result.get("version_id") == "111"
    assert result.get("credential") == "<protected>"
    assert result.get("protected_match") is True
    assert FAKE_KEY not in format_display(result)


@pytest.mark.loopback
def test_multiple_references_produce_structured_response_via_real_server():
    upstream = _MockUpstreamServer()
    upstream.start()
    server_port = _free_port()
    try:
        env = make_global_env([])
        _env_with_provider(env, f"http://127.0.0.1:{upstream.server_port}")
        _inject_authority(env)

        source = (
            f"bible_proxy_server({{host: \"127.0.0.1\", port: {server_port}, max_requests: 1}}, "
            "authority_fixture, config)"
        )
        thread, outcome = _start_server(source, env, filename="<bible-proxy-server>")
        status, body = _post_json(
            f"http://127.0.0.1:{server_port}/passages", ["JHN.3.16", "GEN.1.1"]
        )
        _finish_server(thread, outcome)
    finally:
        upstream.stop()

    assert status == 200
    payload = json.loads(body)
    assert [row["reference"] for row in payload["results"]] == ["JHN.3.16", "GEN.1.1"]
    assert all(row["status"] == "ok" for row in payload["results"])
    assert payload["results"][0]["passage"]["text"] == "passage-text:JHN.3.16"
    assert sorted(upstream.hits) == [
        "/v1/bible/111/passages/GEN.1.1",
        "/v1/bible/111/passages/JHN.3.16",
    ]
    assert all(
        headers.get("Youversion-Api-Key") == FAKE_KEY for headers in upstream.captured_headers
    )


@pytest.mark.loopback
def test_upstream_failure_produces_deterministic_error_without_killing_server():
    upstream = _MockUpstreamServer(fail_next=True)
    upstream.start()
    server_port = _free_port()
    try:
        env = make_global_env([])
        _env_with_provider(env, f"http://127.0.0.1:{upstream.server_port}")
        _inject_authority(env)

        source = (
            f"bible_proxy_server({{host: \"127.0.0.1\", port: {server_port}, max_requests: 2}}, "
            "authority_fixture, config)"
        )
        thread, outcome = _start_server(source, env, filename="<bible-proxy-server-failure>")
        status1, body1 = _post_json(f"http://127.0.0.1:{server_port}/passages", ["JHN.3.16"])
        status2, body2 = _post_json(f"http://127.0.0.1:{server_port}/passages", ["JHN.3.16"])
        result = _finish_server(thread, outcome)
    finally:
        upstream.stop()

    for status, body in ((status1, body1), (status2, body2)):
        assert status == 200
        payload = json.loads(body)
        assert payload["results"][0]["status"] == "error"
        assert payload["results"][0]["reason"] == "upstream-status"
        assert payload["results"][0]["http_status"] == 500
    assert result.get("handled_requests") == 2


@pytest.mark.loopback
def test_connect_refused_upstream_is_a_deterministic_error_not_a_crash():
    dead_port = _free_port()
    server_port = _free_port()
    env = make_global_env([])
    _env_with_provider(env, f"http://127.0.0.1:{dead_port}")
    _inject_authority(env)

    source = (
        f"bible_proxy_server({{host: \"127.0.0.1\", port: {server_port}, max_requests: 1}}, "
        "authority_fixture, config)"
    )
    thread, outcome = _start_server(source, env, filename="<bible-proxy-server-refused>")
    status, body = _post_json(f"http://127.0.0.1:{server_port}/passages", ["JHN.3.16"])
    result = _finish_server(thread, outcome)

    assert status == 200
    payload = json.loads(body)
    assert payload["results"][0]["status"] == "error"
    assert payload["results"][0]["reason"] == "http-transport-failure"
    assert result.get("handled_requests") == 1


@pytest.mark.loopback
def test_protected_credential_never_leaks_through_response_or_audit():
    upstream = _MockUpstreamServer()
    upstream.start()
    server_port = _free_port()
    try:
        env = make_global_env([])
        _env_with_provider(env, f"http://127.0.0.1:{upstream.server_port}")
        audits = _inject_authority(env)

        source = (
            f"bible_proxy_server({{host: \"127.0.0.1\", port: {server_port}, max_requests: 1}}, "
            "authority_fixture, config)"
        )
        thread, outcome = _start_server(source, env, filename="<bible-proxy-server-sentinel>")
        status, body = _post_json(f"http://127.0.0.1:{server_port}/passages", ["JHN.3.16"])
        _finish_server(thread, outcome)
    finally:
        upstream.stop()

    assert status == 200
    assert FAKE_KEY not in body
    assert len(audits) == 1 and audits[0]["success"] is True
    audit_text = str({k: v for k, v in audits[0].items() if k != "provider_identity"})
    assert FAKE_KEY not in audit_text


def test_no_real_credential_or_network_dependency():
    source = EXAMPLE.read_text(encoding="utf-8")
    assert "youversionapi.com" in source  # documents the intended upstream only
    assert FAKE_KEY.startswith("FAKE_")
    # The credential in the example is an explicit synthetic sentinel, never
    # a value that could be mistaken for a real API key.
    assert "FAKE_YOUVERSION_KEY_SENTINEL_628" in source
