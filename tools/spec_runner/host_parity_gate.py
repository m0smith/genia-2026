"""
Host parity CI gate (R26+ pre-flight #1018).

Compares two E16-7 evidence documents (``tools.spec_runner --host ...
--evidence ...``), one from the Python reference host and one from another
host (currently C++, ``m0smith/genia-cpp``), against a checked-in known-gaps
manifest (``spec/known_host_gaps.json``), so a portable-semantic change
cannot quietly pass in Python while the other host silently drifts, and so
every gap between hosts is an explicit, tracked fact rather than a silent
skip.

This module adds no new protocol, evidence format, or capability registry --
it only reads the E16-7 documents and E16-3 capability vocabulary that
already exist.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

from .capabilities import MANIFEST_PATH

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWN_GAPS_PATH = REPO_ROOT / "spec" / "known_host_gaps.json"


def optional_capabilities() -> frozenset[str]:
    """The subset of the genia-2026-owned capability vocabulary that is
    ``requires``-gated per host (``spec/manifest.json``'s
    ``optional_capabilities``). Required capabilities are the baseline every
    conforming host implements by definition (E16-3); this gate only
    compares the optional/gated set, which is the granularity the E16-7
    evidence's ``capabilities`` map actually distinguishes as
    supported/partial/unsupported per host."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return frozenset(manifest["optional_capabilities"])

_FAILING_COUNT_FIELDS = ("fail", "protocol_error", "crash", "timeout", "invalid")

_REQUIRED_GAP_FIELDS = (
    "capability",
    "reason",
    "tracking_issue",
    "affected_host",
    "affected_tests",
    "removal_condition",
)

PARITY_OK = "PARITY_OK"
KNOWN_GAP = "KNOWN_GAP"
UNDOCUMENTED_GAP = "UNDOCUMENTED_GAP"
STALE_GAP = "STALE_GAP"

_FAILING_STATES = (UNDOCUMENTED_GAP, STALE_GAP)


class HostParityGateError(ValueError):
    """A malformed evidence document or known-gaps manifest was given. This
    is a tooling-input error, distinct from a genuine parity failure."""


@dataclass(frozen=True)
class CapabilityParity:
    capability: str
    status: str
    detail: str


@dataclass(frozen=True)
class ParityReport:
    evidence_failures: tuple[str, ...]
    capability_results: tuple[CapabilityParity, ...]
    cpp_unavailable_reason: str | None

    @property
    def ok(self) -> bool:
        if self.evidence_failures:
            return False
        return not any(result.status in _FAILING_STATES for result in self.capability_results)


def load_evidence(path: str | Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HostParityGateError(f"evidence file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HostParityGateError(f"evidence file is not valid JSON: {path} ({exc})") from exc


def load_known_gaps(path: str | Path = DEFAULT_KNOWN_GAPS_PATH) -> dict[str, dict]:
    """Load the known-gaps manifest, keyed by capability name. Raises
    ``HostParityGateError`` for a manifest entry naming a capability outside
    the genia-2026-owned vocabulary (``spec/manifest.json``), so a typo in
    the manifest itself is never silently ignored. Each checked-in gap must
    also carry enough issue-backed tracking detail to keep this file from
    becoming an unowned skip list."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    gaps = raw.get("gaps", [])
    known = optional_capabilities()
    by_capability: dict[str, dict] = {}
    for entry in gaps:
        for field in _REQUIRED_GAP_FIELDS:
            if field not in entry or entry[field] in ("", [], None):
                raise HostParityGateError(
                    f"known-gaps manifest {path} entry {entry.get('capability', '<unknown>')!r} "
                    f"is missing required field {field!r}"
                )
        capability = entry.get("capability")
        if capability not in known:
            raise HostParityGateError(
                f"known-gaps manifest {path} names unknown optional capability {capability!r}; "
                f"known optional capabilities: {sorted(known)}"
            )
        tracking_issue = entry["tracking_issue"]
        if not isinstance(tracking_issue, str) or (
            "github.com/m0smith/genia-2026/issues/" not in tracking_issue
            and "m0smith/genia-2026#" not in tracking_issue
        ):
            raise HostParityGateError(
                f"known-gaps manifest {path} entry {capability!r} must include a GitHub issue reference "
                "in 'tracking_issue'"
            )
        if capability in by_capability:
            raise HostParityGateError(f"known-gaps manifest {path} lists capability {capability!r} twice")
        by_capability[capability] = entry
    return by_capability


def _evidence_failures(label: str, evidence: Mapping[str, object]) -> list[str]:
    counts = evidence.get("counts")
    if not isinstance(counts, dict):
        raise HostParityGateError(f"{label} evidence is missing a 'counts' object")
    failures = []
    for field in _FAILING_COUNT_FIELDS:
        value = counts.get(field, 0)
        if value:
            failures.append(f"{label} evidence has {field}={value} (must be 0)")
    return failures


def check_parity(
    *,
    python_evidence: Mapping[str, object],
    cpp_evidence: Mapping[str, object] | None,
    known_gaps: Mapping[str, dict],
    cpp_unavailable_reason: str | None = None,
) -> ParityReport:
    """Build a :class:`ParityReport` from already-loaded evidence documents.

    ``cpp_evidence`` may be ``None`` only when ``cpp_unavailable_reason`` is
    given -- an explicit, human-readable reason the C++ side could not be
    evaluated in this run (e.g. no toolchain/checkout available). Passing
    neither is a caller error: silently skipping the C++ side without a
    reason is exactly the silent-drift outcome this gate exists to prevent.
    """
    if cpp_evidence is None and not cpp_unavailable_reason:
        raise HostParityGateError(
            "cpp_evidence is missing and no cpp_unavailable_reason was given; "
            "a skipped C++ comparison must always carry an explicit reason"
        )

    evidence_failures = list(_evidence_failures("python", python_evidence))
    if cpp_evidence is not None:
        evidence_failures.extend(_evidence_failures("cpp", cpp_evidence))

    capability_results: list[CapabilityParity] = []
    if cpp_evidence is not None:
        cpp_capabilities = cpp_evidence.get("capabilities")
        if not isinstance(cpp_capabilities, dict):
            raise HostParityGateError("cpp evidence is missing a 'capabilities' object")

        for capability in sorted(optional_capabilities()):
            cpp_status = cpp_capabilities.get(capability, "unsupported")
            gap = known_gaps.get(capability)

            if cpp_status == "supported":
                if gap is not None:
                    capability_results.append(
                        CapabilityParity(
                            capability=capability,
                            status=STALE_GAP,
                            detail=(
                                f"cpp now declares {capability!r} supported, but spec/known_host_gaps.json "
                                "still lists it as a gap -- update or remove that entry"
                            ),
                        )
                    )
                else:
                    capability_results.append(
                        CapabilityParity(capability=capability, status=PARITY_OK, detail="cpp declares supported")
                    )
                continue

            # cpp_status is "partial" or "unsupported" (or undeclared, treated as unsupported).
            if gap is not None:
                capability_results.append(
                    CapabilityParity(
                        capability=capability,
                        status=KNOWN_GAP,
                        detail=f"cpp declares {cpp_status!r}: {gap['reason']} ({gap['tracking_issue']})",
                    )
                )
            else:
                capability_results.append(
                    CapabilityParity(
                        capability=capability,
                        status=UNDOCUMENTED_GAP,
                        detail=(
                            f"cpp declares {cpp_status!r} for {capability!r} with no matching entry in "
                            "spec/known_host_gaps.json -- either the host regressed or the manifest is out of date"
                        ),
                    )
                )

    return ParityReport(
        evidence_failures=tuple(evidence_failures),
        capability_results=tuple(capability_results),
        cpp_unavailable_reason=cpp_unavailable_reason if cpp_evidence is None else None,
    )


def format_report(report: ParityReport) -> str:
    lines: list[str] = []
    if report.cpp_unavailable_reason:
        lines.append(f"C++ PARITY NOT EVALUATED: {report.cpp_unavailable_reason}")
        lines.append("(Python-side evidence integrity was still checked below.)")
    for failure in report.evidence_failures:
        lines.append(f"EVIDENCE FAILURE: {failure}")
    for result in report.capability_results:
        lines.append(f"{result.status:<18} {result.capability:<40} {result.detail}")
    lines.append("OK" if report.ok else "FAIL")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Host parity CI gate: compare Python/C++ E16-7 evidence")
    parser.add_argument("--python-evidence", required=True, metavar="PATH", help="E16-7 evidence JSON for Python")
    parser.add_argument(
        "--cpp-evidence",
        default=None,
        metavar="PATH",
        help="E16-7 evidence JSON for the C++ host; omit only together with --cpp-unavailable-reason",
    )
    parser.add_argument(
        "--cpp-unavailable-reason",
        default=None,
        metavar="TEXT",
        help="explicit reason the C++ evidence could not be produced in this run (required if --cpp-evidence is omitted)",
    )
    parser.add_argument(
        "--known-gaps",
        default=str(DEFAULT_KNOWN_GAPS_PATH),
        metavar="PATH",
        help=f"known-gaps manifest (default: {DEFAULT_KNOWN_GAPS_PATH})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        python_evidence = load_evidence(args.python_evidence)
        cpp_evidence = load_evidence(args.cpp_evidence) if args.cpp_evidence else None
        known_gaps = load_known_gaps(args.known_gaps)
        report = check_parity(
            python_evidence=python_evidence,
            cpp_evidence=cpp_evidence,
            known_gaps=known_gaps,
            cpp_unavailable_reason=args.cpp_unavailable_reason,
        )
    except HostParityGateError as exc:
        print(f"HOST PARITY GATE ERROR: {exc}")
        return 2

    print(format_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
