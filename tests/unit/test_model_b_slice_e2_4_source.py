"""Slice E2.4 TEST-only RED: Python-host source and direct-IR activation (issue #1250).

PYTHON REFERENCE HOST ONLY: evaluator entry, Core IR carriers, lock/lineage mechanics
and Python CLI modes. Portable observables live in the shared
``spec/{eval,error,cli}/model-b-closed-*.yaml`` cases (design 10.2); this module holds
what shared specs cannot say (design 10.3 E2-L6/L7/L9, T0-T3 ordering, host consumers).
Expectations come from the approved design sections 4, 5, 7 and 8, never from the
implementation. Closed evaluation is still rejected, so the activation tests fail with
``model-b-not-implemented`` until E2.4 GREEN.
"""

from __future__ import annotations

import pytest

import genia
from genia import environment as e
from genia import ir
from genia.http_annotation_binding import resolve_http_annotation
from genia.interpreter import Evaluator
from tests.unit.model_b_slice_c_support import cli, fresh_env

NOT_YET = 'closed-function-not-yet-published: f is not yet published'
BOUND = 'Cannot declare immutable binding f: name is already bound in this scope'


def lit(value):
    """A literal IR node."""
    return ir.IrLiteral(value)


def clause(name='f', params=('x',), body=None, annotations=()):
    """One identifier-header declaration record carried by a closed group."""
    return ir.IrFuncDef(name, list(params), None, None,
                        body if body is not None else ir.IrVar(params[-1]), list(annotations))


def closed(name='f', *declarations):
    """Directly constructed `IrClosedFuncDef`, never produced by the parser."""
    return ir.IrClosedFuncDef(name, list(declarations) or [clause(name)])


def run_ir(nodes, env=None):
    """Evaluate hand-built Core IR through the evaluator, returning an Outcome-like tuple."""
    printed = []
    env = env or genia.make_global_env([], output_handler=printed.append)
    try:
        return env, printed, Evaluator(env).eval_program(nodes), None
    except Exception as error:  # noqa: BLE001 - the exact class and text are asserted
        return env, printed, None, error


# --- E2-L7: source and direct Core IR enter at T0 and agree -----------------------------------

def test_direct_ir_valid_group_publishes_and_returns_the_committed_callable():
    env, printed, value, error = run_ir([closed('f', clause('f', ('x',), ir.IrVar('x')))])
    assert error is None
    assert repr(value) == '<closed-function f>' and env.get('f') is value
    assert value(7) == 7 and 'f' in env.immutable_names()


@pytest.mark.parametrize('source, direct', [
    ('f(x) =: x\n', lambda: closed('f', clause('f'))),
    ('f(x) =: x\nf(x, y) =: y\n',
     lambda: closed('f', clause('f'), clause('f', ('x', 'y'), ir.IrVar('y')))),
])
def test_source_and_direct_ir_publish_the_same_observable_group(source, direct):
    src_env, src_printed = fresh_env()
    src_value = genia.run_source(source, src_env)
    env, printed, value, error = run_ir([direct()])
    assert error is None
    assert repr(src_value) == repr(value) == '<closed-function f>'
    assert src_env.get('f').shapes() == env.get('f').shapes()
    assert src_env.immutable_names() == env.immutable_names()


MALFORMED = {
    'empty-group': lambda: ir.IrClosedFuncDef('f', []),
    'name-mismatch': lambda: ir.IrClosedFuncDef('f', [clause('g')]),
    'non-declaration': lambda: ir.IrClosedFuncDef('f', [lit(1)]),
    'dotted-name': lambda: closed('a.b', clause('a.b')),
}


@pytest.mark.parametrize('label', sorted(MALFORMED))
def test_malformed_ir_is_rejected_at_t0_after_prior_statements_ran(label):
    printed = []
    env = genia.make_global_env([], output_handler=printed.append)
    nodes = [ir.IrExprStmt(ir.IrCall(ir.IrVar('print'), [lit('before')])), MALFORMED[label]()]
    with pytest.raises(ValueError):
        Evaluator(env).eval_program(nodes)
    assert printed == ['before\n'], 'statements before the declaration still run'
    with pytest.raises(NameError):
        env.get('f')


def test_direct_ir_multiple_simultaneous_errors_report_the_name_error_first():
    """Design 12 DQ-V: name, then annotation permission, then clause structure."""
    effects = []
    env = genia.make_global_env([], output_handler=effects.append)
    genia.run_source('f = 1', env)
    route = ir.IrAnnotation('route', lit('/x'))
    sentinel = ir.IrAnnotation('meta', ir.IrCall(ir.IrVar('print'), [lit('sentinel')]))
    node = closed('f', clause('f', annotations=[sentinel, route]), clause('f', ('y',)))
    with pytest.raises(Exception) as caught:
        Evaluator(env).eval_program([node])
    assert str(caught.value) == BOUND and effects == []


@pytest.mark.parametrize('name', ['route', 'get', 'post', 'server', 'cors', 'bogus'])
def test_direct_ir_forbidden_annotation_matches_source_and_runs_nothing(name):
    effects = []
    env = genia.make_global_env([], output_handler=effects.append)
    sentinel = ir.IrAnnotation('meta', ir.IrCall(ir.IrVar('print'), [lit('sentinel')]))
    node = closed('f', clause('f', annotations=[sentinel, ir.IrAnnotation(name, lit('x'))]))
    message = f'closed-function-annotation-not-permitted: @{name} is not permitted on closed function f'
    with pytest.raises(Exception) as caught:
        Evaluator(env).eval_program([node])
    assert str(caught.value) == message and effects == []
    src_env, src_effects = fresh_env()
    with pytest.raises(Exception) as src_caught:
        genia.run_source(f'@meta ({{m: print("sentinel")}})\n@{name} "x"\nf(x) =: x\n', src_env)
    assert str(src_caught.value) == message and src_effects == []
    for scope in (env, src_env):
        with pytest.raises(NameError):
            scope.get('f')


# --- T0-T3 ordering and T1 name holding ---------------------------------------------------------

def test_t1_name_held_by_a_live_transaction_is_rejected_before_its_effects():
    env, printed = fresh_env()
    env.set_host('inner', lambda: genia.run_source(
        '@meta ({m: print("inner-effect")})\nf(x) =: x\n', env), visibility='runtime-public')
    with pytest.raises(Exception) as caught:
        genia.run_source('@meta ({m: inner()})\nf(x) =: x\n', env)
    assert str(caught.value) == BOUND
    assert printed == [], 'the second declaration is rejected before any of its annotation effects'
    with pytest.raises(NameError):
        env.get('f')
    genia.run_source('f(x) =: x\n', env)  # a failed owner released the name: reusable
    assert env.get('f')(3) == 3


def test_closed_clause_body_cannot_assign_its_own_name():
    env, _ = fresh_env()
    genia.run_source('f(x) =: { f = 1; x }\n', env)
    with pytest.raises(Exception) as caught:
        env.get('f')(5)
    assert str(caught.value) == 'Cannot assign to immutable binding: f'


# --- E2-L9 through source: user code never runs under the binding lock ------------------------

def test_source_annotation_and_body_run_without_the_binding_lock():
    env, _ = fresh_env()
    free = []

    def probe():
        """Report whether the lock can be taken (non-blocking, so a regression cannot hang)."""
        acquired = e._BINDING_LOCK.acquire(False)
        if acquired:
            e._BINDING_LOCK.release()
        free.append(acquired)
        return acquired

    env.set_host('probe', probe, visibility='runtime-public')
    genia.run_source('@meta ({during_annotation: probe()})\nf(x) =: probe()\n', env)
    assert env.get('f')(0) is True
    assert free == [True, True]
    assert env.get_metadata('f').get('during_annotation') is True


# --- E2-L6 through source: a module load triggered by an annotation nests transactions -------

def test_nested_source_transactions_through_a_module_load(tmp_path):
    (tmp_path / 'nested.genia').write_text(
        '@meta ({inner_probe: b(2)})\nb(x) =: x + 1\n', encoding='utf-8')
    env, _ = fresh_env()

    def load_nested():
        """Host bridge: load the module while the outer annotation window is open."""
        module = env.load_module('nested', str(tmp_path / 'entry.genia'))
        assert module.get_export('b')(1) == 2
        return module.get_export('b').metadata.get('inner_probe')

    env.set_host('load_nested', load_nested, visibility='runtime-public')
    genia.run_source('@meta ({outer_probe: load_nested()})\na(x) =: x\n', env)
    assert env.get_metadata('a').get('outer_probe') == 3
    assert not e._OPEN_TRANSACTIONS
    assert env.get('a')(9) == 9


# --- Consumers of a committed closed callable (design 5.2, 5.3, 7.3, 8) -----------------------

def test_send_annotated_excludes_a_committed_closed_callable_whatever_its_metadata():
    env, _ = fresh_env()
    genia.run_source('@meta ({http_annotation: {method: "GET", path: "/x"}})\nf() =: {}\n', env)
    with pytest.raises(TypeError) as caught:
        resolve_http_annotation(env.get('f'))
    assert str(caught.value) == 'send_annotated expected a function annotated with @get or @post'


def test_help_doc_meta_work_on_a_committed_closed_callable():
    result = cli('-c', '@doc "adds one"\nf(x) =: x + 1\nprint(doc("f"))\nm = meta("f")\nprint(m.doc)\nhelp("f")\n')
    assert result.returncode == 0 and result.stderr == ''
    lines = result.stdout.splitlines()
    assert lines[:2] == ['adds one', 'adds one']  # doc() and meta().doc
    assert lines[2] == 'f/1' and 'adds one' in lines[3:]  # help shows shape and the doc


def test_closed_main_selection_follows_the_ordinary_rule_in_file_mode(tmp_path):
    path = tmp_path / 'm.genia'
    path.write_text('main(args) =: print("closed main/1")\n', encoding='utf-8')
    result = cli(str(path))
    # An ordinary main also prints the returned value (print returns its argument).
    assert (result.stdout, result.stderr, result.returncode) == (
        'closed main/1\n"closed main/1"\n', '', 0)
    path.write_text('main() =: print("closed main/0")\n', encoding='utf-8')
    result = cli(str(path))
    assert (result.stdout, result.stderr, result.returncode) == (
        'closed main/0\n"closed main/0"\n', '', 0)


def test_pattern_header_closed_main_is_not_selected(tmp_path):
    path = tmp_path / 'm.genia'
    path.write_text('print("loaded")\nmain(0) =: print("pattern main")\n', encoding='utf-8')
    result = cli(str(path))
    # Like the ordinary twin (`<function main/1>`), the final declaration value is shown and
    # `main` is never called: 'pattern main' must not appear.
    assert (result.stdout, result.stderr, result.returncode) == (
        'loaded\n<closed-function main>\n', '', 0)


def test_repl_never_selects_a_closed_main():
    result = cli(stdin='main() =: print("selected")\n')
    assert (result.stdout, result.stderr, result.returncode) == ('<closed-function main>\n', '', 0)


@pytest.mark.parametrize('walker', ['route', 'config', 'cors'])
def test_server_discovery_still_rejects_a_closed_declaration_in_the_entry_program(walker):
    """Design 5.1 and 8: the three walkers are unchanged; a closed group is still rejected.

    Regression guard: it passes at RED and must keep passing, because closed
    evaluation becoming live must not turn these walkers into silent acceptors.
    """
    from genia import server_config_binding, server_cors_binding, server_route_binding

    nodes = [closed('f', clause('f'))]
    env = genia.make_global_env([])
    kwargs = dict(entry_source_identity='<entry>')
    with pytest.raises(RuntimeError) as caught:
        if walker == 'route':
            server_route_binding.discover_entry_file_route_bindings(nodes, env, **kwargs)
        elif walker == 'config':
            server_config_binding.discover_entry_file_server_config_binding(nodes, env, **kwargs)
        else:
            server_cors_binding.discover_entry_file_cors_binding(
                nodes, env, server_declaration_name='s', server_source_index=0, **kwargs)
    assert str(caught.value) == 'model-b-not-implemented: server discovery is not available'
