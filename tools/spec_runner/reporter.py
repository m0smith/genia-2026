from __future__ import annotations

from .comparator import ComparisonFailure
from .loader import LoadedSpec


def _format_value(value: object) -> str:
    return repr(value)


def report_failure(spec: LoadedSpec, failures: list[ComparisonFailure]) -> None:
    print(f"FAIL {spec.category} {spec.name} ({spec.path})")
    for failure in failures:
        print(f"  field: {failure.field}")
        print(f"    expected: {_format_value(failure.expected)}")
        print(f"    actual:   {_format_value(failure.actual)}")


def report_invalid(path: str, message: str) -> None:
    print(f"INVALID {path}")
    print(f"  {message}")


def report_spec_started(spec: LoadedSpec) -> None:
    print(spec.name, flush=True)


def report_spec_elapsed(spec: LoadedSpec, elapsed_seconds: float) -> None:
    print(f"{spec.name}\t{elapsed_seconds:.3f}s")


def report_summary(*, total: int, passed: int, failed: int, invalid: int) -> None:
    print(
        f"Summary: total={total} passed={passed} failed={failed} invalid={invalid}"
    )
