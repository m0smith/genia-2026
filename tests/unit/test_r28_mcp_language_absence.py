"""R28 amendment A11 (#1084): absence-aware callee wording in `idioms.outcomes`.

Python-host tests of the MCP adapter boundary and of build-time governance. They add no Genia
semantics: A11 is a profile wording correction, and every claim is cross-checked against direct
command-source evaluation by the Python reference host. Contract: amendment A11 in
`docs/design/r28-genia-mcp-contract-threat-model.md`.

RED PHASE (intentional): the tests in the "A11 wire" and "A11 registry" groups fail until the
implementation phase corrects the registry and regenerates the profile. The "Genia already implements"
group passes today and must keep passing; it is the evidence the corrected wording restates. The exact
string below is an independent oracle copied from the contract, never generated from the registry.
"""

from __future__ import annotations

import pytest

from genia.interpreter import make_global_env, run_source
from tools import gen_mcp_language_profile as gen
from tools import state_anchors as sa
from tests.fixtures.r28_mcp_conformance import launcher_batch
from tests.fixtures.r28_mcp_helpers import (
    REPO_ROOT,
    REVISION,
    RUN_TOOLS,
    SERVER_PATH,
    request,
    responses,
    run_messages,
    structured,
)
from tests.unit.test_r28_mcp_language_flow import A10_FACT, A10_IDIOM
from tests.unit.test_r28_mcp_language_outcomes import A9_FACT, A9_IDIOM
from tests.unit.test_r28_mcp_language_profile import GOLDEN, PROFILE_CALL, _profile

pytestmark = pytest.mark.unit

A11_IDIOM = (
    "Outcomes are values: some(x) is present, none(...) is absent, and err(reason) is a recoverable "
    "failure that is not absence. In |> pipelines an ordinary stage receives x from some(x) and its "
    "plain result is wrapped back into some, while none and err skip the remaining stages and are "
    "returned unchanged. A direct call passes the Outcome itself as the argument, except that a none "
    "argument short-circuits the call unless the callee explicitly handles absence, such as "
    "unwrap_or. Recover around the expression, as in unwrap_or(0, parse_int(s)), not as a later |> "
    "stage."
)
RETIRED_PHRASE = "short-circuits an ordinary call"
EXCEPTION_PHRASE = "unless the callee explicitly handles absence"
STATE_EXCEPTION = "ordinary function calls short-circuit on `none(...)` arguments unless the callee explicitly handles absence"
A11_PROBE = "absence_aware_callee_receives_none"
REGISTRY = gen.load_registry()
STATE = (REPO_ROOT / "GENIA_STATE.md").read_text(encoding="utf-8")
ANCHORS = sa.parse_anchors(STATE)

INC = "inc(x) = x + 1\n"
HANDLES = "handles(o) = unwrap_or(0, o)\n"
PATTERN = 'g(o) =\n  none(r) -> "absent" |\n  _ -> "other"\n'


def _direct(source):
    """Evaluate `source` as command source on the Python reference host and return the host value."""
    return run_source(source, make_global_env(), filename="<command>")


def _shown(source):
    """Return the evaluated value's string form with double quotes, so Outcome text matches the CLI display."""
    return str(_direct(source)).replace("'", '"')


# --- Genia already implements this (passes today; the evidence A11 restates) ----------------------


def test_the_direct_evaluation_helper_really_evaluates():
    assert _direct("1 + 2") == 3  # guards the negative assertions below against a broken helper


def test_an_ordinary_callee_still_short_circuits_on_a_none_argument():
    assert _shown(INC + 'inc(none("m"))') == 'none("m")'


def test_unwrap_or_is_absence_aware_and_receives_the_none():
    assert _direct('unwrap_or(7, none("m"))') == 7


def test_a_callee_delegating_to_unwrap_or_receives_the_none():
    assert _direct(HANDLES + 'handles(none("a"))') == 0


def test_a_callee_with_a_none_pattern_receives_the_none():
    assert _direct(PATTERN + 'g(none("a"))') == "absent"
    assert _direct(PATTERN + 'g("x")') == "other"


def test_some_is_still_a_normal_value_in_a_direct_call_and_not_lifted():
    direct = _shown(INC + "inc(some(1))")
    assert direct != "some(2)" and direct.startswith("none(")


def test_a_pipeline_still_skips_every_later_stage_after_none_even_an_absence_aware_one():
    assert (
        _shown(PATTERN + 'none("z") |> g') == 'none("z")'
    )  # A9 meaning preserved: none skips later stages
    assert _shown(INC + "some(1) |> inc") == "some(2)"


def test_state_states_the_exception_under_the_outcome_anchor():
    span = sa.span_text(STATE, ANCHORS["state:outcome-propagation"])
    assert STATE_EXCEPTION in span


# --- A11 wire (RED until implementation) ----------------------------------------------------------


def test_a11_outcomes_idiom_is_the_exact_contract_text():
    assert _profile()["idioms"]["outcomes"] == A11_IDIOM
    assert len(A11_IDIOM.encode("utf-8")) == 566 <= 600


def test_a11_the_exception_is_stated_and_the_retired_phrase_is_gone():
    text = _profile()["idioms"]["outcomes"]
    assert EXCEPTION_PHRASE in text and "unwrap_or" in text
    assert RETIRED_PHRASE not in text


def test_a11_only_the_one_clause_changed_from_a9():
    before, after = A9_IDIOM.split("except that a none argument ")
    new_before, new_after = A11_IDIOM.split("except that a none argument ")
    assert new_before == before  # text before the clause is byte-identical
    assert (
        new_after.split(" Recover around", 1)[1] == after.split(" Recover around", 1)[1]
    )  # and after it


def test_a11_other_a9_meaning_is_preserved():
    text = _profile()["idioms"]["outcomes"]
    for term in (
        "some(x) is present",
        "none(...) is absent",
        "err(reason) is a recoverable failure that is not absence",
        "ordinary stage receives x from some(x)",
        "wrapped back into some",
        "none and err skip the remaining stages and are returned unchanged",
        "passes the Outcome itself as the argument",
        "unwrap_or(0, parse_int(s))",
        "not as a later |> stage",
    ):
        assert term in text, term


def test_a11_golden_snapshot_carries_the_corrected_idiom():
    assert GOLDEN["idioms"]["outcomes"] == A11_IDIOM


def test_a11_whole_profile_still_equals_the_golden_except_the_launch_revision():
    language = _profile()
    language.pop("contract_revision")
    assert language == GOLDEN


def test_a11_plain_file_mode_carries_the_corrected_idiom():
    (response,) = responses(run_messages([PROFILE_CALL], args=(REVISION,)))
    assert structured(response)[1]["result"]["language"]["idioms"]["outcomes"] == A11_IDIOM


def test_a11_output_is_deterministic_across_calls():
    stdout, _ = launcher_batch([PROFILE_CALL, PROFILE_CALL])
    first, second = stdout.split(b"\n")[:2]
    assert first == second


# --- A11 preservation (passes today; must keep passing) -------------------------------------------


def test_a11_a10_flow_content_is_byte_identical():
    language = _profile()
    assert language["idioms"]["flow"] == A10_IDIOM
    assert language["discovery"]["facts"][-1] == A10_FACT


def test_a11_the_a9_fact_and_the_catalogue_are_unchanged():
    facts = _profile()["discovery"]["facts"]
    assert len(facts) == 15 and len({f["id"] for f in facts}) == 15
    assert facts[13] == A9_FACT
    assert set(_profile()["idioms"]) == {
        "branching",
        "clauses",
        "flow",
        "outcomes",
        "pipelines",
        "repetition",
    }


def test_a11_the_mcp_surface_stays_the_closed_four_tools():
    _, out = launcher_batch([request("tools/list", 1)])
    assert [t["name"] for t in out[0]["result"]["tools"]] == list(RUN_TOOLS)
    assert len(RUN_TOOLS) == 4


# --- A11 registry (RED until implementation) ------------------------------------------------------


def test_a11_registry_holds_the_corrected_idiom_and_still_15_facts():
    body = REGISTRY["language"]["idioms"]
    assert body["value"]["outcomes"] == A11_IDIOM
    assert body["value"]["flow"] == A10_IDIOM
    assert len(REGISTRY["discovery"]["facts"]) == gen.DISCOVERY_FACT_COUNT == 15


def test_a11_registry_pins_the_full_state_exception_and_a_probe():
    body = REGISTRY["language"]["idioms"]
    pinned = [
        i
        for i in body["evidence"]
        if i["kind"] == "state_text" and i["anchor"] == "state:outcome-propagation"
    ]
    assert any(i["fragment"] == STATE_EXCEPTION for i in pinned), (
        "A11: the full STATE exception is not pinned"
    )
    assert {"kind": "probe", "name": A11_PROBE} in body["evidence"]


def test_a11_registry_a9_fact_evidence_is_untouched():
    fact = next(
        f for f in REGISTRY["discovery"]["facts"] if f["id"] == "outcome_pipeline_propagation"
    )
    assert {i["name"] for i in fact["evidence"] if i["kind"] == "probe"} == {
        "direct_call_vs_pipeline_outcome",
        "err_is_not_absence",
        "recovery_wraps_pipeline",
    }
    assert fact["summary"] == A9_FACT["summary"]


def test_a11_registry_validates_and_its_projection_matches_the_committed_block():
    assert gen.validate(REGISTRY) == []
    assert gen.check(REGISTRY, SERVER_PATH.read_text(encoding="utf-8")) == []
    assert gen.wire_projection(REGISTRY)["idioms"]["outcomes"] == A11_IDIOM
