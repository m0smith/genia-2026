"""R22 exact numeric runtime values.

Implements docs/design/r22-exact-numeric-runtime-contract.md:

- section 2 (Decimal value), E22-1: a genuine arbitrary-precision Decimal
  runtime value, materialized from R21's tagged Decimal `IrLiteral`
  payload without ever transiting host binary64.
- section 3 (Rational value), E22-2: an exact reduced ratio of two
  arbitrary-precision Integers, via `rational_from_integers`.
- section 6 (exact arithmetic), E22-3: `+`, `-`, `*`, and unary negation
  across the full `Integer < Decimal < Rational` promotion lattice.

`/` and `%` (section 7/8, E22-4), Float64 (E22-5/E22-6), and comparison/
equality integration (E22-7) are later slices -- see the class-level
docstrings below for exactly what each type does and does not support yet.

Display/debug text produced here is NOT the R23 canonical rendering
contract. It exists only so the value can be printed/formatted without
crashing during the R22 sequence; R23 owns canonical spelling.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _canonicalize(coefficient: int, exponent: int) -> tuple[int, int]:
    """Canonicalize per contract section 2.

    zero -> (0, 0); otherwise strip trailing base-10 zeros from the
    magnitude of coefficient, increasing exponent by the count removed.
    Sign is carried by coefficient. No negative-zero identity.
    """
    if coefficient == 0:
        return 0, 0
    sign = -1 if coefficient < 0 else 1
    magnitude = abs(coefficient)
    text = str(magnitude)
    stripped = text.rstrip("0")
    if stripped == "":
        # magnitude was a power of ten with no nonzero digits left, e.g. 100
        return 0, 0
    removed = len(text) - len(stripped)
    return sign * int(stripped), exponent + removed


@dataclass(frozen=True, eq=False)
class GeniaDecimal:
    """Exact runtime Decimal value: coefficient * 10**exponent.

    Both fields are arbitrary-precision Python ints. Construct only
    through this class's __init__ (never mutate fields) so the
    canonical-form invariant always holds.
    """

    coefficient: int
    exponent: int

    def __init__(self, coefficient: int, exponent: int) -> None:
        coefficient, exponent = _canonicalize(coefficient, exponent)
        object.__setattr__(self, "coefficient", coefficient)
        object.__setattr__(self, "exponent", exponent)

    # -- exact rational value, used internally for arithmetic/compat only --
    def _as_fraction(self) -> tuple[int, int]:
        """Return (numerator, denominator) with denominator a positive power of ten."""
        if self.exponent >= 0:
            return self.coefficient * (10**self.exponent), 1
        return self.coefficient, 10 ** (-self.exponent)

    def is_zero(self) -> bool:
        return self.coefficient == 0

    # -- same-kind / Integer-interop arithmetic (see module docstring) --
    #
    # E22-3 (docs/design/r22-exact-numeric-runtime-contract.md section 6):
    # Rational is the top of the exact promotion lattice, so any operand
    # that is a GeniaRational is NotImplemented here and delegated to
    # GeniaRational's reflected method via Python's normal binary-operator
    # protocol, rather than handled in this class.
    def __add__(self, other):
        if isinstance(other, GeniaRational):
            return NotImplemented
        return _decimal_binop(self, other, lambda a, b: a + b)

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, GeniaRational):
            return NotImplemented
        return _decimal_binop(self, other, lambda a, b: a - b)

    def __rsub__(self, other):
        if isinstance(other, GeniaRational):
            return NotImplemented
        return _decimal_binop(_as_decimal(other), self, lambda a, b: a - b)

    def __mul__(self, other):
        if isinstance(other, GeniaRational):
            return NotImplemented
        return _decimal_mul(self, other)

    __rmul__ = __mul__

    def __neg__(self):
        return GeniaDecimal(-self.coefficient, self.exponent)

    def __pos__(self):
        return self

    def __eq__(self, other):
        if isinstance(other, GeniaDecimal):
            return self.coefficient == other.coefficient and self.exponent == other.exponent
        if isinstance(other, int) and not isinstance(other, bool):
            return self.coefficient == other and self.exponent == 0 or (self.coefficient == 0 and other == 0)
        return NotImplemented

    def __hash__(self):
        return hash((GeniaDecimal, self.coefficient, self.exponent))

    def __lt__(self, other):
        return _decimal_cmp(self, other) < 0

    def __le__(self, other):
        return _decimal_cmp(self, other) <= 0

    def __gt__(self, other):
        return _decimal_cmp(self, other) > 0

    def __ge__(self, other):
        return _decimal_cmp(self, other) >= 0

    def __repr__(self) -> str:  # pending R23 canonical spelling
        if self.exponent >= 0:
            digits = str(self.coefficient * (10**self.exponent))
            return digits
        magnitude = abs(self.coefficient)
        digits = str(magnitude)
        point = len(digits) + self.exponent
        sign = "-" if self.coefficient < 0 else ""
        if point <= 0:
            return f"{sign}0.{'0' * (-point)}{digits}"
        return f"{sign}{digits[:point]}.{digits[point:]}"

    __str__ = __repr__


def _as_decimal(value) -> GeniaDecimal:
    if isinstance(value, GeniaDecimal):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return GeniaDecimal(value, 0)
    raise TypeError(f"cannot combine GeniaDecimal with {type(value).__name__}")


def _decimal_binop(left, right, op):
    if isinstance(right, bool) or (not isinstance(right, (GeniaDecimal, int))):
        raise TypeError("unsupported operand type for exact Decimal arithmetic")
    left_d = _as_decimal(left)
    right_d = _as_decimal(right)
    ln, ld = left_d._as_fraction()
    rn, rd = right_d._as_fraction()
    # common power-of-ten denominator
    if ld == rd:
        num, den_exp = op(ln, rn), -_log10(ld)
    elif ld < rd:
        scale = rd // ld
        num, den_exp = op(ln * scale, rn), -_log10(rd)
    else:
        scale = ld // rd
        num, den_exp = op(ln, rn * scale), -_log10(ld)
    return GeniaDecimal(num, den_exp)


def _decimal_mul(left, right):
    if isinstance(right, bool) or (not isinstance(right, (GeniaDecimal, int))):
        raise TypeError("unsupported operand type for exact Decimal arithmetic")
    left_d = _as_decimal(left)
    right_d = _as_decimal(right)
    return GeniaDecimal(left_d.coefficient * right_d.coefficient, left_d.exponent + right_d.exponent)


def _decimal_cmp(left, right) -> int:
    if isinstance(right, bool) or (not isinstance(right, (GeniaDecimal, int))):
        raise TypeError("unsupported operand type for exact Decimal comparison")
    left_d = _as_decimal(left)
    right_d = _as_decimal(right)
    ln, ld = left_d._as_fraction()
    rn, rd = right_d._as_fraction()
    lhs = ln * rd
    rhs = rn * ld
    return (lhs > rhs) - (lhs < rhs)


def _log10(power_of_ten: int) -> int:
    n = power_of_ten
    exp = 0
    while n > 1:
        n //= 10
        exp += 1
    return exp


def decimal_as_fraction(value: GeniaDecimal) -> tuple[int, int]:
    """Public accessor for a GeniaDecimal's exact (numerator, denominator).

    Denominator is always a positive power of ten. Used by R18 equality/key
    reconciliation (equality.py) to compare/bucket GeniaDecimal exactly
    against Integer and against itself, without duplicating the
    coefficient/exponent-to-fraction conversion.
    """
    return value._as_fraction()


def make_decimal_from_payload(coefficient: str, exponent: str) -> GeniaDecimal:
    """Materialize a GeniaDecimal from an R21 tagged Decimal IrLiteral payload.

    Consumes already-canonical base-10 strings; never constructs or
    consults a host binary float.
    """
    return GeniaDecimal(int(coefficient), int(exponent))


# ---------------------------------------------------------------------------
# E22-2: exact Rational runtime value (contract section 3)
# ---------------------------------------------------------------------------


def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a or 1


@dataclass(frozen=True, eq=False)
class GeniaRational:
    """Exact reduced ratio of two arbitrary-precision Integers.

    Construct only through ``rational_from_integers`` (never directly),
    which enforces the canonical-form invariant: nonzero, gcd-reduced,
    positive denominator strictly greater than 1 (a reduced denominator
    of 1 collapses to a plain Integer and is never represented as
    GeniaRational -- see ``rational_from_integers``).
    """

    numerator: int
    denominator: int

    def __eq__(self, other):
        if isinstance(other, GeniaRational):
            return (
                self.numerator == other.numerator
                and self.denominator == other.denominator
            )
        return NotImplemented

    def __hash__(self):
        return hash((GeniaRational, self.numerator, self.denominator))

    def __repr__(self) -> str:  # pending R23 canonical spelling
        return f"{self.numerator}/{self.denominator}"

    __str__ = __repr__

    # -- E22-3 exact arithmetic: Rational is the top of the promotion
    # lattice (Integer < Decimal < Rational), so these accept Integer,
    # GeniaDecimal, and GeniaRational operands directly rather than
    # delegating anywhere -- see module docstring and _to_exact_fraction.
    def __add__(self, other):
        return _rational_binop(self, other, lambda a, b: a + b)

    __radd__ = __add__

    def __sub__(self, other):
        return _rational_binop(self, other, lambda a, b: a - b)

    def __rsub__(self, other):
        return _rational_binop(other, self, lambda a, b: a - b)

    def __mul__(self, other):
        return _rational_mul(self, other)

    __rmul__ = __mul__

    def __neg__(self):
        # Negating the numerator alone preserves the gcd(numerator,
        # denominator) == 1 and denominator > 0 invariants, so direct
        # construction (bypassing rational_from_integers) is still canonical.
        return GeniaRational(-self.numerator, self.denominator)

    def __pos__(self):
        return self


def _to_exact_fraction(value: Any) -> tuple[int, int]:
    """Return (numerator, denominator > 0) for any exact-family value.

    Used only by Rational-participating arithmetic (E22-3): Integer,
    GeniaDecimal, and GeniaRational all have an exact rational value.
    Raises TypeError for anything else (bool included), which callers
    convert to NotImplemented so Python's operator protocol can still try
    the other operand's reflected method or a host TypeError.
    """
    if isinstance(value, bool):
        raise TypeError("unsupported operand type for exact Rational arithmetic")
    if isinstance(value, int):
        return value, 1
    if isinstance(value, GeniaDecimal):
        return value._as_fraction()
    if isinstance(value, GeniaRational):
        return value.numerator, value.denominator
    raise TypeError("unsupported operand type for exact Rational arithmetic")


def _rational_binop(left: Any, right: Any, op) -> Any:
    try:
        ln, ld = _to_exact_fraction(left)
        rn, rd = _to_exact_fraction(right)
    except TypeError:
        return NotImplemented
    return rational_from_integers(op(ln * rd, rn * ld), ld * rd)


def _rational_mul(left: Any, right: Any) -> Any:
    try:
        ln, ld = _to_exact_fraction(left)
        rn, rd = _to_exact_fraction(right)
    except TypeError:
        return NotImplemented
    return rational_from_integers(ln * rn, ld * rd)


def rational_from_integers(numerator: int, denominator: int) -> "int | GeniaRational":
    """Construct the canonical R22 Rational value from two Integers.

    Per contract section 3: divide both by their positive gcd, denominator
    is positive (sign carried by numerator), and a reduced denominator of
    1 collapses to a plain Integer rather than a GeniaRational. Raises
    TypeError deterministically for a zero denominator; callers are
    expected to have already validated both arguments are Integers.
    """
    if denominator == 0:
        raise TypeError("rational expected a nonzero denominator")
    divisor = _gcd(numerator, denominator)
    reduced_numerator = numerator // divisor
    reduced_denominator = denominator // divisor
    if reduced_denominator < 0:
        reduced_numerator = -reduced_numerator
        reduced_denominator = -reduced_denominator
    if reduced_denominator == 1:
        return reduced_numerator
    return GeniaRational(reduced_numerator, reduced_denominator)
