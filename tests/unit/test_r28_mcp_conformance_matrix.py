"""R28 E28-5 (issue #706): the checked-in conformance matrix cannot silently rot.

`docs/mcp/conformance-matrix.md` is the durable evidence record E28-6 audits. This module checks
that every test it cites exists, that every row carries a legal status, that the corpus sizes it
states match the code, and that it keeps the honesty statements (R28 not complete; no HTTP; no C++;
no VS Code run claimed). Documentation-consistency test of the Python-host test suite.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.fixtures.r28_mcp_helpers import REPO_ROOT

pytestmark = pytest.mark.unit

MATRIX = REPO_ROOT / "docs" / "mcp" / "conformance-matrix.md"
UNIT = REPO_ROOT / "tests" / "unit"
KEYS = {
    "surface": "test_r28_mcp_conformance_surface.py",
    "run": "test_r28_mcp_conformance_run.py",
    "security": "test_r28_mcp_conformance_security.py",
    "lifecycle": "test_r28_mcp_conformance_lifecycle.py",
    "e1": "test_r28_mcp_skeleton.py",
    "e2": "test_r28_mcp_parse.py",
    "e3run": "test_r28_mcp_run.py",
    "e3sup": "test_r28_mcp_run_supervisor.py",
    "e3wrk": "test_r28_mcp_run_worker.py",
    "e4cfg": "test_r28_mcp_stdio_config.py",
    "e4launch": "test_r28_mcp_stdio_launch.py",
    "e4life": "test_r28_mcp_stdio_lifecycle.py",
    "arch": "test_r28_mcp_architecture.py",
    "launcher": "test_r28_mcp_launcher.py",
    "client": "test_r28_mcp_official_client.py",
    "demo": "test_r28_mcp_demo.py",
    "entry": "test_r28_mcp_entrypoint.py",
    "gate": "test_r28_release_gate.py",
    "compat": "test_r28_mcp_compat.py",
    "lprofile": "test_r28_mcp_language_profile.py",
    "compatconf": "test_r28_mcp_compat_conformance.py",
    "port": "test_r28_mcp_portability.py",
}
STATUSES = {"PASS", "KNOWN LIMITATION", "NOT APPLICABLE"}
REF = re.compile(r"`(" + "|".join(KEYS) + r")::(test_[A-Za-z0-9_]+)`")


def _text():
    assert MATRIX.is_file(), "the E28-5 matrix is missing"
    return MATRIX.read_text(encoding="utf-8")


def _rows():
    for line in _text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| ") and cells and re.match(r"^[A-Z](\d|-)", cells[0]) and cells[0] != "ID":
            yield cells


def test_every_cited_test_exists():
    refs = REF.findall(_text())
    assert len(refs) >= 120, "the matrix cites too little evidence"
    missing = []
    for key, name in refs:
        source = (UNIT / KEYS[key]).read_text(encoding="utf-8")
        if not re.search(rf"^def {name}\(", source, re.M):
            missing.append(f"{key}::{name}")
    assert not missing, f"matrix cites tests that do not exist: {sorted(set(missing))}"


def test_every_row_has_a_legal_status_and_evidence_unless_not_applicable():
    rows = list(_rows())
    assert len(rows) >= 100
    for cells in rows:
        status = cells[-1]
        assert status.split(" (")[0] in STATUSES, cells[0]
        if status != "NOT APPLICABLE":
            joined = "|".join(cells)
            assert REF.search(joined) or "recorded in the E28-5 report" in joined or "ledger [H" in joined, cells[0]


def test_row_ids_are_unique_within_the_document():
    ids = [cells[0] for cells in _rows()]
    assert len(ids) == len(set(ids))


def test_stated_corpus_sizes_match_the_code():
    from tests.unit import test_r28_mcp_conformance_run as run
    from tests.unit import test_r28_mcp_conformance_security as security

    text = _text()
    assert f"has {len(run.CORPUS)} programs" in text
    assert f"{len(security.CASES)} attempts in `AUTHORITY`" in text
    assert f"{len(security.DENIED_NAMES)} denied names" in text
    assert f"for {len(security.PROTECTED_PROGRAMS)} programs" in text


def test_the_matrix_keeps_its_honesty_statements():
    text = _text()
    assert "**R28 is complete**" in text
    assert "E28-6" in text
    assert re.search(r"Z4 \| Streamable HTTP parity .* NOT APPLICABLE", text)
    assert re.search(r"Z5 \| C\+\+ MCP parity .* NOT APPLICABLE", text)
    assert "**run 3 passed**" in text  # the authentic acceptance run (Z3)
    assert "not a sandbox" in text or "never the security contract" in text
    for banned in ("fully aligned", "complete coverage", "no drift", "all examples"):
        assert banned not in text.lower()


def test_every_unit_module_the_matrix_relies_on_is_a_real_file():
    for name in KEYS.values():
        assert Path(UNIT / name).is_file(), name
