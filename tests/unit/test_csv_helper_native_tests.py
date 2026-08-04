from pathlib import Path

from genia.test_cli import run_native_tests_from_file


def test_csv_helper_native_tests_pass(capsys):
    fixture = Path("tests/native/csv_helper_behavior.genia")

    exit_code = run_native_tests_from_file(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=6 passed=6 failed=0 errored=0\n"
        "PASS valid_csv_row_returns_fields_with_context\n"
        "PASS quoted_csv_row_handles_commas_and_doubled_quotes\n"
        "PASS headers_map_parsed_csv_fields_positionally\n"
        "PASS blank_csv_row_returns_absence_with_context\n"
        "PASS malformed_csv_row_returns_recoverable_failure_with_context\n"
        "PASS all_csv_outcomes_preserve_exact_original_line_context\n"
        "total=6 passed=6 failed=0 errored=0\n"
    )
    assert captured.err == ""
