"""Python-only F2/P2-D consumer tests (contract 16.2, 16.4, 16.6; issue #1067, tracker #1229).

Supplements the P2-B suite with paths it does not exercise: every identifier-resolution
path that binds reflective builtins, bound-callable identity and caching, `eval` base
isolation from modules, entry inspection views, and runtime-owned debug state. Host
internals only; reflective scope binding is portable only where shared specs say so.
"""

import pytest

from genia import make_program_env, run_source
from genia.values import GeniaOptionNone
from tests.unit.f2_p2_support import separated_scopes


def test_pipeline_call_and_bare_stage_bind_reflection_to_the_evaluating_scope(tmp_path):
    """Both pipeline name paths resolve `doc` in the evaluating scope (entry sees E, module does not)."""
    s = separated_scopes(tmp_path)
    run_source('@doc "entry docs"\nentry_subject(x) = x', s.entry)
    s.load('probe() = "entry_subject" |> doc', "pipe_bare_module")
    s.load('probe() = "entry_subject" |> doc()', "pipe_call_module")
    assert run_source('"entry_subject" |> doc', s.entry) == "entry docs"
    assert run_source('"entry_subject" |> doc()', s.entry) == "entry docs"
    for module in ("pipe_bare_module", "pipe_call_module"):
        assert isinstance(run_source(f"{module}.probe()", s.entry), GeniaOptionNone)


def test_module_reflection_cannot_name_entry_only_binding_but_names_its_own(tmp_path):
    """16.2: no fallback for reflection; module-local names resolve."""
    s = separated_scopes(tmp_path)
    run_source('@doc "entry docs"\nentry_subject(x) = x\nentry_marker = 1', s.entry)
    s.load('@doc "own docs"\nown(x) = x\nprobe() = [doc("own"), doc("entry_subject"), meta("entry_marker")]', "reflect_module")
    own, entry_doc, entry_meta = run_source("reflect_module.probe()", s.entry)
    assert own == "own docs"
    assert isinstance(entry_doc, GeniaOptionNone) and isinstance(entry_meta, GeniaOptionNone)


def test_reflective_value_in_data_structures_keeps_the_scope_it_was_read_in(tmp_path):
    """A bound callable stored in a map and read back is the same bound object (explicit grant)."""
    s = separated_scopes(tmp_path)
    run_source('@doc "entry docs"\nentry_subject(x) = x\nholder = {reflect: doc}', s.entry)
    s.load('probe(h) = {\n  f = unwrap_or(none, get("reflect", h))\n  f("entry_subject")\n}', "holder_module")
    assert run_source("holder_module.probe(holder)", s.entry) == "entry docs"


def test_user_rebinding_of_reflective_names_stays_ordinary(tmp_path):
    """Value-based marking: a user function named like a target is never rebound."""
    s = separated_scopes(tmp_path)
    run_source('help = (name) -> "user help"\nmeta = (name) -> "user meta"', s.entry)
    assert run_source('help("anything")', s.entry) == "user help"
    assert run_source('meta("anything")', s.entry) == "user meta"


def test_unregistered_helper_is_resolvable_but_not_promoted_into_help(tmp_path):
    """16.2/A1: map_acc is runtime-owned and documentable on demand, yet absent from the help catalogue."""
    s = separated_scopes(tmp_path)
    run_source("length([1])", s.entry)
    assert isinstance(run_source('doc("map_acc")', s.entry), GeniaOptionNone)
    s.output.clear()
    run_source("help()", s.entry)
    assert "map_acc" not in "".join(s.output)


@pytest.mark.parametrize("origin", ["entry", "module"])
def test_empty_env_base_hides_entry_names_from_entry_and_module_alike(tmp_path, origin):
    """16.4: eval over `empty_env()` cannot read E-resident names; `define` supplies them explicitly."""
    s = separated_scopes(tmp_path)
    run_source("entry_f(x) = x + 1\nentry_marker = 17", s.entry)
    s.load("probe() = eval(quote(entry_marker), empty_env())\nexplicit() = eval(quote(entry_marker), define(empty_env(), quote(entry_marker), 5))", "eval_module")
    if origin == "entry":
        with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
            run_source("eval(quote(entry_marker), empty_env())", s.entry)
    else:
        with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
            run_source("eval_module.probe()", s.entry)
        assert run_source("eval_module.explicit()", s.entry) == 5


def test_entry_inspection_bindings_list_entry_and_declared_runtime_owned_names_only():
    """16.1.4: E view = own bindings plus declared runtime-owned names; an R view shows runtime bindings."""
    entry = make_program_env([])
    run_source("zzz = 1\nlog = 5\nmap_acc(f, xs, acc) = acc", entry)
    view = entry.inspection_bindings()
    assert list(view)[:1] == ["zzz"] and set(view) == {"zzz", "log", "map_acc"}
    assert entry.entry_binding_owner("log") is entry.runtime_scope()
    assert entry.entry_binding_owner("print") is None and entry.entry_binding_owner("zzz") is entry
    assert "stdout" in entry.runtime_scope().inspection_bindings()


def test_debug_state_is_owned_by_runtime_once_entry_is_registered():
    """16.6.3: hooks/mode are written on R by run_source with a registered E; legacy roots keep P1 behavior."""
    from genia import make_global_env
    from genia.callable import DebugHooks

    hooks = DebugHooks()
    entry = make_program_env([])
    run_source("1", entry, debug_hooks=hooks, debug_mode=True)
    runtime = entry.runtime_scope()
    assert runtime.debug_hooks is hooks and runtime.debug_mode is True
    assert entry.debug_hooks is None and not entry.debug_mode
    root = make_global_env([])
    run_source("1", root, debug_hooks=hooks)
    assert root.debug_hooks is hooks and root.debug_state_scope() is root
