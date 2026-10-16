"""Python-only F2/P2-G closeout guards (issue #1067, tracker #1229, retirement #1230, follow-up #1238).

Pins two implemented facts the closeout documentation states: the temporary module-to-entry fallback is gone
from code and STATE (removed under #1230), and the entry-declaration record lists successful
declarations only (a failed declaration of an existing runtime-owned name never lists that runtime binding
in the entry inspection view; #1238 N1 / R01, corrected after the independent review of PR #1244).
"""

import pytest

from genia import make_program_env, run_source
from tests.unit.f2_p2_support import ROOT

MARKER = "TEMPORARY COMPATIBILITY FALLBACK"


def test_removed_fallback_leaves_no_marker_in_source_or_state():
    """P3 removal (#1230): the temporary fallback's marker and symbols remain nowhere in code or STATE."""
    for path in sorted((ROOT / "src").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert MARKER not in text and "temporary_compatibility_fallback_read" not in text, path
    assert MARKER not in (ROOT / "GENIA_STATE.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("source,error", [("first(x) = x", TypeError), ("open log(x) = x", Exception)])
def test_failed_declaration_of_existing_runtime_name_is_not_recorded(source, error):
    """#1238 N1 / R01: the record is written only after the bind succeeded.

    A failed declaration neither lists the existing runtime binding in the entry inspection view (REPL
    `:env`, debugger entry globals) nor makes the entry the owner of it. Fuller coverage, including
    assignment, MCP-denied names and nested success, is in test_f2_p2_corrections.py.
    """
    entry = make_program_env([])
    run_source("length([1])", entry)  # loads the list prelude so `first` exists
    runtime = entry.runtime_scope()
    name = "first" if source.startswith("first") else "log"
    assert name in runtime.values and name not in entry.entry_declared_runtime_owned
    with pytest.raises(error):
        run_source(source, entry)
    assert name not in entry.entry_declared_runtime_owned
    assert name not in entry.inspection_bindings() and name not in entry.values
