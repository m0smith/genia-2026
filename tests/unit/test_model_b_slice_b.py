"""Python host internals for Model B Slice B (immutable lexical bindings, #1261).

Portable observations (rejection ordering, shadowing, reserved names, shallow
Ref mutation, REPL persistence) are governed by spec/{eval,cli}/model-b-b-*.
This module covers what a shared source spec cannot reach: the Env
prepare/commit mechanism, racing and reentrant commits, writers that bypass
the evaluator (direct Env calls, metacircular helpers, direct Core IR),
the static reserved-name manifest over new declaration nodes (N5), and
statement-level effect staging around still-unimplemented declarations (N8).
PYTHON REFERENCE HOST ONLY.
"""
import threading

import pytest

import genia
from genia import ir
from genia.evaluator import Evaluator


def fresh_entry():
    """Return a registered entry scope over a fresh runtime, as a real execution uses."""
    runtime = genia.make_global_env([])
    return runtime.create_entry_scope() if runtime._entry is None else runtime._entry


def ev(env, node):
    """Evaluate one Core IR node directly in `env`, bypassing source parsing."""
    return Evaluator(env).eval(node)


def bind(name, value):
    """Build a direct-IR immutable declaration of a literal."""
    return ir.IrImmutableBind(name, ir.IrLiteral(value))


# --- prepare / commit mechanism -------------------------------------------------


def test_prepare_then_commit_publishes_immutable_binding():
    env = fresh_entry()
    ticket = env.prepare_immutable_declaration("x")
    assert "x" not in env.values  # preparation publishes nothing
    env.commit_immutable_declaration(ticket, 1)
    assert env.get("x") == 1
    with pytest.raises(RuntimeError, match="Cannot assign to immutable binding: x"):
        env.assign("x", 2)


def test_prepare_rejects_existing_local_binding_before_any_commit():
    env = fresh_entry()
    env.assign("x", 1)  # ordinary mutable binding
    with pytest.raises(RuntimeError, match="Cannot declare immutable binding x: name is already bound"):
        env.prepare_immutable_declaration("x")


def test_prepare_rejects_unloaded_runtime_owned_name_without_autoload():
    env = fresh_entry()
    runtime = env.runtime_scope()
    assert "map" not in runtime.values
    with pytest.raises(RuntimeError, match="name is reserved by the runtime"):
        env.prepare_immutable_declaration("map")
    assert "map" not in runtime.values  # rejection did not acquire the prelude


def test_reentrant_write_during_initializer_fails_commit_without_rollback():
    env = fresh_entry()
    ticket = env.prepare_immutable_declaration("x")
    env.assign("x", "from-initializer")  # a reentrant writer wins the race
    with pytest.raises(RuntimeError, match="already bound"):
        env.commit_immutable_declaration(ticket, "late")
    assert env.get("x") == "from-initializer"
    assert "x" not in env.immutable_names()


def test_racing_commits_publish_exactly_once():
    env = fresh_entry()
    tickets = [env.prepare_immutable_declaration("x") for _ in range(2)]
    barrier = threading.Barrier(2)
    results = []

    def commit(index):
        """Commit the ticket at `index` once both threads reach the barrier."""
        barrier.wait()
        try:
            env.commit_immutable_declaration(tickets[index], index)
            results.append(("ok", index))
        except RuntimeError as error:
            results.append(("err", str(error)))

    threads = [threading.Thread(target=commit, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(kind for kind, _ in results) == ["err", "ok"]
    winner = next(value for kind, value in results if kind == "ok")
    assert env.get("x") == winner


def test_set_after_commit_cannot_overwrite_immutable_binding():
    env = fresh_entry()
    env.commit_immutable_declaration(env.prepare_immutable_declaration("x"), 1)
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: x"):
        env.set_host("x", 2, visibility="entry-only")
    assert env.get("x") == 1


def test_commit_versus_racing_assign_never_loses_the_immutable_value():
    """Whichever writer wins, the end state is one of two coherent outcomes."""
    for _ in range(200):
        env = fresh_entry()
        ticket = env.prepare_immutable_declaration("x")
        barrier = threading.Barrier(2)
        outcome = {}

        def commit():
            """Racing commit of the prepared immutable declaration."""
            barrier.wait()
            try:
                env.commit_immutable_declaration(ticket, "immutable")
                outcome["commit"] = "ok"
            except RuntimeError:
                outcome["commit"] = "rejected"

        def assign():
            """Racing ordinary assignment to the same name."""
            barrier.wait()
            try:
                env.assign("x", "mutable")
                outcome["assign"] = "ok"
            except RuntimeError:
                outcome["assign"] = "rejected"

        threads = [threading.Thread(target=commit), threading.Thread(target=assign)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        if outcome["commit"] == "ok":
            assert outcome["assign"] == "rejected"
            assert env.get("x") == "immutable" and "x" in env.immutable_names()
        else:
            assert outcome["assign"] == "ok"
            assert env.get("x") == "mutable" and "x" not in env.immutable_names()


def test_binding_lock_is_released_after_every_rejection(sealed):
    from genia.environment import _BINDING_LOCK

    for call in (
        lambda: sealed.assign("x", 2),
        lambda: sealed.set_host("x", 2, visibility="entry-only"),
        lambda: sealed.prepare_immutable_declaration("x"),
        lambda: sealed.prepare_immutable_declaration("print"),
    ):
        with pytest.raises(RuntimeError):
            call()
        assert _BINDING_LOCK.acquire(blocking=False)  # would deadlock/fail if a rejection leaked it
        _BINDING_LOCK.release()


# --- every language-visible writer is checked -----------------------------------


@pytest.fixture
def sealed():
    """An entry scope in which `x` is already a committed immutable binding."""
    env = fresh_entry()
    env.commit_immutable_declaration(env.prepare_immutable_declaration("x"), 1)
    return env


def test_assign_rejected(sealed):
    """Ordinary assignment to a sealed name is rejected."""
    with pytest.raises(RuntimeError, match="Cannot assign to immutable binding: x"):
        sealed.assign("x", 2)


def test_set_rejected(sealed):
    """Raw `Env.set` rebinding of a sealed name is rejected."""
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: x"):
        sealed.set("x", 2)


def test_set_host_rejected_for_entry_injection(sealed):
    with pytest.raises(RuntimeError, match="immutable binding: x"):
        sealed.set_host("x", 2, visibility="entry-only")


def test_define_function_rejected(sealed):
    node = ir.IrFuncDef("x", ["y"], None, None, ir.IrVar("y"))
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: x"):
        ev(sealed, node)


def test_merge_metadata_rejected_outside_declaration(sealed):
    from genia.values import GeniaMap

    with pytest.raises(RuntimeError, match="immutable binding: x"):
        sealed.merge_binding_metadata("x", GeniaMap().put("doc", "late"))


def test_metacircular_set_and_define_rejected(sealed):
    from genia.evaluator import GeniaMetaEnv

    meta = GeniaMetaEnv(sealed)
    with pytest.raises(RuntimeError, match="Cannot assign to immutable binding: x"):
        meta.assign("x", 2)
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: x"):
        meta.define("x", 2)
    assert sealed.get("x") == 1


def test_import_alias_writer_rejected_before_module_load(tmp_path, monkeypatch):
    (tmp_path / "lib.genia").write_text('print("loaded")\n')
    env = fresh_entry()
    ev(env, bind("x", 1))
    node = ir.IrImport("lib", "x", span=None)
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: x"):
        ev(env, node)
    assert "lib" not in env.runtime_scope().loaded_modules


def test_named_pattern_writer_rejected():
    env = fresh_entry()
    ev(env, bind("P", 1))
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: P"):
        genia.run_source("pattern P(v) = true", env)


# --- direct Core IR, not only source --------------------------------------------


def test_direct_ir_commits_once_and_rejects_duplicate():
    env = fresh_entry()
    assert ev(env, bind("x", 7)) == 7
    with pytest.raises(RuntimeError, match="already bound in this scope"):
        ev(env, bind("x", 8))
    assert env.get("x") == 7


def test_direct_ir_reserved_name_rejected_before_initializer():
    env = fresh_entry()
    sentinel = []
    env.set_host("probe", lambda: sentinel.append("ran"), visibility="entry-only")
    node = ir.IrImmutableBind("print", ir.IrCall(ir.IrVar("probe"), []))
    with pytest.raises(RuntimeError, match="reserved by the runtime"):
        ev(env, node)
    assert sentinel == []


def test_direct_ir_assign_rejected_before_rhs_effects():
    env = fresh_entry()
    sentinel = []
    env.set_host("probe", lambda: sentinel.append("ran"), visibility="entry-only")
    ev(env, bind("x", 1))
    with pytest.raises(RuntimeError, match="Cannot assign to immutable binding: x"):
        ev(env, ir.IrAssign("x", ir.IrCall(ir.IrVar("probe"), [])))
    assert sentinel == []


def test_annotation_failure_keeps_committed_binding():
    env = fresh_entry()
    node = ir.IrImmutableBind("x", ir.IrLiteral(1), [ir.IrAnnotation("doc", ir.IrVar("undefined_doc"))])
    with pytest.raises(NameError):
        ev(env, node)
    assert env.get("x") == 1
    with pytest.raises(RuntimeError, match="immutable binding: x"):
        env.assign("x", 2)


# --- legacy behavior preserved --------------------------------------------------


def test_legacy_assignment_and_rebinding_unchanged():
    env = genia.make_global_env([])
    assert genia.run_source("x = 1\nx = 2\nx", env) == 2
    assert genia.run_source("f(a) = a\nf(3)", env) == 3
    assert genia.run_source("open g(1) = 1\ng(1)", env) == 1


def test_runtime_owned_entry_write_through_unchanged():
    env = genia.make_global_env([])
    entry = env.create_entry_scope() if env._entry is None else env._entry
    entry.set("map", lambda *a: None)  # existing `=` route still writes through
    assert "map" in entry.runtime_scope().values


# --- N5: static reserved-name manifest over the new declaration nodes ------------


def test_declared_prelude_names_cover_new_declaration_nodes(tmp_path):
    from genia.environment import _declared_prelude_names

    path = tmp_path / "prelude_probe.genia"
    path.write_text("imm_probe =: 1\npat_probe([a]) = a\nclosed_probe(x) =: x\nplain_probe = 2\n")
    assert _declared_prelude_names(str(path)) >= {"imm_probe", "pat_probe", "closed_probe", "plain_probe"}


# --- N8: effect staging around still-unimplemented declarations ------------------


def test_earlier_statement_effects_precede_unimplemented_declaration(capsys):
    env = genia.make_global_env([])
    with pytest.raises(RuntimeError, match="model-b-not-implemented"):
        genia.run_source('print("before")\nf(x) =: x', env)
    assert "before" in capsys.readouterr().out


def test_closed_declarations_remain_not_implemented_and_pattern_declarations_execute():
    """Slice C GREEN (issue #1269, phase-guard flip): only closed `=:` functions still reject."""
    with pytest.raises(RuntimeError, match="model-b-not-implemented"):
        genia.run_source("f(x) =: x", genia.make_global_env([]))
    assert genia.run_source("f([x]) = x\nf([5])", genia.make_global_env([])) == 5


def test_shallow_cell_mutation_is_observable_after_immutable_bind():
    """Cell state is updated through an immutable binding and observed once the worker is idle.

    Portable counterpart: spec/eval/model-b-b-cell-mutation-observable.yaml.
    """
    from importlib import import_module

    env = import_module("hosts.python.exec_r25_concurrency_fixture")._build_env()
    source = "c =: cell(1)\ncell_send(c, (s) -> s + 1)\n_r25_await_idle()\ncell_get(c)"
    assert genia.run_source(source, env) == 2
    with pytest.raises(RuntimeError, match="Cannot assign to immutable binding: c"):
        genia.run_source("c = cell(9)", env)


@pytest.mark.parametrize('discovery', ['route', 'server', 'cors'])
def test_unannotated_immutable_binding_is_ordinary_for_server_discovery(discovery):
    from genia.server_route_binding import discover_entry_file_route_bindings
    from genia.server_config_binding import discover_entry_file_server_config_binding
    from genia.server_cors_binding import discover_entry_file_cors_binding
    from genia.lexer import lex
    from genia.interpreter import Parser, lower_program

    class NoLookup:
        """Fail on any discovery lookup."""
        def get(self, name):
            """Reject value access."""
            raise AssertionError('no declaration should be looked up')

        get_metadata = get

    nodes = lower_program(Parser(lex('x =: 1\n')).parse_program())
    kwargs = {'entry_source_identity': 'entry.genia'}
    function = {'route': discover_entry_file_route_bindings,
                'server': discover_entry_file_server_config_binding,
                'cors': discover_entry_file_cors_binding}[discovery]
    if discovery == 'cors':
        kwargs.update(server_declaration_name='config', server_source_index=0)
    function(nodes, NoLookup(), **kwargs)  # must not raise model-b-not-implemented


@pytest.mark.parametrize("name", ["print", "map", "map_acc"])
def test_runtime_reservation_applies_to_entry_scope_only(name):
    """Current Python behavior: a nested scope may declare a runtime-owned name locally (review M3)."""
    env = fresh_entry()
    with pytest.raises(RuntimeError, match="reserved by the runtime"):
        genia.run_source(f"{name} =: 7", env)
    assert genia.run_source(f"f() = {{\n  {name} =: 7\n  {name}\n}}\nf()", env) == 7
