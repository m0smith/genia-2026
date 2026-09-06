"""Focused invariants for E15-4 (#731) template_schema that shared eval specs can't express."""

from genia import make_global_env, run_source
from genia.values import GeniaOptionErr


def _run(source: str):
    return run_source(source, make_global_env([]), filename="<test>")


def test_protected_default_never_appears_in_unsupported_failure():
    result = _run(
        "Config = open_shape({token: default_field(represent(\"json\", {value: \"do-not-leak\"}), refinement((x) -> true))})\n"
        "template_schema(Config)"
    )
    assert isinstance(result, GeniaOptionErr)
    assert "do-not-leak" not in repr(result)
    assert result.context.get("path") == ["token"]


def test_unsupported_failure_never_invokes_the_template():
    # A refinement predicate that would raise if ever called; template_schema
    # must never execute it (pure inspection only).
    result = _run(
        "Person = exact_shape({name: refinement((x) -> 1 / 0 > 0)})\n"
        "template_schema(Person)"
    )
    assert isinstance(result, GeniaOptionErr)
    assert result.context.get("path") == ["name"]
    assert result.context.get("kind").name == "refinement"
