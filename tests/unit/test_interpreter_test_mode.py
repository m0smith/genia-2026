import pytest

from genia.interpreter import _main


def test_test_mode_runs_passing_test_file(tmp_path, capsys):
    program = tmp_path / "passing_test.genia"
    program.write_text('test("passes", () -> none)\n', encoding="utf-8")

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=1 passed=1 failed=0 errored=0\n"
        "PASS passes\n"
        "total=1 passed=1 failed=0 errored=0\n"
    )
    assert captured.err == ""


def test_test_mode_runs_passing_assertion_helpers(tmp_path, capsys):
    program = tmp_path / "passing_assertions.genia"
    program.write_text(
        "\n".join(
            [
                'test("assert true passes", () -> assert_true(true))',
                'test("assert eq passes", () -> assert_eq(2 + 2, 4))',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=2 passed=2 failed=0 errored=0\n"
        "PASS assert true passes\n"
        "PASS assert eq passes\n"
        "total=2 passed=2 failed=0 errored=0\n"
    )
    assert captured.err == ""


def test_test_mode_reports_failing_assertions_as_failures_and_continues(tmp_path, capsys):
    program = tmp_path / "failing_assertions.genia"
    program.write_text(
        "\n".join(
            [
                'test("assert eq fails", () -> assert_eq(2 + 2, 5))',
                'test("assert true fails", () -> assert_true(false))',
                'test("still runs", () -> none)',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert exit_code == 1
    assert lines[0] == "total=3 passed=1 failed=2 errored=0"
    assert lines[-1] == "total=3 passed=1 failed=2 errored=0"
    assert lines[1].startswith(
        "FAIL assert eq fails phase=evaluation reason=assert_eq failed"
    )
    assert "expected=5" in lines[1]
    assert "actual=4" in lines[1]
    assert lines[2] == "FAIL assert true fails phase=evaluation reason=assert_true failed"
    assert lines[3] == "PASS still runs"
    assert captured.err == ""


def test_test_mode_keeps_assertion_helper_arity_as_runtime_error(tmp_path, capsys):
    program = tmp_path / "bad_assertion_arity.genia"
    program.write_text('test("bad arity", () -> assert_true())\n', encoding="utf-8")

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "total=1 passed=0 failed=0 errored=1\n" in captured.out
    assert "ERROR bad arity phase=evaluation reason=" in captured.out
    assert "FAIL bad arity" not in captured.out
    assert captured.err == ""


def test_test_mode_reports_discovery_error_for_non_callable_body(tmp_path, capsys):
    program = tmp_path / "bad_test.genia"
    program.write_text('test("bad", "not callable")\n', encoding="utf-8")

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ERROR bad phase=discovery reason=test unit body must be callable\n" in captured.out
    assert captured.err == ""


def test_test_mode_discovers_annotated_zero_arg_function(tmp_path, capsys):
    program = tmp_path / "annotated_passing_test.genia"
    program.write_text(
        '@test "passes through annotation discovery"\n'
        "passes() = assert_true(true)\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=1 passed=1 failed=0 errored=0\n"
        "PASS passes\n"
        "total=1 passed=1 failed=0 errored=0\n"
    )
    assert captured.err == ""


def test_test_mode_reports_annotated_assertion_failure_as_failure(tmp_path, capsys):
    program = tmp_path / "annotated_failing_test.genia"
    program.write_text(
        '@test "assertion failures stay failures"\n'
        "fails() = assert_eq(1, 2)\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "total=1 passed=0 failed=1 errored=0\n" in captured.out
    assert "FAIL fails phase=evaluation reason=assert_eq failed" in captured.out
    assert "ERROR fails" not in captured.out
    assert captured.err == ""


def test_test_mode_reports_annotated_runtime_error_as_error(tmp_path, capsys):
    program = tmp_path / "annotated_erroring_test.genia"
    program.write_text(
        '@test "runtime errors stay errors"\n'
        "errors() = missing_name\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "total=1 passed=0 failed=0 errored=1\n" in captured.out
    assert "ERROR errors phase=evaluation reason=Undefined name: missing_name" in captured.out
    assert "FAIL errors" not in captured.out
    assert captured.err == ""


def test_test_mode_runs_legacy_and_annotated_tests_in_deterministic_order(
    tmp_path,
    capsys,
):
    program = tmp_path / "mixed_native_tests.genia"
    program.write_text(
        'test("legacy registration", () -> assert_true(true))\n'
        '@test "annotation registration"\n'
        "annotated() = assert_eq(2 + 2, 4)\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=2 passed=2 failed=0 errored=0\n"
        "PASS legacy registration\n"
        "PASS annotated\n"
        "total=2 passed=2 failed=0 errored=0\n"
    )
    assert captured.err == ""


def test_test_mode_reports_duplicate_legacy_and_annotated_names_as_discovery_error(
    tmp_path,
    capsys,
):
    program = tmp_path / "duplicate_native_test_names.genia"
    program.write_text(
        'test("duplicate", () -> assert_true(true))\n'
        '@test "duplicate native test name"\n'
        "duplicate() = assert_true(true)\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "total=1 passed=0 failed=0 errored=1\n" in captured.out
    assert (
        "ERROR duplicate phase=discovery reason=duplicate native test name: duplicate"
        in captured.out
    )
    assert "PASS duplicate" not in captured.out
    assert captured.err == ""


def test_test_mode_reports_annotated_parameterized_function_as_discovery_error(
    tmp_path,
    capsys,
):
    program = tmp_path / "annotated_parameterized_test.genia"
    program.write_text(
        '@test "parameterized tests are unsupported"\n'
        "with_param(x) = assert_true(x)\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "total=1 passed=0 failed=0 errored=1\n" in captured.out
    assert (
        "ERROR with_param phase=discovery reason=@test functions must take zero arguments"
        in captured.out
    )
    assert captured.err == ""


def test_test_mode_reports_annotated_non_function_as_discovery_error(tmp_path, capsys):
    program = tmp_path / "annotated_non_function_test.genia"
    program.write_text(
        '@test "assignments are not native tests"\n'
        "not_a_function = 42\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "total=1 passed=0 failed=0 errored=1\n" in captured.out
    assert "ERROR not_a_function phase=discovery reason=@test must annotate a function" in captured.out
    assert captured.err == ""


def test_test_mode_does_not_treat_unannotated_setup_as_lifecycle_hook(
    tmp_path,
    capsys,
):
    program = tmp_path / "no_lifecycle_hooks.genia"
    program.write_text(
        "setup() = missing_name\n"
        '@test "ordinary annotated test still passes"\n'
        "passes() = assert_true(true)\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=1 passed=1 failed=0 errored=0\n"
        "PASS passes\n"
        "total=1 passed=1 failed=0 errored=0\n"
    )
    assert "setup" not in captured.out
    assert captured.err == ""


def test_test_mode_rejects_setup_annotation_instead_of_running_lifecycle_hook(
    tmp_path,
    capsys,
):
    program = tmp_path / "setup_annotation_is_not_lifecycle.genia"
    program.write_text(
        '@setup "not supported as lifecycle behavior"\n'
        "setup() = missing_name\n"
        '@test "ordinary test is not reached through lifecycle setup"\n'
        "passes() = assert_true(true)\n",
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Unsupported annotation: @setup" in captured.err
    assert "PASS passes" not in captured.out


def test_test_mode_preserves_doc_metadata_on_annotated_native_test(
    tmp_path,
    capsys,
):
    program = tmp_path / "annotated_test_doc_metadata.genia"
    program.write_text(
        '@doc "Native-test doc metadata remains available."\n'
        '@test "native test marker"\n'
        'documented() = assert_eq(doc("documented"), "Native-test doc metadata remains available.")\n',
        encoding="utf-8",
    )

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=1 passed=1 failed=0 errored=0\n"
        "PASS documented\n"
        "total=1 passed=1 failed=0 errored=0\n"
    )
    assert captured.err == ""


def test_test_mode_runs_empty_suite_successfully(tmp_path, capsys):
    program = tmp_path / "empty_test.genia"
    program.write_text("none\n", encoding="utf-8")

    exit_code = _main(["--test", str(program)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "total=0 passed=0 failed=0 errored=0\n"
        "total=0 passed=0 failed=0 errored=0\n"
    )
    assert captured.err == ""


def test_test_mode_reports_missing_program_path_as_invalid_invocation(capsys):
    with pytest.raises(SystemExit) as exc_info:
        _main(["--test", "missing.genia"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "error:" in captured.err
    assert "--test program path not found: missing.genia" in captured.err


def test_test_mode_rejects_debug_stdio_combination(tmp_path, capsys):
    program = tmp_path / "program.genia"
    program.write_text("none\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        _main(["--debug-stdio", "--test", str(program)])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "error:" in captured.err
    assert "--debug-stdio cannot be used with --test" in captured.err


def test_test_mode_rejects_extra_trailing_args(tmp_path, capsys):
    program = tmp_path / "program.genia"
    program.write_text("none\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        _main(["--test", str(program), "extra_arg"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "error:" in captured.err
    assert "--test accepts exactly one program path" in captured.err
