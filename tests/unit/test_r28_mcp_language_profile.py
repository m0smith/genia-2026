"""R28 amendments A6/A7: the `genia_language_profile` MCP tool.

Python-host tests of the MCP adapter boundary (launcher/stdio wire behavior) for a tool defined
entirely in `apps/mcp/mcp.genia`. They add no Genia semantics: the profile is static adapter text,
and every claim it makes about the language is cross-checked here against direct command-source
evaluation by the Python reference host.
"""

from __future__ import annotations

import json
import re

import pytest

from genia.interpreter import make_global_env, run_source
from tests.fixtures.r28_mcp_conformance import ERAS, NS_MODES, launcher_batch, structured_era
from tests.fixtures.r28_mcp_helpers import (
    PROFILE_TOOL,
    REPO_ROOT,
    REVISION,
    RUN_TOOLS,
    assert_protocol_error,
    compat_handshake,
    request,
    repository_revision,
    run_messages,
    responses,
    structured,
)

pytestmark = pytest.mark.unit

PROFILE_CALL = request("tools/call", 3, {"name": PROFILE_TOOL})
GCD = "open gcd(a, 0) = a\ngcd(a, b) = gcd(b, a % b)\ngcd(48, 18)"
FACT = "open fact(0) = 1\nfact(n) = n * fact(n - 1)\nfact(5)"
TOP_LEVEL_KEYS = [
    "name",
    "contract_revision",
    "control_flow",
    "supported_forms",
    "patterns",
    "absent_forms",
    "idioms",
    "examples",
    "discovery",
]


def _profile(mode="host", revision=None):
    _, out = launcher_batch([PROFILE_CALL], mode)
    _, envelope = structured(out[0])
    assert envelope["status"] == "ok" and envelope["error"] is None
    assert envelope["schema_version"] == "genia.mcp.v1"
    assert set(envelope["result"]) == {"language"}
    return envelope["result"]["language"]


def _direct(source):
    return run_source(source, make_global_env(), filename="<command>")


# --- discovery -------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", NS_MODES)
def test_tools_list_includes_the_profile_tool_in_contract_order(mode):
    _, out = launcher_batch([request("tools/list", 1)], mode)
    tools = out[0]["result"]["tools"]
    assert [t["name"] for t in tools] == ["genia_capabilities", "genia_parse", "genia_run", "genia_language_profile"]
    assert [t["name"] for t in tools] == list(RUN_TOOLS)
    (descriptor,) = [t for t in tools if t["name"] == PROFILE_TOOL]
    assert set(descriptor) == {"name", "description", "inputSchema"}
    assert descriptor["inputSchema"] == {"type": "object", "additionalProperties": False, "properties": {}}


@pytest.mark.parametrize("mode", NS_MODES)
def test_capabilities_tools_agree_with_tools_list(mode):
    _, out = launcher_batch([request("tools/list", 1), request("tools/call", 2, {"name": "genia_capabilities"})], mode)
    listed = [t["name"] for t in out[0]["result"]["tools"]]
    _, envelope = structured(out[1])
    assert envelope["result"]["tools"] == listed
    assert listed[-1] == PROFILE_TOOL


def test_plain_file_mode_advertises_the_profile_without_any_host_capability():
    out = responses(run_messages([request("tools/list", 1), PROFILE_CALL]))
    assert [t["name"] for t in out[0]["result"]["tools"]] == ["genia_capabilities", PROFILE_TOOL]
    _, envelope = structured(out[1])
    assert envelope["status"] == "ok"


# --- argument policy -------------------------------------------------------------------------


@pytest.mark.parametrize("arguments", [None, {}], ids=["omitted", "empty-object"])
def test_omitted_or_empty_arguments_are_accepted(arguments):
    params = {"name": PROFILE_TOOL}
    if arguments is not None:
        params["arguments"] = arguments
    _, out = launcher_batch([request("tools/call", 1, params)])
    _, envelope = structured(out[0])
    assert envelope["status"] == "ok"


@pytest.mark.parametrize(
    "arguments",
    [{"source": "1"}, {"x": 1}, {"mode": "file"}, {"verbose": True}, {"": None}, [], "x", 5, None],
    ids=str,
)
def test_any_non_empty_or_non_object_arguments_are_invalid_params(arguments):
    _, out = launcher_batch([request("tools/call", 1, {"name": PROFILE_TOOL, "arguments": arguments})])
    assert_protocol_error(out[0], -32602, req_id=1)


# --- the profile content ---------------------------------------------------------------------


def test_profile_member_set_and_order_are_exact():
    language = _profile()
    assert set(language) == set(TOP_LEVEL_KEYS)  # the encoder sorts members; order is not a claim
    assert language["name"] == "Genia"
    assert set(language["control_flow"]) == {
        "conditionals",
        "if_expression",
        "loops",
        "recursion",
        "tail_call_optimization",
    }


def test_profile_states_pattern_matching_branching_and_no_if_or_loops():
    flow = _profile()["control_flow"]
    assert flow["conditionals"] == "pattern_matching"
    assert flow["if_expression"] is False
    assert flow["loops"] is False
    assert flow["recursion"] is True
    assert flow["tail_call_optimization"] is True


def test_profile_pattern_and_form_claims():
    language = _profile()
    assert language["patterns"] == {
        "function_argument_patterns": True,
        "literal_patterns": True,
        "wildcard_patterns": True,
        "tuple_patterns": True,
        "list_patterns": True,
        "map_patterns": True,
        "guard_patterns": True,
        "ordered_resolution": "first_match",
    }
    assert language["absent_forms"] == ["if_expression", "while_loop", "for_loop"]
    for form in ("function_definition", "pattern_dispatch", "case_expression", "pipeline"):
        assert form in language["supported_forms"]
    assert not set(language["absent_forms"]) & set(language["supported_forms"])
    assert "pattern" in language["idioms"]["branching"].lower()
    assert "recursion" in language["idioms"]["repetition"].lower()
    pipelines = language["idioms"]["pipelines"]
    for term in ("|>", "keep_some", "some", "none", "err"):
        assert term in pipelines
    assert "define" in pipelines


def test_validated_pipeline_fact_is_13th_experimental_and_scoped_to_state_section_6():
    # A9 (#1084) appends the 14th fact after it, so it is no longer last.
    fact = _profile()["discovery"]["facts"][12]
    assert fact["id"] == "validated_data_pipelines"
    assert (fact["scope"], fact["status"], fact["maturity"], fact["state_sections"]) == ("language", "implemented", "Experimental", ["6"])
    assert "callers define" in fact["summary"]
    for overclaim in ("complete", "fully", "all "):
        assert overclaim not in fact["summary"].lower()


def test_profile_contract_revision_is_the_one_capabilities_reports():
    _, out = launcher_batch([PROFILE_CALL, request("tools/call", 4, {"name": "genia_capabilities"})])
    revision = structured(out[1])[1]["result"]["genia"]["contract_revision"]
    assert revision == repository_revision()
    assert structured(out[0])[1]["result"]["language"]["contract_revision"] == revision


def test_plain_file_mode_reports_its_launch_revision():
    (response,) = responses(run_messages([PROFILE_CALL], args=(REVISION,)))
    assert structured(response)[1]["result"]["language"]["contract_revision"] == REVISION


def test_the_gcd_example_is_the_canonical_pattern_matching_spelling():
    gcd = _profile()["examples"]["gcd"]
    assert gcd == GCD
    assert not re.search(r"\b(if|then|else|while|for)\b", gcd)
    assert "gcd(a, 0) = a" in gcd and "gcd(b, a % b)" in gcd


def test_every_profile_example_evaluates_as_documented_by_direct_evaluation():
    examples = _profile()["examples"]
    assert set(examples) == {"gcd", "factorial"}
    assert examples["factorial"] == FACT
    assert _direct(examples["gcd"]) == 6
    assert _direct(examples["factorial"]) == 120


def test_the_direct_evaluation_helper_really_evaluates():
    assert _direct("1 + 2") == 3  # guards the must-fail tests below against a broken helper


def test_the_requested_literal_spelling_without_open_is_not_valid_genia():
    # The profile must not teach text the language rejects: a literal first-parameter clause needs `open`.
    with pytest.raises(Exception):
        _direct("gcd(a, 0) = a\ngcd(a, b) = gcd(b, a % b)\ngcd(48, 18)")


def test_the_absent_forms_really_are_absent_in_the_language():
    for source in ("if(true, 1, 2)", "while(true, 1)", "for(1, 2)"):
        with pytest.raises(Exception):
            _direct(source)


def test_tail_recursion_claim_holds_in_constant_stack():
    assert _direct("open count(0, acc) = acc\ncount(n, acc) = count(n - 1, acc + 1)\ncount(100000, 0)") == 100000


# --- determinism, eras, and surface closure --------------------------------------------------


def test_profile_is_byte_identical_across_calls_and_namespace_modes():
    frames_seen = set()
    for mode in NS_MODES:
        stdout, out = launcher_batch([PROFILE_CALL, PROFILE_CALL], mode)
        lines = stdout.split(b"\n")
        assert lines[0] == lines[1]
        frames_seen.add(lines[0])
    assert len(frames_seen) == 1


@pytest.mark.parametrize("mode", NS_MODES)
def test_the_profile_is_identical_in_both_protocol_eras(mode):
    modern = structured_era(launcher_batch([PROFILE_CALL], mode)[1][0], "modern")[1]
    messages = [*compat_handshake(), {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": PROFILE_TOOL}}]
    compat = structured_era(launcher_batch(messages, mode)[1][-1], "compat")[1]
    assert modern == compat
    assert ERAS == ("modern", "compat")


def test_text_content_is_the_same_envelope_as_structured_content():
    _, out = launcher_batch([PROFILE_CALL])
    result = out[0]["result"]
    assert json.loads(result["content"][0]["text"]) == result["structuredContent"]
    assert result["isError"] is False


def test_the_tool_introduces_no_resources_or_prompts_surface():
    _, out = launcher_batch(
        [request("server/discover", 1), request("resources/list", 2, {}), request("prompts/list", 3, {})]
    )
    assert out[0]["result"]["capabilities"] == {"tools": {}}
    assert_protocol_error(out[1], -32601, req_id=2)
    assert_protocol_error(out[2], -32601, req_id=3)


def test_the_profile_literals_live_only_in_native_genia():
    native = (REPO_ROOT / "apps" / "mcp" / "mcp.genia").read_text(encoding="utf-8")
    assert PROFILE_TOOL in native and "first_match" in native
    for path in sorted((REPO_ROOT / "hosts" / "python").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert PROFILE_TOOL not in text and "first_match" not in text, path.name


# A7 contract values: independent wire oracle. The golden snapshot was captured from the
# pre-registry implementation (#1099) and is test data, not generated from the registry,
# so a registry/generator defect cannot silently move the wire.
GOLDEN_PATH = REPO_ROOT / "tests" / "data" / "mcp_language_profile.golden.json"
GOLDEN = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
DISCOVERY_FACTS = GOLDEN["discovery"]["facts"]


def test_discovery_is_the_exact_closed_scoped_catalogue():
    discovery = _profile()["discovery"]
    assert discovery == {"coverage": "curated_non_exhaustive", "facts": DISCOVERY_FACTS}
    assert set(discovery) == {"coverage", "facts"}
    assert len(discovery["facts"]) == 14  # A9 (#1084): 13 -> 14
    assert len({fact["id"] for fact in discovery["facts"]}) == 14
    assert len(json.dumps(discovery, ensure_ascii=False).encode("utf-8")) <= 16384
    for fact in discovery["facts"]:
        assert set(fact) == {"id", "scope", "status", "maturity", "summary", "state_sections"}
        assert fact["status"] in {"implemented", "partial", "planned", "scaffolded", "unsupported"}
        assert fact["maturity"] in {None, "Experimental", "Partial", "Stable"}
        assert 0 < len(fact["summary"].encode("utf-8")) <= 256
        assert fact["state_sections"] and all(isinstance(s, str) for s in fact["state_sections"])


def test_discovery_plain_file_mode_matches_launcher_without_host_authority():
    (response,) = responses(run_messages([PROFILE_CALL], args=(REVISION,)))
    assert structured(response)[1]["result"]["language"]["discovery"] == _profile()["discovery"]


def test_discovery_does_not_expand_capabilities_payload():
    _, out = launcher_batch([request("tools/call", 4, {"name": "genia_capabilities"})])
    capabilities = structured(out[0])[1]["result"]
    assert set(capabilities) == {"server", "mcp", "genia", "tools", "execution_profile"}
    assert set(capabilities["genia"]) == {"host", "contract_revision", "portable_mcp_implementation"}
    assert capabilities["genia"]["portable_mcp_implementation"] is False
    assert capabilities["tools"] == list(RUN_TOOLS)


@pytest.mark.parametrize("fact", DISCOVERY_FACTS, ids=lambda fact: fact["id"])
def test_discovery_fact_matches_the_golden_wire_snapshot(fact):
    # STATE authority for each claim is verified structurally by the registry tests
    # (tests/doc/test_state_anchors_and_registry_sync.py); here the wire row must be exact.
    observed = {row["id"]: row for row in _profile()["discovery"]["facts"]}
    assert observed[fact["id"]] == fact


def test_whole_profile_equals_the_golden_snapshot_except_the_launch_revision():
    language = _profile()
    language.pop("contract_revision")
    assert language == {k: v for k, v in GOLDEN.items()}


def test_discovery_literals_remain_native_application_data():
    native = (REPO_ROOT / "apps" / "mcp" / "mcp.genia").read_text(encoding="utf-8")
    assert "curated_non_exhaustive" in native
    for path in sorted((REPO_ROOT / "hosts" / "python").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "curated_non_exhaustive" not in text, path.name
        assert all(fact["id"] not in text for fact in DISCOVERY_FACTS), path.name
