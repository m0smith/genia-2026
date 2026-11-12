"""Python-host real dispatch barriers and conservative AST callable-site inventory."""
import ast
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from genia import interpreter
from genia import values
from tests.unit.test_model_b_slice_e2_1 import fixture, refused, window


@pytest.mark.parametrize('raises', [False, True])
def test_entry_main_boundary(raises):
    env, group, txn = fixture()
    seen = []

    def entry(arg):
        """Exercise the actual selected-record call site, retaining outer authority."""
        refused(lambda: group(1))
        seen.append(arg)
        if raises:
            raise ValueError('main failure')
        return 7

    import genia
    env.set_host('entry_probe', entry, visibility='runtime-public')
    genia.run_source('main(x) = entry_probe(x)', env)
    with window(txn):
        assert group(1) == 1
        if raises:
            with pytest.raises(ValueError, match='main failure'):
                interpreter._resolve_program_result(None, env)
        else:
            assert interpreter._resolve_program_result(None, env) == 7
        assert len(seen) == 1
        assert group(2) == 2


@pytest.mark.parametrize('raises', [False, True])
def test_http_same_thread_real_request_dispatch(monkeypatch, raises):
    import genia.builtins as builtins
    env, group, txn = fixture()
    seen = []

    class Server:
        """No socket setup: drive the real request handler on the declaring thread."""
        def __init__(self, address, handler):
            """Retain the real request-handler class without opening a socket."""
            self.server_address = address
            self.handler = handler

        def handle_request(self):
            """Drive one HEAD request through the real _serve implementation."""
            request = object.__new__(self.handler)
            request.command = 'HEAD'
            request.path = '/'
            request.headers = {}
            request.client_address = ('127.0.0.1', 1)
            request.send_response = lambda status: seen.append(status)
            request.send_header = lambda *args: None
            request.end_headers = lambda: None
            request._serve()

        def server_close(self):
            """Record resource cleanup after request dispatch."""
            seen.append('closed')

    def handler(request):
        """Attempt invocation inside the host's real HTTP dispatch boundary."""
        refused(lambda: group(1))
        seen.append('refused')
        if raises:
            raise ValueError('http failure')
        return values.GeniaMap().put('status', 200).put('body', 'ok')

    monkeypatch.setattr(builtins, 'HTTPServer', Server)
    with window(txn):
        assert group(1) == 1
        env.get('_serve_http')(values.GeniaMap().put('max_requests', 1), handler)
        assert seen == ['refused', 500 if raises else 200, 'closed']
        assert group(2) == 2


@pytest.mark.parametrize('kind', ['cell', 'process'])
@pytest.mark.parametrize('raises', [False, True])
def test_worker_dispatch_barrier_on_declaring_thread(monkeypatch, kind, raises):
    _, group, txn = fixture()
    seen = []

    class End(BaseException):
        """Terminate the real worker loop after exactly one message."""

    class Mailbox:
        """Deliver one real message, then terminate without swallowing test errors."""
        def __init__(self, message):
            """Store exactly one message for the real dispatcher."""
            self.message = message

        def get(self):
            """Return the message once, then stop the inline worker loop."""
            if self.message is None:
                raise End
            message, self.message = self.message, None
            return message

    def callback(value):
        """Both normal and exceptional body exits must pop the barrier."""
        refused(lambda: group(1))
        seen.append('refused')
        if raises:
            raise ValueError('worker failure')
        return value

    # Construct the real worker but run its real dispatcher on this thread, so
    # an empty new-thread stack cannot conceal a missing barrier.
    monkeypatch.setattr(values.threading, 'Thread', lambda **kw: SimpleNamespace(start=lambda: None))
    if kind == 'cell':
        worker = values.GeniaCell(values.GeniaRef(0))
        worker._mailbox = Mailbox((0, 1, callback))
    else:
        worker = values.GeniaProcess(callback)
        worker._mailbox = Mailbox((1, 0))
    with window(txn):
        assert group(1) == 1
        try:
            worker._run()
        except End:
            pass
        assert seen == ['refused']
        assert worker._failed is raises
        assert group(2) == 2
    # These inline private workers must not enter global idle-wait fixtures.
    values._R25_ENTITIES.discard(worker)


# Design §6.3: BRIDGE work is requested by the current synchronous call.
# Providers in model/retrieval run their supplied handler before _attempt returns;
# network IO does not make that callback an independent request. Route assembly
# calls route/route_request synchronously and retains handlers; the eventual
# requester runs behind serve_http's BOUNDARY below. Neither needs a new barrier.
BRIDGE_SITES = {
    'builtins.py:<module>.make_global_env._invoke_from_builtin:invoke_callable': 1,
    'builtins.py:<module>.make_global_env._invoke_raw_from_builtin:invoke_callable': 1,
    'builtins.py:<module>.make_global_env.actor_call_update_fn:handler': 1,
    'builtins.py:<module>.make_global_env.apply_raw_fn:invoke_callable': 1,
    'builtins.py:<module>.make_global_env.cors_fn.cors_handler:_invoke_from_builtin': 1,
    'builtins.py:<module>.make_global_env.flat_map_some_fn:_invoke_from_builtin': 1,
    'builtins.py:<module>.make_global_env.keep_some_else_fn.iterator:_invoke_from_builtin': 2,
    'builtins.py:<module>.make_global_env.map_some_fn:_invoke_from_builtin': 1,
    'builtins.py:<module>.make_global_env.meta_host_apply_fn:invoke_callable': 1,
    'builtins.py:<module>.make_global_env.or_else_with_fn:_invoke_from_builtin': 1,
    'builtins.py:<module>.make_global_env.rules_kernel_fn.iterator:_invoke_from_builtin': 1,
    'builtins.py:<module>.make_global_env.scan_fn.iterator:_invoke_from_builtin': 1,
    'builtins.py:<module>.make_global_env.scan_fn:_invoke_from_builtin': 1,
    'builtins.py:<module>.make_global_env.tick_fn.iterator:_invoke_from_builtin': 1,
    'callable.py:<module>.GeniaFunction.__call__:eval_with_tco': 1,
    'callable.py:<module>.GeniaFunctionGroup.__call__:eval_with_tco': 1,
    'callable.py:<module>.GeniaLinkedOpenFunction.__call__:eval_with_tco': 1,
    'callable.py:<module>.GeniaOpenFunction.__call__:eval_with_tco': 1,
    'callable.py:<module>.invoke_callable:invoke_callable': 2,
    'evaluator.py:<module>.Evaluator.call_matcher:invoke_callable': 1,
    'evaluator.py:<module>.Evaluator.eval_binary:invoke_callable': 1,
    'evaluator.py:<module>.Evaluator.eval_call:invoke_callable': 1,
    'evaluator.py:<module>.Evaluator.eval_pipeline_stage.invoke_with_pipeline_option_lifting:invoke_callable': 2,
    'evaluator.py:<module>.Evaluator.invoke_callable:_invoke_callable': 1,
    'evaluator.py:<module>.Evaluator.resolve_named_pattern:invoke_callable': 1,
    'interpreter.py:<module>._run_serve_file:assemble_route_handler': 1,
    'model.py:<module>.GeniaModelProvider._attempt:_handler': 1,
    'retrieval.py:<module>.GeniaEmbedProvider._attempt:_handler': 1,
    'retrieval.py:<module>.GeniaIndexProvider._attempt:_handler': 1,
    'retrieval.py:<module>.GeniaRerankProvider._attempt:_handler': 1,
    'retrieval.py:<module>.GeniaRetrieveProvider._attempt:_handler': 1,
}

# HOST_ONLY entries do not invoke a Genia callable: Gemini's _handler constructs
# its Python transport adapter; handler-shape predicates inspect values only;
# process_transport threads drain Popen stdout/stderr bytes with _StreamDrain.run.
HOST_ONLY_SITES = {
    'gemini_rest.py:<module>.create_gemini_rest_model_provider:_handler': 1,
    'http_annotation_binding.py:<module>.resolve_http_annotation:_is_exact_zero_argument_handler': 1,
    'process_transport.py:<module>.launch_process:Thread': 2,
    'process_transport.py:<module>.launch_process:start': 2,
    'server_route_binding.py:<module>.discover_route_bindings:_is_exact_one_argument_handler': 1,
}

# Each direct BOUNDARY must lexically enclose the actual invocation in a
# _publication_barrier context (including finally-based restoration by that helper).
BOUNDARY_SITES = {
    'builtins.py:<module>.make_global_env.serve_http_fn._GeniaRequestHandler._serve:_invoke_from_builtin': 1,
    'interpreter.py:<module>._resolve_program_result:main_with_args': 1,
    'interpreter.py:<module>._resolve_program_result:main_without_args': 1,
    'test_kernel.py:<module>.run_test_unit:body': 1,
    'values.py:<module>.GeniaCell._run:update_fn': 1,
    'values.py:<module>.GeniaProcess._run:_handler': 1,
}

# Thread/start sites are BOUNDARY origins. Authority is cut at the associated
# worker dispatch, not around Thread.start on the requesting thread. The checker
# also pins the self._thread -> self._run route, so changing the target cannot
# keep the same site/count while bypassing the required worker barrier.
THREAD_BOUNDARIES = {
    'values.py:<module>.GeniaCell.__init__:Thread': 'values.py:<module>.GeniaCell._run:update_fn',
    'values.py:<module>.GeniaCell.__init__:start': 'values.py:<module>.GeniaCell._run:update_fn',
    'values.py:<module>.GeniaCell.restart:Thread': 'values.py:<module>.GeniaCell._run:update_fn',
    'values.py:<module>.GeniaCell.restart:start': 'values.py:<module>.GeniaCell._run:update_fn',
    'values.py:<module>.GeniaProcess.__init__:Thread': 'values.py:<module>.GeniaProcess._run:_handler',
    'values.py:<module>.GeniaProcess.__init__:start': 'values.py:<module>.GeniaProcess._run:_handler',
}

CALL_NAMES = {
    'invoke_callable', '_invoke_callable', '_invoke_from_builtin', 'eval_with_tco',
    'handler', '_handler', 'callback', 'update_fn', 'body', 'main_with_args',
    'main_without_args', 'Thread', 'start', 'submit', 'call_soon', 'call_later', 'Timer',
}
SOURCE_ROOT = Path(__file__).resolve().parents[2] / 'src' / 'genia'


def _is_barrier(node):
    """Recognize the approved context manager, not an arbitrary with statement."""
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_publication_barrier'


def callable_sites(overrides=None):
    """Collect calls and their lexical barrier, resetting at deferred scope creation.

    Overrides support in-memory mutation checks; production files are never edited.
    A function/lambda defined inside a barrier does not inherit it when called later.
    """
    sites = {}
    for path in SOURCE_ROOT.rglob('*.py'):
        filename = path.relative_to(SOURCE_ROOT).as_posix()
        source = overrides[filename] if overrides and filename in overrides else path.read_text()

        def walk(node, owner='<module>', guarded=False, function=None):
            """Record enclosing scope and barrier for each selected invocation/start."""
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                owner += '.' + node.name
                guarded = False
                function = node
            elif isinstance(node, ast.Lambda):
                guarded = False
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    walk(item, owner, guarded, function)
                for child in node.body:
                    walk(child, owner, guarded or any(_is_barrier(item.context_expr) for item in node.items), function)
                return
            if isinstance(node, ast.Call):
                target = node.func
                name = target.id if isinstance(target, ast.Name) else target.attr if isinstance(target, ast.Attribute) else ''
                if name in CALL_NAMES or name.endswith(('handler', 'callback')):
                    sites.setdefault(f'{filename}:{owner}:{name}', []).append((node, guarded, function))
            for child in ast.iter_child_nodes(node):
                walk(child, owner, guarded, function)
        walk(ast.parse(source))
    return sites


def assert_dispatch_inventory(overrides=None):
    """Require an explicit policy/count for every site and prove boundary placement."""
    groups = [BRIDGE_SITES, HOST_ONLY_SITES, BOUNDARY_SITES, THREAD_BOUNDARIES]
    expected = {site for group in groups for site in group}
    assert len(expected) == sum(map(len, groups)), 'duplicate site classification'
    sites = callable_sites(overrides)
    assert set(sites) == expected, f'unclassified or removed dispatch sites: {set(sites) ^ expected}'
    for classification, group in [('BRIDGE', BRIDGE_SITES), ('HOST_ONLY', HOST_ONLY_SITES), ('BOUNDARY', BOUNDARY_SITES)]:
        for site, count in group.items():
            assert len(sites[site]) == count, f'dispatch count changed: {site}'
            if classification != 'HOST_ONLY':
                expected_guard = classification == 'BOUNDARY'
                assert all(guarded == expected_guard for _, guarded, _ in sites[site]), (
                    f'wrong barrier classification: {site}'
                )
    for site, dispatch in THREAD_BOUNDARIES.items():
        assert len(sites[site]) == 1, f'worker origin count changed: {site}'
        assert dispatch in BOUNDARY_SITES and all(guarded for _, guarded, _ in sites[dispatch]), (
            f'worker barrier missing: {dispatch}'
        )
        owner = site.rsplit(':', 1)[0]
        constructor, _, function = sites[owner + ':Thread'][0]
        targets = [ast.unparse(keyword.value) for keyword in constructor.keywords if keyword.arg == 'target']
        assert targets == ['self._run'], f'worker target changed: {site}'
        assert owner.rsplit('.', 1)[0] == dispatch.rsplit(':', 1)[0].rsplit('.', 1)[0], (
            f'worker owner changed: {site}'
        )
        assigned_to_thread = any(
            isinstance(node, ast.Assign) and node.value is constructor
            and any(ast.unparse(lhs) == 'self._thread' for lhs in node.targets)
            for node in ast.walk(function)
        )
        assert assigned_to_thread, f'worker assignment changed: {site}'
        if site.endswith(':start'):
            assert ast.unparse(sites[site][0][0].func) == 'self._thread.start', f'worker start changed: {site}'
    drains = sites['process_transport.py:<module>.launch_process:Thread']
    drain_targets = Counter(
        ast.unparse(keyword.value) for call, _, _ in drains
        for keyword in call.keywords if keyword.arg == 'target'
    )
    assert drain_targets == Counter(['stdout_drain.run', 'stderr_drain.run'])
    drain_starts = sites['process_transport.py:<module>.launch_process:start']
    assert Counter(ast.unparse(call.func) for call, _, _ in drain_starts) == Counter([
        'stdout_thread.start', 'stderr_thread.start',
    ])


def test_dispatch_inventory_requires_explicit_classification():
    """Each inventoried site has a policy; every boundary's actual call is guarded."""
    assert_dispatch_inventory()


@pytest.mark.parametrize('site', sorted(BOUNDARY_SITES))
def test_inventory_detects_each_removed_boundary_barrier(site):
    """Removing any one required barrier must fail even when names/counts survive."""
    filename, _, call_name = site.split(':')
    tree = ast.parse((SOURCE_ROOT / filename).read_text())

    class RemoveBarrier(ast.NodeTransformer):
        """Unwrap only the barrier enclosing the selected real dispatch call."""
        def visit_With(self, node):
            """Keep the invocation intact so the mutation changes only its protection."""
            if any(_is_barrier(item.context_expr) for item in node.items):
                contains_dispatch = any(
                    isinstance(child, ast.Call) and (
                        getattr(child.func, 'id', None) or getattr(child.func, 'attr', None)
                    ) == call_name
                    for statement in node.body for child in ast.walk(statement)
                )
                if contains_dispatch:
                    return node.body
            return self.generic_visit(node)

    mutated = ast.unparse(RemoveBarrier().visit(tree))
    # The old identity/count snapshot accepts this mutant; the policy must not.
    assert {key: len(calls) for key, calls in callable_sites().items()} == {
        key: len(calls) for key, calls in callable_sites({filename: mutated}).items()
    }
    with pytest.raises(AssertionError, match='wrong barrier classification'):
        assert_dispatch_inventory({filename: mutated})


@pytest.mark.parametrize('worker', ['GeniaCell', 'GeniaProcess'])
def test_inventory_detects_rerouted_worker_target(worker):
    """A same-name/count thread origin cannot silently target an unguarded worker."""
    source = (SOURCE_ROOT / 'values.py').read_text()
    tree = ast.parse(source)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == worker)
    init = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '__init__')
    for node in ast.walk(init):
        if isinstance(node, ast.keyword) and node.arg == 'target':
            node.value = ast.parse('self._unclassified_run', mode='eval').body
    with pytest.raises(AssertionError, match='worker target changed'):
        assert_dispatch_inventory({'values.py': ast.unparse(tree)})


def test_inventory_rejects_new_unclassified_dispatch():
    """A new callable dispatcher needs an explicit reviewed classification."""
    source = (SOURCE_ROOT / 'test_kernel.py').read_text()
    source += '\n\ndef unrelated_dispatch(handler):\n    return handler()\n'
    with pytest.raises(AssertionError, match='unclassified or removed dispatch sites'):
        assert_dispatch_inventory({'test_kernel.py': source})


def test_entry_argument_provider_is_inside_the_same_boundary():
    """User-replaced argv is callable work performed for entry dispatch too."""
    import genia
    env, group, txn = fixture()
    seen = []

    def argv():
        """Attempt inherited admission during entry-argument preparation."""
        refused(lambda: group(1))
        seen.append('refused')
        return []

    env.set_host('argv', argv, visibility='runtime-public')
    genia.run_source('main(x) = 7', env)
    with window(txn):
        assert interpreter._resolve_program_result(None, env) == 7
        assert seen == ['refused']
        assert group(2) == 2
