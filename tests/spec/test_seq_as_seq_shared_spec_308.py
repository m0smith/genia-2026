from __future__ import annotations

from pathlib import Path

import pytest

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]

REQUIRED_AS_SEQ_SHARED_SPECS = {
    "as-seq-list-collect",
    "as-seq-nested-list-preserves-inner-list",
    "as-seq-empty-list-collect",
    "as-seq-list-reusable",
    "as-seq-string-collect",
    "as-seq-empty-string-collect",
    "as-seq-string-each-run",
    "as-seq-rejects-number",
    "issue-306-seq-boundary-string-collect-error",
    "issue-306-seq-boundary-string-each-error",
    "issue-306-seq-boundary-string-map-error",
    "issue-306-seq-boundary-string-run-error",
}


def test_issue_308_as_seq_shared_spec_inventory_is_present() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    eval_names = {spec.name for spec in specs if spec.category == "eval"}

    missing = sorted(REQUIRED_AS_SEQ_SHARED_SPECS - eval_names)

    assert missing == []


@pytest.mark.slow
def test_issue_308_as_seq_shared_specs_execute_as_portable_observable_contract() -> None:
    failures_by_name = {}

    for name in sorted(REQUIRED_AS_SEQ_SHARED_SPECS):
        spec = load_spec(REPO / "spec" / "eval" / f"{name}.yaml")
        actual = execute_spec(spec)
        failures = compare_spec(spec, actual)
        if failures:
            failures_by_name[name] = [
                (failure.field, failure.expected, failure.actual)
                for failure in failures
            ]

    assert failures_by_name == {}
