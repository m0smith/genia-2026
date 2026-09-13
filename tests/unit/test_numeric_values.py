"""Unit tests for the exact numeric runtime value model (issue #838 slice 2).

Covers docs/design/exact-numeric-model-contract.md sections 3 (Decimal), 4
(Rational), 5 (Float64), and 10 (booleans are not numbers). Arithmetic,
cross-kind equality, rendering, JSON, and conversion builtins are explicitly
out of scope for this slice; see src/genia/numeric_values.py's module
docstring.
"""

import math

import pytest

from genia.numeric_values import (
    Decimal,
    Float64,
    Rational,
    is_exact_numeric_value,
    is_numeric_value,
    make_rational,
    materialize_exact_numeric,
)
from genia.numeric_literals import NumericLiteral


class TestDecimalCanonicalization:
    def test_zero_canonicalizes_to_zero_zero(self):
        assert Decimal(0, 5) == Decimal(0, 0)
        assert Decimal(0, -7) == Decimal.of(0, 0)

    def test_trailing_zero_stripping(self):
        # 1.0 -> coefficient 1, exponent 0
        assert Decimal.from_payload("1", "0") == Decimal(1, 0)
        # 1.00 -> coefficient 1, exponent 0 (same as 1.0)
        assert Decimal.from_payload("100", "-2") == Decimal(1, 0)
        # 100e-2 -> coefficient 1, exponent 0 (same value again)
        assert Decimal.from_payload("100", "-2") == Decimal.from_payload("1", "0")

    def test_123_4500_example(self):
        # 123.4500 -> coefficient 12345, exponent -2
        assert Decimal.from_payload("1234500", "-4") == Decimal(12345, -2)

    def test_sign_carried_by_coefficient(self):
        assert Decimal(-100, -2) == Decimal(-1, 0)

    def test_kind_distinct_from_integer_even_when_integral(self):
        # Decimal(1, 0) denotes the same mathematical value as Integer 1
        # but remains a distinct runtime kind (contract section 3).
        d = Decimal(1, 0)
        assert d != 1
        assert not isinstance(d, int)
        assert d.is_integral()

    def test_rejects_bool_fields(self):
        with pytest.raises(TypeError):
            Decimal(True, 0)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            Decimal(1, True)  # type: ignore[arg-type]

    def test_hashable_and_equal_values_hash_equal(self):
        a = Decimal.from_payload("100", "-2")
        b = Decimal.from_payload("1", "0")
        assert a == b
        assert hash(a) == hash(b)


class TestRationalCanonicalization:
    @pytest.mark.parametrize(
        "numerator, denominator, expected_numerator, expected_denominator",
        [
            (2, 6, 1, 3),
            (-2, 6, -1, 3),
            (2, -6, -1, 3),
            (-2, -6, 1, 3),
        ],
    )
    def test_reduction_examples(
        self, numerator, denominator, expected_numerator, expected_denominator
    ):
        value = make_rational(numerator, denominator)
        assert isinstance(value, Rational)
        assert value.numerator == expected_numerator
        assert value.denominator == expected_denominator

    def test_denominator_one_collapses_to_integer(self):
        value = make_rational(6, 3)
        assert value == 2
        assert isinstance(value, int)
        assert not isinstance(value, Rational)

    def test_denominator_always_positive(self):
        value = make_rational(1, -1)
        assert value == -1

    def test_zero_denominator_rejected(self):
        with pytest.raises(ValueError):
            Rational(1, 0)

    def test_rejects_bool_fields(self):
        with pytest.raises(TypeError):
            Rational(True, 2)  # type: ignore[arg-type]

    def test_hashable_and_equal_values_hash_equal(self):
        a = Rational(2, 6)
        b = Rational(-2, -6)
        assert a == b
        assert hash(a) == hash(b)


class TestFloat64:
    def test_wraps_host_float(self):
        assert Float64(1.5).value == 1.5

    def test_rejects_non_float(self):
        with pytest.raises(TypeError):
            Float64(1)  # type: ignore[arg-type]

    def test_is_nan(self):
        assert Float64(float("nan")).is_nan()
        assert not Float64(1.0).is_nan()

    def test_bits_hex_distinguishes_signed_zero(self):
        positive_zero = Float64(0.0).bits_hex()
        negative_zero = Float64(-0.0).bits_hex()
        assert positive_zero != negative_zero
        assert positive_zero == "0000000000000000"
        assert negative_zero == "8000000000000000"

    def test_equality_is_by_bits_not_by_exact_math_value(self):
        # Float64 equality here is plain dataclass field equality; a finite
        # Float64 vs. an exact numeric value's mathematical-value bridge
        # (contract section 10.2) is explicitly out of scope for this slice.
        assert Float64(1.0) == Float64(1.0)
        assert Float64(1.0) != Float64(2.0)


class TestBooleansAreNotNumbers:
    def test_bool_excluded_from_is_numeric_value(self):
        assert is_numeric_value(True) is False
        assert is_numeric_value(False) is False

    def test_bool_excluded_from_is_exact_numeric_value(self):
        assert is_exact_numeric_value(True) is False

    def test_plain_int_and_new_kinds_are_numeric(self):
        assert is_numeric_value(1) is True
        assert is_numeric_value(Decimal(1, 0)) is True
        assert is_numeric_value(Rational(1, 3)) is True
        assert is_numeric_value(Float64(1.0)) is True

    def test_non_numbers_excluded(self):
        assert is_numeric_value("1") is False
        assert is_numeric_value(None) is False
        assert is_exact_numeric_value(Float64(1.0)) is False


class TestMaterializeExactNumeric:
    def test_integer_payload(self):
        assert materialize_exact_numeric({"kind": "integer", "digits": "123"}) == 123

    def test_decimal_payload(self):
        value = materialize_exact_numeric(
            {"kind": "decimal", "coefficient": "12345", "exponent": "-2"}
        )
        assert value == Decimal(12345, -2)

    def test_numeric_literal_descriptor(self):
        literal = NumericLiteral("integer", digits="42")
        assert materialize_exact_numeric(literal) == 42

    def test_rejects_non_payload(self):
        with pytest.raises(ValueError):
            materialize_exact_numeric(math.pi)
