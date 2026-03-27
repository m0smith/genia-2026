from __future__ import annotations

from typing import Any, Iterator


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
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
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
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{_escape_for_debug(value)}"'
    if isinstance(value, list):
        return "[" + ", ".join(format_debug(item) for item in value) + "]"
    return repr(value)
