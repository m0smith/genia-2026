from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "docs" / "strategy" / "release-roadmap.md"
ROADMAP_DIR = ROOT / "docs" / "strategy" / "roadmap"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_root_roadmap_is_small_canonical_index() -> None:
    text = read(ROADMAP)

    assert len(text.splitlines()) < 220
    assert "GENIA_STATE.md" in text
    assert "does not define implemented language behavior" in text
    assert "R15 — Validated Value Modeling" in text
    assert "R21 | Numeric Source and Portable Representation" in text
    assert "R28 | Genia MCP Server" in text
    assert "R37 | Unified Events and Subscriptions" in text
    assert "R38 | Portable Actors, Messaging and Supervision" in text
    assert "R39 | Genia-Native Conformance Tooling" in text
    assert "R40 | Configuration and Secret Hardening and Ergonomics" in text
    assert "R41 | Portable Core IR Artifacts" in text
    assert "roadmap/r15.md" in text
    assert "roadmap/r16-r20.md" in text
    assert "roadmap/r21-r24.md" in text
    assert "roadmap/r25-r29.md" in text
    assert "roadmap/r30-r32.md" in text
    assert "roadmap/r35-r37.md" in text
    assert "roadmap/sequence.md" in text
    assert "roadmap/parking-lot.md" in text
    assert "roadmap/archive/release-roadmap-pre-split.md" in text
    assert "## Release R1 —" not in text


def test_focused_roadmap_files_cover_active_and_future_releases_once() -> None:
    r15 = read(ROADMAP_DIR / "r15.md")
    focused = [
        read(ROADMAP_DIR / "r16-r20.md"),
        read(ROADMAP_DIR / "r21-r24.md"),
        read(ROADMAP_DIR / "r25-r29.md"),
        read(ROADMAP_DIR / "r30-r32.md"),
        read(ROADMAP_DIR / "r35-r37.md"),
        read(ROADMAP_DIR / "r38.md"),
        read(ROADMAP_DIR / "r39.md"),
        read(ROADMAP_DIR / "r40.md"),
        read(ROADMAP_DIR / "r41.md"),
    ]

    assert len(re.findall(r"^# R15 — Validated Value Modeling$", r15, re.MULTILINE)) == 1

    combined_future = "\n".join(focused)
    for release in range(16, 42):
        matches = re.findall(rf"^## Release R{release}\b", combined_future, re.MULTILINE)
        assert len(matches) == 1, f"R{release} should appear exactly once in focused roadmap detail"

    combined = "\n".join([r15, combined_future])
    for release in range(1, 15):
        assert not re.search(rf"^## Release R{release}\b", combined, re.MULTILINE)


def test_sequence_and_parking_material_have_dedicated_files() -> None:
    sequence = read(ROADMAP_DIR / "sequence.md")
    parking = read(ROADMAP_DIR / "parking-lot.md")

    assert "R8  — Server Execution Mode" in sequence
    assert "R21 — Numeric Source & Portable Representation" in sequence
    assert "R24 — C++ Minimal Conforming Host" in sequence
    assert "R28 — Genia MCP Server" in sequence
    assert "R29 — Sheet Record Pipelines" in sequence
    assert "R37 — Unified Events & Subscriptions" in sequence
    assert "R38 — Portable Actors, Messaging & Supervision" in sequence
    assert "R39 — Genia-Native Conformance Tooling" in sequence
    assert "R40 — Configuration and Secret Hardening and Ergonomics" in sequence
    assert "R41 — Portable Core IR Artifacts" in sequence
    assert "R8 through R23 are complete" in sequence
    assert "## Parking Lot / Later" in parking
    assert "## Post-R1 Issue Disposition" in parking
    assert "#102" in parking


def test_frozen_archive_preserves_monolithic_roadmap_history() -> None:
    archive = read(ROADMAP_DIR / "archive" / "release-roadmap-pre-split.md")

    assert archive.startswith("# Genia Release Roadmap")
    for release in range(1, 24):
        matches = re.findall(rf"^## Release R{release}\b", archive, re.MULTILINE)
        assert len(matches) == 1, f"archive should preserve one detailed R{release} section"

    assert "## R8–R23 Sequence and Dependencies" in archive
    assert "## Parking Lot / Later" in archive
    assert "## Post-R1 Issue Disposition" in archive
