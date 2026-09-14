"""Unit tests for retiring the decimal-literal Float64 bridge (issue #840).

Contract: docs/design/exact-numeric-model-contract.md section 3 (Decimal
semantic value: source Decimal parsing "must never pass through Float64")
and section 11 (tagged numeric Core IR).

Before this issue, decimal-classified source literals evaluated through
``genia.numeric_literals.materialize_legacy_numeric``, which constructed a
plain host ``float`` (``float(exact_decimal)``). This module proves that
ordinary decimal-classified source literals now materialize directly as the
runtime exact ``Decimal`` type from ``genia.numeric_values`` and never touch
a host binary float, while Integer literal materialization and unary sign
handling are unchanged.
"""

from __future__ import annotations

from genia.numeric_values import Decimal


class TestDecimalLiteralsAreExact:
    def test_dotted_decimal_literal_is_exact_decimal(self, run):
        result = run("1.5")
        assert isinstance(result, Decimal)
        assert not isinstance(result, float)
        assert result == Decimal(15, -1)

    def test_bare_exponent_decimal_literal_is_exact_decimal(self, run):
        result = run("1e3")
        assert isinstance(result, Decimal)
        assert result == Decimal(1, 3)

    def test_uppercase_signed_exponent_decimal_literal_is_exact_decimal(self, run):
        result = run("1E+3")
        assert isinstance(result, Decimal)
        assert result == Decimal(1, 3)

    def test_dotted_exponent_decimal_literal_is_exact_decimal(self, run):
        result = run("1.25e-2")
        assert isinstance(result, Decimal)
        assert result == Decimal(125, -4)

    def test_equivalent_decimal_spellings_are_canonically_equal(self, run):
        # 1.0, 1.00, and 100e-2 all canonicalize to the same Decimal value
        # (contract section 3) while remaining Decimal, not Integer.
        one = run("1.0")
        one_pad = run("1.00")
        one_exp = run("100e-2")
        assert isinstance(one, Decimal)
        assert isinstance(one_pad, Decimal)
        assert isinstance(one_exp, Decimal)
        assert one == one_pad == one_exp == Decimal(1, 0)

    def test_long_precision_literal_is_not_rounded_through_binary64(self, run):
        # A literal with more significant digits than binary64 can represent
        # exactly must retain every digit -- proof that no float ever sits
        # between the source token and the runtime Decimal.
        text = "1.00000000000000000000000000000012345"
        result = run(text)
        assert isinstance(result, Decimal)
        whole, frac = text.split(".")
        expected_coefficient = int(whole + frac)
        expected_exponent = -len(frac)
        assert result == Decimal(expected_coefficient, expected_exponent)

    def test_integer_literal_materialization_is_unchanged(self, run):
        assert run("42") == 42
        assert isinstance(run("42"), int)
        assert not isinstance(run("42"), Decimal)

    def test_unary_minus_over_decimal_literal_is_still_unary_lowering(self, run):
        # Contract section 2: a source sign is not part of the numeric token;
        # -1.25 is unary minus applied to the positive Decimal literal 1.25.
        result = run("-1.25")
        assert isinstance(result, Decimal)
        assert result == Decimal(-125, -2)

    def test_unary_minus_over_integer_literal_is_unchanged(self, run):
        result = run("-42")
        assert result == -42
        assert isinstance(result, int)

    def test_float64_conversion_of_a_decimal_literal_now_succeeds(self, run):
        # Contract section 5: float64(...) accepts an exact numeric value.
        # 1.5 is now exact Decimal input, so this must succeed rather than
        # raise NumericMisuseError as it did through the legacy float bridge.
        assert run("float64(1.5) == float64(1.5)") is True

    def test_decimal_literal_arithmetic_stays_exact_decimal(self, run):
        result = run("1.5 + 1.5")
        assert isinstance(result, Decimal)
        assert result == Decimal(3, 0)

    def test_decimal_literal_equality_is_mathematical(self, run):
        assert run("1.0 == 1.00") is True
        assert run("1 == 1.0") is True
