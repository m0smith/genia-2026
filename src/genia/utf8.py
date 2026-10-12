"""Python-reference-host Unicode helpers and Genia value rendering.

STATE governs the R19 code-point/UTF-8/debug rules and the R23 numeric spelling.
Recognition uses class names and selected attributes to avoid runtime-value import
cycles; it is not type validation. Known opaque carriers never expose their
payloads here. Arbitrary host objects retain Python str/repr fallbacks, and
composite rendering assumes finite acyclic values. The helpers do not write to
stdout or stderr; fallback host methods may have their own side effects.
"""

from __future__ import annotations

import re
from typing import Any, Iterator

from genia.numeric_runtime import format_float64


_GENIA_IDENT_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$?!.-]*\Z")


def utf8_byte_length(s: str) -> int:
    """Return the strict UTF-8 encoded byte count of a Python string.

    Unpaired surrogates raise UnicodeEncodeError; no replacement or normalization
    is performed.
    """
    return len(s.encode("utf-8"))


def utf8_is_boundary(s: str, byte_offset: int) -> bool:
    """Test whether byte_offset is a scalar boundary in strict UTF-8.

    Offsets outside 0..encoded length return False; both endpoints return True.
    The string is encoded before checking bounds, so unpaired surrogates raise
    UnicodeEncodeError even for an out-of-range offset. Callers supply an integer
    byte offset, not a code-point index.
    """
    encoded = s.encode("utf-8")
    if byte_offset < 0 or byte_offset > len(encoded):
        return False
    if byte_offset == 0 or byte_offset == len(encoded):
        return True
    return (encoded[byte_offset] & 0b1100_0000) != 0b1000_0000


def utf8_codepoints(s: str) -> Iterator[str]:
    """Iterate Python string code points without normalization or grapheme grouping.

    Callers supply a scalar-valid Genia string; this helper does not validate or
    reject surrogate code points supplied directly by host code.
    """
    return iter(s)


def utf8_safe_slice_by_codepoint(s: str, start: int | None, end: int | None) -> str:
    """Return a code-point slice with Python start/end bound normalization.

    None selects the corresponding endpoint, negative indexes count from the end,
    and bounds clamp to the string length. Reversed bounds produce an empty
    string. This does not group graphemes, normalize text or validate scalars.
    """
    return s[slice(start, end)]


def format_display(value: Any) -> str:
    """Return user-facing Genia text without writing output.

    Strings remain unquoted; lists, pairs, ordered maps, Sheets and Outcomes
    render recursively. String Outcome reasons/contexts remain quoted. Recognized
    represented/protected values and capability carriers use opaque markers;
    Float64 uses the R23 canonical atom. Unrecognized host objects fall back to
    str(value), which may execute host code or raise; this is not a general
    serialization or redaction boundary. Cyclic containers are not supported.
    """
    if value is None:
        return 'none("nil")'
    if isinstance(value, bool):
        return "true" if value else "false"
    if _is_symbol(value):
        return value.name
    if _is_option_none(value):
        return _format_option_none(value, format_display)
    if _is_option_some(value):
        return _format_option_some(value, format_display)
    if _is_option_err(value):
        return _format_option_err(value, format_display)
    if _is_pair(value):
        return _format_pair(value, format_display)
    if _is_map(value):
        return _format_map(value, format_display)
    if _is_sheet(value):
        return _format_sheet(value, format_display)
    if _is_format(value):
        return "<format>"
    if _is_represented(value):
        return "<represented>"
    if _is_protected(value):
        return "<protected>"
    if _is_declassification_authority(value):
        return "<declassification-authority>"
    if _is_config_provider(value):
        return "<config-provider>"
    if _is_index_handle(value):
        return "<index-handle>"
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "[" + ", ".join(format_display(item) for item in value) + "]"
    if isinstance(value, float):
        # R23 contract section 2.4: canonical Float64 atom, never Python's
        # own float repr/str.
        return format_float64(value)
    return str(value)


_SHORT_DEBUG_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def _escape_for_debug(s: str) -> str:
    # R19 U3: deterministic debug escaping, independent of host terminal
    # behavior or Unicode printability tables. Every C0 control other than
    # the five short escapes, DEL, and every C1 control renders as lowercase
    # \uXXXX (exactly four hex digits); every other scalar renders literally.
    """Escape string contents deterministically without adding surrounding quotes.

    Backslash, double quote, newline, carriage return and tab use short escapes.
    Other C0 controls, DEL and C1 controls use lowercase four-digit Unicode
    escapes; other code points are literal. No scalar validation is performed.
    """
    out: list[str] = []
    for ch in s:
        short = _SHORT_DEBUG_ESCAPES.get(ch)
        if short is not None:
            out.append(short)
            continue
        cp = ord(ch)
        if cp <= 0x1F or cp == 0x7F or 0x80 <= cp <= 0x9F:
            out.append(f"\\u{cp:04x}")
        else:
            out.append(ch)
    return "".join(out)


def format_debug(value: Any) -> str:
    """Return debug Genia text with quoted, deterministically escaped strings.

    Composite values recurse in their stored order and recognized opaque
    carriers retain the same markers as format_display. Float64 uses its R23
    canonical atom. Unrecognized host objects fall back to repr(value), whose
    host behavior and exceptions are not normalized. This neither writes output
    nor supplies cycle detection or a general serialization/redaction boundary.
    """
    if value is None:
        return 'none("nil")'
    if isinstance(value, bool):
        return "true" if value else "false"
    if _is_symbol(value):
        return value.name
    if _is_option_none(value):
        return _format_option_none(value, format_debug)
    if _is_option_some(value):
        return _format_option_some(value, format_debug)
    if _is_option_err(value):
        return _format_option_err(value, format_debug)
    if _is_pair(value):
        return _format_pair(value, format_debug)
    if _is_map(value):
        return _format_map(value, format_debug)
    if _is_sheet(value):
        return _format_sheet(value, format_debug)
    if _is_format(value):
        return "<format>"
    if _is_represented(value):
        return "<represented>"
    if _is_protected(value):
        return "<protected>"
    if _is_declassification_authority(value):
        return "<declassification-authority>"
    if _is_config_provider(value):
        return "<config-provider>"
    if _is_index_handle(value):
        return "<index-handle>"
    if isinstance(value, str):
        return f'"{_escape_for_debug(value)}"'
    if isinstance(value, list):
        return "[" + ", ".join(format_debug(item) for item in value) + "]"
    if isinstance(value, float):
        # R23 contract section 2.4: canonical Float64 atom (display == debug),
        # never Python's own float repr/str.
        return format_float64(value)
    return repr(value)


def _is_symbol(value: Any) -> bool:
    """Recognize the GeniaSymbol class name plus a string name attribute."""
    return value.__class__.__name__ == "GeniaSymbol" and isinstance(getattr(value, "name", None), str)


def _is_pair(value: Any) -> bool:
    """Recognize the GeniaPair class name plus head/tail attributes, not tail validity."""
    return (
        value.__class__.__name__ == "GeniaPair"
        and hasattr(value, "head")
        and hasattr(value, "tail")
    )


def _is_map(value: Any) -> bool:
    """Recognize the GeniaMap class name plus _entries, without validating entries."""
    return value.__class__.__name__ == "GeniaMap" and hasattr(value, "_entries")


def _is_option_none(value: Any) -> bool:
    """Recognize GeniaOptionNone by class name and reason/context attribute presence."""
    return (
        value.__class__.__name__ == "GeniaOptionNone"
        and hasattr(value, "reason")
        and hasattr(value, "context")
    )


def _is_option_some(value: Any) -> bool:
    """Recognize GeniaOptionSome by class name and a value attribute."""
    return value.__class__.__name__ == "GeniaOptionSome" and hasattr(value, "value")


def _is_option_err(value: Any) -> bool:
    """Recognize GeniaOptionErr by class name and reason/context attribute presence."""
    return (
        value.__class__.__name__ == "GeniaOptionErr"
        and hasattr(value, "reason")
        and hasattr(value, "context")
    )


def _is_format(value: Any) -> bool:
    """Recognize GeniaFormat by class name and a template attribute."""
    return value.__class__.__name__ == "GeniaFormat" and hasattr(value, "template")


def _is_represented(value: Any) -> bool:
    """Recognize GeniaRepresented by class name, string facet and value attribute."""
    return (
        value.__class__.__name__ == "GeniaRepresented"
        and isinstance(getattr(value, "facet", None), str)
        and hasattr(value, "value")
    )


def _is_protected(value: Any) -> bool:
    """Recognize only the GeniaProtected class name, without inspecting its payload."""
    return value.__class__.__name__ == "GeniaProtected"


def _is_declassification_authority(value: Any) -> bool:
    """Recognize only the GeniaDeclassificationAuthority class name."""
    return value.__class__.__name__ == "GeniaDeclassificationAuthority"


def _is_config_provider(value: Any) -> bool:
    """Recognize only the GeniaConfigProvider class name, without acquiring data."""
    return value.__class__.__name__ == "GeniaConfigProvider"


def _is_index_handle(value: Any) -> bool:
    """Recognize only the GeniaIndexHandle class name, without inspecting index data."""
    return value.__class__.__name__ == "GeniaIndexHandle"


def _is_sheet(value: Any) -> bool:
    """Recognize GeniaSheet by class name and columns/row_count attribute presence."""
    return (
        value.__class__.__name__ == "GeniaSheet"
        and hasattr(value, "columns")
        and hasattr(value, "row_count")
    )


def _format_pair(value: Any, formatter) -> str:
    """Render a finite pair chain with formatter applied to heads and any dotted tail.

    Python None or context-free none("nil") terminates a proper list; every other
    tail is rendered after a dot. Callers provide an acyclic chain: there is no
    cycle detection, and formatter failures propagate.
    """
    parts: list[str] = []
    current = value
    while _is_pair(current):
        parts.append(formatter(current.head))
        current = current.tail
    if current is None or _is_nil_none_value(current):
        return "(" + " ".join(parts) + ")"
    return "(" + " ".join(parts + [".", formatter(current)]) + ")"


def _format_map(value: Any, formatter) -> str:
    """Render original map keys/values in _entries insertion order.

    String keys matching the local ASCII identifier spelling remain bare; other
    keys and all values use formatter. Internal canonical keys are not printed.
    Malformed entries or formatter failures propagate to the caller.
    """
    entries = getattr(value, "_entries", {})
    parts: list[str] = []
    for _, (original_key, original_value) in entries.items():
        parts.append(f"{_format_map_key(original_key, formatter)}: {formatter(original_value)}")
    return "{" + ", ".join(parts) + "}"


def _format_map_key(key: Any, formatter) -> str:
    """Leave locally recognized ASCII identifier strings bare; format other keys.

    The local regex is a rendering convention, not the lexer identifier grammar
    and not a promise that arbitrary rendered keys can be parsed back.
    """
    if isinstance(key, str) and _GENIA_IDENT_RE.fullmatch(key):
        return key
    return formatter(key)


def _format_sheet(value: Any, formatter) -> str:
    """Render stored columns as sheet([[name, [values]], ...]) using formatter.

    Preserve column and cell order; do not validate row counts or mutate columns.
    Malformed columns and formatter failures propagate.
    """
    columns = getattr(value, "columns")
    parts = [
        "[" + formatter(name) + ", [" + ", ".join(formatter(item) for item in values) + "]]"
        for name, values in columns
    ]
    return "sheet([" + ", ".join(parts) + "])"


def _format_option_none(value: Any, formatter) -> str:
    """Render none(reason[, context]), quoting string parts even in display mode.

    A context of Python None omits the context argument; other values recurse
    through formatter. This represents absence without propagating it.
    """
    reason = getattr(value, "reason", None)
    context = getattr(value, "context", None)
    reason_text = _format_option_part(reason, formatter)
    if context is None:
        return f"none({reason_text})"
    return f"none({reason_text}, {_format_option_part(context, formatter)})"


def _format_option_some(value: Any, formatter) -> str:
    """Render some(value[, context]) without unwrapping or propagating the Outcome.

    The payload uses formatter directly; string context uses debug quoting.
    A context of Python None omits that argument; formatter failures propagate.
    """
    value_text = formatter(getattr(value, "value"))
    context = getattr(value, "context", None)
    if context is None:
        return f"some({value_text})"
    return f"some({value_text}, {_format_option_part(context, formatter)})"


def _format_option_err(value: Any, formatter) -> str:
    """Render err(reason[, context]), preserving failure as ordinary text.

    String reason/context parts use debug quoting; other parts use formatter.
    Python None context omits the argument. No recovery or normalization occurs.
    """
    reason = getattr(value, "reason")
    context = getattr(value, "context", None)
    reason_text = _format_option_part(reason, formatter)
    if context is None:
        return f"err({reason_text})"
    return f"err({reason_text}, {_format_option_part(context, formatter)})"


def _is_nil_none_value(value: Any) -> bool:
    """Recognize a none Outcome with reason "nil" and no context as a pair terminator."""
    return _is_option_none(value) and getattr(value, "reason", None) == "nil" and getattr(value, "context", None) is None


def _format_option_part(value: Any, formatter) -> str:
    """Debug-quote string Outcome metadata; delegate every other value to formatter."""
    if isinstance(value, str):
        return f'"{_escape_for_debug(value)}"'
    return formatter(value)
