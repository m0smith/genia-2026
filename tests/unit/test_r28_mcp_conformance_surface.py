"""R28 E28-5 (issue #706): conformance matrix, discovery/schemas/capabilities and `genia_parse`.

Matrix rows D1-D8 and P1-P12 in docs/mcp/conformance-matrix.md. Python-host tests of the MCP
adapter boundary (transport and wire behavior of the launcher); they add no Genia semantics.
Namespace honesty: the discovery and capability surface is identical whether the host grants
or denies an unprivileged namespace (matrix N1/N2).
"""

from __future__ import annotations

import json
import re

import pytest

from hosts.python.parse_adapter import parse_and_normalize
from tests.fixtures.r28_mcp_conformance import (
    NS_MODES,
    SOURCE_LIMIT,
    assert_closed_failure,
    launcher_batch,
    parse_sources,
)
from tests.fixtures.r28_mcp_helpers import (
    REPO_ROOT,
    RUN_TOOLS,
    UNKNOWN_TOOL_MESSAGE,
    assert_protocol_error,
    encode,
    error_envelope,
    expected_envelope,
    frames,
    parse_request,
    repository_revision,
    request,
    run_launcher_raw,
    run_request,
    structured,
)

pytestmark = pytest.mark.unit

# Exact descriptions. The contract does not make descriptions normative; they are pinned here
# only as drift detectors (a change must be a deliberate, reviewed edit of this table).
DESCRIPTIONS = {
    "genia_capabilities": (
        "Report the Genia MCP server identity, protocol revision, transport, advertised tools, "
        "and governed execution profile."
    ),
    "genia_parse": (
        "Parse explicit Genia source text and return the existing normalized parse output, or a "
        "bounded parse diagnostic. Parsing never evaluates the source."
    ),
    "genia_run": (
        "Run explicit Genia source in a fresh, disposable, policy-restricted worker. Returns the "
        "canonical debug rendering of the value, program stdout, and program stderr as separate "
        "fields, or a bounded failure. Source only: no file, environment, configuration, secret, "
        "network, process, or import authority."
    ),
}
SOURCE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["source"],
    "properties": {"source": {"type": "string", "maxLength": SOURCE_LIMIT}},
}
INPUT_SCHEMAS = {
    "genia_capabilities": {"type": "object", "additionalProperties": False, "properties": {}},
    "genia_parse": SOURCE_SCHEMA,
    "genia_run": SOURCE_SCHEMA,
}


def _discovery(mode):
    messages = [
        request("server/discover", 1),
        request("tools/list", 2),
        request("tools/list", 3),
        request("tools/call", 4, {"name": "genia_capabilities"}),
    ]
    _, out = launcher_batch(messages, mode)
    return out


# --- D1-D6: discovery and schema stability ---------------------------------------------------


@pytest.mark.parametrize("mode", NS_MODES)
def test_discovery_advertises_exactly_the_three_tools_in_contract_order(mode):
    discover, listed, listed_again, _ = _discovery(mode)
    tools = listed["result"]["tools"]
    assert [tool["name"] for tool in tools] == list(RUN_TOOLS)  # exact names, exact order
    assert listed["result"]["tools"] == listed_again["result"]["tools"]  # stable
    assert set(listed["result"]) == {"_meta", "cacheScope", "resultType", "tools", "ttlMs"}
    assert "nextCursor" not in listed["result"]  # no pagination: no hidden further tools
    assert set(discover["result"]["capabilities"]) == {"tools"}


@pytest.mark.parametrize("mode", NS_MODES)
def test_every_descriptor_has_the_exact_key_set_description_and_closed_schema(mode):
    tools = _discovery(mode)[1]["result"]["tools"]
    for tool in tools:
        assert set(tool) == {"name", "description", "inputSchema"}, tool["name"]
        assert tool["description"] == DESCRIPTIONS[tool["name"]], tool["name"]
        assert tool["inputSchema"] == INPUT_SCHEMAS[tool["name"]], tool["name"]
        # closed at every object level: no extra input property is accepted by the schema
        assert tool["inputSchema"]["additionalProperties"] is False
        for prop in tool["inputSchema"]["properties"].values():
            assert prop.get("additionalProperties", False) is False
    # no annotations, output schema, icons, or other extension fields are advertised
    assert all(set(tool) == {"name", "description", "inputSchema"} for tool in tools)


def test_server_capabilities_name_tools_only_so_resources_and_prompts_are_absent():
    discover = _discovery("host")[0]
    assert discover["result"]["capabilities"] == {"tools": {}}


@pytest.mark.parametrize(
    "method",
    [
        "resources/list",
        "resources/read",
        "resources/templates/list",
        "resources/subscribe",
        "prompts/list",
        "prompts/get",
        "completion/complete",
        "logging/setLevel",
        "sampling/createMessage",
        "roots/list",
        "elicitation/create",
        "tasks/list",
        "ping/extra",
    ],
)
def test_unadvertised_protocol_surface_is_method_not_found(method):
    out = launcher_batch([request(method, 1, {})])[1][0]
    assert_protocol_error(out, -32601, req_id=1)


@pytest.mark.parametrize(
    "name",
    [
        "genia_eval",
        "genia_exec",
        "genia_run_file",
        "genia_import",
        "genia_repl",
        "genia_test",
        "genia_format",
        "execution_process",
        "read_file",
        "genia_Run",
        "GENIA_RUN",
        " genia_run",
        "genia_run ",
        "genia_run\u0000",
        "genia-run",
        "",
    ],
)
def test_no_fourth_tool_and_no_host_only_tool_is_callable(name):
    out = launcher_batch([request("tools/call", 1, {"name": name, "arguments": {}})])[1][0]
    assert_protocol_error(out, -32602, req_id=1, message=UNKNOWN_TOOL_MESSAGE)


def test_tool_names_exist_only_in_native_genia_not_in_python_host_modules():
    native = (REPO_ROOT / "apps" / "mcp" / "mcp.genia").read_text(encoding="utf-8")
    quoted = set(re.findall(r'"(genia_[a-z_]+)"', native))
    assert {"genia_capabilities", "genia_parse", "genia_run"} <= quoted
    for path in sorted((REPO_ROOT / "hosts" / "python").glob("mcp_*.py")):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r'"genia_(capabilities|parse|run)"', text), path.name


@pytest.mark.parametrize("tool", sorted(INPUT_SCHEMAS))
@pytest.mark.parametrize(
    "extra", [{"mode": "file"}, {"argv": []}, {"extra": None}, {"Source": "1"}], ids=str
)
def test_no_extra_input_property_is_accepted_by_any_tool(tool, extra):
    arguments = dict(extra)
    if tool != "genia_capabilities":
        arguments["source"] = "1"
    out = launcher_batch([request("tools/call", 1, {"name": tool, "arguments": arguments})])[1][0]
    assert_protocol_error(out, -32602, req_id=1)


# --- D7: capabilities are truthful and do not claim an OS mechanism --------------------------

OS_CLAIM_WORDS = (
    "namespace",
    "unshare",
    "sandbox",
    "seccomp",
    "cgroup",
    "chroot",
    "container",
    "landlock",
    "jail",
    "rlimit",
)


@pytest.mark.parametrize("mode", NS_MODES)
def test_capabilities_describe_the_implemented_profile_and_claim_no_os_isolation(mode):
    response = _discovery(mode)[3]
    _, envelope = structured(response)
    assert envelope == expected_envelope(repository_revision(), tools=RUN_TOOLS)
    profile = envelope["result"]["execution_profile"]
    assert [profile[k] for k in ("filesystem", "environment", "configuration", "secrets", "network")] == [False] * 5
    assert profile["timeout_ms"] == 5000 and profile["source_max_bytes"] == SOURCE_LIMIT
    assert envelope["result"]["genia"]["portable_mcp_implementation"] is False
    assert envelope["result"]["genia"]["host"] == "python-reference"
    text = json.dumps(response).lower()
    for word in OS_CLAIM_WORDS:
        assert word not in text, f"capabilities must not mention {word!r} (best-effort OS layer)"


def test_capabilities_are_byte_identical_whether_the_namespace_is_granted_or_denied():
    host = _discovery("host")[3]["result"]["structuredContent"]
    denied = _discovery("denied")[3]["result"]["structuredContent"]
    assert host == denied


def test_capability_tools_agree_with_tools_list():
    _, listed, _, caps = _discovery("host")
    assert caps["result"]["structuredContent"]["result"]["tools"] == [
        tool["name"] for tool in listed["result"]["tools"]
    ]


# --- D8: the legacy handshake (ledger R28-H36; amendment A5 adds the 2025-11-25 era) ------------


def test_initialize_with_a_modern_meta_is_still_method_not_found_and_changes_nothing():
    messages = [
        request("tools/list", 1),
        request("initialize", 2, {"protocolVersion": "2025-11-25", "capabilities": {},
                                  "clientInfo": {"name": "c", "version": "0"}}),
        request("tools/list", 3),
    ]
    first, init, last = launcher_batch(messages)[1]
    assert_protocol_error(init, -32601, req_id=2)
    assert first["result"]["tools"] == last["result"]["tools"]


def test_the_compat_initialize_handshake_succeeds_and_serves_the_same_three_tools():
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "c", "version": "0"}}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        request("tools/list", 3),
    ]
    init, compat, modern = launcher_batch(messages)[1]
    assert init["result"]["protocolVersion"] == "2025-11-25"
    assert compat["result"]["tools"] == modern["result"]["tools"]


# --- P: genia_parse -----------------------------------------------------------------------

_OFFSET = re.compile(r" at (\d+)$")


def _direct_parse_envelope(source):
    parsed = parse_and_normalize(source)
    if parsed["kind"] == "ok":
        return {"schema_version": "genia.mcp.v1", "status": "ok",
                "result": {"kind": "parsed", "ast": parsed["ast"]}, "error": None}
    match = _OFFSET.search(parsed["message"])
    message = "Genia source failed to parse" + (f" at character offset {match.group(1)}" if match else "")
    return error_envelope("parse_error", "parse", message)


VALID = [
    "1",
    "x = 1",
    "f(x) = x + 1\nf(41)",
    "[1, 2, 3] |> map((x) -> x * 2)",
    '{"a": [1, {"b": none("nil")}]}',
    '"héllo 日本語 😀"',
    "# a comment only\n",
    "\n\n",
    "   ",
    "some(1)",
    'err("bad", {a: 1})',
]
INVALID = [
    "f(x) =",
    "1 +",
    "(1, ",
    "x = = 2",
    "f(x) = x |",
    "[1, 2",
    '"unterminated',
    "a ? ",
    "é = 1",  # Unicode identifiers are not supported by the parser today (matrix P6, limitation)
    "π = 3\nπ",
    "x = 1\ny = 2\nz = =",
    '"日本語" + ',
]


@pytest.mark.parametrize("mode", NS_MODES)
def test_valid_and_invalid_sources_match_the_existing_parse_surface_exactly(mode):
    sources = VALID + INVALID
    results = parse_sources(sources, mode)
    for source, (_, envelope) in zip(sources, results):
        assert envelope == _direct_parse_envelope(source), source


def test_empty_source_is_a_successful_empty_program():
    ((_, envelope),) = parse_sources([""])
    assert envelope == {"schema_version": "genia.mcp.v1", "status": "ok",
                        "result": {"kind": "parsed", "ast": []}, "error": None}


def test_syntax_errors_report_distinct_character_offsets_never_source_text():
    sources = ["f(x) =", "1 +", "(1, ", "x = = 2", "x = 1\ny = 2\nz = =", '"日本語" + ']
    results = parse_sources(sources)
    offsets = []
    for source, (response, envelope) in zip(sources, results):
        message = envelope["error"]["message"]
        assert re.fullmatch(r"Genia source failed to parse at character offset \d+", message)
        offsets.append(int(message.rsplit(" ", 1)[1]))
        assert envelope["result"] is None and envelope["error"]["phase"] == "parse"
        assert source.strip() not in json.dumps(response)  # no source echo
    assert len(set(offsets)) >= 4  # several offsets, not one constant


def test_offsets_are_characters_not_bytes():
    source = '"日本語😀" + '  # four multibyte characters before the failure
    ((_, envelope),) = parse_sources([source])
    direct = _OFFSET.search(parse_and_normalize(source)["message"]).group(1)
    assert envelope["error"]["message"].endswith(f"offset {direct}")
    assert int(direct) < len(source.encode("utf-8"))  # would differ if bytes were counted


def test_unicode_identifiers_fail_identically_to_the_direct_parser():
    # Matrix P6 (KNOWN LIMITATION): the parser does not accept non-ASCII identifiers today.
    # The adapter must reproduce that failure, not paper over it and not invent support.
    for source in ("é = 1\né", "π = 3", "x😀 = 1"):
        assert parse_and_normalize(source)["kind"] == "error", source
        ((_, envelope),) = parse_sources([source])
        assert envelope == _direct_parse_envelope(source)
        assert envelope["error"]["kind"] == "parse_error"


def test_unicode_string_literals_and_mixed_scripts_parse_like_the_direct_host():
    for source in ('"é"', '"日本語"', '"😀"', '{"ключ": "значение"}', '"á"', '" "'):
        ((_, envelope),) = parse_sources([source])
        assert envelope == _direct_parse_envelope(source), source


@pytest.mark.parametrize(
    "raw",
    [
        b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"genia_parse","arguments":{"source":"\\ud800"}}}',
        b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"genia_run","arguments":{"source":"\\udfff"}}}',
        b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"genia_parse","arguments":{"source":"\xff\xfe"}}}',
    ],
    ids=["lone-high-surrogate-parse", "lone-low-surrogate-run", "invalid-utf8-bytes"],
)
def test_invalid_unicode_is_rejected_at_the_json_rpc_boundary_and_the_stream_continues(raw):
    done = run_launcher_raw([raw, encode(request("tools/list", 2))])
    out = [json.loads(frame) for frame in frames(done.stdout)]
    assert out[0]["error"]["code"] == -32700 and "result" not in out[0]
    assert [t["name"] for t in out[1]["result"]["tools"]] == list(RUN_TOOLS)  # still serving


def _multibyte_literal(total_bytes):
    inner = total_bytes - 2
    assert inner % 2 == 0
    return '"' + "é" * (inner // 2) + '"'


def test_source_limit_is_utf8_bytes_one_below_exact_and_one_above():
    below = _multibyte_literal(SOURCE_LIMIT - 2)  # 262142 bytes
    exact = _multibyte_literal(SOURCE_LIMIT)  # 262144 bytes, only 131074 characters
    above = '"' + "é" * ((SOURCE_LIMIT - 2) // 2) + 'x"'  # 262145 bytes: one over
    assert [len(s.encode("utf-8")) for s in (below, exact, above)] == [SOURCE_LIMIT - 2, SOURCE_LIMIT, SOURCE_LIMIT + 1]
    assert len(exact) < SOURCE_LIMIT  # a character count would have accepted every case
    results = parse_sources([below, exact, above])
    assert [env["status"] for _, env in results] == ["ok", "ok", "error"]
    assert results[2][1] == error_envelope(
        "input_limit", "protocol", "Genia source exceeds the 262144-byte limit"
    )
    assert results[2][1]["result"] is None


LARGE_INTEGER_SOURCES = [
    "9007199254740991",
    "9007199254740992",
    "9007199254740993",
    "18446744073709551616",
    "x = 99999999999999999999999999999999999999999999",
    "9007199254740992 + 123456789012345678901234567890",
    "1\n9007199254740993",
    # The normalized surface collapses unary/list/map nodes to their kind (ledger R28-H23),
    # so these carry no digits; equality with the direct surface is still required.
    "[9007199254740991, 9007199254740992, 9007199254740993]",
    "-123456789012345678901234567890",
    "{a: 340282366920938463463374607431768211456}",
]


def _integers(ast):
    if isinstance(ast, dict):
        for value in ast.values():
            yield from _integers(value)
    elif isinstance(ast, list):
        for value in ast:
            yield from _integers(value)
    elif isinstance(ast, int) and not isinstance(ast, bool):
        yield ast


@pytest.mark.parametrize("source", LARGE_INTEGER_SOURCES)
def test_large_exact_integers_stay_exact_in_the_ast_and_never_pass_through_r9_json(source):
    expected = parse_and_normalize(source)["ast"]
    out = run_launcher_raw([encode(parse_request(source, 1))])
    (frame,) = frames(out.stdout)
    text = frame.decode("utf-8")
    ast = structured(json.loads(text))[1]["result"]["ast"]
    assert ast == expected  # exact Python integers: no float rounding, no stringification
    assert all(type(n) is int for n in _integers(ast))
    for number in _integers(expected):
        if abs(number) > 9007199254740991:  # beyond the R9 safe-integer interval
            assert f'"value": {number}' in text or f'"value":{number}' in text
            assert f'"{number}"' not in text and f"{number}.0" not in text


def test_parse_is_deterministic_across_calls_and_independent_launches():
    sources = ["f(x) = x * 2\nf(21)", "y = =", "9007199254740993", '"é"']
    messages = [parse_request(s, i) for i, s in enumerate(sources)]
    first = run_launcher_raw([encode(m) for m in messages]).stdout
    second = run_launcher_raw([encode(m) for m in messages]).stdout
    again = run_launcher_raw([encode(m) for m in messages + messages]).stdout
    assert first == second  # byte-identical frames across independent server launches
    assert again.startswith(first)


def test_parsing_never_evaluates_or_acquires_authority(tmp_path):
    marker = tmp_path / "marker"
    sources = [
        f'write_file("{marker}", "x")',
        f'"x" |> $(touch {marker})',
        "import web\n1",
        'read_file("/etc/hostname")',
        'secret_get("K")',
        "loop(n) = loop(n + 1)\nloop(0)",
    ]
    results = parse_sources(sources)
    assert [env["status"] for _, env in results] == ["ok"] * len(sources)
    assert not marker.exists()


def test_parse_failure_for_hostile_text_is_bounded_and_echo_free():
    hostile = "= " + "SENTINEL_" * 5000 + "/home/secret/path"
    ((response, envelope),) = parse_sources([hostile])
    assert envelope["status"] == "error" and envelope["error"]["kind"] == "parse_error"
    assert "SENTINEL_" not in json.dumps(response) and "/home/secret" not in json.dumps(response)
    assert len(envelope["error"]["message"].encode()) <= 65536  # diagnostic bound (contract 5)
    assert_closed_failure(response, "parse_error", "parse", envelope["error"]["message"])


def test_parse_authority_is_independent_of_run_policy():
    # `genia_parse` accepts source that `genia_run` denies: parsing acquires no authority.
    source = 'read_file("/etc/hostname")'
    ((_, parsed),) = parse_sources([source])
    run_out = launcher_batch([run_request(source, 1)])[1][0]
    assert parsed["status"] == "ok"
    assert structured(run_out)[1]["error"]["kind"] == "policy_denied"
