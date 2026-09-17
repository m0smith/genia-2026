"""E22-2 (issue #888): Rational runtime value and rational(...).

Covers docs/design/r22-exact-numeric-runtime-contract.md section 3: exact
reduced ratio of two arbitrary-precision Integers, with gcd reduction,
positive denominator, sign carried by the numerator, and denominator-one
collapse to Integer.
"""
from __future__ import annotations

from src.genia.numeric_runtime import GeniaRational, rational_from_integers


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


def test_rational_reduces_by_gcd() -> None:
    value = rational_from_integers(2, 4)
    assert isinstance(value, GeniaRational)
    assert (value.numerator, value.denominator) == (1, 2)


def test_rational_negative_over_negative_is_positive() -> None:
    value = rational_from_integers(-2, -4)
    assert isinstance(value, GeniaRational)
    assert (value.numerator, value.denominator) == (1, 2)


def test_rational_sign_carried_by_numerator() -> None:
    value = rational_from_integers(2, -4)
    assert isinstance(value, GeniaRational)
    assert (value.numerator, value.denominator) == (-1, 2)


def test_rational_denominator_one_collapses_to_integer() -> None:
    value = rational_from_integers(2, 2)
    assert value == 1
    assert type(value) is int


def test_rational_already_reduced_denominator_one_collapses() -> None:
    value = rational_from_integers(7, 1)
    assert value == 7
    assert type(value) is int


def test_rational_zero_denominator_is_deterministic_misuse() -> None:
    try:
        rational_from_integers(1, 0)
        assert False, "expected TypeError for zero denominator"
    except TypeError as exc:
        assert "nonzero denominator" in str(exc)


def test_rational_huge_arbitrary_precision_values() -> None:
    huge = 10**80
    value = rational_from_integers(huge * 2, huge * 3)
    assert isinstance(value, GeniaRational)
    assert (value.numerator, value.denominator) == (2, 3)


# ---------------------------------------------------------------------------
# rational(...) builtin, through the evaluator
# ---------------------------------------------------------------------------


def test_genia_rational_builtin_reduces() -> None:
    result = _run("rational(2, 4)")
    assert type(result).__name__ == "GeniaRational"
    assert result.numerator == 1
    assert result.denominator == 2


def test_genia_rational_builtin_collapses_to_integer() -> None:
    assert _run("rational(2, 2)") == 1


def test_genia_rational_builtin_zero_denominator_is_error() -> None:
    try:
        _run("rational(1, 0)")
        assert False, "expected an error for zero denominator"
    except TypeError as exc:
        assert "nonzero denominator" in str(exc)


def test_genia_rational_builtin_non_integer_arguments_are_errors() -> None:
    for source in ('rational("a", 2)', "rational(1.5, 2)", "rational(true, 2)", "rational(1, 2.0)"):
        try:
            _run(source)
            assert False, f"expected an error for {source!r}"
        except TypeError:
            pass
