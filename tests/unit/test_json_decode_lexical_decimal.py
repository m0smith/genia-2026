"""Unit tests for lexical JSON Decimal decode (issue #841).

Contract: docs/design/exact-numeric-model-contract.md section 13.5 --
JSON number tokens are consumed lexically: an integer-form token becomes
Integer (within the existing safe-integer interval); a fraction/exponent
token becomes exact Decimal only when it satisfies `stable_json_decimal`;
JSON never directly constructs Rational; non-finite spellings stay invalid.

These tests call the `_json_decode` builtin directly (as
`tests/unit/test_json_representation_boundary.py` does) so the underlying
Python runtime type of a decoded number is directly inspectable -- a plain
host `float` must never appear for a fraction/exponent JSON token.
"""

from __future__ import annotations

from genia.builtins import make_global_env
from genia.numeric_values import Decimal, Rational
from genia.values import GeniaOptionErr, GeniaOptionSome


def _decode(text: str):
    return make_global_env([]).get("_json_decode")(text)


class TestFractionExponentTokensDecodeToExactDecimal:
    def test_simple_fraction_is_exact_decimal_not_host_float(self):
        result = _decode("0.1")
        assert isinstance(result, GeniaOptionSome)
        value = result.value.value
        assert isinstance(value, Decimal)
        assert not isinstance(value, float)
        assert value == Decimal(1, -1)

    def test_bare_exponent_token_is_exact_decimal(self):
        result = _decode("1e3")
        assert isinstance(result, GeniaOptionSome)
        value = result.value.value
        assert isinstance(value, Decimal)
        assert value == Decimal(1, 3)

    def test_negative_fraction_token_is_exact_decimal(self):
        result = _decode("-1.5")
        assert isinstance(result, GeniaOptionSome)
        value = result.value.value
        assert isinstance(value, Decimal)
        assert value == Decimal(-15, -1)

    def test_dotted_exponent_token_is_exact_decimal(self):
        result = _decode("1.25e-2")
        assert isinstance(result, GeniaOptionSome)
        value = result.value.value
        assert isinstance(value, Decimal)
        assert value == Decimal(125, -4)

    def test_fraction_token_nested_in_array_is_exact_decimal(self):
        result = _decode("[0.5, 1, 2.5e1]")
        assert isinstance(result, GeniaOptionSome)
        items = result.value.value
        assert isinstance(items[0], Decimal)
        assert items[1] == 1 and isinstance(items[1], int)
        assert isinstance(items[2], Decimal)
        assert items[2] == Decimal(25, 0)

    def test_fraction_token_nested_in_object_is_exact_decimal(self):
        result = _decode('{"score": 7.5}')
        assert isinstance(result, GeniaOptionSome)
        root = result.value.value
        assert isinstance(root.get("score"), Decimal)


class TestIntegerTokensStillMaterializeAsInteger:
    def test_safe_integer_decodes_as_plain_int(self):
        result = _decode("42")
        assert isinstance(result, GeniaOptionSome)
        assert result.value.value == 42
        assert isinstance(result.value.value, int)

    def test_out_of_range_integer_is_rejected(self):
        result = _decode("9007199254740992")
        assert isinstance(result, GeniaOptionErr)
        assert str(result.reason) == "json_number_out_of_range"


class TestUnstableDecimalTokensAreRejected:
    def test_unstable_fraction_is_rejected_not_rounded(self):
        # A fraction whose exact base-10 value round-trips through binary64
        # to a *different* Decimal must be rejected outright, never rounded.
        result = _decode("0.1000000000000000055511151231257827021181583404541015625")
        assert isinstance(result, GeniaOptionErr)
        assert str(result.reason) == "json_number_out_of_range"

    def test_huge_exponent_overflowing_binary64_is_rejected(self):
        result = _decode("1e400")
        assert isinstance(result, GeniaOptionErr)
        assert str(result.reason) == "json_number_out_of_range"

    def test_tiny_exponent_underflowing_binary64_is_rejected(self):
        result = _decode("1e-400")
        assert isinstance(result, GeniaOptionErr)
        assert str(result.reason) == "json_number_out_of_range"


class TestNonFiniteSpellingsStayInvalid:
    def test_nan_is_rejected(self):
        result = _decode("NaN")
        assert isinstance(result, GeniaOptionErr)

    def test_infinity_is_rejected(self):
        result = _decode("Infinity")
        assert isinstance(result, GeniaOptionErr)

    def test_negative_infinity_is_rejected(self):
        result = _decode("-Infinity")
        assert isinstance(result, GeniaOptionErr)


class TestJsonNeverDirectlyConstructsRational:
    def test_no_json_number_token_ever_decodes_to_rational(self):
        for text in ("0.1", "1", "1e3", "-1.5", "1.25e-2", "3.0"):
            result = _decode(text)
            assert isinstance(result, GeniaOptionSome)
            assert not isinstance(result.value.value, Rational)


class TestEncodeDecodeRoundTrip:
    def test_stable_decimal_round_trips_through_encode_decode(self):
        env = make_global_env([])
        encode = env.get("_json_encode")
        decode = env.get("_json_decode")
        original = Decimal(1, -1)  # 0.1
        encoded = encode(original)
        assert isinstance(encoded, GeniaOptionSome)
        decoded = decode(encoded.value)
        assert isinstance(decoded, GeniaOptionSome)
        assert decoded.value.value == original

    def test_terminating_rational_round_trips_through_encode_decode_as_decimal(self):
        env = make_global_env([])
        encode = env.get("_json_encode")
        decode = env.get("_json_decode")
        from genia.numeric_values import make_rational

        original = make_rational(1, 4)  # 0.25, terminating
        encoded = encode(original)
        assert isinstance(encoded, GeniaOptionSome)
        decoded = decode(encoded.value)
        assert isinstance(decoded, GeniaOptionSome)
        # Contract section 13.5: JSON never directly constructs Rational --
        # the round-tripped mathematical value equals the original Rational,
        # but the decoded runtime kind is exact Decimal.
        assert isinstance(decoded.value.value, Decimal)
        assert decoded.value.value == Decimal(25, -2)
