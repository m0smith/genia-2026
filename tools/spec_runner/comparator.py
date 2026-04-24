from __future__ import annotations

from dataclasses import dataclass

from .executor import ActualResult
from .loader import LoadedSpec


@dataclass(frozen=True)
class ComparisonFailure:
    field: str
    expected: object
    actual: object


def compare_spec(spec: LoadedSpec, actual: ActualResult) -> list[ComparisonFailure]:
    failures: list[ComparisonFailure] = []
    if spec.category == "ir":
        if actual.ir != spec.expected_ir:
            failures.append(ComparisonFailure("ir", spec.expected_ir, actual.ir))
        return failures

    if spec.category == "parse":
        expected = spec.expected_parse
        actual_parse = actual.parse
        if expected["kind"] == "ok":
            if actual_parse["kind"] != "ok":
                failures.append(ComparisonFailure("parse.kind", "ok", actual_parse["kind"]))
            elif actual_parse["ast"] != expected["ast"]:
                failures.append(ComparisonFailure("parse.ast", expected["ast"], actual_parse["ast"]))
        else:
            if actual_parse["kind"] != "error":
                failures.append(ComparisonFailure("parse.kind", "error", actual_parse["kind"]))
            else:
                if actual_parse["type"] != expected["type"]:
                    failures.append(ComparisonFailure("parse.type", expected["type"], actual_parse["type"]))
                if expected["message"] not in actual_parse["message"]:
                    failures.append(ComparisonFailure("parse.message", expected["message"], actual_parse["message"]))
        return failures

    if actual.stdout != spec.expected_stdout:
        failures.append(
            ComparisonFailure("stdout", spec.expected_stdout, actual.stdout)
        )
    if actual.stderr != spec.expected_stderr:
        failures.append(
            ComparisonFailure("stderr", spec.expected_stderr, actual.stderr)
        )
    if actual.exit_code != spec.expected_exit_code:
        failures.append(
            ComparisonFailure("exit_code", spec.expected_exit_code, actual.exit_code)
        )
    return failures
