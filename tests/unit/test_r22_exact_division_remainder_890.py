"""E22-4 (issue #890): exact division and floor remainder.

Covers docs/design/r22-exact-numeric-runtime-contract.md sections 7 and 8:
exact `/` selects Integer/Decimal/Rational per the division-result table
(a reduced quotient terminates in base 10 exactly when its denominator has
no prime factors other than 2 and 5), and `%` is floor remainder using the
same exact-family promotion rule as +, -, *.
"""
from __future__ import annotations

import pytest

from src.genia.numeric_runtime import GeniaDecimal, GeniaRational, rational_from_integers


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


def _dec(coefficient: int, exponent: int) -> GeniaDecimal:
    return GeniaDecimal(coefficient, exponent)


# ---------------------------------------------------------------------------
# Contract section 7's six required proof examples
# ---------------------------------------------------------------------------


def test_integer_evenly_divisible_is_integer() -> None:
    result = _run("6 / 3")
    assert type(result) is int and result == 2


def test_integer_not_evenly_divisible_is_rational() -> None:
    result = _run("1 / 2")
    assert type(result).__name__ == "GeniaRational"
    assert (result.numerator, result.denominator) == (1, 2)


def test_integer_division_non_terminating_is_rational() -> None:
    result = _run("1 / 3")
    assert type(result).__name__ == "GeniaRational"
    assert (result.numerator, result.denominator) == (1, 3)


def test_decimal_integer_division_terminating_is_decimal() -> None:
    result = _run("1.0 / 2")
    assert type(result).__name__ == "GeniaDecimal"
    assert (result.coefficient, result.exponent) == (5, -1)


def test_decimal_integer_division_non_terminating_is_rational() -> None:
    result = _run("1.0 / 3")
    assert type(result).__name__ == "GeniaRational"
    assert (result.numerator, result.denominator) == (1, 3)


def test_rational_round_trip_collapses_to_integer() -> None:
    result = _run("(1 / 3) * 3")
    assert result == 1
    assert type(result) is int


# ---------------------------------------------------------------------------
# Termination detection edge cases
# ---------------------------------------------------------------------------


def test_pure_integer_division_never_becomes_decimal() -> None:
    # 1 / 40 = 0.025 exactly, and 40's only prime factors are 2 and 5 --
    # but pure Integer/Integer division is Integer-or-Rational only, never
    # Decimal (contract section 7's table has no Decimal cell for the
    # Integer row/column combination).
    result = _run("1 / 40")
    assert type(result).__name__ == "GeniaRational"
    assert (result.numerator, result.denominator) == (1, 40)


def test_decimal_participation_with_terminating_denominator_is_decimal() -> None:
    # 1.0 / 40 = 0.025; 40 = 2^3 * 5, and a Decimal operand participates.
    result = _run("1.0 / 40")
    assert type(result).__name__ == "GeniaDecimal"
    assert (result.coefficient, result.exponent) == (25, -3)


def test_decimal_participation_integral_quotient_stays_decimal() -> None:
    # 2.0 / 2 = 1, but Decimal participation retains Decimal kind even for
    # an integral quotient (contract section 6's rule, carried into /).
    result = _run("2.0 / 2")
    assert type(result).__name__ == "GeniaDecimal"
    assert (result.coefficient, result.exponent) == (1, 0)


def test_denominator_with_other_prime_factor_does_not_terminate() -> None:
    # 1 / 7 has denominator with prime factor 7 -> Rational
    result = _run("1 / 7")
    assert type(result).__name__ == "GeniaRational"
    assert (result.numerator, result.denominator) == (1, 7)


def test_denominator_11_times_power_of_ten_does_not_terminate() -> None:
    # 1.0 / 22 = 1/(2*11): the *reduced* denominator has prime factor 11,
    # so this must be Rational even though 22 shares a factor of 2 with 10,
    # and even with Decimal participation.
    result = _run("1.0 / 22")
    assert type(result).__name__ == "GeniaRational"
    assert (result.numerator, result.denominator) == (1, 22)


# ---------------------------------------------------------------------------
# Rational participation always yields Rational (or collapsed Integer)
# ---------------------------------------------------------------------------


def test_rational_divided_by_integer() -> None:
    result = rational_from_integers(1, 2)
    from src.genia.numeric_runtime import exact_divide

    quotient = exact_divide(result, 2)
    assert isinstance(quotient, GeniaRational)
    assert (quotient.numerator, quotient.denominator) == (1, 4)


def test_rational_divided_by_rational_collapses() -> None:
    from src.genia.numeric_runtime import exact_divide

    half = rational_from_integers(1, 2)
    quotient = exact_divide(half, half)
    assert quotient == 1
    assert type(quotient) is int


def test_decimal_divided_by_rational_is_rational() -> None:
    from src.genia.numeric_runtime import exact_divide

    quotient = exact_divide(_dec(5, -1), rational_from_integers(1, 4))  # 0.5 / (1/4) = 2
    assert quotient == 2
    assert type(quotient) is int


# ---------------------------------------------------------------------------
# Division by zero: deterministic misuse, not a silently-returned value
# ---------------------------------------------------------------------------


def test_integer_division_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        _run("1 / 0")


def test_decimal_division_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        _run("1.0 / 0")


def test_rational_division_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        _run("rational(1, 2) / 0")


def test_integer_remainder_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        _run("1 % 0")


def test_division_by_zero_message_is_deterministic_not_host_leaked() -> None:
    from src.genia.numeric_runtime import exact_divide

    with pytest.raises(ZeroDivisionError) as excinfo:
        exact_divide(1, 0)
    assert str(excinfo.value) == "exact division by zero"


# ---------------------------------------------------------------------------
# Floor remainder: positive and negative operand combinations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "left,right,expected",
    [
        (7, 3, 1),
        (-7, 3, 2),
        (7, -3, -2),
        (-7, -3, -1),
        (6, 3, 0),
        (-6, 3, 0),
    ],
)
def test_integer_floor_remainder(left: int, right: int, expected: int) -> None:
    result = _run(f"{left} % {right}")
    assert result == expected
    assert type(result) is int


def test_decimal_floor_remainder_stays_decimal() -> None:
    # 5.5 % 2 : floor(5.5/2) = floor(2.75) = 2; 5.5 - 2*2 = 1.5
    result = _run("5.5 % 2")
    assert type(result).__name__ == "GeniaDecimal"
    assert (result.coefficient, result.exponent) == (15, -1)


def test_negative_decimal_floor_remainder() -> None:
    # -5.5 % 2: floor(-5.5/2) = floor(-2.75) = -3; -5.5 - (-3*2) = 0.5
    result = _run("-5.5 % 2")
    assert type(result).__name__ == "GeniaDecimal"
    assert (result.coefficient, result.exponent) == (5, -1)


def test_rational_floor_remainder() -> None:
    # rational(7,2) % 1 : floor(3.5) = 3; 7/2 - 3 = 1/2
    result = _run("rational(7, 2) % 1")
    assert type(result).__name__ == "GeniaRational"
    assert (result.numerator, result.denominator) == (1, 2)


def test_remainder_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        _run("1.0 % 0")
