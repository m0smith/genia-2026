"""
E16-7 conformance evidence reporting (issue #764).

Builds one deterministic evidence document per ``--host`` run: the exact
contract revision (declared, this checkout's, and its E16-4
classification), protocol version, advertised capabilities, applicable
case count, and the full six-state outcome taxonomy count. Pure function
of its inputs, so repeated runs over the same deterministic inputs
produce byte-identical evidence (E16-7 acceptance criterion). Never
claims an unsupported or unexecuted case as passing: ``pass`` is always
its own field, distinct from ``unsupported``/``protocol_error``/``crash``/
``timeout``, and ``applicable_cases`` never exceeds ``total_cases``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

from .revision import RevisionCheck

_COUNT_FIELDS = ("pass", "fail", "unsupported", "protocol_error", "crash", "timeout", "invalid")


@dataclass(frozen=True)
class EvidenceCounts:
    passed: int
    failed: int
    unsupported: int
    protocol_error: int
    crash: int
    timeout: int
    invalid: int

    def as_dict(self) -> dict[str, int]:
        return {
            "pass": self.passed,
            "fail": self.failed,
            "unsupported": self.unsupported,
            "protocol_error": self.protocol_error,
            "crash": self.crash,
            "timeout": self.timeout,
            "invalid": self.invalid,
        }


def build_evidence(
    *,
    capabilities_result: Mapping[str, object],
    revision_check: RevisionCheck,
    total_cases: int,
    counts: EvidenceCounts,
) -> dict:
    """Build the deterministic per-host evidence document."""
    counted = sum(counts.as_dict().values())
    if counted != total_cases:
        raise ValueError(
            f"evidence counts sum to {counted}, but total_cases is {total_cases}; "
            "every discovered case must resolve to exactly one taxonomy outcome"
        )
    applicable_cases = total_cases - counts.invalid

    return {
        "protocol_version": capabilities_result["protocol_version"],
        "contract_revision": {
            "declared": revision_check.declared_revision,
            "checkout": revision_check.current_revision,
            "classification": revision_check.kind,
        },
        "capabilities": dict(capabilities_result["capabilities"]),
        "capability_operations": list(capabilities_result["operations"]),
        "total_cases": total_cases,
        "applicable_cases": applicable_cases,
        "counts": counts.as_dict(),
    }


def encode_evidence(evidence: Mapping[str, object]) -> str:
    """Deterministic JSON serialization: sorted keys, stable indentation, a
    trailing newline. Identical evidence documents always encode to
    byte-identical text."""
    return json.dumps(evidence, sort_keys=True, indent=2) + "\n"


def write_evidence(path: str | Path, evidence: Mapping[str, object]) -> None:
    Path(path).write_text(encode_evidence(evidence), encoding="utf-8")
