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

from .numeric_runtime import GeniaDecimal, GeniaRational, decimal_as_fraction
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

__all__ = ["genia_equal", "canonical_map_key"]


# ---------------------------------------------------------------------------
# identity-bearing runtime values
# ---------------------------------------------------------------------------
#
# R18 (#793). These values denote runtime entities, so they compare only by
# logical runtime entity identity. Equivalent visible state, configuration, or
# construction arguments never imply equality, and comparison never
# dereferences, invokes, advances, or inspects the entity behind them.
#
# Classifying them explicitly deliberately overrides host dataclass equality,
# which compares fields for several of these types — `ModuleValue`'s generated
# equality compares its entire export table, which is exactly the
# "equivalent visible state implies equality" error the contract forbids.

_IDENTITY_BEARING: tuple[type, ...] = (
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

# Matched by class name so this module does not import the
# model/retrieval/callable/lifecycle layers and cannot create an import cycle.
_IDENTITY_BEARING_BY_NAME = frozenset(
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


def _is_identity_bearing(value: Any) -> bool:
    if isinstance(value, _IDENTITY_BEARING):
        return True
    if type(value).__name__ in _IDENTITY_BEARING_BY_NAME:
        return True
    # Plain host callables (functions, lambdas, bound methods) denote executable
    # behavior, so they are classified deliberately rather than being left to
    # the unclassified terminal.
    return callable(value)


# ---------------------------------------------------------------------------
# opaque semantic tokens
# ---------------------------------------------------------------------------
#
# R18 (#793). An opaque semantic token represents an immutable semantic fact
# whose equality is meaningful but whose representation is not public.
#
# R18 adds no public token class, value, minting API, or syntax, and implements
# no storage or `Revision`. What it adds is the adapter shape the engine uses
# when a token type eventually exists: a token exposes three immutable hidden
# identities and the engine compares them.
#
# The token supplies DATA, never BEHAVIOR. The engine never calls a comparator,
# equality method, issuer, provider, or callback offered by the token. That
# distinction is what lets future built-in and user-defined token domains join
# this family while `==` stays non-overloadable.

_TOKEN_EQUALITY_ATTRIBUTE = "__genia_token_equality__"


def _token_identity(value: Any) -> Any:
    """Return a token's hidden (domain, provenance, semantic) identities, or None."""
    return getattr(value, _TOKEN_EQUALITY_ATTRIBUTE, None)


# ---------------------------------------------------------------------------
# numeric
# ---------------------------------------------------------------------------


def _is_exact_numeric_kind(value: Any) -> bool:
    """True for Integer/Decimal/Rational -- the R22 exact family."""
    return isinstance(value, (int, GeniaDecimal, GeniaRational))


def _exact_fraction(value: Any) -> tuple[int, int]:
    """Return (numerator, denominator > 0) for an exact-family value.

    Caller guarantees ``value`` satisfies ``_is_exact_numeric_kind``.
    """
    if isinstance(value, int):
        return value, 1
    if isinstance(value, GeniaDecimal):
        return decimal_as_fraction(value)
    return value.numerator, value.denominator  # GeniaRational


def _numeric_equal(left: Any, right: Any) -> bool:
    """Equality across Integer, Decimal, Rational, and Float64 (R22 contract
    section 10.1/10.2). Every exact-family pair (including plain
    Integer/Integer) is decided by exact-fraction cross-multiplication --
    R17 integers are never narrowed and no exact operand is ever rounded to
    a host float. The Float64 bridge decomposes the float's own exact
    represented value (never rounds the exact side to Float64) via
    ``float.as_integer_ratio()``, which CPython guarantees is exact.
    """
    left_is_float = isinstance(left, float)
    right_is_float = isinstance(right, float)
    left_is_exact = _is_exact_numeric_kind(left)
    right_is_exact = _is_exact_numeric_kind(right)

    if not (left_is_float or left_is_exact) or not (right_is_float or right_is_exact):
        return False

    if left_is_float and right_is_float:
        # NaN is unequal to everything, including itself. Every other case is
        # IEEE-754 equality, which already gives 0.0 == -0.0 and matching
        # infinities equal.
        if math.isnan(left) or math.isnan(right):
            return False
        return left == right

    if left_is_float or right_is_float:
        float_value = left if left_is_float else right
        exact_value = right if left_is_float else left
        if math.isnan(float_value) or math.isinf(float_value):
            # No exact value is ever NaN or infinite, so neither can equal one.
            return False
        float_numerator, float_denominator = float_value.as_integer_ratio()
        exact_numerator, exact_denominator = _exact_fraction(exact_value)
        return float_numerator * exact_denominator == exact_numerator * float_denominator

    left_numerator, left_denominator = _exact_fraction(left)
    right_numerator, right_denominator = _exact_fraction(right)
    return left_numerator * right_denominator == right_numerator * left_denominator


# ---------------------------------------------------------------------------
# the relation
# ---------------------------------------------------------------------------


def genia_equal(left: Any, right: Any) -> bool:
    """Return whether two Genia values are equal under the one Genia relation."""

    # 0. The three families that must never be compared by contents, checked
    #    before every structural branch so recursion can never reach inside one.
    #
    #    Protected carriers come first so no other branch — present or future —
    #    can observe a carrier before the identity-only rule applies.
    if isinstance(left, GeniaProtected) or isinstance(right, GeniaProtected):
        # Carrier identity only. The payload is never read, so equality cannot
        # disclose whether two independently acquired carriers hold equal
        # secrets. Revealing carrier identity is permitted; revealing payload
        # equality is not.
        return left is right

    left_token = _token_identity(left)
    right_token = _token_identity(right)
    if left_token is not None or right_token is not None:
        if left_token is None or right_token is None:
            return False
        # Equal iff domain, provenance and semantic identities are all equal.
        # The components are compared with this same relation, so the comparison
        # is portable rather than delegated to host equality. No issuer is
        # contacted and no token-supplied comparator is consulted.
        if len(left_token) != len(right_token):
            return False
        return all(
            genia_equal(a, b) for a, b in zip(left_token, right_token)
        )

    if _is_identity_bearing(left) or _is_identity_bearing(right):
        return left is right

    # 1. Booleans are their own semantic kind and are decided first, before any
    #    numeric branch, because this host represents them as integers.
    left_is_bool = isinstance(left, bool)
    right_is_bool = isinstance(right, bool)
    if left_is_bool or right_is_bool:
        return left_is_bool and right_is_bool and left is right

    # 2. Numbers, including the only cross-kind bridge in R18.
    if isinstance(left, (int, float, GeniaDecimal, GeniaRational)):
        return _numeric_equal(left, right)
    if isinstance(right, (int, float, GeniaDecimal, GeniaRational)):
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

    # 4. Structural values: compare named semantic fields recursively. Each kind
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

    if isinstance(left, GeniaMap):
        return isinstance(right, GeniaMap) and _map_equal(left, right)
    if isinstance(right, GeniaMap):
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


_MAP_ENTRY_MISSING = object()


def _map_equal(left: GeniaMap, right: GeniaMap) -> bool:
    """Map equality is equality of mappings, not of insertion history.

    Entries are matched by canonical key identity, which *is* Genia key
    equality, so iterating one side and looking up the other is exactly "every
    mapping in one has an equal key in the other". Order is ignored by
    construction, and the length check makes the one-directional scan
    sufficient.
    """
    left_entries = left._entries
    right_entries = right._entries
    if len(left_entries) != len(right_entries):
        return False
    for canonical_key, (_, left_value) in left_entries.items():
        entry = right_entries.get(canonical_key, _MAP_ENTRY_MISSING)
        if entry is _MAP_ENTRY_MISSING:
            return False
        if not genia_equal(left_value, entry[1]):
            return False
    return True


# ---------------------------------------------------------------------------
# legal map keys
# ---------------------------------------------------------------------------
#
# R18 (#792). Map key identity is exactly Genia `==` for legal keys. This is the
# only place that decides key legality and key identity, so the two can never
# drift apart.
#
# Each canonical identity is a tuple tagged by Genia semantic kind, which is what
# stops a host container from merging two kinds — before R18 the host dictionary
# merged `true` with `1`. The identity is internal: it is not a public hash API
# and is not reachable from Genia source.

_KEY_NAN_MESSAGE = "map key must equal itself; NaN is not a legal map key"


def _key_error(message: str) -> TypeError:
    return TypeError(message)


def _reduced_fraction(numerator: int, denominator: int) -> tuple[int, int]:
    """Reduce (numerator, denominator > 0) to lowest terms.

    Used only for GeniaDecimal map keys: GeniaDecimal's own canonical form
    (coefficient/exponent) is unique per value but its fraction form is not
    always in lowest terms (e.g. 0.5 is coefficient=5, exponent=-1, i.e.
    5/10), while float.as_integer_ratio() and GeniaRational are always
    already reduced -- this brings all three into one comparable form.
    """
    divisor = math.gcd(numerator, denominator)
    return numerator // divisor, denominator // divisor


def canonical_map_key(value: Any) -> Any:
    """Return the internal canonical identity for a legal map key.

    Raises ``TypeError`` for any key that is not legal, including NaN and any
    otherwise-legal structural key containing NaN at any depth.
    """
    # Booleans first, for the same reason as in `genia_equal`: this host
    # represents them as integers, and they must not share a numeric identity.
    if isinstance(value, bool):
        return ("bool", value)

    if isinstance(value, int):
        return ("num", value)

    if isinstance(value, float):
        if math.isnan(value):
            raise _key_error(_KEY_NAN_MESSAGE)
        if not math.isfinite(value):
            # The two infinities keep exact float identity, distinct by sign.
            # They denote no finite exact-fraction value, so they cannot and
            # must not collide with any Integer/Decimal/Rational key.
            return ("float-infinite", value)
        if value.is_integer():
            # An integer and an exactly equal integral float are one key. The
            # float is converted upward so an arbitrary-precision integer key is
            # never narrowed. This also collapses 0.0 with -0.0, as required.
            return ("num", int(value))
        # A non-integral finite float keys on its own exact represented
        # value (R22 contract section 10.3), in the same reduced-fraction
        # form GeniaDecimal/GeniaRational below use, so an equal-valued
        # Decimal/Rational/float share one key. float.as_integer_ratio()
        # is CPython's exact, already-reduced (numerator, denominator).
        return ("num-fraction", *value.as_integer_ratio())

    if isinstance(value, GeniaDecimal):
        numerator, denominator = decimal_as_fraction(value)
        if denominator == 1:
            # An Integer and a mathematically-integral Decimal share one key,
            # by the same "num" bucket the Integer/float case above already
            # uses. R22 contract section 10.3: equal legal numeric keys have
            # identical internal key/hash equivalence.
            return ("num", numerator)
        return ("num-fraction", *_reduced_fraction(numerator, denominator))

    if isinstance(value, GeniaRational):
        # Already gcd-reduced with denominator > 1 by construction
        # (numeric_runtime.rational_from_integers never returns a
        # GeniaRational otherwise), so no further reduction is needed --
        # this is directly comparable to the float/Decimal fraction keys.
        return ("num-fraction", value.numerator, value.denominator)

    if isinstance(value, str):
        return ("string", value)

    if isinstance(value, GeniaSymbol):
        return ("symbol", value.name)

    if isinstance(value, GeniaPair):
        return ("pair", canonical_map_key(value.head), canonical_map_key(value.tail))

    if isinstance(value, list):
        return ("list", tuple(canonical_map_key(item) for item in value))

    if isinstance(value, GeniaRepresented):
        return ("represented", value.facet, canonical_map_key(value.value))

    # Families with their own established rejection messages. Protected carriers
    # are rejected without inspecting or mentioning their payload.
    if isinstance(value, GeniaProtected):
        raise _key_error("protected values cannot be map keys")
    if isinstance(value, GeniaDeclassificationAuthority):
        raise _key_error("declassification authority cannot be a map key")
    if type(value).__name__ == "GeniaIndexHandle":
        raise _key_error("index handles cannot be map keys")

    # Host-internal accommodations. The approved R18 contract is explicit that
    # these are "not authority to introduce a new public tuple/null key kind", so
    # they keep working for internal callers but are not public key families and
    # are not documented as such.
    if value is None:
        return ("host-none",)
    if isinstance(value, tuple):
        return ("host-tuple", tuple(canonical_map_key(item) for item in value))

    raise _key_error(f"map key type is not supported: {type(value).__name__}")


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
