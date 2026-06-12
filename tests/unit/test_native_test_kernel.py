from genia.test_kernel import (
    NativeTestFailure,
    TestUnit,
    aggregate_results,
    run_test_suite,
    run_test_unit,
    suite_exit_code,
)
from genia.values import GeniaMap


def test_passing_test_unit_result_aggregation_and_exit_code():
    result = run_test_unit(TestUnit("passes", lambda: None))

    assert result == {
        "kind": "pass",
        "name": "passes",
        "phase": "evaluation",
        "reason": None,
        "expected": None,
        "actual": None,
        "stdout": "",
        "stderr": "",
        "diagnostics": {},
    }

    suite = run_test_suite([TestUnit("passes", lambda: None)])
    assert suite == {
        "total": 1,
        "passed": 1,
        "failed": 0,
        "errored": 0,
        "results": [result],
    }
    assert suite_exit_code(suite) == 0


def test_failed_expectation_result_aggregation_and_exit_code():
    def body():
        raise NativeTestFailure("values differed", expected=3, actual=4)

    result = run_test_unit(TestUnit("fails", body))

    assert result == {
        "kind": "fail",
        "name": "fails",
        "phase": "evaluation",
        "reason": "values differed",
        "expected": 3,
        "actual": 4,
        "stdout": "",
        "stderr": "",
        "diagnostics": {},
    }

    suite = run_test_suite([TestUnit("fails", body)])
    assert suite == {
        "total": 1,
        "passed": 0,
        "failed": 1,
        "errored": 0,
        "results": [result],
    }
    assert suite_exit_code(suite) == 1


def test_runtime_error_result_aggregation_and_exit_code():
    def body():
        raise RuntimeError("boom")

    result = run_test_unit(TestUnit("errors", body))

    assert result == {
        "kind": "error",
        "name": "errors",
        "phase": "evaluation",
        "reason": "boom",
        "expected": None,
        "actual": None,
        "stdout": "",
        "stderr": "",
        "diagnostics": {},
    }

    suite = run_test_suite([TestUnit("errors", body)])
    assert suite == {
        "total": 1,
        "passed": 0,
        "failed": 0,
        "errored": 1,
        "results": [result],
    }
    assert suite_exit_code(suite) == 1


def test_malformed_named_test_unit_with_non_callable_body_is_discovery_error():
    result = run_test_unit(TestUnit("bad", "not callable"))

    assert result == {
        "kind": "error",
        "name": "bad",
        "phase": "discovery",
        "reason": "test unit body must be callable",
        "expected": None,
        "actual": None,
        "stdout": "",
        "stderr": "",
        "diagnostics": {},
    }
    assert isinstance(result["diagnostics"], dict)


def test_valid_string_test_metadata_remains_accepted():
    result = run_test_unit(
        TestUnit("passes", lambda: None, metadata={"description": "string metadata"})
    )

    assert result == {
        "kind": "pass",
        "name": "passes",
        "phase": "evaluation",
        "reason": None,
        "expected": None,
        "actual": None,
        "stdout": "",
        "stderr": "",
        "diagnostics": {},
    }


def test_non_string_metadata_value_is_discovery_error_with_location():
    result = run_test_unit(
        TestUnit(
            "bad_metadata",
            lambda: None,
            location="metadata_boundary.genia:2",
            metadata={"description": 123},
        )
    )

    assert result == {
        "kind": "error",
        "name": "bad_metadata",
        "phase": "discovery",
        "reason": (
            "invalid native test metadata value for key 'description': "
            "expected string, received int at metadata_boundary.genia:2"
        ),
        "expected": None,
        "actual": None,
        "stdout": "",
        "stderr": "",
        "diagnostics": {},
    }


def test_composite_metadata_values_are_discovery_errors():
    suite = run_test_suite(
        [
            TestUnit("list_metadata", lambda: None, metadata={"description": ["bad"]}),
            TestUnit(
                "map_metadata",
                lambda: None,
                metadata={"description": GeniaMap().put("bad", "value")},
            ),
        ]
    )

    assert suite == {
        "total": 2,
        "passed": 0,
        "failed": 0,
        "errored": 2,
        "results": [
            {
                "kind": "error",
                "name": "list_metadata",
                "phase": "discovery",
                "reason": (
                    "invalid native test metadata value for key 'description': "
                    "expected string, received list"
                ),
                "expected": None,
                "actual": None,
                "stdout": "",
                "stderr": "",
                "diagnostics": {},
            },
            {
                "kind": "error",
                "name": "map_metadata",
                "phase": "discovery",
                "reason": (
                    "invalid native test metadata value for key 'description': "
                    "expected string, received map"
                ),
                "expected": None,
                "actual": None,
                "stdout": "",
                "stderr": "",
                "diagnostics": {},
            },
        ],
    }
    assert suite_exit_code(suite) == 1


def test_non_string_metadata_key_is_discovery_error():
    result = run_test_unit(TestUnit("bad_key", lambda: None, metadata={1: "value"}))

    assert result == {
        "kind": "error",
        "name": "bad_key",
        "phase": "discovery",
        "reason": "invalid native test metadata key: expected string, received int",
        "expected": None,
        "actual": None,
        "stdout": "",
        "stderr": "",
        "diagnostics": {},
    }


def test_aggregation_preserves_order_and_counts_mixed_results():
    results = [
        {
            "kind": "pass",
            "name": "passes",
            "phase": "evaluation",
            "reason": None,
            "expected": None,
            "actual": None,
            "stdout": "",
            "stderr": "",
            "diagnostics": {},
        },
        {
            "kind": "fail",
            "name": "fails",
            "phase": "evaluation",
            "reason": "values differed",
            "expected": 3,
            "actual": 4,
            "stdout": "",
            "stderr": "",
            "diagnostics": {},
        },
        {
            "kind": "error",
            "name": "errors",
            "phase": "evaluation",
            "reason": "boom",
            "expected": None,
            "actual": None,
            "stdout": "",
            "stderr": "",
            "diagnostics": {},
        },
    ]

    assert aggregate_results(results) == {
        "total": 3,
        "passed": 1,
        "failed": 1,
        "errored": 1,
        "results": results,
    }


def test_empty_suite_aggregates_as_successful_kernel_result():
    suite = run_test_suite([])

    assert suite == {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errored": 0,
        "results": [],
    }
    assert suite_exit_code(suite) == 0
