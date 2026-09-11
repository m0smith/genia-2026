"""E18-2 (#792) focused evidence for map equality and the legal-key relation.

Shared `spec/eval/r18-map-*.yaml` and `spec/error/r18-map-key-*.yaml` cases carry
the portable evidence. These tests cover the internal canonicalizer directly, the
legality boundary for families that are awkward to construct from source, and the
R17 order guarantees that must survive the key-identity change.

Issue contract: .genia/process/tmp/handoffs/e18-2-map-equality-legal-keys/01-contract.md
"""

from __future__ import annotations

import math

import pytest

from genia.equality import canonical_map_key, genia_equal
from genia.values import (
    GeniaBytes,
    GeniaMap,
    GeniaOptionSome,
    GeniaPair,
    GeniaProtected,
    GeniaRepresented,
    GeniaSymbol,
    symbol,
)


def build(pairs: list[tuple[object, object]]) -> GeniaMap:
    result = GeniaMap()
    for key, value in pairs:
        result = result.put(key, value)
    return result


# --------------------------------------------------------------------------
# map equality
# --------------------------------------------------------------------------


def test_equal_content_maps_are_equal_regardless_of_insertion_order() -> None:
    left = build([("x", 1), ("y", 2)])
    right = build([("y", 2), ("x", 1)])
    assert genia_equal(left, right) is True
    assert genia_equal(right, left) is True
    # and the differing R17 orders are still observable on the same values
    assert [k for k, _ in left.items()] == ["x", "y"]
    assert [k for k, _ in right.items()] == ["y", "x"]


def test_maps_differing_in_any_mapping_are_unequal() -> None:
    base = build([("x", 1), ("y", 2)])
    assert genia_equal(base, build([("x", 1), ("y", 3)])) is False
    assert genia_equal(base, build([("x", 1)])) is False
    assert genia_equal(base, build([("x", 1), ("y", 2), ("z", 3)])) is False
    assert genia_equal(base, build([("x", 1), ("z", 2)])) is False


def test_empty_maps_are_equal() -> None:
    assert genia_equal(GeniaMap(), GeniaMap()) is True


def test_map_values_use_the_full_relation() -> None:
    assert genia_equal(build([("k", 1)]), build([("k", 1.0)])) is True
    assert genia_equal(build([("k", True)]), build([("k", 1)])) is False
    assert genia_equal(
        build([("k", GeniaBytes(b"hi"))]), build([("k", GeniaBytes(b"hi"))])
    ) is True
    # nested maps
    assert genia_equal(
        build([("k", build([("n", 1)]))]), build([("k", build([("n", 1)]))])
    ) is True


def test_map_holding_nan_as_a_value_is_not_reflexive() -> None:
    """Not a defect: R18 requires reflexivity of legal keys, not of all values."""
    nan_map = build([("k", math.nan)])
    assert genia_equal(nan_map, nan_map) is False
    assert genia_equal(nan_map, build([("k", math.nan)])) is False


def test_map_is_unequal_to_other_kinds() -> None:
    m = build([("x", 1)])
    assert genia_equal(m, [["x", 1]]) is False
    assert genia_equal(m, "x") is False
    assert genia_equal(m, GeniaOptionSome(1)) is False
    assert genia_equal([["x", 1]], m) is False


def test_cross_kind_equal_keys_make_maps_equal() -> None:
    assert genia_equal(build([(1, "v")]), build([(1.0, "v")])) is True
    assert genia_equal(build([(0.0, "v")]), build([(-0.0, "v")])) is True
    assert genia_equal(build([(True, "v")]), build([(1, "v")])) is False


# --------------------------------------------------------------------------
# canonical key identity
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "left,right",
    [
        (1, 1.0),
        (0.0, -0.0),
        (0, -0.0),
        (2, 2.0),
        ("a", "a"),
        (True, True),
        (GeniaSymbol("s"), GeniaSymbol("s")),
        (GeniaPair(1, 2), GeniaPair(1.0, 2.0)),
        ([1, 2], [1.0, 2.0]),
        (GeniaRepresented("json", 1), GeniaRepresented("json", 1.0)),
    ],
)
def test_equal_keys_share_one_canonical_identity(left: object, right: object) -> None:
    assert genia_equal(left, right) is True, "precondition: keys must be equal"
    assert canonical_map_key(left) == canonical_map_key(right)
    assert hash(canonical_map_key(left)) == hash(canonical_map_key(right))


@pytest.mark.parametrize(
    "left,right",
    [
        (True, 1),
        (False, 0),
        (True, 1.0),
        ("1", 1),
        (GeniaSymbol("a"), "a"),
        (1, 2),
        (1, 1.5),
        ([1], GeniaPair(1, None)),
        (GeniaRepresented("json", 1), 1),
        (GeniaRepresented("json", 1), GeniaRepresented("csv", 1)),
        ([1, 2], [2, 1]),
    ],
)
def test_unequal_keys_never_share_a_canonical_identity(
    left: object, right: object
) -> None:
    assert genia_equal(left, right) is False, "precondition: keys must differ"
    assert canonical_map_key(left) != canonical_map_key(right)


def test_canonical_identity_is_kind_tagged_so_kinds_cannot_merge() -> None:
    """The specific collapse R18 removes: boolean and numeric keys."""
    entries = build([(True, "bool"), (1, "int"), (False, "boolF"), (0, "intZ")])
    assert entries.count() == 4
    assert entries.get(True) == "bool"
    assert entries.get(1) == "int"
    assert entries.get(False) == "boolF"
    assert entries.get(0) == "intZ"


def test_infinities_are_legal_keys_and_distinct_by_sign() -> None:
    entries = build([(math.inf, "pos"), (-math.inf, "neg")])
    assert entries.count() == 2
    assert entries.get(math.inf) == "pos"
    assert entries.get(-math.inf) == "neg"


def test_large_integer_key_is_not_collapsed_with_a_nearby_float() -> None:
    exact = 9007199254740993
    nearby = 9007199254740992.0
    entries = build([(exact, "int"), (nearby, "float")])
    assert entries.count() == 2
    assert entries.get(exact) == "int"
    assert entries.get(nearby) == "float"


# --------------------------------------------------------------------------
# legality boundary
# --------------------------------------------------------------------------


def test_nan_is_not_a_legal_key() -> None:
    with pytest.raises(TypeError):
        canonical_map_key(math.nan)


@pytest.mark.parametrize(
    "key",
    [
        [1, math.nan],
        [1, [2, math.nan]],
        GeniaPair(1, math.nan),
        GeniaPair(math.nan, 1),
        GeniaRepresented("json", math.nan),
        GeniaRepresented("json", [math.nan]),
    ],
)
def test_nested_nan_rejects_the_whole_key(key: object) -> None:
    with pytest.raises(TypeError):
        canonical_map_key(key)


def test_illegal_key_is_rejected_on_every_operation_not_only_insertion() -> None:
    populated = build([("a", 1)])
    for operation in (
        lambda: populated.get(math.nan),
        lambda: populated.has(math.nan),
        lambda: populated.remove(math.nan),
        lambda: populated.put(math.nan, 1),
    ):
        with pytest.raises(TypeError):
            operation()


@pytest.mark.parametrize(
    "key",
    [
        GeniaMap(),
        GeniaOptionSome(1),
        GeniaBytes(b"x"),
    ],
)
def test_non_keyable_families_stay_rejected(key: object) -> None:
    with pytest.raises(TypeError):
        canonical_map_key(key)


def test_protected_values_remain_illegal_keys() -> None:
    protected = GeniaProtected("secret", object(), symbol("purpose"))
    with pytest.raises(TypeError) as excinfo:
        canonical_map_key(protected)
    assert "secret" not in str(excinfo.value), (
        "a key rejection must never disclose a protected payload"
    )


def test_key_rejection_messages_do_not_leak_internal_canonical_forms() -> None:
    for key in (math.nan, [math.nan], GeniaMap()):
        with pytest.raises(TypeError) as excinfo:
            canonical_map_key(key)
        message = str(excinfo.value)
        assert "('" not in message and '("' not in message, (
            f"internal canonical tuple leaked into a diagnostic: {message}"
        )


# --------------------------------------------------------------------------
# R17 order preservation
# --------------------------------------------------------------------------


def test_new_key_appends_to_the_end() -> None:
    entries = build([("a", 1), ("b", 2), ("c", 3)])
    assert [k for k, _ in entries.items()] == ["a", "b", "c"]


def test_replacement_preserves_position() -> None:
    entries = build([("a", 1), ("b", 2)]).put("a", 99)
    assert [k for k, _ in entries.items()] == ["a", "b"]
    assert entries.get("a") == 99


def test_replacement_through_an_equal_cross_kind_key_preserves_position() -> None:
    entries = build([(1, "one"), ("b", "two")]).put(1.0, "ONE")
    assert entries.count() == 2
    assert [v for _, v in entries.items()] == ["ONE", "two"]
    assert entries.get(1) == "ONE"


def test_removal_preserves_remaining_order_and_reinsertion_appends() -> None:
    entries = build([("a", 1), ("b", 2), ("c", 3)])
    removed = entries.remove("a")
    assert [k for k, _ in removed.items()] == ["b", "c"]
    reinserted = removed.put("a", 1)
    assert [k for k, _ in reinserted.items()] == ["b", "c", "a"]


def test_maps_are_persistent_and_operations_do_not_mutate_the_source() -> None:
    original = build([("a", 1)])
    original.put("b", 2)
    original.remove("a")
    assert [k for k, _ in original.items()] == ["a"]
    assert original.count() == 1


# --------------------------------------------------------------------------
# purity
# --------------------------------------------------------------------------


def test_map_equality_does_not_invoke_values() -> None:
    calls: list[object] = []

    def spy(*args: object) -> object:  # pragma: no cover - must not be called
        calls.append(args)
        return None

    genia_equal(build([("k", spy)]), build([("k", spy)]))
    assert calls == []
