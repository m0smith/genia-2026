from __future__ import annotations

import argparse
from time import perf_counter

from .comparator import compare_spec
from .executor import execute_spec
from .loader import discover_specs
from .reporter import (
    report_failure,
    report_invalid,
    report_spec_elapsed,
    report_spec_started,
    report_summary,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Genia shared specs")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print per-spec start and elapsed timing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args([] if argv is None else argv)
    specs, invalid_specs = discover_specs()

    total = len(specs)
    passed = 0
    failed = 0
    invalid = len(invalid_specs)

    for invalid_spec in invalid_specs:
        report_invalid(str(invalid_spec.path), invalid_spec.message)

    for spec in specs:
        start_time = perf_counter()
        if args.verbose:
            report_spec_started(spec)
        try:
            actual = execute_spec(spec)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            if args.verbose:
                report_spec_elapsed(spec, perf_counter() - start_time)
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
        if args.verbose:
            report_spec_elapsed(spec, perf_counter() - start_time)
        if failures:
            failed += 1
            report_failure(spec, failures)
            continue

        passed += 1

    report_summary(total=total, passed=passed, failed=failed, invalid=invalid)
    return 0 if failed == 0 and invalid == 0 else 1
