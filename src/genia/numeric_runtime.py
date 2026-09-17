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


# ---------------------------------------------------------------------------
# E22-4: exact division and floor remainder (contract sections 7, 8)
# ---------------------------------------------------------------------------


def is_exact_numeric(value: Any) -> bool:
    """True for a value in the R22 exact family: Integer, Decimal, Rational."""
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, GeniaDecimal, GeniaRational))


def _exact_is_zero(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return value == 0
    if isinstance(value, GeniaDecimal):
        return value.is_zero()
    # A GeniaRational instance can never denote zero: rational_from_integers
    # collapses a zero numerator to plain Integer 0 before construction.
    return False


def _terminates_in_base10(denominator: int) -> bool:
    """True when `denominator` (already positive, already reduced against
    its numerator) has no prime factors other than 2 and 5 -- contract
    section 7: "A reduced quotient terminates in base 10 exactly when its
    denominator has no prime factors other than 2 and 5."
    """
    n = denominator
    while n % 2 == 0:
        n //= 2
    while n % 5 == 0:
        n //= 5
    return n == 1


def _decimal_from_reduced_fraction(numerator: int, denominator: int) -> GeniaDecimal:
    """Build the exact GeniaDecimal for numerator/denominator.

    Caller guarantees denominator is positive and _terminates_in_base10.
    """
    twos = 0
    n = denominator
    while n % 2 == 0:
        n //= 2
        twos += 1
    fives = 0
    while n % 5 == 0:
        n //= 5
        fives += 1
    scale = max(twos, fives)
    scaled_numerator = numerator * (2 ** (scale - twos)) * (5 ** (scale - fives))
    return GeniaDecimal(scaled_numerator, -scale)


def exact_divide(left: Any, right: Any) -> Any:
    """Exact `/` per contract section 7.

    Both operands must already be known exact-family values (see
    `is_exact_numeric`). Raises ZeroDivisionError -- not TypeError -- for
    division by exact zero, deliberately distinct from the evaluator's
    generic mixed-type TypeError-to-none(type-error) handling: division by
    zero is deterministic numeric misuse that terminates evaluation (this
    already-established behavior, e.g. actor handler failure, predates R22
    and is preserved here), not a value the caller silently continues with.

    The division-result table (section 7) is precise about which cells can
    ever become Decimal: only when a Decimal operand participates. Pure
    Integer/Integer division is Integer-when-evenly-divisible or Rational
    -- never Decimal, even when the reduced denominator would otherwise
    terminate in base 10 (`1 / 2` is Rational `1/2`, not Decimal `0.5`).
    Any Rational operand always yields Rational (subject to the same
    denominator-one collapse `rational_from_integers` already applies).
    """
    if _exact_is_zero(right):
        raise ZeroDivisionError("exact division by zero")
    ln, ld = _to_exact_fraction(left)
    rn, rd = _to_exact_fraction(right)
    numerator = ln * rd
    denominator = ld * rn
    if denominator < 0:
        numerator, denominator = -numerator, -denominator
    divisor = _gcd(numerator, denominator)
    numerator //= divisor
    denominator //= divisor
    if isinstance(left, GeniaRational) or isinstance(right, GeniaRational):
        return rational_from_integers(numerator, denominator)
    if isinstance(left, int) and isinstance(right, int):
        if denominator == 1:
            return numerator
        return rational_from_integers(numerator, denominator)
    # A GeniaDecimal operand participates (and no Rational): Decimal when
    # the reduced quotient terminates in base 10, else Rational. Decimal
    # participation retains Decimal kind even for an integral quotient,
    # matching section 6's established rule for +, -, *.
    if _terminates_in_base10(denominator):
        return _decimal_from_reduced_fraction(numerator, denominator)
    return rational_from_integers(numerator, denominator)


def exact_remainder(left: Any, right: Any) -> Any:
    """Exact `%` (floor remainder) per contract section 8.

    q = floor(left / right); left % right = left - q * right, using the
    same exact-family promotion rule as +, -, * (reused directly here via
    the already-established arithmetic dunders) rather than section 7's
    division-domain-selection rule. Raises ZeroDivisionError for a zero
    divisor, for the same reason exact_divide does.
    """
    if _exact_is_zero(right):
        raise ZeroDivisionError("exact remainder by zero")
    ln, ld = _to_exact_fraction(left)
    rn, rd = _to_exact_fraction(right)
    quotient_numerator = ln * rd
    quotient_denominator = ld * rn
    if quotient_denominator < 0:
        quotient_numerator, quotient_denominator = -quotient_numerator, -quotient_denominator
    floor_quotient = quotient_numerator // quotient_denominator
    return left - (floor_quotient * right)


# ---------------------------------------------------------------------------
# E22-5: explicit Float64 value and conversions (contract sections 4, 5)
# ---------------------------------------------------------------------------
#
# Float64 has no dedicated wrapper class: a Python float already is exactly
# one IEEE-754 binary64 bit pattern, which is precisely what the contract
# defines Float64 to be. R18 (equality.py) already treats host float as a
# first-class Genia kind with correct NaN/signed-zero/infinity semantics,
# so reusing it here introduces no new runtime type.


def to_float64(value: Any) -> float:
    """`float64(value)` per contract section 4.

    Accepts an exact numeric value (Integer/Decimal/Rational) or an
    existing Float64 (returned unchanged). Exact input is converted using
    round-to-nearest, ties-to-even: `numerator / denominator` on Python's
    arbitrary-precision ints IS specified and implemented by CPython to be
    correctly rounded to the nearest representable float (ties-to-even),
    which is exactly what this conversion needs and why exact_divide/
    exact_remainder's own `_to_exact_fraction` helper is reused here rather
    than any float()-of-text or float()-of-Decimal path. Exact magnitude
    beyond the largest finite binary64 value fails (Python's int/int true
    division already raises OverflowError in exactly that case, rather
    than silently producing infinity) instead of the caller getting a
    silent infinity. Exact mathematical zero converts to positive Float64
    zero: Integer 0, canonical GeniaDecimal zero (no negative-zero
    identity -- see numeric_runtime module), and the impossibility of a
    zero-valued GeniaRational (it always collapses to Integer 0) mean
    `numerator` is never negative when the exact value is zero, so
    `numerator / denominator` already yields +0.0 natively.
    """
    if isinstance(value, bool):
        raise TypeError("float64 expected a numeric value, received bool")
    if isinstance(value, float):
        return value
    if not is_exact_numeric(value):
        raise TypeError(
            f"float64 expected a numeric value, received {type(value).__name__}"
        )
    numerator, denominator = _to_exact_fraction(value)
    try:
        return numerator / denominator
    except OverflowError:
        raise OverflowError(
            "float64: exact magnitude exceeds the largest finite binary64 value"
        ) from None


def exact(value: Any) -> Any:
    """`exact(value)` per contract section 5.

    Integer/Decimal/Rational are returned unchanged. A finite Float64
    converts to the Decimal denoting the exact real value its binary64
    bits represent -- not the shortest human spelling that round-trips to
    it. `float.as_integer_ratio()` returns the *exact* (numerator,
    denominator) pair for the float with no rounding (CPython guarantees
    this; the denominator is always a power of two, or 1 for an integral
    value), so this never goes through float repr/str text. Since the
    denominator is a power of two, scaling both numerator and denominator
    by the matching power of five turns it into an exact power-of-ten
    denominator, which is precisely what GeniaDecimal's
    coefficient/exponent form represents -- so this reconstruction is
    exact by construction, not an approximation. Float64 +0.0/-0.0 both
    convert to canonical Decimal zero (GeniaDecimal has no negative-zero
    identity). NaN and +/-infinity are conversion failures.
    """
    if isinstance(value, bool):
        raise TypeError("exact expected a numeric value, received bool")
    if isinstance(value, (int, GeniaDecimal, GeniaRational)):
        return value
    if isinstance(value, float):
        if value != value:  # NaN is the only value unequal to itself
            raise ValueError("exact expected a finite value, received NaN")
        if value in (float("inf"), float("-inf")):
            raise ValueError("exact expected a finite value, received an infinity")
        if value == 0.0:
            return GeniaDecimal(0, 0)
        numerator, denominator = value.as_integer_ratio()
        power_of_two = denominator.bit_length() - 1  # denominator == 2**power_of_two
        coefficient = numerator * (5**power_of_two)
        return GeniaDecimal(coefficient, -power_of_two)
    raise TypeError(f"exact expected a numeric value, received {type(value).__name__}")


# ---------------------------------------------------------------------------
# E22-6: Float64 arithmetic and mixed-domain rejection (contract section 9)
# ---------------------------------------------------------------------------
#
# Float64-with-Float64 arithmetic needs no new implementation: a Python
# float already IS one IEEE-754 binary64 value, and its native +, -, *, /
# operators are already round-to-nearest-ties-to-even (that is what
# hardware/CPython float arithmetic is). Unary negation is likewise
# already correct native float behavior. Only two things are this slice's
# actual work: (1) division/remainder by Float64 zero must be deterministic
# misuse -- Python's native float already raises ZeroDivisionError rather
# than silently producing infinity/NaN, so this only needs a clearer,
# explicitly-authored message; (2) arithmetic mixing a bare Float64 with
# any exact-family operand must be rejected, which Python's native numeric
# tower does NOT do on its own for plain int (an `int` and `float` freely
# interoperate via Python's own arithmetic) -- this is the one gap the
# evaluator must explicitly close.


def is_mixed_exact_and_float64(left: Any, right: Any) -> bool:
    """True when exactly one of left/right is Float64 and the other is
    exact-family (Integer/Decimal/Rational). Contract section 9: such
    arithmetic must be rejected; the caller must explicitly convert with
    float64(...) or exact(...) first.
    """
    left_is_float = isinstance(left, float)
    right_is_float = isinstance(right, float)
    if left_is_float == right_is_float:
        return False
    other = right if left_is_float else left
    return is_exact_numeric(other)
