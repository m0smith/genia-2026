"""Automated drift guard for docs/design/composability-matrix.md.

The composability matrix is a hand-authored design aid, but the Template /
representation / matcher family it documents is a real, growing part of the
public builtin surface (`*_match` helpers, `represent`, `strip_representation`,
and the `json_decode` / `json_encode` / `json_schema` boundary). Nothing else
in the repo re-derives that family from source and checks it against the
matrix, so a newly added or renamed member of the family could land without
anyone updating the matrix.

These tests close that gap by deriving the family directly from
`src/genia/builtins.py` and `src/genia/std/prelude/*.genia` — the same source
GENIA_STATE.md itself is written from — rather than hand-maintaining a second
copy of the name list here. Whenever the derived set changes, these tests
change what they check without any edits, so the matrix (and, as a
cross-check, GENIA_STATE.md) must be updated to keep pace or the tests fail.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MATRIX_PATH = REPO / "docs" / "design" / "composability-matrix.md"
STATE_PATH = REPO / "GENIA_STATE.md"
BUILTINS_PATH = REPO / "src" / "genia" / "builtins.py"
PRELUDE_DIR = REPO / "src" / "genia" / "std" / "prelude"

# The naming convention actually used by the implemented Template /
# representation family today: every structural/refinement/representation
# matcher ends in `_match`, plus the fixed carrier/boundary names below.
# A new helper that follows this convention is picked up automatically; a
# helper that does NOT follow it is, by definition, outside what this guard
# can infer and must be added to the pattern deliberately (with a matching
# matrix update in the same change).
FAMILY_PATTERN = re.compile(
    r"^(represent|strip_representation|json_decode|json_encode|json_schema|.*_match)$"
)

_ENV_SET_NAME = re.compile(r'env\.set(?:_internal)?\(\s*"([A-Za-z_][A-Za-z0-9_?]*)"')
_PRELUDE_DEF_NAME = re.compile(r"(?m)^([a-zA-Z_][a-zA-Z0-9_?]*)\([^\n]*\)\s*(?:=|->)")


def _mentions_name(text: str, name: str) -> bool:
    """True if `name` appears inside inline code in `text`, either bare
    (`` `name` ``) or as the head of a call span (`` `name(...)` ``)."""
    return re.search(rf"`{re.escape(name)}(?:`|\()", text) is not None


def _template_representation_family() -> set[str]:
    builtins_text = BUILTINS_PATH.read_text(encoding="utf-8")
    names = set(_ENV_SET_NAME.findall(builtins_text))

    for genia_file in PRELUDE_DIR.glob("*.genia"):
        names.update(_PRELUDE_DEF_NAME.findall(genia_file.read_text(encoding="utf-8")))

    return {name for name in names if FAMILY_PATTERN.match(name)}


FAMILY = sorted(_template_representation_family())


def test_template_representation_family_is_non_empty_and_stable() -> None:
    """Sanity check on the derivation itself: if this ever comes back empty
    or drops a name every reviewer would expect (the E9-1..E9-6 core), the
    extraction pattern has broken, not the feature set."""
    expected_minimum = {
        "refinement_match",
        "open_shape_match",
        "exact_shape_match",
        "representation_match",
        "represent",
        "strip_representation",
        "json_decode",
        "json_encode",
        "json_schema",
    }
    assert expected_minimum <= set(FAMILY), (
        "Template/representation family extraction from src/genia/builtins.py "
        "and src/genia/std/prelude/*.genia is missing expected R9 names; the "
        f"extraction pattern may have broken. Found: {FAMILY}"
    )


@pytest.mark.parametrize("name", FAMILY)
def test_composability_matrix_documents_every_template_representation_builtin(
    name: str,
) -> None:
    text = MATRIX_PATH.read_text(encoding="utf-8")
    assert _mentions_name(text, name), (
        f"docs/design/composability-matrix.md does not mention `{name}`. "
        "A Template/representation/matcher-family builtin (name ending in "
        "`_match`, or `represent`/`strip_representation`/`json_decode`/"
        "`json_encode`/`json_schema`) was added, renamed, or removed in "
        "src/genia/builtins.py or src/genia/std/prelude/*.genia without a "
        "matching update to the composability matrix. Update the matrix's "
        "'Current foundation' or 'R9 relationships' table to cover it."
    )


@pytest.mark.parametrize("name", FAMILY)
def test_genia_state_documents_every_template_representation_builtin(name: str) -> None:
    """GENIA_STATE.md is final authority; the matrix must never describe a
    builtin STATE itself does not document."""
    text = STATE_PATH.read_text(encoding="utf-8")
    assert _mentions_name(text, name), (
        f"GENIA_STATE.md does not mention `{name}`, but it exists as a "
        "Template/representation-family builtin. GENIA_STATE.md is final "
        "authority for implemented behavior and must document it before the "
        "composability matrix (or anything else) can rely on it."
    )


def test_composability_matrix_has_no_stale_family_style_names() -> None:
    """Reverse direction: every backticked identifier in the matrix that
    itself looks like a family member (matches FAMILY_PATTERN) must
    correspond to a builtin that actually exists. This catches a rename or
    removal in code that left a stale mention behind in the matrix."""
    text = MATRIX_PATH.read_text(encoding="utf-8")
    mentioned = {
        token
        for token in re.findall(r"`([A-Za-z_][A-Za-z0-9_?]*)(?:`|\()", text)
        if FAMILY_PATTERN.match(token)
    }
    stale = mentioned - set(FAMILY)
    assert not stale, (
        "docs/design/composability-matrix.md mentions Template/representation-"
        f"family name(s) that no longer exist as builtins: {sorted(stale)}. "
        "Either the matrix is stale (the builtin was renamed/removed and the "
        "matrix wasn't updated) or the name legitimately isn't part of this "
        "family and should be phrased without the exact `name` code span."
    )


def test_composability_matrix_keeps_its_non_authoritative_disclaimer() -> None:
    """The matrix must never start claiming to be authoritative itself —
    that would make future drift invisible instead of merely undetected."""
    text = MATRIX_PATH.read_text(encoding="utf-8")
    unquoted = "\n".join(
        line[2:] if line.startswith("> ") else line for line in text.splitlines()
    )
    normalized = " ".join(unquoted.split())
    assert "PROPOSED / EXPLORATORY" in normalized
    assert "does not define implemented behavior" in normalized
    assert "`GENIA_STATE.md` is final authority" in normalized


def test_composability_matrix_r9_section_present() -> None:
    text = MATRIX_PATH.read_text(encoding="utf-8")
    assert "## R9 relationships" in text
