"""P1-B red gate for proposed Python Env ownership accessors (issue #1067).

These are host-internal APIs, not portable Genia syntax or scope-isolation
semantics. Root remains runtime and entry; debugger inspection remains root
even when the declaring unit is a module. No implementation is included.
"""

import pytest

from genia import make_global_env, run_source
from genia.callable import DebugHooks
from genia.environment import Env


class ScopeRecorder(DebugHooks):
    """Retain evaluated scopes to check ownership without changing execution."""

    def __init__(self):
        """Keep separate frame and expression-scope observations for each run."""
        self.frames = []
        self.node_scopes = []

    def on_function_enter(self, fn_name, args, env, span):
        """Record real named-function frames, including their lexical parents."""
        self.frames.append((fn_name, env))

    def before_node(self, node, env):
        """Retain block/lambda scopes that need not have logical debug frames."""
        self.node_scopes.append(env)


def assert_owners(scope, runtime, unit):
    """Check owner object identity and the P1 root inspection compatibility view."""
    assert scope.runtime_scope() is runtime
    assert scope.entry_scope() is runtime
    assert scope.unit_scope() is unit
    assert scope.inspection_globals_scope() is runtime


def load_fixture(tmp_path, root, source, name="scope_fixture"):
    """Load a real module and return its declaration Env from an ordinary closure."""
    (tmp_path / f"{name}.genia").write_text(source, encoding="utf-8")
    run_source(f"import {name}\n", root, filename=str(tmp_path / "entry.genia"))
    module = root.get(name)
    module_scope = module.exports["probe"].get(1).closure
    return module, module_scope


@pytest.mark.parametrize("factory", [Env, make_global_env], ids=["standalone", "host"])
@pytest.mark.parametrize("accessor", [
    "runtime_scope", "entry_scope", "unit_scope", "inspection_globals_scope",
])
def test_root_is_its_own_runtime_entry_unit_and_inspection_owner(factory, accessor):
    root = factory()
    assert root.parent is None
    assert getattr(root, accessor)() is root
    assert root.parent is None


def test_repeated_entry_submissions_keep_root_as_entry_and_function_closure():
    root = make_global_env([])
    run_source("entry_marker = 17\nprobe(x) = x + entry_marker\n", root)
    assert run_source("entry_marker = 19\nprobe(23)\n", root) == 42
    assert root.get("probe").get(1).closure is root
    assert root.values["entry_marker"] == 19
    assert_owners(root, root, root)
    assert root.parent is None


@pytest.mark.parametrize("rebind_parent", [True, False])
def test_caller_supplied_child_is_not_registered_as_entry_or_module_unit(rebind_parent):
    root = make_global_env([])
    child = Env(root, rebind_parent=rebind_parent)
    assert run_source("child_marker = 11\nprobe(x) = x + child_marker\nprobe(12)\n", child) == 23
    assert child.get("probe").get(1).closure is child
    assert "child_marker" not in root.values
    assert_owners(child, root, root)
    assert_owners(root, root, root)
    assert child.parent is root


@pytest.mark.parametrize("accessor,owner", [
    ("runtime_scope", "root"),
    ("entry_scope", "root"),
    ("unit_scope", "module"),
    ("inspection_globals_scope", "root"),
])
def test_loaded_module_distinguishes_declaring_unit_from_entry_and_inspection(tmp_path, accessor, owner):
    root = make_global_env([])
    root.set("entry_marker", 17)
    module, module_scope = load_fixture(tmp_path, root, "module_marker = 41\nprobe(x) = x\n")
    assert module_scope.parent is root
    assert module_scope.values["module_marker"] == 41
    assert "module_marker" not in root.values
    assert module.exports["probe"].get(1).closure is module_scope
    assert getattr(module_scope, accessor)() is (root if owner == "root" else module_scope)
    assert module_scope.parent is root
    assert module_scope.get("entry_marker") == 17  # P1 deliberately retains today's read.


def test_module_descendants_inherit_owner_without_module_id_or_write_boundary_inference(tmp_path):
    root = make_global_env([])
    _module, module_scope = load_fixture(tmp_path, root, "probe(x) = x\n")
    child = Env(module_scope, rebind_parent=False)
    grandchild = Env(child)
    grandchild.module_id = "unrelated-provenance-string"
    assert_owners(module_scope, root, module_scope)
    assert_owners(child, root, module_scope)
    assert_owners(grandchild, root, module_scope)
    assert child.parent is module_scope
    assert grandchild.parent is child
    assert root.unit_scope() is root


def test_module_unit_is_available_before_its_first_top_level_assignment(tmp_path):
    observations = []

    class ModuleEntryProbe(DebugHooks):
        """Inspect ownership during evaluation, before module exports exist."""

        def before_node(self, node, env):
            """Capture owners before the module's marker assignment runs."""
            if getattr(node, "name", None) == "module_marker":
                assert "module_marker" not in env.values
                observations.append((
                    env, env.runtime_scope(), env.entry_scope(),
                    env.unit_scope(), env.inspection_globals_scope(),
                ))

    root = make_global_env([], debug_hooks=ModuleEntryProbe(), debug_mode=True)
    _module, module_scope = load_fixture(tmp_path, root, "module_marker = 41\nprobe(x) = x\n")
    assert observations == [(module_scope, root, root, module_scope, root)]
    assert module_scope.parent is root


def test_module_aliases_and_sibling_imports_do_not_reset_execution_entry(tmp_path):
    root = make_global_env([])
    (tmp_path / "sibling.genia").write_text("probe(x) = x + 1\n", encoding="utf-8")
    module, module_scope = load_fixture(
        tmp_path, root, "import sibling\nprobe(x) = sibling.probe(x)\n"
    )
    assert run_source("import scope_fixture as alias\nalias.probe(41)\n", root, filename=str(tmp_path / "entry.genia")) == 42
    sibling = module_scope.get("sibling")
    sibling_scope = sibling.exports["probe"].get(1).closure
    assert root.get("alias") is module
    assert module_scope.parent is sibling_scope.parent is root
    assert_owners(module_scope, root, module_scope)
    assert_owners(sibling_scope, root, sibling_scope)
    assert_owners(root, root, root)
    assert root.loaded_modules["scope_fixture"] is module
    assert root.loaded_modules["sibling"] is sibling


def test_real_module_function_block_and_lambda_scopes_keep_lexical_unit(tmp_path):
    recorder = ScopeRecorder()
    root = make_global_env([], debug_hooks=recorder, debug_mode=True)
    _module, module_scope = load_fixture(
        tmp_path, root,
        "probe(x) = {\n  local_marker = x\n"
        "  {\n    nested_marker = local_marker\n    nested_marker\n  }\n}\n"
        "make_callback() = (value) -> value + 1\n",
    )
    assert run_source(
        "scope_fixture.probe(23)\ncallback = scope_fixture.make_callback()\ncallback(41)\n",
        root, filename=str(tmp_path / "entry.genia"),
    ) == 42
    probe_frame = next(env for name, env in recorder.frames if name == "probe")
    assert probe_frame.parent is module_scope
    # A nested block and a returned lambda create lexical descendants.
    descendants = [env for env in recorder.node_scopes if env.parent is probe_frame]
    assert descendants
    lambda_scopes = [env for env in recorder.node_scopes if env.values.get("value") == 41]
    assert lambda_scopes
    assert_owners(probe_frame, root, module_scope)
    for scope in [*descendants, *lambda_scopes]:
        assert_owners(scope, root, module_scope)
    assert_owners(root, root, root)


def test_prelude_autoload_from_module_keeps_runtime_unit_and_state(tmp_path):
    recorder = ScopeRecorder()
    root = make_global_env([], debug_hooks=recorder, debug_mode=True)
    _module, module_scope = load_fixture(tmp_path, root, "probe(xs) = length(xs)\n")
    assert run_source("scope_fixture.probe([1, 2])\n", root) == 2
    prelude_function = root.get("length").get(1)
    assert prelude_function.closure is root
    assert "length" not in module_scope.values
    assert root.loaded_files
    length_frame = next(env for name, env in recorder.frames if name == "length")
    assert_owners(length_frame, root, root)
    assert_owners(module_scope, root, module_scope)
    assert_owners(root, root, root)
    assert module_scope.runtime_scope().loaded_files is root.loaded_files
    assert module_scope.runtime_scope().autoloads is root.autoloads
    assert module_scope.runtime_scope().internal_values is root.internal_values


def test_accessors_return_live_binding_and_metadata_owner_without_rebinding(tmp_path):
    root = make_global_env([])
    run_source("entry_marker = 17\n", root)
    _module, module_scope = load_fixture(
        tmp_path, root, '@meta {label: "module"}\nprobe(x) = x\nmodule_marker = 41\n'
    )
    values = module_scope.values
    metadata = module_scope.binding_metadata
    module_cache = root.loaded_modules
    entry_values = root.values
    assert_owners(module_scope, root, module_scope)
    assert module_scope.unit_scope().values is values
    assert module_scope.unit_scope().binding_metadata is metadata
    assert module_scope.entry_scope().values is entry_values
    assert module_scope.runtime_scope().loaded_modules is module_cache
    assert module_scope.inspection_globals_scope().values is entry_values
    assert module_scope.unit_scope().get_metadata("probe").get("label") == "module"
    assert "module_marker" not in module_scope.inspection_globals_scope().values
    assert module_scope.inspection_globals_scope().values["entry_marker"] == 17
    root.assign("entry_marker", 19)
    assert module_scope.entry_scope().values["entry_marker"] == 19
    assert module_scope.get("entry_marker") == 19
    assert module_scope.values is values
    assert module_scope.binding_metadata is metadata


def test_independent_executions_never_share_scope_owners(tmp_path):
    first = make_global_env([])
    second = make_global_env([])
    _first_module, first_scope = load_fixture(tmp_path, first, "probe(x) = x\n")
    _second_module, second_scope = load_fixture(tmp_path, second, "probe(x) = x\n")
    assert first_scope is not second_scope
    assert_owners(first_scope, first, first_scope)
    assert_owners(second_scope, second, second_scope)
    assert_owners(first, first, first)
    assert_owners(second, second, second)
