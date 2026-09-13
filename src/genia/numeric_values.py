"""Exact numeric runtime value model (issue #838 slice 2).

This module implements the *value model* portion of
``docs/design/exact-numeric-model-contract.md`` sections 3, 4, and 5:
canonical runtime representations for Decimal and Rational, and an explicit
Float64 tag, independent of any host-native ``int``/``float`` conflation.

Scope boundary (see PR #839 discussion for issue #838):

- Integer remains plain Python ``int`` (R17 arbitrary precision is already
  satisfied by ``int``; no wrapper type is introduced).
- ``Decimal`` and ``Rational`` are new frozen value types with canonical
  construction per contract sections 3 and 4.
- ``Float64`` is a new explicit tag distinguishing an approximate binary64
  value from any exact numeric value; earlier code paths never produced this
  type since decimal-classified source literals materialized as Python
  ``float`` through the temporary ``materialize_legacy_numeric`` bridge
  (``src/genia/numeric_literals.py``).
- This module intentionally implements **no** arithmetic operators,
  cross-kind equality/ordering, display/debug rendering, JSON boundary
  behavior, or ``exact()``/``float64()``/``rational()`` conversion builtins.
  Those are separately staged follow-on slices (contract sections 6-14) and
  are not implemented here. Wiring these types into the live evaluator ahead
  of that arithmetic/equality/rendering work would regress the existing
  shared-spec suite, which already relies on decimal-classified literals
  behaving like Python ``float`` for cross-kind equality (``1 == 1.0``),
  arithmetic (``0.0 - pinf``), NaN/signed-zero semantics, and JSON/format
  rendering (see e.g. ``spec/eval/r18-equality-*.yaml``,
  ``spec/eval/json-representation-number-boundaries.yaml``). Until those
  follow-on slices land, ``materialize_legacy_numeric`` remains the live
  bridge and is left unchanged.

Booleans are never numbers: :func:`is_numeric_value` explicitly excludes
``bool`` even though Python's ``bool`` is an ``int`` subclass, per contract
section 10 ("Booleans are not numbers").
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal as _PyDecimal
from math import gcd
from typing import Any


@dataclass(frozen=True, slots=True)
class Decimal:
    """An exact base-10 value ``coefficient * 10**exponent``.

    Canonicalization (contract section 3):

    - zero canonicalizes to coefficient ``0``, exponent ``0``
    - otherwise every trailing base-10 zero is removed from the absolute
      coefficient and the exponent is increased by the count removed
    - the sign is carried by the coefficient
    - lexical scale (e.g. ``1.0`` vs ``1.00``) is not retained
    """

    coefficient: int
    exponent: int

    def __post_init__(self) -> None:
        if not isinstance(self.coefficient, int) or isinstance(self.coefficient, bool):
            raise TypeError("Decimal coefficient must be an int")
        if not isinstance(self.exponent, int) or isinstance(self.exponent, bool):
            raise TypeError("Decimal exponent must be an int")
        coefficient, exponent = self.coefficient, self.exponent
        if coefficient == 0:
            object.__setattr__(self, "coefficient", 0)
            object.__setattr__(self, "exponent", 0)
            return
        sign = -1 if coefficient < 0 else 1
        magnitude = abs(coefficient)
        while magnitude % 10 == 0:
            magnitude //= 10
            exponent += 1
        object.__setattr__(self, "coefficient", sign * magnitude)
        object.__setattr__(self, "exponent", exponent)

    @classmethod
    def of(cls, coefficient: int, exponent: int) -> "Decimal":
        """Construct a canonical Decimal from a coefficient/exponent pair."""
        return cls(coefficient, exponent)

    @classmethod
    def from_payload(cls, coefficient: str, exponent: str) -> "Decimal":
        """Construct from the tagged Core IR/AST string payload."""
        return cls(int(coefficient), int(exponent))

    def to_py_decimal(self) -> _PyDecimal:
        """Return an equal ``decimal.Decimal`` (a host implementation tool)."""
        return _PyDecimal(self.coefficient).scaleb(self.exponent)

    def is_integral(self) -> bool:
        return self.exponent >= 0


@dataclass(frozen=True, slots=True)
class Rational:
    """An exact reduced ratio of arbitrary-precision integers.

    Canonicalization (contract section 4): denominator must be nonzero,
    numerator/denominator are divided by their positive gcd, the sign is
    carried by the numerator, and the denominator is positive. A reduced
    denominator of ``1`` canonicalizes to Integer — callers should use
    :func:`make_rational` rather than the constructor directly so that
    collapse is applied.
    """

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if not isinstance(self.numerator, int) or isinstance(self.numerator, bool):
            raise TypeError("Rational numerator must be an int")
        if not isinstance(self.denominator, int) or isinstance(self.denominator, bool):
            raise TypeError("Rational denominator must be an int")
        if self.denominator == 0:
            raise ValueError("Rational denominator must be nonzero")
        numerator, denominator = self.numerator, self.denominator
        if denominator < 0:
            numerator, denominator = -numerator, -denominator
        divisor = gcd(numerator, denominator) or 1
        object.__setattr__(self, "numerator", numerator // divisor)
        object.__setattr__(self, "denominator", denominator // divisor)


def make_rational(numerator: int, denominator: int) -> "int | Rational":
    """Build a canonical Rational, collapsing a denominator of 1 to Integer."""
    value = Rational(numerator, denominator)
    if value.denominator == 1:
        return value.numerator
    return value


@dataclass(frozen=True, slots=True)
class Float64:
    """An explicit IEEE-754 binary64 approximate value.

    This is a distinct runtime tag from Python ``float`` used elsewhere in
    the codebase; it exists so a later slice can make "explicit Float64" a
    real, checkable domain instead of overloading host ``float`` for both
    "someone explicitly asked for Float64" and "a Decimal literal happened
    to be represented as a host float," which is what the current
    ``materialize_legacy_numeric`` bridge still does.
    """

    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, float):
            raise TypeError("Float64 value must be a host float")

    def is_nan(self) -> bool:
        return self.value != self.value  # noqa: PLR0124 - explicit NaN check

    def bits_hex(self) -> str:
        """Exact IEEE-754 binary64 bits, 16 lowercase hex digits (contract 2.2/11)."""
        import struct

        (raw,) = struct.unpack(">Q", struct.pack(">d", self.value))
        return f"{raw:016x}"


ExactNumeric = (int, Decimal, Rational)
NumericValue = (int, Decimal, Rational, Float64)


def is_numeric_value(value: Any) -> bool:
    """True for Integer/Decimal/Rational/Float64; false for bool and non-numbers.

    Booleans are not numbers (contract section 10), even though Python's
    ``bool`` is an ``int`` subclass.
    """
    if isinstance(value, bool):
        return False
    return isinstance(value, NumericValue)


def is_exact_numeric_value(value: Any) -> bool:
    """True for Integer/Decimal/Rational; false for Float64, bool, non-numbers."""
    if isinstance(value, bool):
        return False
    return isinstance(value, ExactNumeric)


def materialize_exact_numeric(value: Any) -> Any:
    """Build a real runtime value from a tagged numeric literal payload.

    Accepts the same ``{"kind": "integer"|"decimal", ...}`` payload (or the
    ``NumericLiteral`` AST descriptor) produced by
    ``src/genia/numeric_literals.py``. This is the exact-value counterpart
    to ``materialize_legacy_numeric`` and is not yet wired into evaluation
    (see module docstring); it exists so this value model has a tested,
    concrete construction path from the portable literal payload ahead of
    the evaluator being switched over in a later slice.
    """
    from .numeric_literals import NumericLiteral, is_portable_numeric_payload

    if isinstance(value, NumericLiteral):
        value = value.portable_payload()
    if not is_portable_numeric_payload(value):
        raise ValueError(f"not a portable numeric literal payload: {value!r}")
    if value["kind"] == "integer":
        return int(value["digits"])
    return Decimal.from_payload(value["coefficient"], value["exponent"])
