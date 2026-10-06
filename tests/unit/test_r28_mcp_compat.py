"""R28 E28-6 amendment A5 (issue #707): the MCP 2025-11-25 compatibility era.

Pinned to docs/design/r28-genia-mcp-contract-threat-model.md section 18 (A5) and
docs/design/r28-e28-6-protocol-compat-preflight.md. VS Code 1.138.0 sends `initialize` for protocol
2025-11-25 (evidence run 1); these tests start from that authentic message and prove the amended
protocol: the handshake, the one-bit state and its deterministic ordering errors, the closed version
policy, ping, the era wire shapes, that both eras serve the same three tools, and that client
capabilities (roots, sampling, elicitation, tasks, extensions) grant nothing. Protocol-transport tests of
the Python-host MCP server; they add no Genia semantics. Expected red against the pre-amendment server.
"""

from __future__ import annotations

import json
import re

import pytest

from tests.fixtures.r28_mcp_helpers import (
    COMPAT_VERSION,
    INITIALIZED_NOTIFICATION,
    REPO_ROOT,
    REVISION,
    RUN_TOOLS,
    SERVER_PATH,
    VSCODE_CAPABILITIES,
    VSCODE_INITIALIZE_LINE,
    assert_protocol_error,
    compat_call,
    compat_request,
    encode,
    expected_capabilities,
    frames,
    initialize_request,
    request,
    run_launcher_raw,
    run_messages,
    run_raw,
)
from tests.fixtures.r28_mcp_conformance import era_batch, structured_era

pytestmark = pytest.mark.unit

INIT_RESULT = {
    "protocolVersion": "2025-11-25",
    "capabilities": {"tools": {}},
    "serverInfo": {"name": "genia-mcp", "version": REVISION},
}
UNSUPPORTED = "Unsupported protocol version"


def _native(messages):
    """Responses of the native server alone (no host capabilities: only `genia_capabilities`)."""
    done = run_messages(messages)
    assert done.returncode == 0, done.stderr.decode()
    return [json.loads(frame) for frame in frames(done.stdout)]


# --- the authentic VS Code message ------------------------------------------------------------


def test_the_exact_vscode_initialize_from_the_first_authentic_run_now_succeeds():
    done = run_raw([VSCODE_INITIALIZE_LINE, encode(INITIALIZED_NOTIFICATION), encode(compat_request("tools/list", 2))])
    assert done.returncode == 0
    init, listed = [json.loads(frame) for frame in frames(done.stdout)]  # exactly two frames: nothing for the notification
    assert init == {"jsonrpc": "2.0", "id": 1, "result": INIT_RESULT}
    assert set(listed["result"]) == {"tools"} and listed["id"] == 2
    assert [t["name"] for t in listed["result"]["tools"]] == ["genia_capabilities", "genia_language_profile"]  # native-only server


def test_initialize_result_is_exactly_version_tools_capability_and_identity():
    ((init),) = _native([initialize_request(1)])
    assert init["result"] == INIT_RESULT
    assert set(init["result"]) == {"protocolVersion", "capabilities", "serverInfo"}  # no instructions
    assert set(init["result"]["capabilities"]) == {"tools"}  # no resources, prompts, logging, completions, tasks
    assert init["result"]["capabilities"]["tools"] == {}  # no listChanged


# --- the closed version policy -------------------------------------------------------------


@pytest.mark.parametrize(
    "version",
    ["2025-06-18", "2025-03-26", "2024-11-05", "2024-10-07", "2026-07-28", "2025-11-26", "", "garbage", "1.0.0"],
)
def test_any_other_version_is_rejected_never_negotiated_down_and_leaves_the_state_new(version):
    bad, listed = _native([initialize_request(1, version=version), compat_request("tools/list", 2)])
    assert_protocol_error(bad, -32602, req_id=1, message=UNSUPPORTED, data={"supported": [COMPAT_VERSION], "requested": version})
    assert_protocol_error(listed, -32602, req_id=2)  # still no era: the failed initialize changed nothing


@pytest.mark.parametrize(
    "mutation",
    [
        {"protocolVersion": 20251125},
        {"protocolVersion": None},
        {"protocolVersion": ["2025-11-25"]},
        {"capabilities": "roots"},
        {"capabilities": None},
        {"capabilities": [{}]},
        {"clientInfo": "vscode"},
        {"clientInfo": None},
        {"clientInfo": {"name": "x"}},
        {"clientInfo": {"version": "1"}},
        {"clientInfo": {"name": 1, "version": "1"}},
        {"clientInfo": {"name": "x", "version": 1}},
    ],
    ids=lambda m: json.dumps(m),
)
def test_a_malformed_initialize_is_invalid_params_and_leaves_the_state_new(mutation):
    params = initialize_request(1)["params"] | mutation
    bad, listed = _native([{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": params},
                           compat_request("tools/list", 2)])
    assert_protocol_error(bad, -32602, req_id=1)
    assert_protocol_error(listed, -32602, req_id=2)


@pytest.mark.parametrize("missing", ["protocolVersion", "capabilities", "clientInfo"])
def test_an_initialize_missing_a_required_member_is_invalid_params(missing):
    params = {k: v for k, v in initialize_request(1)["params"].items() if k != missing}
    (bad,) = _native([{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": params}])
    assert_protocol_error(bad, -32602, req_id=1)


@pytest.mark.parametrize("params", [None, [], "x", 5, []], ids=["absent", "list", "string", "number", "empty-list"])
def test_an_initialize_with_non_object_or_absent_params_is_invalid_params(params):
    message = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
    if params is not None:
        message["params"] = params
    (bad,) = _native([message])
    assert_protocol_error(bad, -32602, req_id=1)


@pytest.mark.parametrize("bad_id", [None, 1.5, True, [1], {"a": 1}], ids=str)
def test_an_initialize_with_an_unusable_id_is_an_invalid_request(bad_id):
    message = initialize_request(1) | {"id": bad_id}
    (bad,) = _native([message])
    assert_protocol_error(bad, -32600, req_id=None)


def test_initialize_without_an_id_is_a_notification_with_no_response_and_no_state_change():
    message = {k: v for k, v in initialize_request(1).items() if k != "id"}
    out = _native([message, compat_request("tools/list", 2)])
    assert len(out) == 1
    assert_protocol_error(out[0], -32602, req_id=2)  # no era was established


def test_extra_initialize_members_and_a_meta_without_the_version_key_are_ignored():
    params = initialize_request(1)["params"] | {"_meta": {"progressToken": "p"}, "future": {"x": 1}}
    (init,) = _native([{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": params}])
    assert init["result"] == INIT_RESULT


# --- the one-bit state and deterministic ordering --------------------------------------------------


def test_requests_before_initialize_are_invalid_params_exactly_as_before_the_amendment():
    out = _native([
        compat_request("tools/list", 1),
        compat_call("genia_capabilities", {}, 2),
        compat_request("server/discover", 3),
    ])
    for index, response in enumerate(out, 1):
        assert_protocol_error(response, -32602, req_id=index)


def test_after_initialize_the_requests_are_served_and_a_second_initialize_is_invalid():
    out = _native([
        initialize_request(1),
        compat_request("tools/list", 2),
        initialize_request(3),
        compat_call("genia_capabilities", {}, 4),
        initialize_request(5, version="2025-06-18"),
        compat_request("tools/list", 6),
    ])
    assert out[0]["result"] == INIT_RESULT
    assert "result" in out[1] and out[1]["id"] == 2
    assert_protocol_error(out[2], -32600, req_id=3)  # duplicate initialize
    assert "result" in out[3] and out[3]["id"] == 4  # the session survived the duplicate
    assert_protocol_error(out[4], -32600, req_id=5)  # duplicate wins over the version check: already initialized
    assert "result" in out[5]


def test_the_initialized_notification_is_accepted_silently_in_every_state_and_changes_nothing():
    out = _native([
        INITIALIZED_NOTIFICATION,  # before initialize: ignored, does not create a session
        compat_request("tools/list", 1),
        initialize_request(2),
        INITIALIZED_NOTIFICATION,
        INITIALIZED_NOTIFICATION,
        compat_request("tools/list", 3),
    ])
    assert [r["id"] for r in out] == [1, 2, 3]  # no frame for any notification
    assert_protocol_error(out[0], -32602, req_id=1)
    assert out[1]["result"] == INIT_RESULT and "result" in out[2]


def test_the_state_is_per_process_and_never_survives_a_launch():
    first = _native([initialize_request(1), compat_request("tools/list", 2)])
    second = _native([compat_request("tools/list", 1)])
    assert "result" in first[1]
    assert_protocol_error(second[0], -32602, req_id=1)  # a new launch starts NEW


def test_a_fresh_launch_after_a_failed_session_is_independent():
    _native([initialize_request(1, version="1.0.0")])
    out = _native([initialize_request(1)])
    assert out[0]["result"] == INIT_RESULT


# --- ping and the other methods ----------------------------------------------------------------


def test_ping_answers_an_empty_result_in_every_state():
    out = _native([
        compat_request("ping", 1),
        initialize_request(2),
        compat_request("ping", 3),
        compat_request("ping", 4, {"_meta": {"progressToken": 9}}),
    ])
    assert out[0] == {"jsonrpc": "2.0", "id": 1, "result": {}}
    assert out[2] == {"jsonrpc": "2.0", "id": 3, "result": {}}
    assert out[3] == {"jsonrpc": "2.0", "id": 4, "result": {}}


def test_ping_with_non_object_params_is_invalid_params():
    (bad,) = _native([compat_request("ping", 1, [1])])
    assert_protocol_error(bad, -32602, req_id=1)


@pytest.mark.parametrize(
    "method",
    [
        "resources/list", "resources/read", "resources/templates/list", "resources/subscribe",
        "prompts/list", "prompts/get", "completion/complete", "logging/setLevel", "tasks/list", "tasks/get",
        "tasks/result", "tasks/cancel", "roots/list", "sampling/createMessage", "elicitation/create",
        "notifications/initialized", "notifications/cancelled", "unknown/method", "",
    ],
)
def test_every_other_method_is_method_not_found_before_and_after_initialize(method):
    before, _, after = _native([compat_request(method, 1, {}), initialize_request(2), compat_request(method, 3, {})])
    assert_protocol_error(before, -32601, req_id=1)
    assert_protocol_error(after, -32601, req_id=3)


def test_tools_list_cursor_and_bad_tool_calls_keep_their_protocol_errors_in_the_compat_era():
    out = _native([
        initialize_request(1),
        compat_request("tools/list", 2, {"cursor": "x"}),
        compat_call("no_such_tool", {}, 3),
        compat_request("tools/call", 4, {"arguments": {}}),
        compat_request("tools/call", 5, {"name": 7}),
        compat_call("genia_capabilities", {"extra": 1}, 6),
        compat_request("tools/call", 7, [1]),
    ])
    assert_protocol_error(out[1], -32602, req_id=2)
    assert_protocol_error(out[2], -32602, req_id=3, message="Unknown tool")
    for index, rid in ((3, 4), (4, 5), (5, 6), (6, 7)):
        assert_protocol_error(out[index], -32602, req_id=rid)


def test_malformed_lines_are_parse_errors_and_the_session_keeps_serving():
    done = run_raw([encode(initialize_request(1)), b"{not json", b'{"jsonrpc":"2.0","id":9,"method":"tools/list"}'])
    out = [json.loads(frame) for frame in frames(done.stdout)]
    assert out[0]["result"] == INIT_RESULT
    assert out[1]["error"]["code"] == -32700 and "id" not in out[1]
    assert "result" in out[2] and out[2]["id"] == 9


# --- coexistence with the 2026-07-28 era (era selection by the _meta version key) ---------------------


def test_a_request_with_the_modern_meta_is_always_a_modern_request_even_after_initialize():
    out = _native([
        initialize_request(1),
        request("tools/list", 2),  # modern `_meta`
        compat_request("tools/list", 3),
    ])
    modern, compat = out[1]["result"], out[2]["result"]
    assert modern["resultType"] == "complete" and modern["ttlMs"] == 0 and "_meta" in modern
    assert set(compat) == {"tools"} and compat["tools"] == modern["tools"]


def test_initialize_carrying_the_modern_meta_is_still_method_not_found():
    meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clientCapabilities": {}}
    params = initialize_request(1)["params"] | {"_meta": meta}
    (bad,) = _native([{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": params}])
    assert_protocol_error(bad, -32601, req_id=1)


def test_a_malformed_modern_meta_is_invalid_params_in_every_state():
    broken = {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}  # capabilities missing
    out = _native([request("tools/list", 1, meta=broken), initialize_request(2), request("tools/list", 3, meta=broken)])
    assert_protocol_error(out[0], -32602, req_id=1)
    assert_protocol_error(out[2], -32602, req_id=3)


def test_the_modern_unsupported_version_error_is_unchanged():
    meta = {"io.modelcontextprotocol/protocolVersion": "2025-11-25", "io.modelcontextprotocol/clientCapabilities": {}}
    (bad,) = _native([request("tools/list", 1, meta=meta)])
    assert bad["error"] == {"code": -32022, "message": "Unsupported protocol version",
                            "data": {"supported": ["2026-07-28"], "requested": "2025-11-25"}}


# --- both eras reach the same three tools, schemas, and tool implementations ------------------------------


def _launcher(messages):
    done = run_launcher_raw([encode(m) for m in messages])
    assert done.returncode == 0, done.stderr.decode()
    return [json.loads(frame) for frame in frames(done.stdout)]


def test_the_compat_era_lists_exactly_the_same_three_tools_with_identical_descriptors():
    out = _launcher([request("tools/list", 1), initialize_request(2), compat_request("tools/list", 3)])
    modern, compat = out[0]["result"]["tools"], out[2]["result"]["tools"]
    assert [t["name"] for t in compat] == list(RUN_TOOLS)
    assert compat == modern  # byte-for-byte the same descriptors (names, descriptions, closed schemas)
    assert set(out[2]["result"]) == {"tools"}


def test_the_compat_era_advertises_no_resources_or_prompts_and_no_pagination():
    out = _launcher([
        initialize_request(1),
        compat_request("resources/list", 2, {}),
        compat_request("prompts/list", 3, {}),
        compat_request("tools/list", 4),
    ])
    assert out[0]["result"]["capabilities"] == {"tools": {}}
    assert_protocol_error(out[1], -32601, req_id=2)
    assert_protocol_error(out[2], -32601, req_id=3)
    assert "nextCursor" not in out[3]["result"]


def test_capabilities_report_the_serving_protocol_revision_and_are_otherwise_identical_across_eras():
    out = _launcher([request("tools/call", 1, {"name": "genia_capabilities"}), initialize_request(2),
                     compat_call("genia_capabilities", {}, 3)])
    _, modern = structured_era(out[0], "modern")
    _, compat = structured_era(out[2], "compat")
    assert modern["result"]["mcp"]["protocol_version"] == "2026-07-28"
    assert compat["result"]["mcp"]["protocol_version"] == "2025-11-25"
    modern["result"]["mcp"]["protocol_version"] = compat["result"]["mcp"]["protocol_version"]
    assert modern == compat  # tools, execution profile, identity: one definition serves both eras
    assert compat["result"]["tools"] == list(RUN_TOOLS)
    assert compat["result"] == expected_capabilities(compat["result"]["genia"]["contract_revision"], RUN_TOOLS) | {
        "mcp": {"protocol_version": "2025-11-25", "transport": "stdio"}}


def test_a_compat_tools_call_result_has_exactly_content_structuredcontent_and_iserror():
    _, out = era_batch([compat_call("genia_capabilities", {}, 1)], "compat")
    result = out[0]["result"]
    assert set(result) == {"content", "structuredContent", "isError"}
    assert result["isError"] is False and len(result["content"]) == 1
    assert "resultType" not in result and "_meta" not in result and "ttlMs" not in result


def test_serverinfo_version_is_the_same_contract_revision_in_both_eras():
    out = _launcher([request("server/discover", 1), initialize_request(2)])
    modern = out[0]["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]
    assert out[1]["result"]["serverInfo"] == modern and set(modern) == {"name", "version"}


# --- client capabilities grant nothing ---------------------------------------------------------------------

MAXIMAL = {
    "roots": {"listChanged": True},
    "sampling": {"tools": {}, "context": {}},
    "elicitation": {"form": {}, "url": {}},
    "tasks": {"list": {}, "cancel": {}, "requests": {"tools": {"call": {}}}},
    "experimental": {"anything": {"x": 1}},
    "extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": ["text/html;profile=mcp-app"]}},
}


@pytest.mark.parametrize("caps", [{}, VSCODE_CAPABILITIES, MAXIMAL], ids=["empty", "vscode", "maximal"])
def test_results_are_identical_whatever_capabilities_the_client_advertises(caps):
    out = _launcher([initialize_request(1, capabilities=caps), compat_request("tools/list", 2),
                     compat_call("genia_capabilities", {}, 3)])
    baseline = _launcher([initialize_request(1, capabilities={}), compat_request("tools/list", 2),
                          compat_call("genia_capabilities", {}, 3)])
    assert out == baseline
    assert out[0]["result"]["capabilities"] == {"tools": {}}


def test_the_server_never_sends_a_request_or_notification_to_a_client_that_advertises_everything():
    messages = [initialize_request(1, capabilities=MAXIMAL), INITIALIZED_NOTIFICATION,
                compat_request("tools/list", 2), compat_call("genia_capabilities", {}, 3),
                compat_call("genia_parse", {"source": "1 +"}, 4), compat_call("genia_run", {"source": "6 * 7"}, 5),
                compat_call("genia_run", {"source": 'read_file("/etc/hostname")'}, 6), compat_request("ping", 7)]
    out = _launcher(messages)
    assert [m["id"] for m in out] == [1, 2, 3, 4, 5, 6, 7]  # one response per request, nothing else
    for message in out:
        assert "method" not in message and ("result" in message) != ("error" in message)


def test_client_supplied_values_are_validated_for_shape_and_never_reflected_or_stored():
    marker = "SENTINEL-CLIENT-" + "Z9Q"
    caps = {"experimental": {marker: {marker: marker}}}
    info = {"name": marker, "version": marker, "title": marker}
    done = run_launcher_raw([encode(initialize_request(1, capabilities=caps, client_info=info)),
                             encode(compat_request("tools/list", 2)), encode(compat_call("genia_capabilities", {}, 3))])
    assert marker.encode() not in done.stdout and marker.encode() not in done.stderr


def test_the_native_program_names_no_server_to_client_method_or_client_capability_behavior():
    text = SERVER_PATH.read_text(encoding="utf-8")
    for forbidden in ("roots/list", "sampling/createMessage", "elicitation/create", "tasks/", "notifications/message",
                      "list_changed", "notifications/progress", "logging/", "resources/", "prompts/", "completion/"):
        assert forbidden not in text, forbidden


def test_the_initialization_state_is_one_process_local_cell_in_native_genia():
    text = SERVER_PATH.read_text(encoding="utf-8")
    assert text.count("ref(") == 1 and "ref_set(" in text  # exactly one mutable cell
    assert "initialize" in text and "COMPAT_PROTOCOL_VERSION" in text


# --- host modules stay free of protocol semantics (architecture) ---------------------------------------------------


def test_no_python_host_module_gains_initialize_ping_or_any_protocol_version_literal():
    for path in sorted((REPO_ROOT / "hosts" / "python").glob("mcp_*.py")):
        text = path.read_text(encoding="utf-8")
        for literal in ("initialize", "protocolVersion", "2025-11-25", "2026-07-28", "serverInfo", '"ping"',
                        "notifications/initialized", "tools/list", "tools/call"):
            assert literal not in text, f"{path.name} must not own MCP protocol semantics: {literal}"


def test_the_launcher_and_host_are_unchanged_by_the_amendment():
    launcher = (REPO_ROOT / "hosts" / "python" / "mcp_launch.py").read_text(encoding="utf-8")
    assert re.search(r"def main\(\)", launcher) and "initialize" not in launcher
