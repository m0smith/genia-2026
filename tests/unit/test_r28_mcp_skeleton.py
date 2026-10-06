"""R28 E28-1 (issue #702): native Genia MCP skeleton, wire-level tests.

Pinned to the verified MCP 2026-07-28 shapes recorded in
docs/design/r28-e28-1-native-mcp-skeleton-design.md section 7. The server under
test is the native ``apps/mcp/mcp.genia`` program; nothing here imports an MCP SDK
or any Python MCP application.

These tests are written before implementation and are expected to fail until
``apps/mcp/mcp.genia`` exists (failing-test phase).
"""

from __future__ import annotations

import json

import pytest

from tests.fixtures.r28_mcp_helpers import (
    META_CAPABILITIES,
    META_CLIENT_INFO,
    META_SERVER_INFO,
    META_VERSION,
    OTHER_REVISION,
    PROTOCOL_VERSION,
    REVISION,
    UNKNOWN_TOOL_MESSAGE,
    assert_protocol_error,
    cached_call,
    call,
    encode,
    expected_capabilities,
    expected_envelope,
    frames,
    good_meta,
    notification,
    request,
    responses,
    run_messages,
    run_raw,
)

pytestmark = pytest.mark.unit

CAPS_CALL = request("tools/call", 7, {"name": "genia_capabilities", "arguments": {}})


# --- server/discover --------------------------------------------------------


def test_discover_result_shape_is_exact():
    response = cached_call(request("server/discover", 1))
    assert set(response) == {"jsonrpc", "id", "result"}
    assert response["jsonrpc"] == "2.0" and response["id"] == 1
    result = response["result"]
    assert set(result) == {
        "resultType",
        "supportedVersions",
        "capabilities",
        "ttlMs",
        "cacheScope",
        "_meta",
    }
    assert result["resultType"] == "complete"
    assert result["supportedVersions"] == [PROTOCOL_VERSION]
    # Only tools: no resources, prompts, logging, completions, subscriptions.
    assert result["capabilities"] == {"tools": {}}
    assert type(result["ttlMs"]) is int and result["ttlMs"] == 0
    assert result["cacheScope"] == "public"
    assert result["_meta"] == {META_SERVER_INFO: {"name": "genia-mcp", "version": REVISION}}


def test_discover_does_not_require_a_prior_request_or_session():
    # Stateless: a first-ever request may be any method; no initialize needed.
    first = call(request("tools/list", 1))
    assert "error" not in first


# --- tools/list (E28-1 intermediate surface) --------------------------------


def test_tools_list_advertises_only_implemented_tools():
    result = cached_call(request("tools/list", 2))["result"]
    names = [tool["name"] for tool in result["tools"]]
    # Plain file mode provisions no host capability: genia_parse (E28-2) and genia_run (E28-3)
    # must not be advertised before they work. genia_language_profile (A6) is native-only.
    assert names == ["genia_capabilities", "genia_language_profile"]


def test_tools_list_result_shape_is_exact():
    response = cached_call(request("tools/list", 2))
    result = response["result"]
    assert set(result) == {"resultType", "tools", "ttlMs", "cacheScope", "_meta"}
    assert result["resultType"] == "complete"
    assert "nextCursor" not in result
    assert result["ttlMs"] == 0 and result["cacheScope"] == "public"
    (tool,) = result["tools"]
    assert set(tool) == {"name", "description", "inputSchema"}
    assert isinstance(tool["description"], str) and tool["description"]
    assert tool["inputSchema"] == {
        "type": "object",
        "additionalProperties": False,
        "properties": {},
    }


def test_tools_list_is_deterministic_across_calls():
    a = call(request("tools/list", 1))
    b = call(request("tools/list", 1))
    assert a == b


def test_tools_list_rejects_any_cursor_no_pagination_in_e28_1():
    response = call(request("tools/list", 3, {"cursor": "x"}))
    assert_protocol_error(response, -32602, req_id=3)


# --- tools/call genia_capabilities -------------------------------------------


def test_capabilities_call_uses_verified_calltoolresult_shape():
    response = cached_call(CAPS_CALL)
    assert set(response) == {"jsonrpc", "id", "result"} and response["id"] == 7
    result = response["result"]
    assert set(result) == {"resultType", "content", "structuredContent", "isError", "_meta"}
    assert result["resultType"] == "complete"
    assert result["isError"] is False
    assert result["_meta"] == {META_SERVER_INFO: {"name": "genia-mcp", "version": REVISION}}
    (item,) = result["content"]
    assert set(item) == {"type", "text"} and item["type"] == "text"


def test_capabilities_structured_content_is_the_exact_contract_envelope():
    structured = cached_call(CAPS_CALL)["result"]["structuredContent"]
    assert structured == expected_envelope()
    assert list(structured["result"]["tools"]) == ["genia_capabilities", "genia_language_profile"]


def test_capabilities_text_content_is_the_same_json_as_structured_content():
    result = cached_call(CAPS_CALL)["result"]
    text = result["content"][0]["text"]
    assert "\n" not in text  # the text item is itself one line
    assert json.loads(text) == result["structuredContent"]


def test_capabilities_is_truthful_about_implemented_tools_only():
    caps = cached_call(CAPS_CALL)["result"]["structuredContent"]["result"]
    assert "genia_parse" not in caps["tools"] and "genia_run" not in caps["tools"]
    assert caps["tools"] == ["genia_capabilities", "genia_language_profile"]
    assert caps["mcp"] == {"protocol_version": PROTOCOL_VERSION, "transport": "stdio"}
    assert caps["genia"]["host"] == "python-reference"
    assert caps["genia"]["portable_mcp_implementation"] is False
    assert caps == expected_capabilities()


def test_capabilities_arguments_may_be_omitted_or_empty():
    omitted = call(request("tools/call", 1, {"name": "genia_capabilities"}))
    empty = call(request("tools/call", 1, {"name": "genia_capabilities", "arguments": {}}))
    assert omitted == empty
    assert omitted["result"]["structuredContent"] == expected_envelope()


@pytest.mark.parametrize(
    "arguments",
    [{"extra": 1}, {"path": "/etc/hostname"}, {"source": "1"}, [], "x", 1, None, True],
)
def test_capabilities_arguments_schema_is_closed(arguments):
    response = call(
        request("tools/call", 4, {"name": "genia_capabilities", "arguments": arguments})
    )
    assert_protocol_error(response, -32602, req_id=4)


def test_responses_are_deterministic_and_stateless_across_order():
    a = run_messages(
        [request("tools/list", 1), CAPS_CALL, request("server/discover", 2)]
    )
    b = run_messages(
        [request("server/discover", 2), CAPS_CALL, request("tools/list", 1)]
    )
    by_id_a = {r["id"]: r for r in responses(a)}
    by_id_b = {r["id"]: r for r in responses(b)}
    assert by_id_a == by_id_b
    # Repeating a request never changes its answer (no cross-request state).
    twice = responses(run_messages([CAPS_CALL, CAPS_CALL]))
    assert twice[0] == twice[1]


def test_contract_revision_comes_only_from_launch_argument():
    other = call(CAPS_CALL, args=(OTHER_REVISION,))
    assert other["result"]["structuredContent"] == expected_envelope(OTHER_REVISION)


def test_request_cannot_select_paths_or_environment():
    hostile = request(
        "tools/call",
        5,
        {"name": "genia_capabilities", "arguments": {"path": "/etc/passwd", "env": "HOME"}},
    )
    response = call(hostile)
    assert_protocol_error(response, -32602, req_id=5)


# --- unknown tools / methods -------------------------------------------------


@pytest.mark.parametrize(
    "name",
    ["genia_parse", "genia_run", "genia_CAPABILITIES", "nope", "", "genia_capabilities "],
)
def test_unadvertised_tool_is_unknown_tool_protocol_error(name):
    response = call(request("tools/call", 9, {"name": name, "arguments": {}}))
    assert_protocol_error(response, -32602, req_id=9, message=UNKNOWN_TOOL_MESSAGE)


def test_unknown_tool_message_never_echoes_caller_strings():
    marker = "SENTINEL-TOOL-NAME- -\"-\\"
    response = call(request("tools/call", 9, {"name": marker}))
    assert_protocol_error(response, -32602, req_id=9, message=UNKNOWN_TOOL_MESSAGE)
    assert "SENTINEL" not in json.dumps(response)


@pytest.mark.parametrize(
    "params",
    [{}, {"name": 5}, {"name": None}, {"name": ["genia_capabilities"]}],
)
def test_calltool_params_must_carry_a_string_name(params):
    response = call(request("tools/call", 6, params))
    assert_protocol_error(response, -32602, req_id=6)


@pytest.mark.parametrize(
    "method",
    [
        "initialize",  # legacy handshake is not offered; no session behavior
        "notifications/initialized",
        "resources/list",
        "resources/read",
        "prompts/list",
        "prompts/get",
        "logging/setLevel",
        "completion/complete",
        "subscriptions/listen",
        "tasks/get",
        "nope",
        "",
    ],
)
def test_unsupported_methods_are_method_not_found(method):
    response = call(request(method, 11))
    assert_protocol_error(response, -32601, req_id=11)


def test_initialize_creates_no_session_and_does_not_change_later_answers():
    out = responses(
        run_messages([request("initialize", 1), request("tools/list", 2)])
    )
    assert_protocol_error(out[0], -32601, req_id=1)
    assert [t["name"] for t in out[1]["result"]["tools"]] == ["genia_capabilities", "genia_language_profile"]


# --- per-request _meta and protocol version ----------------------------------


@pytest.mark.parametrize("method", ["server/discover", "tools/list", "tools/call"])
def test_missing_meta_is_invalid_params(method):
    params = {"name": "genia_capabilities"} if method == "tools/call" else {}
    response = call(request(method, 3, params, meta=False))
    assert_protocol_error(response, -32602, req_id=3)


@pytest.mark.parametrize(
    "meta",
    [
        {META_CAPABILITIES: {}},  # version missing
        {META_VERSION: PROTOCOL_VERSION},  # capabilities missing
        {META_VERSION: 20260728, META_CAPABILITIES: {}},  # version not a string
        {META_VERSION: None, META_CAPABILITIES: {}},
        {META_VERSION: PROTOCOL_VERSION, META_CAPABILITIES: []},  # not an object
        {META_VERSION: PROTOCOL_VERSION, META_CAPABILITIES: "x"},
        {},
        [],
        "x",
        None,
    ],
)
def test_malformed_meta_is_invalid_params(meta):
    response = call(request("tools/list", 3, meta=meta))
    assert_protocol_error(response, -32602, req_id=3)


@pytest.mark.parametrize("requested", ["2025-11-25", "2025-06-18", "1900-01-01", "2026-07-29", ""])
def test_unsupported_protocol_version_is_32022_with_supported_list(requested):
    meta = {META_VERSION: requested, META_CAPABILITIES: {}}
    for method in ("server/discover", "tools/list"):
        response = call(request(method, 8, meta=meta))
        assert_protocol_error(
            response,
            -32022,
            req_id=8,
            data={"supported": [PROTOCOL_VERSION], "requested": requested},
        )


def test_extra_meta_keys_and_client_info_are_accepted_and_ignored():
    meta = good_meta(
        **{
            META_CLIENT_INFO: {"name": "test-client", "version": "9.9"},
            "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
            "progressToken": "p1",
        }
    )
    plain = call(request("tools/list", 1))
    rich = call(request("tools/list", 1, meta=meta))
    assert plain == rich  # client identity never changes server behavior


def test_params_that_are_not_an_object_are_invalid_params():
    message = {"jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": 5}
    assert_protocol_error(call(message), -32602, req_id=4)
    message = {"jsonrpc": "2.0", "id": 4, "method": "tools/list"}  # no params, no _meta
    assert_protocol_error(call(message), -32602, req_id=4)


# --- malformed messages and notifications ------------------------------------


@pytest.mark.parametrize(
    "raw",
    [b"{bad", b"not json", b"{\"jsonrpc\":\"2.0\",", b"\xff\xfe", b"{\"a\":1}{\"b\":2}", b"nul\x00l"],
)
def test_unparseable_line_is_parse_error_and_server_keeps_running(raw):
    out = responses(run_raw([raw, encode(request("tools/list", 1))]))
    assert len(out) == 2
    assert_protocol_error(out[0], -32700, req_id=None)
    assert out[1]["id"] == 1 and "result" in out[1]


@pytest.mark.parametrize(
    ("message", "expected_id"),
    [
        ([1], None),
        ("string", None),
        (5, None),
        (None, None),
        ({"jsonrpc": "1.0", "id": 1, "method": "tools/list"}, 1),
        ({"id": 1, "method": "tools/list"}, 1),
        ({"jsonrpc": "2.0", "id": 1}, 1),
        ({"jsonrpc": "2.0", "id": 1, "method": 5}, 1),
        ({"jsonrpc": "2.0", "id": None, "method": "tools/list"}, None),
        ({"jsonrpc": "2.0", "id": True, "method": "tools/list"}, None),
        ({"jsonrpc": "2.0", "id": {"a": 1}, "method": "tools/list"}, None),
        ({"jsonrpc": "2.0", "id": 1.5, "method": "tools/list"}, None),
    ],
)
def test_invalid_jsonrpc_object_is_invalid_request(message, expected_id):
    out = responses(run_messages([message, request("tools/list", 2)]))
    assert len(out) == 2
    assert_protocol_error(out[0], -32600, req_id=expected_id)
    assert out[1]["id"] == 2


def test_notifications_get_no_response_and_do_not_disturb_the_stream():
    out = responses(
        run_messages(
            [
                notification("notifications/cancelled", {"requestId": "nope", "reason": "x"}),
                notification("notifications/unknown-extension"),
                request("tools/list", 1),
                notification("notifications/cancelled", {"requestId": 1}),
            ]
        )
    )
    assert [r["id"] for r in out] == [1]


def test_server_never_sends_requests_or_extra_messages():
    out = responses(
        run_messages(
            [request("server/discover", 1), request("tools/list", 2), CAPS_CALL]
        )
    )
    assert [r["id"] for r in out] == [1, 2, 7]
    assert all(set(r) == {"jsonrpc", "id", "result"} for r in out)


def test_eof_with_no_input_exits_zero_with_no_output():
    completed = run_raw([])
    assert completed.returncode == 0
    assert completed.stdout == b"" and completed.stderr == b""


# --- stdio framing ------------------------------------------------------------

ID_VECTORS = [
    "a\nb",
    'quote"inside',
    "back\\slash",
    "  ",
    "\U0001f600",
    "\x00\x01\x1f",
    "tab\tcr\r",
    "  lead and trail  ",
    "",
    "line\nbreak inside an id that also \\n has a literal backslash-n",
    "x" * 20000,
    "café 中文",
    7,
    0,
    -3,
    9007199254740991,
]


@pytest.mark.parametrize("ensure_ascii", [True, False])
def test_every_response_is_exactly_one_protocol_line_and_round_trips_ids(ensure_ascii):
    messages = [request("tools/list", i) for i in ID_VECTORS]
    lines = [encode(m, ensure_ascii=ensure_ascii) for m in messages]
    completed = run_raw(lines)
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    out_frames = frames(completed.stdout)
    # exactly one line per request, each a complete JSON value
    assert len(out_frames) == len(ID_VECTORS)
    for frame, sent_id in zip(out_frames, ID_VECTORS):
        assert b"\n" not in frame and b"\r" not in frame
        decoded = json.loads(frame.decode("utf-8"))
        assert decoded["id"] == sent_id and type(decoded["id"]) is type(sent_id)
        assert decoded["result"]["tools"][0]["name"] == "genia_capabilities"


def test_framing_holds_for_the_tool_result_text_item_too():
    hostile_id = "a\nb \"\\\x00"
    response = call(request("tools/call", hostile_id, {"name": "genia_capabilities"}))
    text = response["result"]["content"][0]["text"]
    assert "\n" not in text
    assert json.loads(text) == response["result"]["structuredContent"] == expected_envelope()
    assert response["id"] == hostile_id


def test_emitted_json_decodes_to_the_intended_value():
    # Round trip: the decoded frames equal the independently specified values.
    out = responses(run_messages([CAPS_CALL]))
    assert out[0]["result"]["structuredContent"] == expected_envelope()


def test_stdout_contains_only_protocol_frames_and_stderr_is_quiet():
    completed = run_messages(
        [request("tools/list", 1), {"bad": True}, request("nope", 2), CAPS_CALL]
    )
    assert completed.returncode == 0
    for frame in frames(completed.stdout):
        message = json.loads(frame.decode("utf-8"))
        assert message["jsonrpc"] == "2.0" and ("result" in message or "error" in message)
    assert completed.stderr == b""


def test_bytes_written_before_a_bad_line_are_not_lost_or_reordered():
    lines = [
        encode(request("tools/list", 1)),
        b"{bad",
        encode(request("tools/list", 2)),
    ]
    out = responses(run_raw(lines))
    assert [r.get("id") for r in out] == [1, None, 2]


# --- startup: contract_revision launch datum ---------------------------------


@pytest.mark.parametrize(
    "args",
    [
        (),
        (REVISION.upper(),),
        (REVISION[:39],),
        (REVISION + "0",),
        ("g" * 40,),
        (REVISION + "-dirty",),
        (" " + REVISION,),
        ("",),
        (REVISION, "extra"),
    ],
)
def test_invalid_launch_revision_fails_closed_before_serving(args):
    completed = run_raw([encode(request("tools/list", 1))], args=args)
    assert completed.returncode != 0
    assert completed.stdout == b""  # nothing on the protocol channel
    assert completed.stderr != b""  # fixed diagnostic on stderr
    stderr = completed.stderr.decode("utf-8", "replace")
    for arg in args:
        if arg:
            assert arg not in stderr  # never echo the rejected value
    assert "Traceback" not in stderr


def test_valid_revision_is_reported_verbatim():
    response = call(CAPS_CALL, args=(OTHER_REVISION,))
    caps = response["result"]["structuredContent"]["result"]
    assert caps["genia"]["contract_revision"] == OTHER_REVISION
    assert len(OTHER_REVISION) == 40 and OTHER_REVISION == OTHER_REVISION.lower()
