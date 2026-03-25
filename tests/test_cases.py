from pathlib import Path
import pytest
from genia import make_global_env, run_source

CASES = Path(__file__).parent / "cases"

@pytest.mark.parametrize("case", CASES.glob("*.genia"))
def test_cases(case):
    env = make_global_env([])
    src = case.read_text()
    out_file = case.with_suffix(".out")
    err_file = case.with_suffix(".err")

    try:
        result = run_source(src, env)
        if err_file.exists():
            pytest.fail("Expected error but got result")
        if out_file.exists():
            assert str(result).strip() == out_file.read_text().strip()
    except Exception as e:
        if not err_file.exists():
            raise
        assert err_file.read_text().strip() in str(e)