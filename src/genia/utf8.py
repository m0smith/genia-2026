from __future__ import annotations

import re
from typing import Any, Iterator


_GENIA_IDENT_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$?!.-]*\Z")


def utf8_byte_length(s: str) -> int:
    return len(s.encode("utf-8"))


def utf8_is_boundary(s: str, byte_offset: int) -> bool:
    encoded = s.encode("utf-8")
    if byte_offset < 0 or byte_offset > len(encoded):
        return False
    if byte_offset == 0 or byte_offset == len(encoded):
        return True
    return (encoded[byte_offset] & 0b1100_0000) != 0b1000_0000


def utf8_codepoints(s: str) -> Iterator[str]:
    return iter(s)


def utf8_safe_slice_by_codepoint(s: str, start: int | None, end: int | None) -> str:
    return s[slice(start, end)]


def format_display(value: Any) -> str:
    if value is None:
        return 'none("nil")'
    if isinstance(value, bool):
        return "true" if value else "false"
    if _is_symbol(value):
        return value.name
    if _is_option_none(value):
        return _format_option_none(value, format_display)
    if _is_option_some(value):
        return f"some({format_display(value.value)})"
    if _is_pair(value):
        return _format_pair(value, format_display)
    if _is_map(value):
        return _format_map(value, format_display)
    if _is_format(value):
        return "<format>"
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ", ".join(format_display(item) for item in value) + "]"
    return str(value)


def _escape_for_debug(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def format_debug(value: Any) -> str:
    if value is None:
        return 'none("nil")'
    if isinstance(value, bool):
        return "true" if value else "false"
    if _is_symbol(value):
        return value.name
    if _is_option_none(value):
        return _format_option_none(value, format_debug)
    if _is_option_some(value):
        return f"some({format_debug(value.value)})"
    if _is_pair(value):
        return _format_pair(value, format_debug)
    if _is_map(value):
        return _format_map(value, format_debug)
    if _is_format(value):
        return "<format>"
    if isinstance(value, str):
        return f'"{_escape_for_debug(value)}"'
    if isinstance(value, list):
        return "[" + ", ".join(format_debug(item) for item in value) + "]"
    return repr(value)


def _is_symbol(value: Any) -> bool:
    return value.__class__.__name__ == "GeniaSymbol" and isinstance(getattr(value, "name", None), str)


def _is_pair(value: Any) -> bool:
    return (
        value.__class__.__name__ == "GeniaPair"
        and hasattr(value, "head")
        and hasattr(value, "tail")
    )


def _is_map(value: Any) -> bool:
    return value.__class__.__name__ == "GeniaMap" and hasattr(value, "_entries")


def _is_option_none(value: Any) -> bool:
    return (
        value.__class__.__name__ == "GeniaOptionNone"
        and hasattr(value, "reason")
        and hasattr(value, "context")
    )


def _is_option_some(value: Any) -> bool:
    return value.__class__.__name__ == "GeniaOptionSome" and hasattr(value, "value")


def _is_format(value: Any) -> bool:
    return value.__class__.__name__ == "GeniaFormat" and hasattr(value, "template")


def _format_pair(value: Any, formatter) -> str:
    parts: list[str] = []
    current = value
    while _is_pair(current):
        parts.append(formatter(current.head))
        current = current.tail
    if current is None or _is_nil_none_value(current):
        return "(" + " ".join(parts) + ")"
    return "(" + " ".join(parts + [".", formatter(current)]) + ")"


def _format_map(value: Any, formatter) -> str:
    entries = getattr(value, "_entries", {})
    parts: list[str] = []
    for _, (original_key, original_value) in entries.items():
        parts.append(f"{_format_map_key(original_key, formatter)}: {formatter(original_value)}")
    return "{" + ", ".join(parts) + "}"


def _format_map_key(key: Any, formatter) -> str:
    if isinstance(key, str) and _GENIA_IDENT_RE.fullmatch(key):
        return key
    return formatter(key)


def _format_option_none(value: Any, formatter) -> str:
    reason = getattr(value, "reason", None)
    context = getattr(value, "context", None)
    reason_text = _format_option_part(reason, formatter)
    if context is None:
        return f"none({reason_text})"
    return f"none({reason_text}, {_format_option_part(context, formatter)})"


def _is_nil_none_value(value: Any) -> bool:
    return _is_option_none(value) and getattr(value, "reason", None) == "nil" and getattr(value, "context", None) is None


def _format_option_part(value: Any, formatter) -> str:
    if isinstance(value, str):
        return f'"{_escape_for_debug(value)}"'
    return formatter(value)
