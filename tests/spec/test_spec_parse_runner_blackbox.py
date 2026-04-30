import pytest
from pathlib import Path
from tools.spec_runner.parse_loader import load_parse_spec
from tools.spec_runner.parse_executor import execute_parse_spec
from tools.spec_runner.parse_comparator import compare_parse_spec

PARSE_DIR = Path(__file__).resolve().parents[2] / "tests" / "data" / "parse_specs"

@pytest.mark.parametrize("fname", [
    "literal-number.yaml",
    "assignment-simple.yaml",
    "fn-def-basic.yaml",
    "invalid-unclosed-paren.yaml",
    "invalid-case-placement.yaml",
])
@pytest.mark.spec
@pytest.mark.slow
def test_parse_spec_fixture(fname):
    spec = load_parse_spec(PARSE_DIR / fname)
    actual = execute_parse_spec(spec.source)
    failures = compare_parse_spec(spec, actual)
    assert not failures, f"Failures: {failures}"
