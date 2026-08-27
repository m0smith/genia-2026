import pytest

from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome, GeniaRepresented, symbol


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _document(text="hello", *, meta=None):
    return _map(
        id="doc-1",
        text=text,
        meta=meta if meta is not None else GeniaRepresented("json", GeniaMap()),
    )


def _run_with_chunker(chunker, document=None):
    env = make_global_env([])
    env.set("chunker_fixture", chunker)
    env.set("document_fixture", document if document is not None else _document())
    return run_source("chunk(chunker_fixture, document_fixture)", env)


def test_chunk_invokes_callback_once_and_constructs_exact_provenance():
    calls = []

    def chunker(text):
        calls.append(text)
        return [_map(offset=0, length=2), _map(offset=2, length=3)]

    result = _run_with_chunker(chunker)

    assert calls == ["hello"]
    assert isinstance(result, GeniaOptionSome)
    assert [item.get("text") for item in result.value] == ["he", "llo"]
    assert [item.get("source").get("doc_id") for item in result.value] == ["doc-1", "doc-1"]
    assert [item.get("source").get("offset") for item in result.value] == [0, 2]
    assert [item.get("source").get("length") for item in result.value] == [2, 3]


def test_chunk_preserves_exact_metadata_object_and_allows_overlap_and_repeat():
    meta = GeniaRepresented("json", _map(tags=["a"], nested=_map(ok=True)))
    document = _document("abcd", meta=meta)

    result = _run_with_chunker(
        lambda _text: [
            _map(offset=1, length=2),
            _map(offset=0, length=3),
            _map(offset=1, length=2),
        ],
        document,
    )

    assert isinstance(result, GeniaOptionSome)
    assert [item.get("text") for item in result.value] == ["bc", "abc", "bc"]
    assert all(item.get("meta") is meta for item in result.value)


def test_chunk_uses_unicode_code_point_offsets():
    result = _run_with_chunker(
        lambda text: [_map(offset=1, length=2)],
        _document("A😀éZ"),
    )
    assert isinstance(result, GeniaOptionSome)
    assert result.value[0].get("text") == "😀é"


def test_chunk_allows_zero_chunks_for_empty_and_nonempty_documents():
    for text in ["", "not empty"]:
        assert _run_with_chunker(lambda _text: [], _document(text)) == GeniaOptionSome([])


def test_chunk_returns_indexed_chunk_invalid_for_bad_spans():
    spans = [
        _map(offset=0),
        _map(offset=0, length=1, extra=True),
        _map(offset=True, length=1),
        _map(offset=-1, length=1),
        _map(offset=0, length=True),
        _map(offset=0, length=0),
        _map(offset=0, length=-1),
        _map(offset=5, length=1),
        _map(offset=4, length=2),
    ]
    for span in spans:
        result = _run_with_chunker(lambda _text: [_map(offset=0, length=1), span])
        assert isinstance(result, GeniaOptionErr)
        assert result.reason == "chunk-invalid"
        assert result.context.get("stage") == symbol("span")
        assert result.context.get("index") == 1


def test_chunk_rejects_malformed_documents_before_callback():
    documents = [
        "not a map",
        _map(id="doc-1", text="x"),
        _map(id="doc-1", text="x", meta=GeniaRepresented("json", GeniaMap()), extra=True),
        _map(id="", text="x", meta=GeniaRepresented("json", GeniaMap())),
        _map(id="doc-1", text=1, meta=GeniaRepresented("json", GeniaMap())),
        _map(id="doc-1", text="x", meta=GeniaMap()),
        _map(id="doc-1", text="x", meta=GeniaRepresented("other", GeniaMap())),
        _map(id="doc-1", text="x", meta=GeniaRepresented("json", [])),
        _map(id="doc-1", text="x", meta=GeniaRepresented("json", _map(bad=symbol("x")))),
    ]
    for document in documents:
        calls = []
        with pytest.raises(TypeError, match="chunk expected"):
            _run_with_chunker(lambda text: calls.append(text) or [], document)
        assert calls == []


def test_chunk_rejects_non_callable_and_non_list_callback_result():
    with pytest.raises(TypeError, match="chunk expected chunker function"):
        _run_with_chunker(42)
    with pytest.raises(TypeError, match="chunker must return a list"):
        _run_with_chunker(lambda _text: _map(offset=0, length=1))


def test_chunk_propagates_callback_exception_once():
    calls = []

    def broken(text):
        calls.append(text)
        raise RuntimeError("chunker exploded")

    with pytest.raises(RuntimeError, match="chunker exploded"):
        _run_with_chunker(broken)
    assert calls == ["hello"]
