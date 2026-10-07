"""#1099 PR B, phase 4b: verbatim preservation gate for docs/state-record/.

Every ledger row dispositioned `moved` or `retained-condensed` must appear, byte-identical and
contiguous, in its record file under a provenance line; records are fenced non-authoritative
provenance material and stay out of the truth hierarchy.
"""

from __future__ import annotations

import hashlib
import json
import re

from docs_truth_utils import REPO, read_text

LEDGER = json.loads((REPO / "docs/analysis/state-distillation-migration-map.json").read_text(encoding="utf-8"))
ROWS = LEDGER["rows"]
ARCHIVED = [r for r in ROWS if r["archive"]]
FENCE = "~~~~~"


def _blocks(relpath: str) -> dict[str, tuple[str, str]]:
    text = read_text(relpath)
    found = {}
    pattern = re.compile(
        r"^## (B\d{3}): baseline lines (\d+)-(\d+)\n\n(Moved from GENIA_STATE\.md@[0-9a-f]{8}, lines \d+-\d+ [^\n]+)\n\n"
        + FENCE
        + r"markdown\n(.*?)\n"
        + FENCE
        + r"\n",
        re.S | re.M,
    )
    for m in pattern.finditer(text):
        found[m.group(1)] = (m.group(4), m.group(5))
    return found


def test_every_archived_row_has_a_sha256_in_the_ledger():
    assert all(re.fullmatch(r"[0-9a-f]{64}", r["sha256"]) for r in ROWS)


def test_every_archived_row_is_preserved_verbatim_in_its_record():
    by_record: dict[str, dict] = {}
    for row in ARCHIVED:
        blocks = by_record.setdefault(row["archive"], _blocks(row["archive"]))
        assert row["id"] in blocks, f"{row['id']} missing from {row['archive']}"
        prov, text = blocks[row["id"]]
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == row["sha256"], f"{row['id']} text differs from the baseline"
        assert f"lines {row['start']}-{row['end']}" in prov
        assert row["sha256"][:16] in prov
        assert LEDGER["baseline"]["sha"][:8] in prov


def test_records_contain_no_unledgered_blocks():
    expected = {r["archive"]: {x["id"] for x in ARCHIVED if x["archive"] == r["archive"]} for r in ARCHIVED}
    for path, ids in expected.items():
        assert set(_blocks(path)) == ids, path


def test_records_are_marked_non_authoritative():
    readme = read_text("docs/state-record/README.md")
    flat = " ".join(readme.split())
    assert "not part of the truth hierarchy" in flat and "`GENIA_STATE.md` is the final authority" in flat
    for path in {r["archive"] for r in ARCHIVED}:
        head = read_text(path)[:900].lower()
        assert "non-authoritative" in head and "`genia_state.md` governs" in head, path


def test_state_record_is_not_in_the_truth_hierarchy():
    agents = read_text("AGENTS.md")
    hierarchy = agents.split("# 📚 SOURCE OF TRUTH (ORDERED)")[1].split("Rules:")[0]
    assert "state-record" not in hierarchy


def test_release_and_design_pages_link_their_records():
    for page, record in [
        ("docs/releases/R14.md", "r14-lifecycle-http-records.md"),
        ("docs/releases/R22.md", "numeric-r21-r23-records.md"),
        ("docs/releases/R28.md", "r28-mcp-records.md"),
        ("docs/releases/R16.md", "hosts-and-conformance.md"),
        ("docs/design/p8-alternate-provider-substitution-proof-design.md", "provider-proof-records.md"),
    ]:
        assert f"docs/state-record/{record}" in read_text(page), page
