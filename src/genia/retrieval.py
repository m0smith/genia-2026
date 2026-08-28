"""Experimental portable R12 document chunk and provenance boundary."""

from __future__ import annotations

import math
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


def _embed_closed_map(value: Any, expected: set[str], label: str) -> GeniaMap:
    if not isinstance(value, GeniaMap):
        raise TypeError(f"embed expected {label} map, received {_runtime_type_name(value)}")
    if _keys(value) != expected:
        raise TypeError(f"embed expected closed {label} with keys {sorted(expected)}")
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


def _valid_chunk(value: Any) -> bool:
    if not isinstance(value, GeniaMap) or _keys(value) != {"meta", "source", "text"}:
        return False
    text = value.get("text")
    if not isinstance(text, str) or text == "":
        return False
    source = value.get("source")
    if not isinstance(source, GeniaMap) or _keys(source) != {"doc_id", "length", "offset"}:
        return False
    doc_id = source.get("doc_id")
    offset = source.get("offset")
    length = source.get("length")
    if not isinstance(doc_id, str) or doc_id == "":
        return False
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        return False
    if isinstance(length, bool) or not isinstance(length, int) or length <= 0:
        return False
    if length != len(text):
        return False
    meta = value.get("meta")
    return (
        isinstance(meta, GeniaRepresented)
        and meta.facet == "json"
        and isinstance(meta.value, GeniaMap)
        and _valid_json_value(meta.value)
    )


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


_EMBED_ERROR_KINDS = {
    "authentication",
    "permission",
    "policy",
    "request",
    "unavailable",
    "other",
}


def _validate_embed_config(value: Any) -> GeniaMap:
    config = _embed_closed_map(value, {"id", "space", "timeout_ms"}, "config")
    if not isinstance(config.get("id"), str) or config.get("id") == "":
        raise TypeError("embed expected config id to be a non-empty string")
    if not isinstance(config.get("space"), str) or config.get("space") == "":
        raise TypeError("embed expected config space to be a non-empty string")
    timeout = config.get("timeout_ms")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or timeout < 1
        or timeout > 300_000
    ):
        raise TypeError("embed expected config timeout_ms to be an integer in 1..300000")
    return config


def _validate_embedding_input(value: Any) -> tuple[str, Any] | GeniaOptionErr:
    if contains_protected(value):
        raise TypeError("protected-value: embed-input")
    if not isinstance(value, GeniaMap):
        raise TypeError(
            f"embed expected input map, received {_runtime_type_name(value)}"
        )
    kind = value.get("kind")
    if not isinstance(kind, GeniaSymbol) or kind.name not in {"chunk", "query"}:
        raise TypeError("embed expected input kind symbol in [chunk, query]")
    if kind.name == "query":
        value = _embed_closed_map(value, {"kind", "text"}, "query input")
        text = value.get("text")
        if not isinstance(text, str) or text == "":
            raise TypeError("embed expected query text to be a non-empty string")
        return "query", text
    value = _embed_closed_map(value, {"chunk", "kind"}, "chunk input")
    chunk = value.get("chunk")
    if not _valid_chunk(chunk):
        return GeniaOptionErr("chunk-invalid", _map(stage=symbol("document")))
    return "chunk", chunk


def _embed_invalid(stage: str) -> GeniaOptionErr:
    return GeniaOptionErr("embed-response-invalid", _map(stage=symbol(stage)))


def _valid_embed_error(value: GeniaOptionErr, timeout_ms: int) -> bool:
    context = value.context
    if value.reason == "embed-timeout":
        return (
            isinstance(context, GeniaMap)
            and _keys(context) == {"timeout_ms"}
            and context.get("timeout_ms") == timeout_ms
            and not isinstance(context.get("timeout_ms"), bool)
        )
    if value.reason == "embed-rate-limited":
        if not isinstance(context, GeniaMap) or _keys(context) != {"retry_after_ms"}:
            return False
        retry = context.get("retry_after_ms")
        if isinstance(retry, GeniaOptionSome):
            return (
                retry.context is None
                and isinstance(retry.value, int)
                and not isinstance(retry.value, bool)
                and retry.value >= 0
            )
        return (
            isinstance(retry, GeniaOptionNone)
            and retry.reason == "embed-retry-after-unavailable"
            and retry.context is None
        )
    if value.reason in {"embed-rejected", "embed-transport-failure"}:
        return (
            isinstance(context, GeniaMap)
            and _keys(context) == {"kind"}
            and isinstance(context.get("kind"), GeniaSymbol)
            and context.get("kind").name in _EMBED_ERROR_KINDS
        )
    return False


def _validate_embedding(value: Any, configured_space: str) -> tuple[list[Any], int] | GeniaOptionErr:
    if not isinstance(value, GeniaMap) or _keys(value) != {"dims", "space", "vector"}:
        return _embed_invalid("provider_response")
    vector = value.get("vector")
    if (
        not isinstance(vector, list)
        or not vector
        or any(
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
            for item in vector
        )
    ):
        return _embed_invalid("vector")
    dims = value.get("dims")
    if isinstance(dims, bool) or not isinstance(dims, int) or dims <= 0 or dims != len(vector):
        return _embed_invalid("dims")
    space = value.get("space")
    if not isinstance(space, str) or space == "" or space != configured_space:
        return _embed_invalid("space")
    return vector, dims


class GeniaEmbedProvider:
    """Opaque Python-host deterministic embedding capability."""

    __slots__ = ("_handler", "_attempt_count")

    def __init__(self, handler: Callable[[GeniaMap, GeniaMap, str], Any]):
        self._handler = handler
        self._attempt_count = 0

    @property
    def attempt_count(self) -> int:
        return self._attempt_count

    def _attempt(self, config: GeniaMap, value: GeniaMap, credential: str) -> Any:
        self._attempt_count += 1
        return self._handler(config, value, credential)

    def __repr__(self) -> str:
        return "<embed-provider>"


class GeniaEmbedder:
    """Ordinary one-argument embedding callable."""

    __slots__ = ("_authority", "_config", "_credential", "_provider")

    def __init__(
        self,
        provider: GeniaEmbedProvider,
        config: GeniaMap,
        credential: GeniaProtected,
        authority: GeniaDeclassificationAuthority,
    ):
        self._provider = provider
        self._config = config
        self._credential = credential
        self._authority = authority

    def __call__(self, value: Any) -> Any:
        validated = _validate_embedding_input(value)
        if isinstance(validated, GeniaOptionErr):
            return validated
        kind, identity = validated
        ordinary_credential = declassify(self._authority, self._credential)
        if not isinstance(ordinary_credential, str):
            raise TypeError("embed expected protected credential to carry a string")
        try:
            observation = self._provider._attempt(
                self._config, value, ordinary_credential
            )
        except Exception:
            return GeniaOptionErr(
                "embed-transport-failure", _map(kind=symbol("other"))
            )
        if isinstance(observation, GeniaOptionErr):
            if _valid_embed_error(observation, self._config.get("timeout_ms")):
                return observation
            return _embed_invalid("provider_response")
        if not isinstance(observation, GeniaOptionSome) or observation.context is not None:
            return _embed_invalid("provider_response")
        response = observation.value
        expected_keys = {"embedding", "text"} if kind == "query" else {"chunk", "embedding"}
        if not isinstance(response, GeniaMap) or _keys(response) != expected_keys:
            return _embed_invalid("provider_response")
        response_identity = response.get("text" if kind == "query" else "chunk")
        if response_identity != identity:
            return _embed_invalid("input_identity")
        embedding = _validate_embedding(response.get("embedding"), self._config.get("space"))
        if isinstance(embedding, GeniaOptionErr):
            return embedding
        vector, dims = embedding
        normalized_embedding = _map(
            vector=vector,
            dims=dims,
            space=self._config.get("space"),
        )
        if kind == "query":
            return GeniaOptionSome(_map(text=identity, embedding=normalized_embedding))
        return GeniaOptionSome(_map(chunk=identity, embedding=normalized_embedding))

    def __repr__(self) -> str:
        return "<function>"


def create_fixture_embed_provider(
    handler: Callable[[GeniaMap, GeniaMap, str], Any],
) -> GeniaEmbedProvider:
    if not callable(handler):
        raise TypeError("fixture embed provider expected a callable handler")
    return GeniaEmbedProvider(handler)


def construct_embed(
    provider: Any,
    config: Any,
    credential: Any,
    authority: Any,
) -> GeniaEmbedder:
    if not isinstance(provider, GeniaEmbedProvider):
        raise TypeError(
            "embed expected an embed provider capability, "
            f"received {_runtime_type_name(provider)}"
        )
    validated_config = _validate_embed_config(config)
    if not isinstance(credential, GeniaProtected):
        raise TypeError("embed expected a protected credential")
    if not isinstance(authority, GeniaDeclassificationAuthority):
        raise TypeError("embed expected a declassification authority")
    return GeniaEmbedder(provider, validated_config, credential, authority)


_INDEX_ERROR_KINDS = _EMBED_ERROR_KINDS


def _validate_index_config(value: Any) -> GeniaMap:
    config = _embed_closed_map(value, {"id", "timeout_ms"}, "config")
    if not isinstance(config.get("id"), str) or config.get("id") == "":
        raise TypeError("index expected config id to be a non-empty string")
    timeout = config.get("timeout_ms")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or timeout < 1
        or timeout > 300_000
    ):
        raise TypeError("index expected config timeout_ms to be an integer in 1..300000")
    return config


def _index_invalid(stage: str) -> GeniaOptionErr:
    return GeniaOptionErr("index-response-invalid", _map(stage=symbol(stage)))


def _embedding_invalid(stage: str) -> GeniaOptionErr:
    return GeniaOptionErr("embedding-invalid", _map(stage=symbol(stage)))


def _validate_index_corpus(value: Any) -> tuple[str, int] | GeniaOptionErr:
    if contains_protected(value):
        raise TypeError("protected-value: index-input")
    if not isinstance(value, list) or not value:
        raise TypeError("index expected a non-empty list of embedded chunks")
    corpus_space: str | None = None
    corpus_dims: int | None = None
    for embedded in value:
        if not isinstance(embedded, GeniaMap) or _keys(embedded) != {"chunk", "embedding"}:
            raise TypeError("index expected closed embedded chunk with keys ['chunk', 'embedding']")
        if not _valid_chunk(embedded.get("chunk")):
            return GeniaOptionErr("chunk-invalid", _map(stage=symbol("document")))
        embedding = embedded.get("embedding")
        if not isinstance(embedding, GeniaMap) or _keys(embedding) != {"dims", "space", "vector"}:
            return _embedding_invalid("vector")
        vector = embedding.get("vector")
        if (
            not isinstance(vector, list)
            or not vector
            or any(
                isinstance(item, bool)
                or not isinstance(item, (int, float))
                or not math.isfinite(item)
                for item in vector
            )
        ):
            return _embedding_invalid("vector")
        dims = embedding.get("dims")
        if isinstance(dims, bool) or not isinstance(dims, int) or dims <= 0 or dims != len(vector):
            return _embedding_invalid("dims")
        space = embedding.get("space")
        if not isinstance(space, str) or space == "":
            return _embedding_invalid("space")
        if corpus_dims is None:
            corpus_dims = dims
            corpus_space = space
            continue
        if dims != corpus_dims:
            return GeniaOptionErr(
                "index-embedding-incompatible", _map(kind=symbol("dimension"))
            )
        if space != corpus_space:
            return GeniaOptionErr(
                "index-embedding-incompatible", _map(kind=symbol("space"))
            )
    assert corpus_space is not None and corpus_dims is not None
    return corpus_space, corpus_dims


def _valid_index_error(value: GeniaOptionErr, timeout_ms: int) -> bool:
    context = value.context
    if value.reason == "index-timeout":
        return (
            isinstance(context, GeniaMap)
            and _keys(context) == {"timeout_ms"}
            and context.get("timeout_ms") == timeout_ms
            and not isinstance(context.get("timeout_ms"), bool)
        )
    if value.reason == "index-rate-limited":
        if not isinstance(context, GeniaMap) or _keys(context) != {"retry_after_ms"}:
            return False
        retry = context.get("retry_after_ms")
        if isinstance(retry, GeniaOptionSome):
            return (
                retry.context is None
                and isinstance(retry.value, int)
                and not isinstance(retry.value, bool)
                and retry.value >= 0
            )
        return (
            isinstance(retry, GeniaOptionNone)
            and retry.reason == "index-retry-after-unavailable"
            and retry.context is None
        )
    if value.reason in {"index-rejected", "index-transport-failure"}:
        return (
            isinstance(context, GeniaMap)
            and _keys(context) == {"kind"}
            and isinstance(context.get("kind"), GeniaSymbol)
            and context.get("kind").name in _INDEX_ERROR_KINDS
        )
    return False


class _FixtureIndexResult:
    __slots__ = ("backend_ref",)

    def __init__(self, backend_ref: Any):
        self.backend_ref = backend_ref


class GeniaIndexHandle:
    """Opaque host-produced index compatibility handle."""

    __slots__ = (
        "__backend_ref",
        "__compatibility_identity",
        "__corpus_chunks",
        "__dims",
        "__space",
    )

    def __init__(
        self,
        compatibility_identity: object,
        space: str,
        dims: int,
        backend_ref: Any,
        corpus_chunks: tuple[Any, ...],
    ):
        self.__compatibility_identity = compatibility_identity
        self.__space = space
        self.__dims = dims
        self.__backend_ref = backend_ref
        self.__corpus_chunks = corpus_chunks

    def __eq__(self, other: object) -> bool:
        raise TypeError("index handles cannot be compared")

    def __hash__(self) -> int:
        raise TypeError("index handles cannot be hashed")

    def __copy__(self) -> Any:
        raise TypeError("index handles cannot be copied")

    def __deepcopy__(self, memo: Any) -> Any:
        raise TypeError("index handles cannot be copied")

    def __repr__(self) -> str:
        return "<index-handle>"


class GeniaIndexProvider:
    """Opaque Python-host deterministic indexing capability."""

    __slots__ = ("_compatibility_identity", "_handler", "_attempt_count")

    def __init__(self, handler: Callable[[GeniaMap, list[Any], str], Any]):
        self._handler = handler
        self._attempt_count = 0
        self._compatibility_identity = object()

    @property
    def attempt_count(self) -> int:
        return self._attempt_count

    def _attempt(self, config: GeniaMap, corpus: list[Any], credential: str) -> Any:
        self._attempt_count += 1
        return self._handler(config, corpus, credential)

    def _handle_is_compatible_for_test(self, handle: Any, space: str, dims: int) -> bool:
        return (
            isinstance(handle, GeniaIndexHandle)
            and handle._GeniaIndexHandle__compatibility_identity is self._compatibility_identity
            and handle._GeniaIndexHandle__space == space
            and handle._GeniaIndexHandle__dims == dims
        )

    def _backend_ref_for_test(self, handle: Any) -> Any:
        if not isinstance(handle, GeniaIndexHandle):
            raise TypeError("expected index handle")
        return handle._GeniaIndexHandle__backend_ref

    def __repr__(self) -> str:
        return "<index-provider>"


class GeniaIndexer:
    """Ordinary one-argument indexing callable."""

    __slots__ = ("_authority", "_config", "_credential", "_provider")

    def __init__(
        self,
        provider: GeniaIndexProvider,
        config: GeniaMap,
        credential: GeniaProtected,
        authority: GeniaDeclassificationAuthority,
    ):
        self._provider = provider
        self._config = config
        self._credential = credential
        self._authority = authority

    def __call__(self, corpus: Any) -> Any:
        validated = _validate_index_corpus(corpus)
        if isinstance(validated, GeniaOptionErr):
            return validated
        space, dims = validated
        ordinary_credential = declassify(self._authority, self._credential)
        if not isinstance(ordinary_credential, str):
            raise TypeError("index expected protected credential to carry a string")
        try:
            observation = self._provider._attempt(self._config, corpus, ordinary_credential)
        except Exception:
            return GeniaOptionErr(
                "index-transport-failure", _map(kind=symbol("other"))
            )
        if isinstance(observation, GeniaOptionErr):
            if _valid_index_error(observation, self._config.get("timeout_ms")):
                return observation
            return _index_invalid("provider_response")
        if not isinstance(observation, GeniaOptionSome) or observation.context is not None:
            return _index_invalid("provider_response")
        if not isinstance(observation.value, _FixtureIndexResult):
            return _index_invalid("index_handle")
        return GeniaOptionSome(
            GeniaIndexHandle(
                self._provider._compatibility_identity,
                space,
                dims,
                observation.value.backend_ref,
                tuple(embedded.get("chunk") for embedded in corpus),
            )
        )

    def __repr__(self) -> str:
        return "<function>"


def create_fixture_index_provider(
    handler: Callable[[GeniaMap, list[Any], str], Any],
) -> GeniaIndexProvider:
    if not callable(handler):
        raise TypeError("fixture index provider expected a callable handler")
    return GeniaIndexProvider(handler)


def create_fixture_index_result(backend_ref: Any) -> _FixtureIndexResult:
    return _FixtureIndexResult(backend_ref)


def construct_index(
    provider: Any,
    config: Any,
    credential: Any,
    authority: Any,
) -> GeniaIndexer:
    if not isinstance(provider, GeniaIndexProvider):
        raise TypeError(
            "index expected an index provider capability, "
            f"received {_runtime_type_name(provider)}"
        )
    validated_config = _validate_index_config(config)
    if not isinstance(credential, GeniaProtected):
        raise TypeError("index expected a protected credential")
    if not isinstance(authority, GeniaDeclassificationAuthority):
        raise TypeError("index expected a declassification authority")
    return GeniaIndexer(provider, validated_config, credential, authority)


_RETRIEVE_ERROR_KINDS = _EMBED_ERROR_KINDS


def _validate_retrieve_config(value: Any) -> GeniaMap:
    config = _embed_closed_map(value, {"id", "timeout_ms"}, "config")
    if not isinstance(config.get("id"), str) or config.get("id") == "":
        raise TypeError("retrieve expected config id to be a non-empty string")
    timeout = config.get("timeout_ms")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or timeout < 1
        or timeout > 300_000
    ):
        raise TypeError(
            "retrieve expected config timeout_ms to be an integer in 1..300000"
        )
    return config


def _validate_query_embedding(value: Any) -> tuple[str, int]:
    if contains_protected(value):
        raise TypeError("protected-value: retrieve-input")
    query = _embed_closed_map(value, {"embedding", "text"}, "query embedding")
    text = query.get("text")
    if not isinstance(text, str) or text == "":
        raise TypeError("retrieve expected query text to be a non-empty string")
    embedding = _embed_closed_map(
        query.get("embedding"), {"dims", "space", "vector"}, "embedding"
    )
    vector = embedding.get("vector")
    if (
        not isinstance(vector, list)
        or not vector
        or any(
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
            for item in vector
        )
    ):
        raise TypeError("retrieve expected embedding vector to be non-empty and finite")
    dims = embedding.get("dims")
    if (
        isinstance(dims, bool)
        or not isinstance(dims, int)
        or dims <= 0
        or dims != len(vector)
    ):
        raise TypeError("retrieve expected embedding dims to equal vector length")
    space = embedding.get("space")
    if not isinstance(space, str) or space == "":
        raise TypeError("retrieve expected embedding space to be a non-empty string")
    return space, dims


def _retrieve_invalid(stage: str) -> GeniaOptionErr:
    return GeniaOptionErr("retrieve-response-invalid", _map(stage=symbol(stage)))


def _valid_retrieve_error(value: GeniaOptionErr, timeout_ms: int) -> bool:
    context = value.context
    if value.reason == "retrieve-timeout":
        return (
            isinstance(context, GeniaMap)
            and _keys(context) == {"timeout_ms"}
            and context.get("timeout_ms") == timeout_ms
            and not isinstance(context.get("timeout_ms"), bool)
        )
    if value.reason == "retrieve-rate-limited":
        if not isinstance(context, GeniaMap) or _keys(context) != {"retry_after_ms"}:
            return False
        retry = context.get("retry_after_ms")
        if isinstance(retry, GeniaOptionSome):
            return (
                retry.context is None
                and isinstance(retry.value, int)
                and not isinstance(retry.value, bool)
                and retry.value >= 0
            )
        return (
            isinstance(retry, GeniaOptionNone)
            and retry.reason == "retrieve-retry-after-unavailable"
            and retry.context is None
        )
    if value.reason in {"retrieve-rejected", "retrieve-transport-failure"}:
        return (
            isinstance(context, GeniaMap)
            and _keys(context) == {"kind"}
            and isinstance(context.get("kind"), GeniaSymbol)
            and context.get("kind").name in _RETRIEVE_ERROR_KINDS
        )
    return False


class _FixtureRetrieveResult:
    __slots__ = ("results",)

    def __init__(self, results: Any):
        self.results = results


class GeniaRetrieveProvider:
    """Opaque Python-host deterministic retrieval capability."""

    __slots__ = ("_attempt_count", "_compatibility_identity", "_handler")

    def __init__(
        self,
        compatibility_identity: object,
        handler: Callable[[GeniaMap, Any, GeniaMap, int, str], Any],
    ):
        self._compatibility_identity = compatibility_identity
        self._handler = handler
        self._attempt_count = 0

    @property
    def attempt_count(self) -> int:
        return self._attempt_count

    def _attempt(
        self,
        config: GeniaMap,
        backend_ref: Any,
        query: GeniaMap,
        k: int,
        credential: str,
    ) -> Any:
        self._attempt_count += 1
        return self._handler(config, backend_ref, query, k, credential)

    def __repr__(self) -> str:
        return "<retrieve-provider>"


class GeniaRetriever:
    """Ordinary three-argument retrieval callable."""

    __slots__ = ("_authority", "_config", "_credential", "_provider")

    def __init__(
        self,
        provider: GeniaRetrieveProvider,
        config: GeniaMap,
        credential: GeniaProtected,
        authority: GeniaDeclassificationAuthority,
    ):
        self._provider = provider
        self._config = config
        self._credential = credential
        self._authority = authority

    def __call__(self, handle: Any, query: Any, k: Any) -> Any:
        space, dims = _validate_query_embedding(query)
        if isinstance(k, bool) or not isinstance(k, int) or k < 1 or k > 1000:
            raise TypeError("retrieve expected k to be an integer in 1..1000")
        if not isinstance(handle, GeniaIndexHandle):
            raise TypeError("retrieve expected an index handle")
        if (
            handle._GeniaIndexHandle__compatibility_identity
            is not self._provider._compatibility_identity
        ):
            return GeniaOptionErr(
                "retrieve-capability-incompatible",
                _map(kind=symbol("index_handle")),
            )
        if handle._GeniaIndexHandle__space != space:
            return GeniaOptionErr(
                "retrieve-embedding-incompatible", _map(kind=symbol("space"))
            )
        if handle._GeniaIndexHandle__dims != dims:
            return GeniaOptionErr(
                "retrieve-embedding-incompatible", _map(kind=symbol("dimension"))
            )
        ordinary_credential = declassify(self._authority, self._credential)
        if not isinstance(ordinary_credential, str):
            raise TypeError("retrieve expected protected credential to carry a string")
        try:
            observation = self._provider._attempt(
                self._config,
                handle._GeniaIndexHandle__backend_ref,
                query,
                k,
                ordinary_credential,
            )
        except Exception:
            return GeniaOptionErr(
                "retrieve-transport-failure", _map(kind=symbol("other"))
            )
        if isinstance(observation, GeniaOptionErr):
            if _valid_retrieve_error(observation, self._config.get("timeout_ms")):
                return observation
            return _retrieve_invalid("provider_response")
        if not isinstance(observation, GeniaOptionSome) or observation.context is not None:
            return _retrieve_invalid("provider_response")
        if not isinstance(observation.value, _FixtureRetrieveResult):
            return _retrieve_invalid("provider_response")
        results = observation.value.results
        if not isinstance(results, list):
            return _retrieve_invalid("result")
        if len(results) > k:
            return _retrieve_invalid("limit")
        corpus_chunks = list(handle._GeniaIndexHandle__corpus_chunks)
        used: list[int] = []
        normalized: list[GeniaMap] = []
        for result in results:
            if not isinstance(result, GeniaMap) or _keys(result) != {"chunk", "score"}:
                return _retrieve_invalid("result")
            chunk = result.get("chunk")
            if not _valid_chunk(chunk):
                return _retrieve_invalid("chunk")
            score = result.get("score")
            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(score)
            ):
                return _retrieve_invalid("score")
            occurrence = next(
                (
                    index
                    for index, indexed_chunk in enumerate(corpus_chunks)
                    if index not in used and chunk == indexed_chunk
                ),
                None,
            )
            if occurrence is None:
                return _retrieve_invalid("provenance")
            used.append(occurrence)
            normalized.append(_map(chunk=corpus_chunks[occurrence], score=score))
        if not normalized:
            return GeniaOptionNone("retrieval-no-results")
        return GeniaOptionSome(normalized)

    def __repr__(self) -> str:
        return "<function>"


def create_fixture_retrieve_provider(
    index_provider: Any,
    handler: Callable[[GeniaMap, Any, GeniaMap, int, str], Any],
) -> GeniaRetrieveProvider:
    if not isinstance(index_provider, GeniaIndexProvider):
        raise TypeError("fixture retrieve provider expected an index provider")
    if not callable(handler):
        raise TypeError("fixture retrieve provider expected a callable handler")
    return GeniaRetrieveProvider(index_provider._compatibility_identity, handler)


def create_fixture_retrieve_result(results: Any) -> _FixtureRetrieveResult:
    return _FixtureRetrieveResult(results)


def construct_retrieve(
    provider: Any,
    config: Any,
    credential: Any,
    authority: Any,
) -> GeniaRetriever:
    if not isinstance(provider, GeniaRetrieveProvider):
        raise TypeError(
            "retrieve expected a retrieve provider capability, "
            f"received {_runtime_type_name(provider)}"
        )
    validated_config = _validate_retrieve_config(config)
    if not isinstance(credential, GeniaProtected):
        raise TypeError("retrieve expected a protected credential")
    if not isinstance(authority, GeniaDeclassificationAuthority):
        raise TypeError("retrieve expected a declassification authority")
    return GeniaRetriever(provider, validated_config, credential, authority)


_RERANK_ERROR_KINDS = _EMBED_ERROR_KINDS


def _validate_rerank_config(value: Any) -> GeniaMap:
    config = _embed_closed_map(value, {"id", "timeout_ms"}, "config")
    if not isinstance(config.get("id"), str) or config.get("id") == "":
        raise TypeError("rerank expected config id to be a non-empty string")
    timeout = config.get("timeout_ms")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int)
        or timeout < 1
        or timeout > 300_000
    ):
        raise TypeError(
            "rerank expected config timeout_ms to be an integer in 1..300000"
        )
    return config


def _validate_retrieved_chunks(value: Any) -> list[GeniaMap]:
    if contains_protected(value):
        raise TypeError("protected-value: rerank-input")
    if not isinstance(value, list):
        raise TypeError("rerank expected a list of retrieved chunks")
    for retrieved in value:
        if not isinstance(retrieved, GeniaMap) or _keys(retrieved) != {"chunk", "score"}:
            raise TypeError(
                "rerank expected each retrieved chunk to have keys ['chunk', 'score']"
            )
        if not _valid_chunk(retrieved.get("chunk")):
            raise TypeError("rerank expected a valid retrieved chunk")
        score = retrieved.get("score")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
        ):
            raise TypeError("rerank expected each score to be finite")
    return value


def _validate_grounded_content(value: Any, label: str) -> GeniaMap:
    if not isinstance(value, GeniaMap):
        raise TypeError(f"grounding expected {label} content map")
    kind = value.get("kind")
    if kind == symbol("text"):
        if _keys(value) != {"kind", "text"}:
            raise TypeError(f"grounding expected closed content for {label}")
        if not isinstance(value.get("text"), str):
            raise TypeError(f"grounding expected {label} text to be a string")
        return value
    if kind == symbol("json"):
        if _keys(value) != {"kind", "value"}:
            raise TypeError(f"grounding expected closed {label} content")
        represented = value.get("value")
        if not isinstance(represented, GeniaRepresented) or represented.facet != "json":
            raise TypeError(
                f"grounding expected {label} JSON content to retain representation"
            )
        return value
    raise TypeError(f"grounding expected {label} content kind in [json, text]")


def assemble_grounded_context(
    question: Any, content: Any, evidence_value: Any
) -> GeniaMap:
    """Construct one exact E12 grounded context without a provider attempt."""

    if contains_protected(question) or contains_protected(content) or contains_protected(
        evidence_value
    ):
        raise TypeError("protected-value: grounding-input")
    if not isinstance(question, str) or question == "":
        raise TypeError("grounding expected a non-empty question string")
    validated_content = _validate_grounded_content(content, "context")
    try:
        evidence = _validate_retrieved_chunks(evidence_value)
    except TypeError as exc:
        message = str(exc)
        if "score to be finite" in message:
            raise TypeError("grounding expected a finite score") from exc
        raise TypeError(message.replace("rerank expected", "grounding expected")) from exc
    return _map(question=question, content=validated_content, evidence=evidence)


def _validate_grounded_context(value: Any) -> GeniaMap:
    if contains_protected(value):
        raise TypeError("protected-value: grounding-input")
    if not isinstance(value, GeniaMap) or _keys(value) != {
        "question",
        "content",
        "evidence",
    }:
        raise TypeError(
            "grounding expected closed context with keys ['content', 'evidence', 'question']"
        )
    return assemble_grounded_context(
        value.get("question"), value.get("content"), value.get("evidence")
    )


def _validate_grounded_response(value: Any) -> GeniaMap:
    if not isinstance(value, GeniaMap) or _keys(value) != {
        "finish_reason",
        "message",
        "usage",
    }:
        raise TypeError("grounding expected a closed R11 response")
    message = value.get("message")
    if not isinstance(message, GeniaMap) or _keys(message) != {"content", "role"}:
        raise TypeError("grounding expected a closed R11 response message")
    if message.get("role") != symbol("assistant"):
        raise TypeError("grounding expected an assistant response message")
    _validate_grounded_content(message.get("content"), "answer")
    finish_reason = value.get("finish_reason")
    if not isinstance(finish_reason, GeniaSymbol) or finish_reason.name not in {
        "stop",
        "length",
        "filtered",
        "other",
    }:
        raise TypeError("grounding expected a valid R11 finish reason")
    from .model import _validate_usage

    try:
        _validate_usage(value.get("usage"))
    except ValueError as exc:
        raise TypeError("grounding expected valid R11 usage") from exc
    return value


def assemble_grounded_answer(context_value: Any, model_outcome: Any) -> Any:
    """Assemble an answer only from one exact R11 successful Outcome."""

    context = _validate_grounded_context(context_value)
    if isinstance(model_outcome, (GeniaOptionNone, GeniaOptionErr)):
        return model_outcome
    if not isinstance(model_outcome, GeniaOptionSome) or model_outcome.context is not None:
        raise TypeError("grounding expected an R11 model Outcome")
    response = _validate_grounded_response(model_outcome.value)
    sources: list[GeniaMap] = []
    for retrieved in context.get("evidence"):
        source = retrieved.get("chunk").get("source")
        if not any(
            existing.get("doc_id") == source.get("doc_id")
            and existing.get("offset") == source.get("offset")
            and existing.get("length") == source.get("length")
            for existing in sources
        ):
            sources.append(source)
    return _map(
        answer=response.get("message").get("content"),
        sources=sources,
        evidence=context.get("evidence"),
    )


def _rerank_invalid(stage: str) -> GeniaOptionErr:
    return GeniaOptionErr("rerank-response-invalid", _map(stage=symbol(stage)))


def _valid_rerank_error(value: GeniaOptionErr, timeout_ms: int) -> bool:
    context = value.context
    if value.reason == "rerank-timeout":
        return (
            isinstance(context, GeniaMap)
            and _keys(context) == {"timeout_ms"}
            and context.get("timeout_ms") == timeout_ms
            and not isinstance(context.get("timeout_ms"), bool)
        )
    if value.reason == "rerank-rate-limited":
        if not isinstance(context, GeniaMap) or _keys(context) != {"retry_after_ms"}:
            return False
        retry = context.get("retry_after_ms")
        if isinstance(retry, GeniaOptionSome):
            return (
                retry.context is None
                and isinstance(retry.value, int)
                and not isinstance(retry.value, bool)
                and retry.value >= 0
            )
        return (
            isinstance(retry, GeniaOptionNone)
            and retry.reason == "rerank-retry-after-unavailable"
            and retry.context is None
        )
    if value.reason in {"rerank-rejected", "rerank-transport-failure"}:
        return (
            isinstance(context, GeniaMap)
            and _keys(context) == {"kind"}
            and isinstance(context.get("kind"), GeniaSymbol)
            and context.get("kind").name in _RERANK_ERROR_KINDS
        )
    return False


class _FixtureRerankResult:
    __slots__ = ("results",)

    def __init__(self, results: Any):
        self.results = results


class GeniaRerankProvider:
    """Opaque Python-host deterministic reranking capability."""

    __slots__ = ("_handler", "_attempt_count")

    def __init__(self, handler: Callable[[GeniaMap, str, list[Any], str], Any]):
        self._handler = handler
        self._attempt_count = 0

    @property
    def attempt_count(self) -> int:
        return self._attempt_count

    def _attempt(
        self, config: GeniaMap, query: str, evidence: list[Any], credential: str
    ) -> Any:
        self._attempt_count += 1
        return self._handler(config, query, evidence, credential)

    def __repr__(self) -> str:
        return "<rerank-provider>"


class GeniaReranker:
    """Ordinary two-argument provider-backed reranking callable."""

    __slots__ = ("_authority", "_config", "_credential", "_provider")

    def __init__(
        self,
        provider: GeniaRerankProvider,
        config: GeniaMap,
        credential: GeniaProtected,
        authority: GeniaDeclassificationAuthority,
    ):
        self._provider = provider
        self._config = config
        self._credential = credential
        self._authority = authority

    def __call__(self, query: Any, evidence_value: Any) -> Any:
        if contains_protected(query):
            raise TypeError("protected-value: rerank-input")
        if not isinstance(query, str) or query == "":
            raise TypeError("rerank expected query to be a non-empty string")
        evidence = _validate_retrieved_chunks(evidence_value)
        if not evidence:
            return GeniaOptionSome([])

        ordinary_credential = declassify(self._authority, self._credential)
        if not isinstance(ordinary_credential, str):
            raise TypeError("rerank expected protected credential to carry a string")
        try:
            observation = self._provider._attempt(
                self._config, query, evidence, ordinary_credential
            )
        except Exception:
            return GeniaOptionErr(
                "rerank-transport-failure", _map(kind=symbol("other"))
            )
        if isinstance(observation, GeniaOptionErr):
            if _valid_rerank_error(observation, self._config.get("timeout_ms")):
                return observation
            return _rerank_invalid("provider_response")
        if not isinstance(observation, GeniaOptionSome) or observation.context is not None:
            return _rerank_invalid("provider_response")
        response = observation.value
        if not isinstance(response, _FixtureRerankResult):
            return _rerank_invalid("provider_response")
        if not isinstance(response.results, list):
            return _rerank_invalid("result")

        unmatched = [item.get("chunk") for item in evidence]
        normalized: list[GeniaMap] = []
        for result in response.results:
            if not isinstance(result, GeniaMap) or _keys(result) != {"chunk", "score"}:
                return _rerank_invalid("result")
            score = result.get("score")
            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(score)
            ):
                return _rerank_invalid("result")
            provider_chunk = result.get("chunk")
            matched_index = next(
                (index for index, chunk in enumerate(unmatched) if chunk == provider_chunk),
                None,
            )
            if matched_index is None:
                return _rerank_invalid("result")
            exact_chunk = unmatched.pop(matched_index)
            normalized.append(_map(chunk=exact_chunk, score=score))
        if unmatched:
            return _rerank_invalid("result")
        return GeniaOptionSome(normalized)

    def __repr__(self) -> str:
        return "<function>"


def create_fixture_rerank_provider(
    handler: Callable[[GeniaMap, str, list[Any], str], Any],
) -> GeniaRerankProvider:
    if not callable(handler):
        raise TypeError("fixture rerank provider expected a callable handler")
    return GeniaRerankProvider(handler)


def create_fixture_rerank_result(results: Any) -> _FixtureRerankResult:
    return _FixtureRerankResult(results)


def construct_rerank(
    provider: Any,
    config: Any,
    credential: Any,
    authority: Any,
) -> GeniaReranker:
    if not isinstance(provider, GeniaRerankProvider):
        raise TypeError(
            "rerank expected a rerank provider capability, "
            f"received {_runtime_type_name(provider)}"
        )
    validated_config = _validate_rerank_config(config)
    if not isinstance(credential, GeniaProtected):
        raise TypeError("rerank expected a protected credential")
    if not isinstance(authority, GeniaDeclassificationAuthority):
        raise TypeError("rerank expected a declassification authority")
    return GeniaReranker(provider, validated_config, credential, authority)
