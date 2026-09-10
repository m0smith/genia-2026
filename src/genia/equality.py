"""Canonical Genia value equality (R18).

Genia has exactly one semantic equality relation. ``genia_equal`` *is* that
relation for the Python reference host. It is not user-overloadable and it adds
no public Genia surface: ``==`` and ``!=`` are routed here, and later R18 slices
route the remaining equality-like surfaces here too rather than reimplementing
any rule.

Two properties of this module are load-bearing for portability, and both are
requirements of the approved contract
(``docs/design/r18-portable-value-equality-contract.md``):

1. **Explicit semantic-kind dispatch.** There is no terminal
   ``return left == right`` for unrecognized objects. Host-language equality is
   not the language specification, so a future runtime class cannot become a
   structural or identity Genia value merely by inheriting a host default.

2. **Booleans are decided before numbers.** In this host ``bool`` is a subclass
   of ``int``. Testing booleans first is what makes ``true == 1`` false. The
   rule is host-independent and written in the contract; only this defence
   against it is host-specific.

Equality is pure: it reads fields already present on its operands. It performs
no IO, acquires nothing, invokes no user code, consumes no Seq or Flow,
dereferences no Ref, and inspects no Cell/Process/provider state. Values whose
contents must never be traversed terminate recursion instead.

Issue: #791 (E18-1). Later slices: #792 map equality and legal keys, #793
identity/opaque-token/protected families, #794 the remaining equality-like
surfaces.
"""

from __future__ import annotations

import math
from typing import Any

from .sheet import GeniaSheet
from .values import (
    GeniaBytes,
    GeniaCell,
    GeniaConfigProvider,
    GeniaDeclassificationAuthority,
    GeniaFlow,
    GeniaFormat,
    GeniaMap,
    GeniaNamedPattern,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaOutputSink,
    GeniaPair,
    GeniaProcess,
    GeniaProtected,
    GeniaPythonHandle,
    GeniaRef,
    GeniaRepresented,
    GeniaRng,
    GeniaSeq,
    GeniaStdinSource,
    GeniaSymbol,
    GeniaZipEntry,
    ModuleValue,
)

__all__ = ["genia_equal"]


# ---------------------------------------------------------------------------
# transitional families
# ---------------------------------------------------------------------------
#
# TRANSITIONAL (E18-1 only). These families are recognized here but their
# semantics belong to later R18 slices. Until their owning issue lands they keep
# exactly the behavior they had before R18 so this slice regresses nothing and
# pre-implements nothing.
#
# Each owning issue removes the entries it takes over; after #793 this whole
# section and `_deferred_equal` are deleted. This is one relation with
# explicitly deferred branches, not a second equality mechanism, and it is not a
# generic host fallback: only the named kinds below can reach it.

# Owned by #792 (map equality, legal keys, key equivalence).
_DEFERRED_TO_MAP_SLICE: tuple[type, ...] = (GeniaMap,)

# Owned by #793 (identity-bearing, opaque-token, and protected equality).
_DEFERRED_TO_IDENTITY_SLICE: tuple[type, ...] = (
    GeniaProtected,
    GeniaDeclassificationAuthority,
    GeniaConfigProvider,
    GeniaNamedPattern,
    ModuleValue,
    GeniaPythonHandle,
    GeniaRef,
    GeniaCell,
    GeniaProcess,
    GeniaSeq,
    GeniaFlow,
    GeniaOutputSink,
    GeniaStdinSource,
)

# Also owned by #793, matched by class name so this module does not import the
# model/retrieval/callable/lifecycle layers and cannot create an import cycle.
_DEFERRED_TO_IDENTITY_SLICE_BY_NAME = frozenset(
    {
        "GeniaFunction",
        "GeniaFunctionGroup",
        "GeniaModel",
        "GeniaModelProvider",
        "GeniaEmbedProvider",
        "GeniaEmbedder",
        "GeniaIndexHandle",
        "GeniaIndexProvider",
        "GeniaIndexer",
        "GeniaRetrieveProvider",
        "GeniaRetriever",
        "GeniaRerankProvider",
        "GeniaReranker",
        "GeniaMetaEnv",
        "GeniaPromise",
        "LifecycleDefinition",
        "LifecycleScope",
        "LifecycleContext",
    }
)


def _is_deferred(value: Any) -> bool:
    if isinstance(value, _DEFERRED_TO_MAP_SLICE):
        return True
    if isinstance(value, _DEFERRED_TO_IDENTITY_SLICE):
        return True
    return type(value).__name__ in _DEFERRED_TO_IDENTITY_SLICE_BY_NAME


def _deferred_equal(left: Any, right: Any) -> bool:
    """TRANSITIONAL: preserve pre-R18 behavior for families owned by #792/#793."""
    return bool(left == right)


# ---------------------------------------------------------------------------
# numeric
# ---------------------------------------------------------------------------


def _int_equals_float(integer: int, number: float) -> bool:
    """Exact integer/float equality.

    Deliberately never converts ``integer`` to a float: R17 integers are
    arbitrary precision and such a conversion would lose precision or overflow.
    Instead the float — which is finite and integral, and therefore exactly an
    integer — is converted upward, and two exact integers are compared.
    """
    if not math.isfinite(number):
        return False
    if not number.is_integer():
        return False
    return integer == int(number)


def _numeric_equal(left: Any, right: Any) -> bool:
    left_is_int = isinstance(left, int)
    right_is_int = isinstance(right, int)
    left_is_float = isinstance(left, float)
    right_is_float = isinstance(right, float)

    if left_is_int and right_is_int:
        return left == right
    if left_is_float and right_is_float:
        # NaN is unequal to everything, including itself. Every other case is
        # IEEE-754 equality, which already gives 0.0 == -0.0 and matching
        # infinities equal.
        if math.isnan(left) or math.isnan(right):
            return False
        return left == right
    if left_is_int and right_is_float:
        return _int_equals_float(left, right)
    if left_is_float and right_is_int:
        return _int_equals_float(right, left)
    return False


# ---------------------------------------------------------------------------
# the relation
# ---------------------------------------------------------------------------


def genia_equal(left: Any, right: Any) -> bool:
    """Return whether two Genia values are equal under the one Genia relation."""

    # 1. Booleans are their own semantic kind and are decided first, before any
    #    numeric branch, because this host represents them as integers.
    left_is_bool = isinstance(left, bool)
    right_is_bool = isinstance(right, bool)
    if left_is_bool or right_is_bool:
        return left_is_bool and right_is_bool and left is right

    # 2. Numbers, including the only cross-kind bridge in R18.
    if isinstance(left, (int, float)):
        return _numeric_equal(left, right)
    if isinstance(right, (int, float)):
        return False

    # 3. Strings and symbols are distinct kinds and never compare across.
    if isinstance(left, str):
        return isinstance(right, str) and left == right
    if isinstance(right, str):
        return False

    if isinstance(left, GeniaSymbol):
        return isinstance(right, GeniaSymbol) and left.name == right.name
    if isinstance(right, GeniaSymbol):
        return False

    # 4. Families whose semantics belong to a later R18 slice.
    if _is_deferred(left) or _is_deferred(right):
        if _is_deferred(left) and _is_deferred(right):
            return _deferred_equal(left, right)
        return False

    # 5. Structural values: compare named semantic fields recursively. Each kind
    #    names its own fields; no generic field reflection is used, so adding a
    #    host-level field cannot silently change Genia equality.
    if isinstance(left, list):
        if not isinstance(right, list) or len(left) != len(right):
            return False
        return all(genia_equal(a, b) for a, b in zip(left, right))
    if isinstance(right, list):
        return False

    if isinstance(left, GeniaPair):
        return (
            isinstance(right, GeniaPair)
            and genia_equal(left.head, right.head)
            and genia_equal(left.tail, right.tail)
        )
    if isinstance(right, GeniaPair):
        return False

    # Outcomes compare by exact constructor kind first, so some/none/err never
    # compare equal to one another merely because their contents resemble.
    if isinstance(left, GeniaOptionSome):
        return (
            isinstance(right, GeniaOptionSome)
            and genia_equal(left.value, right.value)
            and genia_equal(left.context, right.context)
        )
    if isinstance(left, GeniaOptionNone):
        return (
            isinstance(right, GeniaOptionNone)
            and genia_equal(left.reason, right.reason)
            and genia_equal(left.context, right.context)
        )
    if isinstance(left, GeniaOptionErr):
        return (
            isinstance(right, GeniaOptionErr)
            and genia_equal(left.reason, right.reason)
            and genia_equal(left.context, right.context)
        )
    if isinstance(right, (GeniaOptionSome, GeniaOptionNone, GeniaOptionErr)):
        return False

    # Representation layers stay ordered: facet identity plus the carried value,
    # so nesting order and duplicate layers participate in equality.
    if isinstance(left, GeniaRepresented):
        return (
            isinstance(right, GeniaRepresented)
            and left.facet == right.facet
            and genia_equal(left.value, right.value)
        )
    if isinstance(right, GeniaRepresented):
        return False

    if isinstance(left, GeniaRng):
        return isinstance(right, GeniaRng) and left.state == right.state
    if isinstance(right, GeniaRng):
        return False

    if isinstance(left, GeniaBytes):
        return isinstance(right, GeniaBytes) and left.value == right.value
    if isinstance(right, GeniaBytes):
        return False

    if isinstance(left, GeniaZipEntry):
        return (
            isinstance(right, GeniaZipEntry)
            and left.name == right.name
            and genia_equal(left.data, right.data)
        )
    if isinstance(right, GeniaZipEntry):
        return False

    if isinstance(left, GeniaFormat):
        return isinstance(right, GeniaFormat) and _format_equal(left, right)
    if isinstance(right, GeniaFormat):
        return False

    if isinstance(left, GeniaSheet):
        return isinstance(right, GeniaSheet) and _sheet_equal(left, right)
    if isinstance(right, GeniaSheet):
        return False

    # The host absence sentinel is still used internally in this host. It is
    # classified explicitly so it stays out of the unclassified terminal and
    # keeps its existing behavior.
    if left is None or right is None:
        return left is None and right is None

    # 6. Unclassified terminal. An object reaching here matches no Genia
    #    semantic kind and is host leakage. It is compared by logical identity
    #    only — never by host equality, which would make the host language the
    #    specification, and never by raising, which would add an error surface
    #    this slice's contract excludes.
    return left is right


def _format_equal(left: GeniaFormat, right: GeniaFormat) -> bool:
    if left.template != right.template or left.tag != right.tag:
        return False
    if left.pieces is None or right.pieces is None:
        return left.pieces is None and right.pieces is None
    if len(left.pieces) != len(right.pieces):
        return False
    return all(genia_equal(a, b) for a, b in zip(left.pieces, right.pieces))


def _sheet_equal(left: GeniaSheet, right: GeniaSheet) -> bool:
    # Sheets are defined by *ordered* semantic columns, so comparison is
    # positional rather than set-like.
    if left.row_count != right.row_count:
        return False
    if len(left.columns) != len(right.columns):
        return False
    for (left_name, left_values), (right_name, right_values) in zip(
        left.columns, right.columns
    ):
        if not genia_equal(left_name, right_name):
            return False
        if len(left_values) != len(right_values):
            return False
        if not all(genia_equal(a, b) for a, b in zip(left_values, right_values)):
            return False
    return True
