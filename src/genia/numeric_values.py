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
from math import floor as _math_floor
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


class NumericMisuseError(ValueError):
    """Deterministic numeric misuse (contract section 17).

    Raised for exact/Float64 division or remainder by zero and for mixed
    exact/Float64 arithmetic. Never a bare Python ``ZeroDivisionError`` or a
    host-dependent exception: callers translate this into the portable
    Genia error surface (see ``evaluator.py``'s ``eval_binary``/unary-minus
    dispatch), not a raw host traceback.
    """


def _decimal_parts(value: int | "Decimal") -> tuple[int, int]:
    if isinstance(value, Decimal):
        return value.coefficient, value.exponent
    return value, 0


def _as_fraction(value: "int | Decimal | Rational") -> tuple[int, int]:
    """Return ``(numerator, denominator)`` with denominator > 0."""
    if isinstance(value, Rational):
        return value.numerator, value.denominator
    coefficient, exponent = _decimal_parts(value)
    if exponent >= 0:
        return coefficient * (10**exponent), 1
    return coefficient, 10 ** (-exponent)


def _reduce_fraction(numerator: int, denominator: int) -> tuple[int, int]:
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    divisor = gcd(numerator, denominator) or 1
    return numerator // divisor, denominator // divisor


def _terminates_in_base10(denominator: int) -> bool:
    """True when a reduced positive denominator has only prime factors 2, 5."""
    remaining = denominator
    for factor in (2, 5):
        while remaining % factor == 0:
            remaining //= factor
    return remaining == 1


def _fraction_to_decimal(numerator: int, denominator: int) -> "Decimal":
    """Build the exact Decimal for a reduced fraction known to terminate."""
    remaining = denominator
    twos = 0
    while remaining % 2 == 0:
        remaining //= 2
        twos += 1
    fives = 0
    while remaining % 5 == 0:
        remaining //= 5
        fives += 1
    scale = max(twos, fives)
    multiplier = (2 ** (scale - twos)) * (5 ** (scale - fives))
    return Decimal(numerator * multiplier, -scale)


def _is_exact_zero(value: "int | Decimal | Rational") -> bool:
    if isinstance(value, Decimal):
        return value.coefficient == 0
    if isinstance(value, Rational):
        return False  # canonical Rational never has numerator 0 (collapses to int 0)
    return value == 0


def _reject_bool(*values: Any) -> None:
    for value in values:
        if isinstance(value, bool):
            raise NumericMisuseError("boolean operands are not numbers")


def _reject_float64_mix(left: Any, right: Any) -> None:
    left_f64 = isinstance(left, Float64)
    right_f64 = isinstance(right, Float64)
    if left_f64 != right_f64:
        raise NumericMisuseError("mixed exact/Float64 arithmetic is rejected")


def _check_exact_operand(value: Any) -> None:
    if not isinstance(value, (int, Decimal, Rational)) or isinstance(value, bool):
        raise TypeError(f"not an exact numeric value: {value!r}")


def add(left: Any, right: Any) -> Any:
    """Contract section 7: exact ``+`` with Integer/Decimal/Rational promotion."""
    _reject_bool(left, right)
    _reject_float64_mix(left, right)
    if isinstance(left, Float64):
        return Float64(left.value + right.value)
    _check_exact_operand(left)
    _check_exact_operand(right)
    if isinstance(left, Rational) or isinstance(right, Rational):
        na, da = _as_fraction(left)
        nb, db = _as_fraction(right)
        return make_rational(na * db + nb * da, da * db)
    if isinstance(left, Decimal) or isinstance(right, Decimal):
        ca, ea = _decimal_parts(left)
        cb, eb = _decimal_parts(right)
        e = min(ea, eb)
        return Decimal(ca * 10 ** (ea - e) + cb * 10 ** (eb - e), e)
    return left + right


def subtract(left: Any, right: Any) -> Any:
    """Contract section 7: exact ``-`` with Integer/Decimal/Rational promotion."""
    _reject_bool(left, right)
    _reject_float64_mix(left, right)
    if isinstance(left, Float64):
        return Float64(left.value - right.value)
    _check_exact_operand(left)
    _check_exact_operand(right)
    if isinstance(left, Rational) or isinstance(right, Rational):
        na, da = _as_fraction(left)
        nb, db = _as_fraction(right)
        return make_rational(na * db - nb * da, da * db)
    if isinstance(left, Decimal) or isinstance(right, Decimal):
        ca, ea = _decimal_parts(left)
        cb, eb = _decimal_parts(right)
        e = min(ea, eb)
        return Decimal(ca * 10 ** (ea - e) - cb * 10 ** (eb - e), e)
    return left - right


def multiply(left: Any, right: Any) -> Any:
    """Contract section 7: exact ``*`` with Integer/Decimal/Rational promotion."""
    _reject_bool(left, right)
    _reject_float64_mix(left, right)
    if isinstance(left, Float64):
        return Float64(left.value * right.value)
    _check_exact_operand(left)
    _check_exact_operand(right)
    if isinstance(left, Rational) or isinstance(right, Rational):
        na, da = _as_fraction(left)
        nb, db = _as_fraction(right)
        return make_rational(na * nb, da * db)
    if isinstance(left, Decimal) or isinstance(right, Decimal):
        ca, ea = _decimal_parts(left)
        cb, eb = _decimal_parts(right)
        return Decimal(ca * cb, ea + eb)
    return left * right


def divide(left: Any, right: Any) -> Any:
    """Contract section 8.1: exact division with terminating/non-terminating split."""
    _reject_bool(left, right)
    _reject_float64_mix(left, right)
    if isinstance(left, Float64):
        if right.value == 0.0:
            raise NumericMisuseError("Float64 division by zero")
        return Float64(left.value / right.value)
    _check_exact_operand(left)
    _check_exact_operand(right)
    if _is_exact_zero(right):
        raise NumericMisuseError("exact division by zero")
    if isinstance(left, Rational) or isinstance(right, Rational):
        na, da = _as_fraction(left)
        nb, db = _as_fraction(right)
        return make_rational(na * db, da * nb)
    if isinstance(left, Decimal) or isinstance(right, Decimal):
        na, da = _as_fraction(left)
        nb, db = _as_fraction(right)
        numerator, denominator = _reduce_fraction(na * db, da * nb)
        if _terminates_in_base10(denominator):
            return _fraction_to_decimal(numerator, denominator)
        return make_rational(numerator, denominator)
    # Integer / Integer: Integer when evenly divisible, otherwise Rational
    # (never Decimal — contract section 8.1's table has no Decimal cell for
    # this row/column, matching the "1 / 2 -> Rational 1/2" example).
    if left % right == 0:
        return left // right
    return make_rational(left, right)


def remainder(left: Any, right: Any) -> Any:
    """Contract section 8.2: exact floor-remainder, +/-/* promotion rule."""
    _reject_bool(left, right)
    _reject_float64_mix(left, right)
    if isinstance(left, Float64):
        if right.value == 0.0:
            raise NumericMisuseError("Float64 remainder by zero")
        quotient = _math_floor(left.value / right.value)
        return Float64(left.value - quotient * right.value)
    _check_exact_operand(left)
    _check_exact_operand(right)
    if _is_exact_zero(right):
        raise NumericMisuseError("exact remainder by zero")
    na, da = _as_fraction(left)
    nb, db = _as_fraction(right)
    quotient = (na * db) // (da * nb)
    return subtract(left, multiply(quotient, right))


def negate(value: Any) -> Any:
    """Unary ``-`` per contract section 7 (exact family) / section 9 (Float64)."""
    _reject_bool(value)
    if isinstance(value, Float64):
        return Float64(-value.value)
    if isinstance(value, Decimal):
        return Decimal(-value.coefficient, value.exponent)
    if isinstance(value, Rational):
        return make_rational(-value.numerator, value.denominator)
    if isinstance(value, int):
        return -value
    raise TypeError(f"cannot negate {value!r}")


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
