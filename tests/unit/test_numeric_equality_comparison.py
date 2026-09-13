"""Unit tests for exact-numeric equality/comparison/map-key reconciliation
(issue #838 step 4).

Covers docs/design/exact-numeric-model-contract.md section 10 (numeric
comparisons and equality): 10.1 exact-family cross-kind equality/ordering,
10.2 the Float64 bridge (including NaN/infinity), and 10.3 map-key
equivalence, reconciled into R18's single equality relation
(``genia.equality.genia_equal``/``canonical_map_key``,
docs/design/r18-portable-value-equality-contract.md) rather than a second,
competing relation.

These tests exercise ``genia.equality``/``genia.numeric_values`` directly for
Decimal/Float64 shapes that are not yet reachable from ordinary Genia source
(no source syntax constructs a bare Decimal or Float64 value ahead of step
5's conversion builtins — see ``numeric_values.py``'s module docstring).
Source-reachable behavior (Integer/Integer division producing Rational) is
covered portably by ``spec/eval/exact-numeric-equality-comparison-rational.yaml``
and by the evaluator-level tests in ``TestEvaluatorWiring`` below.
"""

from __future__ import annotations

import pytest

from genia.equality import canonical_map_key, genia_equal
from genia.numeric_values import (
    Decimal,
    Float64,
    Rational,
    compare_numeric,
    make_rational,
)
from genia.values import GeniaMap, is_none


# ---------------------------------------------------------------------------
# 10.1 exact family cross-kind equality
# ---------------------------------------------------------------------------


class TestExactFamilyEquality:
    def test_integer_decimal_rational_mathematically_equal(self):
        assert genia_equal(1, Decimal(1, 0))
        assert genia_equal(Decimal(1, 0), 1)
        assert genia_equal(1, make_rational(2, 2))
        assert genia_equal(Rational(1, 2), Decimal(5, -1))  # 1/2 == 0.5
        assert genia_equal(Decimal(5, -1), Rational(1, 2))

    def test_exact_family_mathematically_unequal(self):
        assert not genia_equal(Decimal(1, 0), Decimal(2, 0))
        assert not genia_equal(Rational(1, 3), Rational(1, 2))
        assert not genia_equal(1, Rational(1, 2))

    def test_two_independently_constructed_equal_rationals_are_equal(self):
        # Rational is a fresh runtime object each time division produces one;
        # genia_equal must not fall back to host identity for it.
        assert genia_equal(Rational(2, 6), Rational(-2, -6))
        assert genia_equal(Rational(1, 3), Rational(1, 3))

    def test_two_independently_constructed_equal_decimals_are_equal(self):
        assert genia_equal(Decimal.from_payload("100", "-2"), Decimal.from_payload("1", "0"))

    def test_boolean_is_not_number_extends_to_new_numeric_kinds(self):
        assert not genia_equal(True, Decimal(1, 0))
        assert not genia_equal(Decimal(1, 0), True)
        assert not genia_equal(True, make_rational(1, 1))
        assert not genia_equal(False, Decimal(0, 0))


# ---------------------------------------------------------------------------
# 10.2 Float64 bridge, NaN, infinities
# ---------------------------------------------------------------------------


class TestFloat64Bridge:
    def test_finite_float64_bridges_to_exact_by_mathematical_value(self):
        assert genia_equal(Float64(0.5), Rational(1, 2))
        assert genia_equal(Rational(1, 2), Float64(0.5))
        assert genia_equal(Float64(5.0), 5)
        assert genia_equal(5, Float64(5.0))
        assert genia_equal(Float64(0.5), Decimal(5, -1))

    def test_finite_float64_unequal_when_mathematically_different(self):
        assert not genia_equal(Float64(0.5), Rational(1, 3))
        assert not genia_equal(Float64(1.5), 1)

    def test_signed_zero_float64_equals_exact_zero(self):
        assert genia_equal(Float64(0.0), 0)
        assert genia_equal(Float64(-0.0), 0)
        assert genia_equal(Float64(0.0), Float64(-0.0))

    def test_float64_nan_unequal_to_everything_including_itself(self):
        nan = Float64(float("nan"))
        assert not genia_equal(nan, nan)
        assert not genia_equal(nan, 1)
        assert not genia_equal(1, nan)
        assert not genia_equal(nan, Float64(float("nan")))

    def test_matching_float64_infinities_equal_opposite_do_not(self):
        pinf = Float64(float("inf"))
        ninf = Float64(float("-inf"))
        assert genia_equal(pinf, Float64(float("inf")))
        assert genia_equal(ninf, Float64(float("-inf")))
        assert not genia_equal(pinf, ninf)

    def test_float64_bridge_does_not_extend_to_legacy_host_float(self):
        # The decimal-literal bridge (plain Python float) is a distinct,
        # unreconciled domain in this gate (see numeric_values.py's module
        # docstring); genia_equal must not invent a bridge for it ahead of
        # the literal-materialization switch.
        assert not genia_equal(Rational(1, 2), 0.5)
        assert not genia_equal(0.5, Rational(1, 2))
        assert not genia_equal(Decimal(1, 0), 1.0)
        assert not genia_equal(Float64(1.0), 1.0)


# ---------------------------------------------------------------------------
# 10.1/10.2 ordering (compare_numeric)
# ---------------------------------------------------------------------------


class TestCompareNumeric:
    @pytest.mark.parametrize(
        "left,right,expected",
        [
            (Rational(1, 3), Rational(1, 2), -1),
            (Rational(1, 2), Rational(1, 3), 1),
            (Rational(1, 2), Decimal(5, -1), 0),
            (Decimal(1, 0), 2, -1),
            (2, Decimal(1, 0), 1),
            (Float64(0.5), Rational(1, 2), 0),
            (Float64(0.25), Rational(1, 2), -1),
            (1, Float64(1.0), 0),
        ],
    )
    def test_exact_and_float64_ordering(self, left, right, expected):
        assert compare_numeric(left, right) == expected

    def test_nan_is_not_well_ordered(self):
        nan = Float64(float("nan"))
        assert compare_numeric(nan, 1) is None
        assert compare_numeric(1, nan) is None
        assert compare_numeric(nan, nan) is None

    def test_infinities_order_against_finite_values(self):
        pinf = Float64(float("inf"))
        ninf = Float64(float("-inf"))
        assert compare_numeric(ninf, Rational(-1, 1_000_000)) == -1
        assert compare_numeric(pinf, 10**30) == 1
        assert compare_numeric(ninf, pinf) == -1
        assert compare_numeric(pinf, pinf) == 0


# ---------------------------------------------------------------------------
# 10.3 map-key equivalence
# ---------------------------------------------------------------------------


class TestMapKeyEquivalence:
    def test_integer_and_mathematically_equal_decimal_share_a_key(self):
        assert canonical_map_key(1) == canonical_map_key(Decimal(1, 0))
        assert canonical_map_key(Decimal(1, 0)) == canonical_map_key(1)

    def test_mathematically_equal_exact_values_share_a_key_across_kinds(self):
        assert canonical_map_key(Rational(1, 2)) == canonical_map_key(Decimal(5, -1))
        assert canonical_map_key(Float64(0.5)) == canonical_map_key(Rational(1, 2))
        assert canonical_map_key(Float64(5.0)) == canonical_map_key(5)

    def test_mathematically_unequal_values_have_different_keys(self):
        assert canonical_map_key(Rational(1, 3)) != canonical_map_key(Rational(1, 2))
        assert canonical_map_key(Decimal(1, 0)) != canonical_map_key(2)

    def test_float64_nan_is_not_a_legal_map_key(self):
        with pytest.raises(TypeError):
            canonical_map_key(Float64(float("nan")))

    def test_float64_infinity_keys_are_self_consistent_but_distinct_from_legacy_float(self):
        pinf_key = canonical_map_key(Float64(float("inf")))
        assert pinf_key == canonical_map_key(Float64(float("inf")))
        assert pinf_key != canonical_map_key(float("inf"))

    def test_genia_map_collapses_mathematically_equal_numeric_keys(self):
        # End-to-end: GeniaMap.put/get route through canonical_map_key, so an
        # Integer key and a mathematically-equal Decimal/Rational/Float64 key
        # must be interchangeable (contract 10.3 + R18 map-key identity).
        m = GeniaMap().put(1, "a")
        m = m.put(Decimal(1, 0), "b")  # replaces the same key
        assert m.get(1) == "b"
        assert m.get(Rational(2, 2)) == "b"
        assert m.get(Float64(1.0)) == "b"
        assert len(m._entries) == 1

        m2 = GeniaMap().put(Rational(1, 2), "half")
        assert m2.get(Decimal(5, -1)) == "half"
        assert m2.get(Float64(0.5)) == "half"
        assert is_none(m2.get(Rational(1, 3)))


class TestBooleansStillDistinctFromNumberKeys:
    def test_bool_key_never_collapses_with_decimal_or_rational(self):
        assert canonical_map_key(True) != canonical_map_key(Decimal(1, 0))
        assert canonical_map_key(False) != canonical_map_key(Decimal(0, 0))
