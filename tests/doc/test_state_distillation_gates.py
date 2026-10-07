"""#1099 PR B: gates for the distilled GENIA_STATE.md.

Size and structure bounds (ratified in review), identifier preservation across STATE and the
non-authoritative state records, link integrity for retired section numbers, crosswalk freshness,
and anchor survival. `GENIA_STATE.md` remains final authority; these tests only prove that the
distillation did not silently lose or orphan information.
"""

from __future__ import annotations

import glob
import json
import re

from tools import state_records as rec

from docs_truth_utils import REPO, read_text

MAX_LINES = 3900
MAX_WORDS = 43000
MAX_ISSUE_REFS = 60

STATE = read_text("GENIA_STATE.md")
LEDGER = json.loads((REPO / "docs/analysis/state-distillation-migration-map.json").read_text(encoding="utf-8"))
RECORD_PATHS = sorted(glob.glob(str(REPO / "docs/state-record/*.md")))
LIVE_NUMBERS = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)*)\)", STATE, re.M))
BASELINE_NUMBERS = {h["number"] for h in LEDGER["headings"] if h["number"]}
# Numbers cited next to "STATE" in other documents that never named a baseline STATE section
# (they refer to another document's numbering); verified absent from the baseline headings.
NON_STATE_CITATIONS = {"3.2", "18"}


def test_state_is_within_the_ratified_size_bounds():
    assert len(STATE.rstrip("\n").split("\n")) <= MAX_LINES
    assert len(STATE.split()) <= MAX_WORDS


def test_state_has_no_ticket_narrative_in_headings_or_historical_evidence_markers():
    headings = [l for l in STATE.split("\n") if l.startswith("#")]
    assert [h for h in headings if re.search(r"\bE\d+-\d+\b", h)] == []
    assert len(re.findall(r"#\d{3,4}", STATE)) <= MAX_ISSUE_REFS
    assert not re.findall(r"\b[0-9a-f]{40}\b", STATE), "pinned evidence commit hashes belong in release/evidence documents"
    assert not re.search(r"\b\d+ total\s*/\s*\d+ pass", STATE)
    assert "Validated by" not in STATE


def test_every_baseline_identifier_is_in_state_or_a_state_record():
    baseline = json.loads((REPO / "docs/analysis/state-distillation-baseline-identifiers.json").read_text(encoding="utf-8"))
    corpus = STATE + "\n" + "\n".join(open(p, encoding="utf-8").read() for p in RECORD_PATHS)
    missing = [i for i in baseline if f"`{i}`" not in corpus]
    assert missing == [], f"{len(missing)} baseline identifiers are unaccounted for: {missing[:20]}"


def test_crosswalk_is_fresh_and_covers_every_baseline_section_number():
    expected = rec.crosswalk(LEDGER, STATE)
    assert read_text("docs/state-record/crosswalk.md") == expected
    for number in BASELINE_NUMBERS:
        assert f"| {number} |" in expected, number


def test_every_cited_state_section_number_resolves_to_a_live_heading_or_the_crosswalk():
    pattern = re.compile(r"(?:GENIA_STATE(?:\.md)?|STATE)[`\s]{0,3}[^\n]{0,30}?(?:section|sections|§)\s*`?(\d+(?:\.\d+)*)", re.I)
    unresolved = {}
    for path in glob.glob(str(REPO / "**/*"), recursive=True):
        if not path.endswith((".md", ".py", ".json", ".yaml", ".yml", ".genia", ".mjs", ".txt")):
            continue
        rel = path[len(str(REPO)) + 1 :]
        if rel.startswith((".git/", "node_modules", ".tmp", ".venv")) or "/state-record/" in rel or rel == "GENIA_STATE.md":
            continue
        if "state-distillation" in rel or rel.startswith("tests/doc/test_state_distillation"):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for m in pattern.finditer(text):
            n = m.group(1)
            if n not in LIVE_NUMBERS and n not in BASELINE_NUMBERS and n not in NON_STATE_CITATIONS:
                unresolved.setdefault(n, []).append(rel)
    assert unresolved == {}, unresolved


def test_retired_numbers_are_resolved_by_the_crosswalk_document_itself():
    text = read_text("docs/state-record/crosswalk.md")
    for number in sorted(BASELINE_NUMBERS - LIVE_NUMBERS):
        assert f"| {number} |" in text, number


def test_state_links_the_record_collection_and_the_crosswalk():
    assert "docs/state-record/README.md" in STATE
    assert "docs/state-record/crosswalk.md" in STATE


def test_registry_anchors_and_legacy_sections_survive():
    # The wire contract keeps legacy numbers; each must still be a live heading number.
    registry = json.loads(read_text("docs/contract/semantic_facts.json"))["mcp_language_profile"]
    for name, row in registry["state_anchors"].items():
        assert f"<!-- anchor: {name} -->" in STATE, name
        assert row["legacy_section"] in LIVE_NUMBERS, (name, row["legacy_section"])


def test_ledger_records_every_disposition_change_and_test_retarget():
    exceptions = LEDGER["exceptions"]
    kinds = {e["kind"] for e in exceptions}
    assert {"disposition-change", "test-retarget", "row-consolidation"} <= kinds
    for e in exceptions:
        assert e["rationale"] and e["ids"], e
