"""Explicit immutable configuration-provider boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from .values import (
    GeniaConfigProvider,
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaProtected,
    GeniaSymbol,
    _runtime_type_name,
    make_none,
)


_MISSING = object()


def _valid_key(value: Any) -> bool:
    return isinstance(value, str) and value != "" and "\0" not in value


def _source_context(index: int) -> GeniaMap:
    return GeniaMap().put("source_index", index)


def _provider_error(reason: str, index: int) -> GeniaOptionErr:
    return GeniaOptionErr(reason, _source_context(index))


def _validate_literal_values(values: GeniaMap, index: int) -> dict[str, str]:
    copied: dict[str, str] = {}
    for key, value in values.items():
        if not _valid_key(key) or not isinstance(value, str):
            raise TypeError(
                "config_provider expected valid string keys and string values "
                f"at source index {index}"
            )
        copied[key] = value
    return copied


def construct_provider(
    sources: Any,
    environment_snapshot_provider: Callable[[], Mapping[str, str]] | None,
) -> GeniaOptionSome | GeniaOptionErr:
    if not isinstance(sources, list):
        raise TypeError(
            "config_provider expected a list of source descriptors, "
            f"received {_runtime_type_name(sources)}"
        )

    validated: list[tuple[str, dict[str, str] | None]] = []
    for index, descriptor in enumerate(sources):
        if not isinstance(descriptor, GeniaMap):
            raise TypeError(
                "config_provider expected a source descriptor map "
                f"at index {index}, received {_runtime_type_name(descriptor)}"
            )
        if not descriptor.has("kind"):
            raise TypeError(
                "config_provider expected a source kind symbol "
                f"at index {index}, received none"
            )
        kind = descriptor.get("kind")
        if not isinstance(kind, GeniaSymbol):
            raise TypeError(
                "config_provider expected a source kind symbol "
                f"at index {index}, received {_runtime_type_name(kind)}"
            )
        if kind.name == "values":
            if not descriptor.has("values"):
                raise TypeError(
                    f"config_provider expected a values map at index {index}, received none"
                )
            values = descriptor.get("values")
            if not isinstance(values, GeniaMap):
                raise TypeError(
                    "config_provider expected a values map "
                    f"at index {index}, received {_runtime_type_name(values)}"
                )
            validated.append(("values", _validate_literal_values(values, index)))
        elif kind.name == "environment":
            validated.append(("environment", None))
        else:
            raise TypeError(
                f"config_provider received unsupported source kind at index {index}"
            )

    snapshots: list[Mapping[str, str]] = []
    for index, (kind, literal) in enumerate(validated):
        if kind == "values":
            snapshots.append(MappingProxyType(dict(literal or {})))
            continue
        if environment_snapshot_provider is None:
            return _provider_error("config-source-unavailable", index)
        try:
            acquired = environment_snapshot_provider()
            if not isinstance(acquired, Mapping):
                raise TypeError("invalid environment snapshot")
            copied: dict[str, str] = {}
            for key, value in acquired.items():
                if not _valid_key(key) or not isinstance(value, str):
                    raise TypeError("invalid environment snapshot")
                copied[key] = value
            snapshots.append(MappingProxyType(copied))
        except Exception:
            return _provider_error("config-provider-failure", index)

    return GeniaOptionSome(GeniaConfigProvider(tuple(snapshots)))


def _get_configuration(provider: Any, key: Any, operation: str) -> GeniaOptionSome | Any:
    if not isinstance(provider, GeniaConfigProvider):
        raise TypeError(
            f"{operation} expected a configuration provider, "
            f"received {_runtime_type_name(provider)}"
        )
    if not _valid_key(key):
        raise TypeError(
            f"{operation} expected a non-empty configuration key string without NUL, "
            f"received {_runtime_type_name(key)}"
        )
    value = provider.lookup(key, _MISSING)
    if value is _MISSING:
        return make_none("config-missing")
    return GeniaOptionSome(value)


def get_configuration(provider: Any, key: Any) -> GeniaOptionSome | Any:
    return _get_configuration(provider, key, "config_get")


def _validated_purpose(purpose: Any, operation: str) -> GeniaSymbol:
    if not isinstance(purpose, GeniaSymbol) or purpose.name == "":
        raise TypeError(f"{operation} expected a non-empty purpose symbol")
    return purpose


def get_secret_configuration(provider: Any, key: Any, purpose: Any) -> Any:
    validated_purpose = _validated_purpose(purpose, "secret_get")
    result = _get_configuration(provider, key, "secret_get")
    if not isinstance(result, GeniaOptionSome):
        return result
    return GeniaOptionSome(provider.protect(result.value, validated_purpose), result.context)


def contains_protected(value: Any, _seen: set[int] | None = None) -> bool:
    if isinstance(value, GeniaProtected):
        return True
    if _seen is None:
        _seen = set()
    value_id = id(value)
    if value_id in _seen:
        return False
    if isinstance(value, (GeniaOptionSome, GeniaOptionNone, GeniaOptionErr)):
        _seen.add(value_id)
        return (
            contains_protected(getattr(value, "value", None), _seen)
            or contains_protected(getattr(value, "reason", None), _seen)
            or contains_protected(value.context, _seen)
        )
    if isinstance(value, (list, tuple)):
        _seen.add(value_id)
        return any(contains_protected(item, _seen) for item in value)
    if isinstance(value, GeniaMap):
        _seen.add(value_id)
        return any(
            contains_protected(key, _seen) or contains_protected(item, _seen)
            for key, item in value.items()
        )
    if value.__class__.__name__ == "GeniaPair":
        _seen.add(value_id)
        return contains_protected(value.head, _seen) or contains_protected(
            value.tail, _seen
        )
    if value.__class__.__name__ == "GeniaSheet":
        _seen.add(value_id)
        return any(
            contains_protected(name, _seen)
            or contains_protected(list(column), _seen)
            for name, column in value.columns
        )
    return False


def reject_protected(value: Any, operation: str) -> None:
    if contains_protected(value):
        raise TypeError(f"protected-value: {operation}")


def protect_secret_default(provider: Any, purpose: Any, result: Any) -> Any:
    if not isinstance(provider, GeniaConfigProvider):
        raise TypeError(
            "secret_get_or expected a configuration provider, "
            f"received {_runtime_type_name(provider)}"
        )
    validated_purpose = _validated_purpose(purpose, "secret_get_or")
    if isinstance(result, (GeniaOptionNone, GeniaOptionErr)):
        return result
    if isinstance(result, GeniaOptionSome):
        if contains_protected(result.value):
            raise TypeError("secret_get_or default success cannot contain a protected value")
        return GeniaOptionSome(
            provider.protect(result.value, validated_purpose), result.context
        )
    if contains_protected(result):
        raise TypeError("secret_get_or default success cannot contain a protected value")
    return GeniaOptionSome(provider.protect(result, validated_purpose))
