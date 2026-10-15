"""Python-host reflection factoring seams; host-direct retrieval stays root-bound, identifier evaluation binds (F2/P2-D)."""

import inspect

import pytest

from genia import make_global_env, run_source
from genia.environment import Env


@pytest.mark.parametrize("name", ["doc", "meta", "help"])
def test_private_reflection_helper_uses_explicit_scope_without_rebinding_public_callable(name):
    outputs = []
    root = make_global_env([], output_handler=outputs.append)
    child = Env(root)
    run_source('@doc "root documentation"\nsubject(x) -> x\n', root)
    run_source('@doc "child documentation"\nsubject(x) -> x\n', child)
    public = root.get(name)
    assert child.get(name) is public
    helper = inspect.getclosurevars(public).nonlocals[f"_{name}_in_scope"]
    if name == "doc":
        assert helper(child, "subject") == "child documentation"
        assert public("subject") == "root documentation"
    elif name == "meta":
        assert helper(child, "subject") is child.get_metadata("subject")
        assert public("subject") is root.get_metadata("subject")
    else:
        helper(child, "subject")
        assert "child documentation" in "".join(outputs)
        outputs.clear()
        public("subject")
        assert "root documentation" in "".join(outputs)
        assert "child documentation" not in "".join(outputs)
    assert root.get(name) is public


@pytest.mark.parametrize("name", ["doc", "meta", "help"])
def test_raw_runtime_target_binds_at_identifier_evaluation_and_bound_value_keeps_its_scope(name):
    """F2/P2-D (contract 16.2): marking is value-based on the original runtime target.

    Before P2-D a host-installed alias of the raw callable stayed root-bound when
    passed on. Now evaluating the identifier binds it to the evaluating scope, while
    an already-bound callable (here, one read in root) keeps that scope when passed
    to child code. Host `Env.get` still returns the raw, root-bound public callable.
    """
    outputs = []
    root = make_global_env([], output_handler=outputs.append)
    child = Env(root)
    run_source('@doc "root documentation"\nsubject(x) -> x\n', root)
    run_source('@doc "child documentation"\nsubject(x) -> x\nuse_reflection(f) -> f("subject")\n', child)
    public = root.get(name)
    child.set("reflection_alias", public)

    def observe(source):
        """Run `source` in the child scope and return its result with captured help text."""
        outputs.clear()
        result = run_source(source, child)
        return result, "".join(outputs)

    result, text = observe("use_reflection(reflection_alias)")
    if name == "doc":
        assert result == "child documentation"
    elif name == "meta":
        assert result is child.get_metadata("subject")
    else:
        assert "child documentation" in text and "root documentation" not in text
    root_bound = run_source(name, root)
    child.set("granted", root_bound)
    result, text = observe("use_reflection(granted)")
    if name == "doc":
        assert result == "root documentation"
    elif name == "meta":
        assert result is root.get_metadata("subject")
    else:
        assert "root documentation" in text and "child documentation" not in text
    assert child.get("reflection_alias") is public


@pytest.mark.parametrize("name", ["doc", "meta", "help"])
def test_explicit_lookup_helper_keeps_autoload_runtime_owned(name):
    root = make_global_env([], output_handler=lambda text: None)
    child = Env(root)
    helper = inspect.getclosurevars(root.get(name)).nonlocals[f"_{name}_in_scope"]
    assert "map_put" not in root.values
    helper(child, "map_put")
    assert "map_put" in root.values
    assert "map_put" not in child.values
    assert child.get("map_put") is root.get("map_put")
