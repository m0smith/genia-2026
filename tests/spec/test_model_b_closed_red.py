"""Slice E2.4 TEST-only RED harness for the shared closed-publication cases (issue #1250).

LANGUAGE CONTRACT: the frozen ``spec/{eval,error,cli}/model-b-closed-*.yaml`` inventory
is the shared executable evidence for Slice E design 10.2 (approved Q-C1b/DQ rulings).
PYTHON REFERENCE HOST: this module executes each case directly through the existing
shared-spec loader, ``execute_spec`` and ``compare_spec``; it adds no runner, comparator
or expected-output store. It deliberately bypasses the external-host applicability
gate, never consults capability claims, and uses no skip, xfail or slow marker, so the
unimplemented behavior is visible as a real mismatch until E2.4 GREEN.

Every case requires the optional ``closed_functions`` capability; the transitioned
Slice C case ``model-b-c-stage-closed-rejected`` (design 10.4) is deliberately NOT part
of this inventory and changes only in the separate transition commit.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs

REPO = Path(__file__).resolve().parents[2]
PREFIX = "model-b-closed-"
CAPABILITY = "closed_functions"

# Exact requires per case (design 9 item 4): closed_functions plus a capability only
# where the case uses it.
CLOSED_REQUIRES = {
    "model-b-closed-alias-clause-rejected": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-alias-mutable-name-immutable": ('closed_functions', 'repl'),
    "model-b-closed-annotation-effect-then-value-failure": ('closed_functions', 'repl', 'doc_help'),
    "model-b-closed-annotation-forbidden-cors": ('closed_functions',),
    "model-b-closed-annotation-forbidden-get": ('closed_functions',),
    "model-b-closed-annotation-forbidden-post": ('closed_functions',),
    "model-b-closed-annotation-forbidden-route": ('closed_functions',),
    "model-b-closed-annotation-forbidden-server": ('closed_functions',),
    "model-b-closed-annotation-helper-self-call": ('closed_functions', 'doc_help'),
    "model-b-closed-annotation-introspection-while-initializing": ('closed_functions', 'doc_help'),
    "model-b-closed-annotation-meta-keys-allowed": ('closed_functions', 'doc_help'),
    "model-b-closed-annotation-order-and-atomic-metadata": ('closed_functions', 'doc_help'),
    "model-b-closed-annotation-permitted-set": ('closed_functions', 'doc_help'),
    "model-b-closed-annotation-reaches-later-clause": ('closed_functions', 'doc_help'),
    "model-b-closed-annotation-recursion": ('closed_functions', 'default_open_functions', 'doc_help'),
    "model-b-closed-annotation-self-call": ('closed_functions', 'doc_help'),
    "model-b-closed-annotation-unknown-name": ('closed_functions',),
    "model-b-closed-comments-blank-lines-one-group": ('closed_functions', 'default_open_functions'),
    "model-b-closed-committed-export-callable": ('closed_functions', 'multi_file_eval', 'open_functions', 'default_open_functions'),
    "model-b-closed-committed-export-not-link-target": ('closed_functions', 'multi_file_eval', 'open_functions'),
    "model-b-closed-conflicting-docstring": ('closed_functions',),
    "model-b-closed-deep-tail-call": ('closed_functions', 'default_open_functions'),
    "model-b-closed-duplicate-key-no-effects": ('closed_functions',),
    "model-b-closed-failed-apply-raw": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-call": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-call-err": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-call-none": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-call-wrong-arity": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-escape-transport-cell": ('closed_functions', 'repl', 'refs', 'cell_primitives'),
    "model-b-closed-failed-escape-transport-ref": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-flow-not-pulled": ('closed_functions', 'repl', 'refs', 'flow_phase_1'),
    "model-b-closed-failed-flow-pulled": ('closed_functions', 'repl', 'refs', 'flow_phase_1'),
    "model-b-closed-failed-higher-order": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-inner-lambda-self-reference": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-introspection": ('closed_functions', 'repl', 'refs', 'doc_help'),
    "model-b-closed-failed-matcher": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-pipeline-upstream-none-skips": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-failed-tail-call": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-main-selection": ('closed_functions',),
    "model-b-closed-mixed-operators": ('closed_functions',),
    "model-b-closed-multi-clause-order": ('closed_functions',),
    "model-b-closed-name-collision-existing": ('closed_functions',),
    "model-b-closed-name-collision-import": ('closed_functions', 'multi_file_eval'),
    "model-b-closed-name-reserved-runtime": ('closed_functions',),
    "model-b-closed-ordinary-clause-after-closed": ('closed_functions',),
    "model-b-closed-ordinary-linking-unaffected": ('closed_functions', 'multi_file_eval', 'open_functions', 'default_open_functions'),
    "model-b-closed-parameter-shadows-own-name": ('closed_functions',),
    "model-b-closed-pattern-guard-headers": ('closed_functions', 'default_open_functions'),
    "model-b-closed-reexported-closed-not-link-target": ('closed_functions', 'multi_file_eval', 'open_functions'),
    "model-b-closed-repl-later-submission-clause": ('closed_functions', 'repl'),
    "model-b-closed-repl-name-reuse-new-identity": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-restored-name-clause-rejected": ('closed_functions', 'repl', 'refs'),
    "model-b-closed-second-group-after-statement": ('closed_functions', 'repl'),
    "model-b-closed-self-recursion": ('closed_functions', 'default_open_functions'),
    "model-b-closed-single-clause": ('closed_functions',),
    "model-b-closed-single-clause-call": ('closed_functions',),
    "model-b-closed-test-alias-discovered": ('closed_functions',),
    "model-b-closed-test-annotation-discovered": ('closed_functions',),
    "model-b-closed-test-meta-key-discovered": ('closed_functions',),
    "model-b-closed-validation-order": ('closed_functions',),
}

EXPECTED_CASE_COUNT = 60


def _load():
    """Discover every shared spec once; returns `(specs, invalid)` exactly as `discover_specs` reports them."""
    return discover_specs()


_SPECS, _INVALID = _load()
_CLOSED = {s.name: s for s in _SPECS if s.name.startswith(PREFIX)}


def test_inventory_is_frozen_and_complete() -> None:
    assert len(CLOSED_REQUIRES) == EXPECTED_CASE_COUNT
    assert _INVALID == [], [f"{i.path}: {i.message}" for i in _INVALID]
    loaded = [s.name for s in _SPECS if s.name.startswith(PREFIX)]
    assert len(loaded) == len(set(loaded)) == EXPECTED_CASE_COUNT
    assert set(loaded) == set(CLOSED_REQUIRES)
    for spec in _CLOSED.values():
        assert spec.path.stem == spec.name


def test_exact_requires_per_case() -> None:
    mismatches = {
        name: (tuple(_CLOSED[name].requires), expected)
        for name, expected in CLOSED_REQUIRES.items()
        if tuple(_CLOSED[name].requires) != tuple(expected)
    }
    assert not mismatches, mismatches
    assert all(CAPABILITY in requires for requires in CLOSED_REQUIRES.values())


@pytest.mark.parametrize("name", sorted(CLOSED_REQUIRES))
def test_shared_case_passes_on_the_python_host(name: str) -> None:
    """Real executor output must equal the committed oracle (fails until E2.4 GREEN)."""
    spec = _CLOSED[name]
    failures = compare_spec(spec, execute_spec(spec))
    assert not failures, [(f.field, f.expected, f.actual) for f in failures]
