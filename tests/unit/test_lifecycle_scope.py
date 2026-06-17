import importlib

import pytest

from genia.values import GeniaMap, GeniaOptionSome, OPTION_NONE, symbol


def _lifecycle_scope_module():
    return importlib.import_module("genia.lifecycle_scope")


def _record(**fields):
    record = GeniaMap()
    for key, value in fields.items():
        record = record.put(key, value)
    return record


def _scope(name, parent, children, **fields):
    return _record(
        name=symbol(name),
        parent=parent,
        children=[symbol(child) for child in children],
        **fields,
    )


def _scope_tree(scopes, **fields):
    return _record(scopes=scopes, **fields)


def _canonical_scope_tree(**fields):
    return _scope_tree(
        [
            _scope("execution", OPTION_NONE, ["suite"]),
            _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
            _scope("module", GeniaOptionSome(symbol("suite")), ["test"]),
            _scope("test", GeniaOptionSome(symbol("module")), []),
        ],
        **fields,
    )


def _normalize(scope_tree):
    return _lifecycle_scope_module().normalize_lifecycle_scope_tree(scope_tree)


def _assert_invalid(scope_tree, expected_message):
    lifecycle_scope = _lifecycle_scope_module()
    with pytest.raises(ValueError, match=expected_message):
        lifecycle_scope.normalize_lifecycle_scope_tree(scope_tree)


def test_normalize_accepts_canonical_scope_tree_and_relationships():
    normalized = _normalize(_canonical_scope_tree())

    scopes = normalized.get("scopes")
    assert [scope.get("name") for scope in scopes] == [
        symbol("execution"),
        symbol("suite"),
        symbol("module"),
        symbol("test"),
    ]
    assert [scope.get("parent") for scope in scopes] == [
        OPTION_NONE,
        GeniaOptionSome(symbol("execution")),
        GeniaOptionSome(symbol("suite")),
        GeniaOptionSome(symbol("module")),
    ]
    assert [scope.get("children") for scope in scopes] == [
        [symbol("suite")],
        [symbol("module")],
        [symbol("test")],
        [],
    ]


def test_normalize_preserves_scope_order_exactly_as_declared():
    tree = _scope_tree(
        [
            _scope("test", GeniaOptionSome(symbol("module")), []),
            _scope("module", GeniaOptionSome(symbol("suite")), ["test"]),
            _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
            _scope("execution", OPTION_NONE, ["suite"]),
        ]
    )

    normalized = _normalize(tree)

    assert [scope.get("name") for scope in normalized.get("scopes")] == [
        symbol("test"),
        symbol("module"),
        symbol("suite"),
        symbol("execution"),
    ]


def test_normalize_preserves_optional_root_and_scope_data_without_execution():
    calls = []

    def metadata_callable_that_must_not_be_called():
        calls.append("called")

    root_metadata = _record(owner=symbol("r4"))
    module_metadata = _record(host_callable=metadata_callable_that_must_not_be_called)
    tree = _scope_tree(
        [
            _scope("execution", OPTION_NONE, ["suite"]),
            _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
            _scope(
                "module",
                GeniaOptionSome(symbol("suite")),
                ["test"],
                description="source module boundary",
                metadata=module_metadata,
            ),
            _scope("test", GeniaOptionSome(symbol("module")), []),
        ],
        description="canonical R4 scope tree",
        metadata=root_metadata,
    )

    normalized = _normalize(tree)

    assert normalized.get("description") == "canonical R4 scope tree"
    assert normalized.get("metadata") == root_metadata
    assert normalized.get("scopes")[2].get("description") == "source module boundary"
    assert normalized.get("scopes")[2].get("metadata") == module_metadata
    assert calls == []


def test_validate_accepts_canonical_scope_tree_without_execution():
    lifecycle_scope = _lifecycle_scope_module()

    assert lifecycle_scope.validate_lifecycle_scope_tree(_canonical_scope_tree()) is None


def test_rejects_invalid_root_shape_with_path_diagnostics():
    cases = [
        ([], r"invalid lifecycle scope tree at scope_tree: expected map, got list"),
        (_record(), r"invalid lifecycle scope tree at scope_tree\.scopes: missing required field"),
        (
            _record(scopes=symbol("not_a_list")),
            r"invalid lifecycle scope tree at scope_tree\.scopes: expected list, got symbol",
        ),
    ]
    for scope_tree, expected_message in cases:
        _assert_invalid(scope_tree, expected_message)


def test_rejects_invalid_scope_record_shape_with_path_diagnostics():
    cases = [
        (
            symbol("not_a_scope_record"),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[0\]: expected map, got symbol",
        ),
        (
            _record(parent=OPTION_NONE, children=[symbol("suite")]),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[0\]\.name: missing required field",
        ),
        (
            _record(name=symbol("execution"), children=[symbol("suite")]),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[0\]\.parent: missing required field",
        ),
        (
            _record(name=symbol("execution"), parent=OPTION_NONE),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[0\]\.children: missing required field",
        ),
        (
            _record(name="execution", parent=OPTION_NONE, children=[symbol("suite")]),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[0\]\.name: expected identifier, got string",
        ),
        (
            _record(name=symbol("execution"), parent=symbol("none"), children=[symbol("suite")]),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[0\]\.parent: expected none or some\(identifier\), got symbol",
        ),
        (
            _record(name=symbol("execution"), parent=OPTION_NONE, children=symbol("suite")),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[0\]\.children: expected list, got symbol",
        ),
        (
            _record(name=symbol("execution"), parent=OPTION_NONE, children=["suite"]),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[0\]\.children\[0\]: expected identifier, got string",
        ),
    ]
    for scope_record, expected_message in cases:
        _assert_invalid(_scope_tree([scope_record]), expected_message)


def test_rejects_unsupported_scope_names_with_supported_scope_hint():
    unsupported_names = ["server", "actor", "plugin", "request", "resource", "browser", "notebook"]
    for unsupported_name in unsupported_names:
        tree = _scope_tree(
            [
                _scope("execution", OPTION_NONE, ["suite"]),
                _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
                _scope("module", GeniaOptionSome(symbol("suite")), ["test"]),
                _scope(unsupported_name, GeniaOptionSome(symbol("module")), []),
            ]
        )

        _assert_invalid(
            tree,
            rf"invalid lifecycle scope tree at scope_tree\.scopes\[3\]\.name: "
            rf"unsupported scope {unsupported_name}; supported scopes: execution, suite, module, test",
        )


def test_rejects_duplicate_scope_names_with_deterministic_diagnostic():
    tree = _scope_tree(
        [
            _scope("execution", OPTION_NONE, ["suite"]),
            _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
            _scope("module", GeniaOptionSome(symbol("suite")), ["test"]),
            _scope("test", GeniaOptionSome(symbol("module")), []),
            _scope("test", GeniaOptionSome(symbol("module")), []),
        ]
    )

    _assert_invalid(
        tree,
        r"invalid lifecycle scope tree at scope_tree\.scopes\[4\]\.name: duplicate scope name test",
    )


def test_rejects_noncanonical_scope_hierarchy():
    cases = [
        (
            _scope_tree(
                [
                    _scope("execution", OPTION_NONE, ["suite"]),
                    _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
                    _scope("module", GeniaOptionSome(symbol("suite")), []),
                ]
            ),
            r"invalid lifecycle scope tree at scope_tree\.scopes: missing required scope test",
        ),
        (
            _scope_tree(
                [
                    _scope("execution", GeniaOptionSome(symbol("suite")), ["suite"]),
                    _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
                    _scope("module", GeniaOptionSome(symbol("suite")), ["test"]),
                    _scope("test", GeniaOptionSome(symbol("module")), []),
                ]
            ),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[execution\]\.parent: expected parent none, got suite",
        ),
        (
            _scope_tree(
                [
                    _scope("execution", OPTION_NONE, ["suite"]),
                    _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
                    _scope("module", GeniaOptionSome(symbol("execution")), ["test"]),
                    _scope("test", GeniaOptionSome(symbol("module")), []),
                ]
            ),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[module\]\.parent: expected parent suite, got execution",
        ),
        (
            _scope_tree(
                [
                    _scope("execution", OPTION_NONE, ["suite"]),
                    _scope("suite", GeniaOptionSome(symbol("execution")), ["module"]),
                    _scope("module", GeniaOptionSome(symbol("suite")), []),
                    _scope("test", GeniaOptionSome(symbol("module")), []),
                ]
            ),
            r"invalid lifecycle scope tree at scope_tree\.scopes\[module\]\.children: expected children \[test\], got \[\]",
        ),
    ]
    for scope_tree, expected_message in cases:
        _assert_invalid(scope_tree, expected_message)
