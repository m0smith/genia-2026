from pathlib import Path

from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import discover_specs, load_spec


REPO = Path(__file__).resolve().parents[2]

REQUIRED_TEMPLATE_MATCHER_ERROR_SPECS = {
    "error-template-at-check-non-outcome-return",
    "error-template-at-assert-non-outcome-return",
    "error-template-compose-left-non-outcome-return",
    "error-template-compose-right-non-outcome-return",
}

REQUIRED_TEMPLATE_MATCHER_PARSE_SPECS = {
    "parse-template-at-check-compose-precedence",
    "parse-template-compose",
}

REQUIRED_TEMPLATE_MATCHER_IR_SPECS = {
    "template-compose",
}

REQUIRED_TEMPLATE_MATCHER_EVAL_SPECS = {
    "template-at-check-some",
    "template-at-check-none",
    "template-at-check-err",
    "template-at-assert-some",
    "template-compose-success-passes-value",
    "template-compose-right-sees-original-subject",
    "template-compose-second-none",
    "template-compose-first-none-short-circuit",
    "template-compose-first-err-short-circuit",
}


def test_template_matcher_error_shared_spec_inventory_is_present():
    specs, invalid_specs = discover_specs()

    assert not invalid_specs
    discovered = {
        category: {spec.name for spec in specs if spec.category == category}
        for category in ("parse", "ir", "eval", "error")
    }

    assert REQUIRED_TEMPLATE_MATCHER_PARSE_SPECS.issubset(discovered["parse"])
    assert REQUIRED_TEMPLATE_MATCHER_IR_SPECS.issubset(discovered["ir"])
    assert REQUIRED_TEMPLATE_MATCHER_EVAL_SPECS.issubset(discovered["eval"])
    assert REQUIRED_TEMPLATE_MATCHER_ERROR_SPECS.issubset(discovered["error"])


def test_template_matcher_error_shared_specs_execute_as_contract():
    failures_by_name = {}

    cases = {
        "parse": REQUIRED_TEMPLATE_MATCHER_PARSE_SPECS,
        "ir": REQUIRED_TEMPLATE_MATCHER_IR_SPECS,
        "eval": REQUIRED_TEMPLATE_MATCHER_EVAL_SPECS,
        "error": REQUIRED_TEMPLATE_MATCHER_ERROR_SPECS,
    }

    for category, names in cases.items():
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
