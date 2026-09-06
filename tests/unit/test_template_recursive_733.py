"""Focused invariants for E15-6 (#733) recursive_template that shared eval specs can't express."""

from genia import make_global_env, run_source
from genia.values import GeniaOptionSome


def _run(source: str):
    return run_source(source, make_global_env([]), filename="<test>")


def test_independent_instances_do_not_share_depth_state():
    # Inner is nested as an ordinary field inside Outer's own structure (not
    # a self-reference of Outer). Outer's own recursion must not be
    # perturbed by Inner's independent depth counter, and vice versa.
    result = _run(
        "Inner = recursive_template(\"inner\", (ref) -> alternatives(\"kind\", "
        "{leaf: exact_shape({kind: refinement((x) -> x == \"leaf\")}), "
        "node: exact_shape({kind: refinement((x) -> x == \"node\"), next: ref(\"inner\")})}), 2)\n"
        "Outer = recursive_template(\"outer\", (ref) -> exact_shape({kind: refinement((x) -> x == \"wrap\"), inner: Inner, next: ref(\"outer\")}), 2)\n"
        "value = {kind: \"wrap\", inner: {kind: \"node\", next: {kind: \"leaf\"}}, next: {kind: \"wrap\", inner: {kind: \"leaf\"}, next: {kind: \"wrap\", inner: {kind: \"leaf\"}, next: {}}}}\n"
        "Outer(value)"
    )
    # Outer recurses 2 levels deep (within its own bound 2); the third
    # nested "wrap" exceeds Outer's bound, so this must fail there, not
    # because Inner's independent 1-level-deep validation ever interfered.
    from genia.values import GeniaOptionErr

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "recursive-template-depth-exceeded"


def test_recursion_bound_never_raises_a_python_recursion_error():
    # A tree deep enough that an unbounded implementation relying on Python's
    # own call stack would risk RecursionError; our explicit bound must
    # produce an ordinary Outcome instead.
    result = _run(
        "Tree = recursive_template(\"tree\", (ref) -> alternatives(\"kind\", "
        "{leaf: exact_shape({kind: refinement((x) -> x == \"leaf\")}), "
        "node: exact_shape({kind: refinement((x) -> x == \"node\"), left: ref(\"tree\")})}), 10)\n"
        "build(n) =\n"
        "  0 -> {kind: \"leaf\"} |\n"
        "  _ -> {kind: \"node\", left: build(n - 1)}\n"
        "Tree(build(50))"
    )
    from genia.values import GeniaOptionErr

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "recursive-template-depth-exceeded"
