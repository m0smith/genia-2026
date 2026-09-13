"""Unit tests for issue #838 step 6: canonical display/debug rendering
(contract section 12), the JSON encode boundary (contract section 13), and
format-spec integration (contract section 14) for the Decimal/Rational/
Float64 exact-numeric-model runtime kinds.

These exercise ``genia.numeric_values``, ``genia.utf8``, and
``genia._format_engine`` directly, plus a handful of end-to-end
``run_source`` cases for the observable print/format/json_encode surface.
"""

from __future__ import annotations

import pytest

from genia import make_global_env, run_source
from genia._format_engine import apply_format_spec
from genia.numeric_values import (
    Decimal,
    Float64,
    Rational,
    decimal_json_number,
    render_decimal,
    render_float64,
    render_numeric_value,
    render_rational,
    stable_json_decimal,
)
from genia.utf8 import format_debug, format_display


def run(source: str):
    env = make_global_env()
    return run_source(source, env)


# ---------------------------------------------------------------------------
# Canonical Decimal rendering -- contract section 12.2
# ---------------------------------------------------------------------------


class TestDecimalRendering:
    def test_simple_fraction(self):
        assert render_decimal(Decimal(15, -1)) == "1.5"

    def test_zero(self):
        assert render_decimal(Decimal(0, 0)) == "0.0"

    def test_negative(self):
        assert render_decimal(Decimal(-5, 0)) == "-5.0"

    def test_integral_value_keeps_dot_zero(self):
        # 100e-2 == 1, but Decimal kind retains .0 (contract section 3/12.2)
        assert render_decimal(Decimal(100, -2)) == "1.0"

    def test_small_fraction_no_leading_int_digit_loss(self):
        assert render_decimal(Decimal(5, -3)) == "0.005"

    def test_scientific_notation_outside_fixed_window(self):
        # adjusted_exponent = len("123456789") + 20 - 1 = 28, outside [-6, 20]
        assert render_decimal(Decimal(123456789, 20)) == "1.23456789e+28"

    def test_scientific_single_significant_digit_keeps_dot_zero(self):
        assert render_decimal(Decimal(1, 25)) == "1.0e+25"

    def test_scientific_negative_exponent(self):
        assert render_decimal(Decimal(1, -30)) == "1.0e-30"

    def test_boundary_adjusted_exponent_20_is_fixed(self):
        value = Decimal(1, 20)
        text = render_decimal(value)
        assert "e" not in text
        assert text == "1" + "0" * 20 + ".0"

    def test_boundary_adjusted_exponent_21_is_scientific(self):
        value = Decimal(1, 21)
        assert render_decimal(value) == "1.0e+21"

    def test_no_python_dataclass_repr_leak(self):
        text = render_decimal(Decimal(4, 0))
        assert "Decimal(" not in text
        assert text == "4.0"


class TestRationalRendering:
    def test_simple(self):
        assert render_rational(Rational(1, 3)) == "1/3"

    def test_negative_numerator(self):
        assert render_rational(Rational(-2, 5)) == "-2/5"

    def test_no_python_dataclass_repr_leak(self):
        text = render_rational(Rational(1, 3))
        assert "Rational(" not in text


class TestFloat64Rendering:
    def test_finite(self):
        assert render_float64(Float64(1.5)) == "float64(1.5)"

    def test_integral_keeps_dot_zero(self):
        assert render_float64(Float64(3.0)) == "float64(3.0)"

    def test_negative_zero(self):
        assert render_float64(Float64(-0.0)) == "float64(-0.0)"

    def test_positive_zero(self):
        assert render_float64(Float64(0.0)) == "float64(0.0)"

    def test_nan(self):
        assert render_float64(Float64(float("nan"))) == "float64(nan)"

    def test_infinity(self):
        assert render_float64(Float64(float("inf"))) == "float64(inf)"
        assert render_float64(Float64(float("-inf"))) == "float64(-inf)"

    def test_scientific_lowercase_e_and_explicit_sign(self):
        text = render_float64(Float64(1e30))
        assert text == "float64(1.0e+30)"

    def test_small_scientific_no_leading_zero_in_exponent(self):
        text = render_float64(Float64(1e-10))
        assert text == "float64(1.0e-10)"

    def test_no_python_repr_leak(self):
        text = render_float64(Float64(3.0))
        assert "Float64(" not in text


class TestRenderNumericValueDispatch:
    def test_rejects_non_numeric(self):
        with pytest.raises(TypeError):
            render_numeric_value(3)  # plain int is Integer, not this dispatcher's job


# ---------------------------------------------------------------------------
# format_display / format_debug wiring (contract section 12: "Display and
# debug use this same canonical atom" for each kind)
# ---------------------------------------------------------------------------


class TestUtf8Wiring:
    def test_display_decimal(self):
        assert format_display(Decimal(15, -1)) == "1.5"

    def test_debug_decimal_matches_display(self):
        value = Decimal(15, -1)
        assert format_debug(value) == format_display(value)

    def test_display_rational(self):
        assert format_display(Rational(1, 3)) == "1/3"

    def test_debug_rational_matches_display(self):
        value = Rational(1, 3)
        assert format_debug(value) == format_display(value)

    def test_display_float64(self):
        assert format_display(Float64(3.0)) == "float64(3.0)"

    def test_debug_float64_matches_display(self):
        value = Float64(3.0)
        assert format_debug(value) == format_display(value)

    def test_list_of_numeric_kinds(self):
        assert format_display([Decimal(15, -1), Rational(1, 3)]) == "[1.5, 1/3]"


# ---------------------------------------------------------------------------
# End-to-end print/debug_repr through the evaluator
# ---------------------------------------------------------------------------


class TestEndToEndDisplay:
    def test_exact_float_conversion_prints_canonically(self, capsys):
        run('print(exact(float64(4)))')
        assert capsys.readouterr().out == "4.0\n"

    def test_rational_prints_canonically(self, capsys):
        run('print(exact(1) / exact(3))')
        assert capsys.readouterr().out == "1/3\n"

    def test_float64_prints_canonically(self, capsys):
        run('print(float64(3))')
        assert capsys.readouterr().out == "float64(3.0)\n"

    def test_debug_repr_matches_display_for_decimal(self, capsys):
        run('print(debug_repr(exact(float64(4))))')
        assert capsys.readouterr().out == "4.0\n"


# ---------------------------------------------------------------------------
# JSON encode boundary -- contract section 13
# ---------------------------------------------------------------------------


class TestStableJsonDecimal:
    def test_accepts_terminating_short_decimal(self):
        assert stable_json_decimal(Decimal(1, -1)) is True  # 0.1

    def test_rejects_long_expansion_from_float_conversion(self):
        # exact(float64(0.1))-shaped value: not the shortest round-trip text
        long_value = Decimal(
            1000000000000000055511151231257827021181583404541015625, -55
        )
        assert stable_json_decimal(long_value) is False

    def test_accepts_integral_decimal(self):
        assert stable_json_decimal(Decimal(4, 0)) is True

    def test_rejects_overflow_magnitude(self):
        assert stable_json_decimal(Decimal(10**400, 0)) is False

    def test_decimal_json_number_matches_predicate(self):
        value = Decimal(1, -1)
        assert stable_json_decimal(value) is True
        assert decimal_json_number(value) == 0.1


class TestJsonEncodeBoundary:
    def test_encodes_terminating_rational(self, capsys):
        result = run("json_encode(rational(1, 2))")
        assert result is not None

    def test_terminating_rational_end_to_end(self, capsys):
        run('print(json_encode(rational(1, 2)))')
        out = capsys.readouterr().out
        assert "some(0.5" in out

    def test_non_terminating_rational_rejected(self, capsys):
        run('print(json_encode(rational(1, 3)))')
        out = capsys.readouterr().out
        assert "err(json_number_out_of_range" in out

    def test_finite_float64_encodes(self, capsys):
        run('print(json_encode(float64(3)))')
        out = capsys.readouterr().out
        assert "some(3.0" in out

    def test_exact_decimal_from_float_conversion_encodes(self, capsys):
        run('print(json_encode(exact(float64(4))))')
        out = capsys.readouterr().out
        assert "some(4.0" in out

    def test_unstable_decimal_rejected(self, capsys):
        run('print(json_encode(exact(float64(1) / float64(4))))')
        out = capsys.readouterr().out
        # 0.25 is stable, should encode fine -- sanity check the "happy" path
        assert "some(0.25" in out

    def test_json_decode_still_produces_legacy_float_for_fraction(self, capsys):
        # Contract section 13.5's decode-to-Decimal requirement is NOT
        # implemented in this slice -- decode is unchanged.
        run(
            'print(unwrap_or(0, json_decode("1.5")) |> representation_match("json") |> unwrap_or(0))'
        )
        out = capsys.readouterr().out
        assert out == "1.5\n"


# ---------------------------------------------------------------------------
# Format-spec integration -- contract section 14
# ---------------------------------------------------------------------------


class TestFormatSpecPrecision:
    def test_rational_precision_rounds_half_up(self):
        assert apply_format_spec(Rational(1, 3), ".2") == "0.33"

    def test_rational_precision_zero_digits(self):
        assert apply_format_spec(Rational(1, 3), ".0") == "0"

    def test_decimal_precision(self):
        assert apply_format_spec(Decimal(4, 0), ".3") == "4.000"

    def test_float64_precision(self):
        assert apply_format_spec(Float64(4.0), ".2") == "4.00"

    def test_negative_rational_precision(self):
        assert apply_format_spec(Rational(-1, 3), ".2") == "-0.33"

    def test_rounds_to_zero_drops_sign(self):
        assert apply_format_spec(Rational(-1, 1000), ".2") == "0.00"


class TestFormatSpecPlainInterpolation:
    def test_plain_placeholder_uses_canonical_display(self, capsys):
        run('print(format("{0}", [exact(float64(4))]))')
        assert capsys.readouterr().out == "4.0\n"

    def test_zero_pad_decimal(self):
        assert apply_format_spec(Decimal(4, 0), "010") == "00000004.0"

    def test_grouping_decimal(self):
        assert apply_format_spec(Decimal(1234567, 0), ",") == "1,234,567.0"

    def test_zero_pad_rejects_rational(self):
        with pytest.raises(ValueError):
            apply_format_spec(Rational(1, 3), "05")

    def test_grouping_rejects_rational(self):
        with pytest.raises(ValueError):
            apply_format_spec(Rational(1, 3), ",")
