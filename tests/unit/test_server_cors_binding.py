from __future__ import annotations

import importlib

import pytest

from genia import make_global_env, run_source
from genia.interpreter import Parser, lex, lower_program
from genia.values import GeniaMap


def _api():
    return importlib.import_module("genia.server_cors_binding")


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
    return api.CorsDeclaration(
        name=name,
        metadata=_map(cors=descriptor),
        target_kind=target_kind,
        source_identity=source_identity,
        source_index=source_index,
        source_location=f"{source_identity}:{source_index + 1}:1",
    )


def test_validate_cors_descriptor_accepts_closed_policy_without_mutation():
    descriptor = _map(
        origin="https://app.example",
        methods=["GET", "POST"],
        headers=["content-type", "x-request-id"],
    )

    validated = _api().validate_cors_descriptor(descriptor)

    assert validated is descriptor
    assert validated.items() == descriptor.items()


@pytest.mark.parametrize(
    ("descriptor", "message"),
    [
        ([], "cors expected policy to be a map"),
        (_map(extra=True), 'cors unexpected policy field "extra"'),
        (_map(origin=""), "cors expected policy.origin to be a non-empty string"),
        (_map(methods=[]), "cors expected policy.methods to be a non-empty list"),
        (
            _map(methods=["GET", ""]),
            "cors expected policy.methods item at index 1 to be a non-empty string",
        ),
        (_map(headers=[]), "cors expected policy.headers to be a non-empty list"),
        (
            _map(headers=["content-type", 7]),
            "cors expected policy.headers item at index 1 to be a non-empty string",
        ),
    ],
)
def test_validate_cors_descriptor_reuses_r7_policy_failures(descriptor, message):
    with pytest.raises(TypeError, match=message):
        _api().validate_cors_descriptor(descriptor)


def test_evaluator_attaches_valid_inert_cors_metadata_to_server_assignment():
    env = make_global_env([])
    source = """
    @server {port: 8000}
    @cors {origin: "https://app.example", methods: ["GET"]}
    application = {name: "api"}
    """

    run_source(source, env, filename="entry.genia")

    policy = env.get_metadata("application").get("cors")
    assert policy.items() == [
        ["origin", "https://app.example"],
        ["methods", ["GET"]],
    ]
    assert env.get("application").get("name") == "api"


def test_evaluator_rejects_cors_annotation_on_function():
    with pytest.raises(TypeError, match="@cors annotation requires a top-level assignment"):
        run_source(
            '@cors {origin: "*"}\napplication(request) = request\n',
            make_global_env([]),
            filename="entry.genia",
        )


def test_evaluator_rejects_duplicate_cors_annotation_on_one_declaration():
    with pytest.raises(TypeError, match="duplicate @cors annotation on application"):
        run_source(
            "@cors {}\n@cors {origin: \"*\"}\napplication = 1\n",
            make_global_env([]),
            filename="entry.genia",
        )


def test_evaluator_rejects_replacing_existing_cors_metadata():
    with pytest.raises(TypeError, match="cannot replace @cors metadata for application"):
        run_source(
            "@cors {}\napplication = 1\n@cors {origin: \"*\"}\napplication = 2\n",
            make_global_env([]),
            filename="entry.genia",
        )


def test_generic_cors_metadata_remains_ordinary_and_is_not_a_candidate():
    source = '@meta {cors: {origin: "*"}}\napplication = 1\n'
    env = make_global_env([])
    run_source(source, env, filename="entry.genia")
    nodes = lower_program(Parser(lex(source), source=source, filename="entry.genia").parse_program())

    result = _api().discover_entry_file_cors_binding(
        nodes,
        env,
        entry_source_identity="entry.genia",
        server_declaration_name="application",
    )

    assert result.binding is None
    assert result.diagnostics == []


def test_discovery_accepts_absence_and_ignores_imported_declarations():
    result = _api().discover_cors_binding(
        [_declaration("imported", source_identity="dep.genia")],
        entry_source_identity="entry.genia",
        server_declaration_name="application",
    )

    assert result.binding is None
    assert result.diagnostics == []


def test_discovery_selects_single_descriptor_on_server_owner():
    result = _api().discover_cors_binding(
        [_declaration("application", descriptor=_map(origin="*"), source_index=2)],
        entry_source_identity="entry.genia",
        server_declaration_name="application",
    )

    assert result.diagnostics == []
    assert result.binding.declaration_name == "application"
    assert result.binding.policy.get("origin") == "*"


def test_discovery_rejects_descriptor_on_different_assignment_than_server_owner():
    result = _api().discover_cors_binding(
        [_declaration("other")],
        entry_source_identity="entry.genia",
        server_declaration_name="application",
    )

    assert result.binding is None
    assert [item.declaration_name for item in result.diagnostics] == ["other"]
    assert result.diagnostics[0].reason == (
        "@cors descriptor must be attached to @server owner application"
    )


def test_discovery_reports_multiple_descriptors_in_source_order():
    result = _api().discover_cors_binding(
        [
            _declaration("later", source_index=3),
            _declaration("zeta", source_index=1),
            _declaration("alpha", source_index=1),
        ],
        entry_source_identity="entry.genia",
        server_declaration_name="alpha",
    )

    assert result.binding is None
    assert [item.declaration_name for item in result.diagnostics] == [
        "alpha",
        "zeta",
        "later",
    ]
    assert all("multiple @cors descriptors" in item.reason for item in result.diagnostics)


def test_discovery_reports_payload_errors_before_cardinality():
    result = _api().discover_cors_binding(
        [
            _declaration("bad", descriptor=_map(methods=[]), source_index=0),
            _declaration("first", source_index=1),
            _declaration("second", source_index=2),
        ],
        entry_source_identity="entry.genia",
        server_declaration_name="first",
    )

    assert result.binding is None
    assert [item.declaration_name for item in result.diagnostics] == [
        "bad",
        "first",
        "second",
    ]
    assert "policy.methods" in result.diagnostics[0].reason
    assert all("multiple @cors descriptors" in item.reason for item in result.diagnostics[1:])


def test_entry_file_discovery_uses_annotated_assignments_and_environment_metadata():
    source = """
    @server {port: 8000}
    @cors {origin: "https://app.example"}
    application = {name: "api"}
    unannotated = 2
    """
    env = make_global_env([])
    run_source(source, env, filename="entry.genia")
    nodes = lower_program(Parser(lex(source), source=source, filename="entry.genia").parse_program())

    result = _api().discover_entry_file_cors_binding(
        nodes,
        env,
        entry_source_identity="entry.genia",
        server_declaration_name="application",
    )

    assert result.diagnostics == []
    assert result.binding.declaration_name == "application"
    assert result.binding.policy.get("origin") == "https://app.example"


def test_bind_down_returns_same_handler_without_cors_descriptor():
    result = _api().discover_cors_binding(
        [],
        entry_source_identity="entry.genia",
        server_declaration_name="application",
    )
    handler = object()
    calls = []

    output = _api().bind_cors(result, handler, cors=lambda *_: calls.append("cors"))

    assert output is handler
    assert calls == []


def test_bind_down_wraps_handler_once_through_existing_cors_shape():
    result = _api().discover_cors_binding(
        [_declaration("application", descriptor=_map(origin="*"))],
        entry_source_identity="entry.genia",
        server_declaration_name="application",
    )
    handler = object()
    calls = []

    def cors(policy, received_handler):
        calls.append((policy, received_handler))
        return "wrapped-handler"

    output = _api().bind_cors(result, handler, cors=cors)

    assert output == "wrapped-handler"
    assert calls == [(result.binding.policy, handler)]


def test_bind_down_never_wraps_when_discovery_has_diagnostics():
    result = _api().discover_cors_binding(
        [_declaration("other")],
        entry_source_identity="entry.genia",
        server_declaration_name="application",
    )
    calls = []

    with pytest.raises(ValueError, match="cannot bind CORS with diagnostics"):
        _api().bind_cors(result, object(), cors=lambda *_: calls.append("cors"))

    assert calls == []
