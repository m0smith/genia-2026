from pathlib import Path

from genia.native_test_runner import run_native_tests


def test_r1_validated_pipeline_native_tests_pass(capsys):
    fixture = Path("tests/native/r1_validated_pipeline.genia")

    exit_code = run_native_tests(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "[PASS] validated pipeline collects clean records and diagnostics\n"
        "Summary: total=1 passed=1 failed=0 errors=0\n"
    )
    assert captured.err == ""
