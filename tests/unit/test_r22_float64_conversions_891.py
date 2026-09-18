"""E22-5 (issue #891): explicit Float64 value and conversions.

Covers docs/design/r22-exact-numeric-runtime-contract.md sections 4 and 5:
float64(value) converts an exact numeric value to IEEE-754 binary64
(round-nearest ties-even, magnitude overflow fails rather than silently
becoming infinity, exact zero converts to positive Float64 zero), and
exact(value) is its inverse (finite Float64 -> the exact Decimal it
represents -- bit-level reconstruction, not shortest round-tripping text).
"""
from __future__ import annotations

import math

import pytest

from src.genia.numeric_runtime import GeniaDecimal, exact, rational_from_integers, to_float64


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


def _dec(coefficient: int, exponent: int) -> GeniaDecimal:
    return GeniaDecimal(coefficient, exponent)


# ---------------------------------------------------------------------------
# float64(...)
# ---------------------------------------------------------------------------


def test_float64_of_integer() -> None:
    assert to_float64(2) == 2.0
    assert isinstance(to_float64(2), float)


def test_float64_of_decimal() -> None:
    assert to_float64(_dec(15, -1)) == 1.5


def test_float64_of_rational_is_round_nearest_ties_even() -> None:
    result = to_float64(rational_from_integers(1, 3))
    assert result == pytest.approx(1 / 3, abs=0)
    assert result == 1 / 3  # Python's own correctly-rounded int/int division


def test_float64_of_existing_float64_is_identity() -> None:
    assert to_float64(3.5) == 3.5
    assert to_float64(float("nan")) != to_float64(float("nan"))  # NaN unchanged, still NaN


def test_float64_exact_zero_is_positive_zero() -> None:
    result = to_float64(0)
    assert result == 0.0
    assert math.copysign(1.0, result) == 1.0


def test_float64_decimal_zero_is_positive_zero() -> None:
    result = to_float64(_dec(0, 0))
    assert result == 0.0
    assert math.copysign(1.0, result) == 1.0


def test_float64_magnitude_overflow_fails_rather_than_infinity() -> None:
    huge = 10**400
    with pytest.raises(OverflowError):
        to_float64(huge)


def test_float64_rejects_bool() -> None:
    with pytest.raises(TypeError):
        to_float64(True)


def test_float64_rejects_non_numeric() -> None:
    with pytest.raises(TypeError):
        to_float64("1.5")


# ---------------------------------------------------------------------------
# exact(...)
# ---------------------------------------------------------------------------


def test_exact_of_integer_decimal_rational_unchanged() -> None:
    assert exact(5) == 5
    assert type(exact(5)) is int
    decimal_value = _dec(15, -1)
    assert exact(decimal_value) is decimal_value
    rational_value = rational_from_integers(1, 3)
    assert exact(rational_value) is rational_value


def test_exact_of_float64_0_1_matches_contract_worked_example() -> None:
    # docs/design/r22-exact-numeric-runtime-contract.md section 5's own
    # worked example: the exact real value denoted by the binary64 bits
    # nearest to 0.1.
    result = exact(0.1)
    assert isinstance(result, GeniaDecimal)
    assert str(result) == "0.1000000000000000055511151231257827021181583404541015625"


def test_exact_of_integral_float() -> None:
    result = exact(4.0)
    assert isinstance(result, GeniaDecimal)
    assert (result.coefficient, result.exponent) == (4, 0)


def test_exact_of_positive_zero() -> None:
    result = exact(0.0)
    assert isinstance(result, GeniaDecimal)
    assert (result.coefficient, result.exponent) == (0, 0)


def test_exact_of_negative_zero_is_decimal_zero() -> None:
    result = exact(-0.0)
    assert isinstance(result, GeniaDecimal)
    assert (result.coefficient, result.exponent) == (0, 0)


def test_exact_of_nan_fails() -> None:
    with pytest.raises(ValueError):
        exact(float("nan"))


def test_exact_of_infinity_fails() -> None:
    with pytest.raises(ValueError):
        exact(float("inf"))
    with pytest.raises(ValueError):
        exact(float("-inf"))


def test_exact_rejects_bool() -> None:
    with pytest.raises(TypeError):
        exact(True)


def test_exact_round_trip_through_float64() -> None:
    original = rational_from_integers(1, 4)  # 0.25, exactly representable
    assert exact(to_float64(original)) == _dec(25, -2)


# ---------------------------------------------------------------------------
# Through the evaluator
# ---------------------------------------------------------------------------


def test_genia_source_float64_and_exact() -> None:
    assert _run("float64(2)") == 2.0
    # `0.1` in Genia source is already an exact GeniaDecimal literal (R22
    # E22-1), so exact(0.1) alone would just return it unchanged -- this
    # proves the Float64 round-trip specifically.
    result = _run("exact(float64(0.1))")
    assert type(result).__name__ == "GeniaDecimal"
    assert str(result) == "0.1000000000000000055511151231257827021181583404541015625"
