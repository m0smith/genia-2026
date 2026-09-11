"""E18-5 (#795) R18 conformance evidence, in-process and through the R16 protocol.

Portable evidence that has only ever run in-process is an untested claim about
the transport. These tests prove the R18 cases also pass through the R16 generic
host protocol path — subprocess execution, JSON envelopes, capability
negotiation — and, critically, that they are *executed* rather than declined.

A run in which every R18 case was reported `unsupported` must not look the same
as a run in which they passed. Asserting only an aggregate pass count would not
distinguish the two.
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

# Every R18 case is identified by its filename prefix rather than a hard-coded
# list, so a case added by a later R18 ticket is covered automatically and cannot
# be silently omitted from the conformance claim.
R18_PREFIX = "r18-"


def r18_specs():
    specs, invalid_specs = discover_specs()
    assert not invalid_specs, f"invalid specs: {invalid_specs}"
    return [spec for spec in specs if spec.name.startswith(R18_PREFIX)]


def test_r18_cases_exist_and_span_the_expected_families() -> None:
    """Guard against the suite silently shrinking to nothing."""
    names = {spec.name for spec in r18_specs()}
    assert len(names) >= 20, f"expected the R18 conformance suite, found {len(names)}"

    # One representative case per family that must have shared coverage.
    required = {
        "r18-equality-boolean-number-separation",
        "r18-equality-exact-int-float-bridge",
        "r18-equality-nan-non-reflexive",
        "r18-equality-structural-contents",
        "r18-map-structural-equality",
        "r18-map-key-equivalence-is-equality",
        "r18-map-key-nan-rejected",
        "r18-identity-bearing-equality",
        "r18-protected-equality-is-carrier-identity",
        "r18-surface-agreement-across-equality-like-paths",
        "r18-surface-assert-eq-uses-one-relation",
        "r18-conformance-represented-and-pair-structure",
        "r18-conformance-sheet-structural-equality",
        "r18-conformance-protected-in-containers-and-patterns",
        "r18-conformance-cross-family-summary",
    }
    missing = required - names
    assert not missing, f"R18 conformance coverage lost cases: {sorted(missing)}"


def test_every_r18_case_passes_in_process() -> None:
    failures = []
    for spec in r18_specs():
        actual = execute_spec(spec)
        for failure in compare_spec(spec, actual):
            failures.append((spec.name, failure))
    assert not failures, f"in-process R18 failures: {failures}"


@pytest.mark.slow
@pytest.mark.spec
def test_every_r18_case_passes_through_the_generic_host_protocol() -> None:
    """The transport claim: R18 evidence is reproducible by an external host.

    Each case must resolve to `pass`. Any other outcome — including
    `unsupported` — is a failure of the conformance claim, because a host that
    declines these cases has not demonstrated R18 conformance.
    """
    host_command = shlex.split(PROTOCOL_ADAPTER_COMMAND)
    declined = []
    failed = []

    for spec in r18_specs():
        result = execute_spec_via_host(spec, host_command, timeout=60.0)
        if result.kind == "pass":
            continue
        if result.kind == "fail":
            failed.append((spec.name, result.failures))
        else:
            declined.append((spec.name, result.kind, result.reason))

    assert not failed, f"R18 cases failed through the protocol path: {failed}"
    assert not declined, (
        "R18 cases were not executed through the protocol path "
        f"(unsupported/crash/timeout/protocol_error): {declined}. "
        "Unsupported must never be counted as passing."
    )
