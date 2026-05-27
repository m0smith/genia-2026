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
