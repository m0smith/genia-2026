"""E22-3 (issue #889): exact-family +, -, *, and unary negation.

Covers docs/design/r22-exact-numeric-runtime-contract.md section 6: the
Integer < Decimal < Rational promotion lattice for +, -, * (Rational
results reduced and denominator-one collapsed to Integer; Decimal
participation stays Decimal, including integral results; Rational
participation always wins).
"""
from __future__ import annotations

from src.genia.numeric_runtime import GeniaDecimal, GeniaRational, rational_from_integers


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


def _dec(coefficient: int, exponent: int) -> GeniaDecimal:
    return GeniaDecimal(coefficient, exponent)


def _rat(n: int, d: int):
    return rational_from_integers(n, d)


R_1_2 = _rat(1, 2)  # 1/2
R_1_3 = _rat(1, 3)  # 1/3


# ---------------------------------------------------------------------------
# Promotion table: Integer op Integer -> Integer
# ---------------------------------------------------------------------------


def test_integer_plus_integer_is_integer() -> None:
    result = 2 + 3
    assert type(result) is int and result == 5


# ---------------------------------------------------------------------------
# Integer/Decimal -> Decimal
# ---------------------------------------------------------------------------


def test_integer_plus_decimal_is_decimal() -> None:
    result = 1 + _dec(5, -1)  # 1 + 0.5
    assert isinstance(result, GeniaDecimal)
    assert result == _dec(15, -1)


def test_decimal_plus_decimal_stays_decimal_even_when_integral() -> None:
    result = _dec(5, -1) + _dec(5, -1)  # 0.5 + 0.5 = 1 (Decimal, not Integer)
    assert isinstance(result, GeniaDecimal)
    assert result.coefficient == 1 and result.exponent == 0


def test_decimal_minus_decimal() -> None:
    result = _dec(3, 0) - _dec(1, 0)
    assert isinstance(result, GeniaDecimal)
    assert result == _dec(2, 0)


def test_decimal_times_integer() -> None:
    result = _dec(15, -1) * 2  # 1.5 * 2 = 3
    assert isinstance(result, GeniaDecimal)
    assert result == _dec(3, 0)


def test_unary_negative_decimal() -> None:
    result = -_dec(15, -1)
    assert isinstance(result, GeniaDecimal)
    assert result.coefficient == -15 and result.exponent == -1


# ---------------------------------------------------------------------------
# Anything touching Rational -> Rational (or collapsed Integer)
# ---------------------------------------------------------------------------


def test_integer_plus_rational_is_rational() -> None:
    result = 1 + R_1_2  # 1 + 1/2 = 3/2
    assert isinstance(result, GeniaRational)
    assert (result.numerator, result.denominator) == (3, 2)


def test_rational_plus_integer_is_rational() -> None:
    result = R_1_2 + 1
    assert isinstance(result, GeniaRational)
    assert (result.numerator, result.denominator) == (3, 2)


def test_decimal_plus_rational_is_rational() -> None:
    result = _dec(5, -1) + R_1_2  # 0.5 + 1/2 = 1 -> collapses to Integer
    assert result == 1
    assert type(result) is int


def test_rational_minus_decimal_order_matters() -> None:
    result = R_1_2 - _dec(1, 0)  # 1/2 - 1 = -1/2
    assert isinstance(result, GeniaRational)
    assert (result.numerator, result.denominator) == (-1, 2)


def test_decimal_minus_rational_order_matters() -> None:
    result = _dec(1, 0) - R_1_2  # 1 - 1/2 = 1/2
    assert isinstance(result, GeniaRational)
    assert (result.numerator, result.denominator) == (1, 2)


def test_rational_plus_rational_reduces() -> None:
    result = R_1_2 + R_1_2  # 1/2 + 1/2 = 1 -> Integer
    assert result == 1
    assert type(result) is int


def test_rational_times_rational() -> None:
    result = R_1_2 * R_1_3  # 1/6
    assert isinstance(result, GeniaRational)
    assert (result.numerator, result.denominator) == (1, 6)


def test_rational_times_integer_collapses() -> None:
    result = R_1_2 * 2  # 1
    assert result == 1
    assert type(result) is int


def test_unary_negative_rational() -> None:
    result = -R_1_2
    assert isinstance(result, GeniaRational)
    assert (result.numerator, result.denominator) == (-1, 2)


def test_huge_arbitrary_precision_rational_arithmetic() -> None:
    huge = 10**60 + 1  # deliberately not a multiple of small primes
    a = _rat(huge, 2)
    b = _rat(huge, 3)
    result = a + b
    assert isinstance(result, GeniaRational)
    # a + b = huge*(1/2 + 1/3) = huge * 5/6
    assert result.numerator == huge * 5
    assert result.denominator == 6


# ---------------------------------------------------------------------------
# Through the evaluator
# ---------------------------------------------------------------------------


def test_genia_source_integer_decimal_rational_arithmetic() -> None:
    assert _run("1 + 2") == 3
    decimal_sum = _run("1.5 + 0.5")
    assert type(decimal_sum).__name__ == "GeniaDecimal"
    assert decimal_sum.coefficient == 2 and decimal_sum.exponent == 0

    rational_sum = _run("rational(1, 2) + rational(1, 3)")
    assert type(rational_sum).__name__ == "GeniaRational"
    assert rational_sum.numerator == 5 and rational_sum.denominator == 6

    collapsed = _run("rational(1, 2) + rational(1, 2)")
    assert collapsed == 1
    assert type(collapsed) is int

    mixed = _run("1 + rational(1, 2)")
    assert type(mixed).__name__ == "GeniaRational"
    assert mixed.numerator == 3 and mixed.denominator == 2

    negated = _run("-rational(1, 2)")
    assert type(negated).__name__ == "GeniaRational"
    assert negated.numerator == -1 and negated.denominator == 2
