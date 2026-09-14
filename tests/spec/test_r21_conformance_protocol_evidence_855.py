"""E21-3 (#855) R21 conformance evidence, in-process and through the R16 protocol.

Mirrors tests/spec/test_r18_conformance_protocol_evidence_795.py's pattern:
portable evidence that has only ever run in-process is an untested claim
about the transport. These tests prove the R21 cases (numeric source
classification and tagged Core IR payloads) also pass through the R16
generic host protocol path -- subprocess execution, JSON envelopes,
capability negotiation -- and, critically, that they are *executed*
rather than declined.

A run in which every R21 case was reported `unsupported` must not look the
same as a run in which they passed. Asserting only an aggregate pass count
would not distinguish the two.
"""

from __future__ import annotations

import shlex
import sys
from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.host_executor import execute_spec_via_host
from tools.spec_runner.loader import discover_specs


REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_ADAPTER_COMMAND = f"{sys.executable} -m hosts.python.protocol_adapter"

# R21 evidence lives in both the parse category (source classification,
# #853) and the ir category (tagged IrLiteral payloads, #854), named
# "parse-r21-...", "parse-error-r21-...", and "r21-..." respectively --
# so this matches by substring, not prefix, unlike the R18 precedent
# (whose evidence is single-category and prefix-named).
R21_SUBSTRING = "r21"


def r21_specs():
    specs, invalid_specs = discover_specs()
    assert not invalid_specs, f"invalid specs: {invalid_specs}"
    return [spec for spec in specs if R21_SUBSTRING in spec.name]


def test_r21_cases_exist_and_span_the_expected_families() -> None:
    """Guard against the suite silently shrinking to nothing."""
    names = {spec.name for spec in r21_specs()}
    assert len(names) >= 18, f"expected the R21 conformance suite, found {len(names)}"

    # One representative case per family that must have shared coverage
    # (docs/design/r21-numeric-source-portable-representation-contract.md
    # section 5's required evidence list).
    required = {
        "parse-r21-integer-source-classification",
        "parse-r21-huge-integer-source-classification",
        "parse-r21-decimal-dotted-classification",
        "parse-r21-decimal-exponent-only-classification",
        "parse-r21-decimal-dot-exponent-classification",
        "parse-r21-decimal-equivalent-spelling-trailing-zero",
        "parse-r21-decimal-equivalent-spelling-exponent-form",
        "parse-error-r21-malformed-exponent-missing-digits",
        "parse-error-r21-malformed-exponent-sign-only",
        "parse-error-r21-leading-dot-rejected",
        "parse-error-r21-trailing-dot-rejected",
        "r21-integer-literal-tagged-payload",
        "r21-huge-integer-literal-tagged-payload",
        "r21-decimal-dotted-literal-tagged-payload",
        "r21-decimal-exponent-literal-tagged-payload",
        "r21-decimal-equivalent-spellings-identical-payload",
        "r21-unary-negative-decimal-tagged-payload",
        "r21-slash-remains-ordinary-binary",
    }
    missing = required - names
    assert not missing, f"R21 conformance coverage lost cases: {sorted(missing)}"


def test_every_r21_case_passes_in_process() -> None:
    failures = []
    for spec in r21_specs():
        actual = execute_spec(spec)
        for failure in compare_spec(spec, actual):
            failures.append((spec.name, failure))
    assert not failures, f"in-process R21 failures: {failures}"


@pytest.mark.slow
@pytest.mark.spec
def test_every_r21_case_passes_through_the_generic_host_protocol() -> None:
    """The transport claim: R21 evidence is reproducible by an external host.

    Each case must resolve to `pass`. Any other outcome -- including
    `unsupported` -- is a failure of the conformance claim, because a host
    that declines these cases has not demonstrated R21 conformance.
    """
    host_command = shlex.split(PROTOCOL_ADAPTER_COMMAND)
    declined = []
    failed = []

    for spec in r21_specs():
        result = execute_spec_via_host(spec, host_command, timeout=60.0)
        if result.kind == "pass":
            continue
        if result.kind == "fail":
            failed.append((spec.name, result.failures))
        else:
            declined.append((spec.name, result.kind, result.reason))

    assert not failed, f"R21 cases failed through the protocol path: {failed}"
    assert not declined, (
        "R21 cases were not executed through the protocol path "
        f"(unsupported/crash/timeout/protocol_error): {declined}. "
        "Unsupported must never be counted as passing."
    )
