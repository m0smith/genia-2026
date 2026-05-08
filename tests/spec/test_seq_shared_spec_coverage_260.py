from __future__ import annotations

from pathlib import Path

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]

REQUIRED_SEQ_SHARED_SPECS = {
    "eval": {
        "seq-compatible-list-each-preserves-items",
        "seq-compatible-run-nonseq-error",
        "seq-compatible-each-nonseq-error",
    },
    "flow": {
        "seq-compatible-flow-each-preserves-items",
        "seq-compatible-flow-scan-basic",
        "seq-compatible-flow-scan-bounded-evolve",
    },
}


def test_issue_260_seq_shared_spec_inventory_is_present() -> None:
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {
        category: {spec.name for spec in specs if spec.category == category}
        for category in REQUIRED_SEQ_SHARED_SPECS
    }

    missing = {
        category: sorted(expected - discovered[category])
        for category, expected in REQUIRED_SEQ_SHARED_SPECS.items()
        if expected - discovered[category]
    }

    assert missing == {}


def test_issue_260_seq_shared_specs_execute_as_portable_observable_contract() -> None:
    missing_paths = []
    failures_by_name = {}

    for category, names in REQUIRED_SEQ_SHARED_SPECS.items():
        for name in sorted(names):
            path = REPO / "spec" / category / f"{name}.yaml"
            if not path.exists():
                missing_paths.append(str(path.relative_to(REPO)))
                continue

            spec = load_spec(path)
            actual = execute_spec(spec)
            failures = compare_spec(spec, actual)
            if failures:
                failures_by_name[name] = [
                    (failure.field, failure.expected, failure.actual)
                    for failure in failures
                ]

    assert missing_paths == []
    assert failures_by_name == {}
