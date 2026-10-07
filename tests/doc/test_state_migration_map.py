"""#1099 PR B, phase 4a: guard for the GENIA_STATE.md distillation migration ledger.

`docs/analysis/state-distillation-migration-map.json` partitions every line of the baseline
STATE into rows, each with exactly one disposition. These tests keep the ledger structurally
complete so no STATE content can disappear without a recorded destination. The ledger is a
non-authoritative planning/audit record; `GENIA_STATE.md` governs.
"""

from __future__ import annotations

import hashlib
import json
import re

import pytest

from tools import state_inventory as inv

from docs_truth_utils import REPO

LEDGER_PATH = REPO / "docs" / "analysis" / "state-distillation-migration-map.json"
IDENTIFIERS_PATH = REPO / "docs" / "analysis" / "state-distillation-baseline-identifiers.json"
LEDGER = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
ROWS = LEDGER["rows"]
VOCAB = set(LEDGER["dispositions"])
ARCHIVES = {
    "docs/state-record/hosts-and-conformance.md",
    "docs/state-record/tooling-and-examples.md",
    "docs/state-record/capability-records.md",
    "docs/state-record/builtin-records.md",
    "docs/state-record/native-test-and-lifecycle-shape-records.md",
    "docs/state-record/server-and-process-records.md",
    "docs/state-record/r14-lifecycle-http-records.md",
    "docs/state-record/numeric-r21-r23-records.md",
    "docs/state-record/provider-proof-records.md",
    "docs/state-record/r28-mcp-records.md",
}


def test_baseline_is_recorded():
    base = LEDGER["baseline"]
    assert re.fullmatch(r"[0-9a-f]{40}", base["sha"])
    assert re.fullmatch(r"[0-9a-f]{64}", base["state_sha256"])
    assert base["lines"] > 0 and base["words"] > 0


def test_rows_partition_every_baseline_line_exactly_once():
    expected = 1
    for row in ROWS:
        assert row["start"] == expected, f"gap or overlap before {row['id']}"
        assert row["end"] >= row["start"]
        assert row["lines"] == row["end"] - row["start"] + 1
        expected = row["end"] + 1
    assert expected - 1 == LEDGER["baseline"]["lines"]
    assert sum(r["lines"] for r in ROWS) == LEDGER["baseline"]["lines"]
    assert len({r["id"] for r in ROWS}) == len(ROWS)


def test_every_row_has_exactly_one_legal_disposition_and_a_destination_when_required():
    for row in ROWS:
        assert row["disposition"] in VOCAB, row["id"]
        if row["disposition"] in {"moved", "retained-condensed"}:
            assert row["archive"] in ARCHIVES, f"{row['id']} needs a verbatim-record destination"
        if row["disposition"] == "retained":
            assert row["archive"] is None and row["est_retained_lines"] == row["lines"], row["id"]
        if row["disposition"] == "moved":
            assert row["est_retained_lines"] == 0, row["id"]
        assert 0 <= row["est_retained_lines"] <= row["lines"], row["id"]
        assert row["disposition"] not in {"redundant", "obsolete"} or row["note"], f"{row['id']} needs evidence"


def test_obsolete_claims_cite_the_superseding_source():
    flagged = [r for r in ROWS if "obsolete" in r["note"].lower() or "superseded" in r["note"].lower()]
    assert flagged, "the known superseded statements must be recorded"
    for row in flagged:
        assert "superseded by" in row["note"], row["id"]


def test_every_baseline_heading_is_owned_by_a_row():
    heading_ids = {h["id"] for h in LEDGER["headings"]}
    assert {r["heading_id"] for r in ROWS} <= heading_ids
    for heading in LEDGER["headings"]:
        owner = [r for r in ROWS if r["start"] <= heading["line"] <= r["end"]]
        assert len(owner) == 1, heading["id"]


def test_pinned_rows_are_never_dropped_and_moved_pins_have_an_action():
    for row in ROWS:
        if row.get("pinned_by") and row["disposition"] == "moved":
            assert row.get("pin_action"), f"{row['id']} is pinned by {row['pinned_by']} but has no pin_action"
        if row.get("pinned_by"):
            assert row["disposition"] != "obsolete", row["id"]


def test_size_model_is_consistent_with_the_rows():
    s = LEDGER["summary"]
    assert s["retained_rows_lines"] == sum(r["est_retained_lines"] for r in ROWS)
    assert s["digest_lines"] == sum(d["est_lines"] for d in s["digests"])
    assert s["model_total_lines"] == s["retained_rows_lines"] + s["digest_lines"]
    assert s["model_total_lines"] < LEDGER["baseline"]["lines"]


def test_baseline_identifier_inventory_is_sorted_unique_and_nonempty():
    ids = json.loads(IDENTIFIERS_PATH.read_text(encoding="utf-8"))
    assert ids == sorted(set(ids)) and len(ids) > 3000


def test_ledger_matches_the_live_state_while_it_is_still_the_baseline():
    state_path = REPO / "GENIA_STATE.md"
    raw = state_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != LEDGER["baseline"]["state_sha256"]:
        pytest.skip("GENIA_STATE.md has been distilled; the baseline is verified by the state-record documents")
    text = raw.decode("utf-8")
    assert len(text.split("\n")) == LEDGER["baseline"]["lines"]
    lines = text.split("\n")
    for row in ROWS:
        first = next((l for l in lines[row["start"] - 1 : row["end"]] if l.strip() and not l.startswith("<!--")), "")
        assert first.strip()[:110] == row["title"], row["id"]
    live = [(h["id"], h["line"], h["heading"]) for h in inv.headings(text)]
    assert live == [(h["id"], h["line"], h["heading"]) for h in LEDGER["headings"]]
    assert json.loads(IDENTIFIERS_PATH.read_text(encoding="utf-8")) == inv.identifiers(text)
