"""Python internals: lexer tables, direct IR validation, traversal and transitional rejection.

Portable syntax/lowering observations are governed by spec/{ir,parse}/model-b-a-*.
"""
import json
import re
from pathlib import Path
import pytest
from genia import ir
from genia.lexer import lex, TOKEN_SPEC, PUNCTUATION_TOKENS
from genia.interpreter import Parser, lower_program, is_complete
from genia.pattern_match import IrPatTuple, IrPatBind
from hosts.python.ir_normalize import normalize_portable_ir


def test_longest_match_both_tables():
    assert [t.kind for t in lex('x =: 1')][1] == 'IMMUTABLE_ASSIGN'
    assert next(k for k, p in TOKEN_SPEC if re.match(p, '=:')) == 'IMMUTABLE_ASSIGN'
    assert next(k for k, p in PUNCTUATION_TOKENS if '=:'.startswith(p)) == 'IMMUTABLE_ASSIGN'


def test_lexer_lookalikes_unchanged():
    assert [t.kind for t in lex('== != <= >= = : "=:" # =:\n{k:1}') if t.kind not in {'NEWLINE','EOF'}] == ['EQEQ','NE','LE','GE','ASSIGN','COLON','STRING','LBRACE','IDENT','COLON','NUMBER','RBRACE']


@pytest.mark.parametrize('source', ['x =:', 'f(x) =:'])
def test_repl_missing_initializer_incomplete(source):
    assert not is_complete(source)


@pytest.mark.parametrize('source', ['x =: 1','f(x) =: x','f([x]) = x','f(x) ? true = x'])
def test_transitional_rejection(run, source):
    """Reject new declaration execution instead of silently using legacy mutable semantics."""
    with pytest.raises(Exception, match='model-b-not-implemented'):
        run(source)


def declaration():
    """Create a legacy direct-IR record without invoking source parsing."""
    return ir.IrFuncDef('f', ['x'], None, None, ir.IrVar('x'))


@pytest.mark.parametrize('kind', ['empty','mixed','wrong','nested'])
def test_malformed_closed_group(kind):
    cls = ir.IrClosedFuncDef
    child = declaration()
    children = {'empty': [], 'mixed': [child, ir.IrFuncDef('g',[],None,None,ir.IrLiteral(1))], 'wrong': [ir.IrLiteral(1)], 'nested':[cls('f',[child])] }[kind]
    with pytest.raises((ValueError, RuntimeError), match='closed'):
        ir.assert_portable_core_ir([cls('f',children)])


@pytest.mark.parametrize('pattern', [None, ir.IrVar('x'), IrPatTuple([ir.IrVar('x')])])
def test_invalid_pattern_carriers(pattern):
    with pytest.raises((ValueError, RuntimeError), match='pattern'):
        ir.assert_portable_core_ir([ir.IrPatternFuncDef('f',pattern,None,ir.IrLiteral(1))])


def test_no_duplicate_header_representation():
    with pytest.raises(TypeError):
        ir.IrPatternFuncDef('f',IrPatTuple([IrPatBind('x')]),None,ir.IrVar('x'),params=['x'])


@pytest.mark.parametrize('container', ['closed','open','contribution','annotation'])
def test_walk_rejects_nested_host_local(container):
    host = ir.IrListTraversalLoop('n','xs',1,None,None)
    child = declaration()
    child.body = host
    clause = ir.IrCaseClause(IrPatTuple([]), None, host)
    node = {'closed': lambda: ir.IrClosedFuncDef('f',[child]),'open': lambda: ir.IrOpenFuncDef('f',[clause],None),'contribution': lambda: ir.IrOpenContribution('m','f',[clause]),'annotation': lambda: ir.IrAnnotation('doc',host)}[container]()
    assert host in list(ir.iter_ir_nodes(node))
    with pytest.raises(RuntimeError, match='host-local'):
        ir.assert_portable_core_ir([node])


def test_new_node_inventory_and_optional_normalization():
    names = {c.__name__ for c in ir.PORTABLE_CORE_IR_NODE_TYPES}
    manifest = json.loads((Path(__file__).resolve().parents[2]/'spec/manifest.json').read_text())
    assert {'IrImmutableBind','IrClosedFuncDef','IrPatternFuncDef'} <= names
    assert names == set(manifest['core_ir_contract']['minimal_portable_node_families'])
    result = normalize_portable_ir(lower_program(Parser(lex('f([x]) = x')).parse_program()))[0]
    assert 'annotations' not in result and 'guard' not in result and 'span' not in result


def test_direct_closed_body_rejects_nested_declaration():
    child = declaration()
    child.body = ir.IrClosedFuncDef('f', [declaration()])
    with pytest.raises(ValueError, match='nested'):
        ir.assert_portable_core_ir([ir.IrClosedFuncDef('f', [child])])


def test_direct_pattern_rejects_competing_header_channel():
    child = ir.IrPatternFuncDef('f', IrPatTuple([IrPatBind('x')]), None, ir.IrVar('x'))
    child.params = ['x']
    with pytest.raises(ValueError, match='competing'):
        ir.assert_portable_core_ir([child])


def test_transitional_rejection_precedes_initializer_effects(run):
    with pytest.raises(RuntimeError, match='model-b-not-implemented'):
        run('x =: undefined_initializer()')


def test_direct_evaluation_validates_before_transitional_rejection():
    from genia import make_global_env
    from genia.evaluator import Evaluator
    with pytest.raises(ValueError, match='closed'):
        Evaluator(make_global_env()).eval(ir.IrClosedFuncDef('f', []))


def test_closed_pattern_annotation_traversal_retains_source_spans():
    source = '@test "pattern"\nf([x]) ? true =: x'
    nodes = lower_program(Parser(lex(source), source=source).parse_program())
    child = nodes[0].declarations[0]
    assert isinstance(child, ir.IrPatternFuncDef)
    assert child.pattern.span is not None and child.guard.span is not None
    assert [a.name for a in child.annotations] == ['test']
    assert child.annotations[0] in list(ir.iter_ir_nodes(nodes))


def test_native_discovery_explicitly_rejects_closed_test():
    from genia.native_test_runner import identify_tests
    source = '@test "closed"\nf() =: true'
    with pytest.raises(RuntimeError, match='model-b-not-implemented'):
        identify_tests(Parser(lex(source)).parse_program())


@pytest.mark.parametrize('discovery', ['route', 'server', 'cors'])
@pytest.mark.parametrize('source', ['x =: unknown()', 'f(x) =: x', 'f([x]) = x'])
@pytest.mark.parametrize('annotated', [False, True])
def test_direct_server_discovery_rejects_before_environment_access(discovery, source, annotated):
    """Python discovery must reject the entire input before metadata/value lookups."""
    from genia.server_route_binding import discover_entry_file_route_bindings
    from genia.server_config_binding import discover_entry_file_server_config_binding
    from genia.server_cors_binding import discover_entry_file_cors_binding

    class NoLookup:
        """Fail on any discovery lookup, including an earlier ordinary declaration."""

        def get(self, name):
            """Reject value access so the test proves rejection ordering."""
            raise AssertionError('value lookup before rejection')

        def get_metadata(self, name):
            """Reject metadata access so the test proves rejection ordering."""
            raise AssertionError('metadata lookup before rejection')

    functions = {
        'route': discover_entry_file_route_bindings,
        'server': discover_entry_file_server_config_binding,
        'cors': discover_entry_file_cors_binding,
    }
    ordinary = 'g(x) = x' if discovery == 'route' else 'config = 1'
    source = f'@{discovery} {{}}\n{ordinary}\n' + (f'@{discovery} {{}}\n' if annotated else '') + source
    nodes = lower_program(Parser(lex(source)).parse_program())
    kwargs = {'entry_source_identity': 'entry.genia'}
    if discovery == 'cors':
        kwargs.update(server_declaration_name='config', server_source_index=0)
    with pytest.raises(RuntimeError, match='model-b-not-implemented'):
        functions[discovery](nodes, NoLookup(), **kwargs)
