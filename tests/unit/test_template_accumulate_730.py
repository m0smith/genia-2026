"""Focused invariants for E15-3 (#730) accumulate that shared eval specs can't express."""

from genia import make_global_env, run_source
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome


def _run(source: str):
    return run_source(source, make_global_env([]), filename="<test>")


def test_accumulate_over_flow_pulls_only_demanded_elements():
    # The third source element ("boom") would raise a Python TypeError if
    # its refinement predicate ever ran (`"boom" > 0`). Bounding consumption
    # to the first element with `take(1)` must never reach it.
    result = _run(
        "Positive = refinement((x) -> x > 0)\n"
        "[1, -1, \"boom\"] |> as_seq |> map(accumulate(Positive)) |> take(1) |> collect"
    )
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], GeniaOptionSome)
    assert result[0].value == 1


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
