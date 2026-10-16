"""Python-only repository-module load inventory under module/entry isolation (#1230, F2/P2-F, P3 removal).

Imports every repository module (packaged `web`/`resource`/`execution` and the example modules) from a
registered entry scope. With the module-to-entry fallback removed, a module that read an entry name at its top
level would fail to load. Only top-level evaluation and module loading are executed here (function bodies run
in their own tests); this is not coverage of every repository program.
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
def test_repository_module_loads_from_a_registered_entry_without_reading_entry_names(name, path):
    """Loading the module evaluates its top level in M; no entry-name read is possible, so the load succeeds."""
    from tests.unit.f2_p2_support import ROOT

    entry = make_program_env([])
    requester = str(ROOT / "examples" / "entry.genia")
    alias = name.replace("-", "_")
    run_source(f"import {name} as {alias}", entry, filename=requester)
    assert entry.get(alias).name == name
