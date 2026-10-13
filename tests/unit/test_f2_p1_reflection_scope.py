"""Python-host reflection factoring seams; public scope binding remains legacy root."""

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
def test_reflection_alias_and_module_argument_keep_root_binding(name):
    outputs = []
    root = make_global_env([], output_handler=outputs.append)
    child = Env(root)
    run_source('@doc "root documentation"\nsubject(x) -> x\n', root)
    run_source('@doc "child documentation"\nsubject(x) -> x\nuse_reflection(f) -> f("subject")\n', child)
    public = root.get(name)
    child.set("reflection_alias", public)
    result = run_source('use_reflection(reflection_alias)', child)
    if name == "doc":
        assert result == "root documentation"
    elif name == "meta":
        assert result is root.get_metadata("subject")
    else:
        assert "root documentation" in "".join(outputs)
        assert "child documentation" not in "".join(outputs)
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
