import pytest


def _format_report(suite):
    from genia.test_cli import format_test_suite_report

    return format_test_suite_report(suite)


def _run_native_test_source(tmp_path, capsys, source):
    from genia.test_cli import run_native_tests_from_file

    program = tmp_path / "native_tests.genia"
    program.write_text(source, encoding="utf-8")

    exit_code = run_native_tests_from_file(str(program))
    captured = capsys.readouterr()
    return exit_code, captured


def test_native_test_cli_runs_valid_annotated_native_test(tmp_path, capsys):
    exit_code, captured = _run_native_test_source(
        tmp_path,
        capsys,
        '@test "passes"\n'
        "passes() = assert_true(true)\n",
    )

    assert exit_code == 0
    assert captured.out == (
        "total=1 passed=1 failed=0 errored=0\n"
        "PASS passes\n"
        "total=1 passed=1 failed=0 errored=0\n"
    )
    assert "phase=discovery" not in captured.out
    assert captured.err == ""


def test_native_test_cli_reports_empty_test_description_as_discovery_error(
    tmp_path,
    capsys,
):
    exit_code, captured = _run_native_test_source(
        tmp_path,
        capsys,
        '@test ""\n'
        "bad_description() = assert_true(true)\n",
    )

    assert exit_code == 1
    assert (
        "ERROR bad_description phase=discovery "
        "reason=@test description must be a non-empty string\n"
    ) in captured.out
    assert "PASS bad_description" not in captured.out
    assert captured.err == ""


def test_native_test_cli_reports_test_on_non_function_as_discovery_error(
    tmp_path,
    capsys,
):
    exit_code, captured = _run_native_test_source(
        tmp_path,
        capsys,
        '@test "not a function"\n'
        "value = 1\n",
    )

    assert exit_code == 1
    assert (
        "ERROR value phase=discovery reason=@test must annotate a function\n"
        in captured.out
    )
    assert captured.err == ""


def test_native_test_cli_reports_parameterized_annotated_function_as_discovery_error(
    tmp_path,
    capsys,
):
    exit_code, captured = _run_native_test_source(
        tmp_path,
        capsys,
        '@test "has a parameter"\n'
        "needs_arg(x) = assert_true(true)\n",
    )

    assert exit_code == 1
    assert (
        "ERROR needs_arg phase=discovery "
        "reason=@test functions must take zero arguments\n"
    ) in captured.out
    assert "PASS needs_arg" not in captured.out
    assert captured.err == ""


def test_native_test_cli_reports_all_malformed_annotations_and_runs_valid_tests(
    tmp_path,
    capsys,
):
    exit_code, captured = _run_native_test_source(
        tmp_path,
        capsys,
        '@test ""\n'
        "bad_a() = assert_true(true)\n"
        "\n"
        '@test "has a parameter"\n'
        "bad_b(x) = assert_true(true)\n"
        "\n"
        '@test "valid"\n'
        "good() = assert_true(true)\n",
    )

    assert exit_code == 1
    assert (
        "ERROR bad_a phase=discovery "
        "reason=@test description must be a non-empty string\n"
    ) in captured.out
    assert (
        "ERROR bad_b phase=discovery "
        "reason=@test functions must take zero arguments\n"
    ) in captured.out
    assert "PASS good\n" in captured.out
    assert captured.err == ""


def test_native_test_cli_preserves_malformed_annotation_reason_before_duplicate_name(
    tmp_path,
    capsys,
):
    exit_code, captured = _run_native_test_source(
        tmp_path,
        capsys,
        'test("bad_duplicate", () -> assert_true(true))\n'
        "\n"
        '@test ""\n'
        "bad_duplicate() = assert_true(true)\n",
    )

    assert exit_code == 1
    assert (
        "ERROR bad_duplicate phase=discovery "
        "reason=@test description must be a non-empty string\n"
    ) in captured.out
    assert "duplicate native test name: bad_duplicate" not in captured.out
    assert "PASS bad_duplicate\n" in captured.out
    assert captured.err == ""


def test_native_test_cli_reports_duplicate_valid_native_test_names(
    tmp_path,
    capsys,
):
    exit_code, captured = _run_native_test_source(
        tmp_path,
        capsys,
        'test("same_name", () -> assert_true(true))\n'
        "\n"
        '@test "annotated duplicate"\n'
        "same_name() = assert_true(true)\n",
    )

    assert exit_code == 1
    assert (
        "ERROR same_name phase=discovery "
        "reason=duplicate native test name: same_name\n"
    ) in captured.out
    assert "PASS same_name" not in captured.out
    assert captured.err == ""


def test_native_test_cli_rejects_setup_annotation_instead_of_running_lifecycle_hook(
    tmp_path,
    capsys,
):
    exit_code, captured = _run_native_test_source(
        tmp_path,
        capsys,
        '@setup "not supported as lifecycle behavior"\n'
        "setup() = missing_name\n"
        "\n"
        '@test "ordinary test"\n'
        "ordinary() = assert_true(true)\n",
    )

    assert exit_code == 1
    assert captured.out == ""
    assert "Unsupported annotation: @setup" in captured.err
    assert "PASS ordinary" not in captured.out


def test_formats_passing_suite_with_summary_before_and_after_results():
    report = _format_report(
        {
            "total": 1,
            "passed": 1,
            "failed": 0,
            "errored": 0,
            "results": [
                {
                    "kind": "pass",
                    "name": "passes",
                    "phase": "evaluation",
                    "reason": None,
                    "expected": None,
                    "actual": None,
                    "stdout": "",
                    "stderr": "",
                    "diagnostics": {},
                }
            ],
        }
    )

    assert report == (
        "total=1 passed=1 failed=0 errored=0\n"
        "PASS passes\n"
        "total=1 passed=1 failed=0 errored=0\n"
    )


def test_formats_failed_expectation_with_reason_expected_and_actual():
    report = _format_report(
        {
            "total": 1,
            "passed": 0,
            "failed": 1,
            "errored": 0,
            "results": [
                {
                    "kind": "fail",
                    "name": "fails",
                    "phase": "evaluation",
                    "reason": "values differed",
                    "expected": 3,
                    "actual": 4,
                    "stdout": "",
                    "stderr": "",
                    "diagnostics": {},
                }
            ],
        }
    )

    assert report == (
        "total=1 passed=0 failed=1 errored=0\n"
        "FAIL fails phase=evaluation reason=values differed expected=3 actual=4\n"
        "total=1 passed=0 failed=1 errored=0\n"
    )


def test_formats_runtime_error_result():
    report = _format_report(
        {
            "total": 1,
            "passed": 0,
            "failed": 0,
            "errored": 1,
            "results": [
                {
                    "kind": "error",
                    "name": "errors",
                    "phase": "evaluation",
                    "reason": "boom",
                    "expected": None,
                    "actual": None,
                    "stdout": "",
                    "stderr": "",
                    "diagnostics": {},
                }
            ],
        }
    )

    assert report == (
        "total=1 passed=0 failed=0 errored=1\n"
        "ERROR errors phase=evaluation reason=boom\n"
        "total=1 passed=0 failed=0 errored=1\n"
    )


def test_formats_discovery_error_empty_name_as_unnamed():
    report = _format_report(
        {
            "total": 1,
            "passed": 0,
            "failed": 0,
            "errored": 1,
            "results": [
                {
                    "kind": "error",
                    "name": "",
                    "phase": "discovery",
                    "reason": "test unit name must be a non-empty string",
                    "expected": None,
                    "actual": None,
                    "stdout": "",
                    "stderr": "",
                    "diagnostics": {},
                }
            ],
        }
    )

    assert report == (
        "total=1 passed=0 failed=0 errored=1\n"
        "ERROR <unnamed> phase=discovery reason=test unit name must be a non-empty string\n"
        "total=1 passed=0 failed=0 errored=1\n"
    )


def test_formats_empty_suite_with_duplicate_zero_summary_and_one_final_newline():
    report = _format_report(
        {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errored": 0,
            "results": [],
        }
    )

    assert report == (
        "total=0 passed=0 failed=0 errored=0\n"
        "total=0 passed=0 failed=0 errored=0\n"
    )
    assert report.endswith("\n")
    assert not report.endswith("\n\n")


def test_formatter_rejects_unknown_result_kind():
    with pytest.raises(ValueError, match="unknown test result kind: skip"):
        _format_report(
            {
                "total": 1,
                "passed": 0,
                "failed": 0,
                "errored": 0,
                "results": [
                    {
                        "kind": "skip",
                        "name": "future",
                        "phase": "evaluation",
                        "reason": None,
                        "expected": None,
                        "actual": None,
                        "stdout": "",
                        "stderr": "",
                        "diagnostics": {},
                    }
                ],
            }
        )
