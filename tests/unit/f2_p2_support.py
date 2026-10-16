"""Python-only P2 red-test support; never substitutes a child Env for registered E.

The approved API is Env.create_entry_scope (§16.6.1). Missing APIs fail during
execution with an explicit marker, rather than breaking pytest collection.
"""

from dataclasses import dataclass
from pathlib import Path

import pytest

from genia import make_global_env, run_source


ROOT = Path(__file__).resolve().parents[2]


def register_entry(runtime):
    """Call the approved host operation or report an intentional API-absence red."""
    operation = getattr(runtime, "create_entry_scope", None)
    if not callable(operation):
        pytest.fail("P2-C API missing: Env.create_entry_scope() (§16.6.1)")
    return operation()


@dataclass
class Scopes:
    """Real R/E/M owners plus captured runtime output, with a real module loader."""

    runtime: object
    entry: object
    module: object
    output: list
    directory: Path

    def load(self, source, name="scope_probe"):
        """Import source from a temporary file and return its actual module value."""
        (self.directory / f"{name}.genia").write_text(source, encoding="utf-8")
        run_source(f"import {name}", self.entry, filename=str(self.directory / "entry.genia"))
        return self.entry.get(name)


def separated_scopes(tmp_path, *, prune=None, prepare=None):
    """Build R through production, finish host work, register E, and load real M.

    Alias rejection is mandatory: shared-root or manually fabricated scopes
    cannot supply evidence for #1221. No accessor or lookup is mocked here.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    output = []
    runtime = make_global_env([], output_handler=output.append)
    if prepare:
        prepare(runtime)
    if prune:
        prune(runtime)
    entry = register_entry(runtime)
    assert entry is not runtime, "P2 registration aliased E and R"
    assert entry.parent is runtime
    assert not (set(entry.values) & set(runtime.values)), "R/E setup bindings overlap"
    assert entry.autoloads == {} and runtime.autoloads
    scopes = Scopes(runtime, entry, None, output, tmp_path)
    module = scopes.load("module_marker = 23\nprobe() = module_marker")
    scopes.module = module.exports["probe"].get(0).closure
    assert scopes.module is not entry and scopes.module is not runtime
    assert scopes.module.parent is runtime
    return scopes


def program_env(**kwargs):
    """Use an existing production construction path for behavioral reds on P1."""
    from genia.test_cli import make_test_env

    entry, _registrations = make_test_env(**kwargs)
    return entry


def load_program_module(tmp_path, entry, source, name="behavior_probe"):
    """Load a real file into a host-constructed execution; no topology emulation."""
    (tmp_path / f"{name}.genia").write_text(source, encoding="utf-8")
    run_source(f"import {name}", entry, filename=str(tmp_path / "entry.genia"))
    return entry.get(name)


def wrong_accessor(monkeypatch, owner, accessor, replacement):
    """Inject one wrong owner at a production accessor seam for mutation evidence.

    The consumer remains real. Callers must assert the same observation succeeds
    without mutation and raises AssertionError with it; aliasing is forbidden.
    """
    assert getattr(owner, accessor)() is not replacement
    monkeypatch.setattr(owner, accessor, lambda: replacement)
