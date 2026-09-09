from __future__ import annotations

from .comparator import ComparisonFailure
from .loader import LoadedSpec
from .revision import RevisionCheck


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


def report_capabilities_fetch_failed(kind: str, reason: str | None) -> None:
    """E16-3: the host's mandatory ``capabilities`` query itself did not
    return a valid, well-formed declaration. Every case is unresolvable
    without it, so the run stops here with one deterministic error rather
    than guessing applicability per case."""
    print(f"{kind.upper()} fetching host capabilities")
    if reason:
        print(f"  reason: {reason}")


def report_revision_check_failed(check: RevisionCheck) -> None:
    """E16-4: the host's declared contract_revision names no commit this
    local git history has. Neither pinned-conformance nor current-main
    evidence can be honestly attributed to it, so the run stops here."""
    print(
        "UNRESOLVABLE host-declared contract_revision "
        f"{check.declared_revision!r} (this checkout is at {check.current_revision})"
    )


def report_revision_status(check: RevisionCheck) -> None:
    """E16-4: state up front, before any case result, exactly what question
    this run's pass/fail evidence can honestly answer."""
    if check.kind == "current":
        print(
            f"Revision: pinned conformance for {check.declared_revision} "
            "(host-declared revision matches this checkout exactly)"
        )
    else:
        print(
            f"Revision: current-main compatibility only -- host declared "
            f"{check.declared_revision}, this checkout is at {check.current_revision}. "
            "This run cannot honestly claim pinned conformance for the "
            "declared revision; a host may still be correctly conforming to "
            "it while visibly behind current main."
        )


def report_host_outcome(spec: LoadedSpec, kind: str, reason: str | None) -> None:
    """E16-2: report a non-pass/fail host-mode outcome (unsupported,
    protocol_error, crash, or timeout) distinctly from an ordinary FAIL."""
    print(f"{kind.upper()} {spec.category} {spec.name} ({spec.path})")
    if reason:
        print(f"  reason: {reason}")


def report_host_summary(
    *,
    total: int,
    passed: int,
    failed: int,
    unsupported: int,
    protocol_error: int,
    crash: int,
    timeout: int,
    invalid: int,
) -> None:
    """E16-2: host-mode summary line naming every outcome in the taxonomy
    explicitly, so unsupported/protocol_error/crash/timeout counts can
    never be silently folded into passed or omitted."""
    print(
        "Summary: "
        f"total={total} passed={passed} failed={failed} "
        f"unsupported={unsupported} protocol_error={protocol_error} "
        f"crash={crash} timeout={timeout} invalid={invalid}"
    )
