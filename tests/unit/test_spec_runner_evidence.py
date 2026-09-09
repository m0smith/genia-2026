"""
E16-7 (issue #764) conformance evidence reporting tests.
"""
from __future__ import annotations

import json

import pytest

from tools.spec_runner.evidence import (
    EvidenceCounts,
    build_evidence,
    encode_evidence,
    write_evidence,
)
from tools.spec_runner.revision import RevisionCheck

_CAPABILITIES_RESULT = {
    "capabilities": {"parser": "supported", "shared_spec_runner": "partial"},
    "operations": ["parse", "lower", "eval", "cli"],
    "contract_revision": "a" * 40,
    "protocol_version": "1",
}


def _revision_check(kind: str = "current") -> RevisionCheck:
    return RevisionCheck(kind=kind, declared_revision="a" * 40, current_revision="a" * 40)


def _counts(**overrides) -> EvidenceCounts:
    base = dict(passed=0, failed=0, unsupported=0, protocol_error=0, crash=0, timeout=0, invalid=0)
    base.update(overrides)
    return EvidenceCounts(**base)


# --- build_evidence: shape and correctness --------------------------------------------------


def test_build_evidence_shape() -> None:
    evidence = build_evidence(
        capabilities_result=_CAPABILITIES_RESULT,
        revision_check=_revision_check(),
        total_cases=10,
        counts=_counts(passed=7, failed=1, unsupported=2),
    )
    assert evidence == {
        "protocol_version": "1",
        "contract_revision": {
            "declared": "a" * 40,
            "checkout": "a" * 40,
            "classification": "current",
        },
        "capabilities": {"parser": "supported", "shared_spec_runner": "partial"},
        "capability_operations": ["parse", "lower", "eval", "cli"],
        "total_cases": 10,
        "applicable_cases": 10,
        "counts": {
            "pass": 7,
            "fail": 1,
            "unsupported": 2,
            "protocol_error": 0,
            "crash": 0,
            "timeout": 0,
            "invalid": 0,
        },
    }


def test_build_evidence_applicable_cases_excludes_invalid() -> None:
    evidence = build_evidence(
        capabilities_result=_CAPABILITIES_RESULT,
        revision_check=_revision_check(),
        total_cases=5,
        counts=_counts(passed=4, invalid=1),
    )
    assert evidence["total_cases"] == 5
    assert evidence["applicable_cases"] == 4


def test_build_evidence_rejects_counts_that_do_not_sum_to_total() -> None:
    with pytest.raises(ValueError, match="counts sum to"):
        build_evidence(
            capabilities_result=_CAPABILITIES_RESULT,
            revision_check=_revision_check(),
            total_cases=10,
            counts=_counts(passed=3),  # sums to 3, not 10
        )


def test_build_evidence_records_declared_vs_checkout_revision_separately() -> None:
    revision_check = RevisionCheck(kind="resolvable_ancestor", declared_revision="b" * 40, current_revision="c" * 40)
    evidence = build_evidence(
        capabilities_result=_CAPABILITIES_RESULT,
        revision_check=revision_check,
        total_cases=1,
        counts=_counts(passed=1),
    )
    assert evidence["contract_revision"] == {
        "declared": "b" * 40,
        "checkout": "c" * 40,
        "classification": "resolvable_ancestor",
    }


@pytest.mark.parametrize("field", ["pass", "unsupported", "protocol_error", "crash", "timeout", "invalid"])
def test_build_evidence_never_folds_a_non_pass_outcome_into_pass(field: str) -> None:
    """Every outcome kind is its own counted field; setting any non-pass
    field to a nonzero value must never change the pass count."""
    kwargs = {
        "pass": "passed",
        "fail": "failed",
        "unsupported": "unsupported",
        "protocol_error": "protocol_error",
        "crash": "crash",
        "timeout": "timeout",
        "invalid": "invalid",
    }
    counts = _counts(**{kwargs[field]: 3})
    evidence = build_evidence(
        capabilities_result=_CAPABILITIES_RESULT,
        revision_check=_revision_check(),
        total_cases=3,
        counts=counts,
    )
    if field != "pass":
        assert evidence["counts"]["pass"] == 0
    assert evidence["counts"][field] == 3


# --- determinism -----------------------------------------------------------------------------


def test_encode_evidence_is_deterministic_across_repeated_calls() -> None:
    evidence = build_evidence(
        capabilities_result=_CAPABILITIES_RESULT,
        revision_check=_revision_check(),
        total_cases=2,
        counts=_counts(passed=2),
    )
    assert encode_evidence(evidence) == encode_evidence(evidence)
    assert encode_evidence(evidence) == encode_evidence(dict(evidence))  # order-independent input


def test_encode_evidence_is_valid_json_with_sorted_keys() -> None:
    evidence = build_evidence(
        capabilities_result=_CAPABILITIES_RESULT,
        revision_check=_revision_check(),
        total_cases=1,
        counts=_counts(passed=1),
    )
    text = encode_evidence(evidence)
    assert json.loads(text) == evidence
    assert text.endswith("\n")


def test_write_evidence_writes_the_encoded_document(tmp_path) -> None:
    evidence = build_evidence(
        capabilities_result=_CAPABILITIES_RESULT,
        revision_check=_revision_check(),
        total_cases=1,
        counts=_counts(passed=1),
    )
    path = tmp_path / "evidence.json"
    write_evidence(path, evidence)
    assert json.loads(path.read_text(encoding="utf-8")) == evidence
