"""Experimental portable R12 document chunk and provenance boundary."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from .values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionSome,
    GeniaRepresented,
    GeniaSymbol,
    _is_nil_none,
    _runtime_type_name,
    symbol,
)


_JSON_SAFE_INTEGER = 9_007_199_254_740_991
_JSON_MAX_NESTING = 128


def _map(**values: Any) -> GeniaMap:
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _keys(value: GeniaMap) -> set[str] | None:
    keys: set[str] = set()
    for key, _ in value.items():
        if not isinstance(key, str):
            return None
        keys.add(key)
    return keys


def _closed_map(value: Any, expected: set[str], label: str) -> GeniaMap:
    if not isinstance(value, GeniaMap):
        raise TypeError(f"chunk expected {label} map, received {_runtime_type_name(value)}")
    if _keys(value) != expected:
        raise TypeError(f"chunk expected closed {label} with keys {sorted(expected)}")
    return value


def _valid_json_value(value: Any, depth: int = 0) -> bool:
    if _is_nil_none(value) or isinstance(value, bool):
        return True
    if isinstance(value, int):
        return -_JSON_SAFE_INTEGER <= value <= _JSON_SAFE_INTEGER
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, str) and not isinstance(value, GeniaSymbol):
        return not any(0xD800 <= ord(char) <= 0xDFFF for char in value)
    if isinstance(value, list):
        next_depth = depth + 1
        return next_depth <= _JSON_MAX_NESTING and all(
            _valid_json_value(item, next_depth) for item in value
        )
    if isinstance(value, GeniaMap):
        next_depth = depth + 1
        return next_depth <= _JSON_MAX_NESTING and all(
            isinstance(key, str)
            and not isinstance(key, GeniaSymbol)
            and not any(0xD800 <= ord(char) <= 0xDFFF for char in key)
            and _valid_json_value(item, next_depth)
            for key, item in value.items()
        )
    return False


def _validate_document(value: Any) -> GeniaMap:
    document = _closed_map(value, {"id", "meta", "text"}, "document")
    document_id = document.get("id")
    if not isinstance(document_id, str) or document_id == "":
        raise TypeError("chunk expected document id to be a non-empty string")
    if not isinstance(document.get("text"), str):
        raise TypeError("chunk expected document text to be a string")
    meta = document.get("meta")
    if (
        not isinstance(meta, GeniaRepresented)
        or meta.facet != "json"
        or not isinstance(meta.value, GeniaMap)
        or not _valid_json_value(meta.value)
    ):
        raise TypeError("chunk expected document meta to be a JSON-represented object")
    return document


def _span_coordinates(value: Any, text_length: int) -> tuple[int, int] | None:
    if not isinstance(value, GeniaMap) or _keys(value) != {"length", "offset"}:
        return None
    offset = value.get("offset")
    length = value.get("length")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        return None
    if isinstance(length, bool) or not isinstance(length, int) or length <= 0:
        return None
    if offset + length > text_length:
        return None
    return offset, length


def construct_chunks(
    chunker: Any,
    document_value: Any,
    *,
    is_callable: Callable[[Any], bool],
    invoke: Callable[[Any, list[Any]], Any],
) -> GeniaOptionSome | GeniaOptionErr:
    """Validate one document, invoke one chunker, and own chunk construction."""

    document = _validate_document(document_value)
    if not is_callable(chunker):
        raise TypeError(
            "chunk expected chunker function, "
            f"received {_runtime_type_name(chunker)}"
        )

    text = document.get("text")
    spans = invoke(chunker, [text])
    if not isinstance(spans, list):
        raise TypeError("chunk chunker must return a list")

    chunks: list[GeniaMap] = []
    for index, span in enumerate(spans):
        coordinates = _span_coordinates(span, len(text))
        if coordinates is None:
            return GeniaOptionErr(
                "chunk-invalid",
                _map(stage=symbol("span"), index=index),
            )
        offset, length = coordinates
        chunks.append(
            _map(
                text=text[offset : offset + length],
                source=_map(
                    doc_id=document.get("id"),
                    offset=offset,
                    length=length,
                ),
                meta=document.get("meta"),
            )
        )
    return GeniaOptionSome(chunks)
