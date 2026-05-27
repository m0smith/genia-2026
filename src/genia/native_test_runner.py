from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .interpreter import Evaluator, Parser, assert_portable_core_ir, lex, lower_program, optimize_program
from . import test_kernel


def run_native_tests(file_path: str) -> int:
    """
    Load, parse, and execute native tests from a Genia file.

    Returns exit code 0 when all tests pass, 1 when any test fails or errors,
    and 2 for file, parse, or no-tests errors.
    """
    source, file_error = _validate_file(file_path)
    if file_error is not None:
        _write_stderr(file_error)
        return 2

    declarations, parse_error = _parse_file(source or "", file_path)
    if parse_error is not None:
        _write_stderr(parse_error)
        return 2

    test_units = _identify_tests(declarations or [])
    if not test_units:
        sys.stdout.write("Summary: total=0 passed=0 failed=0 errors=0\n")
        sys.stdout.flush()
        return 2

    result_summary = _run_tests(test_units)
    sys.stdout.write(_format_results(result_summary))
    sys.stdout.flush()
    return _map_exit_code(result_summary)


def _validate_file(file_path: str) -> tuple[str | None, str | None]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return None, f"genia: test: file not found: {file_path}"
    if not os.access(path, os.R_OK):
        return None, f"genia: test: cannot read {file_path}: not readable"

    try:
        return path.read_text(encoding="utf-8"), None
    except OSError as exc:
        return None, f"genia: test: cannot read {file_path}: {exc}"


def _parse_file(source: str, file_path: str) -> tuple[list[Any] | None, str | None]:
    try:
        declarations = Parser(lex(source), source=source, filename=file_path).parse_program()
    except SyntaxError as exc:
        return None, f"Parse error: {exc}"
    return declarations, None


def _identify_tests(declarations: list[Any]) -> list[Any]:
    return native_test_kernel.identify_tests(declarations)


def _run_tests(test_units: list[Any]) -> Any:
    return native_test_kernel.run_tests(test_units)


def _format_results(result_summary: Any) -> str:
    lines = [
        f"[{_outcome_status(outcome)}] {_outcome_name(outcome)}"
        for outcome in _get(result_summary, "outcomes", [])
    ]
    lines.append(
        "Summary: "
        f"total={_get(result_summary, 'total', 0)} "
        f"passed={_get(result_summary, 'passed', 0)} "
        f"failed={_get(result_summary, 'failed', 0)} "
        f"errors={_get(result_summary, 'errors', 0)}"
    )
    return "\n".join(lines) + "\n"


def _map_exit_code(result_summary: Any) -> int:
    if _get(result_summary, "total", 0) == 0:
        return 2
    if _get(result_summary, "failed", 0) > 0 or _get(result_summary, "errors", 0) > 0:
        return 1
    return 0


def _write_stderr(message: str) -> None:
    try:
        sys.stderr.write(message + "\n")
        sys.stderr.flush()
    except BrokenPipeError:
        return


def _get(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _outcome_status(outcome: Any) -> str:
    status = _get(outcome, "status")
    if status is not None:
        return str(status)

    kind = str(_get(outcome, "kind", "")).upper()
    if kind == "PASS":
        return "PASS"
    if kind == "FAIL":
        return "FAIL"
    if kind == "ERROR":
        return "ERROR"
    return kind


def _outcome_name(outcome: Any) -> str:
    return str(_get(outcome, "name", "<unnamed>") or "<unnamed>")


def _kernel_summary_from_suite(suite: dict[str, Any]) -> SimpleNamespace:
    outcomes = [
        SimpleNamespace(
            name=result.get("name", "<unnamed>") or "<unnamed>",
            status=str(result.get("kind", "")).upper(),
            message=result.get("reason"),
        )
        for result in suite.get("results", [])
    ]
    return SimpleNamespace(
        total=suite.get("total", 0),
        passed=suite.get("passed", 0),
        failed=suite.get("failed", 0),
        errors=suite.get("errored", 0),
        outcomes=outcomes,
    )


def identify_tests(declarations: list[Any]) -> list[Any]:
    """Discover registered native tests through the existing test-mode helper."""
    from .test_cli import discover_test_units, make_test_env

    env, _ = make_test_env()
    ir_nodes = lower_program(declarations)
    assert_portable_core_ir(ir_nodes)
    ir_nodes = optimize_program(ir_nodes)
    Evaluator(env).eval_program(ir_nodes)
    return discover_test_units(env)


def run_tests(test_units: list[Any]) -> SimpleNamespace:
    """Run test units through the existing native test kernel."""
    return _kernel_summary_from_suite(test_kernel.run_test_suite(test_units))


native_test_kernel = SimpleNamespace(
    identify_tests=identify_tests,
    run_tests=run_tests,
)
