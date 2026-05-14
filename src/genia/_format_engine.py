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
from typing import Any

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
    return _is_named_field(field)


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
    if _is_named_field(field):
        if not isinstance(value, GeniaMap):
            raise TypeError(f"format expected a map for named placeholder: {field}")
        if not value.has(field):
            raise ValueError(f"format missing field: {field}")
        return value.get(field)
    raise ValueError("format invalid placeholder")


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
        raise ValueError(f"format-error: format spec {spec!r} requires string or numeric value")

    if spec[0] == "0" and len(spec) > 1 and spec[1:].isdigit():
        width = int(spec)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"format-error: format spec {spec!r} requires numeric value")
        text = format_display(value)
        if len(text) >= width:
            return text
        if text.startswith("-"):
            return "-" + "0" * (width - len(text)) + text[1:]
        return "0" * (width - len(text)) + text

    if spec == ",":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("format-error: format spec ',' requires numeric value")
        return _format_grouping(value)

    raise ValueError(f"format-error: unsupported format spec {spec!r}")


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
