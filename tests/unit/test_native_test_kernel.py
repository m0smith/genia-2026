from genia.test_kernel import (
    NativeTestFailure,
    TestUnit,
    aggregate_results,
    run_test_suite,
    run_test_unit,
    suite_exit_code,
)


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
