from pathlib import Path

from genia.test_cli import run_native_tests_from_file


def test_outcome_rendering_native_tests_pass(capsys):
    fixture = Path("tests/native/outcome_rendering.genia")

    exit_code = run_native_tests_from_file(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=6 passed=6 failed=0 errored=0\n"
        "PASS some_values_render_deterministically\n"
        "PASS some_with_context_renders_deterministically\n"
        "PASS none_values_render_deterministically\n"
        "PASS err_values_render_deterministically\n"
        "PASS outcome_predicates_identify_some_and_none\n"
        "PASS absence_helpers_expose_reason_and_context\n"
        "total=6 passed=6 failed=0 errored=0\n"
    )
    assert captured.err == ""
