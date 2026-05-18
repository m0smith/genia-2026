from pathlib import Path

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]

REQUIRED_FORMAT_FIELD_PATH_SPECS = {
    "eval": {
        "format-field-path-nested",
        "format-field-path-multi-nested",
        "format-field-path-mixed-top-level",
        "format-field-path-repeated",
        "format-field-path-debug-rendering",
        "format-field-path-format-spec",
    },
    "error": {
        "error-format-field-path-missing-top-level",
        "error-format-field-path-missing-nested",
        "error-format-field-path-non-map-intermediate",
        "error-format-field-path-invalid-leading-dot",
        "error-format-field-path-invalid-trailing-dot",
        "error-format-field-path-invalid-double-dot",
        "error-format-field-path-invalid-index",
        "error-format-field-path-slash-separator",
        "error-format-field-path-slash-nested",
        "error-format-field-path-mixed-slash-dot",
    },
}


def test_issue_290_format_field_path_shared_spec_inventory_is_present():
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {
        category: {spec.name for spec in specs if spec.category == category}
        for category in REQUIRED_FORMAT_FIELD_PATH_SPECS
    }

    missing = {
        category: sorted(expected - discovered[category])
        for category, expected in REQUIRED_FORMAT_FIELD_PATH_SPECS.items()
        if expected - discovered[category]
    }

    assert missing == {}


def test_issue_290_format_field_path_shared_specs_execute_as_contract():
    failures_by_name = {}

    for category, names in REQUIRED_FORMAT_FIELD_PATH_SPECS.items():
        for name in sorted(names):
            spec = load_spec(REPO / "spec" / category / f"{name}.yaml")
            actual = execute_spec(spec)
            failures = compare_spec(spec, actual)
            if failures:
                failures_by_name[name] = [
                    (failure.field, failure.expected, failure.actual)
                    for failure in failures
                ]

    assert failures_by_name == {}
