"""E23-1 (issue #911): canonical Integer/Decimal/Rational/Float64 rendering.

Covers docs/design/r23-numeric-representation-interchange-contract.md
sections 2-3: the canonical display/debug rendering atoms, and that the
REPL/CLI final-value echo path (and the generic `format_display`/
`format_debug` dispatch every other rendering surface funnels through) uses
these atoms rather than a host dataclass/object repr.

Out of scope here (later R23 slices, per issue #911): field-format-spec
integration, JSON encode/decode, compatibility JSON.
"""
from __future__ import annotations

from src.genia.numeric_runtime import GeniaDecimal, format_float64, rational_from_integers
from src.genia.utf8 import format_debug, format_display


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


# ---------------------------------------------------------------------------
# 2.1 Integer -- existing canonical rendering must be preserved
# ---------------------------------------------------------------------------


def test_integer_positive_display_and_debug():
    assert format_display(42) == "42"
    assert format_debug(42) == "42"


def test_integer_negative_display_and_debug():
    assert format_display(-7) == "-7"
    assert format_debug(-7) == "-7"


def test_integer_zero():
    assert format_display(0) == "0"
    assert format_debug(0) == "0"


def test_integer_large_magnitude_no_grouping_or_exponent():
    value = 10**30
    assert format_display(value) == str(value)
    assert "e" not in format_display(value)
    assert "," not in format_display(value)


# ---------------------------------------------------------------------------
# 2.2 Decimal -- fixed vs scientific, trailing zeros, .0 suffix
# ---------------------------------------------------------------------------


def test_decimal_simple_fixed_display():
    value = GeniaDecimal(15, -1)  # 1.5
    assert format_display(value) == "1.5"
    assert format_debug(value) == "1.5"


def test_decimal_integral_gets_dot_zero_suffix():
    # coefficient=5, exponent=2 -> 500, mathematically integral
    value = GeniaDecimal(5, 2)
    assert format_display(value) == "500.0"


def test_decimal_zero_is_dot_zero():
    value = GeniaDecimal(0, 0)
    assert format_display(value) == "0.0"


def test_decimal_negative():
    value = GeniaDecimal(-15, -1)  # -1.5
    assert format_display(value) == "-1.5"


def test_decimal_no_insignificant_trailing_fractional_zeros():
    # 1.50 written with excess coefficient trailing zero canonicalizes away
    value = GeniaDecimal(150, -2)  # 1.50 -> canonical coefficient 15, exp -1
    assert format_display(value) == "1.5"


def test_decimal_adjusted_exponent_exactly_minus_6_is_fixed():
    # digits="1", exponent=-6 -> adjusted_exponent = 1 + -6 - 1 = -6 (boundary, fixed)
    value = GeniaDecimal(1, -6)
    text = format_display(value)
    assert text == "0.000001"
    assert "e" not in text


def test_decimal_adjusted_exponent_one_below_minus_6_is_scientific():
    # digits="1", exponent=-7 -> adjusted_exponent = -7 (out of range, scientific)
    value = GeniaDecimal(1, -7)
    assert format_display(value) == "1.0e-7"


def test_decimal_adjusted_exponent_exactly_20_is_fixed():
    # digits="1", exponent=20 -> adjusted_exponent = 1 + 20 - 1 = 20 (boundary, fixed)
    value = GeniaDecimal(1, 20)
    text = format_display(value)
    assert text == "1" + "0" * 20 + ".0"
    assert "e" not in text


def test_decimal_adjusted_exponent_one_above_20_is_scientific():
    # digits="1", exponent=21 -> adjusted_exponent = 21 (out of range, scientific)
    value = GeniaDecimal(1, 21)
    assert format_display(value) == "1.0e+21"


def test_decimal_scientific_retains_dot_zero_for_single_significant_digit():
    value = GeniaDecimal(1, 21)
    assert format_display(value) == "1.0e+21"


def test_decimal_scientific_multi_digit_no_trailing_zero_noise():
    # coefficient=123, exponent=25 -> adjusted_exponent = 3 + 25 - 1 = 27
    value = GeniaDecimal(123, 25)
    assert format_display(value) == "1.23e+27"


def test_decimal_scientific_negative_exponent_sign():
    value = GeniaDecimal(123, -30)  # adjusted_exponent = 3 + -30 - 1 = -28
    text = format_display(value)
    assert text.startswith("1.23e-")
    assert "e-0" not in text  # no unnecessary leading zero in exponent


def test_decimal_display_equals_debug():
    value = GeniaDecimal(15, -1)
    assert format_display(value) == format_debug(value)
    zero = GeniaDecimal(0, 0)
    assert format_display(zero) == format_debug(zero)


def test_decimal_no_dataclass_repr_leakage():
    value = GeniaDecimal(15, -1)
    text = format_display(value)
    assert "GeniaDecimal" not in text
    assert "coefficient" not in text
    assert "exponent" not in text


# ---------------------------------------------------------------------------
# 2.3 Rational -- <numerator>/<denominator>, display == debug
# ---------------------------------------------------------------------------


def test_rational_positive_spelling():
    value = rational_from_integers(1, 3)
    assert format_display(value) == "1/3"
    assert format_debug(value) == "1/3"


def test_rational_negative_numerator_normalized():
    value = rational_from_integers(-1, 3)
    assert format_display(value) == "-1/3"


def test_rational_negative_denominator_normalized_sign_moves_to_numerator():
    value = rational_from_integers(1, -3)
    assert format_display(value) == "-1/3"


def test_rational_no_spaces():
    value = rational_from_integers(5, 7)
    text = format_display(value)
    assert " " not in text


def test_rational_display_equals_debug():
    value = rational_from_integers(2, 9)
    assert format_display(value) == format_debug(value)


def test_rational_no_dataclass_repr_leakage():
    value = rational_from_integers(2, 9)
    text = format_display(value)
    assert "GeniaRational" not in text
    assert "numerator" not in text
    assert "denominator" not in text


# ---------------------------------------------------------------------------
# 2.4 Float64 -- float64(<shortest-roundtrip-decimal>)
# ---------------------------------------------------------------------------


def test_float64_zero_point_one():
    assert format_float64(0.1) == "float64(0.1)"
    assert format_display(0.1) == "float64(0.1)"
    assert format_debug(0.1) == "float64(0.1)"


def test_float64_integral_value_retains_dot_zero():
    assert format_float64(100.0) == "float64(100.0)"


def test_float64_positive_zero():
    assert format_float64(0.0) == "float64(0.0)"


def test_float64_negative_zero():
    import math

    negative_zero = math.copysign(0.0, -1.0)
    assert format_float64(negative_zero) == "float64(-0.0)"


def test_float64_very_large_magnitude_scientific():
    text = format_float64(1e300)
    assert text.startswith("float64(1.0e+")
    assert text.endswith(")")


def test_float64_very_small_magnitude_scientific():
    text = format_float64(1e-300)
    assert text.startswith("float64(1.0e-")
    assert text.endswith(")")


def test_float64_shortest_roundtrip_not_full_binary_expansion():
    # 0.1 must NOT render as its exact 55-digit binary64 dyadic expansion
    # (that's the GeniaDecimal exact() conversion behavior, not Float64
    # canonical rendering).
    text = format_float64(0.1)
    assert text == "float64(0.1)"
    assert len(text) < 30


def test_float64_round_trips_to_identical_bits():
    import re

    for candidate in (0.1, 1.5, 2.0, 123456789.123456, 1e16, 1e-16, -3.25):
        text = format_float64(candidate)
        match = re.fullmatch(r"float64\((.+)\)", text)
        assert match is not None
        inner = match.group(1)
        parsed = float(inner)
        assert parsed == candidate

    # a negative float renders with the constructor-shaped atom, sign inside
    assert format_float64(-3.25).startswith("float64(-")


def test_float64_nan():
    assert format_float64(float("nan")) == "float64(nan)"


def test_float64_positive_infinity():
    assert format_float64(float("inf")) == "float64(inf)"


def test_float64_negative_infinity():
    assert format_float64(float("-inf")) == "float64(-inf)"


def test_float64_lowercase_e_and_explicit_sign():
    text = format_float64(1e300)
    assert "E" not in text
    assert "e+" in text or "e-" in text


def test_float64_display_equals_debug():
    assert format_display(0.1) == format_debug(0.1)
    assert format_display(float("nan")) == format_debug(float("nan"))


def test_float64_no_python_float_repr_leakage_for_nan_inf():
    # Python's own repr(float("nan")) == "nan" and repr(float("inf")) ==
    # "inf" with no constructor wrapper -- canonical rendering must wrap.
    assert format_display(float("nan")) != repr(float("nan"))
    assert format_display(float("inf")) != repr(float("inf"))


# ---------------------------------------------------------------------------
# REPL/CLI final-value echo uses the canonical renderer, not a Python
# fallback -- proven by running actual Genia source through the evaluator
# and rendering the result the same way _emit_result (interpreter.py) does.
# ---------------------------------------------------------------------------


def test_repl_echo_path_renders_canonical_decimal():
    result = _run("1.50")
    assert format_debug(result) == "1.5"


def test_repl_echo_path_renders_canonical_rational():
    result = _run("rational(1, 3)")
    assert format_debug(result) == "1/3"


def test_repl_echo_path_renders_canonical_float64():
    result = _run("float64(1)")
    assert format_debug(result) == "float64(1.0)"


def test_repl_echo_path_renders_canonical_integer():
    result = _run("42")
    assert format_debug(result) == "42"
