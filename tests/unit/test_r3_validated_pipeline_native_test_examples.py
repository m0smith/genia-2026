from pathlib import Path

from genia.native_test_runner import run_native_tests


def test_r3_validated_pipeline_native_test_examples_pass(capsys):
    fixture = Path("examples/r3_validated_pipeline_native_tests.genia")

    exit_code = run_native_tests(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "[PASS] validated pipeline preserves upstream Outcome boundaries\n"
        "[PASS] validate_each feeds collect_validated directly\n"
        "[PASS] validated JSONL pipeline keeps clean records and diagnostics observable\n"
        "Summary: total=3 passed=3 failed=0 errors=0\n"
    )
    assert captured.err == ""
