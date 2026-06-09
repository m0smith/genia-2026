from pathlib import Path

from genia.test_cli import run_native_tests_from_file


def test_jsonl_helper_native_tests_pass(capsys):
    fixture = Path("tests/native/jsonl_helper_behavior.genia")

    exit_code = run_native_tests_from_file(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=5 passed=5 failed=0 errored=0\n"
        "PASS valid_json_object_returns_record_with_context\n"
        "PASS blank_line_returns_absence_with_context\n"
        "PASS malformed_json_returns_recoverable_failure_with_context\n"
        "PASS non_object_json_returns_recoverable_failure_with_context\n"
        "PASS all_jsonl_outcomes_preserve_exact_original_line_context\n"
        "total=5 passed=5 failed=0 errored=0\n"
    )
    assert captured.err == ""
