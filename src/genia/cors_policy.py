"""Shared validation for the existing Python-host CORS policy."""

from __future__ import annotations

from typing import Any

from .utf8 import format_debug
from .values import GeniaMap


def resolve_cors_policy(value: Any) -> tuple[str, list[str], list[str]]:
    """Validate one closed CORS policy and return its resolved fields."""

    if not isinstance(value, GeniaMap):
        raise TypeError("cors expected policy to be a map")

    allowed_fields = {"origin", "methods", "headers"}
    for field, _ in value.items():  # noqa: PERF102 - GeniaMap exposes ordered items
        if field not in allowed_fields:
            raise TypeError(f"cors unexpected policy field {format_debug(field)}")

    origin = value.get("origin", "*")
    if not isinstance(origin, str) or not origin:
        raise TypeError("cors expected policy.origin to be a non-empty string")

    methods_value = value.get("methods", ["GET", "POST", "OPTIONS"])
    if not isinstance(methods_value, list) or not methods_value:
        raise TypeError("cors expected policy.methods to be a non-empty list")
    methods: list[str] = []
    for index, method in enumerate(methods_value):
        if not isinstance(method, str) or not method:
            raise TypeError(
                "cors expected policy.methods item "
                f"at index {index} to be a non-empty string"
            )
        methods.append(method)

    headers_value = value.get("headers", ["content-type"])
    if not isinstance(headers_value, list) or not headers_value:
        raise TypeError("cors expected policy.headers to be a non-empty list")
    headers: list[str] = []
    for index, header in enumerate(headers_value):
        if not isinstance(header, str) or not header:
            raise TypeError(
                "cors expected policy.headers item "
                f"at index {index} to be a non-empty string"
            )
        headers.append(header)

    return origin, methods, headers
