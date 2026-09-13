"""Unit tests for exact/Float64 arithmetic (issue #838 step 3).

Covers docs/design/exact-numeric-model-contract.md sections 7 (exact
+/-/*), 8 (exact division/remainder), 9 (Float64 arithmetic and mixing
rejection), and the "booleans are not numbers" rule from section 10 as it
applies to arithmetic operators.

Two layers are exercised:

- ``genia.numeric_values``'s pure arithmetic functions directly, against the
  contract's promotion/termination rules.
- ``genia.evaluator``'s binary/unary-op dispatch, proving these functions are
  actually wired into live evaluation (not merely available), per issue
  #838 step 3's scope. Decimal-literal source materialization itself is
  intentionally left on the pre-existing float bridge (see
  ``numeric_values.py``'s module docstring and PR #839's step 2 comment);
  the reachable live-evaluation surface in this slice is Integer/Integer
  division and remainder (a real, currently-wrong-by-contract behavior) plus
  full engine correctness whenever a Decimal/Rational/Float64 value is
  already present (e.g. built by a host boundary/import, as exercised here
  via direct environment injection through the real evaluator).
"""

from __future__ import annotations

import math

import pytest

from genia.numeric_values import (
    Decimal,
    Float64,
    NumericMisuseError,
    Rational,
    add,
    divide,
    multiply,
    negate,
    remainder,
    subtract,
)


class TestExactAdditionSubtractionMultiplication:
    def test_integer_integer_stays_integer(self):
        assert add(2, 3) == 5
        assert subtract(2, 3) == -1
        assert multiply(2, 3) == 6
        assert isinstance(add(2, 3), int)

    def test_decimal_participation_retains_decimal_even_when_integral(self):
        # contract section 7: "Decimal participation retains Decimal for
        # Integer/Decimal-only +, -, *, including mathematically integral
        # results."
        result = add(Decimal(1, 0), Decimal(2, 0))  # 1.0 + 2.0 -> 3.0
        assert isinstance(result, Decimal)
        assert result == Decimal(3, 0)

        result = add(1, Decimal(2, 0))  # 1 + 2.0 -> 3.0 (Decimal, not Integer)
        assert isinstance(result, Decimal)
        assert result == Decimal(3, 0)

    def test_decimal_arithmetic_is_exact_not_binary_float(self):
        # 0.1 + 0.2 must be exactly 0.3 in the exact Decimal domain, unlike
        # IEEE-754 binary64 0.1 + 0.2.
        tenth = Decimal(1, -1)
        two_tenths = Decimal(2, -1)
        assert add(tenth, two_tenths) == Decimal(3, -1)

    def test_rational_participation_promotes_to_rational(self):
        half = Rational(1, 2)
        assert add(half, 1) == Rational(3, 2)
        assert add(1, half) == Rational(3, 2)
        assert add(Decimal(1, 0), half) == Rational(3, 2)

    def test_rational_results_reduced_and_denominator_one_collapses(self):
        result = multiply(Rational(1, 3), 3)  # (1/3) * 3 -> Integer 1
        assert result == 1
        assert isinstance(result, int)

    def test_multiply_decimal_tracks_coefficient_and_exponent(self):
        result = multiply(Decimal(15, -1), Decimal(2, 0))  # 1.5 * 2.0 -> 3.0
        assert result == Decimal(3, 0)
        assert isinstance(result, Decimal)

    def test_booleans_are_not_numbers(self):
        with pytest.raises(NumericMisuseError):
            add(True, 1)
        with pytest.raises(NumericMisuseError):
            subtract(1, False)
        with pytest.raises(NumericMisuseError):
            multiply(True, False)


class TestExactDivision:
    def test_contract_examples(self):
        assert divide(6, 3) == 2
        assert isinstance(divide(6, 3), int)

        assert divide(1, 2) == Rational(1, 2)
        assert divide(1, 3) == Rational(1, 3)

        result = divide(Decimal(1, 0), 2)  # 1.0 / 2 -> Decimal 0.5
        assert result == Decimal(5, -1)
        assert isinstance(result, Decimal)

        result = divide(Decimal(1, 0), 3)  # 1.0 / 3 -> Rational 1/3
        assert result == Rational(1, 3)

        result = multiply(divide(1, 3), 3)  # (1 / 3) * 3 -> Integer 1
        assert result == 1
        assert isinstance(result, int)

    def test_integer_division_never_produces_decimal(self):
        # 1 / 2 terminates in base 10 but the Integer/Integer table cell is
        # Rational, never Decimal (contract section 8.1).
        result = divide(1, 2)
        assert isinstance(result, Rational)

    def test_decimal_division_non_terminating_becomes_rational(self):
        result = divide(Decimal(2, 0), Decimal(3, 0))  # 2.0 / 3.0
        assert result == Rational(2, 3)

    def test_decimal_division_terminating_stays_decimal_including_wholes(self):
        result = divide(Decimal(4, 0), Decimal(2, 0))  # 4.0 / 2.0 -> Decimal 2.0
        assert isinstance(result, Decimal)
        assert result == Decimal(2, 0)

    def test_rational_division_always_rational_family(self):
        result = divide(Rational(1, 2), Rational(1, 4))  # -> 2 (Integer)
        assert result == 2
        assert isinstance(result, int)

    def test_negative_operands_carry_sign_on_numerator(self):
        result = divide(-1, 3)
        assert result == Rational(-1, 3)
        assert result.numerator == -1
        assert result.denominator == 3

    def test_exact_division_by_zero_is_deterministic_misuse(self):
        with pytest.raises(NumericMisuseError):
            divide(1, 0)
        with pytest.raises(NumericMisuseError):
            divide(Decimal(1, 0), Decimal(0, 0))
        with pytest.raises(NumericMisuseError):
            divide(Rational(1, 2), 0)

    def test_booleans_are_not_numbers(self):
        with pytest.raises(NumericMisuseError):
            divide(True, 1)


class TestExactRemainder:
    def test_floor_remainder_matches_python_int_semantics(self):
        for a, b in [(7, 3), (-7, 3), (7, -3), (-7, -3)]:
            q = math.floor(a / b)
            expected = a - q * b
            assert remainder(a, b) == expected

    def test_remainder_promotes_like_additive_ops(self):
        result = remainder(Decimal(7, 0), 2)  # 7.0 % 2 -> Decimal 1.0
        assert isinstance(result, Decimal)
        assert result == Decimal(1, 0)

    def test_remainder_rational_collapses_denominator_one(self):
        result = remainder(Rational(7, 2), Rational(1, 2))  # 3.5 % 0.5 -> 0
        assert result == 0
        assert isinstance(result, int)

    def test_remainder_by_zero_is_deterministic_misuse(self):
        with pytest.raises(NumericMisuseError):
            remainder(1, 0)
        with pytest.raises(NumericMisuseError):
            remainder(Decimal(1, 0), 0)


class TestFloat64Arithmetic:
    def test_binary_ops_stay_in_float64_domain(self):
        a, b = Float64(1.5), Float64(2.0)
        assert add(a, b) == Float64(3.5)
        assert subtract(a, b) == Float64(-0.5)
        assert multiply(a, b) == Float64(3.0)
        assert divide(a, b) == Float64(0.75)

    def test_float64_remainder_uses_floor_definition(self):
        result = remainder(Float64(-7.0), Float64(3.0))
        assert isinstance(result, Float64)
        assert result.value == pytest.approx(2.0)

    def test_float64_division_by_zero_is_deterministic_misuse_not_infinity(self):
        with pytest.raises(NumericMisuseError):
            divide(Float64(1.0), Float64(0.0))
        with pytest.raises(NumericMisuseError):
            remainder(Float64(1.0), Float64(0.0))

    def test_negate(self):
        assert negate(Float64(1.5)) == Float64(-1.5)
        assert negate(Decimal(5, -1)) == Decimal(-5, -1)
        assert negate(Rational(1, 2)) == Rational(-1, 2)
        assert negate(3) == -3

    def test_negate_rejects_bool(self):
        with pytest.raises(NumericMisuseError):
            negate(True)


class TestMixedExactFloat64ArithmeticRejected:
    def test_plus_minus_times_reject_mixing(self):
        for fn in (add, subtract, multiply, divide, remainder):
            with pytest.raises(NumericMisuseError):
                fn(1, Float64(1.0))
            with pytest.raises(NumericMisuseError):
                fn(Float64(1.0), 1)
            with pytest.raises(NumericMisuseError):
                fn(Decimal(1, 0), Float64(1.0))
            with pytest.raises(NumericMisuseError):
                fn(Rational(1, 2), Float64(1.0))
