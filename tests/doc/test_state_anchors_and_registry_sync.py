"""#1099 PR A: STATE semantic anchors and the governed MCP language-profile registry.

Documentation-sync tests. `GENIA_STATE.md` remains final authority; these tests prove that
every MCP-visible fact in `docs/contract/semantic_facts.json` (`mcp_language_profile`) is
anchored to a stable semantic anchor in STATE, verified by STATE text evidence located by
anchor (never by section number), and that editorial STATE edits do not cause false failures.
"""

from __future__ import annotations

import re

import pytest

from tools import gen_mcp_language_profile as gen
from tools import state_anchors as sa

from docs_truth_utils import read_text

STATE = read_text("GENIA_STATE.md")
REGISTRY = gen.load_registry()
ANCHORS = sa.parse_anchors(STATE)

REQUIRED_ANCHORS = {
    "state:host-status",
    "state:browser",
    "state:conformance",
    "state:execution-model",
    "state:syntax-forms",
    "state:open-functions",
    "state:pattern-matching",
    "state:control-flow",
    "state:tail-calls",
    "state:mcp-macos",
    "state:mcp-surface",
    "state:mcp-language-profile",
    "state:validated-pipelines",
    "state:outcome-propagation",  # A9 (#1084): intentionally red until the implementation phase
}
LANGUAGE_ANCHORS = {
    "state:syntax-forms",
    "state:open-functions",
    "state:pattern-matching",
    "state:control-flow",
    "state:tail-calls",
    "state:validated-pipelines",
    "state:outcome-propagation",  # A9 (#1084)
}


def _evidence_items():
    for member, body in REGISTRY["language"].items():
        for item in body["evidence"]:
            yield f"language.{member}", [], item
    for fact in REGISTRY["discovery"]["facts"]:
        for item in fact["evidence"]:
            yield fact["id"], fact["anchors"], item


def test_state_anchor_markers_are_well_formed_and_unique():
    assert sa.find_anchor_problems(STATE) == []


def test_every_required_anchor_exists_exactly_once():
    assert REQUIRED_ANCHORS <= set(ANCHORS)
    names = re.findall(r"^<!-- anchor: (state:[a-z0-9-]+) -->$", STATE, re.M)
    assert len(names) == len(set(names))


def test_anchor_span_is_heading_to_next_heading_of_same_or_higher_level():
    control = ANCHORS["state:control-flow"]
    assert control.level == 3 and "Conditionals" in control.heading
    pattern = ANCHORS["state:pattern-matching"]
    assert pattern.level == 2
    assert control.start >= pattern.start and control.end <= pattern.end  # nested ### inside ##


def test_state_states_control_flow_independently_of_mcp_sections():
    span = sa.span_text(STATE, ANCHORS["state:control-flow"]).lower()
    assert "no `if` expression or `if` form exists" in span
    assert "no dedicated loop syntax" in span
    assert "repetition is expressed by recursion" in span
    assert "tail calls are optimized" in span


def test_crosswalk_matches_current_enclosing_section_numbers():
    table = REGISTRY["state_anchors"]
    assert set(table) <= set(ANCHORS), "crosswalk names an anchor STATE does not define"
    for name, row in table.items():
        assert row["legacy_section"] == ANCHORS[name].section_number, name


def test_recorded_anchor_nesting_matches_state_spans():
    for name, row in REGISTRY["state_anchors"].items():
        if "within" in row:
            inner, outer = ANCHORS[name], ANCHORS[row["within"]]
            assert outer.start <= inner.start and inner.end <= outer.end, (name, row["within"])


def test_every_cited_anchor_is_in_the_crosswalk():
    for fact in REGISTRY["discovery"]["facts"]:
        for anchor in fact["anchors"]:
            assert anchor in REGISTRY["state_anchors"], (fact["id"], anchor)


@pytest.mark.parametrize(
    ("owner", "cited", "item"),
    [pytest.param(*row, id=f"{row[0]}-{i}") for i, row in enumerate(_evidence_items())],
)
def test_state_text_evidence_is_found_inside_its_anchor_span(owner, cited, item):
    if item["kind"] != "state_text":
        pytest.skip("non-text evidence is verified by the unit tests")
    anchor = ANCHORS[item["anchor"]]
    assert item["fragment"] in sa.span_text(STATE, anchor), (owner, item["anchor"], item["fragment"])
    if cited:
        cited_spans = [ANCHORS[a] for a in cited]
        assert any(c.start <= anchor.start and anchor.end <= c.end for c in cited_spans), (
            f"{owner}: evidence anchor {item['anchor']} lies outside every cited anchor {cited}"
        )


def test_language_claim_text_is_anchored_in_language_sections_not_only_mcp_sections():
    for member, body in REGISTRY["language"].items():
        texts = [i for i in body["evidence"] if i["kind"] == "state_text"]
        assert texts, f"language.{member} needs STATE text evidence"
        assert all(i["anchor"] in LANGUAGE_ANCHORS for i in texts), member
    loops = next(f for f in REGISTRY["discovery"]["facts"] if f["id"] == "if_and_loops")
    texts = [i for i in loops["evidence"] if i["kind"] == "state_text"]
    assert texts and all(i["anchor"] in LANGUAGE_ANCHORS for i in texts), "no circular MCP-only evidence"


def test_every_fact_has_evidence_and_text_pins_are_not_the_only_mechanism_for_executable_claims():
    for fact in REGISTRY["discovery"]["facts"]:
        assert fact["evidence"], fact["id"]
    for fid in ("tail_calls", "if_and_loops", "pattern_branching"):
        fact = next(f for f in REGISTRY["discovery"]["facts"] if f["id"] == fid)
        assert any(i["kind"] == "probe" for i in fact["evidence"]), fid


# --- editorial immunity and loud failure on meaningful change -----------------------------


def _mutated(text: str) -> str:
    # editorial: unrelated prose, an extra unanchored section, trailing whitespace, reordering
    out = text.replace("## 10) Explicitly not implemented (current)", "## 10) Explicitly not implemented (current)\n\nEditorial note.", 1)
    return out + "\n## 99) Unrelated appendix\n\nText only.\n"


def test_editorial_state_changes_do_not_break_anchor_resolution_or_evidence():
    text = _mutated(STATE)
    anchors = sa.parse_anchors(text)
    assert sa.find_anchor_problems(text) == []
    for owner, _cited, item in _evidence_items():
        if item["kind"] == "state_text":
            assert item["fragment"] in sa.span_text(text, anchors[item["anchor"]]), owner


def test_removing_an_anchor_marker_is_detected():
    text = STATE.replace("<!-- anchor: state:control-flow -->\n", "", 1)
    assert "state:control-flow" not in sa.parse_anchors(text)


def test_rewording_a_pinned_fragment_is_detected():
    item = next(i for _o, _c, i in _evidence_items() if i["kind"] == "state_text" and i["anchor"] == "state:tail-calls")
    text = STATE.replace(item["fragment"], "reworded", 1)
    assert item["fragment"] not in sa.span_text(text, sa.parse_anchors(text)["state:tail-calls"])


def test_duplicate_anchor_markers_are_reported():
    text = STATE + "\n## 98) Dup\n<!-- anchor: state:tail-calls -->\n"
    assert any("duplicate" in p for p in sa.find_anchor_problems(text))


def test_misplaced_marker_is_reported():
    text = STATE + "\nplain line\n<!-- anchor: state:orphan -->\n"
    assert any("heading" in p for p in sa.find_anchor_problems(text))


# --- workflow rule -------------------------------------------------------------------------

RULE_SURFACES = [
    ".github/ISSUE_TEMPLATE/genia-change-preflight.md",
    "docs/process/00-preflight.md",
    "docs/process/05-doc.md",
    "docs/process/06-audit.md",
    "docs/process/run-change.md",
    "AGENTS.md",
    "docs/ai/LLM_CONTRACT.md",
    ".github/copilot-instructions.md",
]


@pytest.mark.parametrize("relpath", RULE_SURFACES)
def test_future_change_rule_requires_mcp_language_knowledge_impact(relpath):
    text = read_text(relpath)
    assert "MCP language-knowledge impact" in text, relpath
    assert "docs/contract/semantic_facts.json" in text, relpath


def test_agents_names_the_registry_generator_and_check():
    text = read_text("AGENTS.md")
    assert "tools/gen_mcp_language_profile.py --check" in text


def test_conformance_architecture_doc_states_the_registry_is_a_guarded_projection_source():
    text = " ".join(read_text("docs/architecture/executable-semantic-conformance.md").split()).lower()
    assert "mcp_language_profile" in text
    assert "not a second language definition" in text
    assert "projection source" in text


# --- A9 (#1084): Outcome propagation anchor and STATE text --------------------------------------
# RED PHASE (intentional): `state:outcome-propagation` and the explicit direct-call sentence are
# STATE prerequisites of contract amendment A9, clause A9.3; the implementation phase adds them. These tests
# only assert their required future presence; they do not define a second authority.

A9_ANCHOR = "state:outcome-propagation"
A9_STATE_FRAGMENTS = [
    "for recoverable failure (Experimental)",
    "`err(...)` is not absence",
    "ordinary function calls short-circuit on `none(...)` arguments",
    "pipelines short-circuit on `none(...)` and `err(...)`, and automatically lift ordinary stages over `some(...)`",
    "non-Option stage results are wrapped back into `some(...)`",
    "recovery must wrap the whole pipeline",
]
A9_PIPELINE_FRAGMENTS = [  # already under the existing state:syntax-forms anchor
    "automatic Outcome propagation is part of pipeline evaluation",
    "if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage receives `x`",
    "if a stage input is `err(...)`, the remaining stages do not execute and the same `err(...)` is returned",
]
A9_DIRECT_CALL_SENTENCE = "In direct calls, `some(x)` is still a normal value and is passed explicitly."


def test_a9_pipeline_fragments_already_exist_under_the_syntax_forms_anchor():
    span = sa.span_text(STATE, ANCHORS["state:syntax-forms"])
    for fragment in A9_PIPELINE_FRAGMENTS:
        assert fragment in span, fragment


def test_a9_outcome_propagation_anchor_exists_once_and_is_in_section_2():
    assert A9_ANCHOR in ANCHORS, "A9.3 prerequisite 1: add <!-- anchor: state:outcome-propagation --> in STATE section 2"
    assert ANCHORS[A9_ANCHOR].section_number == "2"
    assert re.findall(r"^<!-- anchor: (state:[a-z0-9-]+) -->$", STATE, re.M).count(A9_ANCHOR) == 1


@pytest.mark.parametrize("fragment", A9_STATE_FRAGMENTS)
def test_a9_outcome_fragments_are_inside_the_new_anchor_span(fragment):
    assert A9_ANCHOR in ANCHORS, "A9.3 prerequisite 1 (anchor) is missing"
    assert fragment in sa.span_text(STATE, ANCHORS[A9_ANCHOR]), fragment


def test_a9_state_states_the_direct_call_sentence_under_the_new_anchor():
    assert A9_ANCHOR in ANCHORS, "A9.3 prerequisite 1 (anchor) is missing"
    assert A9_DIRECT_CALL_SENTENCE in sa.span_text(STATE, ANCHORS[A9_ANCHOR]), (
        "A9.3 prerequisite 2: STATE must restate the GENIA_RULES.md direct-call sentence"
    )


def test_a9_the_direct_call_sentence_is_already_authoritative_in_rules():
    assert A9_DIRECT_CALL_SENTENCE in read_text("GENIA_RULES.md")
