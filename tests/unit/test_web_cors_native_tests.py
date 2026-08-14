from pathlib import Path

from genia.test_cli import run_native_tests_from_file


def test_web_cors_native_tests_pass(capsys):
    fixture = Path("tests/native/web_cors_behavior.genia")

    exit_code = run_native_tests_from_file(fixture)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=5 passed=5 failed=0 errored=0\n"
        "PASS cors_defaults_decorate_ordinary_responses_once\n"
        "PASS cors_explicit_policy_serializes_and_overrides_collisions\n"
        "PASS cors_true_preflight_bypasses_handler\n"
        "PASS cors_ordinary_options_delegates_when_origin_is_missing\n"
        "PASS cors_ordinary_options_delegates_when_requested_method_is_missing\n"
        "total=5 passed=5 failed=0 errored=0\n"
    )
    assert captured.err == ""
