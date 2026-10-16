"""Python-only F2/P3 regression: a module cannot read a calling program's variables (issue #1230).

Covers the Python-reference-host removal of the temporary module-to-entry compatibility fallback
(contract 11.4 and 16.3): a module free-name read that misses its module chain, the runtime and
autoload is the ordinary `Undefined name` error, with no warning, no event record and no strict
switch. The portable observations (module read denied, explicit passing, local writes) live in
`spec/error/f2-module-cannot-read-entry-binding.yaml` and
`spec/eval/f2-module-entry-isolation-explicit-passing-and-local-writes.yaml`; this module keeps the
Python-only observations: stderr silence, ignored environment switch, absent host state and the
host construction paths (CLI file run, native test runner).
"""

import importlib.util
import os
import subprocess
import sys

import pytest

from genia import make_global_env, run_source
from genia.environment import Env
from hosts.python.mcp_worker_profile import prune_environment
from tests.unit.f2_p2_support import ROOT, load_program_module, program_env, separated_scopes


@pytest.mark.parametrize("switch", [None, "0", "1"])
def test_module_read_of_entry_name_is_an_ordinary_name_error_whatever_the_environment(tmp_path, monkeypatch, capsys, switch):
    """Function body, lambda and top-level module reads are denied; the old strict variable has no effect."""
    if switch is None:
        monkeypatch.delenv("GENIA_STRICT_MODULE_SCOPE", raising=False)
    else:
        monkeypatch.setenv("GENIA_STRICT_MODULE_SCOPE", switch)
    s = separated_scopes(tmp_path)
    run_source("entry_marker = 17", s.entry)
    module = s.load("body() = entry_marker\nlam() = map((x) -> x + entry_marker, [1])", "denied_module")
    for name in ("body", "lam"):
        with pytest.raises(NameError) as failure:
            module.exports[name]()
        assert str(failure.value) == "Undefined name: entry_marker" and type(failure.value) is NameError
    assert capsys.readouterr().err == ""
    with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
        s.load("top_level = entry_marker", "top_level_module")


def test_module_top_level_read_through_a_host_constructed_execution_is_denied(tmp_path, capsys):
    """The host program-construction path (native test runner env) registers E and gives modules no entry reads."""
    entry = program_env()
    run_source("entry_marker = 41", entry)
    module = load_program_module(tmp_path, entry, "probe() = entry_marker", "host_module")
    with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
        module.exports["probe"]()
    assert capsys.readouterr().err == ""


def test_entry_closure_given_to_a_module_still_sees_entry_names(tmp_path):
    """Lexical scope is untouched: a closure created in the entry keeps its entry scope inside a module."""
    s = separated_scopes(tmp_path)
    run_source("entry_marker = 7\nentry_closure() = entry_marker", s.entry)
    module = s.load("call(f) = f()", "closure_module")
    assert module.exports["call"](s.entry.get("entry_closure")) == 7


def test_module_keeps_runtime_prelude_and_import_access_and_explicit_arguments(tmp_path):
    """Legitimate access is preserved: runtime builtins, prelude autoload, own names, imports, arguments."""
    s = separated_scopes(tmp_path)
    run_source("entry_marker = 3", s.entry)
    module = s.load("own = 10\nuse() = map((x) -> x + own, [1])\nadd(x) = x + 1", "legit_module")
    assert module.exports["use"]() == [11]
    assert module.exports["add"](s.entry.get("entry_marker")) == 4


def test_module_write_of_an_entry_spelled_name_never_changes_the_entry_binding(tmp_path):
    """Writes were never shared: the module assignment is local and the entry binding is unchanged."""
    s = separated_scopes(tmp_path)
    run_source("entry_marker = 5", s.entry)
    module = s.load("write() = {\n  entry_marker = 99\n  entry_marker\n}", "writer_module")
    assert module.exports["write"]() == 99
    assert run_source("entry_marker", s.entry) == 5


def test_pruned_capabilities_stay_undefined_for_modules_and_an_entry_lookalike_is_not_visible(tmp_path):
    """MCP pruning: denied capabilities are undefined in modules, and an entry value spelled like one is not conjured."""
    s = separated_scopes(tmp_path, prune=prune_environment)
    run_source("secret_get = 5", s.entry)
    module = s.load("a() = secret_get\nb() = read_file\nc() = http_operation", "pruned_module")
    for name in ("a", "b", "c"):
        with pytest.raises(NameError, match="^Undefined name: "):
            module.exports[name]()
    assert "secret_get" not in s.runtime.values


def test_inspection_and_host_lookup_from_a_module_scope_do_not_see_entry_names(tmp_path):
    """REPL/debugger inspection views, binding_owner and host get never expose an entry binding to a module scope."""
    s = separated_scopes(tmp_path)
    run_source("entry_marker = 17", s.entry)
    module = s.load("probe() = entry_marker", "inspect_module")
    scope = module.exports["probe"].get(0).closure
    assert "entry_marker" not in scope.inspection_bindings() and scope.binding_owner("entry_marker") is None
    with pytest.raises(NameError):
        scope.get("entry_marker")


def test_fallback_host_surface_is_gone():
    """No fallback module, event set, lock, strict capture or strict reader remains on the host."""
    assert importlib.util.find_spec("genia.module_fallback") is None
    for attribute in ("fallback_events", "_fallback_lock", "strict_module_scope", "init_fallback_state", "claim_fallback_event"):
        assert not hasattr(Env, attribute), attribute
    import genia.environment as environment

    assert not hasattr(environment, "strict_module_scope_requested")
    assert not hasattr(make_global_env([]), "fallback_events")


def _run_cli(tmp_path, main_source, lib_source, strict=None):
    """Run the real CLI on `main.genia` importing `lib.genia`; `strict` sets the removed switch to prove it is ignored."""
    (tmp_path / "lib.genia").write_text(lib_source, encoding="utf-8")
    (tmp_path / "main.genia").write_text(main_source, encoding="utf-8")
    env = {key: value for key, value in os.environ.items() if key != "GENIA_STRICT_MODULE_SCOPE"}
    if strict is not None:
        env["GENIA_STRICT_MODULE_SCOPE"] = strict
    return subprocess.run(
        [sys.executable, "-c", "from genia.interpreter import _main; raise SystemExit(_main())", str(tmp_path / "main.genia")],
        cwd=ROOT, env=env, text=True, capture_output=True, timeout=60, check=False,
    )


@pytest.mark.parametrize("strict", [None, "1"])
def test_cli_file_run_denies_module_read_without_warning_regardless_of_the_old_switch(tmp_path, strict):
    """The CLI file path reports the ordinary diagnostic, exit 1, and never the old warning."""
    result = _run_cli(tmp_path, "import lib\nentry_only = 5\nlib.read_entry()\n", "read_entry() = entry_only\n", strict)
    assert result.returncode == 1 and result.stdout == ""
    assert result.stderr == "Error: Undefined name: entry_only\n"
