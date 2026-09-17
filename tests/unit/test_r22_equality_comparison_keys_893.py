"""E22-7 (issue #893): mathematical comparison, equality, and R18 map-key
reconciliation.

Covers docs/design/r22-exact-numeric-runtime-contract.md section 10:
Integer/Decimal/Rational compare by mathematical value for ==/!=/</<=/>/>=;
a finite Float64 bridges to exact values by its own exact represented
value (never rounding the exact operand to Float64); NaN is unequal/
unordered against everything including itself; R18 remains the single
equality/key relation (docs/design/r18-portable-value-equality-contract.md).
"""
from __future__ import annotations

import pytest

from src.genia.equality import canonical_map_key, genia_equal
from src.genia.numeric_runtime import GeniaDecimal, rational_from_integers


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


def _dec(coefficient: int, exponent: int) -> GeniaDecimal:
    return GeniaDecimal(coefficient, exponent)


def _rat(n: int, d: int):
    return rational_from_integers(n, d)


# ---------------------------------------------------------------------------
# 10.1 Exact family equality/ordering
# ---------------------------------------------------------------------------


def test_integer_decimal_rational_equal_cross_kind() -> None:
    assert genia_equal(1, _dec(10, -1))  # 1 == 1.0
    assert genia_equal(_dec(1, 0), _dec(100, -2))  # 1.0 == 1.00
    assert genia_equal(1, _rat(2, 2))  # 1 == rational(2,2) -> collapses to 1 anyway
    assert genia_equal(_rat(1, 2), _dec(5, -1))  # 1/2 == 0.5
    assert genia_equal(_rat(1, 2), _rat(2, 4))  # already-reduced, still equal


def test_exact_family_inequality() -> None:
    assert not genia_equal(1, 2)
    assert not genia_equal(_rat(1, 2), _rat(1, 3))
    assert not genia_equal(_dec(1, 0), _rat(1, 2))


def test_genia_source_exact_equality() -> None:
    assert _run("1 == 1.0") is True
    assert _run("1.0 == 1.00") is True
    assert _run("1 == rational(2, 2)") is True
    assert _run("rational(1, 2) == 0.5") is True
    assert _run("1 != 2") is True
    assert _run("rational(1, 2) != rational(1, 3)") is True


@pytest.mark.parametrize(
    "left,right,expected",
    [
        (1, _dec(15, -1), True),  # 1 < 1.5
        (_dec(15, -1), 1, False),
        (_rat(1, 3), _rat(1, 2), True),  # 1/3 < 1/2
        (_rat(1, 2), _rat(1, 3), False),
        (1, _rat(3, 2), True),  # 1 < 3/2
        (_dec(1, 0), _rat(1, 2), False),  # 1.0 < 1/2 is False
        (_rat(1, 2), _dec(1, 0), True),  # 1/2 < 1.0
    ],
)
def test_exact_family_ordering(left, right, expected) -> None:
    assert (left < right) is expected


def test_genia_source_exact_ordering() -> None:
    assert _run("1 < rational(3, 2)") is True
    assert _run("rational(1, 2) <= rational(1, 2)") is True
    assert _run("rational(2, 3) > rational(1, 2)") is True
    assert _run("1.5 >= 1") is True


def test_huge_exact_ordering_arbitrary_precision() -> None:
    huge = 10**60 + 1
    assert _rat(huge, 3) > huge // 3
    assert huge < _rat(huge * 3 + 1, 3)


# ---------------------------------------------------------------------------
# 10.2 Float64 bridge
# ---------------------------------------------------------------------------


def test_float64_equals_exact_only_when_mathematically_identical() -> None:
    assert genia_equal(1.0, 1)
    assert genia_equal(1, 1.0)
    assert not genia_equal(1.5, 1)
    # A float that is NOT exactly 0.1 (since 0.1 has no exact binary64
    # representation) must not equal the exact Decimal 0.1.
    assert not genia_equal(0.1, _dec(1, -1))


def test_float64_bridge_never_rounds_exact_operand() -> None:
    # exact(0.1) is the long non-terminating expansion; float64(0.1) must
    # equal exactly THAT Decimal, not the short spelling "0.1".
    from src.genia.numeric_runtime import exact, to_float64

    float_value = to_float64(_dec(1, -1))  # float64(0.1)
    exact_value = exact(float_value)  # the long exact expansion
    assert genia_equal(float_value, exact_value)
    assert not genia_equal(float_value, _dec(1, -1))  # short "0.1" spelling


def test_float64_signed_zero_equals_exact_zero() -> None:
    assert genia_equal(0.0, 0)
    assert genia_equal(-0.0, 0)
    assert genia_equal(0.0, _dec(0, 0))
    assert genia_equal(-0.0, _dec(0, 0))


def test_float64_nan_unequal_to_everything() -> None:
    nan = float("nan")
    assert not genia_equal(nan, nan)
    assert not genia_equal(nan, 1)
    assert not genia_equal(1, nan)
    assert not genia_equal(nan, _dec(1, 0))
    assert not genia_equal(nan, _rat(1, 2))


def test_float64_infinity_never_equals_finite_exact() -> None:
    assert not genia_equal(float("inf"), 1)
    assert not genia_equal(float("-inf"), _dec(1, 0))
    assert not genia_equal(float("inf"), _rat(1, 2))


def test_float64_ordering_bridge_exact_dyadic_value() -> None:
    from src.genia.numeric_runtime import to_float64

    half = to_float64(_rat(1, 2))  # exactly representable
    assert not (half < _dec(5, -1))  # 0.5 < 0.5 is False
    assert not (half > _dec(5, -1))
    assert half <= _dec(5, -1)
    assert half >= _dec(5, -1)
    assert half < 1
    assert 0 < half


def test_float64_ordering_with_nan_is_always_false() -> None:
    nan = float("nan")
    assert not (nan < 1)
    assert not (1 < nan)
    assert not (nan <= 1)
    assert not (nan > _dec(1, 0))
    assert not (_rat(1, 2) >= nan)


def test_float64_ordering_with_infinity() -> None:
    assert 1 < float("inf")
    assert float("-inf") < 1
    assert _dec(1, 0) < float("inf")
    assert _rat(1, 2) > float("-inf")


def test_genia_source_float64_bridge() -> None:
    assert _run("float64(2) == 2") is True
    assert _run("2 == float64(2)") is True
    assert _run("float64(1) < 2") is True
    assert _run("rational(1, 2) < float64(1)") is True


# ---------------------------------------------------------------------------
# 10.3 Map keys
# ---------------------------------------------------------------------------


def test_map_key_cross_kind_collision() -> None:
    int_key = canonical_map_key(1)
    decimal_key = canonical_map_key(_dec(10, -1))  # 1.0
    rational_key = canonical_map_key(_rat(2, 2))  # collapses to Integer 1 already
    float_key = canonical_map_key(1.0)
    assert int_key == decimal_key == rational_key == float_key


def test_map_key_non_integral_cross_kind_collision() -> None:
    decimal_key = canonical_map_key(_dec(5, -1))  # 0.5
    rational_key = canonical_map_key(_rat(1, 2))
    float_key = canonical_map_key(0.5)
    assert decimal_key == rational_key == float_key


def test_map_key_distinguishes_unequal_values() -> None:
    assert canonical_map_key(_dec(5, -1)) != canonical_map_key(_rat(1, 3))
    assert canonical_map_key(1) != canonical_map_key(2)


def test_map_key_nan_illegal() -> None:
    with pytest.raises(TypeError):
        canonical_map_key(float("nan"))


def test_map_key_infinity_legal_and_distinct() -> None:
    pos = canonical_map_key(float("inf"))
    neg = canonical_map_key(float("-inf"))
    assert pos != neg
    # Infinity never collides with any finite exact/float key.
    assert pos != canonical_map_key(1)


def test_genia_source_map_key_cross_kind() -> None:
    result = _run(
        "m = map_put(map_new(), 1, \"one\"); "
        "[map_get(m, 1.0), map_get(m, rational(2, 2)), map_has?(m, float64(1))]"
    )
    assert result == ["one", "one", True]


def test_genia_source_map_key_non_integral_cross_kind() -> None:
    result = _run(
        "m = map_put(map_new(), 0.5, \"half\"); "
        "[map_get(m, rational(1, 2)), map_get(m, float64(0.5))]"
    )
    assert result == ["half", "half"]
