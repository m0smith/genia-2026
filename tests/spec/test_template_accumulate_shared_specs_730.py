"""Shared-spec inventory/execution contract for E15-3 (#730) accumulate."""

from pathlib import Path

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec

REPO = Path(__file__).resolve().parents[2]

REQUIRED = {
    "eval": {
        "template-accumulate-multi-field-failures",
        "template-accumulate-nested-depth-first",
        "template-accumulate-exact-missing-extra-order",
        "template-accumulate-default-field",
        "template-accumulate-refinement-leaf",
        "template-accumulate-success-returns-real-value",
    },
    "error": {
        "error-accumulate-non-callable",
        "error-accumulate-opaque-template",
    },
}


def test_issue_730_accumulate_shared_spec_inventory_is_present():
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {
        category: {spec.name for spec in specs if spec.category == category}
        for category in REQUIRED
    }
    for category, names in REQUIRED.items():
        assert names.issubset(discovered[category])


def test_issue_730_accumulate_shared_specs_execute_as_contract():
    failures_by_name = {}
    for category, names in REQUIRED.items():
        for name in sorted(names):
            spec = load_spec(REPO / "spec" / category / f"{name}.yaml")
            failures = compare_spec(spec, execute_spec(spec))
            if failures:
                failures_by_name[name] = [
                    (failure.field, failure.expected, failure.actual)
                    for failure in failures
                ]

    assert failures_by_name == {}
