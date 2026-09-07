"""Focused invariants for E15-6 (#733) recursive_template that shared eval specs can't express."""

import genia.interpreter as interpreter_module
from genia import make_global_env, run_source
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome


def _run(source: str):
    return run_source(source, make_global_env([]), filename="<test>")


def _build_chain(depth):
    value = GeniaMap().put("kind", "leaf")
    for _ in range(depth):
        value = GeniaMap().put("kind", "node").put("left", value)
    return value


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
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "recursive-template-depth-exceeded"


def test_recursion_bound_holds_at_the_documented_ceiling_far_beyond_python_stack_limits():
    # E15-8 (#735) hardening found that the original implementation recursed
    # through Python's own call stack once per logical level, so it raised a
    # genuine RecursionError around logical depth ~75-80 -- well under the
    # documented "at most 100" ceiling, in direct contradiction of this
    # contract's own guarantee. The value below is built entirely in Python
    # (never through an ordinary recursive Genia function, which hits its own
    # unrelated Python-stack ceiling far earlier) so this test isolates
    # recursive_template's own bound from that unrelated limitation, and
    # pushes to a depth (10000) far beyond Python's default recursion limit
    # (1000) to prove the bound is now independent of Python's call stack.
    env = make_global_env([])
    env.set("chain_10000", _build_chain(10000))
    result = interpreter_module.run_source(
        "Tree = recursive_template(\"tree\", (ref) -> alternatives(\"kind\", "
        "{leaf: exact_shape({kind: refinement((x) -> x == \"leaf\")}), "
        "node: exact_shape({kind: refinement((x) -> x == \"node\"), left: ref(\"tree\")})}), 100)\n"
        "Tree(chain_10000)",
        env,
    )
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "recursive-template-depth-exceeded"
    assert result.context.get("limit") == 100


def test_recursion_bound_precise_boundary_at_the_documented_ceiling():
    # At exactly max_depth=100, a chain of 100 nested levels must validate
    # successfully (an off-by-one here would silently narrow the documented
    # ceiling), while 101 must fail -- both far beyond the ~75-80 depth where
    # the original Python-recursion-based implementation actually crashed.
    env = make_global_env([])
    env.set("chain_100", _build_chain(100))
    env.set("chain_101", _build_chain(101))
    source = (
        "Tree = recursive_template(\"tree\", (ref) -> alternatives(\"kind\", "
        "{leaf: exact_shape({kind: refinement((x) -> x == \"leaf\")}), "
        "node: exact_shape({kind: refinement((x) -> x == \"node\"), left: ref(\"tree\")})}), 100)\n"
    )
    at_boundary = interpreter_module.run_source(source + "Tree(chain_100)", env)
    beyond_boundary = interpreter_module.run_source(source + "Tree(chain_101)", env)
    assert isinstance(at_boundary, GeniaOptionSome)
    assert isinstance(beyond_boundary, GeniaOptionErr)
    assert beyond_boundary.reason == "recursive-template-depth-exceeded"


def test_multiple_self_references_per_node_are_all_independently_checked():
    # A binary tree has two self-references per node (left AND right), unlike
    # every other E15-6 example's single linear spine. The iterative
    # stack-based walker must check both branches, not silently special-case
    # a single self-reference field per level.
    source = (
        "BTree = recursive_template(\"btree\", (ref) -> alternatives(\"kind\", "
        "{leaf: exact_shape({kind: refinement((x) -> x == \"leaf\")}), "
        "node: exact_shape({kind: refinement((x) -> x == \"node\"), left: ref(\"btree\"), right: ref(\"btree\")})}), 10)\n"
    )
    valid = _run(
        source
        + "BTree({kind: \"node\", "
        + "left: {kind: \"node\", left: {kind: \"leaf\"}, right: {kind: \"leaf\"}}, "
        + "right: {kind: \"leaf\"}})"
    )
    assert isinstance(valid, GeniaOptionSome)

    bad_right_branch = _run(
        source
        + "BTree({kind: \"node\", left: {kind: \"leaf\"}, right: {kind: \"sideways\"}})"
    )
    assert bad_right_branch.reason == "alternative-unknown-discriminator"
