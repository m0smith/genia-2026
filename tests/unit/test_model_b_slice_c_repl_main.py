"""Slice C RED host-local tests: REPL transcripts, entry selection structure, file-mode labels.

PYTHON REFERENCE HOST ONLY (issue #1269; test plan R6.E HL-9, HL-12, HL-15,
HL-19, HL-20, HL-24). Python's REPL echoes function values (`<function f/1>`,
`GeniaFunctionGroup(...)`), the CLI file-mode duplicate label is the
host-resolved entry path, and `_resolve_program_result` is a Python-internal
function; none of these is portable. The portable counterparts are the shared
`model-b-c-open-persistent-*`, `model-b-c-main-*`, `model-b-c-ann-repl-recovery`
and `model-b-c-mode-*` cases.

RED phase: ``*_today`` tests pin implemented behavior and pass; the others assert
approved Slice C behavior and fail until GREEN.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.unit.model_b_slice_c_support import REPO_ROOT, cli, outcome

INTERPRETER = REPO_ROOT / "src" / "genia" / "interpreter.py"

# --- HL-9 / HL-20: _resolve_program_result is structurally limited ---------------------------


def _function_defs(tree: ast.AST) -> dict[str, ast.FunctionDef]:
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def test_resolve_program_result_is_called_only_from_command_and_file_branches_today():
    text = INTERPRETER.read_text(encoding="utf-8")
    tree = ast.parse(text)
    callers = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_resolve_program_result":
            callers.append(node.lineno)
    assert len(callers) == 2
    lines = text.splitlines()
    for lineno in callers:
        preceding = "\n".join(lines[max(0, lineno - 12) : lineno])
        assert 'mode.kind == "command"' in preceding or 'mode.kind == "file"' in preceding
        for banned in ('mode.kind == "repl"', 'mode.kind == "pipe"', 'mode.kind == "test"'):
            assert banned not in preceding.split('mode.kind == "command"')[-1].split('mode.kind == "file"')[-1]


def test_resolve_program_result_does_not_evaluate_guards_or_patterns_and_adds_no_main_error_today():
    tree = ast.parse(INTERPRETER.read_text(encoding="utf-8"))
    func = _function_defs(tree)["_resolve_program_result"]
    names = {n.id for n in ast.walk(func) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(func) if isinstance(n, ast.Attribute)}
    # Entry selection reads only the arity-keyed index: no dispatch, matching, guard or key walker.
    assert not names & {"Evaluator", "match_pattern", "invoke_callable", "eval_program"}
    assert not attrs & {"match", "guard", "dispatch", "resolve", "select_clause"}
    raises = [n for n in ast.walk(func) if isinstance(n, ast.Raise)]
    assert raises == [], "entry selection must not introduce a new main diagnostic"


# --- HL-15: REPL function-value transcript (host representation) ----------------------------


def test_repl_echoes_a_function_value_for_declarations_today():
    completed = cli(stdin="f(x) = x\nf(x, y) = x + y\nf(1, 2)\n")
    assert completed.returncode == 0
    assert completed.stderr == ""
    lines = completed.stdout.splitlines()
    assert lines[-1] == "3"
    assert lines[0].startswith("<function f/1>")
    assert "f/2" in lines[1]


def test_repl_pattern_declaration_transcript_has_no_host_object_text():
    """After GREEN the declaration echo must still be a bounded representation, never an address."""
    completed = cli(stdin='f(0) = "zero"\nf(1) = "one"\n[f(0), f(1)]\n')
    assert completed.returncode == 0
    assert completed.stderr == ""
    assert completed.stdout.splitlines()[-1] == '["zero", "one"]'
    assert "0x" not in completed.stdout and "Traceback" not in completed.stdout


# --- HL-19: REPL transcripts after a failed annotation or declaration ------------------------


def test_repl_failed_annotation_reports_on_stderr_and_keeps_the_session_today():
    completed = cli(stdin="f(x) = x; 0\n@doc 7; f(x, y) = x + y; 0\nf(1, 2)\n")
    assert completed.returncode == 0
    assert "Error: @doc annotation expected a string, received int" in completed.stderr
    assert completed.stdout.splitlines()[-1] == "3"


def test_repl_failed_pattern_declaration_leaves_the_group_unchanged_and_the_name_usable():
    completed = cli(stdin='f(0) = "zero"; 0\nf(0) = "again"; 0\nf(0)\n')
    assert completed.returncode == 0
    assert completed.stderr.startswith("Error: open-function-duplicate-clause: f in unit 'base'")
    assert completed.stdout.splitlines()[-1] == '"zero"'


# --- HL-20: REPL never selects main (function-echo variant) -----------------------------------


def test_repl_declaration_of_main_runs_no_body_today():
    completed = cli(stdin='main() = { print("ran"); 1 }\n')
    assert completed.returncode == 0
    assert "ran" not in completed.stdout
    assert "<function main/0>" in completed.stdout


def test_repl_pattern_main_declaration_runs_no_body():
    completed = cli(stdin='main(["x"]) = { print("ran"); 1 }\n')
    assert completed.returncode == 0
    assert "ran" not in completed.stdout
    assert completed.stderr == ""


# --- HL-12: file-mode label for a pattern-clause duplicate is the host-resolved path -----------


def test_file_mode_pattern_duplicate_label_is_the_resolved_entry_path(tmp_path: Path):
    program = tmp_path / "dup.genia"
    program.write_text("f([a, b]) = 1\nf([c, d]) = 2\n", encoding="utf-8")
    completed = cli(str(program))
    assert completed.returncode == 1
    resolved = str(program.resolve())
    assert completed.stderr == (
        "Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical "
        f"dispatch key shape=('fixed', 1) (first at {resolved}:1, duplicate at {resolved}:2)\n"
    )


def test_command_mode_duplicate_label_is_the_command_label():
    completed = cli("-c", "f([a, b]) = 1\nf([c, d]) = 2")
    assert completed.returncode == 1
    assert "(first at <command>:1, duplicate at <command>:2)" in completed.stderr


# --- HL-24: after a guard error, no partial binding and no later guard evaluated ---------------


def test_guard_error_propagates_leaves_no_partial_binding_and_runs_no_later_guard():
    import genia

    from tests.unit.model_b_slice_c_support import fresh_env

    env, printed = fresh_env()
    source = (
        "boom() = 1 / 0\n"
        "note(tag) = { print(tag); true }\n"
        'f(x) ? boom() = "first"\n'
        'f(x) ? note("later-guard") = "second"\n'
        "f(1)"
    )
    result = outcome(source, env=env)
    assert result.error is not None
    assert "model-b-not-implemented" not in result.message
    assert "zero" in result.message.lower()
    assert "later-guard" not in "".join(printed)
    # the pattern binder `x` of the failed attempt never leaked into the entry scope
    with pytest.raises(NameError):
        genia.run_source("x", env)
