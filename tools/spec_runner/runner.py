from __future__ import annotations

import argparse
import shlex
from time import perf_counter

from .capabilities import CapabilityDeclarationError, validate_capability_claims
from .comparator import compare_spec
from .executor import execute_spec
from .host_executor import execute_spec_via_host
from .loader import discover_specs
from .protocol import fetch_capabilities
from .reporter import (
    report_capabilities_fetch_failed,
    report_failure,
    report_host_outcome,
    report_host_summary,
    report_invalid,
    report_spec_elapsed,
    report_spec_started,
    report_summary,
)

DEFAULT_HOST_TIMEOUT_SECONDS = 10.0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Genia shared specs")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print per-spec start and elapsed timing",
    )
    parser.add_argument(
        "--host",
        metavar="COMMAND",
        default=None,
        help=(
            "run applicable cases through an external adapter command "
            "speaking the E16-1 protocol (tools/spec_runner/protocol.py) "
            "instead of the in-process Python adapter; pass the full "
            "command as one shell-quoted string, e.g. "
            "--host 'python3 -m my_host.adapter'"
        ),
    )
    parser.add_argument(
        "--host-timeout",
        type=float,
        default=DEFAULT_HOST_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help=f"per-case timeout when --host is given (default: {DEFAULT_HOST_TIMEOUT_SECONDS})",
    )
    return parser


def _run_in_process(args: argparse.Namespace) -> int:
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


def _run_via_host(args: argparse.Namespace) -> int:
    host_command = shlex.split(args.host)

    capabilities_outcome = fetch_capabilities(host_command, timeout=args.host_timeout)
    if capabilities_outcome.kind != "ok":
        report_capabilities_fetch_failed(capabilities_outcome.kind, capabilities_outcome.reason)
        return 1

    host_capabilities = capabilities_outcome.result["capabilities"]
    try:
        validate_capability_claims(host_capabilities)
    except CapabilityDeclarationError as exc:
        report_capabilities_fetch_failed("protocol_error", str(exc))
        return 1

    specs, invalid_specs = discover_specs()

    total = len(specs)
    passed = failed = unsupported = protocol_error = crash = timeout = 0
    invalid = len(invalid_specs)

    for invalid_spec in invalid_specs:
        report_invalid(str(invalid_spec.path), invalid_spec.message)

    for spec in specs:
        start_time = perf_counter()
        if args.verbose:
            report_spec_started(spec)

        result = execute_spec_via_host(
            spec, host_command, timeout=args.host_timeout, host_capabilities=host_capabilities
        )

        if args.verbose:
            report_spec_elapsed(spec, perf_counter() - start_time)

        if result.kind == "pass":
            passed += 1
        elif result.kind == "fail":
            failed += 1
            report_failure(spec, list(result.failures))
        else:
            if result.kind == "unsupported":
                unsupported += 1
            elif result.kind == "protocol_error":
                protocol_error += 1
            elif result.kind == "crash":
                crash += 1
            else:
                timeout += 1
            report_host_outcome(spec, result.kind, result.reason)

    report_host_summary(
        total=total,
        passed=passed,
        failed=failed,
        unsupported=unsupported,
        protocol_error=protocol_error,
        crash=crash,
        timeout=timeout,
        invalid=invalid,
    )
    return 0 if failed == 0 and protocol_error == 0 and crash == 0 and timeout == 0 and invalid == 0 else 1


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args([] if argv is None else argv)
    if args.host is not None:
        return _run_via_host(args)
    return _run_in_process(args)
