from pathlib import Path

from genia.native_test_runner import run_native_tests


def test_tic_tac_toe_native_test_examples_pass(capsys):
    fixture = Path("examples/tic_tac_toe_native_tests.genia")

    exit_code = run_native_tests(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "[PASS] winner_detects_row_column_and_diagonal_wins\n"
        "[PASS] winner_reports_no_winner_on_open_board\n"
        "[PASS] is_legal_move_checks_target_square_state\n"
        "[PASS] set_at_replaces_only_the_targeted_index\n"
        "[PASS] contains_empty_reports_whether_open_squares_remain\n"
        "[PASS] next_player_alternates_marker\n"
        "Summary: total=6 passed=6 failed=0 errors=0\n"
    )
    assert captured.err == ""
