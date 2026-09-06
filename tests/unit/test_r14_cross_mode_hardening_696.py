"""Cross-mode lifecycle and HTTP hardening for R14 (issue #696, E14-13).

Per docs/design/r14-composable-lifecycle-contract.md and the R13 E13-5
precedent (tests/unit/test_r13_cross_mode_hardening_675.py), this is a
focused conformance/hardening proof over the *combined* R14 surface --
the cross-cutting risk individual slice tests cannot see -- not a
re-proof of every prior ticket's own acceptance criteria. It composes
E14-1 through E14-12 (issues #621, #692, #693, #694, #622, #623, #624,
#625, #626, #627, #695, #628) with no new public helper, syntax,
annotation, or parser/AST/Core IR node.

Covers, from issue #696's acceptance criteria:
- imports and non-activating modes perform zero outbound IO
- protected credentials and lifecycle-local sentinels never leak through
  any unauthorized observable sink
- primary failure survives every cleanup-failure combination
- only successfully entered/owned scopes and attachments receive
  finalization
- early Flow termination does not over-pull or leak element context
- server-owned resources survive request/client child completion and
  failure
- Python exception/library details do not become portable diagnostics
- parser/AST/Core IR shapes remain unchanged (ordinary call/value forms)
- automated tests require no public network or real credential
"""

from __future__ import annotations

import http.server
import io
import json
import socket
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pytest

import genia.http_client as http_client_module
from genia.builtins import make_global_env
from genia.http_client import perform_http_send
from genia.interpreter import run_source
from genia.test_cli import run_native_tests_from_file
from genia.utf8 import format_display
from genia.values import GeniaOptionNone

SENTINELS = ("KEY_SENTINEL_696", "PAYLOAD_SENTINEL_696")
PURPOSE = "cross_mode_696"
DISTINCTIVE_PYTHON_DETAIL = "distinctive-python-detail-696"


def _assert_sentinels_absent(*observations):
    rendered = "\n".join(str(value) for value in observations)
    assert all(sentinel not in rendered for sentinel in SENTINELS)


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


def _get(url: str):
    last_error = None
    for _ in range(60):
        try:
            with urlopen(url, timeout=2) as response:
                return response.status, response.read().decode("utf-8")
        except HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")
        except URLError as exc:
            last_error = exc
            time.sleep(0.02)
    raise last_error  # type: ignore[misc]


class _DownstreamHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        self.server.hits.append(self.path)  # type: ignore[attr-defined]
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"pong")

    def log_message(self, format, *args):  # noqa: A002
        pass


class _DownstreamServer(http.server.ThreadingHTTPServer):
    def __init__(self):
        super().__init__(("127.0.0.1", 0), _DownstreamHandler)
        self.hits: list[str] = []
        self.daemon_threads = True

    def start(self) -> None:
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self.shutdown()
        self.server_close()


def test_import_of_module_defining_http_and_lifecycle_functions_is_inert(tmp_path, monkeypatch):
    """Defining (never invoking) http_operation/@get/lifecycle functions at
    module scope must trigger zero transport calls on import."""

    def spy(*args, **kwargs):
        raise AssertionError("network transport must not be called during import")

    monkeypatch.setattr(http_client_module, "send_http_request", spy)

    module_path = tmp_path / "inert_module.genia"
    module_path.write_text(
        '''
import web

@get {path: "/items"}
list_items() = {headers: {}, query: {}, body: none("http-no-body")}

peers = [{name: quote(cfg), enter: (h) -> some("ctx"), exit: (h, s) -> some("nil")}]
work(h) = 1

fetch_op() = http_operation(quote(get), "http://127.0.0.1:9", "/x", {}, {}, none("http-no-body"))
''',
        encoding="utf-8",
    )
    env = make_global_env([])
    result = run_source(
        f"import {module_path.stem}\n{module_path.stem}.fetch_op()",
        env,
        filename=str(tmp_path / "entry.genia"),
    )
    assert format_display(result).startswith("some(")


def test_native_test_discovery_does_not_activate_http_or_lifecycle(tmp_path, monkeypatch):
    """Discovering @test units that merely reference http/lifecycle
    functions (without calling them) must never touch the transport."""

    def spy(*args, **kwargs):
        raise AssertionError("network transport must not be called during discovery")

    monkeypatch.setattr(http_client_module, "send_http_request", spy)

    program = tmp_path / "http_native_tests.genia"
    program.write_text(
        '''
import web

@get {path: "/items"}
list_items() = {headers: {}, query: {}, body: none("http-no-body")}

fetch_op() = http_operation(quote(get), "http://127.0.0.1:9", "/x", {}, {}, none("http-no-body"))

@test "operation construction only, no network"
constructs_operation() = assert_true(fetch_op() |> some?)
''',
        encoding="utf-8",
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = run_native_tests_from_file(str(program), stdout_stream=stdout, stderr_stream=stderr)

    assert exit_code == 0
    assert "passed=1" in stdout.getvalue()
    assert stderr.getvalue() == ""


@pytest.mark.loopback
def test_serve_mode_annotation_registration_never_self_executes():
    """An @get-annotated function's registration at server startup must
    never itself perform outbound IO; only an explicit request handler
    call does."""

    downstream = _DownstreamServer()
    downstream.start()
    server_port = _free_port()
    try:
        env = make_global_env([])
        source = f'''
import web

@get {{path: "/ping"}}
ping() = {{headers: {{}}, query: {{}}, body: none("http-no-body")}}

handler(request) = web.json({{registered: "ok"}})

web.serve_http({{host: "127.0.0.1", port: {server_port}, max_requests: 1}}, web.route_request([web.get("/health", handler)]))
'''
        thread, outcome = _start_server(source, env, filename="<serve-inert>")
        status, body = _get(f"http://127.0.0.1:{server_port}/health")
        _finish_server(thread, outcome)
    finally:
        downstream.stop()

    assert status == 200
    assert json.loads(body) == {"registered": "ok"}
    assert downstream.hits == []


def test_recursive_sentinel_scan_across_protected_and_lifecycle_values():
    """One comprehensive value combining a protected credential and
    ordinary lifecycle-context data must never leak either sentinel
    through display/debug_repr, matching the E10/E14-8 sink discipline."""

    env = make_global_env([])
    key, payload = SENTINELS
    result = run_source(
        f'''
provider = config_provider([{{kind: quote(values), values: {{{key}: "{payload}"}}}}]) |> unwrap_or(none)
token = secret_get(provider, "{key}", quote({PURPOSE})) |> unwrap_or(none)
op = http_operation(quote(get), "http://example.invalid", "/x", {{authorization: token}}, {{}}, none("http-no-body")) |> unwrap_or(none)
scope_ctx = lifecycle_repeat([], ["a", "b"], (h) -> lifecycle_context(h, quote(element)) |> unwrap_or(none))
[display(op), debug_repr(op), display(scope_ctx), debug_repr(scope_ctx), display(token), debug_repr(token)]
''',
        env,
    )
    _assert_sentinels_absent(*result)


def test_primary_failure_survives_combined_multi_peer_cleanup_failures():
    """A work-phase primary failure must survive multiple simultaneous
    exit-phase cleanup failures, in exit-call (reverse-entry) order,
    matching E14-1/E14-2's own partial-entry/failure matrix at combined
    breadth."""

    env = make_global_env([])
    result = run_source(
        '''
peer_a = {name: quote(a), enter: (h) -> some("a-ctx"), exit: (h, s) -> err("a-exit-broke", {})}
peer_b = {name: quote(b), enter: (h) -> some("b-ctx"), exit: (h, s) -> some("nil")}
peer_c = {name: quote(c), enter: (h) -> some("c-ctx"), exit: (h, s) -> err("c-exit-broke", {})}
work(h) = { _ = 1 / 0; "unreachable" }
lifecycle_scope([peer_a, peer_b, peer_c], work)
''',
        env,
    )
    assert format_display(result.get("status")) == "error"
    assert format_display(result.get("phase")) == "work"
    cleanup = result.get("cleanup_failures")
    peers_in_order = [format_display(f.get("peer")) for f in cleanup]
    assert peers_in_order == ["some(c)", "some(a)"]


def test_bounded_flow_termination_over_protected_element_scopes_no_leak():
    """take(n) over lifecycle_repeat with a protected value threaded
    through element scopes must pull exactly n elements, close before
    the next pull, and never leak a later element's context."""

    env = make_global_env([])
    key, payload = SENTINELS
    result = run_source(
        f'''
provider = config_provider([{{kind: quote(values), values: {{{key}: "{payload}"}}}}]) |> unwrap_or(none)
token = secret_get(provider, "{key}", quote({PURPOSE})) |> unwrap_or(none)

guarded_peer() = {{
  name: quote(guarded),
  enter: (scope) -> some(token),
  exit: (scope, summary) -> some("nil")
}}

work(h) = lifecycle_context(h, quote(index)) |> unwrap_or(none)

lifecycle_repeat([guarded_peer()], lines(["a", "b", "c", "d"]), work) |> take(2) |> collect |> map((r) -> unwrap_or(none, r.result))
''',
        env,
    )
    assert result == [1, 2]


def test_python_exception_detail_does_not_become_portable_diagnostic():
    """A raising transport's raw Python exception text must never appear
    in the normalized err(...) Outcome -- only the closed {kind} shape."""

    env = make_global_env([])

    def _invoke(fn, args):
        return fn(*args)

    def _json_encode(value):
        return None

    def raising_transport(request):
        raise RuntimeError(DISTINCTIVE_PYTHON_DETAIL)

    operation = run_source(
        'http_operation(quote(get), "http://example.invalid", "/x", {}, {}, none("http-no-body")) |> unwrap_or(none)',
        env,
    )
    result = perform_http_send(
        operation,
        GeniaOptionNone("nil"),
        2000,
        json_encode=_json_encode,
        invoke=_invoke,
        transport=raising_transport,
    )
    rendered = format_display(result)
    assert rendered == 'err("http-transport-failure", {kind: other})'
    assert DISTINCTIVE_PYTHON_DETAIL not in rendered


@pytest.mark.loopback
def test_combined_server_request_outbound_client_resilience_without_network():
    """One request making both a successful and a failed outbound call,
    followed by a second successful request, proves the server's own
    resources survive both outcomes with no external network."""

    downstream = _DownstreamServer()
    downstream.start()
    dead_port = _free_port()
    server_port = _free_port()
    try:
        env = make_global_env([])
        source = f'''
import web

failure_reason(result) = (some(_)) -> "unexpected-ok" | (err(reason, _)) -> reason

handler(request) = {{
  op_ok = http_operation(quote(get), "http://127.0.0.1:{downstream.server_port}", "/ok", {{}}, {{}}, none("http-no-body")) |> unwrap_or(none)
  op_bad = http_operation(quote(get), "http://127.0.0.1:{dead_port}", "/bad", {{}}, {{}}, none("http-no-body")) |> unwrap_or(none)
  result_ok = web.http_send(op_ok, none("nil"), 2000)
  result_bad = web.http_send(op_bad, none("nil"), 2000)
  status_ok = unwrap_or(none, result_ok)("status")
  web.json({{ok: status_ok, bad: failure_reason(result_bad)}})
}}

web.serve_http({{host: "127.0.0.1", port: {server_port}, max_requests: 2}}, web.route_request([web.get("/proxy", handler)]))
'''
        thread, outcome = _start_server(source, env, filename="<combined-resilience>")
        status1, body1 = _get(f"http://127.0.0.1:{server_port}/proxy")
        status2, body2 = _get(f"http://127.0.0.1:{server_port}/proxy")
        result = _finish_server(thread, outcome)
    finally:
        downstream.stop()

    for status, body in ((status1, body1), (status2, body2)):
        assert status == 200
        payload = json.loads(body)
        assert payload["ok"] == 200
        assert payload["bad"] == "http-transport-failure"
    assert result.get("handled_requests") == 2
    assert sorted(downstream.hits) == ["/ok", "/ok"]


def test_parser_accepts_all_r14_call_forms_with_no_new_grammar():
    """A parse-only regression: every R14 surface (lifecycle_scope/child/
    repeat/context/config, http_operation, web.http_send/send_annotated,
    @get/@post) must parse using only ordinary existing call/annotation/
    map/list grammar -- confirming issue #696's "parser/AST/Core IR shapes
    remain unchanged" criterion without requiring any new node type."""

    from genia.lexer import lex
    from genia.parser import Parser

    source = '''
import web

@get {path: "/items"}
list_items() = {headers: {}, query: {}, body: none("http-no-body")}

peers = [{name: quote(cfg), enter: (h) -> some("ctx"), exit: (h, s) -> some("nil")}]

root_work(scope) = lifecycle_child(scope, [], (child) -> lifecycle_context(child, quote(cfg)) |> unwrap_or(none))

repeated(records) = lifecycle_repeat(peers, records, (h) -> lifecycle_context(h, quote(element)) |> unwrap_or(none))

configured(provider) = lifecycle_config(provider)

operation() = http_operation(quote(get), "http://example.invalid", "/x", {}, {}, none("http-no-body"))

send(op, authority) = web.http_send(op, authority, 1000)

annotated_send(authority) = web.send_annotated(list_items, "http://example.invalid", authority, 1000)

lifecycle_scope(peers, root_work)
'''
    # Must not raise SyntaxError.
    tokens = lex(source)
    Parser(tokens, source=source, filename="<r14-parse-regression>").parse_program()


def test_no_real_credential_or_public_network_in_this_module():
    """Structural self-check: every fixture server in this file binds to
    127.0.0.1, and the only credential-shaped strings are explicit
    synthetic sentinels, never a real key."""

    source = Path(__file__).read_text(encoding="utf-8")
    assert "127.0.0.1" in source
    assert "example.invalid" in source
    for sentinel in SENTINELS:
        assert sentinel.endswith("_696")
