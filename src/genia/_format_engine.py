"""Internal format engine for issue #298 format-refactor.

Exposes three testable, module-level helpers extracted from format_fn:
  - parse_format_template  — template string → list of TemplateParts
  - resolve_format_placeholder — (Genia value, field name) → resolved value
  - render_format_value    — Genia value → display string

Also exposes apply_format_spec (used by format_fn for field-spec rendering).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from genia.numeric_runtime import GeniaDecimal, GeniaRational, decimal_as_fraction
from genia.utf8 import format_debug, format_display
from genia.values import GeniaMap

# R23 contract section 7 (issue #913, E23-2): field-format-spec integration
# against the E23-1 canonical renderer. GeniaRational is a first-class
# numeric kind for format specs (in particular `.n` precision, which rounds
# its exact ratio) -- it was missing here before this slice, which meant
# every numeric format spec silently rejected Rational values, including
# `.n`, which the contract requires to work.
_NUMERIC_TYPES = (int, float, GeniaDecimal, GeniaRational)

# A "plain numeral" canonical rendering: optional sign, digits, optional
# fractional digits. This is the only shape zero-padding/grouping operate
# on (contract section 7: "zero-padding and grouping remain numeric
# presentation operations where the represented shape supports them").
# Integer and GeniaDecimal-in-fixed-notation canonical text are plain
# numerals. GeniaRational's `<numerator>/<denominator>` atom, Float64's
# `float64(...)` atom, and GeniaDecimal-in-scientific-notation text are
# not -- digit-position-counting presentation ops (grouping in particular)
# would silently mangle them rather than reformat a shape they don't fit.
_PLAIN_NUMERAL_RE = re.compile(r"-?\d+(\.\d+)?\Z")


def _require_plain_numeral_text(value: Any, spec: str) -> str:
    text = format_display(value)
    if not _PLAIN_NUMERAL_RE.match(text):
        raise ValueError(
            f"format-error: format spec {spec!r} is not supported for this numeric representation"
        )
    return text


# ---------------------------------------------------------------------------
# Template part types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemplateLiteral:
    text: str


@dataclass(frozen=True)
class TemplatePlaceholder:
    field: str
    spec: str | None


TemplatePart = TemplateLiteral | TemplatePlaceholder


# ---------------------------------------------------------------------------
# parse_format_template
# ---------------------------------------------------------------------------


def parse_format_template(template: str) -> list[TemplatePart]:
    """Parse a format template string into a list of TemplateLiteral / TemplatePlaceholder parts."""
    parts: list[TemplatePart] = []
    i = 0
    while i < len(template):
        ch = template[i]
        if ch == "{":
            if i + 1 < len(template) and template[i + 1] == "{":
                parts.append(TemplateLiteral("{"))
                i += 2
                continue
            close = template.find("}", i + 1)
            if close < 0:
                raise ValueError("format invalid placeholder")
            body = template[i + 1 : close]
            if ":" in body:
                colon = body.index(":")
                field = body[:colon]
                spec: str | None = body[colon + 1 :]
            else:
                field = body
                spec = None
            if not _is_valid_field(field):
                raise ValueError("format invalid placeholder")
            parts.append(TemplatePlaceholder(field, spec))
            i = close + 1
            continue
        if ch == "}":
            if i + 1 < len(template) and template[i + 1] == "}":
                parts.append(TemplateLiteral("}"))
                i += 2
                continue
            raise ValueError("format invalid placeholder")
        # accumulate literal characters
        start = i
        while i < len(template) and template[i] not in "{}":
            i += 1
        parts.append(TemplateLiteral(template[start:i]))
    return parts


def _is_valid_field(field: str) -> bool:
    if field == "":
        return False
    if _is_positional_field(field):
        return True
    return _is_named_path(field)


def _is_named_path(field: str) -> bool:
    return all(_is_named_field(part) for part in field.split("."))


def _split_named_path(field: str) -> list[str]:
    if not _is_named_path(field):
        raise ValueError("format invalid placeholder")
    return field.split(".")


def _is_named_field(field: str) -> bool:
    if not field:
        return False
    first = field[0]
    if not (first == "_" or ("A" <= first <= "Z") or ("a" <= first <= "z")):
        return False
    return all(
        ch == "_"
        or ("A" <= ch <= "Z")
        or ("a" <= ch <= "z")
        or ("0" <= ch <= "9")
        for ch in field[1:]
    )


def _is_positional_field(field: str) -> bool:
    return field != "" and all("0" <= ch <= "9" for ch in field)


# ---------------------------------------------------------------------------
# resolve_format_placeholder
# ---------------------------------------------------------------------------


def resolve_format_placeholder(value: Any, field: str) -> Any:
    """Resolve a named or positional field from a Genia value."""
    if _is_positional_field(field):
        if not isinstance(value, list):
            raise TypeError(f"format expected a list for positional placeholder: {field}")
        index = int(field, 10)
        if index >= len(value):
            raise ValueError(f"format missing field: {index}")
        return value[index]
    current = value
    for segment in _split_named_path(field):
        current = _resolve_named_segment(current, segment, field)
    return current


def _resolve_named_segment(value: Any, segment: str, full_path: str) -> Any:
    if not isinstance(value, GeniaMap):
        if segment == full_path:
            raise TypeError(f"format expected a map for named placeholder: {segment}")
        raise TypeError(f"format expected a map while resolving placeholder path: {full_path}")
    if not value.has(segment):
        raise ValueError(f"format missing field: {full_path}")
    return value.get(segment)


# ---------------------------------------------------------------------------
# render_format_value
# ---------------------------------------------------------------------------


def render_format_value(value: Any) -> str:
    """Render a Genia value to its display string."""
    return format_display(value)


# ---------------------------------------------------------------------------
# apply_format_spec (internal, used by format_fn)
# ---------------------------------------------------------------------------


def apply_format_spec(value: Any, spec: str) -> str:
    """Apply a format field spec (e.g. '<5', '.2', '03', ',') to a resolved value."""
    if not spec:
        raise ValueError("format-error: invalid format spec ''")

    if spec == "?":
        return format_debug(value)

    if spec[0] in "<>^":
        rest = spec[1:]
        if not rest or not rest.isdigit():
            raise ValueError(f"format-error: invalid format spec {spec!r}")
        width = int(rest)
        text = format_display(value)
        if len(text) >= width:
            return text
        pad = width - len(text)
        if spec[0] == "<":
            return text + " " * pad
        if spec[0] == ">":
            return " " * pad + text
        left = pad // 2
        return " " * left + text + " " * (pad - left)

    if spec[0] == ".":
        rest = spec[1:]
        if not rest or not rest.isdigit():
            raise ValueError(f"format-error: invalid format spec {spec!r}")
        n = int(rest)
        if isinstance(value, bool):
            raise ValueError(f"format-error: format spec {spec!r} requires string or numeric value")
        if isinstance(value, str):
            return value[:n]
        if isinstance(value, _NUMERIC_TYPES):
            return _format_numeric_precision(value, n, spec)
        raise ValueError(f"format-error: format spec {spec!r} requires string or numeric value")

    if spec[0] == "0" and len(spec) > 1 and spec[1:].isdigit():
        width = int(spec)
        if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
            raise ValueError(f"format-error: format spec {spec!r} requires numeric value")
        text = _require_plain_numeral_text(value, spec)
        if len(text) >= width:
            return text
        if text.startswith("-"):
            return "-" + "0" * (width - len(text)) + text[1:]
        return "0" * (width - len(text)) + text

    if spec == ",":
        if isinstance(value, bool) or not isinstance(value, _NUMERIC_TYPES):
            raise ValueError("format-error: format spec ',' requires numeric value")
        return _format_grouping(value, spec)

    raise ValueError(f"format-error: unsupported format spec {spec!r}")


def _exact_ratio_for_precision(value: Any, spec: str) -> tuple[int, int]:
    """Return `(numerator, denominator)`, exact, for `.n` precision rounding.

    R23 contract section 7: Decimal formatting operates directly on its
    exact coefficient/exponent; Rational rounds its exact ratio; Float64
    starts from the exact dyadic value represented by its bits. None of
    these three go through a `float(...)` cast or a host decimal
    formatter -- `float.as_integer_ratio()` returns Float64's exact
    binary64 bit-pattern ratio (no rounding), and `decimal_as_fraction`
    reads GeniaDecimal's coefficient/exponent fields directly.
    """
    if isinstance(value, int):
        return value, 1
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"format-error: format spec {spec!r} requires a finite numeric value")
        return value.as_integer_ratio()
    if isinstance(value, GeniaDecimal):
        return decimal_as_fraction(value)
    if isinstance(value, GeniaRational):
        return value.numerator, value.denominator
    raise ValueError(f"format-error: format spec {spec!r} requires string or numeric value")


def _format_numeric_precision(value: int | float | GeniaDecimal | GeniaRational, n: int, spec: str) -> str:
    numerator, denominator = _exact_ratio_for_precision(value, spec)
    return _round_ratio_half_up_text(numerator, denominator, n)


def _round_ratio_half_up_text(numerator: int, denominator: int, n: int) -> str:
    """Render `numerator/denominator` rounded to `n` decimal places, half-up.

    Pure arbitrary-precision integer arithmetic (`divmod` on
    `numerator * 10**n` against `denominator`) -- never `decimal.Decimal`
    division (whose default context precision cannot correctly round an
    arbitrary repeating ratio like `1/3`) and never a host binary float.
    Ties round away from zero, matching `decimal.ROUND_HALF_UP` (the
    pre-existing format-surface rule this slice preserves).
    """
    sign = "-" if numerator < 0 else ""
    magnitude = abs(numerator) * (10**n)
    quotient, remainder = divmod(magnitude, denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    if n == 0:
        return sign + str(quotient)
    digits = str(quotient).zfill(n + 1)
    return f"{sign}{digits[:-n]}.{digits[-n:]}"


def _format_grouping(value: int | float | GeniaDecimal | GeniaRational, spec: str) -> str:
    text = _require_plain_numeral_text(value, spec)
    negative = text.startswith("-")
    if negative:
        text = text[1:]
    if "." in text:
        int_part, frac_part = text.split(".", 1)
    else:
        int_part, frac_part = text, None
    n = len(int_part)
    grouped = ""
    for i, ch in enumerate(int_part):
        if i > 0 and (n - i) % 3 == 0:
            grouped += ","
        grouped += ch
    result = grouped if frac_part is None else grouped + "." + frac_part
    return "-" + result if negative else result
