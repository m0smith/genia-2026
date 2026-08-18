from pathlib import Path

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]

REQUIRED = {
    "eval": {
        "json-representation-decode",
        "json-representation-encode",
        "json-representation-errors",
        "json-representation-number-boundaries",
    },
    "flow": {"json-representation-template-flow"},
    "error": {"error-json-decode-input-type"},
}


def test_issue_571_json_representation_shared_spec_inventory_is_present():
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {
        category: {spec.name for spec in specs if spec.category == category}
        for category in REQUIRED
    }
    for category, names in REQUIRED.items():
        assert names.issubset(discovered[category])


def test_issue_571_json_representation_shared_specs_execute_as_contract():
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
