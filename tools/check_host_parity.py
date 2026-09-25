"""Validate and summarize Python/C++ R16 conformance evidence for CI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HARD_FAILURES = ("fail", "protocol_error", "crash", "timeout", "invalid")
VALID_CAPABILITY_STATES = {"supported", "partial", "unsupported"}


class ParityError(ValueError):
    """Raised when host evidence cannot support the parity gate."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ParityError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ParityError(f"{path} must contain a JSON object")
    return value


def _validate_host(
    host: str, evidence: dict[str, Any], policy: dict[str, Any]
) -> list[str]:
    counts = evidence.get("counts")
    capabilities = evidence.get("capabilities")
    if not isinstance(counts, dict) or not isinstance(capabilities, dict):
        raise ParityError(f"{host}: evidence must contain counts and capabilities objects")

    missing_counts = [name for name in (*HARD_FAILURES, "pass", "unsupported") if name not in counts]
    if missing_counts:
        raise ParityError(f"{host}: evidence is missing counts: {', '.join(missing_counts)}")

    hard = {name: counts[name] for name in HARD_FAILURES if counts[name] != 0}
    if hard:
        raise ParityError(f"{host}: conformance failures are nonzero: {hard}")

    expected_gaps = policy.get("expected_non_supported_capabilities")
    if not isinstance(expected_gaps, dict) or any(
        state not in VALID_CAPABILITY_STATES - {"supported"}
        for state in expected_gaps.values()
    ):
        raise ParityError(f"{host}: gap policy has invalid capability states")
    observed_gaps = {
        name: state for name, state in capabilities.items() if state != "supported"
    }
    if observed_gaps != expected_gaps:
        missing = {k: v for k, v in expected_gaps.items() if observed_gaps.get(k) != v}
        unexpected = {k: v for k, v in observed_gaps.items() if expected_gaps.get(k) != v}
        raise ParityError(
            f"{host}: capability gaps differ from spec/host-parity-gaps.json; "
            f"missing_or_changed={missing}, unexpected={unexpected}"
        )

    unsupported = counts["unsupported"]
    if unsupported and policy.get("unsupported_case_policy") != "allowed":
        raise ParityError(f"{host}: {unsupported} unsupported cases are not allowed")
    reason = policy.get("unsupported_case_reason")
    if unsupported and not isinstance(reason, str):
        raise ParityError(f"{host}: unsupported cases require a documented reason")

    lines = [
        f"{host.upper()} PASS: {counts['pass']} shared cases passed; "
        f"hard failures=0; unsupported={unsupported}."
    ]
    if unsupported:
        lines.append(f"{host.upper()} KNOWN GAP: {reason}")
    if observed_gaps:
        rendered = ", ".join(f"{name}={state}" for name, state in sorted(observed_gaps.items()))
        lines.append(f"{host.upper()} CAPABILITY GAPS: {rendered}")
    return lines


def check_parity(
    python_evidence: dict[str, Any],
    cpp_evidence: dict[str, Any],
    policies: dict[str, Any],
) -> list[str]:
    """Return readable parity lines or raise when evidence fails the gate."""
    if python_evidence.get("total_cases") != cpp_evidence.get("total_cases"):
        raise ParityError(
            "hosts did not run the same shared inventory: "
            f"python={python_evidence.get('total_cases')}, "
            f"cpp={cpp_evidence.get('total_cases')}"
        )
    python_checkout = python_evidence.get("contract_revision", {}).get("checkout")
    cpp_checkout = cpp_evidence.get("contract_revision", {}).get("checkout")
    if not python_checkout or python_checkout != cpp_checkout:
        raise ParityError(
            f"hosts did not run against the same contract revision: "
            f"python={python_checkout!r}, cpp={cpp_checkout!r}"
        )
    if set(policies) != {"python", "cpp"}:
        raise ParityError("gap manifest must define exactly python and cpp policies")

    host_lines: dict[str, list[str]] = {}
    host_errors: dict[str, str] = {}
    for host, evidence in (("python", python_evidence), ("cpp", cpp_evidence)):
        try:
            host_lines[host] = _validate_host(host, evidence, policies[host])
        except ParityError as exc:
            host_errors[host] = str(exc)
    if host_errors:
        results = "; ".join(
            f"{host}={'FAIL (' + host_errors[host] + ')' if host in host_errors else 'PASS'}"
            for host in ("python", "cpp")
        )
        raise ParityError(results)

    lines = host_lines["python"] + host_lines["cpp"]
    lines.append(
        f"PARITY PASS: both hosts ran {python_evidence['total_cases']} shared cases "
        f"at contract revision {python_checkout}; unsupported remains a documented gap."
    )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-evidence", type=Path, required=True)
    parser.add_argument("--cpp-evidence", type=Path, required=True)
    parser.add_argument(
        "--gaps", type=Path, default=Path("spec/host-parity-gaps.json")
    )
    args = parser.parse_args(argv)
    try:
        lines = check_parity(
            _load_json(args.python_evidence),
            _load_json(args.cpp_evidence),
            _load_json(args.gaps),
        )
    except ParityError as exc:
        print(f"PARITY FAIL: {exc}")
        return 1
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
