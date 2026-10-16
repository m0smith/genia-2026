"""Python-only F2/P2-F whole-stack integration tests (issue #1067, tracker #1229, retirement #1230).

Drives real host entry paths (CLI subprocess, native-test runner, MCP worker, REPL) and one
combined registered R/E/M execution to prove the approved P2 behaviours compose. Python
reference host only: nothing here is portable language behaviour or a C++ claim; the
portable observations live in the shared specs (spec/eval/f2-*.yaml).
"""

import os
import subprocess
import sys

import pytest

from genia import make_program_env, run_source
from genia.values import GeniaOptionNone
from hosts.python import mcp_worker
from tests.unit.f2_p2_support import ROOT, load_program_module

MODULE = "lib.genia"
LIBRARY = '@doc "library docs"\nown(x) = x\nread_entry() = shared_name\nreflect_entry() = doc("entry_fn")\nreflect_own() = doc("own")\nrun_eval() = eval(quote(shared_name), empty_env())\n'
ENTRY = 'import lib\n@doc "entry docs"\nentry_fn(x) = x\nshared_name = "from-entry"\nmain(args) = [lib.read_entry(), lib.reflect_entry(), lib.reflect_own()]\n'


def run_cli(tmp_path, *args, source=ENTRY):
    """Run the real CLI entry in a subprocess over a program that imports a sibling module."""
    (tmp_path / MODULE).write_text(LIBRARY, encoding="utf-8")
    program = tmp_path / "entry.genia"
    program.write_text(source, encoding="utf-8")
    env = dict(os.environ)
    command = [sys.executable, "-c", "from genia.interpreter import _main; raise SystemExit(_main())", *args, str(program)]
    return subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=ROOT, env=env)


def test_cli_file_mode_denies_module_read_of_entry_name(tmp_path):
    """The CLI file path registers E: the module read of an entry name is the ordinary name error, no warning."""
    result = run_cli(tmp_path)
    assert result.returncode == 1
    assert result.stderr == "Error: Undefined name: shared_name\n" and result.stdout == ""


def test_cli_command_mode_runs_in_a_registered_entry_with_unit_reflection(tmp_path):
    """Command mode: entry reflection resolves the entry name; main dispatch finds the entry main."""
    (tmp_path / MODULE).write_text(LIBRARY, encoding="utf-8")
    result = subprocess.run([sys.executable, "-c", "from genia.interpreter import _main; raise SystemExit(_main())", "-c",
                             '@doc "cmd docs"\nthing(x) = x\nmain() = doc("thing")'],
                            capture_output=True, text=True, timeout=60, cwd=tmp_path,
                            env={**os.environ, "PYTHONPATH": str(ROOT / "src")})
    assert result.returncode == 0, result.stderr
    assert result.stdout == '"cmd docs"\n'


def test_combined_registered_execution_composes_every_approved_boundary(tmp_path):
    """One registered execution: R/E/M distinct, reflection bound, eval based on R, module reads of E denied."""
    entry = make_program_env([])
    runtime = entry.runtime_scope()
    run_source('@doc "entry docs"\nentry_fn(x) = x\nshared_name = "from-entry"\nlog = 5', entry)
    module = load_program_module(tmp_path, entry, LIBRARY, "lib")
    unit = module.exports["read_entry"].get(0).closure
    assert len({id(runtime), id(entry), id(unit)}) == 3 and entry.parent is runtime and unit.parent is runtime
    assert entry.entry_scope() is entry and unit.entry_scope() is entry and unit.unit_scope() is unit
    assert "shared_name" in entry.values and "shared_name" not in runtime.values and "log" in runtime.values
    assert isinstance(module.exports["reflect_entry"](), GeniaOptionNone)
    assert module.exports["reflect_own"]() == "library docs"
    with pytest.raises(NameError, match="^Undefined name: shared_name$"):
        module.exports["run_eval"]()
    with pytest.raises(NameError, match="^Undefined name: shared_name$"):
        module.exports["read_entry"]()


def test_native_test_runner_path_registers_entry_and_modules_cannot_read_entry_fixtures(tmp_path, capsys):
    """The native-test host path builds E (fixtures live there); a module read of a fixture is denied, silently."""
    from genia.test_cli import run_native_tests_from_file

    (tmp_path / "fixlib.genia").write_text("read_fixture() = fixture_marker", encoding="utf-8")
    program = tmp_path / "suite.genia"
    program.write_text('import fixlib\n@test "module reads fixture"\nreads() = fixlib.read_fixture() == 41', encoding="utf-8")
    assert run_native_tests_from_file(str(program), fixture_bindings={"fixture_marker": 41}) != 0
    captured = capsys.readouterr()
    assert "errored=1" in captured.out and "reason=Undefined name: fixture_marker" in captured.out
    assert "COMPATIBILITY FALLBACK" not in captured.err and str(tmp_path) not in captured.err


def test_mcp_worker_path_prunes_before_entry_and_keeps_denied_names_denied():
    """The MCP worker host path: allowed code runs in E, denied capabilities are undefined, no fallback surface."""
    assert mcp_worker.execute_source("length([1, 2])")["status"] == "completed"
    assert mcp_worker.execute_source('read_file("x")')["status"] == "policy_denied"
    assert mcp_worker.execute_source("secret_get", enforce_policy=False)["status"] == "runtime_error"


def test_reflection_inside_metacircular_eval_is_runtime_scoped_and_cannot_see_entry(tmp_path):
    """#1238 corner: a reflective call evaluated by `eval` over `empty_env()` sees runtime names and never
    entry names (no leak). Binding to names added with `define` (maintainer ruling, PR #1244) is pinned
    discriminatingly in test_f2_p2_meta_reflection.py; the integer `doc("added")` check here cannot tell."""
    entry = make_program_env([])
    run_source('@doc "entry docs"\nentry_fn(x) = x', entry)
    assert isinstance(run_source('eval(quote(doc("entry_fn")), empty_env())', entry), GeniaOptionNone)
    assert isinstance(run_source('eval(quote(doc("map")), empty_env())', entry), str)
    assert isinstance(run_source('eval(quote(doc("added")), define(empty_env(), quote(added), 1))', entry), GeniaOptionNone)
