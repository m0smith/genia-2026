from pathlib import Path

from genia.test_cli import run_native_tests_from_file


def test_flow_seq_native_tests_pass(capsys):
    fixture = Path("tests/native/flow_seq_behavior.genia")

    exit_code = run_native_tests_from_file(fixture)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=5 passed=5 failed=0 errored=0\n"
        "PASS flow_map_transforms_visible_values\n"
        "PASS flow_filter_preserves_matching_values_in_order\n"
        "PASS flow_scan_emits_accumulated_values\n"
        "PASS list_collect_returns_reusable_list_values\n"
        "PASS list_run_traverses_and_returns_none\n"
        "total=5 passed=5 failed=0 errored=0\n"
    )
    assert captured.err == ""
