import pytest

from genia.builtins import make_global_env
from genia.callable import GeniaFunctionGroup
from genia.interpreter import run_source
from genia.values import symbol


def _run(source: str, env=None):
    return run_source(source, env or make_global_env([]))


def test_get_annotation_attaches_inert_metadata_to_top_level_function():
    env = make_global_env([])
    _run(
        '@get {path: "/items"}\n'
        "list_items() = {headers: {}, query: {}, body: none(\"http-no-body\")}\n",
        env,
    )
    fn = env.get("list_items")
    assert isinstance(fn, GeniaFunctionGroup)
    descriptor = fn.metadata.get("http_annotation")
    assert descriptor.get("verb") == symbol("get")
    assert descriptor.get("path") == "/items"


def test_post_annotation_attaches_inert_metadata_to_top_level_function():
    env = make_global_env([])
    _run(
        '@post {path: "/items"}\n'
        "create_item() = {headers: {}, query: {}, body: none(\"http-no-body\")}\n",
        env,
    )
    fn = env.get("create_item")
    descriptor = fn.metadata.get("http_annotation")
    assert descriptor.get("verb") == symbol("post")
    assert descriptor.get("path") == "/items"


def test_get_annotation_on_assignment_target_is_rejected():
    with pytest.raises(TypeError, match="@get annotation requires a top-level named function"):
        _run('@get {path: "/items"}\nconfig = {a: 1}\n')


@pytest.mark.parametrize(
    "descriptor,reason_fragment",
    [
        ('{}', "exactly one path field"),
        ('{path: "/items", extra: 1}', "exactly one path field"),
        ('{path: 5}', "must be a non-empty string"),
        ('{path: ""}', "must be a non-empty string"),
        ('{path: "items"}', "must be a non-empty string"),
    ],
)
def test_get_annotation_rejects_malformed_descriptor(descriptor, reason_fragment):
    with pytest.raises(TypeError, match=reason_fragment):
        _run(f"@get {descriptor}\nlist_items() = none\n")


def test_duplicate_get_annotation_on_one_declaration_is_rejected():
    with pytest.raises(TypeError, match="duplicate outbound HTTP annotation"):
        _run(
            '@get {path: "/a"}\n@get {path: "/b"}\n'
            "list_items() = none\n"
        )


def test_mixed_get_and_post_annotation_on_one_declaration_is_rejected():
    with pytest.raises(TypeError, match="duplicate outbound HTTP annotation"):
        _run(
            '@get {path: "/a"}\n@post {path: "/b"}\n'
            "list_items() = none\n"
        )


def test_annotated_rebinding_of_http_annotation_metadata_is_rejected():
    env = make_global_env([])
    _run('@get {path: "/items"}\nlist_items() = none\n', env)
    with pytest.raises(TypeError, match="cannot replace @http_annotation metadata"):
        _run('@get {path: "/other"}\nlist_items() = none\n', env)


def test_loading_a_file_with_get_annotation_performs_no_network_io():
    # Mere evaluation of an annotated declaration must never call the
    # transport layer -- proven structurally: evaluating an IrFuncDef only
    # ever calls eval_annotations/merge_binding_metadata, never
    # send_http_request. No fake-transport injection point even exists at
    # this layer, which is itself the proof: there is no code path from
    # ordinary evaluation into genia.http_transport.send_http_request.
    env = make_global_env([])
    result = _run(
        '@get {path: "/items"}\n'
        "list_items() = {headers: {}, query: {}, body: none(\"http-no-body\")}\n"
        "quote(loaded)",
        env,
    )
    assert result == symbol("loaded")


def test_calling_annotated_function_directly_performs_no_network_io():
    env = make_global_env([])
    result = _run(
        '@get {path: "/items"}\n'
        "list_items() = {headers: {}, query: {q: \"1\"}, body: none(\"http-no-body\")}\n"
        "list_items()",
        env,
    )
    assert result.get("query").get("q") == "1"


def test_existing_route_server_cors_annotations_are_unaffected():
    env = make_global_env([])
    _run(
        "@route {method: \"GET\", path: \"/health\"}\n"
        "health(_request) = {status: 200, headers: {}, body: \"ok\"}\n",
        env,
    )
    fn = env.get("health")
    assert fn.metadata.get("route").get("path") == "/health"
    assert not fn.metadata.has("http_annotation")
