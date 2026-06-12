from __future__ import annotations

import ast
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from .builtins import make_global_env
from .callable import GeniaFunctionGroup
from .errors import GeniaQuietBrokenPipe
from .test_kernel import TestUnit, run_test_suite, suite_exit_code
from .utf8 import format_debug
from .values import GeniaMap, GeniaOutputSink


_LEGACY_TEST_REGISTRATION_RE = re.compile(
    r"""\btest\s*\(\s*(?P<literal>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')"""
)


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
    return validate_unique_test_names([
        *list(getattr(env, "_native_test_units", [])),
        *discover_annotated_test_units(env),
    ])


def validate_unique_test_names(test_units: list[TestUnit]) -> list[TestUnit]:
    by_name: dict[str, list[TestUnit]] = {}
    duplicate_names: set[str] = set()
    for test_unit in test_units:
        if _has_discovery_error(test_unit):
            continue
        name = getattr(test_unit, "name", None)
        if not isinstance(name, str) or name == "":
            continue
        by_name.setdefault(name, []).append(test_unit)
        if len(by_name[name]) > 1:
            duplicate_names.add(name)
    for name in by_name:
        if name in duplicate_names:
            return [
                _discovery_error_test_unit(
                    name,
                    _duplicate_name_reason(name, by_name[name]),
                )
            ]
    return test_units


def _duplicate_name_reason(name: str, occurrences: list[TestUnit]) -> str:
    lines = [f"duplicate native test name: {name}"]
    for index, test_unit in enumerate(occurrences, start=1):
        location = _format_test_location(getattr(test_unit, "location", None))
        lines.append(f"occurrence {index}: {location}")
    return "\n".join(lines)


def _format_test_location(location: Any) -> str:
    if isinstance(location, dict):
        parts: list[str] = []
        file_name = location.get("file")
        if file_name:
            parts.append(str(file_name))
        line = location.get("line")
        if line is not None:
            parts.append(f"line {line}")
        column = location.get("column")
        if column is not None:
            parts.append(f"column {column}")
        source = location.get("source")
        if source:
            parts.append(f"source={source}")
        return " ".join(parts) if parts else "<unknown>"

    file_name = getattr(location, "filename", None)
    line = getattr(location, "line", None)
    column = getattr(location, "column", None)
    parts = []
    if file_name:
        parts.append(str(file_name))
    if line is not None:
        parts.append(f"line {line}")
    if column is not None:
        parts.append(f"column {column}")
    return " ".join(parts) if parts else "<unknown>"


def _has_discovery_error(test_unit: TestUnit) -> bool:
    metadata = getattr(test_unit, "metadata", None)
    return isinstance(metadata, dict) and metadata.get("discovery_error") is not None


def discover_annotated_test_units(env: Any) -> list[TestUnit]:
    test_units: list[TestUnit] = []
    for name, value in env.values.items():
        metadata = env.binding_metadata.get(name)
        if not _is_test_metadata(metadata):
            continue
        if not isinstance(value, GeniaFunctionGroup):
            test_units.append(_discovery_error_test_unit(name, "@test must annotate a function"))
            continue
        description = metadata.get("test")
        if not isinstance(description, str) or description == "":
            test_units.append(_discovery_error_test_unit(name, "@test description must be a non-empty string"))
            continue
        body = value.get(0)
        if body is None or value.sorted_arities() != [0]:
            test_units.append(_discovery_error_test_unit(name, "@test functions must take zero arguments"))
            continue
        test_units.append(
            TestUnit(
                name,
                body,
                location=_span_location(getattr(body, "span", None), source="@test"),
                metadata={"description": description},
            )
        )
    return test_units


def _is_test_metadata(metadata: Any) -> bool:
    return isinstance(metadata, GeniaMap) and metadata.has("test")


def _discovery_error_test_unit(name: str, reason: str) -> TestUnit:
    return TestUnit(name, None, metadata={"discovery_error": reason})


def _span_location(span: Any, *, source: str | None = None) -> dict[str, Any] | None:
    if span is None:
        return None
    location: dict[str, Any] = {}
    file_name = getattr(span, "filename", None)
    if file_name is not None:
        location["file"] = file_name
    line = getattr(span, "line", None)
    if line is not None:
        location["line"] = line
    column = getattr(span, "column", None)
    if column is not None:
        location["column"] = column
    if source is not None:
        location["source"] = source
    return location or None


def _attach_legacy_test_locations(
    test_units: list[TestUnit],
    source: str,
    file_name: str,
) -> None:
    locations_by_name = _legacy_test_registration_locations(source, file_name)
    used_by_name: dict[str, int] = {}
    for index, test_unit in enumerate(test_units):
        if getattr(test_unit, "location", None) is not None:
            continue
        name = getattr(test_unit, "name", None)
        if not isinstance(name, str):
            continue
        locations = locations_by_name.get(name)
        if not locations:
            continue
        used_index = used_by_name.get(name, 0)
        if used_index >= len(locations):
            continue
        test_units[index] = replace(test_unit, location=locations[used_index])
        used_by_name[name] = used_index + 1


def _legacy_test_registration_locations(
    source: str,
    file_name: str,
) -> dict[str, list[dict[str, Any]]]:
    locations_by_name: dict[str, list[dict[str, Any]]] = {}
    for line_number, line in enumerate(source.splitlines(), start=1):
        match = _LEGACY_TEST_REGISTRATION_RE.search(line)
        if match is None:
            continue
        try:
            name = ast.literal_eval(match.group("literal"))
        except (SyntaxError, ValueError):
            continue
        if not isinstance(name, str):
            continue
        locations_by_name.setdefault(name, []).append(
            {
                "file": file_name,
                "line": line_number,
                "source": "test()",
            }
        )
    return locations_by_name


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
    env, _ = make_test_env()
    try:
        path = Path(program_path)
        source = path.read_text(encoding="utf-8")
        from .interpreter import run_source

        run_source(source, env, filename=str(path.resolve()))
        _attach_legacy_test_locations(
            getattr(env, "_native_test_units", []),
            source,
            str(path.resolve()),
        )
        tests = discover_test_units(env)
        suite = run_test_suite(tests)
        _write_stdout(env, format_test_suite_report(suite))
        return suite_exit_code(suite)
    except GeniaQuietBrokenPipe:
        return 0
    except Exception as exc:  # noqa: BLE001
        _write_stderr(env, f"Error: {exc}")
        return 1
