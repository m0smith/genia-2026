from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from genia.native_test_runner import run_native_tests


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_kernel():
    """Mock native test kernel with identify_tests and run_tests."""
    kernel = Mock()
    kernel.identify_tests.return_value = []
    kernel.run_tests.return_value = SimpleNamespace(
        total=0,
        passed=0,
        failed=0,
        errors=0,
        outcomes=[],
    )
    return kernel


@pytest.fixture
def temp_genia_file(tmp_path):
    """Create a temporary .genia file path."""
    return tmp_path / "test.genia"


@pytest.fixture
def valid_passing_test_file(temp_genia_file):
    """File with one passing native test registration."""
    temp_genia_file.write_text('test("passes", () -> none)\n', encoding="utf-8")
    return temp_genia_file


@pytest.fixture
def no_tests_file(temp_genia_file):
    """File that parses but discovers no native tests."""
    temp_genia_file.write_text("x = 42\n", encoding="utf-8")
    return temp_genia_file


@pytest.fixture
def syntax_error_file(temp_genia_file):
    """File with invalid Genia syntax."""
    temp_genia_file.write_text("x = \n", encoding="utf-8")
    return temp_genia_file


def _test_unit(name):
    """Create a minimal mock test unit."""
    return SimpleNamespace(name=name)


def _outcome(name, status):
    """Create a minimal mock test outcome."""
    return SimpleNamespace(name=name, status=status)


def _summary(*outcomes):
    """Create a mock native test summary from outcomes."""
    return SimpleNamespace(
        total=len(outcomes),
        passed=sum(item.status == "PASS" for item in outcomes),
        failed=sum(item.status == "FAIL" for item in outcomes),
        errors=sum(item.status == "ERROR" for item in outcomes),
        outcomes=list(outcomes),
    )


def run_with_kernel(file_path: Path, mock_kernel):
    """Run the native test runner with a patched native test kernel."""
    with patch("genia.native_test_runner.native_test_kernel", mock_kernel):
        return run_native_tests(str(file_path))


# ============================================================================
# TEST CLASSES
# ============================================================================


class TestNativeTestRunnerFileHandling:
    """Test file I/O and error handling."""

    def test_file_not_found(self, tmp_path, capsys):
        """Missing file returns exit code 2 and a clear stderr message."""
        missing_file = tmp_path / "missing.genia"

        exit_code = run_native_tests(str(missing_file))

        captured = capsys.readouterr()
        assert exit_code == 2, "missing files should return usage/data error code 2"
        assert "file not found" in captured.err.lower()
        assert captured.out == ""

    def test_file_not_readable(self, temp_genia_file, capsys):
        """Unreadable files return exit code 2 and do not write stdout."""
        temp_genia_file.write_text('test("passes", () -> none)\n', encoding="utf-8")
        temp_genia_file.chmod(0)

        try:
            exit_code = run_native_tests(str(temp_genia_file))
        finally:
            temp_genia_file.chmod(0o600)

        captured = capsys.readouterr()
        assert exit_code == 2, "unreadable files should return usage/data error code 2"
        assert "not readable" in captured.err.lower()
        assert captured.out == ""

    def test_file_empty(self, temp_genia_file, mock_kernel, capsys):
        """Empty files parse but discover no tests, so the runner returns 2."""
        temp_genia_file.write_text("", encoding="utf-8")
        mock_kernel.identify_tests.return_value = []

        exit_code = run_with_kernel(temp_genia_file, mock_kernel)

        captured = capsys.readouterr()
        assert exit_code == 2, "empty files should be treated as no-tests errors"
        assert captured.out == "Summary: total=0 passed=0 failed=0 errors=0\n"
        assert captured.err == ""
        mock_kernel.run_tests.assert_not_called()


class TestNativeTestRunnerParsing:
    """Test parsing and parse-related error reporting."""

    def test_parse_error(self, syntax_error_file, capsys):
        """Syntax errors return exit code 2 with parse-error stderr."""
        exit_code = run_native_tests(str(syntax_error_file))

        captured = capsys.readouterr()
        assert exit_code == 2, "parse errors should return usage/data error code 2"
        assert captured.err.startswith("Parse error:")
        assert captured.out == ""

    def test_valid_parse_no_tests(self, no_tests_file, mock_kernel, capsys):
        """A valid file with no discovered tests returns exit code 2."""
        mock_kernel.identify_tests.return_value = []

        exit_code = run_with_kernel(no_tests_file, mock_kernel)

        captured = capsys.readouterr()
        assert exit_code == 2, "valid files with no tests should return code 2"
        assert captured.out == "Summary: total=0 passed=0 failed=0 errors=0\n"
        assert captured.err == ""
        mock_kernel.run_tests.assert_not_called()

    def test_valid_file_invokes_kernel_for_discovered_tests(
        self,
        valid_passing_test_file,
        mock_kernel,
        capsys,
    ):
        """A valid file delegates discovered tests to the native test kernel."""
        tests = [_test_unit("passes")]
        mock_kernel.identify_tests.return_value = tests
        mock_kernel.run_tests.return_value = _summary(_outcome("passes", "PASS"))

        exit_code = run_with_kernel(valid_passing_test_file, mock_kernel)

        captured = capsys.readouterr()
        assert exit_code == 0
        mock_kernel.identify_tests.assert_called_once()
        mock_kernel.run_tests.assert_called_once_with(tests)
        assert captured.err == ""


class TestNativeTestRunnerExecution:
    """Test execution and result reporting."""

    def test_all_tests_pass(self, valid_passing_test_file, mock_kernel, capsys):
        """All passing tests print PASS lines and return exit code 0."""
        mock_kernel.identify_tests.return_value = [_test_unit("test_passes")]
        mock_kernel.run_tests.return_value = _summary(_outcome("test_passes", "PASS"))

        exit_code = run_with_kernel(valid_passing_test_file, mock_kernel)

        captured = capsys.readouterr()
        assert exit_code == 0
        assert captured.out == (
            "[PASS] test_passes\n"
            "Summary: total=1 passed=1 failed=0 errors=0\n"
        )
        assert captured.err == ""

    def test_one_test_fails(self, valid_passing_test_file, mock_kernel, capsys):
        """Any failing test prints FAIL and returns exit code 1."""
        mock_kernel.identify_tests.return_value = [_test_unit("test_fails")]
        mock_kernel.run_tests.return_value = _summary(_outcome("test_fails", "FAIL"))

        exit_code = run_with_kernel(valid_passing_test_file, mock_kernel)

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "[FAIL] test_fails\n" in captured.out
        assert "Summary: total=1 passed=0 failed=1 errors=0\n" in captured.out
        assert captured.err == ""

    def test_one_test_errors(self, valid_passing_test_file, mock_kernel, capsys):
        """Any erroring test prints ERROR and returns exit code 1."""
        mock_kernel.identify_tests.return_value = [_test_unit("test_errors")]
        mock_kernel.run_tests.return_value = _summary(_outcome("test_errors", "ERROR"))

        exit_code = run_with_kernel(valid_passing_test_file, mock_kernel)

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "[ERROR] test_errors\n" in captured.out
        assert "Summary: total=1 passed=0 failed=0 errors=1\n" in captured.out
        assert captured.err == ""

    def test_mixed_results(self, valid_passing_test_file, mock_kernel, capsys):
        """Mixed pass, fail, and error results report counts and return 1."""
        mock_kernel.identify_tests.return_value = [
            _test_unit("test_passes"),
            _test_unit("test_fails"),
            _test_unit("test_errors"),
        ]
        mock_kernel.run_tests.return_value = _summary(
            _outcome("test_passes", "PASS"),
            _outcome("test_fails", "FAIL"),
            _outcome("test_errors", "ERROR"),
        )

        exit_code = run_with_kernel(valid_passing_test_file, mock_kernel)

        captured = capsys.readouterr()
        assert exit_code == 1
        assert captured.out == (
            "[PASS] test_passes\n"
            "[FAIL] test_fails\n"
            "[ERROR] test_errors\n"
            "Summary: total=3 passed=1 failed=1 errors=1\n"
        )
        assert captured.err == ""


class TestNativeTestRunnerFormatting:
    """Test output formatting."""

    @pytest.mark.parametrize(
        ("status", "expected_line"),
        [
            ("PASS", "[PASS] test_name"),
            ("FAIL", "[FAIL] test_name"),
            ("ERROR", "[ERROR] test_name"),
        ],
    )
    def test_output_line_format(
        self,
        valid_passing_test_file,
        mock_kernel,
        capsys,
        status,
        expected_line,
    ):
        """Each test result is formatted as '[STATUS] name' on one line."""
        mock_kernel.identify_tests.return_value = [_test_unit("test_name")]
        mock_kernel.run_tests.return_value = _summary(_outcome("test_name", status))

        run_with_kernel(valid_passing_test_file, mock_kernel)

        captured = capsys.readouterr()
        assert captured.out.splitlines()[0] == expected_line

    def test_summary_format(self, valid_passing_test_file, mock_kernel, capsys):
        """The summary line matches the exact contracted format."""
        mock_kernel.identify_tests.return_value = [
            _test_unit("test_one"),
            _test_unit("test_two"),
        ]
        mock_kernel.run_tests.return_value = _summary(
            _outcome("test_one", "PASS"),
            _outcome("test_two", "FAIL"),
        )

        run_with_kernel(valid_passing_test_file, mock_kernel)

        captured = capsys.readouterr()
        assert captured.out.splitlines()[-1] == (
            "Summary: total=2 passed=1 failed=1 errors=0"
        )

    def test_output_order(self, valid_passing_test_file, mock_kernel, capsys):
        """Test results are printed in the source/kernel outcome order."""
        mock_kernel.identify_tests.return_value = [
            _test_unit("test_first"),
            _test_unit("test_second"),
            _test_unit("test_third"),
        ]
        mock_kernel.run_tests.return_value = _summary(
            _outcome("test_first", "PASS"),
            _outcome("test_second", "FAIL"),
            _outcome("test_third", "ERROR"),
        )

        run_with_kernel(valid_passing_test_file, mock_kernel)

        captured = capsys.readouterr()
        assert captured.out.splitlines()[:3] == [
            "[PASS] test_first",
            "[FAIL] test_second",
            "[ERROR] test_third",
        ]


class TestNativeTestRunnerExitCodes:
    """Test exit code mapping for the native test runner contract."""

    @pytest.mark.parametrize(
        ("suite", "expected_exit_code"),
        [
            (_summary(_outcome("test_passes", "PASS")), 0),
            (_summary(_outcome("test_fails", "FAIL")), 1),
            (_summary(_outcome("test_errors", "ERROR")), 1),
            (
                _summary(
                    _outcome("test_passes", "PASS"),
                    _outcome("test_fails", "FAIL"),
                    _outcome("test_errors", "ERROR"),
                ),
                1,
            ),
        ],
    )
    def test_exit_code_from_execution_summary(
        self,
        valid_passing_test_file,
        mock_kernel,
        suite,
        expected_exit_code,
    ):
        """Execution summaries map cleanly to exit code 0 or 1."""
        mock_kernel.identify_tests.return_value = [_test_unit("test_name")]
        mock_kernel.run_tests.return_value = suite

        exit_code = run_with_kernel(valid_passing_test_file, mock_kernel)

        assert exit_code == expected_exit_code

    def test_exit_0_all_pass(self, valid_passing_test_file, mock_kernel):
        """Exit code 0 when all tests pass."""
        mock_kernel.identify_tests.return_value = [_test_unit("test_passes")]
        mock_kernel.run_tests.return_value = _summary(_outcome("test_passes", "PASS"))

        assert run_with_kernel(valid_passing_test_file, mock_kernel) == 0

    def test_exit_1_any_fail(self, valid_passing_test_file, mock_kernel):
        """Exit code 1 when any test fails."""
        mock_kernel.identify_tests.return_value = [_test_unit("test_fails")]
        mock_kernel.run_tests.return_value = _summary(_outcome("test_fails", "FAIL"))

        assert run_with_kernel(valid_passing_test_file, mock_kernel) == 1

    def test_exit_1_any_error(self, valid_passing_test_file, mock_kernel):
        """Exit code 1 when any test errors."""
        mock_kernel.identify_tests.return_value = [_test_unit("test_errors")]
        mock_kernel.run_tests.return_value = _summary(_outcome("test_errors", "ERROR"))

        assert run_with_kernel(valid_passing_test_file, mock_kernel) == 1

    def test_exit_2_file_not_found(self, tmp_path):
        """Exit code 2 when the file is missing."""
        assert run_native_tests(str(tmp_path / "missing.genia")) == 2

    def test_exit_2_file_not_readable(self, temp_genia_file):
        """Exit code 2 when the file exists but is unreadable."""
        temp_genia_file.write_text('test("passes", () -> none)\n', encoding="utf-8")
        temp_genia_file.chmod(0)

        try:
            exit_code = run_native_tests(str(temp_genia_file))
        finally:
            temp_genia_file.chmod(0o600)

        assert exit_code == 2

    def test_exit_2_parse_error(self, syntax_error_file):
        """Exit code 2 when parsing fails."""
        assert run_native_tests(str(syntax_error_file)) == 2

    def test_exit_2_no_tests(self, no_tests_file, mock_kernel):
        """Exit code 2 when no tests are discovered."""
        mock_kernel.identify_tests.return_value = []

        assert run_with_kernel(no_tests_file, mock_kernel) == 2
