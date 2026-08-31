"""Contract tests for the canonical Python-host builtin documentation registry."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from genia.builtins import make_global_env
from genia.callable import GeniaFunctionGroup


REPO = Path(__file__).resolve().parents[2]


def _registry_module():
    from genia import host_builtin_docs

    return host_builtin_docs


def _is_callable(value) -> bool:
    return callable(value) or isinstance(value, GeniaFunctionGroup)


def test_registry_covers_every_direct_host_callable_exactly_once():
    registry = _registry_module()
    env = make_global_env([]).root()
    direct_names = {name for name, value in env.values.items() if _is_callable(value)}
    direct_names.update(
        name for name, value in env.internal_values.items() if _is_callable(value)
    )

    entries = registry.host_builtin_docs()
    assert len({entry.name for entry in entries}) == len(entries)
    assert {entry.name for entry in entries} == direct_names


def test_public_entries_have_complete_metadata_and_internal_bridges_are_explicit():
    registry = _registry_module()
    entries = registry.host_builtin_docs()

    for entry in entries:
        assert entry.name
        assert entry.stability
        if entry.stability == "internal":
            continue
        assert entry.doc.strip(), entry.name
        assert entry.category.strip(), entry.name
        assert entry.signatures, entry.name

    assert registry.host_builtin_doc("print").stability != "internal"
    assert registry.host_builtin_doc("_seq_transform").stability == "internal"
    assert "_parse_int" in registry.internal_host_builtin_names()


def test_public_registry_metadata_is_attached_without_replacing_bound_values():
    registry = _registry_module()
    env = make_global_env([])
    value = env.get("print")
    metadata = env.get_metadata("print")

    assert env.get("print") is value
    entry = registry.host_builtin_doc("print")
    assert metadata.get("doc") == entry.doc
    assert metadata.get("category") == entry.category
    assert metadata.get("stability") == entry.stability


def test_generator_collects_public_host_entries_and_excludes_internal_entries():
    spec = importlib.util.spec_from_file_location(
        "gen_function_docs", REPO / "tools" / "gen_function_docs.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    records = module.collect()
    by_name = {record["name"]: record for record in records}
    assert by_name["print"]["source_kind"] == "python-host"
    assert by_name["parse_int"]["source_kind"] == "prelude"
    assert by_name["Format"]["slug"].casefold() != by_name["format"]["slug"].casefold()
    assert "_parse_int" not in by_name
    assert "_seq_transform" not in by_name
    assert len(by_name) == len(records)


def test_generated_reference_has_no_pending_host_registry_note():
    index = (REPO / "docs" / "reference" / "index.md").read_text(encoding="utf-8")
    assert "host doc registry in a follow-up phase" not in index
    assert "[`print`](functions/print.md)" in index
