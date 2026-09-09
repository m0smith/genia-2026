"""
E16-2 generic external-host execution path (issue #759).

Maps a ``LoadedSpec`` onto the E16-1 protocol
(``tools/spec_runner/protocol.py``) and classifies the result. This module
contains no host-specific knowledge (C++, Python, or otherwise); it only
knows the generic wire contract and the existing category-to-operation
mapping already documented for the in-process path (``ir`` -> ``lower``;
``flow``/``error`` -> ``eval``, matching ``hosts/python/adapter.py``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .capabilities import case_is_applicable
from .comparator import ComparisonFailure, compare_spec
from .executor import ActualResult
from .loader import LoadedSpec
from .protocol import AdapterOutcome, build_request, run_adapter_request

_OPERATION_BY_CATEGORY = {
    "parse": "parse",
    "ir": "lower",
    "eval": "eval",
    "error": "eval",
    "flow": "eval",
    "cli": "cli",
}

HOST_OUTCOME_KINDS = ("pass", "fail", "unsupported", "protocol_error", "crash", "timeout")

_UNSUPPORTED_LOCAL_CAPABILITY_REASON = (
    "case requires a Python-host-only injected test fixture or the "
    "debug-stdio CLI mode; neither is expressible over the generic E16-1 "
    "protocol yet. Explicit capability-aware selection is E16-3 (#760); this "
    "is a minimal, clearly-labeled interim exclusion, not a capability system."
)


@dataclass(frozen=True)
class HostCaseResult:
    """The E16-2 classification of one spec case run through a host command."""

    kind: str
    failures: tuple[ComparisonFailure, ...] = ()
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in HOST_OUTCOME_KINDS:
            raise ValueError(f"invalid HostCaseResult kind: {self.kind!r}")


def _cli_argv(spec: LoadedSpec) -> list[str]:
    if spec.test:
        return ["--test", spec.test]
    if spec.file:
        return [spec.file, *spec.argv]
    if spec.command and not spec.stdin:
        return ["-c", spec.command, *spec.argv]
    if spec.command:
        return ["-p", spec.command]
    raise ValueError(f"cli spec {spec.name!r} has no file or command")


def build_host_request(spec: LoadedSpec) -> dict[str, Any] | None:
    """Build the E16-1 request for one spec case, or ``None`` when the case
    is not yet expressible over the generic protocol (see
    ``_UNSUPPORTED_LOCAL_CAPABILITY_REASON``)."""
    if spec.fixtures or spec.debug_stdio:
        return None

    operation = _OPERATION_BY_CATEGORY[spec.category]
    if operation in ("parse", "lower"):
        input_payload: dict[str, Any] = {"source": spec.source}
    elif operation == "eval":
        input_payload = {"source": spec.source, "stdin": spec.stdin or None, "argv": None}
    else:  # cli
        input_payload = {"argv": _cli_argv(spec), "stdin": spec.stdin or None}

    return build_request(spec.name, operation, input_payload)


def _outcome_to_actual_result(operation: str, result: dict[str, Any]) -> ActualResult:
    if operation == "parse":
        return ActualResult(parse=result)
    if operation == "lower":
        return ActualResult(ir=result["ir"])
    return ActualResult(stdout=result["stdout"], stderr=result["stderr"], exit_code=result["exit_code"])


def execute_spec_via_host(
    spec: LoadedSpec,
    host_command: Sequence[str],
    *,
    timeout: float,
    host_capabilities: Mapping[str, str] | None = None,
) -> HostCaseResult:
    """Execute one spec case through an external adapter command speaking
    the E16-1 protocol, and classify it into the deterministic taxonomy.

    ``host_capabilities`` is the host's already-fetched, already-validated
    ``capabilities`` response (E16-3, issue #760): a mapping from capability
    name to ``"supported" | "partial" | "unsupported"``. A case declaring
    ``requires`` is checked against it *before* the adapter is invoked for
    that case's own operation; an unmet requirement is reported
    ``unsupported`` and never silently skipped or counted as a pass. A case
    with no ``requires`` is unaffected by this check regardless of whether
    ``host_capabilities`` was supplied.
    """
    request = build_host_request(spec)
    if request is None:
        return HostCaseResult(kind="unsupported", reason=_UNSUPPORTED_LOCAL_CAPABILITY_REASON)

    if spec.requires:
        if host_capabilities is None:
            return HostCaseResult(
                kind="unsupported",
                reason=(
                    f"case requires explicit host capabilities {list(spec.requires)} "
                    "but none were declared/fetched for this host"
                ),
            )
        applicable, reason = case_is_applicable(spec.requires, dict(host_capabilities))
        if not applicable:
            return HostCaseResult(kind="unsupported", reason=reason)

    outcome: AdapterOutcome = run_adapter_request(list(host_command), request, timeout=timeout)

    if outcome.kind in ("unsupported", "protocol_error", "crash", "timeout"):
        return HostCaseResult(kind=outcome.kind, reason=outcome.reason)

    actual = _outcome_to_actual_result(request["operation"], outcome.result)
    failures = compare_spec(spec, actual)
    if failures:
        return HostCaseResult(kind="fail", failures=tuple(failures))
    return HostCaseResult(kind="pass")
