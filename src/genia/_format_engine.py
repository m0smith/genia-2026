"""Internal format engine for issue #298 format-refactor.

Exposes three testable, module-level helpers extracted from format_fn:
  - parse_format_template  — template string → list of TemplateParts
  - resolve_format_placeholder — (Genia value, field name) → resolved value
  - render_format_value    — Genia value → display string

Also exposes apply_format_spec (used by format_fn for field-spec rendering).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Any

from genia.numeric_values import Decimal as _NumDecimal
from genia.numeric_values import Float64 as _NumFloat64
from genia.numeric_values import Rational as _NumRational
from genia.numeric_values import to_fraction as _numeric_to_fraction
from genia.utf8 import format_debug, format_display
from genia.values import GeniaMap


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
        if isinstance(value, (int, float)):
            return _format_numeric_precision(value, n)
        if _is_extended_numeric(value):
            return _format_extended_numeric_precision(value, n)
        raise ValueError(f"format-error: format spec {spec!r} requires string or numeric value")

    if spec[0] == "0" and len(spec) > 1 and spec[1:].isdigit():
        width = int(spec)
        if isinstance(value, bool) or not (isinstance(value, (int, float)) or _is_decimal_shaped_numeric(value)):
            raise ValueError(f"format-error: format spec {spec!r} requires numeric value")
        text = format_display(value)
        if len(text) >= width:
            return text
        if text.startswith("-"):
            return "-" + "0" * (width - len(text)) + text[1:]
        return "0" * (width - len(text)) + text

    if spec == ",":
        if isinstance(value, bool) or not (isinstance(value, (int, float)) or _is_decimal_shaped_numeric(value)):
            raise ValueError("format-error: format spec ',' requires numeric value")
        return _format_grouping(value)

    raise ValueError(f"format-error: unsupported format spec {spec!r}")


def _is_extended_numeric(value: Any) -> bool:
    """True for the exact-numeric-model Decimal/Rational/Float64 runtime kinds
    (contract section 14: format-spec presentation covers these too, on top
    of the preexisting plain ``int``/``float`` handling above)."""
    return isinstance(value, (_NumDecimal, _NumRational, _NumFloat64))


def _is_decimal_shaped_numeric(value: Any) -> bool:
    """True for the extended-numeric kinds whose canonical rendering is
    ordinary decimal/float text (Decimal, Float64) -- i.e. excluding
    Rational, whose canonical ``<numerator>/<denominator>`` text is not a
    presentation shape that zero-padding/grouping can be meaningfully
    applied to (contract section 14 only pins ``.n`` precision rounding for
    Rational, via decimal expansion of the exact ratio)."""
    return isinstance(value, (_NumDecimal, _NumFloat64))


def _extended_numeric_fraction(value: Any) -> Fraction:
    if isinstance(value, (_NumDecimal, _NumRational)):
        return _numeric_to_fraction(value)
    if isinstance(value, _NumFloat64):
        return Fraction(*value.value.as_integer_ratio())
    raise TypeError(f"not an extended numeric value: {value!r}")


def _format_extended_numeric_precision(value: Any, n: int) -> str:
    """``.n`` precision for Decimal/Rational/Float64 (contract section 14):
    decimal half-up rounding of the exact mathematical value, computed
    without going through a host binary float intermediate."""
    fraction = _extended_numeric_fraction(value)
    sign = "-" if fraction < 0 else ""
    magnitude = -fraction if fraction < 0 else fraction
    scale = Fraction(10) ** n
    scaled = magnitude * scale
    floor_value = scaled.numerator // scaled.denominator
    if scaled - floor_value >= Fraction(1, 2):
        floor_value += 1
    if floor_value == 0:
        sign = ""
    if n == 0:
        return f"{sign}{floor_value}"
    digits = str(floor_value).rjust(n + 1, "0")
    return f"{sign}{digits[:-n]}.{digits[-n:]}"


def _format_numeric_precision(value: int | float, n: int) -> str:
    d = Decimal(repr(value))
    if n == 0:
        return str(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    quantize_str = "0." + "0" * n
    return str(d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP))


def _format_grouping(value: int | float) -> str:
    text = format_display(value)
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
