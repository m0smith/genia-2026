"""Unit tests for reconciling legacy `json_parse`/`json_stringify` numeric
semantics with the exact numeric model (issue #842).

Contract: docs/design/exact-numeric-model-contract.md section 13.5's
lexical-decode principle generalizes to the legacy compatibility surface --
"No conforming implementation may parse a JSON fraction to host binary
floating point first" applies to every public JSON parser path, not only
strict `json_decode`. The legacy surface differs from strict `json_decode`
only in its already-approved permissive safe-boundary posture (no
safe-integer/`stable_json_decimal` rejection) -- see issue #842's own
"Direction" section.

`json_parse`/`json_stringify` return a bare value on success and
`none(reason, context)` on failure (never `some(...)` on success -- unlike
`json_decode`/`json_encode`, this legacy pair's existing convention is not
Option-wrapped success). These tests call the `_json_parse`/`_json_stringify`
builtins directly so the underlying Python runtime type is directly
inspectable.
"""

from __future__ import annotations

from genia import make_global_env, run_source
from genia.builtins import make_global_env as _make_env
from genia.numeric_values import Decimal, Float64, make_rational
from genia.values import GeniaOptionNone


def _run(src: str):
    return run_source(src, make_global_env([]))


def _parse(text: str):
    return _make_env([]).get("_json_parse")(text)


def _stringify(value):
    return _make_env([]).get("_json_stringify")(value)


class TestJsonParseDecodesFractionsToExactDecimal:
    def test_simple_fraction_is_exact_decimal_not_host_float(self):
        value = _parse("0.1")
        assert isinstance(value, Decimal)
        assert not isinstance(value, float)
        assert value == Decimal(1, -1)

    def test_fraction_nested_in_array_is_exact_decimal(self):
        items = _parse("[1, 2.5, 3]")
        assert isinstance(items[1], Decimal)
        assert items[1] == Decimal(25, -1)

    def test_fraction_nested_in_object_is_exact_decimal(self):
        root = _parse('{"price": 9.99}')
        assert isinstance(root.get("price"), Decimal)

    def test_integer_token_stays_plain_int_with_no_safe_range_limit(self):
        # Legacy json_parse has always accepted arbitrary-size integers
        # (no R9 safe-integer gate) -- that permissive posture is an
        # already-approved surface difference from strict json_decode and
        # must not change.
        big = "9" * 40
        value = _parse(big)
        assert value == int(big)
        assert isinstance(value, int)


class TestJsonParseIsMorePermissiveThanStrictDecode:
    def test_accepts_a_fraction_strict_decode_would_reject_as_unstable(self):
        # A Decimal token whose text is not the canonical shortest
        # round-trip decimal for its nearest binary64 value fails
        # stable_json_decimal and is rejected by strict json_decode --
        # legacy json_parse has no such safe-boundary restriction.
        unstable = "0.1000000000000000055511151231257827021181583404541015625"
        value = _parse(unstable)
        assert isinstance(value, Decimal)
        assert not isinstance(value, GeniaOptionNone)

    def test_accepts_a_huge_exponent_strict_decode_would_reject(self):
        value = _parse("1e400")
        assert isinstance(value, Decimal)
        assert value == Decimal(1, 400)

    def test_accepts_a_tiny_exponent_strict_decode_would_reject(self):
        value = _parse("1e-400")
        assert isinstance(value, Decimal)


class TestJsonStringifyAcceptsExactNumericValues:
    def test_stringifies_a_decimal(self):
        result = _stringify(Decimal(1, -1))  # 0.1
        assert isinstance(result, str)
        assert result == "0.1"

    def test_stringifies_a_terminating_rational(self):
        result = _stringify(make_rational(1, 4))  # 0.25
        assert isinstance(result, str)
        assert result == "0.25"

    def test_stringifies_a_non_terminating_rational_via_float_approximation(self):
        # Legacy json_stringify has no interop-exactness promise -- a
        # non-terminating Rational (which strict json_encode rejects
        # outright) approximates via the same correctly-rounded conversion
        # a plain float64 conversion would use.
        result = _stringify(make_rational(1, 3))
        assert isinstance(result, str)
        assert result.startswith("0.3333333333333")

    def test_stringifies_a_finite_float64(self):
        result = _stringify(Float64(3.0))
        assert isinstance(result, str)
        assert result == "3.0"

    def test_rejects_a_decimal_exceeding_binary64_range(self):
        huge = Decimal(10**400, 0)
        result = _stringify(huge)
        assert isinstance(result, GeniaOptionNone)
        assert str(result.reason) == "json-stringify-error"


class TestEncodeDecodeRoundTripThroughLegacySurface:
    def test_decimal_round_trips_through_parse_and_stringify(self):
        original = Decimal(1, -1)  # 0.1
        text = _stringify(original)
        assert isinstance(text, str)
        decoded = _parse(text)
        assert isinstance(decoded, Decimal)
        assert decoded == original


class TestNoContradictoryNumericModelBetweenJsonEntryPoints:
    def test_json_parse_and_json_decode_agree_on_fraction_kind(self):
        parsed = _run('json_parse("0.1")')
        decoded = _run(
            'unwrap_or(0, json_decode("0.1")) |> representation_match("json") |> unwrap_or(0)'
        )
        assert type(parsed) is type(decoded) is Decimal
        assert parsed == decoded


class TestExistingNonNumericBehaviorIsUnaffected:
    def test_json_parse_still_parses_strings_bools_and_null(self):
        result = _run(
            r'''
            parsed = json_parse("{\"name\":\"genia\",\"enabled\":true,\"n\":7,\"items\":[1,2,3]}")
            [
              unwrap_or("?", parsed |> get("name")),
              unwrap_or(false, parsed |> get("enabled")),
              unwrap_or(0, parsed |> get("n")),
              unwrap_or([], parsed |> get("items"))
            ]
            '''
        )
        assert result == ["genia", True, 7, [1, 2, 3]]

    def test_json_stringify_still_renders_deterministic_pretty_json(self):
        result = _run("json_stringify({ b: 2, a: 1 })")
        assert result == '{\n  "a": 1,\n  "b": 2\n}'

    def test_json_parse_invalid_json_still_returns_structured_none(self):
        result = _parse('{"x":')
        assert isinstance(result, GeniaOptionNone)
        assert str(result.reason) == "json-parse-error"
