"""R28 findings ledger guard (docs/analysis/r28-host-dependency-inventory.md).

Keeps the living ledger present, structured, and referenced by the roadmap so
findings cannot silently disappear into phase transcripts.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER = REPO_ROOT / "docs" / "analysis" / "r28-host-dependency-inventory.md"
ROADMAP = REPO_ROOT / "docs" / "strategy" / "roadmap" / "r25-r29.md"
FIELDS = (
    "Class:",
    "Status:",
    "Evidence:",
    "Disposition:",
    "Raised in:",
)
VALID_CLASS = re.compile(r"Class: \*\*(A|B|C|N|A/B)\b")
VALID_STATUS = re.compile(r"Status: `(open|closed|promoted)`")


def _entries():
    text = LEDGER.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^\*\*(R28-H\d{2}) — ", text)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def test_ledger_exists_and_is_non_authoritative():
    text = LEDGER.read_text(encoding="utf-8")
    assert "GENIA_STATE.md" in text and "final authority" in text
    assert "not a language contract" in text


def test_ledger_entries_carry_required_fields_and_valid_values():
    entries = _entries()
    assert len(entries) >= 14
    for entry_id, body in entries.items():
        for field in FIELDS:
            assert field in body, f"{entry_id} missing {field}"
        assert VALID_CLASS.search(body), f"{entry_id} has no valid class"
        assert VALID_STATUS.search(body), f"{entry_id} has no valid status"


def test_promoted_entries_link_their_issue():
    for entry_id, body in _entries().items():
        if "Status: `promoted`" in body:
            assert re.search(r"(issue|pre-flight)[^\n]*#\d+", body, re.I), entry_id


def test_ledger_states_the_mandatory_process_rules():
    text = LEDGER.read_text(encoding="utf-8")
    assert "Required input" in text
    assert "No ticket from discovery alone" in text
    assert "MUST disposition" in text


def test_roadmap_points_r28_at_the_ledger():
    assert "docs/analysis/r28-host-dependency-inventory.md" in ROADMAP.read_text(
        encoding="utf-8"
    )
