"""Explicit immutable configuration-provider boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Any

from .values import (
    GeniaConfigProvider,
    GeniaDeclassificationAuthority,
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionNone,
    GeniaOptionSome,
    GeniaProtected,
    GeniaSymbol,
    contains_declassification_authority_value,
    _runtime_type_name,
    make_none,
)


_MISSING = object()
_DOTENV_FIELDS = {"kind", "path", "required"}


class _DotenvParseError(Exception):
    """Internal grammar-failure marker, normalized at the dotenv acquisition boundary."""
    pass


def _valid_key(value: Any) -> bool:
    """Accept a nonempty string without NUL, preserving case and whitespace."""
    return isinstance(value, str) and value != "" and "\0" not in value


def _config_args_error() -> GeniaOptionErr:
    """Return the atomic argument-parse err with source kind/stage only, no input text."""
    context = (
        GeniaMap()
        .put("source_kind", GeniaSymbol("arguments"))
        .put("stage", GeniaSymbol("parse"))
    )
    return GeniaOptionErr("config-source-invalid", context)


def _valid_config_arg_name(name: str) -> bool:
    """Accept ASCII letter-led alphanumeric segments joined by single hyphens.

    Callers supply strings; underscore, empty segments and non-ASCII names fail.
    """
    segments = name.split("-")
    return all(
        segment != ""
        and ("A" <= segment[0] <= "Z" or "a" <= segment[0] <= "z")
        and all(
            "A" <= char <= "Z"
            or "a" <= char <= "z"
            or "0" <= char <= "9"
            for char in segment[1:]
        )
        for segment in segments
    )


def normalize_config_args(args: Any) -> GeniaOptionSome | GeniaOptionErr:
    """Normalize explicit long-option/value pairs into some(values source descriptor).

    Require a list of strings, raising TypeError for misuse before parsing. Before
    the first standalone --, require --name followed by one exact string value
    (even empty or option-looking). Ignore later tokens. Uppercase names and replace
    hyphens with underscores; malformed or colliding keys return config-source-invalid
    with non-sensitive arguments/parse context and no partial descriptor.
    No argv acquisition, conversion, schema lookup or mutation of args occurs.
    """
    if not isinstance(args, list):
        raise TypeError(
            "config_args expected a list of strings, "
            f"received {_runtime_type_name(args)}"
        )
    if any(not isinstance(arg, str) for arg in args):
        raise TypeError("config_args expected a list containing only strings")

    values = GeniaMap()
    index = 0
    while index < len(args):
        option = args[index]
        if option == "--":
            break
        if not option.startswith("--"):
            return _config_args_error()
        name = option[2:]
        if not _valid_config_arg_name(name) or index + 1 >= len(args):
            return _config_args_error()
        normalized = name.replace("-", "_").upper()
        if values.has(normalized):
            return _config_args_error()
        values = values.put(normalized, args[index + 1])
        index += 2

    descriptor = GeniaMap().put("kind", GeniaSymbol("values")).put("values", values)
    return GeniaOptionSome(descriptor)


def _source_context(index: int) -> GeniaMap:
    """Return a fresh source_index-only diagnostic map using the supplied zero-based index."""
    return GeniaMap().put("source_index", index)


def _provider_error(reason: str, index: int) -> GeniaOptionErr:
    """Wrap a reason in err with source_index only; retain no source or exception detail."""
    return GeniaOptionErr(reason, _source_context(index))


def _dotenv_context(index: int, stage: str) -> GeniaMap:
    """Return source_index/dotenv-kind/stage context without path or file content."""
    return (
        GeniaMap()
        .put("source_index", index)
        .put("source_kind", GeniaSymbol("dotenv"))
        .put("stage", GeniaSymbol(stage))
    )


def _dotenv_error(reason: str, index: int, stage: str) -> GeniaOptionErr:
    """Wrap a reason and dotenv stage in a non-sensitive source-indexed err."""
    return GeniaOptionErr(reason, _dotenv_context(index, stage))


def _is_ascii_alpha(char: str) -> bool:
    """Test ASCII A-Z/a-z membership; callers provide one character."""
    return "A" <= char <= "Z" or "a" <= char <= "z"


def _is_dotenv_key_char(char: str) -> bool:
    """Accept an ASCII letter, digit or underscore within a dotenv identifier."""
    return _is_ascii_alpha(char) or "0" <= char <= "9" or char == "_"


def _skip_hws(line: str, index: int) -> int:
    """Return the first index after ASCII spaces/tabs starting at a valid line offset."""
    while index < len(line) and line[index] in " \t":
        index += 1
    return index


def _finish_quoted_dotenv_value(line: str, index: int) -> None:
    """Require end of line or a comment after a closing quote and optional spaces/tabs.

    Raise _DotenvParseError on trailing non-comment text; do not parse comment content.
    """
    index = _skip_hws(line, index)
    if index < len(line) and line[index] == "#":
        return
    if index != len(line):
        raise _DotenvParseError


def _parse_dotenv_value(line: str, index: int) -> str:
    """Parse one value beginning at a valid offset after leading spaces/tabs.

    Single quotes preserve literal contents with no escapes. Double quotes decode
    only backslash, double quote, n/r/t escapes. Unquoted values trim trailing
    spaces/tabs; # starts a comment only at value start or after space/tab.
    Unquoted quotes, backslash, CR/LF and BOM are invalid. Reject unterminated
    quotes, raw quoted CR/LF and unsupported escapes with _DotenvParseError.
    Return exact resulting text, including empty; no interpolation or conversion.
    """
    if index == len(line):
        return ""

    quote = line[index]
    if quote == "'":
        closing = line.find("'", index + 1)
        if closing < 0:
            raise _DotenvParseError
        value = line[index + 1 : closing]
        if "\r" in value or "\n" in value:
            raise _DotenvParseError
        _finish_quoted_dotenv_value(line, closing + 1)
        return value

    if quote == '"':
        output: list[str] = []
        index += 1
        escapes = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}
        while index < len(line):
            char = line[index]
            if char == '"':
                _finish_quoted_dotenv_value(line, index + 1)
                return "".join(output)
            if char in "\r\n":
                raise _DotenvParseError
            if char == "\\":
                index += 1
                if index >= len(line) or line[index] not in escapes:
                    raise _DotenvParseError
                output.append(escapes[line[index]])
            else:
                output.append(char)
            index += 1
        raise _DotenvParseError

    start = index
    while index < len(line):
        char = line[index]
        if char == "#":
            if index == start or line[index - 1] in " \t":
                return line[start:index].rstrip(" \t")
            raise _DotenvParseError
        if char in "\r\n'\"\\" or char == "\ufeff":
            raise _DotenvParseError
        index += 1
    return line[start:].rstrip(" \t")


def _parse_dotenv(text: str) -> dict[str, str]:
    """Parse already decoded, LF-normalized dotenv text into a fresh string dictionary.

    Ignore blank/comment lines and ASCII horizontal space around key/equal/value.
    Require ASCII identifier keys, rejecting exact duplicates and malformed lines
    with _DotenvParseError. Support a final unterminated line; reject residual CR.
    Caller removes one leading BOM and normalizes CRLF before invoking this helper.
    No export prefix, interpolation or multiline quoted value grammar is added.
    """
    values: dict[str, str] = {}
    for line in text.split("\n"):
        if "\r" in line:
            raise _DotenvParseError
        index = _skip_hws(line, 0)
        if index == len(line) or line[index] == "#":
            continue
        if not (_is_ascii_alpha(line[index]) or line[index] == "_"):
            raise _DotenvParseError
        key_start = index
        index += 1
        while index < len(line) and _is_dotenv_key_char(line[index]):
            index += 1
        key = line[key_start:index]
        index = _skip_hws(line, index)
        if index >= len(line) or line[index] != "=":
            raise _DotenvParseError
        if key in values:
            raise _DotenvParseError
        index = _skip_hws(line, index + 1)
        values[key] = _parse_dotenv_value(line, index)
    return values


def _validate_literal_values(values: GeniaMap, index: int) -> dict[str, str]:
    """Copy valid nonempty NUL-free string keys and string values from a GeniaMap.

    Raise TypeError with source index on misuse, excluding key/value text.
    Caller supplies the map; no input mutation or host acquisition occurs.
    """
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
    dotenv_snapshot_provider: Callable[[str], bytes] | None = None,
) -> GeniaOptionSome | GeniaOptionErr:
    """Validate explicit source descriptors, then acquire ordered immutable snapshots.

    Require a list of GeniaMaps with a symbol kind: values with a string map,
    environment, or dotenv with path/required fields. Validate every descriptor
    and literal value before host callbacks run; malformed arguments raise TypeError.
    No descriptor is acquired implicitly. Copy each source in declared order into
    read-only maps; first source containing a key wins, including an empty string.
    Return some(provider) only after every snapshot succeeds; no partial provider
    is returned, though earlier callbacks may already have performed effects.

    PYTHON REFERENCE HOST: injected environment callback supplies a string Mapping;
    injected dotenv callback takes the exact path and supplies UTF-8 bytes, once
    per descriptor. A missing callback returns config-source-unavailable. Callback
    Exceptions or invalid snapshots return config-provider-failure; BaseException
    is not normalized. Optional FileNotFoundError contributes an empty snapshot.
    Dotenv failures carry source_index/source_kind/stage only: acquire for missing
    capability/read failure, decode or parse for config-source-invalid. Remove one
    leading BOM and normalize CRLF before parsing.
    Paths, contents and raw exceptions never enter these normalized Outcomes.
    Lookup later performs no callback, refresh or file discovery.
    """
    if not isinstance(sources, list):
        raise TypeError(
            "config_provider expected a list of source descriptors, "
            f"received {_runtime_type_name(sources)}"
        )

    validated: list[tuple[str, Any]] = []
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
        elif kind.name == "dotenv":
            fields = {key for key, _ in descriptor.items() if isinstance(key, str)}
            path = descriptor.get("path") if descriptor.has("path") else None
            required = descriptor.get("required") if descriptor.has("required") else None
            if (
                fields != _DOTENV_FIELDS
                or not isinstance(path, str)
                or not _valid_key(path)
                or not isinstance(required, bool)
            ):
                raise TypeError(
                    "config_provider expected a valid dotenv descriptor "
                    f"at source index {index}"
                )
            validated.append(("dotenv", (path, required)))
        else:
            raise TypeError(
                f"config_provider received unsupported source kind at index {index}"
            )

    snapshots: list[Mapping[str, str]] = []
    for index, (kind, source_data) in enumerate(validated):
        if kind == "values":
            snapshots.append(MappingProxyType(dict(source_data or {})))
            continue
        if kind == "environment":
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
            continue

        path, required = source_data
        if dotenv_snapshot_provider is None:
            return _dotenv_error("config-source-unavailable", index, "acquire")
        try:
            content = dotenv_snapshot_provider(path)
            if not isinstance(content, bytes):
                raise TypeError("invalid dotenv snapshot")
        except FileNotFoundError:
            if not required:
                snapshots.append(MappingProxyType({}))
                continue
            return _dotenv_error("config-provider-failure", index, "acquire")
        except Exception:
            return _dotenv_error("config-provider-failure", index, "acquire")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return _dotenv_error("config-source-invalid", index, "decode")
        if text.startswith("\ufeff"):
            text = text[1:]
        try:
            parsed = _parse_dotenv(text.replace("\r\n", "\n"))
        except _DotenvParseError:
            return _dotenv_error("config-source-invalid", index, "parse")
        snapshots.append(MappingProxyType(dict(parsed)))

    return GeniaOptionSome(GeniaConfigProvider(tuple(snapshots)))


def _get_configuration(provider: Any, key: Any, operation: str) -> GeniaOptionSome | Any:
    """Validate provider then key and perform an exact snapshot lookup without host IO.

    Return some(string), including empty, or context-free none(config-missing).
    Misuse raises operation-labelled TypeError without key text; first source wins.
    """
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
    """Return some(exact string) or context-free none(config-missing) from snapshots.

    Require a configuration provider and nonempty NUL-free key; misuse raises
    config_get TypeError. No defaults, conversion, refresh or host IO occurs.
    """
    return _get_configuration(provider, key, "config_get")


def _validate_view_provider(provider: Any, operation: str) -> GeniaConfigProvider:
    """Return the same configuration provider or raise operation-labelled TypeError."""
    if not isinstance(provider, GeniaConfigProvider):
        raise TypeError(
            f"{operation} expected a configuration provider, "
            f"received {_runtime_type_name(provider)}"
        )
    return provider


def _validate_view_prefix(prefix: Any, operation: str) -> str:
    """Return exact NUL-free string prefix, allowing empty; otherwise raise TypeError."""
    if not isinstance(prefix, str) or "\0" in prefix:
        raise TypeError(
            f"{operation} expected a prefix string without NUL, "
            f"received {_runtime_type_name(prefix)}"
        )
    return prefix


def _validate_logical_name(logical_name: Any, operation: str) -> str:
    """Return exact nonempty NUL-free name or raise operation-labelled TypeError."""
    if not _valid_key(logical_name):
        raise TypeError(
            f"{operation} expected a non-empty logical name string without NUL, "
            f"received {_runtime_type_name(logical_name)}"
        )
    return logical_name


def construct_config_view(provider: Any, prefix: Any) -> Callable[[Any], Any]:
    """Validate and capture provider/prefix in an inert one-argument lookup callable.

    Empty prefix is valid; no lookup or host effect runs at construction. Each call
    validates the logical name and delegates once with exact prefix + name.
    Return existing lookup Outcome unchanged; no cache, conversion or fallback.
    """
    captured_provider = _validate_view_provider(provider, "config_view")
    captured_prefix = _validate_view_prefix(prefix, "config_view")

    def view(logical_name: Any) -> Any:
        """Validate a logical name and perform one captured-provider lookup for prefix + name.

        Return its exact Outcome; name misuse raises TypeError before lookup.
        """
        name = _validate_logical_name(logical_name, "config_view")
        return get_configuration(captured_provider, captured_prefix + name)

    return view


def _validated_purpose(purpose: Any, operation: str) -> GeniaSymbol:
    """Return the same nonempty symbol purpose; other values raise operation TypeError."""
    if not isinstance(purpose, GeniaSymbol) or purpose.name == "":
        raise TypeError(f"{operation} expected a non-empty purpose symbol")
    return purpose


def get_secret_configuration(provider: Any, key: Any, purpose: Any) -> Any:
    """Validate purpose, then lookup and protect a present string exactly once.

    Return some(provider-owned protected leaf), preserving success context; retain
    missing Outcome unchanged. Purpose/provider/key misuse raises TypeError.
    No declassification, audit, refresh or payload conversion occurs.
    """
    validated_purpose = _validated_purpose(purpose, "secret_get")
    result = _get_configuration(provider, key, "secret_get")
    if not isinstance(result, GeniaOptionSome):
        return result
    return GeniaOptionSome(provider.protect(result.value, validated_purpose), result.context)


def construct_secret_view(
    provider: Any, prefix: Any, purpose: Any
) -> Callable[[Any], Any]:
    """Validate/capture provider, exact prefix and purpose in an inert secret callable.

    Construction performs no lookup or audit. Each call validates the name and
    delegates once to secret_get for prefix + name and the captured purpose.
    Return its protected-success or missing Outcome; no fallback or refresh.
    """
    captured_provider = _validate_view_provider(provider, "secret_view")
    captured_prefix = _validate_view_prefix(prefix, "secret_view")
    captured_purpose = _validated_purpose(purpose, "secret_view")

    def view(logical_name: Any) -> Any:
        """Validate name then perform one secret lookup with captured prefix/purpose.

        Return existing Outcome; invalid name raises TypeError before lookup.
        """
        name = _validate_logical_name(logical_name, "secret_view")
        return get_secret_configuration(
            captured_provider, captured_prefix + name, captured_purpose
        )

    return view


def contains_protected(value: Any, _seen: set[int] | None = None) -> bool:
    """Find protected leaves recursively in supported containers without revealing payloads.

    Inspect Outcome value/reason/context, list/tuple, GeniaMap keys/values, pair
    head/tail and Sheet names/columns. Other values return False; opaque objects,
    callable closures and lazy sources are not traversed. Track container identity
    to terminate cycles, mutating a supplied internal _seen set when provided.
    Traversal/access failures propagate; no generic whole-object scan is promised.
    """
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
    """Raise protected-value TypeError if the supported-container scan finds a leaf.

    Do not reveal or transform payloads; caller invokes this before sink effects.
    """
    if contains_protected(value):
        raise TypeError(f"protected-value: {operation}")


def contains_declassification_authority(
    value: Any, _seen: set[int] | None = None
) -> bool:
    """Delegate supported-container, cycle-aware authority detection to the value layer.

    Pass the optional internal seen set through unchanged; no declassification occurs.
    """
    return contains_declassification_authority_value(value, _seen)


def reject_declassification_authority(value: Any, operation: str) -> None:
    """Raise an operation-labelled TypeError when a recursively detected authority crosses.

    Caller guards the boundary before effects; do not copy or reveal authority data.
    """
    if contains_declassification_authority(value):
        raise TypeError(f"declassification authority cannot cross {operation}")


def create_declassification_authority(
    provider: Any,
    purposes: Any,
    audit_recorder: Any,
) -> GeniaDeclassificationAuthority:
    """Mint an opaque authority for exactly one provider identity and allowed purposes.

    PYTHON REFERENCE HOST: privileged factory, not a Genia-visible constructor.
    Require provider, nonempty list of nonempty symbols, and callable audit recorder;
    misuse raises TypeError. Collapse duplicate purpose names into an immutable set.
    Capture recorder without calling it; no lookup, audit or payload acquisition.
    """
    if not isinstance(provider, GeniaConfigProvider):
        raise TypeError("authority factory expected a configuration provider")
    if not isinstance(purposes, list) or not purposes:
        raise TypeError("authority factory expected a non-empty purpose list")
    names: set[str] = set()
    for purpose in purposes:
        names.add(_validated_purpose(purpose, "authority factory").name)
    if not callable(audit_recorder):
        raise TypeError("authority factory expected an audit recorder")
    return GeniaDeclassificationAuthority(
        provider._identity, frozenset(names), audit_recorder
    )


def declassify(authority: Any, protected_value: Any) -> Any:
    """Authorize one protected layer and audit the attempt before returning its payload.

    Require authority first; misuse raises TypeError. With valid authority and an
    ordinary subject, audit failure with no purpose then raise TypeError. For a
    protected subject, require exact provider identity and allowed purpose; audit
    success/denial before returning or raising. Denial reveals no payload.
    Audit-recorder failures propagate and prevent return, even after authorization.
    Return exact carried value on success; no recursive unwrapping or conversion.
    """
    if not isinstance(authority, GeniaDeclassificationAuthority):
        raise TypeError("declassify expected a declassification authority")
    if not isinstance(protected_value, GeniaProtected):
        authority._audit(None, False)
        raise TypeError("declassify expected a protected value")
    allowed, purpose, value = protected_value._declassify_with(authority)
    authority._audit(purpose, allowed)
    if not allowed:
        raise TypeError("declassify authority does not permit protected value")
    return value


def protect_secret_default(provider: Any, purpose: Any, result: Any) -> Any:
    """Protect an already-computed default success once; retain none/err unchanged.

    Validate provider and purpose first. Ordinary results become some(protected);
    some results preserve context while protecting their payload. Reject success
    payloads containing existing protection with TypeError using the supported
    container scanner. This helper neither invokes nor selects the default, checks
    missingness, converts data, declassifies, nor audits; caller owns default timing.
    """
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
