"""Failing tests for issue #915 (E23-3): strict generic JSON boundary for
Integer and Decimal.

Implements docs/design/r23-numeric-representation-interchange-contract.md
sections 4.1 (Integer), 4.2 (`stable_json_decimal`), 5 (decode, Integer/
Decimal only), and 8 (diagnostics, this slice only) against the strict
generic JSON boundary (`json_decode`/`json_encode`, i.e. `_json_decode`/
`_json_encode` in `src/genia/builtins.py`) -- never the compatibility
`json_parse`/`json_stringify` surface, which is untouched (E23-5).

Out of scope here (later R23 slices): Rational/Float64 JSON policy
(E23-4); compatibility JSON reconciliation (E23-5); a full diagnostics
sweep (E23-6); release audit (E23-7).
"""
from __future__ import annotations

import pytest

from src.genia import make_global_env, run_source
from src.genia.builtins import _JSON_SAFE_INTEGER
from src.genia.numeric_runtime import GeniaDecimal, stable_json_decimal
from src.genia.utf8 import format_debug
from src.genia.values import GeniaOptionErr, GeniaOptionSome


def _env():
    return make_global_env([])


def _run(src: str):
    return run_source(src, make_global_env())


def _decode(text_or_bytes):
    return _env().get("_json_decode")(text_or_bytes)


def _encode(value):
    return _env().get("_json_encode")(value)


# ---------------------------------------------------------------------------
# section 4.1 / 5: Integer at exactly the R9 safe-integer boundary
# ---------------------------------------------------------------------------


def test_json_safe_integer_constant_matches_r9_bound():
    assert _JSON_SAFE_INTEGER == 9_007_199_254_740_991


def test_decode_integer_in_range_low_boundary():
    result = _decode(str(-_JSON_SAFE_INTEGER))
    assert isinstance(result, GeniaOptionSome)
    assert result.value.value == -_JSON_SAFE_INTEGER


def test_decode_integer_in_range_high_boundary():
    result = _decode(str(_JSON_SAFE_INTEGER))
    assert isinstance(result, GeniaOptionSome)
    assert result.value.value == _JSON_SAFE_INTEGER


def test_decode_integer_one_over_high_boundary_rejected_with_normalized_diagnostic():
    result = _decode(str(_JSON_SAFE_INTEGER + 1))
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_decode_integer_one_under_low_boundary_rejected_with_normalized_diagnostic():
    result = _decode(str(-_JSON_SAFE_INTEGER - 1))
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_encode_integer_in_range_round_trips():
    result = _encode(_JSON_SAFE_INTEGER)
    assert isinstance(result, GeniaOptionSome)
    assert result.value == str(_JSON_SAFE_INTEGER)


def test_encode_integer_one_over_high_boundary_rejected_with_normalized_diagnostic():
    result = _encode(_JSON_SAFE_INTEGER + 1)
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_encode_integer_one_under_low_boundary_rejected_with_normalized_diagnostic():
    result = _encode(-_JSON_SAFE_INTEGER - 1)
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_decode_integer_form_token_produces_integer_not_decimal():
    result = _decode("42")
    assert isinstance(result, GeniaOptionSome)
    assert result.value.value == 42
    assert isinstance(result.value.value, int)
    assert not isinstance(result.value.value, GeniaDecimal)


# ---------------------------------------------------------------------------
# section 4.2: stable_json_decimal unit-level tests
# ---------------------------------------------------------------------------


def test_stable_json_decimal_rejects_non_decimal():
    with pytest.raises(TypeError):
        stable_json_decimal(5)


@pytest.mark.parametrize(
    "coefficient,exponent",
    [
        (1, -1),  # 0.1
        (5, -1),  # 0.5
        (10, -1),  # 1.0
        (1000, -1),  # 100.0
        (0, 0),  # 0
        (25, -1),  # 2.5
    ],
)
def test_stable_json_decimal_true_for_stable_values(coefficient, exponent):
    assert stable_json_decimal(GeniaDecimal(coefficient, exponent)) is True


def test_stable_json_decimal_false_for_excess_precision():
    # More significant digits than binary64 round-trip can preserve --
    # this is NOT the shortest-roundtrip decimal for its nearest binary64.
    unstable = GeniaDecimal(1000000000000000000001, -22)  # 0.1000000000000000000001
    assert stable_json_decimal(unstable) is False


def test_stable_json_decimal_false_for_huge_coefficient_precision():
    unstable = GeniaDecimal(123456789123456789123456789, 0)
    assert stable_json_decimal(unstable) is False


def test_stable_json_decimal_false_for_overflow():
    # Exponent large enough that the exact value exceeds the largest finite
    # binary64 -- conversion overflows to infinity.
    huge = GeniaDecimal(1, 400)
    assert stable_json_decimal(huge) is False


def test_stable_json_decimal_false_for_underflow_to_zero():
    # Tiny nonzero coefficient with very negative exponent underflows to
    # binary64 0.0.
    tiny = GeniaDecimal(1, -400)
    assert stable_json_decimal(tiny) is False


# ---------------------------------------------------------------------------
# encode: stable Decimal round-trips to canonical text as a raw JSON number
# ---------------------------------------------------------------------------


def test_encode_stable_decimal_emits_canonical_text_as_raw_number():
    d = GeniaDecimal(1, -1)  # 0.1
    assert stable_json_decimal(d) is True
    result = _encode(d)
    assert isinstance(result, GeniaOptionSome)
    assert result.value == repr(d)
    assert result.value == "0.1"
    # Must be a raw JSON number token, not a quoted string.
    assert '"0.1"' not in result.value


def test_encode_stable_decimal_integral_value_keeps_dot_zero():
    d = GeniaDecimal(1000, -1)  # 100.0
    result = _encode(d)
    assert isinstance(result, GeniaOptionSome)
    assert result.value == "100.0"


def test_encode_unstable_decimal_rejected_not_degraded_to_string_or_rounded():
    unstable = GeniaDecimal(1000000000000000000001, -22)
    result = _encode(unstable)
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_encode_decimal_inside_list_and_map():
    payload = ["k", GeniaDecimal(25, -1)]
    result = _encode(payload)
    assert isinstance(result, GeniaOptionSome)
    assert "2.5" in result.value
    assert '"2.5"' not in result.value


# ---------------------------------------------------------------------------
# decode: fraction/exponent tokens -> exact Decimal, lexically parsed
# ---------------------------------------------------------------------------


def test_decode_fraction_token_produces_exact_decimal_not_float():
    result = _decode("0.1")
    assert isinstance(result, GeniaOptionSome)
    value = result.value.value
    assert isinstance(value, GeniaDecimal)
    assert not isinstance(value, float)
    assert value == GeniaDecimal(1, -1)


def test_decode_lexical_parse_differs_from_float_round_trip():
    # A naive implementation that decoded via `Decimal(float(token))`
    # (constructing an exact decimal.Decimal from the already-lossy host
    # float, rather than parsing the token text lexically) would produce a
    # ~55-significant-digit coefficient for "0.1" (Python's `float('0.1')`
    # is not exactly one tenth: `decimal.Decimal(0.1)` is
    # `0.1000000000000000055511151231257827021181583404541015625`). A
    # correct lexical decode must instead produce the exact digit-for-digit
    # coefficient/exponent the token text itself spells.
    result = _decode("0.1")
    assert isinstance(result, GeniaOptionSome)
    value = result.value.value
    assert isinstance(value, GeniaDecimal)
    assert value.coefficient == 1
    assert value.exponent == -1
    import decimal as _decimal_module

    float_exact_coefficient = int(_decimal_module.Decimal(0.1).as_tuple().digits and "".join(
        str(d) for d in _decimal_module.Decimal(0.1).as_tuple().digits
    ))
    assert value.coefficient != float_exact_coefficient


def test_decode_exponent_token_produces_exact_decimal():
    result = _decode("1.5e3")
    assert isinstance(result, GeniaOptionSome)
    value = result.value.value
    assert isinstance(value, GeniaDecimal)
    assert value == GeniaDecimal(15, 2)  # 1500.0 canonical form


def test_decode_unstable_fraction_token_rejected_with_normalized_diagnostic():
    result = _decode("0.1000000000000000000001")
    assert isinstance(result, GeniaOptionErr)
    assert str(result.reason) == "json_number_out_of_range"


def test_decode_negative_fraction_token():
    result = _decode("-0.5")
    assert isinstance(result, GeniaOptionSome)
    value = result.value.value
    assert isinstance(value, GeniaDecimal)
    assert value == GeniaDecimal(-5, -1)


def test_decode_nonfinite_spellings_remain_invalid_json():
    for token in ["NaN", "Infinity", "-Infinity"]:
        result = _decode(token)
        assert isinstance(result, GeniaOptionErr)


# ---------------------------------------------------------------------------
# round-trip property tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "coefficient,exponent",
    [
        (1, -1),
        (5, -1),
        (10, -1),
        (25, -1),
        (0, 0),
        (-5, -1),
        (1000, -1),
        (150, 2),
    ],
)
def test_encode_then_decode_round_trips_exactly(coefficient, exponent):
    original = GeniaDecimal(coefficient, exponent)
    encoded = _encode(original)
    assert isinstance(encoded, GeniaOptionSome)
    decoded = _decode(encoded.value)
    assert isinstance(decoded, GeniaOptionSome)
    assert decoded.value.value == original


# ---------------------------------------------------------------------------
# nested containers via full Genia source
# ---------------------------------------------------------------------------


def test_genia_source_round_trips_decimal_in_nested_object():
    src = (
        'text = unwrap_or("", json_encode({price: 0.1, items: [1.5, 100]}))\n'
        'represented = unwrap_or("", json_decode(text))\n'
        'decoded = unwrap_or({}, representation_match("json", represented))\n'
        "decoded"
    )
    result = _run(src)
    rendered = format_debug(result)
    assert "0.1" in rendered
    assert "1.5" in rendered


def test_genia_source_rejects_unstable_decimal_encode():
    src = "json_encode(0.1000000000000000000001)"
    result = _run(src)
    rendered = format_debug(result)
    assert "err(" in rendered
    assert "json_number_out_of_range" in rendered
