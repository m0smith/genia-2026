"""E22-8 (issue #894): numeric misuse, resource limits, and diagnostic
normalization.

Covers docs/design/r22-exact-numeric-runtime-contract.md sections 11 and
13: every deterministic numeric-misuse family already introduced by
E22-1..E22-7 produces a normalized diagnostic with no raw host exception
text, and numeric-resource-limit is implemented as a private,
non-public-semantics host bound.
"""
from __future__ import annotations

import pytest

from src.genia.numeric_runtime import (
    GeniaDecimal,
    NumericResourceLimitError,
    _numeric_resource_limit_test_seam,
    exact,
    rational_from_integers,
    to_float64,
)


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


# ---------------------------------------------------------------------------
# Audit: every misuse family already produces a normalized diagnostic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source,message",
    [
        ("1 / 0", "exact division by zero"),
        ("1 % 0", "exact remainder by zero"),
        ("float64(1) / float64(0)", "float64 division by zero"),
        ("float64(1) % float64(0)", "float64 remainder by zero"),
        ("rational(1, 0)", "rational expected a nonzero denominator"),
        ("rational(1.5, 2)", "rational expected an Integer numerator, received decimal"),
        ("rational(true, 2)", "rational expected an Integer numerator, received bool"),
        ("exact(__r18_conformance_test_only_nan)", "exact expected a finite value, received NaN"),
        (
            "map_put(map_new(), __r18_conformance_test_only_nan, 1)",
            "map key must equal itself; NaN is not a legal map key",
        ),
    ],
)
def test_misuse_message_is_deterministic_and_clean(source: str, message: str) -> None:
    """No raw Python exception text, traceback fragment, or host module
    path ever appears -- each message is exactly the one this project
    authored."""
    with pytest.raises(Exception) as excinfo:
        _run(source)
    assert str(excinfo.value) == message
    # No leaked Python internals: file paths, "Traceback", or bare type
    # names that would mean a raw exception crossed the diagnostic
    # boundary unformatted.
    assert "Traceback" not in str(excinfo.value)
    assert ".py" not in str(excinfo.value)


def test_float64_magnitude_overflow_message_is_clean() -> None:
    huge = 10**400
    with pytest.raises(OverflowError) as excinfo:
        to_float64(huge)
    assert str(excinfo.value) == "float64: exact magnitude exceeds the largest finite binary64 value"


def test_mixed_domain_rejection_uses_existing_type_error_mechanism() -> None:
    # Not a raised exception at all -- reuses the evaluator's existing
    # none("type-error", ...) value mechanism, consistent with how every
    # other type mismatch in this evaluator already behaves.
    result = _run("1 + float64(2)")
    assert type(result).__name__ == "GeniaOptionNone"


# ---------------------------------------------------------------------------
# numeric-resource-limit
# ---------------------------------------------------------------------------


def test_resource_limit_seam_is_off_by_default_for_ordinary_values() -> None:
    # A merely large (not host-resource-exhausting) value -- comfortably
    # under both this project's default bound and CPython's own
    # int-to-decimal-text conversion guard -- must not trip the limit.
    # Deliberately not a power of ten, so canonicalization does not strip
    # it down to a small coefficient.
    large = 10**1000 + 1
    assert GeniaDecimal(large, 0).coefficient == large
    assert rational_from_integers(large, large + 2) is not None


def test_resource_limit_seam_triggers_deterministically_for_decimal() -> None:
    with _numeric_resource_limit_test_seam(max_bits=32):
        with pytest.raises(NumericResourceLimitError) as excinfo:
            GeniaDecimal(2**40, 0)
    assert str(excinfo.value) == "numeric-resource-limit"


def test_resource_limit_seam_triggers_deterministically_for_rational() -> None:
    with _numeric_resource_limit_test_seam(max_bits=32):
        with pytest.raises(NumericResourceLimitError) as excinfo:
            rational_from_integers(2**40 + 1, 3)
    assert str(excinfo.value) == "numeric-resource-limit"


def test_resource_limit_seam_restores_previous_bound() -> None:
    with _numeric_resource_limit_test_seam(max_bits=32):
        pass
    # After the context manager exits, a value that would have tripped
    # the lowered bound must succeed again under the restored default.
    assert GeniaDecimal(2**40, 0).coefficient == 2**40


def test_resource_limit_is_not_reported_as_type_error_or_overflow() -> None:
    """NumericResourceLimitError is its own exception kind -- never
    disguised as a language-level numeric overflow (OverflowError) or a
    generic type mismatch (TypeError), matching contract section 11: the
    failure must not be presented as numeric overflow or a smaller
    language domain."""
    with _numeric_resource_limit_test_seam(max_bits=32):
        with pytest.raises(NumericResourceLimitError):
            GeniaDecimal(2**40, 0)
        with pytest.raises(NumericResourceLimitError):
            rational_from_integers(2**40 + 1, 3)


def test_resource_limit_via_genia_source_is_deterministic() -> None:
    """Exercised through the evaluator, not just the constructor directly,
    to prove the failure propagates as a program-terminating deterministic
    error (consistent with zero-division precedent), never a silently
    truncated/rounded value."""
    with _numeric_resource_limit_test_seam(max_bits=32):
        with pytest.raises(NumericResourceLimitError):
            _run(f"{2**40}.5")


def test_resource_limit_seam_not_reachable_from_genia_source() -> None:
    """The seam itself is a private Python-only test utility, never a
    Genia builtin or otherwise reachable from Genia source."""
    result = _run("1 + 1")
    assert result == 2  # sanity: ordinary evaluation is completely unaffected
    with pytest.raises(Exception):
        _run("_numeric_resource_limit_test_seam(32)")
