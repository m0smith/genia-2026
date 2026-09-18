"""Failing tests for issue #923 (E23-5): compatibility JSON reconciliation.

Implements docs/design/r23-numeric-representation-interchange-contract.md
section 6 ("Compatibility JSON surfaces") against the compatibility JSON
boundary only: `json_parse`/`json_stringify`/`json_pretty`
(`json_parse_fn`/`json_stringify_fn`, backed by `_json_to_runtime`/
`_json_from_runtime` in `src/genia/builtins.py`) and `parse_jsonl_record`
(`parse_jsonl_record_fn`). The strict generic JSON boundary
(`json_decode`/`json_encode`, E23-3/E23-4) is frozen and is only called
into here, never asserted to have changed.

Decisions this file pins (see
docs/analysis/issue-923-e23-5-compatibility-json-reconciliation-preflight.md
for full rationale):

- Decode: a fraction/exponent JSON number token always decodes to an
  exact `GeniaDecimal`, never a Python `float`, whether or not it would
  satisfy strict `json_decode`'s `stable_json_decimal` gate (compatibility
  decode is deliberately permissive, never rejecting a syntactically
  valid number).
- Decode: `json_parse` and `json_decode` share the exact same lexical
  token parser function object (`_parse_json_decimal_token`) -- proven
  directly, not just behaviorally.
- Encode: `json_stringify` now accepts `GeniaDecimal`/terminating
  `GeniaRational`/finite Float64, reusing E23-3/E23-4's canonical-text +
  sentinel-injection machinery, without enforcing `stable_json_decimal`
  (same permissiveness as decode). A non-terminating `GeniaRational` and
  a non-finite Float64 remain unsupported (`none("json-stringify-error",
  ...)`, this surface's existing failure shape).
- Encode: a bare Float64 (`float`) value now renders through the same
  canonical-digit computation `format_float64`/strict `json_encode` use,
  not `json.dumps`'s own `float.__repr__`-derived digits.
- `parse_jsonl_record` shares the same decode fix as `json_parse` (same
  underlying `parse_float` hook).

Out of scope here: unifying the `none(...)`-vs-`err(...)` failure-shape
difference between compatibility and strict JSON (approved pre-existing
difference); full diagnostics sweep (E23-6); release audit (E23-7).
"""
from __future__ import annotations

from genia import make_global_env, run_source
from genia.numeric_runtime import (
    GeniaDecimal,
    format_float64,
    rational_from_integers,
)
from genia.values import GeniaMap, GeniaOptionSome


def _env():
    return make_global_env([])


def _run(src: str):
    return run_source(src, make_global_env())


def _json_parse(text):
    return _env().get("_json_parse")(text)


def _json_stringify(value):
    return _env().get("_json_stringify")(value)


def _parse_jsonl_record(line):
    return _env().get("_parse_jsonl_record")(line)


# ---------------------------------------------------------------------------
# decode: json_parse never materializes a fraction/exponent token as float
# ---------------------------------------------------------------------------


def test_json_parse_fraction_token_decodes_to_exact_decimal_not_float():
    parsed = _json_parse('{"x": 1.5}')
    assert isinstance(parsed, GeniaMap)
    x = parsed.get("x")
    assert isinstance(x, GeniaDecimal)
    assert not isinstance(x, float)
    assert x == GeniaDecimal(15, -1)


def test_json_parse_exponent_token_decodes_to_exact_decimal_not_float():
    parsed = _json_parse('{"y": 1e3}')
    y = parsed.get("y")
    assert isinstance(y, GeniaDecimal)
    assert not isinstance(y, float)
    assert y == GeniaDecimal(1, 3)


def test_json_parse_integer_token_is_unaffected_plain_int():
    parsed = _json_parse('{"z": 7}')
    z = parsed.get("z")
    assert isinstance(z, int)
    assert not isinstance(z, GeniaDecimal)


def test_json_parse_decodes_fraction_even_when_it_would_fail_strict_stability_gate():
    # A value with more significant digits than binary64 round-trip
    # precision preserves. Strict json_decode rejects this
    # (json_number_out_of_range); compatibility json_parse must still
    # decode it to an exact Decimal (deliberate permissiveness decision).
    text = "0.123456789012345678901234567890"
    strict = _env().get("_json_decode")(text)
    from genia.values import GeniaOptionErr

    assert isinstance(strict, GeniaOptionErr)

    parsed = _json_parse('{"p": %s}' % text)
    p = parsed.get("p")
    assert isinstance(p, GeniaDecimal)
    assert not isinstance(p, float)


def test_json_parse_nested_and_list_fraction_tokens_decode_to_decimal():
    parsed = _json_parse('[1.5, {"n": 2.25}]')
    assert isinstance(parsed[0], GeniaDecimal)
    assert isinstance(parsed[1].get("n"), GeniaDecimal)


# ---------------------------------------------------------------------------
# decode: no second lexical parser -- json_parse and json_decode share it
# ---------------------------------------------------------------------------


def test_json_parse_and_json_decode_share_the_same_lexical_token_parser():
    import genia.builtins as builtins_module
    import inspect

    source = inspect.getsource(builtins_module.make_global_env)
    # Both the strict (_strict_json_decimal) and compatibility
    # (_compat_json_decimal) parse_float hooks must delegate to the same
    # shared `_parse_json_decimal_token` function -- not duplicate their
    # own regex/parsing logic. Confirmed by direct source inspection of
    # each hook body, not a black-box behavioral guess.
    assert "_parse_json_decimal_token" in source
    # Each hook's own body should be a thin delegation, not a
    # reimplementation: neither should contain its own independent
    # regex-match call outside the shared helper.
    strict_marker = "def _strict_json_decimal("
    compat_marker = "def _compat_json_decimal("
    assert strict_marker in source
    assert compat_marker in source
    strict_body = source.split(strict_marker, 1)[1].split("def ", 1)[0]
    compat_body = source.split(compat_marker, 1)[1].split("def ", 1)[0]
    assert "_JSON_NUMBER_TOKEN_RE" not in strict_body
    assert "_JSON_NUMBER_TOKEN_RE" not in compat_body
    assert "_parse_json_decimal_token(" in strict_body
    assert "_parse_json_decimal_token(" in compat_body


# ---------------------------------------------------------------------------
# encode: json_stringify now supports Decimal/Rational/Float64
# ---------------------------------------------------------------------------


def test_json_stringify_encodes_decimal_as_exact_canonical_number_text():
    result = _json_stringify(GeniaDecimal(15, -1))
    assert result == "1.5"
    assert '"' not in result


def test_json_stringify_encodes_decimal_even_when_unstable_under_binary64():
    # Same value as the strict-boundary-rejecting decode case above --
    # compatibility encode does not enforce stable_json_decimal either.
    value = GeniaDecimal(123456789012345678901234567890, -30)
    result = _json_stringify(value)
    assert result == "0.12345678901234567890123456789"


def test_json_stringify_encodes_terminating_rational_as_decimal_text():
    value = rational_from_integers(1, 4)
    result = _json_stringify(value)
    assert result == "0.25"


def test_json_stringify_rejects_non_terminating_rational():
    from genia.values import GeniaOptionErr, is_none

    value = rational_from_integers(1, 3)
    result = _json_stringify(value)
    # Compatibility failure shape is `none(...)`, not `err(...)`.
    assert not isinstance(result, GeniaOptionErr)
    assert is_none(result)


def test_json_stringify_rejects_non_terminating_rational_received_field_is_portable():
    """Issue #933 (E23-8): `received` must be the portable type name
    ("rational"), never the raw Python implementation class name
    ("GeniaRational") -- see docs/analysis/r23-release-truth-audit.md.
    """
    from genia.values import is_none

    value = rational_from_integers(1, 3)
    result = _json_stringify(value)
    assert is_none(result)
    context = result.context
    assert context.get("received") == "rational"


def test_json_stringify_rejects_non_finite_float():
    from genia.values import is_none

    result = _json_stringify(float("nan"))
    assert is_none(result)


def test_json_stringify_float_uses_canonical_digits_not_python_repr():
    # A magnitude where format_float64's canonical fixed/scientific
    # threshold and Python's float.__repr__ threshold diverge.
    value = 1e21
    result = _json_stringify(value)
    canonical = format_float64(value)
    assert canonical.startswith("float64(")
    canonical_digits = canonical[len("float64(") : -1]
    assert result == canonical_digits
    assert result != repr(value)


def test_json_stringify_finite_float_matches_strict_json_encode_digits():
    value = 3.14
    compat_result = _json_stringify(value)
    strict_result = _env().get("_json_encode")(value)
    assert isinstance(strict_result, GeniaOptionSome)
    assert compat_result == strict_result.value


# ---------------------------------------------------------------------------
# encode/decode round trip: the asymmetry this slice's decode fix would
# otherwise introduce is resolved
# ---------------------------------------------------------------------------


def test_json_stringify_json_parse_round_trips_a_decimal_bearing_document():
    text = '{"n": 2.5}'
    parsed = _json_parse(text)
    restringified = _json_stringify(parsed)
    reparsed = _json_parse(restringified)
    assert reparsed.get("n") == parsed.get("n")
    assert isinstance(reparsed.get("n"), GeniaDecimal)


# ---------------------------------------------------------------------------
# parse_jsonl_record shares the same decode fix
# ---------------------------------------------------------------------------


def test_parse_jsonl_record_fraction_token_decodes_to_exact_decimal_not_float():
    result = _parse_jsonl_record('{"n": 1.5}')
    assert isinstance(result, GeniaOptionSome)
    n = result.value.get("n")
    assert isinstance(n, GeniaDecimal)
    assert not isinstance(n, float)


def test_parse_jsonl_record_exponent_token_decodes_to_exact_decimal_not_float():
    result = _parse_jsonl_record('{"n": 2e2}')
    n = result.value.get("n")
    assert isinstance(n, GeniaDecimal)
    assert n == GeniaDecimal(2, 2)


# ---------------------------------------------------------------------------
# Genia-source-level round trip
# ---------------------------------------------------------------------------


def test_genia_source_json_parse_produces_decimal_display():
    src = r'''
    parsed = json_parse("{\"x\": 1.5}")
    display(unwrap_or(0, parsed |> get("x")))
    '''
    assert _run(src) == "1.5"


def test_genia_source_json_stringify_of_parsed_decimal_round_trips():
    src = r'''
    parsed = json_parse("{\"x\": 1.5}")
    json_stringify(parsed)
    '''
    assert _run(src) == '{\n  "x": 1.5\n}'
