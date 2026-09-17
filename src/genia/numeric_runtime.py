"""R22 exact numeric runtime values.

Implements docs/design/r22-exact-numeric-runtime-contract.md section 2
(Decimal value) for E22-1: a genuine arbitrary-precision Decimal runtime
value, materialized from R21's tagged Decimal `IrLiteral` payload without
ever transiting host binary64.

Only Decimal is implemented in this module for E22-1. Rational (E22-2),
Float64 (E22-5/E22-6), and the full exact-family promotion lattice for
`/` and `%` (E22-3/E22-4) are later slices. To avoid regressing existing
Decimal-literal arithmetic that previously ran as host float (see the R21
`numeric_literal_runtime_value` compatibility shim this module replaces
for the Decimal case), `GeniaDecimal` implements exact same-kind and
Integer-interop arithmetic and ordering now; this is required for the
runtime value to be usable at all, not a promotion-lattice implementation
ahead of schedule -- Rational does not exist yet, so "exact arithmetic"
at this point in the sequence is exactly "Decimal (and Integer) arithmetic".

Display/debug text produced here is NOT the R23 canonical rendering
contract. It exists only so the value can be printed/formatted without
crashing during the R22 sequence; R23 owns canonical spelling.
"""
from __future__ import annotations

from dataclasses import dataclass


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
    def __add__(self, other):
        return _decimal_binop(self, other, lambda a, b: a + b)

    __radd__ = __add__

    def __sub__(self, other):
        return _decimal_binop(self, other, lambda a, b: a - b)

    def __rsub__(self, other):
        return _decimal_binop(_as_decimal(other), self, lambda a, b: a - b)

    def __mul__(self, other):
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
