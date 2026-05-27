import pytest


def _format_report(suite):
    from genia.test_cli import format_test_suite_report

    return format_test_suite_report(suite)


def test_formats_passing_suite_with_summary_before_and_after_results():
    report = _format_report(
        {
            "total": 1,
            "passed": 1,
            "failed": 0,
            "errored": 0,
            "results": [
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
                }
            ],
        }
    )

    assert report == (
        "total=1 passed=1 failed=0 errored=0\n"
        "PASS passes\n"
        "total=1 passed=1 failed=0 errored=0\n"
    )


def test_formats_failed_expectation_with_reason_expected_and_actual():
    report = _format_report(
        {
            "total": 1,
            "passed": 0,
            "failed": 1,
            "errored": 0,
            "results": [
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
                }
            ],
        }
    )

    assert report == (
        "total=1 passed=0 failed=1 errored=0\n"
        "FAIL fails phase=evaluation reason=values differed expected=3 actual=4\n"
        "total=1 passed=0 failed=1 errored=0\n"
    )


def test_formats_runtime_error_result():
    report = _format_report(
        {
            "total": 1,
            "passed": 0,
            "failed": 0,
            "errored": 1,
            "results": [
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
                }
            ],
        }
    )

    assert report == (
        "total=1 passed=0 failed=0 errored=1\n"
        "ERROR errors phase=evaluation reason=boom\n"
        "total=1 passed=0 failed=0 errored=1\n"
    )


def test_formats_discovery_error_empty_name_as_unnamed():
    report = _format_report(
        {
            "total": 1,
            "passed": 0,
            "failed": 0,
            "errored": 1,
            "results": [
                {
                    "kind": "error",
                    "name": "",
                    "phase": "discovery",
                    "reason": "test unit name must be a non-empty string",
                    "expected": None,
                    "actual": None,
                    "stdout": "",
                    "stderr": "",
                    "diagnostics": {},
                }
            ],
        }
    )

    assert report == (
        "total=1 passed=0 failed=0 errored=1\n"
        "ERROR <unnamed> phase=discovery reason=test unit name must be a non-empty string\n"
        "total=1 passed=0 failed=0 errored=1\n"
    )


def test_formats_empty_suite_with_duplicate_zero_summary_and_one_final_newline():
    report = _format_report(
        {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errored": 0,
            "results": [],
        }
    )

    assert report == (
        "total=0 passed=0 failed=0 errored=0\n"
        "total=0 passed=0 failed=0 errored=0\n"
    )
    assert report.endswith("\n")
    assert not report.endswith("\n\n")


def test_formatter_rejects_unknown_result_kind():
    with pytest.raises(ValueError, match="unknown test result kind: skip"):
        _format_report(
            {
                "total": 1,
                "passed": 0,
                "failed": 0,
                "errored": 0,
                "results": [
                    {
                        "kind": "skip",
                        "name": "future",
                        "phase": "evaluation",
                        "reason": None,
                        "expected": None,
                        "actual": None,
                        "stdout": "",
                        "stderr": "",
                        "diagnostics": {},
                    }
                ],
            }
        )
