"""Unit tests for the explicit exact-numeric conversion builtins (issue #838
step 5): `rational(...)`, `float64(...)`, `exact(...)`.

Contract: docs/design/exact-numeric-model-contract.md sections 4 (Rational
constructor), 5 (Float64 explicit conversion), 6 (Float64 -> exact
conversion), and 17 (deterministic numeric misuse classes).

These tests exercise ``genia.numeric_values`` directly for the Decimal
shapes and NaN/infinity/overflow edge cases that are not reachable from
ordinary Genia source in this slice (decimal-literal materialization is
still on the pre-existing legacy float bridge; see
``numeric_values.py``'s module docstring and
``spec/eval/exact-numeric-conversion-builtins.yaml``'s notes). Source-
reachable behavior (Integer/Rational round-tripping through the builtins) is
covered by ``TestEvaluatorWiring`` below and by the shared spec case.
"""

from __future__ import annotations

import pytest

from genia.equality import genia_equal
from genia.numeric_values import (
    Decimal,
    Float64,
    NumericMisuseError,
    Rational,
    construct_exact,
    construct_float64,
    construct_rational,
    make_rational,
)


# ---------------------------------------------------------------------------
# rational(numerator, denominator) -- contract section 4
# ---------------------------------------------------------------------------


class TestRationalConstructor:
    def test_canonicalizes_like_make_rational(self):
        assert construct_rational(4, 6) == make_rational(4, 6)
        assert construct_rational(4, 6) == Rational(2, 3)

    def test_denominator_one_collapses_to_integer(self):
        assert construct_rational(6, 3) == 2
        assert isinstance(construct_rational(6, 3), int)

    def test_zero_denominator_is_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_rational(1, 0)

    def test_non_integer_arguments_are_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_rational(1.5, 2)
        with pytest.raises(NumericMisuseError):
            construct_rational(1, 2.5)
        with pytest.raises(NumericMisuseError):
            construct_rational(Decimal(1, 0), 2)

    def test_boolean_arguments_are_numeric_misuse(self):
        # Booleans are not numbers (contract section 10), so they are not
        # Integers either, even though Python's bool is an int subclass.
        with pytest.raises(NumericMisuseError):
            construct_rational(True, 2)
        with pytest.raises(NumericMisuseError):
            construct_rational(1, False)


# ---------------------------------------------------------------------------
# float64(value) -- contract section 5
# ---------------------------------------------------------------------------


class TestFloat64Constructor:
    def test_existing_float64_is_returned_unchanged(self):
        value = Float64(3.5)
        assert construct_float64(value) is value

    def test_integer_converts_exactly(self):
        result = construct_float64(3)
        assert isinstance(result, Float64)
        assert result.value == 3.0

    def test_rational_converts_with_correct_rounding(self):
        result = construct_float64(Rational(1, 4))
        assert result == Float64(0.25)

    def test_decimal_converts_exactly(self):
        result = construct_float64(Decimal(1, -1))  # 0.1
        assert result == Float64(0.1)

    def test_exact_zero_converts_to_positive_zero(self):
        import math

        result = construct_float64(0)
        assert result.value == 0.0
        assert math.copysign(1.0, result.value) == 1.0

    def test_overflow_is_numeric_misuse_not_infinity(self):
        huge = Decimal(10**400, 0)
        with pytest.raises(NumericMisuseError):
            construct_float64(huge)

    def test_non_numeric_input_is_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_float64("1.0")

    def test_boolean_input_is_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_float64(True)

    def test_existing_nan_and_infinity_pass_through_unchanged(self):
        # No public spelling constructs these (contract section 5), but an
        # already-approved host boundary may hand one to float64(); it must
        # be returned unchanged rather than re-validated/rejected.
        nan = Float64(float("nan"))
        inf = Float64(float("inf"))
        neg_inf = Float64(float("-inf"))
        assert construct_float64(nan) is nan
        assert construct_float64(inf) is inf
        assert construct_float64(neg_inf) is neg_inf


# ---------------------------------------------------------------------------
# exact(value) -- contract section 6
# ---------------------------------------------------------------------------


class TestExactConstructor:
    def test_exact_family_values_are_unchanged(self):
        assert construct_exact(3) == 3
        assert construct_exact(Decimal(15, -1)) == Decimal(15, -1)
        assert construct_exact(Rational(1, 3)) == Rational(1, 3)

    def test_finite_float64_returns_exact_dyadic_decimal(self):
        # The worked example from contract section 6: exact(float64(0.1))
        # must denote the exact binary64-represented value, not the shortest
        # round-trip decimal "0.1".
        result = construct_exact(Float64(0.1))
        assert isinstance(result, Decimal)
        assert result.coefficient == 1000000000000000055511151231257827021181583404541015625
        assert result.exponent == -55
        assert str(result.to_py_decimal()).startswith("0.1000000000000000055511151231")
        # And it must NOT be the naive shortest-decimal value.
        assert result != Decimal(1, -1)

    def test_finite_integral_float64_stays_decimal_not_integer(self):
        # Decimal kind is retained even for a mathematically integral value
        # (contract section 3) -- exact(float64(2)) is Decimal 2, not
        # Integer 2, even though it compares equal to Integer 2.
        result = construct_exact(Float64(2.0))
        assert isinstance(result, Decimal)
        assert result.coefficient == 2
        assert result.exponent == 0
        assert genia_equal(result, 2)

    def test_signed_zero_converts_to_decimal_zero_both_signs(self):
        import math

        positive = construct_exact(Float64(0.0))
        negative = construct_exact(Float64(-0.0))
        assert math.copysign(1.0, 0.0) == 1.0  # sanity: +0.0 is the "positive" bit pattern
        assert positive == Decimal(0, 0)
        assert negative == Decimal(0, 0)
        # Decimal has no negative-zero identity (contract section 3).
        assert positive == negative

    def test_nan_is_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_exact(Float64(float("nan")))

    def test_positive_infinity_is_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_exact(Float64(float("inf")))

    def test_negative_infinity_is_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_exact(Float64(float("-inf")))

    def test_non_numeric_input_is_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_exact("0.1")
        with pytest.raises(NumericMisuseError):
            construct_exact(None)

    def test_boolean_input_is_numeric_misuse(self):
        with pytest.raises(NumericMisuseError):
            construct_exact(True)


# ---------------------------------------------------------------------------
# Evaluator wiring -- builtins reachable from ordinary Genia source
# ---------------------------------------------------------------------------


class TestEvaluatorWiring:
    def test_rational_builtin_from_source(self, run):
        assert run("rational(4, 6) == (2 / 3)") is True
        assert run("rational(6, 3)") == 2

    def test_float64_builtin_from_source(self, run):
        assert run("float64(3) == 3") is True
        assert run("float64(3) == float64(3)") is True
        assert run("float64(1) < float64(2)") is True

    def test_exact_builtin_from_source(self, run):
        assert run("exact(3) == 3") is True
        assert run("exact(rational(1, 2)) == (1 / 2)") is True

    def test_float64_rejects_the_legacy_decimal_literal_bridge(self, run):
        # Decimal-classified source literals still materialize through the
        # temporary legacy float bridge (plain host float), which is neither
        # an exact numeric value nor an explicit Float64 per contract
        # section 5 -- float64(...) must not silently accept it.
        with pytest.raises(NumericMisuseError):
            run("float64(0.1)")

    def test_exact_rejects_the_legacy_decimal_literal_bridge(self, run):
        with pytest.raises(NumericMisuseError):
            run("exact(0.1)")

    def test_boolean_operand_is_numeric_misuse_from_source(self, run):
        with pytest.raises(NumericMisuseError):
            run("float64(true)")
        with pytest.raises(NumericMisuseError):
            run("exact(false)")
        with pytest.raises(NumericMisuseError):
            run("rational(true, 2)")

    def test_zero_denominator_is_numeric_misuse_from_source(self, run):
        with pytest.raises(NumericMisuseError):
            run("rational(1, 0)")
