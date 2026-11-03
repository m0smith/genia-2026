"""D2a RED diagnostics only: never implement completion lookup, linking or publication.

Run with PYTHONPATH=src uv run --no-sync python -m tests.unit.model_b_d2a_diagnostic.
The optional --target-shim-pytest flag runs supplied pytest arguments under a
constructor-only shim. Such results are DIAGNOSTIC, never RED acceptance counts.
The shim keeps real duplicate validation and exact records/closures and holds G
strongly. It does not add dataclass fields, change equality/repr, suppress errors,
or provide any other absent D2a seam. The original constructor is always restored.
"""
from contextlib import contextmanager
from pathlib import Path
import json
import tempfile

import genia
from genia import callable as callables
from tests.unit.model_b_d2a_support import base_world, contributor


@contextmanager
def target_shim():
    """Accept the inert target kwarg while delegating every real constructor check."""
    original = callables.GeniaOpenContributionUnit.__init__

    def diagnostic_init(self, *args, target=None, **kwargs):
        """Run the real constructor, then store the inert `target`."""
        original(self, *args, **kwargs)
        self.target = target

    callables.GeniaOpenContributionUnit.__init__ = diagnostic_init
    try:
        yield
    finally:
        callables.GeniaOpenContributionUnit.__init__ = original


def fixtures(directory):
    """Check bounded source fixtures and the shim against existing real runtime paths.

    These checks cannot validate a future link_view or its downstream assertions.
    They intentionally prove only source/record preparation and old dispatch paths.
    """
    from tests.unit.test_model_b_d2a_link_core import F5, NESTED_KEYS
    from tests.unit.test_model_b_d2a_link_dispatch import MATCHER_SOURCE, SELF_SOURCE, MUTUAL_SOURCE
    from tests.unit.test_model_b_d2a_link_publish import CountingLock, bounded_process

    results = []
    lock = CountingLock()
    with lock:
        try:
            with lock:
                raise AssertionError('nested lock was admitted')
        except AssertionError as error:
            assert 'nested binding lock' in str(error)
    bounded_process(lambda: None)
    import threading
    try:
        bounded_process(lambda: threading.Event().wait(60), timeout=0.05)
    except AssertionError as error:
        assert 'bounded deadline' in str(error)
    else:
        raise AssertionError('timeout containment failed')
    results.append('bounded harness normal exit and non-reentrant rejection')
    root = genia.make_global_env([])
    events = []
    outcome = genia.run_source('err("matcher-failed", {stage: "header"})', root)
    root.set_host('match_probe', lambda value: events.append(('matcher', value)) or outcome,
                  visibility='runtime-public')
    for label in ('guard_probe', 'body_probe', 'fallback_probe'):
        root.set_host(label, lambda value, name=label: events.append((name, value)) or True,
                      visibility='runtime-public')
    root, entry, module, group = base_world(directory / 'matcher', MATCHER_SOURCE, root=root)
    assert group(7) is outcome and events == [('matcher', 7)]
    results.append('matcher source returns exact err on existing group path')
    root, entry, module, group = base_world(directory / 'self', SELF_SOURCE)
    assert group(2000, 0) == 2000
    results.append('ordinary identifier-header self-TCO fixture (not linked)')
    root, entry, module, group = base_world(directory / 'mutual', MUTUAL_SOURCE,
                                          {'other': MUTUAL_SOURCE})
    other = root.load_module('other', entry).get_export('f')
    group.records[0].closure.set_host('peer', other, visibility='runtime-public')
    other.records[0].closure.set_host('peer', group, visibility='runtime-public')
    assert group(2001, 0) == 2001
    results.append('ordinary identifier-header mutual-TCO fixture (not linked)')
    with target_shim():
        root, entry, module, group = base_world(directory / 'keys', F5)
        for number, (left, right, equal) in enumerate(NESTED_KEYS):
            a = contributor(root, entry, directory / 'keys', 'a' + str(number), group, [left])
            b = contributor(root, entry, directory / 'keys', 'b' + str(number), group, [right])
            assert (a.clauses[0].dispatch_key == b.clauses[0].dispatch_key) is equal
        harvested = root.loaded_modules['a0'].contributions[('iface', 'f')]
        unit = callables.GeniaOpenContributionUnit(group.owner, 'copied', list(harvested.clauses), target=group)
        assert unit.target is group and unit.clauses[0] is harvested.clauses[0]
        assert unit.clauses[0].closure is harvested.clauses[0].closure
        try:
            callables.GeniaOpenContributionUnit(group.owner, 'duplicate',
                                               [unit.clauses[0], unit.clauses[0]], target=group)
        except callables.OpenFunctionDuplicateClauseError:
            pass
        else:
            raise AssertionError('shim bypassed real duplicate validation')
        # Diagnostic checks for all literal contributor clauses in test calls.
        import ast
        sources = set()
        for path in Path(__file__).parent.glob('test_model_b_d2a_link_*.py'):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.List) and node.elts and all(isinstance(e, ast.Constant) and
                    isinstance(e.value, str) and e.value.startswith('f(') and '=' in e.value
                    for e in node.elts):
                    sources.add(tuple(e.value for e in node.elts))
        for number, clauses in enumerate(sorted(sources)):
            contributor(root, entry, directory / 'keys', 'literal' + str(number), group, clauses)
    # Load literal base sources independently of completion_for/link_view so missing
    # seams cannot hide later source-fixture parser/loader defects.
    base_sources = set()
    for path in Path(__file__).parent.glob('test_model_b_d2a_link_*.py'):
        for node in ast.walk(ast.parse(path.read_text())):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in ('base_world', 'view_of') and len(node.args) > 1
                and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str)):
                base_sources.add(node.args[1].value)
    for number, source in enumerate(sorted(base_sources)):
        fixture_root = genia.make_global_env([])
        fixture_root.set_host('literalize', lambda value: value, visibility='runtime-public')
        base_world(directory / ('literalbase' + str(number)), source, root=fixture_root)
    results.append('nested structural keys, literal contribution/base sources and target shim validation')
    assert callables.GeniaOpenContributionUnit.__init__.__name__ != 'diagnostic_init'
    return results


def main():
    """Emit bounded diagnostics or explicitly labelled shim-assisted pytest results."""
    import sys
    if sys.argv[1:2] == ['--target-shim-pytest']:
        import pytest
        print('DIAGNOSTIC ONLY: target constructor shim active; no D2a acceptance claim')
        with target_shim():
            status = pytest.main(sys.argv[2:])
        raise SystemExit(status)
    with tempfile.TemporaryDirectory(prefix='genia-d2a-fixture-') as directory:
        print(json.dumps({'classification': 'diagnostic, not linked-view acceptance',
                          'checks': fixtures(Path(directory))}, indent=2))


if __name__ == '__main__':
    main()
