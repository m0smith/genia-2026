"""E22-9 (issue #895): cross-surface conformance and compatibility hardening.

Proves the merged R22 runtime model (E22-1..E22-8) behaves consistently
across surfaces outside the evaluator's core arithmetic dispatch: quoted/
metacircular evaluation, pattern matching, and other numeric-touching
surfaces (Sheets render_csv, retrieval finite-score gating).

Covers docs/design/r22-exact-numeric-runtime-contract.md as a whole-model
compatibility slice, not a new semantic slice: every case here already had
a defined runtime kind produced by a prior slice; this slice only proves
other surfaces preserve that kind/value instead of silently reinterpreting
it as a different numeric kind.
"""
from __future__ import annotations

from src.genia.numeric_runtime import GeniaDecimal, GeniaRational, rational_from_integers
from src.genia.retrieval import _is_finite_score
from src.genia.sheet import _csv_scalar_text


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


def _rat(n: int, d: int) -> GeniaRational:
    value = rational_from_integers(n, d)
    assert isinstance(value, GeniaRational)
    return value


# ---------------------------------------------------------------------------
# Quoted / metacircular evaluation matches ordinary evaluation
# ---------------------------------------------------------------------------


def test_quote_decimal_literal_matches_ordinary_evaluation() -> None:
    quoted = _run("quote(1.5)")
    ordinary = _run("1.5")
    assert type(quoted) is GeniaDecimal
    assert type(quoted) is type(ordinary)
    assert quoted.coefficient == ordinary.coefficient
    assert quoted.exponent == ordinary.exponent


def test_quasiquote_decimal_literal_matches_ordinary_evaluation() -> None:
    quoted = _run("quasiquote(1.5)")
    ordinary = _run("1.5")
    assert type(quoted) is GeniaDecimal
    assert quoted.coefficient == ordinary.coefficient
    assert quoted.exponent == ordinary.exponent


def test_quote_integer_literal_is_unaffected() -> None:
    assert _run("quote(3)") == 3
    assert isinstance(_run("quote(3)"), int)


def test_eval_of_quoted_decimal_literal_round_trips() -> None:
    # A decimal literal quoted then eval'd through the metacircular
    # evaluator's self-evaluating-literal path must produce the same exact
    # GeniaDecimal an ordinary (non-quoted) evaluation would -- proving both
    # that quote_node carries a real Decimal payload and that the
    # metacircular evaluator's self-evaluating? predicate recognizes
    # GeniaDecimal/GeniaRational, not just Python int/float.
    result = _run("eval(quote(1.5), empty_env())")
    expected = _run("1.5")
    assert type(result) is GeniaDecimal
    assert result.coefficient == expected.coefficient
    assert result.exponent == expected.exponent


def test_eval_of_quoted_rational_round_trips() -> None:
    result = _run("eval(rational(1, 3), empty_env())")
    expected = _rat(1, 3)
    assert type(result) is GeniaRational
    assert result == expected


# ---------------------------------------------------------------------------
# Pattern matching uses the shared R18/R22 equality relation
# ---------------------------------------------------------------------------


def test_pattern_match_decimal_literal_against_integer_value() -> None:
    # 1 == 1.0 under R22 section 10.1; a `1.0` literal pattern must match an
    # Integer 1 runtime value via genia_equal, not raw ==/is.
    source = """
    classify(x) =
      1.0 -> "matched" |
      _ -> "no-match"
    classify(1)
    """
    assert _run(source) == "matched"


def test_pattern_match_integer_literal_against_decimal_value() -> None:
    source = """
    classify(x) =
      1 -> "matched" |
      _ -> "no-match"
    classify(1.0)
    """
    assert _run(source) == "matched"


# ---------------------------------------------------------------------------
# Sheets render_csv accepts GeniaRational alongside GeniaDecimal
# ---------------------------------------------------------------------------


def test_csv_scalar_text_accepts_rational() -> None:
    assert _csv_scalar_text(_rat(1, 3), "column") == str(_rat(1, 3))


def test_csv_scalar_text_accepts_decimal() -> None:
    value = GeniaDecimal(15, -1)
    assert _csv_scalar_text(value, "column") == str(value)


# ---------------------------------------------------------------------------
# Retrieval finite-score gating accepts GeniaRational alongside GeniaDecimal
# ---------------------------------------------------------------------------


def test_finite_score_accepts_rational() -> None:
    assert _is_finite_score(_rat(1, 3)) is True


def test_finite_score_accepts_decimal() -> None:
    assert _is_finite_score(GeniaDecimal(15, -1)) is True


def test_finite_score_still_rejects_bool() -> None:
    assert _is_finite_score(True) is False


def test_finite_score_still_rejects_nan_and_non_numeric() -> None:
    assert _is_finite_score(float("nan")) is False
    assert _is_finite_score("not-a-score") is False
