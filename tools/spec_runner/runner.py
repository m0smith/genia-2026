from __future__ import annotations

from .comparator import compare_spec
from .executor import execute_spec
from .loader import discover_specs
from .reporter import report_failure, report_invalid, report_summary


def main() -> int:
    specs, invalid_specs = discover_specs()

    total = len(specs)
    passed = 0
    failed = 0
    invalid = len(invalid_specs)

    for invalid_spec in invalid_specs:
        report_invalid(str(invalid_spec.path), invalid_spec.message)

    for spec in specs:
        try:
            actual = execute_spec(spec)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            report_failure(
                spec,
                [
                    type(
                        "RuntimeFailure",
                        (),
                        {
                            "field": "runtime_crash",
                            "expected": "successful execution",
                            "actual": str(exc),
                        },
                    )()
                ],
            )
            continue

        failures = compare_spec(spec, actual)
        if failures:
            failed += 1
            report_failure(spec, failures)
            continue

        passed += 1

    report_summary(total=total, passed=passed, failed=failed, invalid=invalid)
    return 0 if failed == 0 and invalid == 0 else 1
