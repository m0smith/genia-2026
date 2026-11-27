"""Python reference-host regression coverage for pipeline exception identity."""

import pytest

from genia import make_global_env, run_source


@pytest.mark.parametrize(
    "stage, diagnostic",
    [
        ('column("missing")', "column could not find column"),
        ("sort_rows(0)", "sort_rows expected a function"),
        ('inner_join("id", "missing", sheet([["id", [1]]]))',
         "inner_join could not find right key column"),
    ],
)
def test_marked_sheet_error_is_not_its_own_cause(stage, diagnostic):
    with pytest.raises(TypeError) as failure:
        run_source(f'sheet([["id", [1]]]) |> {stage}', make_global_env([]))

    assert str(failure.value) == diagnostic
    assert failure.value.__cause__ is None


def test_already_wrapped_pipeline_error_keeps_its_existing_chain():
    env = make_global_env([])
    original = TypeError("original")
    wrapped = TypeError("pipeline stage 1 failed in Value mode at stage")
    wrapped.__cause__ = original

    def fail(value):
        """Raise the original wrapper with its established cause."""
        raise wrapped

    env.set_host("fail_fixture", fail, visibility="entry-only")
    with pytest.raises(TypeError) as failure:
        run_source("1 |> fail_fixture", env)

    assert failure.value is wrapped
    assert failure.value.__cause__ is original


def test_ordinary_error_still_gets_a_chained_wrapper():
    env = make_global_env([])
    original = TypeError("ordinary error")

    def fail(value):
        """Raise an ordinary error so the evaluator supplies its wrapper."""
        raise original

    env.set_host("fail_fixture", fail, visibility="entry-only")
    with pytest.raises(TypeError, match=r"^pipeline stage 1 failed .*ordinary error$") as failure:
        run_source("1 |> fail_fixture", env)

    assert failure.value is not original
    assert failure.value.__cause__ is original
