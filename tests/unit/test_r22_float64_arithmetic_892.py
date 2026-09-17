"""E22-6 (issue #892): Float64 arithmetic and mixed-domain rejection.

Covers docs/design/r22-exact-numeric-runtime-contract.md section 9:
Float64-with-Float64 supports unary -, +, -, *, /, % as ordinary
IEEE-754 binary64 arithmetic; division/remainder by Float64 zero is
deterministic misuse; arithmetic mixing Float64 with any exact operand is
rejected in both operand orders and for every operator.
"""
from __future__ import annotations

import pytest

from src.genia.numeric_runtime import GeniaDecimal, rational_from_integers


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


def _dec(coefficient: int, exponent: int) -> GeniaDecimal:
    return GeniaDecimal(coefficient, exponent)


# ---------------------------------------------------------------------------
# Float64 + Float64: ordinary IEEE-754 binary64 arithmetic
# ---------------------------------------------------------------------------


def test_float64_arithmetic_operators() -> None:
    # `1.5`/`2.5` in Genia source are exact GeniaDecimal literals (R22
    # E22-1), so float64(...) makes these genuinely Float64 operands.
    assert _run("float64(1.5) + float64(2.5)") == 4.0
    assert _run("float64(-1) + float64(1)") == 0.0


def test_float64_unary_minus() -> None:
    assert _run("-float64(1)") == -1.0


def test_float64_native_operators_directly() -> None:
    from src.genia import make_global_env, run_source

    env = make_global_env([])
    a = run_source("float64(3)", env)
    b = run_source("float64(2)", env)
    assert a + b == 5.0
    assert a - b == 1.0
    assert a * b == 6.0
    assert a / b == 1.5
    assert a % b == 1.0
    assert -a == -3.0


def test_float64_floor_remainder_matches_python_native() -> None:
    from src.genia import make_global_env, run_source

    env = make_global_env([])
    a = run_source("float64(-5.5)", env)
    b = run_source("float64(2)", env)
    assert a % b == (-5.5) % 2.0


# ---------------------------------------------------------------------------
# Division/remainder by Float64 zero: deterministic misuse
# ---------------------------------------------------------------------------


def test_float64_division_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        _run("float64(1) / float64(0)")


def test_float64_remainder_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError):
        _run("float64(1) % float64(0)")


def test_float64_division_by_zero_message_is_deterministic() -> None:
    from src.genia import make_global_env, run_source

    env = make_global_env([])
    with pytest.raises(ZeroDivisionError) as excinfo:
        run_source("float64(1) / float64(0)", env)
    assert str(excinfo.value) == "float64 division by zero"


def test_float64_division_by_zero_never_produces_infinity() -> None:
    # If this ever silently succeeded, it would return inf; ensure it raises.
    with pytest.raises(ZeroDivisionError):
        _run("float64(1) / float64(0)")


# ---------------------------------------------------------------------------
# Mixed exact/Float64 arithmetic: rejected, every operator, both orders
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op", ["+", "-", "*", "/", "%"])
def test_integer_and_float64_mixed_arithmetic_rejected(op: str) -> None:
    result = _run(f"1 {op} float64(2)")
    assert result is not None
    assert type(result).__name__ in ("GeniaOptionNone",)


@pytest.mark.parametrize("op", ["+", "-", "*", "/", "%"])
def test_float64_and_integer_mixed_arithmetic_rejected(op: str) -> None:
    result = _run(f"float64(2) {op} 1")
    assert type(result).__name__ == "GeniaOptionNone"


@pytest.mark.parametrize("op", ["+", "-", "*", "/", "%"])
def test_decimal_and_float64_mixed_arithmetic_rejected(op: str) -> None:
    result = _run(f"1.5 {op} float64(2)")
    assert type(result).__name__ == "GeniaOptionNone"


@pytest.mark.parametrize("op", ["+", "-", "*", "/", "%"])
def test_rational_and_float64_mixed_arithmetic_rejected(op: str) -> None:
    result = _run(f"rational(1, 2) {op} float64(2)")
    assert type(result).__name__ == "GeniaOptionNone"


def test_mixed_arithmetic_requires_explicit_conversion_first() -> None:
    # float64(...) first makes it work.
    assert _run("float64(1) + float64(2)") == 3.0
    # exact(...) first also makes it work (both become exact Decimal).
    result = _run("exact(float64(2.5)) + 1")
    assert type(result).__name__ == "GeniaDecimal"


def test_mixed_arithmetic_helper_directly() -> None:
    from src.genia.numeric_runtime import is_mixed_exact_and_float64

    assert is_mixed_exact_and_float64(1, 2.0) is True
    assert is_mixed_exact_and_float64(2.0, 1) is True
    assert is_mixed_exact_and_float64(_dec(15, -1), 2.0) is True
    assert is_mixed_exact_and_float64(rational_from_integers(1, 2), 2.0) is True
    assert is_mixed_exact_and_float64(2.0, 3.0) is False
    assert is_mixed_exact_and_float64(1, 2) is False
    assert is_mixed_exact_and_float64(_dec(1, 0), rational_from_integers(1, 2)) is False
