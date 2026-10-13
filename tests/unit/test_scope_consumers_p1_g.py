"""P1-G runtime consumers choose ownership explicitly without new scope semantics."""
from types import SimpleNamespace

import pytest

from genia.environment import Env
from hosts.python import mcp_worker_profile
from tools import gen_function_docs, lint_doc


def test_mcp_prunes_runtime_tables_without_pruning_supplied_unit():
    runtime = Env()
    runtime.values.update({'print': object(), 'secret_get': object(), 'future_capability': object()})
    runtime.binding_metadata.update({'secret_get': object(), 'future_capability': object()})
    runtime.autoloads.update({('abs', 1): 'allowed', ('read_file', 1): 'denied'})
    runtime.trusted_autoloads.update(runtime.autoloads)
    unit = SimpleNamespace(values={'unit_marker': 1}, runtime_scope=lambda: runtime)

    mcp_worker_profile.prune_environment(unit)

    assert unit.values == {'unit_marker': 1}
    assert set(runtime.values) == {'print'}
    assert not runtime.binding_metadata
    assert runtime.autoloads == {('abs', 1): 'allowed'}
    assert runtime.trusted_autoloads == {('abs', 1)}


def test_generator_uses_runtime_for_catalogue_lookup_and_metadata(monkeypatch):
    calls = []
    runtime = SimpleNamespace(
        autoloads={('fixture', 0): 'std/prelude/fixture.genia'},
        get=lambda name: calls.append(('value', name)),
        get_metadata=lambda name: calls.append(('metadata', name)),
    )
    monkeypatch.setattr(gen_function_docs, 'make_global_env', lambda _args: SimpleNamespace(runtime_scope=lambda: runtime))
    records = gen_function_docs.collect()
    assert any(record['name'] == 'fixture' for record in records)
    assert calls == [('value', 'fixture'), ('metadata', 'fixture')]


@pytest.mark.parametrize('helper', [lint_doc._runtime_public_names, lint_doc._runtime_public_prelude_names])
def test_linter_uses_runtime_autoload_catalogue(monkeypatch, helper):
    import genia.builtins
    runtime = SimpleNamespace(autoloads={('fixture', 0): 'std/prelude/fixture.genia', ('private', 0): 'other.genia'})
    monkeypatch.setattr(genia.builtins, 'make_global_env', lambda _args: SimpleNamespace(runtime_scope=lambda: runtime))
    names = helper()
    assert 'fixture' in names
    assert 'private' not in names
