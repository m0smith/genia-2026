from pathlib import Path

from genia.test_cli import run_native_tests_from_file


def test_web_header_native_tests_pass(capsys):
    fixture = Path("tests/native/web_header_behavior.genia")

    exit_code = run_native_tests_from_file(fixture)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=3 passed=3 failed=0 errored=0\n"
        "PASS with_headers_adds_normalizes_and_overrides_headers\n"
        "PASS with_headers_preserves_response_fields_and_inputs\n"
        "PASS with_headers_handles_empty_maps_and_later_case_variants\n"
        "total=3 passed=3 failed=0 errored=0\n"
    )
    assert captured.err == ""
