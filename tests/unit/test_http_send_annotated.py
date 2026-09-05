import pytest

from genia.builtins import make_global_env
from genia.http_annotation_binding import perform_send_annotated
from genia.http_transport import HttpTransportResponse
from genia.interpreter import run_source
from genia.values import GeniaOptionErr, GeniaOptionNone, GeniaOptionSome


def _invoke(fn, args):
    return fn(*args)


def _json_encode(value):
    return GeniaOptionSome("{}")


def _annotated_function(env, verb, path, dynamic_source):
    run_source(f'@{verb} {{path: "{path}"}}\nhandler() = {dynamic_source}\n', env)
    return env.get("handler")


def test_perform_send_annotated_composes_operation_and_send():
    env = make_global_env([])
    fn = _annotated_function(
        env, "get", "/items", '{headers: {}, query: {"limit": "5"}, body: none("http-no-body")}'
    )
    calls = []

    def fake_transport(request):
        calls.append(request)
        return HttpTransportResponse(status=200, headers={}, body=b"ok")

    result = perform_send_annotated(
        fn,
        "http://example.invalid",
        GeniaOptionNone("nil"),
        2000,
        json_encode=_json_encode,
        invoke=_invoke,
        transport=fake_transport,
    )

    assert isinstance(result, GeniaOptionSome)
    assert calls[0].method == "GET"
    assert calls[0].url == "http://example.invalid/items?limit=5"


def test_perform_send_annotated_uses_post_verb():
    env = make_global_env([])
    fn = _annotated_function(
        env, "post", "/items", '{headers: {}, query: {}, body: {kind: quote(text), text: "hi"}}'
    )
    calls = []

    def fake_transport(request):
        calls.append(request)
        return HttpTransportResponse(status=201, headers={}, body=b"")

    perform_send_annotated(
        fn, "http://example.invalid", GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=fake_transport,
    )

    assert calls[0].method == "POST"
    assert calls[0].body == b"hi"


def test_perform_send_annotated_rejects_unannotated_function():
    env = make_global_env([])
    run_source("handler() = none\n", env)
    fn = env.get("handler")

    with pytest.raises(TypeError, match="annotated with @get or @post"):
        perform_send_annotated(
            fn, "http://example.invalid", GeniaOptionNone("nil"), 2000,
            json_encode=_json_encode, invoke=_invoke, transport=lambda r: None,
        )


def test_perform_send_annotated_rejects_wrong_arity_function():
    env = make_global_env([])
    run_source('@get {path: "/items"}\nhandler(x) = none\n', env)
    fn = env.get("handler")

    with pytest.raises(TypeError, match="fixed zero-argument"):
        perform_send_annotated(
            fn, "http://example.invalid", GeniaOptionNone("nil"), 2000,
            json_encode=_json_encode, invoke=_invoke, transport=lambda r: None,
        )


def test_perform_send_annotated_rejects_wrong_dynamic_return_shape():
    env = make_global_env([])
    run_source('@get {path: "/items"}\nhandler() = {headers: {}}\n', env)
    fn = env.get("handler")

    with pytest.raises(TypeError, match="headers, query, body"):
        perform_send_annotated(
            fn, "http://example.invalid", GeniaOptionNone("nil"), 2000,
            json_encode=_json_encode, invoke=_invoke, transport=lambda r: None,
        )


def test_perform_send_annotated_propagates_operation_construction_failure():
    env = make_global_env([])
    fn = _annotated_function(
        env, "get", "/items", '{headers: {}, query: {"bad": 5}, body: none("http-no-body")}'
    )

    result = perform_send_annotated(
        fn, "http://example.invalid", GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=lambda r: None,
    )

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "http-operation-invalid"


def test_perform_send_annotated_two_calls_are_independent():
    env = make_global_env([])
    fn = _annotated_function(
        env, "get", "/items", '{headers: {}, query: {}, body: none("http-no-body")}'
    )
    calls = []

    def fake_transport(request):
        calls.append(request)
        return HttpTransportResponse(status=200, headers={}, body=b"ok")

    perform_send_annotated(
        fn, "http://example.invalid", GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=fake_transport,
    )
    perform_send_annotated(
        fn, "http://example.invalid", GeniaOptionNone("nil"), 2000,
        json_encode=_json_encode, invoke=_invoke, transport=fake_transport,
    )

    assert len(calls) == 2
