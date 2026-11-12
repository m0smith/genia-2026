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
    env, group, txn = fixture('main', 'main(x) = x')
    seen = []

    def entry(arg):
        """Exercise the actual selected-record call site, retaining outer authority."""
        refused(lambda: group(1))
        seen.append(arg)
        if raises:
            raise ValueError('main failure')
        return 7

    group.functions[1] = entry
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
            self.server_address = address
            self.handler = handler

        def handle_request(self):
            request = object.__new__(self.handler)
            request.command = 'HEAD'
            request.send_response = lambda status: seen.append(status)
            request.send_header = lambda *args: None
            request.end_headers = lambda: None
            request._serve()

        def server_close(self):
            seen.append('closed')

    def handler(request):
        """Attempt invocation inside the host's real HTTP dispatch boundary."""
        refused(lambda: group(1))
        seen.append('refused')
        if raises:
            raise ValueError('http failure')
        return values.GeniaMap({'status': 200, 'body': 'ok'})

    monkeypatch.setattr(builtins, 'HTTPServer', Server)
    monkeypatch.setattr(builtins, '_http_request_map', lambda request: values.GeniaMap())
    with window(txn):
        assert group(1) == 1
        env.get('serve_http')(values.GeniaMap({'max_requests': 1}), handler)
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
            self.message = message

        def get(self):
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


# BOUNDARY: the five design 6.3 dispatchers. Thread starts for Cell/Process
# lead to those boundaries. process_transport threads drain OS pipes only.
# Every other snapshotted callable entry below is a synchronous BRIDGE:
# evaluator/trampoline, callback, lazy/Flow, lifecycle or host adapter call.
CALL_NAMES = {
    'invoke_callable', '_invoke_callable', '_invoke_from_builtin', 'eval_with_tco',
    'handler', '_handler', 'callback', 'update_fn', 'body', 'main_with_args',
    'main_without_args', 'Thread', 'submit', 'call_soon', 'call_later', 'Timer',
}


def callable_sites():
    """Snapshot host dispatch and scheduling calls, independent of source line drift."""
    root = Path(__file__).resolve().parents[2] / 'src' / 'genia'
    sites = Counter()
    for path in root.rglob('*.py'):
        tree = ast.parse(path.read_text())
        def walk(node, owner='<module>'):
            """Retain enclosing names so newly introduced dispatchers need classification."""
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                owner += '.' + node.name
            if isinstance(node, ast.Call):
                target = node.func
                name = target.id if isinstance(target, ast.Name) else target.attr if isinstance(target, ast.Attribute) else ''
                if name in CALL_NAMES:
                    sites[f'{path.relative_to(root)}:{owner}:{name}'] += 1
            for child in ast.iter_child_nodes(node):
                walk(child, owner)
        walk(tree)
    return dict(sorted(sites.items()))


def test_dispatch_inventory_requires_explicit_classification():
    assert callable_sites() == EXPECTED_SITES


EXPECTED_SITES = {'builtins.py:<module>.make_global_env._invoke_from_builtin:invoke_callable': 1, 'builtins.py:<module>.make_global_env._invoke_raw_from_builtin:invoke_callable': 1, 'builtins.py:<module>.make_global_env.actor_call_update_fn:handler': 1, 'builtins.py:<module>.make_global_env.apply_raw_fn:invoke_callable': 1, 'builtins.py:<module>.make_global_env.cors_fn.cors_handler:_invoke_from_builtin': 1, 'builtins.py:<module>.make_global_env.flat_map_some_fn:_invoke_from_builtin': 1, 'builtins.py:<module>.make_global_env.keep_some_else_fn.iterator:_invoke_from_builtin': 2, 'builtins.py:<module>.make_global_env.map_some_fn:_invoke_from_builtin': 1, 'builtins.py:<module>.make_global_env.meta_host_apply_fn:invoke_callable': 1, 'builtins.py:<module>.make_global_env.or_else_with_fn:_invoke_from_builtin': 1, 'builtins.py:<module>.make_global_env.rules_kernel_fn.iterator:_invoke_from_builtin': 1, 'builtins.py:<module>.make_global_env.scan_fn.iterator:_invoke_from_builtin': 1, 'builtins.py:<module>.make_global_env.scan_fn:_invoke_from_builtin': 1, 'builtins.py:<module>.make_global_env.serve_http_fn._GeniaRequestHandler._serve:_invoke_from_builtin': 1, 'builtins.py:<module>.make_global_env.tick_fn.iterator:_invoke_from_builtin': 1, 'callable.py:<module>.GeniaFunction.__call__:eval_with_tco': 1, 'callable.py:<module>.GeniaFunctionGroup.__call__:eval_with_tco': 1, 'callable.py:<module>.GeniaLinkedOpenFunction.__call__:eval_with_tco': 1, 'callable.py:<module>.GeniaOpenFunction.__call__:eval_with_tco': 1, 'callable.py:<module>.invoke_callable:invoke_callable': 2, 'evaluator.py:<module>.Evaluator.call_matcher:invoke_callable': 1, 'evaluator.py:<module>.Evaluator.eval_binary:invoke_callable': 1, 'evaluator.py:<module>.Evaluator.eval_call:invoke_callable': 1, 'evaluator.py:<module>.Evaluator.eval_pipeline_stage.invoke_with_pipeline_option_lifting:invoke_callable': 2, 'evaluator.py:<module>.Evaluator.invoke_callable:_invoke_callable': 1, 'evaluator.py:<module>.Evaluator.resolve_named_pattern:invoke_callable': 1, 'gemini_rest.py:<module>.create_gemini_rest_model_provider:_handler': 1, 'interpreter.py:<module>._resolve_program_result:main_with_args': 1, 'interpreter.py:<module>._resolve_program_result:main_without_args': 1, 'model.py:<module>.GeniaModelProvider._attempt:_handler': 1, 'process_transport.py:<module>.launch_process:Thread': 2, 'retrieval.py:<module>.GeniaEmbedProvider._attempt:_handler': 1, 'retrieval.py:<module>.GeniaIndexProvider._attempt:_handler': 1, 'retrieval.py:<module>.GeniaRerankProvider._attempt:_handler': 1, 'retrieval.py:<module>.GeniaRetrieveProvider._attempt:_handler': 1, 'test_kernel.py:<module>.run_test_unit:body': 1, 'values.py:<module>.GeniaCell.__init__:Thread': 1, 'values.py:<module>.GeniaCell._run:update_fn': 1, 'values.py:<module>.GeniaCell.restart:Thread': 1, 'values.py:<module>.GeniaProcess.__init__:Thread': 1, 'values.py:<module>.GeniaProcess._run:_handler': 1}
