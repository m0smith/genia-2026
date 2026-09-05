"""R14 E14-9 declarative outbound HTTP annotation binding.

Implements `@get`/`@post` descriptor validation and the `web.send_annotated`
composition function, per issue #626. The E14-0 contract fixes only three
constraints for this ticket: reuse the existing `HttpOperation`/
`web.http_send` surface (no second transport/lifecycle mechanism), stay
inert outside explicit invocation (no self-executing IO), and add no new
syntax/AST/Core IR form. The exact annotation payload and trigger-function
shape are this ticket's own design, following `@route`'s established
metadata-attachment precedent as closely as possible — see this ticket's
Design phase notes for the full reasoning.

`@get {path}`/`@post {path}` attach one closed `{verb, path}` descriptor,
under the shared `http_annotation` metadata key, to a top-level named
zero-argument function. Annotating a function never changes how it is
called: `perform_send_annotated` is the sole place that reads the
descriptor, calls the function to obtain its dynamic `{headers, query,
body}` parts, and composes the unchanged `construct_http_operation` +
`perform_http_send`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .callable import GeniaFunctionGroup
from .http_client import perform_http_send
from .http_operation import construct_http_operation
from .http_transport import HttpTransport
from .lifecycle_runtime import Invoke
from .values import GeniaMap, GeniaOptionSome, _runtime_type_name, symbol

_HTTP_ANNOTATION_KEY = "http_annotation"
_DYNAMIC_KEYS = {"headers", "query", "body"}


def validate_http_annotation_descriptor(verb_name: str, value: Any) -> GeniaMap:
    """Validate one closed ``{path}`` outbound HTTP annotation descriptor."""

    if not isinstance(value, GeniaMap):
        raise TypeError(
            f"@{verb_name} annotation expected a map, received {_runtime_type_name(value)}"
        )
    keys = {key for key, _value in value.items() if isinstance(key, str)}
    if value.count() != 1 or keys != {"path"}:
        raise TypeError(f"@{verb_name} descriptor expected exactly one path field")
    path = value.get("path")
    if not isinstance(path, str) or not path or not path.startswith("/"):
        raise TypeError(f"@{verb_name} descriptor path must be a non-empty string starting with /")
    return GeniaMap().put("verb", symbol(verb_name)).put("path", path)


def _is_exact_zero_argument_handler(value: Any) -> bool:
    if not isinstance(value, GeniaFunctionGroup) or value.sorted_arities() != [0]:
        return False
    function = value.get(0)
    return function is not None and function.rest_param is None


def resolve_http_annotation(fn: Any) -> GeniaMap:
    """Extract and validate the ``{verb, path}`` descriptor from an annotated function."""

    if not isinstance(fn, GeniaFunctionGroup) or not fn.metadata.has(_HTTP_ANNOTATION_KEY):
        raise TypeError("send_annotated expected a function annotated with @get or @post")
    if not _is_exact_zero_argument_handler(fn):
        raise TypeError("send_annotated expected a fixed zero-argument function")
    return fn.metadata.get(_HTTP_ANNOTATION_KEY)


def perform_send_annotated(
    fn: Any,
    base_url: Any,
    authority: Any,
    timeout_ms: Any,
    *,
    json_encode: Callable[[Any], Any],
    invoke: Invoke,
    transport: HttpTransport | None = None,
) -> Any:
    """``web.send_annotated(fn, base_url, authority, timeout_ms)``.

    Composes the unchanged ``construct_http_operation`` and
    ``perform_http_send`` — no method-specific duplicate transport or
    lifecycle implementation is introduced.
    """

    descriptor = resolve_http_annotation(fn)
    dynamic = invoke(fn, [])
    if not isinstance(dynamic, GeniaMap):
        raise TypeError(
            "@get/@post function must return a map with exactly headers, query, body, "
            f"received {_runtime_type_name(dynamic)}"
        )
    dynamic_keys = {key for key, _value in dynamic.items() if isinstance(key, str)}
    if dynamic.count() != 3 or dynamic_keys != _DYNAMIC_KEYS:
        raise TypeError("@get/@post function must return a map with exactly headers, query, body")

    operation_result = construct_http_operation(
        descriptor.get("verb"),
        base_url,
        descriptor.get("path"),
        dynamic.get("headers"),
        dynamic.get("query"),
        dynamic.get("body"),
        json_encode,
    )
    if not isinstance(operation_result, GeniaOptionSome):
        return operation_result

    return perform_http_send(
        operation_result.value,
        authority,
        timeout_ms,
        json_encode=json_encode,
        invoke=invoke,
        transport=transport,
    )
