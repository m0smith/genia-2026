"""Exact numeric runtime value model (issue #838 slices 2-4).

This module implements the *value model*, *arithmetic*, and *equality/
comparison support* portions of ``docs/design/exact-numeric-model-contract.md``
sections 3, 4, 5, 7, 8, 9, and 10: canonical runtime representations for
Decimal and Rational, an explicit Float64 tag independent of any host-native
``int``/``float`` conflation, exact arithmetic/division/remainder, and the
extended-value helpers (:func:`numeric_extended_value`, :func:`compare_numeric`)
that ``genia.equality`` and ``genia.evaluator`` build cross-family
equality/ordering/map-key identity on top of (step 4, issue #838).

Scope boundary (see PR #839 discussion for issue #838):

- Integer remains plain Python ``int`` (R17 arbitrary precision is already
  satisfied by ``int``; no wrapper type is introduced).
- ``Decimal`` and ``Rational`` are new frozen value types with canonical
  construction per contract sections 3 and 4.
- ``Float64`` is a new explicit tag distinguishing an approximate binary64
  value from any exact numeric value; decimal-classified source literals
  still materialize as plain Python ``float`` through the temporary
  ``materialize_legacy_numeric`` bridge (``src/genia/numeric_literals.py``),
  so this module's Decimal/Float64 types remain unreachable from ordinary
  Genia source until that bridge is switched over (step 5/6) — the only
  currently source-reachable "new" value is Rational, produced by
  Integer/Integer division (e.g. ``1 / 3``).
- Cross-kind equality/ordering/map-key identity for Integer/Decimal/
  Rational/Float64 (contract section 10) is implemented here and consumed by
  ``genia.equality``/``genia.evaluator``; it deliberately does **not** bridge
  to the legacy decimal-literal-as-float domain (plain Python ``float``
  produced by ``materialize_legacy_numeric``) — that stays on the
  pre-existing R18 Integer/host-float rule untouched, since flipping it is
  shown to regress the existing shared-spec suite (see
  ``spec/eval/r18-equality-*.yaml``,
  ``spec/eval/json-representation-number-boundaries.yaml``). Display/debug
  rendering and the JSON boundary (contract sections 12-14) and the
  ``exact()``/``float64()``/``rational()`` conversion builtins (contract
  section 6) remain separately staged follow-on slices and are not
  implemented here.

Booleans are never numbers: :func:`is_numeric_value` explicitly excludes
``bool`` even though Python's ``bool`` is an ``int`` subclass, per contract
section 10 ("Booleans are not numbers").
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal as _PyDecimal
from fractions import Fraction
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


def to_fraction(value: "int | Decimal | Rational") -> Fraction:
    """Return the exact mathematical value of an Integer/Decimal/Rational.

    Used by the equality/comparison layer (contract section 10.1) so
    cross-family exact comparison never goes through a lossy intermediate
    representation.
    """
    numerator, denominator = _as_fraction(value)
    return Fraction(numerator, denominator)


# Sentinel for a numeric value with no well-ordered/well-equal mathematical
# value (only Float64 NaN, per contract sections 5/10.2). Kept as a private
# module-level object rather than a class so identity comparison (`is`) is
# the only supported operation on it, matching the contract's "NaN compares
# unequal to every value including itself" rule at the extended-value layer.
NUMERIC_NAN = object()


def numeric_extended_value(value: Any) -> "Fraction | float | object":
    """Return the extended mathematical value of a numeric value.

    Contract sections 10.1/10.2: Integer/Decimal/Rational always return an
    exact :class:`fractions.Fraction`. Float64 returns the same for any
    finite value (an exact dyadic conversion, never a rounded one), the host
    float ``inf``/``-inf`` for a Float64 infinity, or the module-level
    :data:`NUMERIC_NAN` sentinel for Float64 NaN.

    Raises ``TypeError`` for a non-numeric value (including ``bool``); the
    boolean-is-not-number rule is enforced by callers before this is reached.
    """
    if isinstance(value, bool):
        raise TypeError(f"not a numeric value: {value!r}")
    if isinstance(value, (int, Decimal, Rational)):
        return to_fraction(value)
    if isinstance(value, Float64):
        raw = value.value
        if raw != raw:  # noqa: PLR0124 - explicit NaN check
            return NUMERIC_NAN
        if raw in (float("inf"), float("-inf")):
            return raw
        return Fraction(raw)
    raise TypeError(f"not a numeric value: {value!r}")


def compare_numeric(left: Any, right: Any) -> "int | None":
    """Compare two Integer/Decimal/Rational/Float64 values by mathematical value.

    Returns ``-1``, ``0``, or ``1`` per the usual convention, or ``None`` when
    either operand is Float64 NaN (contract section 10.2: "ordered
    comparisons involving NaN are false" — callers turn ``None`` into
    ``False`` for every one of ``<``/``<=``/``>``/``>=``). Extended-real
    infinities order as usual against every finite exact/Float64 value.
    """
    left_value = numeric_extended_value(left)
    right_value = numeric_extended_value(right)
    if left_value is NUMERIC_NAN or right_value is NUMERIC_NAN:
        return None
    if left_value < right_value:
        return -1
    if left_value > right_value:
        return 1
    return 0


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


def construct_rational(numerator: Any, denominator: Any) -> "int | Rational":
    """``rational(numerator, denominator)`` (contract section 4).

    Both arguments must be Integers (plain Python ``int``, never ``bool``).
    A zero denominator or a non-Integer argument is deterministic numeric
    misuse (contract section 17: "invalid `rational` arguments or zero
    denominator"), not a host ``TypeError``/``ZeroDivisionError``.
    """
    if (
        not isinstance(numerator, int)
        or isinstance(numerator, bool)
        or not isinstance(denominator, int)
        or isinstance(denominator, bool)
    ):
        raise NumericMisuseError("rational arguments must be Integers")
    if denominator == 0:
        raise NumericMisuseError("rational denominator must be nonzero")
    return make_rational(numerator, denominator)


def construct_float64(value: Any) -> "Float64":
    """``float64(value)`` (contract section 5).

    Accepted input is an exact numeric value (Integer/Decimal/Rational) or an
    existing Float64, which is returned unchanged. Exact input is converted
    using IEEE-754 round-to-nearest, ties-to-even (Python's correctly-rounded
    big-int true division, via :func:`to_fraction`). A magnitude exceeding
    the largest finite binary64 value is deterministic numeric misuse rather
    than silently producing infinity (contract section 5/17). Exact
    mathematical zero converts to positive Float64 zero.
    """
    if isinstance(value, Float64):
        return value
    if isinstance(value, bool) or not isinstance(value, (int, Decimal, Rational)):
        raise NumericMisuseError("float64 expects an exact numeric value or Float64")
    fraction = to_fraction(value)
    try:
        result = fraction.numerator / fraction.denominator
    except OverflowError:
        raise NumericMisuseError(
            "float64 conversion exceeds the largest finite binary64 value"
        ) from None
    if result in (float("inf"), float("-inf")):
        raise NumericMisuseError("float64 conversion exceeds the largest finite binary64 value")
    return Float64(result)


def construct_exact(value: Any) -> "int | Decimal | Rational":
    """``exact(value)`` (contract section 6).

    - Integer/Decimal/Rational -> unchanged exact value
    - finite Float64 -> Decimal denoting the exact real value represented by
      the binary64 bits (never the shortest round-trip decimal, and never
      collapsed to Integer even when the represented value is mathematically
      integral -- contract section 3's "Decimal kind is retained" rule), via
      the exact ``as_integer_ratio()`` numerator/denominator (always a power
      of two, so it always terminates in base 10) fed through
      :func:`_fraction_to_decimal`
    - Float64 +0.0/-0.0 -> Decimal zero
    - Float64 NaN or +/-infinity -> conversion failure (deterministic
      numeric misuse, contract section 17)
    - any other (non-numeric, or boolean) input -> conversion failure
    """
    if isinstance(value, bool):
        raise NumericMisuseError("exact expects a numeric value")
    if isinstance(value, (int, Decimal, Rational)):
        return value
    if isinstance(value, Float64):
        raw = value.value
        if raw != raw:  # noqa: PLR0124 - explicit NaN check
            raise NumericMisuseError("exact conversion of Float64 NaN is invalid")
        if raw in (float("inf"), float("-inf")):
            raise NumericMisuseError("exact conversion of Float64 infinity is invalid")
        numerator, denominator = raw.as_integer_ratio()
        return _fraction_to_decimal(numerator, denominator)
    raise NumericMisuseError("exact expects a numeric value")


def render_decimal(value: "Decimal") -> str:
    """Canonical Decimal display/debug text (contract section 12.2).

    Fixed notation is used when the adjusted exponent (``len(digits) +
    exponent - 1``) is in ``[-6, 20]``; otherwise scientific notation. Both
    forms retain a trailing ``.0`` for a mathematically integral value so a
    Decimal never renders indistinguishably from an Integer.
    """
    coefficient, exponent = value.coefficient, value.exponent
    sign = "-" if coefficient < 0 else ""
    digits = str(abs(coefficient))
    adjusted_exponent = len(digits) + exponent - 1
    if -6 <= adjusted_exponent <= 20:
        if exponent >= 0:
            return f"{sign}{digits}{'0' * exponent}.0"
        split_pos = len(digits) + exponent
        if split_pos > 0:
            int_part, frac_part = digits[:split_pos], digits[split_pos:]
        else:
            int_part, frac_part = "0", ("0" * -split_pos) + digits
        return f"{sign}{int_part}.{frac_part}"
    mantissa = digits[0] + "." + (digits[1:] if len(digits) > 1 else "0")
    exp_sign = "+" if adjusted_exponent >= 0 else "-"
    return f"{sign}{mantissa}e{exp_sign}{abs(adjusted_exponent)}"


def render_rational(value: "Rational") -> str:
    """Canonical Rational display/debug text (contract section 12.3)."""
    return f"{value.numerator}/{value.denominator}"


def render_float64(value: "Float64") -> str:
    """Canonical Float64 display/debug text (contract section 12.4).

    Renders as the explicit constructor-shaped atom
    ``float64(<shortest-roundtrip-decimal>)`` so copying the rendering never
    silently changes numeric domains. The inner decimal is Python's ``repr``
    of the host float, which already produces the shortest decimal that
    round-trips to the identical binary64 bits under round-to-nearest,
    ties-to-even; it is reformatted only for a lowercase ``e``, an explicit
    exponent sign, no unnecessary exponent leading zeros, and a retained
    ``.0`` for an integral mantissa.
    """
    raw = value.value
    if raw != raw:  # noqa: PLR0124 - explicit NaN check
        inner = "nan"
    elif raw == float("inf"):
        inner = "inf"
    elif raw == float("-inf"):
        inner = "-inf"
    else:
        text = repr(raw)
        if "e" in text:
            mantissa, _, exp_text = text.partition("e")
            if "." not in mantissa:
                mantissa += ".0"
            exp_sign = "-" if exp_text[0] == "-" else "+"
            exp_digits = exp_text[1:].lstrip("0") or "0"
            inner = f"{mantissa}e{exp_sign}{exp_digits}"
        else:
            inner = text if "." in text else text + ".0"
    return f"float64({inner})"


def render_numeric_value(value: Any) -> str:
    """Canonical display/debug text for a Decimal/Rational/Float64 value.

    Integer uses its preexisting rendering (contract section 12.1) and is
    not handled here; callers dispatch to this only for the new runtime
    kinds (see ``genia.utf8.format_display``/``format_debug``).
    """
    if isinstance(value, Decimal):
        return render_decimal(value)
    if isinstance(value, Rational):
        return render_rational(value)
    if isinstance(value, Float64):
        return render_float64(value)
    raise TypeError(f"not a Decimal/Rational/Float64 value: {value!r}")


def _decimal_to_correctly_rounded_float(value: "Decimal") -> "float | None":
    """Round-to-nearest/ties-to-even binary64 for a Decimal, or ``None`` on overflow.

    Uses the same big-integer-ratio true division as :func:`construct_float64`
    (Python's ``int / int`` is correctly rounded) but never raises: it is an
    internal step of :func:`stable_json_decimal`, not the public ``float64``
    conversion, so an out-of-range magnitude is reported as "not encodable"
    rather than as numeric misuse.
    """
    numerator, denominator = _as_fraction(value)
    try:
        result = numerator / denominator
    except OverflowError:
        return None
    if result in (float("inf"), float("-inf")):
        return None
    return result


def _parse_decimal_text(text: str) -> "Decimal":
    """Parse a signed decimal-literal-shaped string (as produced by Python's
    ``repr(float)``) into an exact :class:`Decimal`, purely lexically."""
    from .numeric_literals import parse_numeric_literal

    negative = text.startswith("-")
    unsigned = text[1:] if negative else text
    literal = parse_numeric_literal(unsigned)
    if literal.kind == "integer":
        coefficient, exponent = int(literal.digits), 0
    else:
        coefficient, exponent = int(literal.coefficient), int(literal.exponent)
    return Decimal(-coefficient if negative else coefficient, exponent)


def stable_json_decimal(value: "int | Decimal") -> bool:
    """Contract section 13.2's ``stable_json_decimal(d)`` predicate.

    Also used, per section 13.3, as the terminating-Decimal-representation
    check for Rational JSON encodability (callers pass the Decimal obtained
    from a terminating Rational's exact base-10 expansion).
    """
    decimal_value = value if isinstance(value, Decimal) else Decimal(value, 0)
    as_float = _decimal_to_correctly_rounded_float(decimal_value)
    if as_float is None:
        return False
    if as_float == 0.0 and decimal_value.coefficient != 0:
        return False  # nonzero Decimal underflowed to zero
    roundtrip = _parse_decimal_text(repr(as_float))
    return to_fraction(roundtrip) == to_fraction(decimal_value)


def decimal_json_number(value: "int | Decimal") -> float:
    """The JSON-number ``float`` payload for a Decimal already proven stable
    by :func:`stable_json_decimal`. Callers must check the predicate first;
    this returns the same correctly-rounded binary64 value the predicate
    verified round-trips exactly, which ``json.dumps`` then renders using
    its own shortest-round-trip float formatting -- the same text the
    predicate itself parsed back, by construction.
    """
    decimal_value = value if isinstance(value, Decimal) else Decimal(value, 0)
    result = _decimal_to_correctly_rounded_float(decimal_value)
    if result is None:  # pragma: no cover - callers gate on stable_json_decimal first
        raise ValueError("decimal_json_number requires a stable_json_decimal value")
    return result


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
