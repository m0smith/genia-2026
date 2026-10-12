"""P1-E Python host injection metadata, not language visibility enforcement.

Both classes install into the existing scope in P1. Explicit classes prepare
later placement without granting protected-value authority or changing Env.set.
"""

import ast
import json
from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.environment import Env
from genia.test_cli import make_test_env
from genia.values import GeniaMap


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("visibility", ["runtime-public", "entry-only"])
def test_classification_preserves_installation_identity_metadata_and_assignment(visibility):
    runtime = Env()
    target = Env(runtime, rebind_parent=False)
    marker = object()
    metadata = GeniaMap().put("doc", "fixture")
    target.set_host("fixture", marker, visibility=visibility, metadata=metadata)
    assert target.values["fixture"] is marker
    assert "fixture" not in runtime.values
    assert target.get_metadata("fixture") is metadata
    assert "fixture" in target.assignable
    assert target.host_binding_visibility == {"fixture": visibility}
    assert target.parent is runtime


def test_missing_visibility_is_rejected_before_binding_installation():
    env = Env()
    with pytest.raises(TypeError, match="visibility"):
        env.set_host("fixture", object())
    assert "fixture" not in env.values


@pytest.mark.parametrize("visibility", [None, "", "public", 1])
def test_invalid_visibility_is_rejected_without_mutation(visibility):
    env = Env()
    with pytest.raises(ValueError, match="host visibility"):
        env.set_host("fixture", object(), visibility=visibility)
    assert env.values == {}
    assert env.host_binding_visibility == {}


def test_reinstallation_preserves_existing_set_options_without_language_metadata():
    env = Env()
    metadata = GeniaMap().put("doc", "fixture")
    env.set_host("fixture", 1, visibility="runtime-public", assignable=False, metadata=metadata)
    env.set_host("fixture", 2, visibility="entry-only", preserve_metadata=True)
    assert env.values["fixture"] == 2
    assert env.get_metadata("fixture") is metadata
    assert env.host_binding_visibility["fixture"] == "entry-only"
    assert "fixture" in env.assignable
    assert not metadata.has("visibility")


def test_trusted_internal_classification_does_not_grant_untrusted_access():
    env = Env()
    marker = object()
    env.set_host_internal("fixture_internal", marker, visibility="runtime-public")
    assert env.internal_values["fixture_internal"] is marker
    assert env.host_internal_visibility == {"fixture_internal": "runtime-public"}
    with pytest.raises(NameError):
        Env(env).get("fixture_internal")
    assert Env(env, internal_access=True).get("fixture_internal") is marker


def test_autoload_classification_keeps_runtime_registration_and_lazy_acquisition(tmp_path):
    root = make_global_env([])
    child = Env(root)
    path = tmp_path / "fixture.genia"
    path.write_text("fixture_fn(x) = x\n", encoding="utf-8")
    child.register_host_autoload("fixture_fn", 1, str(path), visibility="runtime-public", trusted=True)
    assert root.autoloads[("fixture_fn", 1)] == str(path)
    assert root.host_autoload_visibility[("fixture_fn", 1)] == "runtime-public"
    assert ("fixture_fn", 1) in root.trusted_autoloads
    assert "fixture_fn" not in root.values
    assert not root.loaded_files
    assert child.get("fixture_fn").get(1).closure is root


def test_reviewed_builtin_internal_and_prelude_inventory_has_exact_classification():
    inventory = json.loads((ROOT / "data/p1_host_binding_inventory.json").read_text())
    env = make_global_env([])
    assert set(env.values) == set(inventory["bindings"])
    assert env.host_binding_visibility == inventory["bindings"]
    assert set(env.internal_values) == set(inventory["internal"])
    assert env.host_internal_visibility == inventory["internal"]
    expected_autoloads = {(row["name"], row["arity"]): row for row in inventory["autoloads"]}
    assert set(env.autoloads) == set(expected_autoloads)
    assert env.host_autoload_visibility == {key: row["visibility"] for key, row in expected_autoloads.items()}
    assert env.autoloads == {key: row["path"] for key, row in expected_autoloads.items()}


def test_native_registrar_and_each_dynamic_fixture_are_entry_only_without_relocation():
    marker = object()
    env, tests = make_test_env(fixture_bindings={"first_fixture": marker, "second_fixture": 17})
    assert env.parent is None
    assert env.entry_scope() is env.runtime_scope() is env
    assert env.values["first_fixture"] is marker
    assert {name: env.host_binding_visibility[name] for name in ["test", "first_fixture", "second_fixture"]} == {
        "test": "entry-only", "first_fixture": "entry-only", "second_fixture": "entry-only",
    }
    assert getattr(env, "_native_test_units") is tests


@pytest.mark.parametrize("adapter,fixtures", [
    ("exec_model_fixture", {"model_provider_fixture", "model_credential_fixture", "model_authority_fixture"}),
    ("exec_r12_grounded_fixture", {f"{family}_{suffix}_fixture" for family in ["embed", "index", "retrieve", "rerank", "model"] for suffix in ["provider", "credential", "authority"]}),
    ("exec_r25_concurrency_fixture", {"_r25_await_idle"}),
])
def test_host_adapter_fixture_classification_is_explicit_and_entry_only(adapter, fixtures):
    from importlib import import_module

    env = import_module(f"hosts.python.{adapter}")._build_env()
    assert env.parent is None
    assert fixtures <= env.values.keys()
    assert all(env.host_binding_visibility[name] == "entry-only" for name in fixtures)


def test_maintained_host_installers_do_not_bypass_required_classification():
    repo = ROOT.parent
    paths = [repo / "src/genia/builtins.py", repo / "src/genia/test_cli.py", *sorted((repo / "hosts/python").glob("exec_*.py"))]
    bypasses = []
    for path in paths:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            receiver = node.func.value
            if isinstance(receiver, ast.Name) and receiver.id == "env" and node.func.attr in {"set", "set_internal", "register_autoload"}:
                bypasses.append(f"{path.relative_to(repo)}:{node.lineno}:{node.func.attr}")
    assert bypasses == [], "Unclassified host injections: " + ", ".join(bypasses)
