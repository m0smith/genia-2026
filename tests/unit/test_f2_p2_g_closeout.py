"""Python-only F2/P2-G closeout guards (issue #1067, tracker #1229, retirement #1230, follow-up #1238).

Pins two implemented facts the closeout documentation states: the temporary fallback is one isolated,
marked, singly-called path (so P3 removal is a deletion), and the entry-declaration record is an attempt
record (a failed declaration of an existing runtime-owned name can list that runtime binding in the entry
inspection view). The second is a known, documented limitation, not an endorsed semantic: changing it
(recording after success) is a deliberate follow-up that must flip this test.
"""

import ast
import re

import pytest

from genia import make_program_env, run_source
from tests.unit.f2_p2_support import ROOT

MARKER = "TEMPORARY COMPATIBILITY FALLBACK"


def test_fallback_is_one_isolated_marked_path_with_one_call_site():
    """The marker names the single fallback function; only the evaluator's identifier resolution calls it."""
    callers = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "temporary_compatibility_fallback_read":
                callers.append((str(path.relative_to(ROOT)), node.lineno))
    assert [path for path, _ in callers] == ["src/genia/evaluator.py"], callers
    module = (ROOT / "src/genia/module_fallback.py").read_text(encoding="utf-8")
    function = next(n for n in ast.parse(module).body if isinstance(n, ast.FunctionDef) and n.name == "temporary_compatibility_fallback_read")
    assert MARKER in ast.get_docstring(function)
    assert len(re.findall(MARKER, (ROOT / "GENIA_STATE.md").read_text(encoding="utf-8"))) == 1


@pytest.mark.parametrize("source,error", [("first(x) = x", TypeError), ("open log(x) = x", Exception)])
def test_failed_declaration_of_existing_runtime_name_is_recorded_as_an_attempt(source, error):
    """#1238 N1: the record is written when the name is routed, before the bind can fail.

    Observable effect: the entry inspection view (REPL `:env`, debugger entry globals) can list a runtime
    binding the entry never successfully declared. Runtime-owned names pruned by the host are rejected
    before recording, and the entry never gains authority over the runtime binding. Pinned as documented.
    """
    entry = make_program_env([])
    run_source("length([1])", entry)  # loads the list prelude so `first` exists
    runtime = entry.runtime_scope()
    name = "first" if source.startswith("first") else "log"
    assert name in runtime.values and name not in entry.entry_declared_runtime_owned
    with pytest.raises(error):
        run_source(source, entry)
    assert name in entry.entry_declared_runtime_owned
    assert name in entry.inspection_bindings() and name not in entry.values
