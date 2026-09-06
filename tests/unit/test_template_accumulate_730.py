"""Focused invariants for E15-3 (#730) accumulate that shared eval specs can't express."""

from genia import make_global_env, run_source
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome


def _run(source: str):
    return run_source(source, make_global_env([]), filename="<test>")


def test_accumulate_over_flow_pulls_only_demanded_elements():
    # naturals is an unbounded lazy Flow. If accumulate (composed inside an
    # ordinary map stage) ever forced whole-source buffering or over-pulled,
    # this would hang instead of terminating with exactly 2 items.
    result = _run(
        "Positive = refinement((x) -> x > 0)\n"
        "naturals = evolve(1, (n) -> n + 1)\n"
        "naturals |> map((x) -> accumulate(Positive, x)) |> take(2) |> collect"
    )
    assert isinstance(result, list)
    assert len(result) == 2
    assert [outcome.value for outcome in result] == [1, 2]


def test_protected_value_never_appears_in_diagnostic_reason_or_path():
    result = _run(
        "Person = exact_shape({secret: refinement((x) -> false)})\n"
        "accumulate(Person, {secret: represent(\"json\", {token: \"do-not-leak\"})})"
    )
    assert isinstance(result, GeniaOptionErr)
    diagnostics = result.context.get("diagnostics")
    assert isinstance(diagnostics, list)
    for diagnostic in diagnostics:
        assert isinstance(diagnostic, GeniaMap)
        rendered = repr(diagnostic)
        assert "do-not-leak" not in rendered
        assert "token" not in rendered


def test_accumulate_success_delegates_to_real_template_for_defaults():
    result = _run(
        "Config = open_shape({host: default_field(\"localhost\", refinement((x) -> x != \"\")), port: refinement((x) -> x > 0)})\n"
        "accumulate(Config, {port: 9000})"
    )
    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("host") == "localhost"
    assert result.value.get("port") == 9000
