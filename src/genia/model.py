"""Experimental R11 E11-1 callable model and deterministic fixture boundary."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .configuration import contains_protected, declassify
from .values import (
    GeniaDeclassificationAuthority,
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaProtected,
    GeniaRepresented,
    GeniaSymbol,
    _runtime_type_name,
    symbol,
)


_ROLES = {"system", "user", "assistant"}
_FINISH_REASONS = {"stop", "length", "filtered", "other"}
_ERROR_KINDS = {
    "authentication",
    "permission",
    "policy",
    "request",
    "unavailable",
    "other",
}
_RESPONSE_STAGES = {"message", "finish_reason", "usage", "provider_response"}


def _map(**values: Any) -> GeniaMap:
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _keys(value: GeniaMap) -> set[str] | None:
    result: set[str] = set()
    for key, _ in value.items():
        if not isinstance(key, str):
            return None
        result.add(key)
    return result


def _closed_map(value: Any, expected: set[str], label: str) -> GeniaMap:
    if not isinstance(value, GeniaMap):
        raise TypeError(f"model expected {label} map, received {_runtime_type_name(value)}")
    if _keys(value) != expected:
        raise TypeError(f"model expected closed {label} with keys {sorted(expected)}")
    return value


def _symbol_name(value: Any, label: str, allowed: set[str]) -> str:
    if not isinstance(value, GeniaSymbol) or value.name not in allowed:
        choices = ", ".join(sorted(allowed))
        raise TypeError(f"model expected {label} symbol in [{choices}]")
    return value.name


def _nonnegative_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TypeError(f"model expected {label} to be a non-negative integer")
    return value


def _validate_config(config: Any) -> GeniaMap:
    config = _closed_map(config, {"id", "timeout_ms"}, "config")
    model_id = config.get("id")
    if not isinstance(model_id, str) or model_id == "":
        raise TypeError("model expected config id to be a non-empty string")
    timeout = config.get("timeout_ms")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or timeout < 1
        or timeout > 300_000
    ):
        raise TypeError("model expected config timeout_ms to be an integer in 1..300000")
    return config


def _validate_content(content: Any, *, response: bool = False) -> GeniaMap:
    content = _closed_map(content, {"kind", "text"}, "content")
    _symbol_name(content.get("kind"), "content kind", {"text"})
    if not isinstance(content.get("text"), str):
        raise TypeError("model expected content text to be a string")
    return content


def _validate_message(message: Any, *, response: bool = False) -> GeniaMap:
    message = _closed_map(message, {"role", "content"}, "message")
    allowed = {"assistant"} if response else _ROLES
    _symbol_name(message.get("role"), "message role", allowed)
    _validate_content(message.get("content"), response=response)
    return message


def _validate_request(
    request: Any,
    compile_json_schema: Callable[[Any], Any],
    is_template_callable: Callable[[Any], bool],
) -> GeniaMap:
    if contains_protected(request):
        raise TypeError("protected-value: model-request")
    request = _closed_map(request, {"messages", "output"}, "request")
    messages = request.get("messages")
    if not isinstance(messages, list) or not messages:
        raise TypeError("model request expected a non-empty messages list")
    for message in messages:
        _validate_message(message)
    output_value = request.get("output")
    if not isinstance(output_value, GeniaMap):
        raise TypeError(
            "model expected output map, "
            f"received {_runtime_type_name(output_value)}"
        )
    output_kind = output_value.get("kind")
    kind_name = _symbol_name(output_kind, "output kind", {"json", "text"})
    expected_keys = {"kind"} if kind_name == "text" else {"kind", "schema", "template"}
    output = _closed_map(output_value, expected_keys, "output")
    kind = output.get("kind")
    if kind.name == "json":
        try:
            compiled = compile_json_schema(output.get("schema"))
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "model expected output schema accepted by json_schema"
            ) from exc
        if not isinstance(compiled, GeniaOptionSome):
            raise TypeError("model expected output schema accepted by json_schema")
        template = output.get("template")
        if not is_template_callable(template):
            raise TypeError(
                "model expected output template function, "
                f"received {_runtime_type_name(template)}"
            )
    return request


def _validate_usage(value: Any) -> None:
    if isinstance(value, GeniaOptionNone):
        if value.reason != "model-usage-unavailable" or value.context is not None:
            raise ValueError("usage")
        return
    if not isinstance(value, GeniaOptionSome) or value.context is not None:
        raise ValueError("usage")
    usage = value.value
    try:
        usage = _closed_map(
            usage,
            {"input_tokens", "output_tokens", "total_tokens"},
            "usage",
        )
        input_tokens = _nonnegative_integer(usage.get("input_tokens"), "input_tokens")
        output_tokens = _nonnegative_integer(usage.get("output_tokens"), "output_tokens")
        total_tokens = _nonnegative_integer(usage.get("total_tokens"), "total_tokens")
    except TypeError as exc:
        raise ValueError("usage") from exc
    if total_tokens != input_tokens + output_tokens:
        raise ValueError("usage")


def _invalid_response(stage: str) -> GeniaOptionErr:
    return GeniaOptionErr("model-response-invalid", _map(stage=symbol(stage)))


def _structured_invalid(stage: str, outcome: Any) -> GeniaOptionErr:
    return GeniaOptionErr(
        "model-structured-output-invalid",
        _map(stage=symbol(stage), outcome=outcome),
    )


def _validate_response(
    value: Any,
    output: GeniaMap,
    json_decode: Callable[[Any], Any],
    invoke_template: Callable[[Any, Any], Any],
) -> GeniaOptionSome | GeniaOptionErr:
    try:
        response = _closed_map(value, {"message", "finish_reason", "usage"}, "response")
    except TypeError:
        return _invalid_response("provider_response")
    try:
        _validate_message(response.get("message"), response=True)
    except TypeError:
        return _invalid_response("message")
    try:
        _symbol_name(response.get("finish_reason"), "finish reason", _FINISH_REASONS)
    except TypeError:
        return _invalid_response("finish_reason")
    try:
        _validate_usage(response.get("usage"))
    except ValueError:
        return _invalid_response("usage")
    if output.get("kind") == symbol("json"):
        text = response.get("message").get("content").get("text")
        decoded = json_decode(text)
        if isinstance(decoded, (GeniaOptionNone, GeniaOptionErr)):
            return _structured_invalid("json_decode", decoded)
        if (
            not isinstance(decoded, GeniaOptionSome)
            or not isinstance(decoded.value, GeniaRepresented)
            or decoded.value.facet != "json"
        ):
            raise TypeError("model json_decode callback must return a JSON Outcome")
        template_result = invoke_template(output.get("template"), decoded.value.value)
        if isinstance(template_result, (GeniaOptionNone, GeniaOptionErr)):
            return _structured_invalid("template", template_result)
        if not isinstance(template_result, GeniaOptionSome):
            raise TypeError(
                "model output Template must return Outcome, "
                f"received {_runtime_type_name(template_result)}"
            )
        response = response.put(
            "message",
            _map(
                role=symbol("assistant"),
                content=_map(kind=symbol("json"), value=decoded.value),
            ),
        )
    return GeniaOptionSome(response)


def _valid_exact_map(value: Any, expected: set[str]) -> bool:
    return isinstance(value, GeniaMap) and _keys(value) == expected


def _valid_error_context(result: GeniaOptionErr, timeout_ms: int) -> bool:
    context = result.context
    if result.reason == "model-timeout":
        return (
            _valid_exact_map(context, {"timeout_ms"})
            and isinstance(context.get("timeout_ms"), int)
            and not isinstance(context.get("timeout_ms"), bool)
            and context.get("timeout_ms") == timeout_ms
        )
    if result.reason == "model-rate-limited":
        if not _valid_exact_map(context, {"retry_after_ms"}):
            return False
        retry = context.get("retry_after_ms")
        if isinstance(retry, GeniaOptionSome):
            return retry.context is None and isinstance(retry.value, int) and not isinstance(retry.value, bool) and retry.value >= 0
        return isinstance(retry, GeniaOptionNone) and retry.reason == "model-retry-after-unavailable" and retry.context is None
    if result.reason in {"model-rejected", "model-transport-failure"}:
        return (
            _valid_exact_map(context, {"kind"})
            and isinstance(context.get("kind"), GeniaSymbol)
            and context.get("kind").name in _ERROR_KINDS
        )
    if result.reason == "model-response-invalid":
        return (
            _valid_exact_map(context, {"stage"})
            and isinstance(context.get("stage"), GeniaSymbol)
            and context.get("stage").name in _RESPONSE_STAGES
        )
    return False


class GeniaModelProvider:
    """Opaque Python-host deterministic provider capability."""

    __slots__ = ("_handler", "_attempt_count")

    def __init__(self, handler: Callable[[GeniaMap, GeniaMap, str], Any]):
        self._handler = handler
        self._attempt_count = 0

    @property
    def attempt_count(self) -> int:
        return self._attempt_count

    def _attempt(self, config: GeniaMap, request: GeniaMap, credential: str) -> Any:
        self._attempt_count += 1
        return self._handler(config, request, credential)

    def __repr__(self) -> str:
        return "<model-provider>"


class GeniaModel:
    """Ordinary one-argument callable model value."""

    __slots__ = (
        "_provider",
        "_config",
        "_credential",
        "_authority",
        "_compile_json_schema",
        "_json_decode",
        "_is_template_callable",
        "_invoke_template",
    )

    def __init__(
        self,
        provider: GeniaModelProvider,
        config: GeniaMap,
        credential: GeniaProtected,
        authority: GeniaDeclassificationAuthority,
        compile_json_schema: Callable[[Any], Any],
        json_decode: Callable[[Any], Any],
        is_template_callable: Callable[[Any], bool],
        invoke_template: Callable[[Any, Any], Any],
    ):
        self._provider = provider
        self._config = config
        self._credential = credential
        self._authority = authority
        self._compile_json_schema = compile_json_schema
        self._json_decode = json_decode
        self._is_template_callable = is_template_callable
        self._invoke_template = invoke_template

    def __call__(self, request: Any) -> Any:
        request = _validate_request(
            request, self._compile_json_schema, self._is_template_callable
        )
        ordinary_credential = declassify(self._authority, self._credential)
        if not isinstance(ordinary_credential, str):
            raise TypeError("model expected protected credential to carry a string")
        try:
            observation = self._provider._attempt(
                self._config, request, ordinary_credential
            )
        except Exception:
            return GeniaOptionErr(
                "model-transport-failure", _map(kind=symbol("other"))
            )
        if isinstance(observation, GeniaOptionSome):
            if observation.context is not None:
                return _invalid_response("provider_response")
            return _validate_response(
                observation.value,
                request.get("output"),
                self._json_decode,
                self._invoke_template,
            )
        if isinstance(observation, GeniaOptionNone):
            if observation.reason == "model-no-response" and observation.context is None:
                return observation
            return _invalid_response("provider_response")
        if isinstance(observation, GeniaOptionErr):
            if _valid_error_context(observation, self._config.get("timeout_ms")):
                return observation
            return _invalid_response("provider_response")
        return _invalid_response("provider_response")

    def __repr__(self) -> str:
        return "<function>"


def create_fixture_model_provider(
    handler: Callable[[GeniaMap, GeniaMap, str], Any],
) -> GeniaModelProvider:
    if not callable(handler):
        raise TypeError("fixture model provider expected a callable handler")
    return GeniaModelProvider(handler)


def construct_model(
    provider: Any,
    config: Any,
    credential: Any,
    authority: Any,
    *,
    compile_json_schema: Callable[[Any], Any],
    json_decode: Callable[[Any], Any],
    is_template_callable: Callable[[Any], bool],
    invoke_template: Callable[[Any, Any], Any],
) -> GeniaModel:
    if not isinstance(provider, GeniaModelProvider):
        raise TypeError(
            "model expected a model provider capability, "
            f"received {_runtime_type_name(provider)}"
        )
    validated_config = _validate_config(config)
    if not isinstance(credential, GeniaProtected):
        raise TypeError("model expected a protected credential")
    if not isinstance(authority, GeniaDeclassificationAuthority):
        raise TypeError("model expected a declassification authority")
    return GeniaModel(
        provider,
        validated_config,
        credential,
        authority,
        compile_json_schema,
        json_decode,
        is_template_callable,
        invoke_template,
    )
