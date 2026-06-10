from pathlib import Path

from genia.native_test_runner import run_native_tests


def test_r3_validation_helpers_native_tests_pass(capsys):
    fixture = Path("tests/native/r3_validation_helpers.genia")

    exit_code = run_native_tests(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "[PASS] validate_required and validate_field return current outcomes\n"
        "[PASS] validate_optional handles missing and present fields\n"
        "[PASS] validate_record composes field validators\n"
        "[PASS] validate_each preserves list order and outcome boundaries\n"
        "[PASS] collect_validated aggregates clean records and diagnostics\n"
        "Summary: total=5 passed=5 failed=0 errors=0\n"
    )
    assert captured.err == ""
