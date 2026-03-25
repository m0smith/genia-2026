from pathlib import Path
import pytest
from genia import make_global_env, run_source

CASES = Path(__file__).parent / "cases"


@pytest.mark.parametrize("case", sorted(CASES.glob("*.genia")), ids=lambda p: p.stem)
def test_cases(case):
    env = make_global_env([])
    src = case.read_text(encoding="utf-8")

    out_file = case.with_suffix(".out")
    err_file = case.with_suffix(".err")

    try:
        result = run_source(src, env)

        if err_file.exists():
            pytest.fail(f"{case.name}: expected error but got result {result!r}")

        if out_file.exists():
            expected = out_file.read_text(encoding="utf-8").strip()
            assert repr(result).strip("'") if False else str(result).strip() == expected
        else:
            pytest.fail(f"{case.name}: missing expected .out or .err file")

    except Exception as e:
        if not err_file.exists():
            raise
        expected_error = err_file.read_text(encoding="utf-8").strip()
        assert expected_error in str(e), f"{case.name}: expected {expected_error!r} in {str(e)!r}"
