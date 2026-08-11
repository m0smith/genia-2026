from pathlib import Path

from genia.test_cli import run_native_tests_from_file


def test_sheet_native_tests_pass(capsys):
    fixture = Path("tests/native/sheet_helper_behavior.genia")

    exit_code = run_native_tests_from_file(fixture)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=8 passed=8 failed=0 errored=0\n"
        "PASS sheet_shape_columns_and_rows_are_deterministic\n"
        "PASS empty_sheet_has_zero_shape_columns_and_rows\n"
        "PASS sheet_select_reorders_columns_and_preserves_original\n"
        "PASS sheet_where_filters_rows_and_preserves_original\n"
        "PASS sheet_derive_appends_outcome_cells_and_preserves_original\n"
        "PASS row_get_returns_named_cell_directly_and_inside_where_derive\n"
        "PASS collect_sheet_builds_sheet_from_homogeneous_records\n"
        "PASS render_csv_produces_deterministic_escaped_report_text\n"
        "total=8 passed=8 failed=0 errored=0\n"
    )
    assert captured.err == ""
