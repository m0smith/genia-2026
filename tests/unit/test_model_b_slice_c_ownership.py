"""Slice C RED host-local tests: ownership, diagnostic safety, annotation post-failure state.

PYTHON REFERENCE HOST ONLY (issue #1269; test plan R6.E HL-10, HL-11, HL-14,
HL-16, HL-17, HL-18). These tests look at `Env` identity-level state, the
module loader and exception classes, which no shared source spec can express.
The portable rejection texts are pinned by
``spec/{eval,error,cli}/model-b-c-own-*.yaml``; the future-oracle strings here
are the maintainer-approved contract-derived shapes (R7-D5), not text observed
from the current runtime.

RED phase: tests ending in ``_today`` pin implemented behavior and pass; the
others assert approved Slice C behavior and fail until GREEN.
"""

from __future__ import annotations

import dataclasses
import re

import pytest

import genia
from genia import ir
from genia.callable import GeniaFunctionGroup
from genia.evaluator import GeniaMetaEnv
from tests.unit.model_b_slice_c_support import cli, fresh_env, outcome

NOT_OWNER_LOCAL = (
    "function-declaration-not-owner: cannot declare a/2: "
    "'a' refers to function 'f' declared by another binding in this scope"
)
NOT_OWNER_FOREIGN = (
    "function-declaration-not-owner: cannot declare h/2: "
    "'h' refers to function 'g' owned by module 'lib'"
)
LEAKS = re.compile(r"0x[0-9a-fA-F]+|/[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+|\.genia|<function|GeniaFunction|:\d+:\d+")


def _declare(env, source: str):
    """Run `source` in `env` under the `<command>` filename and return its result."""
    return genia.run_source(source, env, filename="<command>")


def _second_clause(env, name: str, owner_name: str, arity_params):
    """Build a clause named `name` shaped like `owner_name`'s first clause but with new params."""
    group = env.get(owner_name)
    assert isinstance(group, GeniaFunctionGroup)
    template = next(iter(group.values()))
    return dataclasses.replace(template, name=name, params=list(arity_params), body=ir.IrVar(arity_params[0]))


# --- HL-10: Env.define_function owner checks use provenance, not callable(value) --------------


def test_direct_define_function_through_alias_is_rejected_as_not_owner():
    env, _ = fresh_env()
    _declare(env, "f(x) = x\na = f")
    clause = _second_clause(env, "a", "f", ["x", "y"])
    with pytest.raises(Exception) as caught:
        env.define_function(clause)
    assert type(caught.value).__name__ == "FunctionDeclarationNotOwnerError"
    assert str(caught.value) == NOT_OWNER_LOCAL
    # state after rejection (HL-16): nothing installed, alias and owner unchanged
    assert env.get("a") is env.get("f")
    assert env.get("f").sorted_arities() == [1]


def test_direct_define_function_on_the_owning_binding_still_appends_today():
    env, _ = fresh_env()
    _declare(env, "f(x) = x\na = f")
    env.define_function(_second_clause(env, "f", "f", ["x", "y"]))
    assert env.get("f").sorted_arities() == [1, 2]
    assert env.get("a") is env.get("f")


def test_python_callable_is_not_mistaken_for_an_owned_function_group_today():
    env, _ = fresh_env()
    env.assign("p", lambda *a: 0)
    group = genia.run_source("f(x) = x\nf", fresh_env()[0])
    clause = next(iter(group.values()))
    with pytest.raises(TypeError, match="name already bound to non-function value"):
        env.define_function(dataclasses.replace(clause, name="p", params=["x", "y"]))


def test_ordinary_group_is_not_an_extend_or_use_target_today(tmp_path):
    (tmp_path / "base.genia").write_text("f(x) = x\n", encoding="utf-8")
    (tmp_path / "main.genia").write_text("import base\nextend base.f(0) = 1\n", encoding="utf-8")
    completed = cli("main.genia", cwd=tmp_path)
    assert completed.returncode == 1
    assert "open-function-target-not-open" in completed.stderr


# --- HL-14: immutable-owned names cannot be extended by any writer --------------------------


@pytest.fixture
def sealed():
    """Fixture: an environment whose entry scope owns immutable binding `x`, so tests can attempt to extend it."""
    env, _ = fresh_env()
    runtime = env
    entry = runtime.create_entry_scope() if getattr(runtime, "_entry", None) is None else runtime._entry
    entry.commit_immutable_declaration(entry.prepare_immutable_declaration("x"), 1)
    return entry


def test_function_declaration_over_immutable_binding_is_rejected_today(sealed):
    result = outcome("x(a) = a\nx(0) = 1", env=sealed)
    assert result.error_class in {"ImmutableBindingError", "RuntimeError"}
    assert "Cannot rebind immutable binding: x" in result.message or "model-b-not-implemented" in result.message
    assert sealed.get("x") == 1


def test_metacircular_define_cannot_append_to_an_immutable_owned_name_today(sealed):
    clause = dataclasses.replace(
        next(iter(genia.run_source("g(x) = x\ng", fresh_env()[0]).values())), name="x"
    )
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: x"):
        GeniaMetaEnv(sealed).define("x", clause)
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: x"):
        sealed.define_function(clause)
    assert sealed.get("x") == 1


def test_pattern_clause_over_immutable_binding_fails_with_the_immutable_rejection(sealed):
    """Slice B policy wins: rejection precedes any clause installation."""
    result = outcome("x(0) = 1", env=sealed)
    assert result.message == "Cannot rebind immutable binding: x"
    assert sealed.get("x") == 1


# --- HL-11: diagnostic safety (R4) ------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    ["f(x) = x\na = f\na(x, y) = x + y", "f(x) = x\na = f\na(0, y) = y", "f(x) = x\na = f\na(x, ..r) = x"],
    ids=["fixed", "pattern", "varargs"],
)
def test_local_ownership_diagnostic_contains_no_path_address_span_or_value(source):
    result = outcome(source)
    assert result.error_class == "FunctionDeclarationNotOwnerError"
    assert result.message.startswith("function-declaration-not-owner: cannot declare a/")
    assert not LEAKS.search(result.message), result.message


def test_foreign_ownership_diagnostic_names_the_module_by_canonical_identity_only(tmp_path):
    (tmp_path / "lib.genia").write_text("g(x) = x\n", encoding="utf-8")
    (tmp_path / "main.genia").write_text("import lib\nh = lib.g\nh(x, y) = x + y\n", encoding="utf-8")
    completed = cli("main.genia", cwd=tmp_path)
    assert completed.returncode == 1
    assert completed.stderr == f"Error: {NOT_OWNER_FOREIGN}\n"
    assert not LEAKS.search(completed.stderr.replace("Error: ", ""))
    assert str(tmp_path) not in completed.stderr


_SENTINEL = "SLICE_C_SENTINEL_1269"
_PROVIDER_SETUP = (
    "provider = config_provider([{kind: quote(values), values: {"
    f'key: "{_SENTINEL}"'
    "}}]) |> unwrap_or(none)\n"
    'token = secret_get(provider, "key", quote(outbound_api)) |> unwrap_or(none)\n'
)


@pytest.mark.parametrize(
    "source",
    ["f(x) = (0 -> x)\nf(token)", "f(x) = 1\nf(y) = 2\nf(token)", "f(x) = x\nf(token, 1)"],
    ids=["case-miss", "legacy-duplicate", "shape-miss"],
)
def test_protected_sentinel_never_appears_in_existing_diagnostics_today(source):
    env, _ = fresh_env()
    genia.run_source(_PROVIDER_SETUP, env)
    result = outcome(source, env=env)
    assert result.error is not None
    assert _SENTINEL not in (result.message or "")


@pytest.mark.parametrize(
    ("source", "prefix"),
    [
        ("f(0) = 1\nf(token)", "No matching case for function f/1 with arguments"),
        ("f(x) = x\na = f\na(x, y) = x + y\na(token, 1)", "function-declaration-not-owner: cannot declare a/2"),
    ],
    ids=["pattern-case-miss", "ownership"],
)
def test_protected_sentinel_never_appears_in_slice_c_diagnostics(source, prefix):
    env, _ = fresh_env()
    genia.run_source(_PROVIDER_SETUP, env)
    result = outcome(source, env=env)
    assert result.error is not None, source
    assert (result.message or "").startswith(prefix), result.message
    assert _SENTINEL not in (result.message or ""), source


# --- HL-16: state after an ownership rejection (Env identity) ---------------------------------


def test_ownership_rejection_leaves_group_alias_and_metadata_untouched():
    env, _ = fresh_env()
    _declare(env, '@doc "owner doc"\nf(x) = x\na = f')
    group_before = env.get("f")
    metadata_before = group_before.metadata
    arities_before = group_before.sorted_arities()
    with pytest.raises(Exception) as caught:
        _declare(env, '@doc "must not apply"\na(x, y) = x + y')
    assert type(caught.value).__name__ == "FunctionDeclarationNotOwnerError"
    assert env.get("a") is group_before and env.get("f") is group_before
    assert group_before.sorted_arities() == arities_before
    assert group_before.metadata == metadata_before
    # a later legitimate declaration on the owner still works and is visible through the alias
    assert _declare(env, "f(x, y) = x + y\na(1, 2)") == 3


# --- HL-17: imported-alias rejection leaves the exporting module's group alone ----------------


def test_foreign_alias_rejection_leaves_the_module_export_unchanged(tmp_path):
    (tmp_path / "lib.genia").write_text("g(x) = x\n", encoding="utf-8")
    env, _ = fresh_env()
    runtime_entry = env.create_entry_scope() if getattr(env, "_entry", None) is None else env._entry
    path = str(tmp_path / "entry.genia")
    with pytest.raises(Exception) as caught:
        genia.run_source("import lib\nh = lib.g\nh(x, y) = x + y", runtime_entry, filename=path)
    assert type(caught.value).__name__ == "FunctionDeclarationNotOwnerError"
    assert genia.run_source("lib.g(1)", runtime_entry, filename=path) == 1
    follow = outcome("lib.g(1, 2)", env=runtime_entry, filename=path)
    assert follow.message == "No matching function: g/2. Available: g/1"


# --- HL-18: annotation post-failure internals --------------------------------------------------


def test_failed_annotation_keeps_old_metadata_and_installs_the_clause_for_legacy_groups_today():
    """Characterization (baseline): the clause is installed, metadata stays as it was."""
    env, _ = fresh_env()
    _declare(env, '@doc "orig"\nf(x) = x\na = f')
    metadata_before = env.get("f").metadata
    result = outcome("@doc 7\nf(x, y) = x + y", env=env)
    assert result.error_class == "TypeError"
    assert result.message == "@doc annotation expected a string, received int"
    group = env.get("f")
    assert group.sorted_arities() == [1, 2]
    assert group.metadata == metadata_before
    assert genia.run_source("a(1, 2)", env) == 3
    assert genia.run_source('doc("f")', env) == "orig"


def test_failed_annotation_on_pattern_clause_has_the_same_post_failure_shape():
    env, _ = fresh_env()
    _declare(env, '@doc "orig"\nf(0) = "zero"')
    metadata_before = env.get("f").metadata
    result = outcome("@doc 7\nf(1) = \"one\"", env=env)
    assert result.message == "@doc annotation expected a string, received int"
    group = env.get("f")
    assert group.metadata == metadata_before
    assert genia.run_source("[f(0), f(1)]", env) == ["zero", "one"]


def test_later_annotation_expression_is_suppressed_after_the_first_failure_and_earlier_effects_persist():
    env, printed = fresh_env()
    _declare(env, "f(x) = x")
    result = outcome('@doc 7\n@category (print("later-annotation"))\nf(x, y) = x + y', env=env)
    assert result.error_class == "TypeError"
    assert "later-annotation" not in "".join(printed)
