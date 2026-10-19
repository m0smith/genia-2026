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
    runtime = genia.make_global_env([])
    return runtime.create_entry_scope() if runtime._entry is None else runtime._entry


def ev(env, node):
    return Evaluator(env).eval(node)


def bind(name, value):
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
    env.set("x", 1)
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
    env.set("x", "from-initializer")  # a reentrant writer wins the race
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


def test_racing_set_cannot_overwrite_a_committed_immutable_binding():
    env = fresh_entry()
    env.commit_immutable_declaration(env.prepare_immutable_declaration("x"), 1)
    with pytest.raises(RuntimeError, match="Cannot rebind immutable binding: x"):
        env.set("x", 2)
    assert env.get("x") == 1


# --- every language-visible writer is checked -----------------------------------


@pytest.fixture
def sealed():
    env = fresh_entry()
    env.commit_immutable_declaration(env.prepare_immutable_declaration("x"), 1)
    return env


def test_assign_rejected(sealed):
    with pytest.raises(RuntimeError, match="Cannot assign to immutable binding: x"):
        sealed.assign("x", 2)


def test_set_rejected(sealed):
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
    env.set("probe", lambda: sentinel.append("ran"))
    node = ir.IrImmutableBind("print", ir.IrCall(ir.IrVar("probe"), []))
    with pytest.raises(RuntimeError, match="reserved by the runtime"):
        ev(env, node)
    assert sentinel == []


def test_direct_ir_assign_rejected_before_rhs_effects():
    env = fresh_entry()
    sentinel = []
    env.set("probe", lambda: sentinel.append("ran"))
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


def test_closed_and_pattern_declarations_remain_not_implemented():
    for source in ("f(x) =: x", "f([x]) = x"):
        with pytest.raises(RuntimeError, match="model-b-not-implemented"):
            genia.run_source(source, genia.make_global_env([]))


def test_shallow_cell_mutation_allowed_after_immutable_bind():
    env = genia.make_global_env([])
    source = "c =: cell(1)\ncell_send(c, (s) -> s + 1)\ncell_get(c)"
    assert genia.run_source(source, env) in (1, 2)  # asynchronous worker; only no rejection is asserted


@pytest.mark.parametrize('discovery', ['route', 'server', 'cors'])
def test_unannotated_immutable_binding_is_ordinary_for_server_discovery(discovery):
    from genia.server_route_binding import discover_entry_file_route_bindings
    from genia.server_config_binding import discover_entry_file_server_config_binding
    from genia.server_cors_binding import discover_entry_file_cors_binding
    from genia.lexer import lex
    from genia.interpreter import Parser, lower_program

    class NoLookup:
        def get(self, name):
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
