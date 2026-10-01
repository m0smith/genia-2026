"""R28 E28-2 (issue #703): `genia_parse` over the native Genia MCP server.

Pinned to docs/design/r28-e28-2-parse-tool-design.md (§3.3, §3.4) and contract
§2.4 with Clarification A2 (§15). The parse capability is provisioned only by the
host launcher; plain CLI mode keeps the E28-1 surface. Expected to fail until the
E28-2 implementation lands (failing-test phase).
"""

from __future__ import annotations

import glob
import json
import re
import tempfile
from functools import lru_cache
from pathlib import Path

import pytest
import yaml

from hosts.python.parse_adapter import parse_and_normalize
from tests.fixtures.r28_mcp_helpers import (
    PARSE_TOOLS,
    REPO_ROOT,
    UNKNOWN_TOOL_MESSAGE,
    assert_protocol_error,
    call,
    encode,
    error_envelope,
    expected_envelope,
    frames,
    launcher_call,
    parse_request,
    repository_revision,
    request,
    responses,
    run_launcher_raw,
)

pytestmark = pytest.mark.unit

SOURCE_LIMIT = 262144
PARSE_DESCRIPTOR_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["source"],
    "properties": {"source": {"type": "string", "maxLength": SOURCE_LIMIT}},
}
INPUT_LIMIT = error_envelope(
    "input_limit", "protocol", "Genia source exceeds the 262144-byte limit"
)
RESULT_LIMIT = error_envelope(
    "result_limit", "adapter", "Result exceeds the 3276800-byte limit"
)
INTERNAL = error_envelope("internal_error", "adapter", "Internal error while parsing")
_OFFSET = re.compile(r" at (\d+)$")


def _spec_cases():
    cases = []
    for path in sorted(glob.glob(str(REPO_ROOT / "spec" / "parse" / "*.yaml"))):
        case = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        source = case["input"]["source"] if isinstance(case["input"], dict) else case["input"]
        cases.append((Path(path).stem, source))
    return cases


SPEC_CASES = _spec_cases()


def _expected_for(source):
    parsed = parse_and_normalize(source)
    if parsed["kind"] == "ok":
        return {
            "schema_version": "genia.mcp.v1",
            "status": "ok",
            "result": {"kind": "parsed", "ast": parsed["ast"]},
            "error": None,
        }
    assert parsed["type"] == "SyntaxError", parsed
    match = _OFFSET.search(parsed["message"])
    message = "Genia source failed to parse"
    if match:
        message += f" at character offset {match.group(1)}"
    return error_envelope("parse_error", "parse", message)


@lru_cache(maxsize=None)
def _spec_responses():
    messages = [parse_request(source, i) for i, (_, source) in enumerate(SPEC_CASES)]
    out = responses(run_launcher_raw([encode(m) for m in messages]))
    return {r["id"]: r for r in out}


def _tool_result(response):
    assert set(response) == {"jsonrpc", "id", "result"}, response
    result = response["result"]
    assert result["resultType"] == "complete"
    (item,) = result["content"]
    assert item["type"] == "text" and "\n" not in item["text"]
    assert json.loads(item["text"]) == result["structuredContent"]
    return result


# --- surface: CLI mode unchanged, launcher mode adds genia_parse ---------------


def test_cli_mode_without_capability_keeps_the_e28_1_surface():
    listed = call(request("tools/list", 1))["result"]["tools"]
    assert [tool["name"] for tool in listed] == ["genia_capabilities"]
    response = call(parse_request("x = 1", 2))
    assert_protocol_error(response, -32602, req_id=2, message=UNKNOWN_TOOL_MESSAGE)


def test_launcher_mode_advertises_parse_with_the_exact_closed_schema():
    listed = launcher_call(request("tools/list", 1))["result"]["tools"]
    assert [tool["name"] for tool in listed] == list(PARSE_TOOLS)
    descriptor = listed[1]
    assert set(descriptor) == {"name", "description", "inputSchema"}
    assert isinstance(descriptor["description"], str) and descriptor["description"]
    assert descriptor["inputSchema"] == PARSE_DESCRIPTOR_SCHEMA


def test_launcher_mode_capabilities_report_the_advertised_tools():
    response = launcher_call(request("tools/call", 1, {"name": "genia_capabilities"}))
    structured = _tool_result(response)["structuredContent"]
    assert structured == expected_envelope(repository_revision(), tools=PARSE_TOOLS)


# --- parse parity with the existing normalized parse surface -------------------


@pytest.mark.parametrize("name,source", SPEC_CASES, ids=[name for name, _ in SPEC_CASES])
def test_parse_matches_the_existing_parse_surface(name, source):
    index = [n for n, _ in SPEC_CASES].index(name)
    result = _tool_result(_spec_responses()[index])
    expected = _expected_for(source)
    assert result["structuredContent"] == expected
    assert result["isError"] is (expected["status"] == "error")


# --- H22 / Clarification A3: lossless AST transport beyond the R9 range -------------

LARGE_INTEGER_SOURCES = [
    "9007199254740991",
    "9007199254740992",
    "9007199254740993",
    "123456789012345678901234567890",
    "x = 123456789012345678901234567890",
    "9007199254740992 + 123456789012345678901234567890",
    "1\n9007199254740992",
]


def _digits(ast):
    if isinstance(ast, dict):
        for value in ast.values():
            yield from _digits(value)
    elif isinstance(ast, list):
        for value in ast:
            yield from _digits(value)
    elif isinstance(ast, int) and not isinstance(ast, bool):
        yield ast


@pytest.mark.parametrize("source", LARGE_INTEGER_SOURCES)
def test_large_integer_ast_matches_the_existing_parse_surface_exactly(source):
    expected = parse_and_normalize(source)["ast"]
    response = launcher_call(parse_request(source))
    result = _tool_result(response)
    envelope = result["structuredContent"]
    assert envelope["status"] == "ok" and result["isError"] is False
    assert envelope["result"] == {"kind": "parsed", "ast": expected}
    assert envelope["error"] is None
    # No integer-to-string mutation and no rounding: Python decodes integer tokens exactly.
    assert sorted(_digits(envelope["result"]["ast"])) == sorted(_digits(expected))
    assert all(type(n) is int for n in _digits(envelope["result"]["ast"]))


@pytest.mark.parametrize(
    "literal",
    ["9007199254740991", "9007199254740992", "123456789012345678901234567890"],
)
def test_large_integer_is_an_exact_json_number_token_on_the_wire(literal):
    out = run_launcher_raw([encode(parse_request(literal, 1))])
    (line,) = frames(out.stdout)  # exactly one single-line frame
    assert f'"value": {literal}'.encode() in line or f'"value":{literal}'.encode() in line
    assert f'"{literal}"'.encode() not in line  # never stringified
    # The text content item carries the same exact token (JSON-string-escaped).
    text = json.loads(line)["result"]["content"][0]["text"]
    assert f'"value": {literal}' in text and f'"{literal}"' not in text


def test_small_and_large_integers_in_one_session_do_not_interfere():
    messages = [
        parse_request("9007199254740992", 1),
        parse_request("x = 1", 2),
        parse_request("y = = 2", 3),
        parse_request("9007199254740992", 4),
    ]
    out = responses(run_launcher_raw([encode(m) for m in messages]))
    assert out[0]["result"] == out[3]["result"]
    assert out[1]["result"]["structuredContent"]["status"] == "ok"
    assert out[2]["result"]["structuredContent"]["error"]["kind"] == "parse_error"


def test_large_integer_ast_is_not_an_internal_error():
    result = _tool_result(launcher_call(parse_request("123456789012345678901234567890")))
    assert result["structuredContent"]["error"] is None
    assert result["structuredContent"] != INTERNAL


def test_parse_success_shape():
    result = _tool_result(launcher_call(parse_request("x = 1")))
    assert result["isError"] is False
    assert result["structuredContent"] == {
        "schema_version": "genia.mcp.v1",
        "status": "ok",
        "result": {
            "kind": "parsed",
            "ast": {"kind": "Assign", "name": "x", "value": {"kind": "Literal", "value": 1}},
        },
        "error": None,
    }


def test_parse_error_carries_offset_only_never_source_or_host_text():
    source = "f(x) = x | SENTINEL_TOKEN_QQQ ="
    result = _tool_result(launcher_call(parse_request(source)))
    assert result["isError"] is True
    structured = result["structuredContent"]
    assert structured == _expected_for(source)
    text = json.dumps(structured)
    for leak in ("SENTINEL_TOKEN_QQQ", "SyntaxError", "Traceback", "Unexpected", "|"):
        assert leak not in text


# --- limits (contract §2.4, §5; Clarification A2) ------------------------------


def _largest_literal_within_limit(char):
    width = len(char.encode("utf-8"))
    source = '"' + char * ((SOURCE_LIMIT - 2) // width) + '"'
    size = len(source.encode("utf-8"))
    assert size <= SOURCE_LIMIT and SOURCE_LIMIT - size < width
    return source


@pytest.mark.parametrize("char", ["a", "\u00e9", "\u4e2d", "\U0001f600"])
def test_source_at_the_byte_limit_parses(char):
    source = _largest_literal_within_limit(char)
    if char == "a":
        assert len(source.encode("utf-8")) == SOURCE_LIMIT
    result = _tool_result(launcher_call(parse_request(source)))
    assert result["structuredContent"]["status"] == "ok"


@pytest.mark.parametrize("char", ["a", "\u00e9"])
def test_source_one_byte_over_the_limit_is_input_limit(char):
    width = len(char.encode())
    body = (SOURCE_LIMIT - 2) // width + 1
    source = '"' + char * body + '"'
    assert len(source.encode("utf-8")) > SOURCE_LIMIT
    result = _tool_result(launcher_call(parse_request(source)))
    assert result["structuredContent"] == INPUT_LIMIT
    assert result["isError"] is True


def test_oversized_source_is_rejected_before_parsing():
    # Invalid Genia that is too large: input_limit (not parse_error) proves the
    # capability was never asked to parse it.
    source = "= " * (SOURCE_LIMIT // 2 + 1)
    result = _tool_result(launcher_call(parse_request(source)))
    assert result["structuredContent"] == INPUT_LIMIT


def test_oversized_result_is_result_limit_and_discards_the_ast():
    source = "a=1\n" * (SOURCE_LIMIT // 4)
    assert len(source.encode("utf-8")) == SOURCE_LIMIT
    result = _tool_result(launcher_call(parse_request(source), timeout=300))
    assert result["structuredContent"] == RESULT_LIMIT
    assert "Assign" not in result["content"][0]["text"]


def test_invalid_unicode_is_a_protocol_parse_error_not_input_limit():
    # Clarification A2: malformed JSON never reaches genia_parse.
    raw = (
        b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"genia_parse",'
        b'"arguments":{"source":"\\ud800"},"_meta":{"io.modelcontextprotocol/protocolVersion":'
        b'"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}'
    )
    (response,) = responses(run_launcher_raw([raw]))
    assert_protocol_error(response, -32700, req_id=None)


# --- arguments ------------------------------------------------------------------


@pytest.mark.parametrize(
    "arguments",
    [None, {}, {"source": 5}, {"source": None}, {"source": ["x"]}, {"source": "x", "extra": 1}],
)
def test_parse_arguments_are_closed(arguments):
    params = {"name": "genia_parse"}
    if arguments is not None:
        params["arguments"] = arguments
    response = launcher_call(request("tools/call", 4, params))
    assert_protocol_error(response, -32602, req_id=4)


# --- no evaluation, no authority -------------------------------------------------


def test_parsing_never_evaluates_or_acquires_authority():
    with tempfile.TemporaryDirectory() as tmp:
        marker = Path(tmp) / "created-by-evaluation"
        source = (
            'print("SIDE-EFFECT-SENTINEL")\n'
            f'write_file("{marker}", "x")\n'
            "import web\n"
            "web.http_send(1, 2, 3)\n"
        )
        completed = run_launcher_raw([encode(parse_request(source))])
        assert completed.returncode == 0
        (frame,) = frames(completed.stdout)
        assert b"SIDE-EFFECT-SENTINEL" not in completed.stderr
        assert json.loads(frame)["result"]["structuredContent"]["status"] == "ok"
        assert not marker.exists()


def test_parser_internal_failure_is_internal_error_with_fixed_message():
    source = "(" * 3000 + "1" + ")" * 3000  # RecursionError inside the parser
    result = _tool_result(launcher_call(parse_request(source)))
    assert result["structuredContent"] == INTERNAL
    assert "Recursion" not in result["content"][0]["text"]


def test_parse_is_deterministic_and_stateless():
    messages = [parse_request("x = 1", 1), parse_request("y = = 2", 2), parse_request("x = 1", 3)]
    out = responses(run_launcher_raw([encode(m) for m in messages]))
    assert out[0]["result"] == out[2]["result"]
