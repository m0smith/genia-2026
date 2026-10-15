"""Python-only executed-program inventory for the temporary fallback's retirement evidence (#1230, F2/P2-F).

Imports every repository module (packaged `web`/`resource`/`execution` and the example modules) from a
registered entry scope in default mode, where a fallback read would be recorded, and asserts none was. Only
top-level evaluation and module loading are executed here (function bodies run in their own tests and in the
suite-wide measurement recorded in the P2-F evidence); this is not coverage of every repository program.
"""

import pytest

from genia import make_program_env, run_source

MODULES = [
    ("web", None),
    ("resource", None),
    ("execution", None),
    ("ants", "examples/ants.genia"),
    ("tic-tac-toe", "examples/tic-tac-toe.genia"),
    ("r12_grounded_context_answer", "examples/r12_grounded_context_answer.genia"),
    ("ants_terminal", "examples/ants_terminal.genia"),
    ("ants_actor", "examples/ants_actor.genia"),
]


@pytest.mark.parametrize("name,path", MODULES)
@pytest.mark.parametrize("strict", [False, True])
def test_repository_module_loads_from_a_registered_entry_without_fallback_events(name, path, strict, monkeypatch):
    """Loading the module evaluates its top level in M with no entry-name read, in default and strict mode."""
    from tests.unit.f2_p2_support import ROOT

    if strict:
        monkeypatch.setenv("GENIA_STRICT_MODULE_SCOPE", "1")
    else:
        monkeypatch.delenv("GENIA_STRICT_MODULE_SCOPE", raising=False)
    entry = make_program_env([])
    requester = str(ROOT / "examples" / "entry.genia")
    alias = name.replace("-", "_")
    run_source(f"import {name} as {alias}", entry, filename=requester)
    assert entry.runtime_scope().fallback_events == set()
    assert entry.runtime_scope().strict_module_scope is strict
    assert entry.get(alias).name == name
