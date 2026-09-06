from pathlib import Path

from genia.native_test_runner import run_native_tests
from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import load_spec

REPO = Path(__file__).resolve().parents[2]
CLI_SPEC = REPO / "spec/cli/r15-composed-messy-record-proving-case.yaml"
EXAMPLE = REPO / "examples/r15_composed_messy_record_proving_case.genia"
NATIVE_FIXTURE = REPO / "tests/native/r15_composed_messy_record_proving_case.genia"


def test_r15_proving_case_fixtures_exist():
    assert EXAMPLE.is_file()
    assert CLI_SPEC.is_file()
    assert NATIVE_FIXTURE.is_file()


def test_r15_proving_case_file_mode_matches_portable_contract():
    spec = load_spec(CLI_SPEC)

    failures = compare_spec(spec, execute_spec(spec))

    assert failures == []


def test_r15_proving_case_native_fixture_passes(capsys):
    exit_code = run_native_tests(str(NATIVE_FIXTURE))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "[PASS] R15 composed order proving case validates, defaults, diagnoses, "
        "schemas, and bounds recursion\n"
        "Summary: total=1 passed=1 failed=0 errors=0\n"
    )
    assert captured.err == ""
