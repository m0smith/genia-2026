from __future__ import annotations

import importlib

import pytest

from genia import make_global_env, run_source
from genia.interpreter import Parser, lex, lower_program
from genia.values import GeniaMap, OPTION_NONE


def _api():
    return importlib.import_module("genia.server_config_binding")


def _map(**fields: object) -> GeniaMap:
    value = GeniaMap()
    for key, item in fields.items():
        value = value.put(key, item)
    return value


def _declaration(
    name: str,
    *,
    descriptor: object | None = None,
    source_identity: str = "entry.genia",
    source_index: int = 0,
    target_kind: str = "assignment",
):
    api = _api()
    if descriptor is None:
        descriptor = _map()
    return api.ServerConfigDeclaration(
        name=name,
        metadata=_map(server=descriptor),
        target_kind=target_kind,
        source_identity=source_identity,
        source_index=source_index,
        source_location=f"{source_identity}:{source_index + 1}:1",
    )


def test_validate_server_descriptor_applies_defaults_without_mutating_input():
    descriptor = _map()

    normalized = _api().validate_server_descriptor(descriptor)

    assert descriptor.count() == 0
    assert normalized.items() == [["host", "127.0.0.1"], ["port", 8000]]


def test_validate_server_descriptor_preserves_explicit_config():
    descriptor = _map(host="0.0.0.0", port=0, max_requests=3)

    normalized = _api().validate_server_descriptor(descriptor)

    assert normalized.items() == [
        ["host", "0.0.0.0"],
        ["port", 0],
        ["max_requests", 3],
    ]


def test_validate_server_descriptor_treats_explicit_absence_as_omitted_limit():
    normalized = _api().validate_server_descriptor(_map(max_requests=OPTION_NONE))

    assert normalized.items() == [["host", "127.0.0.1"], ["port", 8000]]


def test_validate_server_descriptor_rejects_invalid_values():
    cases = [
        ("localhost:8000", "@server annotation expected a map, received string"),
        (_map(extra=True), "@server descriptor has unknown field: extra"),
        (_map(host=1), "@server descriptor host expected a string, received int"),
        (_map(port=True), "@server descriptor port expected an integer, received bool"),
        (_map(port=-1), "@server descriptor port expected an integer in \\[0, 65535\\]"),
        (_map(port=65536), "@server descriptor port expected an integer in \\[0, 65535\\]"),
        (_map(max_requests=False), "@server descriptor max_requests expected a positive integer, received bool"),
        (_map(max_requests=0), "@server descriptor max_requests expected a positive integer"),
    ]
    for descriptor, message in cases:
        with pytest.raises((TypeError, ValueError), match=message):
            _api().validate_server_descriptor(descriptor)


def test_evaluator_attaches_normalized_inert_server_metadata_to_assignment():
    env = make_global_env([])
    source = """
    @server {port: 0, max_requests: 1}
    application = {name: "api"}
    """

    run_source(source, env, filename="entry.genia")

    metadata = env.get_metadata("application").get("server")
    assert metadata.items() == [
        ["host", "127.0.0.1"],
        ["port", 0],
        ["max_requests", 1],
    ]
    assert env.get("application").get("name") == "api"


def test_evaluator_rejects_server_annotation_on_function():
    with pytest.raises(TypeError, match="@server annotation requires a top-level assignment"):
        run_source(
            '@server {port: 8000}\napplication(request) = request\n',
            make_global_env([]),
            filename="entry.genia",
        )


def test_evaluator_rejects_duplicate_server_annotation_on_one_declaration():
    with pytest.raises(TypeError, match="duplicate @server annotation on application"):
        run_source(
            "@server {}\n@server {port: 8000}\napplication = 1\n",
            make_global_env([]),
            filename="entry.genia",
        )


def test_evaluator_rejects_replacing_existing_server_metadata():
    with pytest.raises(TypeError, match="cannot replace @server metadata for application"):
        run_source(
            "@server {}\napplication = 1\n@server {port: 9000}\napplication = 2\n",
            make_global_env([]),
            filename="entry.genia",
        )


def test_generic_server_metadata_remains_ordinary_and_is_not_a_candidate():
    source = '@meta {server: {port: 9000}}\napplication = 1\n'
    env = make_global_env([])
    run_source(source, env, filename="entry.genia")
    nodes = lower_program(Parser(lex(source), source=source, filename="entry.genia").parse_program())

    result = _api().discover_entry_file_server_config_binding(
        nodes,
        env,
        entry_source_identity="entry.genia",
    )

    assert result.binding is None
    assert [item.reason for item in result.diagnostics] == [
        "required @server descriptor not found in entry file"
    ]


def test_discovery_ignores_imported_declarations_and_selects_entry_owner():
    result = _api().discover_server_config_binding(
        [
            _declaration("imported", source_identity="dep.genia"),
            _declaration("application", descriptor=_map(port=8080), source_index=2),
        ],
        entry_source_identity="entry.genia",
    )

    assert result.diagnostics == []
    assert result.binding.declaration_name == "application"
    assert result.binding.config.get("port") == 8080


def test_discovery_requires_exactly_one_entry_file_server_in_source_order():
    result = _api().discover_server_config_binding(
        [
            _declaration("later", source_index=3),
            _declaration("zeta", source_index=1),
            _declaration("alpha", source_index=1),
        ],
        entry_source_identity="entry.genia",
    )

    assert result.binding is None
    assert [item.declaration_name for item in result.diagnostics] == [
        "alpha",
        "zeta",
        "later",
    ]
    assert all("multiple @server descriptors" in item.reason for item in result.diagnostics)


def test_discovery_reports_payload_errors_before_cardinality():
    result = _api().discover_server_config_binding(
        [
            _declaration("bad", descriptor=_map(port=-1), source_index=0),
            _declaration("first", source_index=1),
            _declaration("second", source_index=2),
        ],
        entry_source_identity="entry.genia",
    )

    assert result.binding is None
    assert [item.declaration_name for item in result.diagnostics] == ["bad", "first", "second"]
    assert "port expected an integer" in result.diagnostics[0].reason
    assert all("multiple @server descriptors" in item.reason for item in result.diagnostics[1:])


def test_entry_file_discovery_uses_annotated_assignments_and_environment_metadata():
    source = """
    @server {port: 8080}
    application = {name: "api"}
    unannotated = 2
    """
    env = make_global_env([])
    run_source(source, env, filename="entry.genia")
    nodes = lower_program(Parser(lex(source), source=source, filename="entry.genia").parse_program())

    result = _api().discover_entry_file_server_config_binding(
        nodes,
        env,
        entry_source_identity="entry.genia",
    )

    assert result.diagnostics == []
    assert result.binding.declaration_name == "application"
    assert result.binding.config.get("port") == 8080


def test_bind_down_calls_existing_serve_http_shape_once_and_returns_result():
    result = _api().discover_server_config_binding(
        [_declaration("application", descriptor=_map(port=8080))],
        entry_source_identity="entry.genia",
    )
    handler = object()
    calls: list[tuple[GeniaMap, object]] = []

    def serve_http(config, received_handler):
        calls.append((config, received_handler))
        return "stopped-server"

    output = _api().bind_server_config(result, handler, serve_http=serve_http)

    assert output == "stopped-server"
    assert len(calls) == 1
    assert calls[0][0].get("port") == 8080
    assert calls[0][1] is handler


def test_bind_down_never_activates_when_discovery_has_diagnostics():
    result = _api().discover_server_config_binding([], entry_source_identity="entry.genia")
    calls: list[str] = []

    with pytest.raises(ValueError, match="cannot bind server config with diagnostics"):
        _api().bind_server_config(
            result,
            object(),
            serve_http=lambda *_: calls.append("serve_http"),
        )

    assert calls == []
