"""R28 amendment A9 (#1084): Outcome propagation content of `genia_language_profile`.

Python-host tests of the MCP adapter boundary and of build-time governance. They add no Genia
semantics; every claim the profile makes is cross-checked against direct command-source evaluation
by the Python reference host. Contract: amendment A9 in
`docs/design/r28-genia-mcp-contract-threat-model.md`.

RED PHASE (intentional): the tests in the "A9 wire" and "A9 registry" groups fail until the
implementation phase adds `idioms.outcomes`, the `outcome_pipeline_propagation` fact, and the
registry entries. The "Genia already implements" group passes today and must keep passing; it is the
evidence the new content restates. The exact strings below are an independent oracle copied from the
contract, never generated from the registry.
"""

from __future__ import annotations

import json
import re

import pytest

from genia.interpreter import make_global_env, run_source
from tools import gen_mcp_language_profile as gen
from tests.unit.test_r28_mcp_language_profile import DISCOVERY_FACTS, GOLDEN, PROFILE_CALL, _profile
from tests.fixtures.r28_mcp_conformance import launcher_batch
from tests.fixtures.r28_mcp_helpers import (
    PROFILE_TOOL,
    REVISION,
    RUN_TOOLS,
    SERVER_PATH,
    request,
    responses,
    run_messages,
    structured,
)

pytestmark = pytest.mark.unit

A9_IDIOM = (
    "Outcomes are values: some(x) is present, none(...) is absent, and err(reason) is a recoverable failure "
    "that is not absence. In |> pipelines an ordinary stage receives x from some(x) and its plain result is "
    "wrapped back into some, while none and err skip the remaining stages and are returned unchanged. A direct "
    "call passes the Outcome itself as the argument, except that a none argument short-circuits an ordinary "
    "call. Recover around the expression, as in unwrap_or(0, parse_int(s)), not as a later |> stage."
)
A9_FACT = {
    "id": "outcome_pipeline_propagation",
    "scope": "language",
    "status": "implemented",
    "maturity": "Experimental",
    "summary": (
        "Experimental: in |> pipelines ordinary stages lift over some and none or err skip later stages "
        "unchanged; err is not absence; a direct call receives the Outcome itself; recover with unwrap_or "
        "around the whole expression."
    ),
    "state_sections": ["2", "3"],
}
FACT_IDS_BEFORE_A9 = [
    "pattern_branching",
    "tail_calls",
    "if_and_loops",
    "flow_shared_coverage",
    "core_ir_stability",
    "cpp_language_floor",
    "other_language_hosts",
    "browser_runtime",
    "mcp_surface",
    "cpp_mcp",
    "windows_mcp",
    "macos_hardening",
    "validated_data_pipelines",
]
REGISTRY = gen.load_registry()


def _direct(source):
    """Evaluate `source` as command source on the Python reference host and return the host value."""
    return run_source(source, make_global_env(), filename="<command>")


def _shown(source):
    """Return the evaluated value's string form with double quotes, so Outcome text matches the CLI display."""
    return str(_direct(source)).replace("'", '"')


# --- Genia already implements this (passes today; the evidence A9 restates) ----------------------

INC = "inc(x) = x + 1\n"


def test_the_direct_evaluation_helper_really_evaluates():
    assert _direct("1 + 2") == 3  # guards the negative assertions below against a broken helper


def test_pipeline_lifts_an_ordinary_stage_over_some_and_wraps_the_result_back():
    assert _shown(INC + "some(1) |> inc") == "some(2)"
    assert _shown(INC + "some(1) |> inc |> inc") == "some(3)"


def test_none_and_err_skip_later_stages_and_are_returned_unchanged():
    assert _shown(INC + 'none("m") |> inc') == 'none("m")'
    assert _shown(INC + 'err("bad") |> inc') == 'err("bad")'
    assert (
        _shown(INC + 'err("bad") |> inc |> inc') == 'err("bad")'
    )  # still err, never converted to none


def test_a_direct_call_passes_the_outcome_itself_and_is_not_lifted():
    direct = _shown(INC + "inc(some(1))")
    assert direct != "some(2)"
    assert direct.startswith(
        "none("
    )  # `some(1) + 1` is a type error surfaced as absence, not a lifted result


def test_a_none_argument_short_circuits_an_ordinary_direct_call():
    assert _shown(INC + 'inc(none("m"))') == 'none("m")'


def test_err_is_not_absence():
    assert _direct('none?(err("e"))') is False
    assert _direct('is_some?(err("e"))') is False
    assert _shown('err("e")') == 'err("e")'


def test_recovery_wraps_the_whole_expression_and_a_later_stage_does_not_recover():
    assert _direct('unwrap_or(0, parse_int("x"))') == 0
    assert _direct('unwrap_or(0, parse_int("7"))') == 7
    assert _shown('parse_int("x") |> unwrap_or(0)').startswith("none(")


def test_the_idiom_example_in_the_contract_is_valid_genia_with_the_documented_result():
    assert _direct('s = "x"\nunwrap_or(0, parse_int(s))') == 0


# --- A9 wire (RED until implementation) -----------------------------------------------------------


def test_a9_idioms_gain_exactly_the_outcomes_member():
    idioms = _profile()["idioms"]
    assert set(idioms) == {"branching", "clauses", "flow", "outcomes", "pipelines", "repetition"}  # A10 adds `flow`


def test_a9_outcomes_idiom_is_the_exact_contract_text():
    assert _profile()["idioms"]["outcomes"] == A9_IDIOM
    assert len(A9_IDIOM.encode("utf-8")) == 510 <= 600


def test_a9_outcomes_idiom_states_the_documented_distinctions():
    text = _profile()["idioms"]["outcomes"]
    for term in (
        "some(x)",
        "none(...)",
        "err(reason)",
        "not absence",
        "|>",
        "direct call",
        "unwrap_or(0, parse_int(s))",
    ):
        assert term in text, term
    for overclaim in (r"\ball\b", r"\balways\b", r"\bcomplete", r"\bfully\b"):  # word-bounded: "call" is not "all"
        assert not re.search(overclaim, text.lower()), overclaim


def test_a9_existing_idioms_are_unchanged():
    idioms = _profile()["idioms"]
    for key in ("branching", "clauses", "pipelines", "repetition"):
        assert idioms[key] == GOLDEN["idioms"][key]


def test_a9_discovery_grows_from_13_to_exactly_14_facts_with_the_new_fact_last():
    facts = _profile()["discovery"]["facts"]
    # A10 (#1084) appends a 15th fact after the A9 one, so A9's fact is no longer last.
    assert [f["id"] for f in facts][:14] == [*FACT_IDS_BEFORE_A9, "outcome_pipeline_propagation"]
    assert facts[:13] == DISCOVERY_FACTS[:13]  # the first 13 rows are untouched


def test_a9_new_fact_is_exact_and_closed():
    fact = _profile()["discovery"]["facts"][13]  # the 14th; A10 appends a 15th after it
    assert fact == A9_FACT
    assert set(fact) == {"id", "scope", "status", "maturity", "summary", "state_sections"}
    assert 0 < len(fact["summary"].encode("utf-8")) <= 256
    assert len(fact["summary"].encode("utf-8")) == 220


def test_a9_discovery_stays_closed_and_within_its_byte_bound():
    discovery = _profile()["discovery"]
    assert (
        set(discovery) == {"coverage", "facts"}
        and discovery["coverage"] == "curated_non_exhaustive"
    )
    assert len(json.dumps(discovery, ensure_ascii=False).encode("utf-8")) <= 16384


def test_a9_golden_snapshot_carries_exactly_the_two_additions():
    assert GOLDEN["idioms"]["outcomes"] == A9_IDIOM
    assert GOLDEN["discovery"]["facts"][13] == A9_FACT
    assert len(GOLDEN["discovery"]["facts"]) == 15  # A10 (#1084): 14 -> 15


def test_a9_whole_profile_still_equals_the_golden_except_the_launch_revision():
    language = _profile()
    language.pop("contract_revision")
    assert language == GOLDEN
    assert set(language) == {
        "name",
        "control_flow",
        "supported_forms",
        "patterns",
        "absent_forms",
        "idioms",
        "examples",
        "discovery",
    }


def test_a9_plain_file_mode_carries_the_same_new_content():
    (response,) = responses(run_messages([PROFILE_CALL], args=(REVISION,)))
    language = structured(response)[1]["result"]["language"]
    assert language["idioms"]["outcomes"] == A9_IDIOM
    assert language["discovery"]["facts"][13] == A9_FACT


def test_a9_output_is_deterministic_across_calls():
    stdout, _ = launcher_batch([PROFILE_CALL, PROFILE_CALL])
    first, second = stdout.split(b"\n")[:2]
    assert first == second


# --- A9 surface closure (passes today; must keep passing) -----------------------------------------


def test_the_mcp_surface_stays_the_closed_four_tools_with_no_resources_or_prompts():
    _, out = launcher_batch([request("tools/list", 1), request("server/discover", 2)])
    assert [t["name"] for t in out[0]["result"]["tools"]] == [
        "genia_capabilities",
        "genia_parse",
        "genia_run",
        PROFILE_TOOL,
    ]
    assert list(RUN_TOOLS) == [t["name"] for t in out[0]["result"]["tools"]]
    assert out[1]["result"]["capabilities"] == {"tools": {}}


def test_capabilities_payload_is_unchanged_by_a9():
    _, out = launcher_batch([request("tools/call", 4, {"name": "genia_capabilities"})])
    capabilities = structured(out[0])[1]["result"]
    assert set(capabilities) == {"server", "mcp", "genia", "tools", "execution_profile"}
    assert capabilities["tools"] == list(RUN_TOOLS)


# --- A9 registry (RED until implementation) -------------------------------------------------------


def _fact(registry=REGISTRY):
    """Return the registry's `outcome_pipeline_propagation` fact, or None when it is not yet registered."""
    return next(
        (f for f in registry["discovery"]["facts"] if f["id"] == "outcome_pipeline_propagation"),
        None,
    )


def test_a9_registry_keeps_its_fact_14th_in_the_catalogue():
    assert len(REGISTRY["discovery"]["facts"]) == gen.DISCOVERY_FACT_COUNT == 15  # A10 (#1084): 14 -> 15
    assert [f["id"] for f in REGISTRY["discovery"]["facts"]][13] == "outcome_pipeline_propagation"


def test_a9_registry_fact_is_anchored_and_probed():
    fact = _fact()
    assert fact is not None, "A9: registry fact outcome_pipeline_propagation is missing"
    assert (fact["scope"], fact["status"], fact["maturity"], fact["summary"]) == (
        "language",
        "implemented",
        "Experimental",
        A9_FACT["summary"],
    )
    assert fact["anchors"] == [
        "state:outcome-propagation",
        "state:syntax-forms",
    ]  # crosswalks to ["2", "3"]
    probes = {i["name"] for i in fact["evidence"] if i["kind"] == "probe"}
    assert probes == {
        "direct_call_vs_pipeline_outcome",
        "err_is_not_absence",
        "recovery_wraps_pipeline",
    }
    assert any(i["kind"] == "state_text" for i in fact["evidence"])


def test_a9_registry_crosswalk_maps_the_new_anchor_to_section_2():
    assert REGISTRY["state_anchors"].get("state:outcome-propagation") == {"legacy_section": "2"}


def test_a9_registry_outcomes_idiom_is_governed_with_state_text_and_probe_evidence():
    body = REGISTRY["language"]["idioms"]
    assert body["value"].get("outcomes") == A9_IDIOM
    texts = [i for i in body["evidence"] if i["kind"] == "state_text"]
    assert {"state:outcome-propagation", "state:syntax-forms"} <= {i["anchor"] for i in texts}
    probes = {i["name"] for i in body["evidence"] if i["kind"] == "probe"}
    assert {
        "direct_call_vs_pipeline_outcome",
        "err_is_not_absence",
        "recovery_wraps_pipeline",
    } <= probes


def test_a9_registry_validates_and_its_projection_matches_the_committed_block():
    assert gen.validate(REGISTRY) == []
    assert gen.check(REGISTRY, SERVER_PATH.read_text(encoding="utf-8")) == []
    projection = gen.wire_projection(REGISTRY)
    assert projection["idioms"]["outcomes"] == A9_IDIOM
    assert projection["discovery"]["facts"][13] == A9_FACT


def test_a9_the_new_content_is_not_hand_copied_outside_the_generated_block():
    text = SERVER_PATH.read_text(encoding="utf-8")
    outside = text[: text.index(gen.BEGIN)] + text[text.index(gen.END) :]
    assert "outcome_pipeline_propagation" not in outside and A9_IDIOM not in outside
