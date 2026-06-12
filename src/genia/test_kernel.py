from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Iterable

from .values import _runtime_type_name


class NativeTestFailure(Exception):
    def __init__(self, reason: str, expected: Any = None, actual: Any = None):
        super().__init__(reason)
        self.reason = reason
        self.expected = expected
        self.actual = actual


@dataclass(frozen=True)
class TestUnit:
    __test__: ClassVar[bool] = False

    name: str
    body: Callable[[], Any]
    location: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _result(
    *,
    kind: str,
    name: str,
    phase: str,
    reason: str | None,
    expected: Any = None,
    actual: Any = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "name": name,
        "phase": phase,
        "reason": reason,
        "expected": expected,
        "actual": actual,
        "stdout": "",
        "stderr": "",
        "diagnostics": {},
    }


def _discovery_error(test_unit: Any, reason: str) -> dict[str, Any]:
    name = getattr(test_unit, "name", "<unnamed>")
    if not isinstance(name, str) or name == "":
        name = "<unnamed>"
    return _result(
        kind="error",
        name=name,
        phase="discovery",
        reason=reason,
    )


def _metadata_location_suffix(test_unit: Any) -> str:
    location = getattr(test_unit, "location", None)
    return f" at {location}" if isinstance(location, str) and location else ""


def _metadata_discovery_error(test_unit: Any) -> str | None:
    metadata = getattr(test_unit, "metadata", None)
    if metadata is None:
        return None
    if not isinstance(metadata, dict):
        received = _runtime_type_name(metadata)
        return (
            "invalid native test metadata: "
            f"expected map, received {received}{_metadata_location_suffix(test_unit)}"
        )
    for key, value in metadata.items():
        if not isinstance(key, str):
            received = _runtime_type_name(key)
            return (
                "invalid native test metadata key: "
                f"expected string, received {received}{_metadata_location_suffix(test_unit)}"
            )
        if not isinstance(value, str):
            received = _runtime_type_name(value)
            return (
                f"invalid native test metadata value for key '{key}': "
                f"expected string, received {received}{_metadata_location_suffix(test_unit)}"
            )
    return None


def run_test_unit(test_unit: TestUnit) -> dict[str, Any]:
    if not isinstance(getattr(test_unit, "name", None), str) or test_unit.name == "":
        return _discovery_error(test_unit, "test unit name must be a non-empty string")

    invalid_metadata = _metadata_discovery_error(test_unit)
    if invalid_metadata is not None:
        return _discovery_error(test_unit, invalid_metadata)

    discovery_error = getattr(test_unit, "discovery_error", None)
    if discovery_error is None and isinstance(getattr(test_unit, "metadata", None), dict):
        discovery_error = test_unit.metadata.get("discovery_error")
    if discovery_error is not None:
        return _discovery_error(test_unit, str(discovery_error))

    body = getattr(test_unit, "body", None)
    if not callable(body):
        return _discovery_error(test_unit, "test unit body must be callable")

    try:
        body()
    except NativeTestFailure as failure:
        return _result(
            kind="fail",
            name=test_unit.name,
            phase="evaluation",
            reason=failure.reason,
            expected=failure.expected,
            actual=failure.actual,
        )
    except Exception as exc:
        return _result(
            kind="error",
            name=test_unit.name,
            phase="evaluation",
            reason=str(exc),
        )

    return _result(
        kind="pass",
        name=test_unit.name,
        phase="evaluation",
        reason=None,
    )


def aggregate_results(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    ordered_results = list(results)
    return {
        "total": len(ordered_results),
        "passed": sum(result.get("kind") == "pass" for result in ordered_results),
        "failed": sum(result.get("kind") == "fail" for result in ordered_results),
        "errored": sum(result.get("kind") == "error" for result in ordered_results),
        "results": ordered_results,
    }


def run_test_suite(test_units: Iterable[TestUnit]) -> dict[str, Any]:
    return aggregate_results(run_test_unit(test_unit) for test_unit in test_units)


def suite_exit_code(suite_result: dict[str, Any]) -> int:
    if suite_result.get("failed", 0) > 0 or suite_result.get("errored", 0) > 0:
        return 1
    return 0
