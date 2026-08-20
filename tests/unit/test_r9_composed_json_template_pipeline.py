from pathlib import Path

from genia.native_test_runner import run_native_tests
from tools.spec_runner.comparator import compare_spec
from tools.spec_runner.executor import execute_spec
from tools.spec_runner.loader import load_spec

REPO = Path(__file__).resolve().parents[2]
CLI_SPEC = REPO / "spec/cli/r9-composed-json-template-pipeline.yaml"
NATIVE_FIXTURE = REPO / "tests/native/r9_composed_json_template_pipeline.genia"


def test_r9_composed_json_template_file_mode_matches_portable_contract():
    spec = load_spec(CLI_SPEC)

    failures = compare_spec(spec, execute_spec(spec))

    assert failures == []


def test_r9_composed_json_template_native_fixture_passes(capsys):
    exit_code = run_native_tests(str(NATIVE_FIXTURE))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "[PASS] composed JSON Template pipeline keeps clean records and diagnostics\n"
        "Summary: total=1 passed=1 failed=0 errors=0\n"
    )
    assert captured.err == ""
