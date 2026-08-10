from pathlib import Path

from genia.test_cli import run_native_tests_from_file


def test_r3_validation_helpers_native_tests_pass(capsys):
    fixture = Path("tests/native/r3_validation_helpers.genia")

    exit_code = run_native_tests_from_file(fixture)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=15 passed=15 failed=0 errored=0\n"
        "PASS required_field_outcomes_are_stable\n"
        "PASS field_validation_outcomes_are_stable\n"
        "PASS nested_validation_paths_are_preserved\n"
        "PASS optional_fields_distinguish_absence_and_presence\n"
        "PASS optional_validators_preserve_and_normalize_outcomes\n"
        "PASS record_validation_builds_clean_records\n"
        "PASS record_validation_collects_diagnostics_in_order\n"
        "PASS record_validation_preserves_record_context\n"
        "PASS validate_each_preserves_list_shape_and_order\n"
        "PASS validate_each_preserves_upstream_outcomes\n"
        "PASS collect_validated_handles_empty_and_clean_inputs\n"
        "PASS collect_validated_reports_mixed_diagnostics\n"
        "PASS validation_pipeline_composes_end_to_end\n"
        "PASS field_index_diagnostic_constructors_preserve_values\n"
        "PASS field_index_diagnostic_accessors_reuse_map_absence\n"
        "total=15 passed=15 failed=0 errored=0\n"
    )
    assert captured.err == ""
