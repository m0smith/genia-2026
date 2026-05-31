from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .builtins import make_global_env
from .errors import GeniaQuietBrokenPipe
from .test_kernel import TestUnit, run_test_suite, suite_exit_code
from .utf8 import format_debug
from .values import GeniaOutputSink


def _summary_line(suite: dict[str, Any]) -> str:
    return (
        f"total={suite.get('total', 0)} "
        f"passed={suite.get('passed', 0)} "
        f"failed={suite.get('failed', 0)} "
        f"errored={suite.get('errored', 0)}"
    )


def _display_name(result: dict[str, Any]) -> str:
    name = result.get("name", "")
    return name if isinstance(name, str) and name else "<unnamed>"


def _reason_text(result: dict[str, Any]) -> str:
    reason = result.get("reason")
    return "" if reason is None else str(reason)


def _format_result_line(result: dict[str, Any]) -> str:
    kind = result.get("kind")
    name = _display_name(result)

    if kind == "pass":
        return f"PASS {name}"

    if kind == "fail":
        line = f"FAIL {name} phase={result.get('phase')} reason={_reason_text(result)}"
        if result.get("expected") is not None or result.get("actual") is not None:
            expected = format_debug(result.get("expected"))
            actual = format_debug(result.get("actual"))
            line += f" expected={expected} actual={actual}"
        return line

    if kind == "error":
        return f"ERROR {name} phase={result.get('phase')} reason={_reason_text(result)}"

    raise ValueError(f"unknown test result kind: {kind}")


def format_test_suite_report(suite: dict[str, Any]) -> str:
    summary = _summary_line(suite)
    lines = [summary]
    lines.extend(_format_result_line(result) for result in suite.get("results", []))
    lines.append(summary)
    return "\n".join(lines) + "\n"


def make_test_env() -> tuple[Any, list[TestUnit]]:
    tests: list[TestUnit] = []
    env = make_global_env(cli_args=[])
    setattr(env, "_native_test_units", tests)

    def register_test(name: Any, body: Any) -> None:
        tests.append(TestUnit(name, body))
        return None

    env.set("test", register_test)
    return env, tests


def discover_test_units(env: Any) -> list[TestUnit]:
    return list(getattr(env, "_native_test_units", []))


def _write_stdout(env: Any, text: str) -> None:
    sink = env.values.get("stdout")
    if isinstance(sink, GeniaOutputSink):
        sink.write_text(text)
        return
    sys.stdout.write(text)
    sys.stdout.flush()


def _write_stderr(env: Any, message: str) -> None:
    sink = env.values.get("stderr")
    text = message + "\n"
    if isinstance(sink, GeniaOutputSink):
        sink.write_text(text)
        return
    try:
        sys.stderr.write(text)
        sys.stderr.flush()
    except BrokenPipeError:
        return


def run_native_tests_from_file(program_path: str) -> int:
    env, tests = make_test_env()
    try:
        path = Path(program_path)
        source = path.read_text(encoding="utf-8")
        from .interpreter import run_source

        run_source(source, env, filename=str(path.resolve()))
        suite = run_test_suite(tests)
        _write_stdout(env, format_test_suite_report(suite))
        return suite_exit_code(suite)
    except GeniaQuietBrokenPipe:
        return 0
    except Exception as exc:  # noqa: BLE001
        _write_stderr(env, f"Error: {exc}")
        return 1
