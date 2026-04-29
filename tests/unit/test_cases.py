from pathlib import Path
import pytest
from genia import make_global_env, run_source

CASES = Path(__file__).parent.parent / "cases"
CASE_FILES = sorted(CASES.rglob("*.genia"))


def test_cases_directory_exists_and_contains_genia_files():
    assert CASES.exists(), f"CASES path does not exist: {CASES}"
    assert CASES.is_dir(), f"CASES path is not a directory: {CASES}"
    assert CASE_FILES, f"No .genia case files found under CASES path: {CASES}"


@pytest.mark.parametrize(
    "case",
    CASE_FILES,
    ids=lambda p: str(p.relative_to(CASES).with_suffix("")),
)
def test_cases(case):
    env = make_global_env([])
    src = case.read_text(encoding="utf-8")

    out_file = case.with_suffix(".out")
    err_file = case.with_suffix(".err")

    try:
        result = run_source(src, env, filename=str(case.relative_to(CASES)))

        if err_file.exists():
            pytest.fail(f"{case.name}: expected error but got result {result!r}")

        if out_file.exists():
            expected = out_file.read_text(encoding="utf-8").strip()
            assert str(result).strip() == expected
        else:
            pytest.fail(f"{case.name}: missing expected .out or .err file")

    except Exception as e:
        if not err_file.exists():
            raise
        expected_error = err_file.read_text(encoding="utf-8").strip()
        assert expected_error in str(e), f"{case.name}: expected {expected_error!r} in {str(e)!r}"
