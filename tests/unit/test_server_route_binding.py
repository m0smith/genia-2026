from __future__ import annotations

from dataclasses import replace

import pytest

from genia import make_global_env, run_source
from genia.interpreter import Parser, lex, lower_program
from genia.server_route_binding import (
    RouteDeclaration,
    assemble_route_handler,
    discover_entry_file_route_bindings,
    discover_route_bindings,
    validate_route_descriptor,
)
from genia.values import GeniaMap


def _map(**fields: object) -> GeniaMap:
    value = GeniaMap()
    for key, item in fields.items():
        value = value.put(key, item)
    return value


def _handler(name: str = "handler", params: str = "request"):
    env = make_global_env([])
    run_source(f"{name}({params}) = request\n", env, filename="routes.genia")
    return env.get(name)


def _declaration(
    name: str,
    *,
    method: str = "GET",
    path: str = "/items",
    source_identity: str = "entry.genia",
    source_index: int = 0,
    target_kind: str = "function",
    value=None,
) -> RouteDeclaration:
    return RouteDeclaration(
        name=name,
        value=_handler(name) if value is None else value,
        metadata=_map(route=_map(method=method, path=path)),
        target_kind=target_kind,
        source_identity=source_identity,
        source_index=source_index,
        source_location=f"{source_identity}:{source_index + 1}:1",
    )


def test_validate_route_descriptor_accepts_exact_closed_map_without_normalizing_strings():
    descriptor = _map(method="GET", path="/Health")

    assert validate_route_descriptor(descriptor) == descriptor


@pytest.mark.parametrize(
    ("descriptor", "message"),
    [
        ("GET /items", "expected a map"),
        (_map(method="GET"), "exactly method and path"),
        (_map(method="GET", path="/items", priority=1), "exactly method and path"),
        (_map(method=1, path="/items"), "method expected a string"),
        (_map(method="", path="/items"), "method must not be empty"),
        (_map(method="GET", path="items"), "path must start with /"),
    ],
)
def test_validate_route_descriptor_rejects_invalid_shapes(descriptor, message):
    with pytest.raises(TypeError, match=message):
        validate_route_descriptor(descriptor)


def test_discovery_keeps_entry_file_routes_in_source_order_with_name_tie_breaker():
    declarations = [
        _declaration("later", path="/later", source_index=2),
        _declaration("zeta", path="/zeta", source_index=1),
        _declaration("alpha", path="/alpha", source_index=1),
        _declaration("imported", path="/ignored", source_identity="dep.genia"),
    ]

    result = discover_route_bindings(declarations, entry_source_identity="entry.genia")

    assert result.diagnostics == []
    assert [route.declaration_name for route in result.routes] == ["alpha", "zeta", "later"]


def test_discovery_accepts_different_methods_on_the_same_path():
    result = discover_route_bindings(
        [
            _declaration("read", method="GET", source_index=0),
            _declaration("create", method="POST", source_index=1),
        ],
        entry_source_identity="entry.genia",
    )

    assert result.diagnostics == []
    assert [(route.method, route.path) for route in result.routes] == [
        ("GET", "/items"),
        ("POST", "/items"),
    ]


def test_entry_file_discovery_uses_evaluated_ir_declarations_and_environment_metadata():
    source = """
    @route {method: "GET", path: "/read"}
    read(request) = request

    unannotated(request) = request

    @route {method: "POST", path: "/create"}
    create(request) = request
    """
    env = make_global_env([])
    run_source(source, env, filename="entry.genia")
    nodes = lower_program(Parser(lex(source), source=source, filename="entry.genia").parse_program())

    result = discover_entry_file_route_bindings(
        nodes,
        env,
        entry_source_identity="entry.genia",
    )

    assert result.diagnostics == []
    assert [route.declaration_name for route in result.routes] == ["read", "create"]


def test_discovery_rejects_every_exact_conflict_member_in_source_order():
    result = discover_route_bindings(
        [
            _declaration("first", source_index=0),
            _declaration("other", path="/other", source_index=1),
            _declaration("second", source_index=2),
        ],
        entry_source_identity="entry.genia",
    )

    assert result.routes == []
    assert [diagnostic.declaration_name for diagnostic in result.diagnostics] == ["first", "second"]
    assert all("conflicting @route GET /items" in diagnostic.reason for diagnostic in result.diagnostics)


def test_discovery_reports_target_payload_and_arity_before_conflicts():
    bad_payload = replace(
        _declaration("bad_payload", source_index=0),
        metadata=_map(route=_map(method="GET")),
    )
    assignment = _declaration("assignment", source_index=1, target_kind="assignment")
    zero_arg = _declaration("zero", source_index=2, value=_handler("zero", ""))
    conflict_a = _declaration("conflict_a", source_index=3)
    conflict_b = _declaration("conflict_b", source_index=4)

    result = discover_route_bindings(
        [conflict_b, zero_arg, bad_payload, conflict_a, assignment],
        entry_source_identity="entry.genia",
    )

    assert result.routes == []
    assert [diagnostic.declaration_name for diagnostic in result.diagnostics] == [
        "bad_payload",
        "assignment",
        "zero",
        "conflict_a",
        "conflict_b",
    ]
    assert "top-level named function" in result.diagnostics[1].reason
    assert "exactly one fixed one-argument" in result.diagnostics[2].reason


def test_discovery_rejects_ambiguous_and_varargs_handlers():
    env = make_global_env([])
    run_source(
        """
        ambiguous(request) = request
        ambiguous(request, extra) = request
        variadic(request, ..rest) = request
        """,
        env,
        filename="entry.genia",
    )
    declarations = [
        _declaration("ambiguous", value=env.get("ambiguous"), source_index=0),
        _declaration("variadic", value=env.get("variadic"), source_index=1),
    ]

    result = discover_route_bindings(declarations, entry_source_identity="entry.genia")

    assert result.routes == []
    assert [item.declaration_name for item in result.diagnostics] == ["ambiguous", "variadic"]
    assert all("exactly one fixed one-argument" in item.reason for item in result.diagnostics)


def test_assembly_uses_existing_route_values_in_order_and_route_request_once():
    result = discover_route_bindings(
        [
            _declaration("read", method="GET", path="/read", source_index=0),
            _declaration("create", method="POST", path="/create", source_index=1),
        ],
        entry_source_identity="entry.genia",
    )
    calls: list[tuple] = []

    def route(method, path, handler):
        calls.append(("route", method, path, handler.name))
        return (method, path, handler)

    def route_request(routes):
        calls.append(("route_request", [(method, path) for method, path, _ in routes]))
        return "assembled-handler"

    assembled = assemble_route_handler(result, route=route, route_request=route_request)

    assert assembled == "assembled-handler"
    assert calls == [
        ("route", "GET", "/read", "read"),
        ("route", "POST", "/create", "create"),
        ("route_request", [("GET", "/read"), ("POST", "/create")]),
    ]


def test_assembly_does_not_invoke_factories_when_discovery_has_diagnostics():
    result = discover_route_bindings(
        [_declaration("first"), _declaration("second", source_index=1)],
        entry_source_identity="entry.genia",
    )
    calls: list[str] = []

    with pytest.raises(ValueError, match="cannot assemble routes with diagnostics"):
        assemble_route_handler(
            result,
            route=lambda *_: calls.append("route"),
            route_request=lambda *_: calls.append("route_request"),
        )

    assert calls == []
