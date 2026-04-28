"""Structural invariant tests for hosts/template/.

All 14 invariants from spec: docs/architecture/issue-127-host-template-spec.md §5

These tests fail before the template directory and its files exist.
They pass once implementation and pointer edits are complete.
No Genia runtime imports — pathlib only.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "hosts" / "template"

AGENTS_MD = TEMPLATE / "AGENTS.md"
README_MD = TEMPLATE / "README.md"
CAP_STATUS = TEMPLATE / "CAPABILITY_STATUS.md"
ADAPTER_STUB = TEMPLATE / "adapter_stub.md"
CI_STUB = TEMPLATE / "ci_stub.md"
EXAMPLE_MD = TEMPLATE / "EXAMPLE.md"

CAPABILITIES_MD = REPO / "docs" / "host-interop" / "capabilities.md"
PORTING_GUIDE = REPO / "docs" / "host-interop" / "HOST_PORTING_GUIDE.md"
CAP_MATRIX = REPO / "docs" / "host-interop" / "HOST_CAPABILITY_MATRIX.md"
HOST_INTEROP = REPO / "docs" / "host-interop" / "HOST_INTEROP.md"
GENIA_STATE = REPO / "GENIA_STATE.md"

PLANNED_HOST_READMES = [
    REPO / "hosts" / "node" / "README.md",
    REPO / "hosts" / "go" / "README.md",
    REPO / "hosts" / "java" / "README.md",
    REPO / "hosts" / "rust" / "README.md",
    REPO / "hosts" / "cpp" / "README.md",
]

# Required section headings from spec §4.2
README_REQUIRED_HEADINGS = [
    "## Status",
    "## Goal",
    "## Required Reading",
    "## Minimal Host Requirements",
    "## Optional Capabilities",
    "## Setup",
    "## Build",
    "## Test",
    "## Lint",
    "## Known commands",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_capability_names_from_registry(text: str) -> set[str]:
    """Extract all capability names from capabilities.md using the **name:** marker."""
    pattern = re.compile(r'\*\*name:\*\*\s+`([^`]+)`')
    return {m.group(1) for m in pattern.finditer(text)}


def _extract_capability_names_from_status(text: str) -> set[str]:
    """Extract capability name cells from CAPABILITY_STATUS.md table rows.

    Expects rows of the form: | name | Status | Notes |
    Skips the header row (which contains 'Capability') and separator rows.
    """
    names: set[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells:
            continue
        first = cells[0]
        # Skip header row and separator rows
        if first in ("Capability", "---", ":---", "---:") or set(first) <= {"-", ":"}:
            continue
        if first:
            names.append(first)
    return set(names)


# ---------------------------------------------------------------------------
# Invariant 0 — required files exist (prerequisite for all other tests)
# ---------------------------------------------------------------------------


def test_template_required_files_exist() -> None:
    """All six required template files must be present."""
    missing = [p for p in (AGENTS_MD, README_MD, CAP_STATUS, ADAPTER_STUB, CI_STUB, EXAMPLE_MD) if not p.exists()]
    assert not missing, f"Missing template files: {[str(p.relative_to(REPO)) for p in missing]}"


# ---------------------------------------------------------------------------
# Invariant 1 — AGENTS.md contains status label
# ---------------------------------------------------------------------------


def test_agents_md_status_label() -> None:
    """Inv 1: hosts/template/AGENTS.md must contain 'scaffolded, not implemented'."""
    text = _read(AGENTS_MD)
    assert "scaffolded, not implemented" in text


# ---------------------------------------------------------------------------
# Invariant 2 — README.md contains status label
# ---------------------------------------------------------------------------


def test_readme_status_label() -> None:
    """Inv 2: hosts/template/README.md must contain 'scaffolded, not implemented'."""
    text = _read(README_MD)
    assert "scaffolded, not implemented" in text


# ---------------------------------------------------------------------------
# Invariant 3 — README.md references HOST_PORTING_GUIDE.md
# ---------------------------------------------------------------------------


def test_readme_references_porting_guide() -> None:
    """Inv 3: hosts/template/README.md must reference HOST_PORTING_GUIDE.md."""
    text = _read(README_MD)
    assert "HOST_PORTING_GUIDE.md" in text


# ---------------------------------------------------------------------------
# Invariant 4 — README.md references HOST_CAPABILITY_MATRIX.md
# ---------------------------------------------------------------------------


def test_readme_references_capability_matrix() -> None:
    """Inv 4: hosts/template/README.md must reference HOST_CAPABILITY_MATRIX.md."""
    text = _read(README_MD)
    assert "HOST_CAPABILITY_MATRIX.md" in text


# ---------------------------------------------------------------------------
# Invariant 5 — CAPABILITY_STATUS.md has no Implemented (plain) status rows
# ---------------------------------------------------------------------------


def test_capability_status_no_implemented_rows() -> None:
    """Inv 5: CAPABILITY_STATUS.md must not contain 'Implemented' as a status cell value.

    'Not Implemented' is allowed. Plain 'Implemented' is not.
    Uses a regex that matches '| Implemented |' but not '| Not Implemented |'.
    """
    text = _read(CAP_STATUS)
    bad = re.findall(r'\|\s+Implemented\s+\|', text)
    assert not bad, (
        f"CAPABILITY_STATUS.md contains plain 'Implemented' status cells: {bad}"
    )


# ---------------------------------------------------------------------------
# Invariant 6 — CAPABILITY_STATUS.md references capabilities.md
# ---------------------------------------------------------------------------


def test_capability_status_references_capabilities_md() -> None:
    """Inv 6: CAPABILITY_STATUS.md must reference capabilities.md."""
    text = _read(CAP_STATUS)
    assert "capabilities.md" in text


# ---------------------------------------------------------------------------
# Invariant 7 — all capability names in CAPABILITY_STATUS.md exist in capabilities.md
# ---------------------------------------------------------------------------


def test_capability_status_no_invented_names() -> None:
    """Inv 7: every capability name in CAPABILITY_STATUS.md must appear in capabilities.md."""
    registry_text = _read(CAPABILITIES_MD)
    status_text = _read(CAP_STATUS)

    valid_names = _extract_capability_names_from_registry(registry_text)
    listed_names = _extract_capability_names_from_status(status_text)

    assert valid_names, "capabilities.md yielded no capability names — extraction regex may be broken"
    assert listed_names, "CAPABILITY_STATUS.md yielded no capability names — table may be missing or malformed"

    invented = listed_names - valid_names
    assert not invented, (
        f"CAPABILITY_STATUS.md contains names not in capabilities.md: {sorted(invented)}"
    )


# ---------------------------------------------------------------------------
# Invariant 8 — adapter_stub.md contains run_case
# ---------------------------------------------------------------------------


def test_adapter_stub_contains_run_case() -> None:
    """Inv 8: hosts/template/adapter_stub.md must contain 'run_case'."""
    text = _read(ADAPTER_STUB)
    assert "run_case" in text


# ---------------------------------------------------------------------------
# Invariant 9 — adapter_stub.md references HOST_INTEROP.md
# ---------------------------------------------------------------------------


def test_adapter_stub_references_host_interop() -> None:
    """Inv 9: hosts/template/adapter_stub.md must reference HOST_INTEROP.md."""
    text = _read(ADAPTER_STUB)
    assert "HOST_INTEROP.md" in text


# ---------------------------------------------------------------------------
# Invariant 10 — EXAMPLE.md references both required guide docs
# ---------------------------------------------------------------------------


def test_example_references_required_docs() -> None:
    """Inv 10: EXAMPLE.md must reference both HOST_PORTING_GUIDE.md and HOST_CAPABILITY_MATRIX.md."""
    text = _read(EXAMPLE_MD)
    assert "HOST_PORTING_GUIDE.md" in text
    assert "HOST_CAPABILITY_MATRIX.md" in text


# ---------------------------------------------------------------------------
# Invariant 11 — HOST_PORTING_GUIDE.md references hosts/template/
# ---------------------------------------------------------------------------


def test_porting_guide_references_template() -> None:
    """Inv 11: HOST_PORTING_GUIDE.md must reference hosts/template/."""
    text = _read(PORTING_GUIDE)
    assert "hosts/template/" in text


# ---------------------------------------------------------------------------
# Invariant 12 — all planned-host READMEs reference hosts/template/
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("readme", PLANNED_HOST_READMES, ids=lambda p: p.parts[-2])
def test_planned_host_readmes_reference_template(readme: Path) -> None:
    """Inv 12: each planned-host README must reference hosts/template/."""
    text = _read(readme)
    assert "hosts/template/" in text, (
        f"{readme.relative_to(REPO)} does not reference hosts/template/"
    )


# ---------------------------------------------------------------------------
# Invariant 13 — HOST_CAPABILITY_MATRIX.md has no Template row
# ---------------------------------------------------------------------------


def test_capability_matrix_has_no_template_row() -> None:
    """Inv 13: HOST_CAPABILITY_MATRIX.md must not contain a 'Template' host row."""
    text = _read(CAP_MATRIX)
    # Table rows start with '| ' — check that no row has 'Template' as a cell
    bad_lines = [
        line for line in text.splitlines()
        if re.match(r'\|\s+Template\s+\|', line)
    ]
    assert not bad_lines, (
        "HOST_CAPABILITY_MATRIX.md contains a 'Template' host row (template is not a host)"
    )


# ---------------------------------------------------------------------------
# Invariant 14 — GENIA_STATE.md unchanged (anchor check)
# ---------------------------------------------------------------------------


def test_genia_state_unchanged_marker() -> None:
    """Inv 14: GENIA_STATE.md must still contain its final-authority anchor string."""
    text = _read(GENIA_STATE)
    assert "GENIA_STATE.md is the final authority for implemented behavior" in text


# ---------------------------------------------------------------------------
# Regression: README required section headings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("heading", README_REQUIRED_HEADINGS)
def test_readme_required_headings(heading: str) -> None:
    """Spec §4.2: README.md must contain all 10 required section headings."""
    text = _read(README_MD)
    assert heading in text, f"README.md missing required section: {heading!r}"


# ---------------------------------------------------------------------------
# Regression: CAPABILITY_STATUS.md footer
# ---------------------------------------------------------------------------


def test_capability_status_footer_present() -> None:
    """Spec §4.3: CAPABILITY_STATUS.md must contain the required footer warning."""
    text = _read(CAP_STATUS)
    assert "Do not mark Implemented until code, tests, and spec coverage all exist" in text


# ---------------------------------------------------------------------------
# Regression: adapter_stub.md documents all six spec categories
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("category", ["parse", "ir", "eval", "cli", "flow", "error"])
def test_adapter_stub_covers_all_categories(category: str) -> None:
    """Spec §4.4: adapter_stub.md must document a TODO stub for each spec category."""
    text = _read(ADAPTER_STUB)
    assert category in text, f"adapter_stub.md missing category stub: {category!r}"


# ---------------------------------------------------------------------------
# Regression: EXAMPLE.md contains all seven required step headings
# ---------------------------------------------------------------------------


EXAMPLE_REQUIRED_STEPS = [
    "Step 1",
    "Step 2",
    "Step 3",
    "Step 4",
    "Step 5",
    "Step 6",
    "Step 7",
]


@pytest.mark.parametrize("step", EXAMPLE_REQUIRED_STEPS)
def test_example_contains_all_steps(step: str) -> None:
    """Spec §4.6: EXAMPLE.md must contain all seven step headings."""
    text = _read(EXAMPLE_MD)
    assert step in text, f"EXAMPLE.md missing required step: {step!r}"
