"""R28 amendment A10 (#1084): Flow content of `genia_language_profile`.

Python-host tests of the MCP adapter boundary and of build-time governance. They add no Genia
semantics; every claim the profile makes is cross-checked against direct command-source evaluation
by the Python reference host. Contract: amendment A10 in
`docs/design/r28-genia-mcp-contract-threat-model.md`.

RED PHASE (intentional): the tests in the "A10 wire" and "A10 registry" groups fail until the
implementation phase adds `idioms.flow`, the `flow_semantics` fact, and the registry entries. The
"Genia already implements" group passes today and must keep passing; it is the evidence the new content
restates. The exact strings below are an independent oracle copied from the contract, never generated
from the registry.
"""

from __future__ import annotations

import contextlib
import io
import json
import re

import pytest

from genia.interpreter import make_global_env, run_source
from tools import gen_mcp_language_profile as gen
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
from tests.unit.test_r28_mcp_language_outcomes import A9_FACT, A9_IDIOM
from tests.unit.test_r28_mcp_language_profile import DISCOVERY_FACTS, GOLDEN, PROFILE_CALL, _profile

pytestmark = pytest.mark.unit

A10_IDIOM = (
    "Flow is a lazy, pull-based, single-use sequence, and a list stays a list. lines turns a list of "
    "strings or stdin into a Flow (a bare string or a list holding a non-string is an error), and "
    "map, filter and take keep a Flow lazy. Nothing runs until a terminal pulls: collect returns a "
    "list and run consumes the Flow and returns nil. Consuming a Flow twice is an error. evolve is "
    "unbounded, so take(n) before collect or run. stdin is a host input, not a Flow: adapt it with "
    "stdin |> lines where the host supplies it."
)
A10_FACT = {
    "id": "flow_semantics",
    "scope": "language",
    "status": "implemented",
    "maturity": "Experimental",
    "summary": (
        "Experimental: Flow is lazy, pull-based and single-use; lines takes a list of strings; bound "
        "unbounded sources with take; the C++ host supports only a bounded Flow subset."
    ),
    "state_sections": ["6", "0"],
}
A10_PROBES = {
    "flow_single_use",
    "lines_input_validation",
    "flow_bounded_demand",
    "flow_terminals_and_kinds",
    "stdin_requires_lines_adapter",
}
REGISTRY = gen.load_registry()


def _direct(source):
    """Evaluate `source` as command source on the Python reference host and return the host value."""
    return run_source(source, make_global_env(), filename="<command>")


def _shown(source):
    """Return the evaluated value's string form with double quotes, so Outcome text matches the CLI display."""
    return str(_direct(source)).replace("'", '"')


def _stdout_of(source):
    """Evaluate `source` and return (value, everything the program printed)."""
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        value = _direct(source)
    return value, printed.getvalue()


# --- Genia already implements this (passes today; the evidence A10 restates) ----------------------


def test_the_direct_evaluation_helper_really_evaluates():
    assert _direct("1 + 2") == 3  # guards the negative assertions below against a broken helper


def test_flow_is_lazy_and_pull_based_take_bounds_an_unbounded_source():
    assert _direct("inc(n) = n + 1\nevolve(0, inc) |> take(3) |> collect") == [0, 1, 2]


def test_take_does_not_over_pull_and_a_full_collect_pulls_everything():
    value, printed = _stdout_of('["a", "b", "c"] |> lines |> each(print) |> take(1) |> collect')
    assert value == ["a"] and printed == "a\n"  # "b" and "c" were never demanded
    _, everything = _stdout_of('["a", "b", "c"] |> lines |> each(print) |> collect')
    assert everything == "a\nb\nc\n"  # control: proves the printing stage really runs when consumed


def test_nothing_runs_until_a_terminal_pulls():
    value, printed = _stdout_of('f = ["a", "b"] |> lines |> each(print)\n1')
    assert value == 1 and printed == ""  # building the Flow pulled nothing


@pytest.mark.parametrize(
    "source",
    [
        'f = ["a"] |> lines\ncollect(f)\ncollect(f)',
        'f = ["a"] |> lines\nrun(f)\ncollect(f)',
        'f = ["a"] |> lines\ncollect(f)\nrun(f)',
    ],
    ids=["collect-collect", "run-collect", "collect-run"],
)
def test_a_consumed_flow_cannot_be_consumed_again(source):
    with pytest.raises(Exception, match="already been consumed"):
        _direct(source)


def test_collect_returns_a_list_and_run_returns_nil():
    assert _direct('["a", "b"] |> lines |> collect') == ["a", "b"]
    assert _shown('["a"] |> lines |> run') == 'none("nil")'


def test_a_list_stays_a_list_and_a_flow_stays_a_lazy_flow():
    assert _direct("inc(n) = n + 1\n[1, 2, 3] |> map(inc)") == [2, 3, 4]
    assert _shown('["a"] |> lines |> map((s) -> s)').startswith("<flow")


@pytest.mark.parametrize(
    "source", ['lines("abc")', "lines(5)", 'lines(["a", 1])', "[1, 2, 3] |> lines"]
)
def test_lines_rejects_a_bare_string_and_non_string_elements(source):
    with pytest.raises(Exception, match="lines expected"):
        _direct(source)


def test_lines_accepts_a_list_of_strings_and_a_flow():
    assert _direct('["a", "b"] |> lines |> collect') == ["a", "b"]
    assert _direct('["a"] |> lines |> lines |> collect') == ["a"]


@pytest.mark.parametrize("source", ["collect(stdin)", "run(stdin)"])
def test_stdin_is_not_a_flow_and_must_be_adapted_with_lines(source):
    with pytest.raises(Exception, match=r"stdin \|> lines"):
        _direct(source)


# --- A10 wire (RED until implementation) ----------------------------------------------------------


def test_a10_idioms_gain_exactly_the_flow_member():
    assert set(_profile()["idioms"]) == {
        "branching",
        "clauses",
        "flow",
        "outcomes",
        "pipelines",
        "repetition",
    }


def test_a10_flow_idiom_is_the_exact_contract_text():
    assert _profile()["idioms"]["flow"] == A10_IDIOM
    assert len(A10_IDIOM.encode("utf-8")) == 513 <= 600


def test_a10_flow_idiom_states_the_documented_distinctions():
    text = _profile()["idioms"]["flow"]
    for term in (
        "lazy",
        "single-use",
        "collect",
        "run",
        "take(n)",
        "evolve",
        "lines",
        "stdin |> lines",
        "list of strings",
        "a list stays a list",
    ):
        assert term in text, term
    for overclaim in (r"\ball\b", r"\balways\b", r"\bcomplete", r"\bfully\b", r"\bportable\b"):
        assert not re.search(overclaim, text.lower()), overclaim
    assert "C++" not in text  # portability is carried by the fact and by STATE, not the idiom


def test_a10_does_not_repeat_a9_or_a8_guidance_in_the_flow_idiom():
    text = _profile()["idioms"]["flow"]
    for term in ("err(", "unwrap_or", "some(x)", "keep_some", "validate"):
        assert term not in text, term


def test_a10_existing_idioms_are_unchanged():
    idioms = _profile()["idioms"]
    for key in ("branching", "clauses", "pipelines", "repetition"):
        assert idioms[key] == GOLDEN["idioms"][key]
    assert idioms["outcomes"] == A9_IDIOM  # A9 survives byte for byte


def test_a10_discovery_grows_from_14_to_exactly_15_facts_with_the_new_fact_last():
    facts = _profile()["discovery"]["facts"]
    assert [f["id"] for f in facts][-2:] == ["outcome_pipeline_propagation", "flow_semantics"]
    assert len(facts) == 15 and len({f["id"] for f in facts}) == 15
    assert facts[:14] == DISCOVERY_FACTS[:14]  # the first 14 rows are untouched
    assert facts[13] == A9_FACT


def test_a10_new_fact_is_exact_and_closed():
    fact = _profile()["discovery"]["facts"][-1]
    assert fact == A10_FACT
    assert set(fact) == {"id", "scope", "status", "maturity", "summary", "state_sections"}
    assert 0 < len(fact["summary"].encode("utf-8")) <= 256
    assert len(fact["summary"].encode("utf-8")) == 170


def test_a10_fact_does_not_overclaim_portability_or_coverage():
    summary = _profile()["discovery"]["facts"][-1]["summary"].lower()
    for overclaim in ("fully", "complete", "all hosts", "portable", "shared coverage"):
        assert overclaim not in summary, overclaim
    assert "c++" in summary and "bounded" in summary


def test_a10_discovery_stays_closed_and_within_its_byte_bound():
    discovery = _profile()["discovery"]
    assert (
        set(discovery) == {"coverage", "facts"}
        and discovery["coverage"] == "curated_non_exhaustive"
    )
    assert len(json.dumps(discovery, ensure_ascii=False).encode("utf-8")) <= 16384


def test_a10_golden_snapshot_carries_exactly_the_two_additions():
    assert GOLDEN["idioms"]["flow"] == A10_IDIOM
    assert GOLDEN["discovery"]["facts"][-1] == A10_FACT
    assert len(GOLDEN["discovery"]["facts"]) == 15


def test_a10_whole_profile_still_equals_the_golden_except_the_launch_revision():
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


def test_a10_plain_file_mode_carries_the_same_new_content():
    (response,) = responses(run_messages([PROFILE_CALL], args=(REVISION,)))
    language = structured(response)[1]["result"]["language"]
    assert language["idioms"]["flow"] == A10_IDIOM
    assert language["discovery"]["facts"][-1] == A10_FACT


def test_a10_output_is_deterministic_across_calls():
    stdout, _ = launcher_batch([PROFILE_CALL, PROFILE_CALL])
    first, second = stdout.split(b"\n")[:2]
    assert first == second


# --- A10 surface closure (passes today; must keep passing) ----------------------------------------


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


def test_capabilities_payload_is_unchanged_by_a10():
    _, out = launcher_batch([request("tools/call", 4, {"name": "genia_capabilities"})])
    capabilities = structured(out[0])[1]["result"]
    assert set(capabilities) == {"server", "mcp", "genia", "tools", "execution_profile"}
    assert capabilities["tools"] == list(RUN_TOOLS)


# --- A10 registry (RED until implementation) ------------------------------------------------------


def _fact():
    """Return the registry's `flow_semantics` fact, or None when it is not yet registered."""
    return next((f for f in REGISTRY["discovery"]["facts"] if f["id"] == "flow_semantics"), None)


def test_a10_registry_holds_15_facts_the_generator_expects_15_and_a9_is_untouched():
    assert len(REGISTRY["discovery"]["facts"]) == gen.DISCOVERY_FACT_COUNT == 15
    assert [f["id"] for f in REGISTRY["discovery"]["facts"]][-2:] == [
        "outcome_pipeline_propagation",
        "flow_semantics",
    ]


def test_a10_registry_fact_is_anchored_and_probed():
    fact = _fact()
    assert fact is not None, "A10: registry fact flow_semantics is missing"
    assert (fact["scope"], fact["status"], fact["maturity"], fact["summary"]) == (
        "language",
        "implemented",
        "Experimental",
        A10_FACT["summary"],
    )
    assert fact["anchors"] == [
        "state:flow-semantics",
        "state:host-status",
    ]  # crosswalks to ["6", "0"]
    assert {i["name"] for i in fact["evidence"] if i["kind"] == "probe"} == A10_PROBES
    anchors = {i["anchor"] for i in fact["evidence"] if i["kind"] == "state_text"}
    assert anchors == {"state:flow-semantics", "state:host-status"}


def test_a10_registry_crosswalk_maps_the_new_anchor_to_section_6():
    assert REGISTRY["state_anchors"].get("state:flow-semantics") == {"legacy_section": "6"}


def test_a10_registry_flow_idiom_is_governed_with_state_text_and_probe_evidence():
    body = REGISTRY["language"]["idioms"]
    assert body["value"].get("flow") == A10_IDIOM
    texts = [i for i in body["evidence"] if i["kind"] == "state_text"]
    assert {"state:flow-semantics", "state:outcome-propagation"} <= {i["anchor"] for i in texts}
    assert A10_PROBES <= {i["name"] for i in body["evidence"] if i["kind"] == "probe"}


def test_a10_registry_validates_and_its_projection_matches_the_committed_block():
    assert gen.validate(REGISTRY) == []
    assert gen.check(REGISTRY, SERVER_PATH.read_text(encoding="utf-8")) == []
    projection = gen.wire_projection(REGISTRY)
    assert projection["idioms"]["flow"] == A10_IDIOM
    assert projection["idioms"]["outcomes"] == A9_IDIOM
    assert projection["discovery"]["facts"][-1] == A10_FACT


def test_a10_the_new_content_is_not_hand_copied_outside_the_generated_block():
    text = SERVER_PATH.read_text(encoding="utf-8")
    outside = text[: text.index(gen.BEGIN)] + text[text.index(gen.END) :]
    assert "flow_semantics" not in outside and A10_IDIOM not in outside
