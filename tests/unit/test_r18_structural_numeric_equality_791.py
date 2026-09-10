"""E18-1 (#791) focused evidence for the canonical Genia equality relation.

These tests exercise `genia_equal` directly for semantic kinds that are awkward
or impossible to construct from ordinary Genia source, plus the purity and
no-host-fallback rules. Source-reachable behavior is covered portably by the
shared `spec/eval/r18-equality-*.yaml` cases.

Contract: docs/design/r18-portable-value-equality-contract.md
Issue contract: .genia/process/tmp/handoffs/e18-1-structural-numeric-equality/01-contract.md
"""

from __future__ import annotations

import math

import pytest

from genia.equality import genia_equal
from genia.sheet import GeniaSheet
from genia.values import (
    GeniaBytes,
    GeniaFlow,
    GeniaFormat,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaPair,
    GeniaRef,
    GeniaRepresented,
    GeniaRng,
    GeniaSymbol,
    GeniaZipEntry,
)


# --------------------------------------------------------------------------
# numeric matrix
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "left,right,expected",
    [
        # booleans are their own kind
        (True, 1, False),
        (1, True, False),
        (False, 0, False),
        (0, False, False),
        (True, 1.0, False),
        (False, 0.0, False),
        (True, True, True),
        (False, False, True),
        (True, False, False),
        # integers
        (1, 1, True),
        (1, 2, False),
        # exact int/float bridge
        (1, 1.0, True),
        (1.0, 1, True),
        (1, 1.5, False),
        (1.5, 1, False),
        # signed zero
        (0.0, -0.0, True),
        (-0.0, 0.0, True),
        (0, -0.0, True),
        # infinities
        (math.inf, math.inf, True),
        (-math.inf, -math.inf, True),
        (math.inf, -math.inf, False),
        # NaN is never equal, including to itself
        (math.nan, math.nan, False),
        (math.nan, 0.0, False),
        (math.nan, math.inf, False),
    ],
)
def test_numeric_matrix(left: object, right: object, expected: bool) -> None:
    assert genia_equal(left, right) is expected
    assert genia_equal(right, left) is expected, "equality must be symmetric"


def test_nan_identity_does_not_imply_equality() -> None:
    """The same NaN object compared with itself is still unequal.

    A host that shortcuts on identity before comparing values would wrongly
    report true here.
    """
    nan = math.nan
    assert genia_equal(nan, nan) is False
    assert genia_equal([nan], [nan]) is False
    assert genia_equal(GeniaOptionSome(nan), GeniaOptionSome(nan)) is False


def test_int_float_bridge_is_exact_for_large_integers() -> None:
    """The bridge must not convert an arbitrary-precision integer to a float."""
    # first odd integer above 2**53; not representable as binary64
    exact = 9007199254740993
    nearby = 9007199254740992.0
    assert genia_equal(exact, nearby) is False
    assert genia_equal(9007199254740992, nearby) is True

    # far beyond float range: converting the integer to a float would overflow
    huge = 10**400
    assert genia_equal(huge, 1.0) is False
    assert genia_equal(huge, math.inf) is False


def test_non_finite_floats_never_equal_integers() -> None:
    assert genia_equal(0, math.nan) is False
    assert genia_equal(0, math.inf) is False
    assert genia_equal(1, -math.inf) is False


# --------------------------------------------------------------------------
# structural kinds
# --------------------------------------------------------------------------


def test_strings_and_symbols_are_distinct_kinds() -> None:
    assert genia_equal("a", "a") is True
    assert genia_equal(GeniaSymbol("a"), GeniaSymbol("a")) is True
    assert genia_equal(GeniaSymbol("a"), "a") is False
    assert genia_equal("a", GeniaSymbol("a")) is False


def test_lists_compare_by_length_then_elements() -> None:
    assert genia_equal([], []) is True
    assert genia_equal([1, 2], [1, 2.0]) is True
    assert genia_equal([1, 2], [1, 2, 3]) is False
    assert genia_equal([1, [2]], [1, [2]]) is True
    assert genia_equal([True], [1]) is False


def test_pairs_compare_head_and_tail() -> None:
    assert genia_equal(GeniaPair(1, 2), GeniaPair(1, 2.0)) is True
    assert genia_equal(GeniaPair(1, 2), GeniaPair(2, 1)) is False
    assert genia_equal(GeniaPair(1, 2), [1, 2]) is False, "a Pair is not a List"


def test_outcomes_compare_constructor_then_fields() -> None:
    assert genia_equal(GeniaOptionSome(1), GeniaOptionSome(1.0)) is True
    assert genia_equal(GeniaOptionSome(1), GeniaOptionErr(1)) is False
    assert genia_equal(GeniaOptionNone("x"), GeniaOptionErr("x")) is False
    assert genia_equal(GeniaOptionErr("x"), GeniaOptionErr("x")) is True
    assert genia_equal(GeniaOptionSome(1, "ctx"), GeniaOptionSome(1)) is False
    assert genia_equal(GeniaOptionSome(1, "ctx"), GeniaOptionSome(1, "ctx")) is True


def test_represented_values_compare_facet_and_carried_value() -> None:
    assert genia_equal(GeniaRepresented("json", 1), GeniaRepresented("json", 1.0)) is True
    assert genia_equal(GeniaRepresented("json", 1), GeniaRepresented("csv", 1)) is False
    assert genia_equal(GeniaRepresented("json", 1), 1) is False, (
        "a represented value is not its carried value"
    )
    # representation layers are ordered and nesting participates in equality
    inner = GeniaRepresented("json", GeniaRepresented("csv", 1))
    outer = GeniaRepresented("csv", GeniaRepresented("json", 1))
    assert genia_equal(inner, outer) is False


def test_rng_compares_by_deterministic_state() -> None:
    assert genia_equal(GeniaRng(7), GeniaRng(7)) is True
    assert genia_equal(GeniaRng(7), GeniaRng(8)) is False


def test_bytes_compare_by_byte_sequence_not_identity() -> None:
    assert genia_equal(GeniaBytes(b"hi"), GeniaBytes(b"hi")) is True
    assert genia_equal(GeniaBytes(b"hi"), GeniaBytes(b"no")) is False
    assert genia_equal(GeniaBytes(b""), GeniaBytes(b"")) is True


def test_zip_entries_compare_name_and_contents() -> None:
    left = GeniaZipEntry("a.txt", GeniaBytes(b"hi"))
    same = GeniaZipEntry("a.txt", GeniaBytes(b"hi"))
    other_name = GeniaZipEntry("b.txt", GeniaBytes(b"hi"))
    other_data = GeniaZipEntry("a.txt", GeniaBytes(b"no"))
    assert genia_equal(left, same) is True
    assert genia_equal(left, other_name) is False
    assert genia_equal(left, other_data) is False


def test_formats_compare_template_tag_and_pieces() -> None:
    assert genia_equal(GeniaFormat(template="{}"), GeniaFormat(template="{}")) is True
    assert genia_equal(GeniaFormat(template="{}"), GeniaFormat(template="[]")) is False
    assert genia_equal(GeniaFormat(tag="t"), GeniaFormat(tag="t")) is True
    assert genia_equal(GeniaFormat(tag="t"), GeniaFormat(template="t")) is False
    nested = GeniaFormat(pieces=["a", GeniaFormat(template="{}")])
    nested_same = GeniaFormat(pieces=["a", GeniaFormat(template="{}")])
    nested_other = GeniaFormat(pieces=["a", GeniaFormat(template="[]")])
    assert genia_equal(nested, nested_same) is True
    assert genia_equal(nested, nested_other) is False


def test_sheets_compare_ordered_columns_and_cells() -> None:
    left = GeniaSheet(columns=(("a", (1, 2)), ("b", (3, 4))), row_count=2)
    same = GeniaSheet(columns=(("a", (1, 2.0)), ("b", (3, 4))), row_count=2)
    reordered = GeniaSheet(columns=(("b", (3, 4)), ("a", (1, 2))), row_count=2)
    other_cell = GeniaSheet(columns=(("a", (1, 9)), ("b", (3, 4))), row_count=2)
    assert genia_equal(left, same) is True
    assert genia_equal(left, other_cell) is False
    assert genia_equal(left, reordered) is False, "Sheet columns are ordered"


# --------------------------------------------------------------------------
# relation properties
# --------------------------------------------------------------------------


def test_relation_always_returns_a_bool() -> None:
    for left, right in [(1, 1), (1, "a"), ([1], [1]), (GeniaSymbol("a"), 1)]:
        assert isinstance(genia_equal(left, right), bool)


def test_structural_values_are_reflexive_without_nan() -> None:
    values = [
        0,
        -0.0,
        "",
        GeniaSymbol("s"),
        [],
        [1, [2, GeniaSymbol("x")]],
        GeniaPair(1, 2),
        GeniaOptionSome(1),
        GeniaOptionNone("nil"),
        GeniaOptionErr("e"),
        GeniaRepresented("json", [1]),
        GeniaRng(3),
        GeniaBytes(b"x"),
        GeniaZipEntry("n", GeniaBytes(b"x")),
        GeniaFormat(template="{}"),
    ]
    for value in values:
        assert genia_equal(value, value) is True, value


def test_relation_is_deterministic() -> None:
    left = [1, [2, "three"], GeniaOptionSome(4)]
    right = [1, [2, "three"], GeniaOptionSome(4.0)]
    results = {genia_equal(left, right) for _ in range(5)}
    assert results == {True}


# --------------------------------------------------------------------------
# no host-equality fallback
# --------------------------------------------------------------------------


class _HostObjectClaimingEquality:
    """A host object whose host equality says it equals everything."""

    def __eq__(self, other: object) -> bool:  # pragma: no cover - must not be used
        return True

    def __ne__(self, other: object) -> bool:  # pragma: no cover - must not be used
        return False

    __hash__ = None  # type: ignore[assignment]


def test_unrecognized_host_objects_do_not_supply_the_relation() -> None:
    """An unclassified host object compares by logical identity, never by host equality.

    This is the guard against Python `__eq__` quietly becoming the language
    specification for any future runtime class.
    """
    left = _HostObjectClaimingEquality()
    right = _HostObjectClaimingEquality()
    assert genia_equal(left, right) is False
    assert genia_equal(left, left) is True
    assert genia_equal(left, 1) is False


def test_host_object_nested_in_structural_value_does_not_leak_host_equality() -> None:
    left = _HostObjectClaimingEquality()
    right = _HostObjectClaimingEquality()
    assert genia_equal([left], [right]) is False
    assert genia_equal([left], [left]) is True


# --------------------------------------------------------------------------
# purity
# --------------------------------------------------------------------------


def test_equality_does_not_invoke_callables_nested_in_structural_values() -> None:
    calls: list[object] = []

    def spy(*args: object) -> object:  # pragma: no cover - must not be called
        calls.append(args)
        return None

    genia_equal([spy], [spy])
    genia_equal(GeniaOptionSome(spy), GeniaOptionSome(spy))
    assert calls == [], "equality must never invoke a value"


def test_equality_does_not_consume_a_flow_or_seq() -> None:
    """Comparing Flow/Seq values must not pull a single element.

    The families themselves are classified by #793; this asserts the purity
    invariant that already applies: equality must never advance a lazy source,
    directly or through a structural container.
    """
    pulls: list[int] = []

    def counting_source() -> object:
        pulls.append(1)
        yield 1

    left = GeniaFlow(counting_source, label="left")
    right = GeniaFlow(counting_source, label="right")

    genia_equal(left, right)
    genia_equal(left, left)
    genia_equal([left], [right])
    genia_equal(GeniaOptionSome(left), GeniaOptionSome(right))

    assert pulls == [], "equality must not consume a lazy source"
    # and the flows remain usable afterwards
    assert list(left.consume()) == [1]


def test_equality_does_not_dereference_a_ref() -> None:
    """Equality compares Ref values without reading what they refer to."""
    left = GeniaRef([1, 2, 3])
    right = GeniaRef([1, 2, 3])

    # Distinct Refs holding equal contents are not made equal by their contents.
    assert genia_equal(left, right) is False
    assert genia_equal(left, left) is True
    assert genia_equal([left], [right]) is False


def test_equality_does_not_mutate_operands() -> None:
    left = [1, [2, 3]]
    right = [1, [2, 3]]
    assert genia_equal(left, right) is True
    assert left == [1, [2, 3]]
    assert right == [1, [2, 3]]
