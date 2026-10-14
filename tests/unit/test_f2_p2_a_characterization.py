"""Python-host P2-A baseline, not portable authority or proposed P2 semantics.

Normal entry execution still shares the runtime root. Modules and ordinary
lexical children are real distinct Envs; a caller-created child is not a P2
entry. These tests deliberately preserve awkward compatibility observations.
"""

import io
import re
import subprocess
import sys

import pytest

from genia import make_global_env, run_source
from genia.callable import DebugHooks
from genia.debug_controller import LogicalFrame, StdioDebugSession
from genia.environment import Env
from genia.interpreter import Parser, _emit_error, _resolve_program_result, lex, lower_program, repl
from genia.server_config_binding import discover_entry_file_server_config_binding
from genia.server_route_binding import discover_entry_file_route_bindings
from genia.test_cli import _write_stderr, _write_stdout, discover_test_units, make_test_env
from genia.values import GeniaOptionNone, GeniaOutputSink
from hosts.python.mcp_worker_profile import (
    ALLOWED_AUTOLOADS,
    ALLOWED_BINDINGS,
    DENIED_NAMES,
    policy_violation,
    prune_environment,
)
from tools import gen_function_docs, lint_doc


def load_module(tmp_path, root, source, name="baseline_module"):
    """Execute a real local module and expose its own closure-owned environment."""
    (tmp_path / f"{name}.genia").write_text(source, encoding="utf-8")
    run_source(f"import {name}", root, filename=str(tmp_path / "entry.genia"))
    module = root.get(name)
    return module, module.exports["probe"].get(0).closure


@pytest.mark.parametrize("name,params,call,result", [
    ("first", "x", "first(41)", 41),
    ("map", "f, xs", "map((x) -> x + 1, [41])", [41]),
    ("map_acc", "f, xs, acc", "map_acc((x) -> x, [], [41])", [41]),
])
def test_entry_definition_before_list_autoload_succeeds_then_poison_load(name, params, call, result):
    root = make_global_env([])
    assert name not in root.values
    registered = {n for n, _arity in root.autoloads}
    assert (name in registered) == (name != "map_acc")
    body = {"first": "x", "map": "xs", "map_acc": "acc"}[name]
    run_source(f"{name}({params}) = {body}", root)
    group = root.values[name]
    assert group.get(len(params.split(","))).closure is root
    assert root.entry_scope() is root.runtime_scope() is root
    assert run_source(call, root) == result
    arity = len(params.split(","))
    with pytest.raises(TypeError, match="^" + re.escape(f"Duplicate function definition: {name}/{arity}") + "$"):
        run_source("length([1])", root)
    assert root.values[name] is group
    assert not root.loading_files


@pytest.mark.parametrize("name,params,body", [
    ("first", "x", "x"), ("map", "f, xs", "xs"),
    ("map_acc", "f, xs, acc", "acc"),
])
def test_entry_duplicate_shape_after_autoload_fails_without_replacing_group(name, params, body):
    root = make_global_env([])
    assert run_source("length([1,2])", root) == 2
    group = root.get(name)
    original = group.get(len(params.split(",")))
    arity = len(params.split(","))
    with pytest.raises(TypeError, match="^" + re.escape(f"Duplicate function definition: {name}/{arity}") + "$"):
        run_source(f"{name}({params}) = {body}", root)
    assert root.get(name) is group
    assert group.get(len(params.split(","))) is original
    assert original.closure is root


def test_rows_zero_arity_joins_existing_host_group_and_preserves_one_arity():
    root = make_global_env([])
    group = root.get("rows")
    host_arm = group.get(1)
    metadata = root.get_metadata("rows")
    assert run_source("rows() = 71\nrows()", root) == 71
    assert root.get("rows") is group
    assert group.get(1) is host_arm
    assert group.get(0).closure is root
    assert root.get_metadata("rows") is metadata
    assert run_source('rows(sheet([["a", [1]]]))', root) == [[["a", 1]]]


def test_new_arity_merges_with_loaded_prelude_without_changing_existing_arm():
    root = make_global_env([])
    original = root.get("first").get(1)
    assert run_source("first(x, y) = y\n[first([3]) |> unwrap_or(0), first(1, 42)]", root) == [3, 42]
    assert root.get("first").get(1) is original
    assert root.get("first").get(2).closure is root


def test_assignment_replaces_runtime_visible_callable_in_shared_root():
    root = make_global_env([])
    before = root.get("log")
    assert callable(before)
    assert run_source("log = 5\nlog", root) == 5
    assert root.values["log"] == 5
    assert root.runtime_scope() is root.entry_scope()
    with pytest.raises(TypeError, match="^pipeline stage expected a callable value, received int$"):
        run_source("log(1)", root)


@pytest.mark.parametrize("rebind_parent,expected", [(True, 19), (False, 17)])
def test_real_lexical_child_assignment_respects_existing_write_boundary(rebind_parent, expected):
    root = make_global_env([])
    run_source("marker = 17", root)
    child = Env(root, rebind_parent=rebind_parent)
    assert run_source("marker = 19\nmarker", child) == 19
    assert root.values["marker"] == expected
    assert ("marker" in child.values) == (not rebind_parent)
    assert child.entry_scope() is root  # Caller child is not registered entry.


def test_parameter_shadow_and_returned_closure_capture_real_frame():
    root = make_global_env([])
    recorder = FrameRecorder()
    root.debug_hooks = recorder
    root.debug_mode = True
    assert run_source("marker = 17\nmake(marker) -> (x) -> marker + x\nf = make(19)\nf(23)", root) == 42
    frame = next(env for name, env in recorder.frames if name == "make")
    assert frame.parent is root
    assert frame.values["marker"] == 19
    assert root.values["marker"] == 17
    run_source("marker = 100", root)
    assert run_source("f(23)", root) == 42
    assert root.values["marker"] == 100
    assert "x" not in root.values


@pytest.mark.parametrize("entry_first", [True, False])
def test_module_free_name_reads_live_shared_entry_root_without_warning(tmp_path, capsys, entry_first):
    root = make_global_env([])
    if entry_first:
        run_source("entry_marker = 17", root)
    module, scope = load_module(tmp_path, root, "probe() = entry_marker")
    if not entry_first:
        run_source("entry_marker = 17", root)
    assert run_source("baseline_module.probe()", root) == 17
    run_source("entry_marker = 19", root)
    assert run_source("baseline_module.probe()", root) == 19
    assert scope.parent is root
    assert scope.unit_scope() is scope
    assert scope.inspection_globals_scope() is root
    assert module.exports["probe"].get(0).closure is scope
    assert "entry_marker" not in scope.values
    assert capsys.readouterr().err == ""


def test_module_local_names_and_writes_are_distinct_from_root_and_sibling(tmp_path):
    root = make_global_env([])
    run_source("marker = 17\nprobe() = marker", root)
    _, first = load_module(tmp_path, root, "marker = 19\nprobe() = marker", "one")
    _, second = load_module(tmp_path, root, "marker = 23\nprobe() = marker", "two")
    assert run_source("[probe(), one.probe(), two.probe()]", root) == [17, 19, 23]
    assert first.parent is second.parent is root
    assert first is not second
    assert first.values["probe"] is not second.values["probe"]
    assert first.values["marker"] == 19
    assert second.values["marker"] == 23
    assert root.values["marker"] == 17


def test_contribution_closure_keeps_module_owner_but_reads_entry_helper_through_root(tmp_path):
    root = make_global_env([])
    (tmp_path / "base.genia").write_text('open dispatch("base", x) = x', encoding="utf-8")
    (tmp_path / "extension.genia").write_text(
        'import base\nextend base.dispatch("ext", x) = entry_helper(x)', encoding="utf-8")
    source = 'entry_helper(x) = x + 1\nimport base\nimport extension\nuse dispatch from base with extension\ndispatch("ext", 41)'
    assert run_source(source, root, filename=str(tmp_path / "entry.genia")) == 42
    assert "entry_helper" not in root.get("extension").exports
    unit = next(iter(root.get("extension").contributions.values()))
    scope = unit.clauses[0].closure
    assert scope is not root
    assert scope.parent is root
    assert scope.unit_scope() is scope
    assert scope.module_identity() == "extension"
    assert scope.get("entry_helper") is root.get("entry_helper")
    assert root.get("entry_helper").get(1).closure is root


def test_top_level_module_read_depends_on_entry_definition_before_import(tmp_path):
    (tmp_path / "immediate.genia").write_text("captured = entry_marker\nprobe() = captured", encoding="utf-8")
    root = make_global_env([])
    with pytest.raises(NameError, match="^Undefined name: entry_marker$"):
        run_source("import immediate", root, filename=str(tmp_path / "entry.genia"))
    assert "immediate" not in root.loaded_modules
    assert not root.loading_modules
    assert run_source("entry_marker = 17\nimport immediate\nimmediate.probe()", root,
                      filename=str(tmp_path / "entry.genia")) == 17
    run_source("entry_marker = 19", root)
    assert run_source("immediate.probe()", root) == 17  # Snapshot assignment, not late free lookup.


def test_lookup_chain_precedes_guarded_internal_then_autoload(tmp_path):
    root = make_global_env([])
    root.set_host_internal("lookup_probe", 7, visibility="runtime-public")
    child = Env(root, internal_access=True)
    assert child.get("lookup_probe") == 7
    root.set_host("lookup_probe", 11, visibility="runtime-public")
    assert child.get("lookup_probe") == 11
    child.set("lookup_probe", 13)
    assert child.get("lookup_probe") == 13
    path = tmp_path / "autoload_probe.genia"
    path.write_text("loaded_probe() = 31", encoding="utf-8")
    root.register_host_autoload("loaded_probe", 0, str(path), visibility="runtime-public")
    assert child.get("loaded_probe").get(0).closure is root
    assert "loaded_probe" not in child.values
    with pytest.raises(NameError, match="^Undefined name: absent_probe$"):
        child.get("absent_probe")


@pytest.mark.parametrize("reflection", ["doc", "meta", "help"])
def test_module_direct_binding_and_metadata_exist_but_string_reflection_uses_root(tmp_path, reflection):
    output = []
    root = make_global_env([], output_handler=output.append)
    _, scope = load_module(tmp_path, root, '@doc "module documentation"\nprobe() = 41\n')
    assert scope.get_metadata("probe").get("doc") == "module documentation"
    assert scope.get("probe") is root.get("baseline_module").exports["probe"]
    assert scope.get(reflection) is root.get(reflection)
    result = run_source(f'{reflection}("probe")', scope)
    if reflection == "help":
        assert "No public helper or runtime name found: probe" in "".join(output)
        output.clear()
        run_source("help(probe)", scope)
        assert "module documentation" in "".join(output)
    else:
        assert isinstance(result, GeniaOptionNone)
        assert result.reason == f"missing-{reflection}"
        assert result.context.get("name") == "probe"
    assert "probe" not in root.values


def test_shared_root_entry_reflection_preserves_metadata_and_callable_identity():
    output = []
    root = make_global_env([], output_handler=output.append)
    run_source('@doc "entry documentation"\nprobe() = 41', root)
    group = root.get("probe")
    assert run_source('doc("probe")', root) == "entry documentation"
    assert run_source('meta("probe")', root) is root.get_metadata("probe")
    run_source('help("probe")', root)
    assert "entry documentation" in "".join(output)
    assert root.get("probe") is group


def test_unregistered_helper_missing_before_autoload_then_directly_visible_but_not_catalogued():
    output = []
    root = make_global_env([], output_handler=output.append)
    with pytest.raises(NameError, match="^Undefined name: map_acc$"):
        root.get("map_acc")
    assert run_source('doc("map_acc")', root).reason == "missing-doc"
    assert isinstance(run_source('doc("map")', root), str)
    assert root.get("map_acc").get(3).closure is root
    assert run_source('doc("map_acc")', root).reason == "missing-doc"
    assert run_source('meta("map_acc")', root).count() == 0
    run_source('help("map_acc")', root)
    assert "map_acc" in "".join(output)
    output.clear()
    run_source("help()", root)
    assert "map_acc" not in "".join(output)
    assert all(name != "map_acc" for name, _arity in root.autoloads)


def test_metacircular_empty_environment_reads_live_entry_root_but_owns_writes():
    root = make_global_env([])
    assert run_source("entry_marker = 17\ne = empty_env()\neval(quote(entry_marker), e)", root) == 17
    meta_scope = root.get("e").env
    assert meta_scope.parent is root
    assert not meta_scope.rebind_parent
    assert run_source("entry_marker = 19\neval(quote(entry_marker), e)", root) == 19
    assert run_source("eval(quote(entry_marker = 23), e)", root) == 23
    assert meta_scope.values["entry_marker"] == 23
    assert root.values["entry_marker"] == 19


@pytest.mark.parametrize("mode", ["command", "file"])
def test_cli_actual_entry_main_dispatch_uses_shared_root(mode, tmp_path):
    source = 'marker = "kept"\nmain(args) = [marker, args]'
    if mode == "command":
        args = ["-c", source, "argument"]
    else:
        path = tmp_path / "entry.genia"
        path.write_text(source, encoding="utf-8")
        args = [str(path), "argument"]
    result = subprocess.run([sys.executable, "-c", "from genia.interpreter import _main; _main()", *args],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert result.stdout == '["kept", ["argument"]]\n'
    assert result.stderr == ""


def test_native_discovery_real_root_includes_entry_tests_excludes_module_tests(tmp_path):
    root, registered = make_test_env(fixture_bindings={"fixture_marker": 41})
    _, scope = load_module(tmp_path, root, '@test "module"\nprobe() = true')
    run_source('@test "entry"\nentry_test() = fixture_marker == 41\ntest("legacy", () -> true)', root)
    units = discover_test_units(root)
    assert [unit.name for unit in units] == ["legacy", "entry_test"]
    assert units[0] is registered[0]
    assert root._native_test_units is registered
    assert root.host_binding_visibility["test"] == "entry-only"
    assert scope.get("fixture_marker") == 41  # Classification does not isolate today.
    assert "fixture_marker" not in scope.values


def test_serve_descriptor_discovery_real_entry_ir_excludes_module_metadata(tmp_path):
    root = make_global_env([])
    load_module(tmp_path, root, '@server {port: 0}\nmodule_app = {}\n@route {method: "GET", path: "/module"}\nprobe(request) = request\nprobe() = true')
    source = '@server {port: 0}\napp = {}\n@route {method: "GET", path: "/entry"}\nhandler(request) = request'
    run_source(source, root, filename="entry.genia")
    nodes = lower_program(Parser(lex(source), source=source, filename="entry.genia").parse_program())
    config = discover_entry_file_server_config_binding(nodes, root.entry_scope(), entry_source_identity="entry.genia")
    routes = discover_entry_file_route_bindings(nodes, root.entry_scope(), entry_source_identity="entry.genia")
    assert config.diagnostics == routes.diagnostics == []
    assert config.binding.declaration_name == "app"
    assert [route.path for route in routes.routes] == ["/entry"]
    assert routes.routes[0].handler is root.get("handler")


class FrameRecorder(DebugHooks):
    """Observe actual entry, module and prelude frames without replacing lookup."""

    def __init__(self):
        """Retain named call frames for debugger inspection after evaluation."""
        self.frames = []

    def on_function_enter(self, fn_name, args, env, span):
        """Capture the real lexical frame constructed by callable dispatch."""
        self.frames.append((fn_name, env))


def test_debugger_real_module_and_prelude_frames_show_root_globals_and_local_parameters(tmp_path):
    recorder = FrameRecorder()
    root = make_global_env([], debug_hooks=recorder, debug_mode=True)
    _, scope = load_module(tmp_path, root, "module_marker = 23\nprobe() = length([1,2])")
    run_source("entry_marker = 17\nbaseline_module.probe()", root)
    session = StdioDebugSession(io.StringIO(), io.StringIO(), filename="entry.genia")
    session.ensure_root_frame(root)
    assert session.frames[0].env is root
    module_frame = next(env for name, env in recorder.frames if name == "probe")
    prelude_frame = next(env for name, env in recorder.frames if name == "length")
    assert module_frame.parent is scope
    assert prelude_frame.parent is root
    for frame_id, frame in enumerate([module_frame, prelude_frame], 2):
        session.frames.append(LogicalFrame(frame_id, "probe", frame, "entry.genia", 1, 1))
        globals_view = {item["name"]: item["value"] for item in session._variables("globals", frame_id)}
        assert globals_view["entry_marker"] == "17"
        assert "module_marker" not in globals_view
        assert "entry_marker" not in {item["name"] for item in session._variables("locals", frame_id)}
    assert "xs" in prelude_frame.values


def test_runtime_documentation_consumers_use_real_autoload_catalogue():
    records = {record["name"]: record for record in gen_function_docs.collect()}
    assert records["map"]["source_kind"] == "prelude"
    assert records["map"]["doc_raw"]
    assert "map_acc" not in records
    assert "map" in lint_doc._runtime_public_names()
    assert "map" in lint_doc._runtime_public_prelude_names()
    assert "map_acc" not in lint_doc._runtime_public_prelude_names()


@pytest.mark.parametrize("child_input", [False, True])
def test_mcp_pruning_real_runtime_denies_bindings_and_autoloads_but_not_child_values(child_input):
    root = make_global_env([])
    child = Env(root)
    child.set("unit_marker", 41)
    prune_environment(child if child_input else root)
    assert set(root.values) <= ALLOWED_BINDINGS
    assert set(root.autoloads) <= ALLOWED_AUTOLOADS
    assert child.values == {"unit_marker": 41}
    assert child.runtime_scope() is root
    for name in DENIED_NAMES:
        with pytest.raises(NameError, match="Undefined name:"):
            child.get(name)
    assert run_source("length([1,2])", child) == 2
    assert root.get("length").get(1).closure is root
    assert "length" not in child.values
    assert not child.internal_access
    assert root.trusted_autoloads <= set(root.autoloads)
    with pytest.raises(NameError, match="^Undefined name: _evolve$"):
        child.get("_evolve")
    assert Env(root, internal_access=True).get("_evolve") is root.internal_values["_evolve"]


def test_mcp_root_bound_help_catalogue_observes_pruned_autoload_table():
    output = []
    root = make_global_env([], output_handler=output.append)
    help_callable = root.get("help")
    prune_environment(root)
    assert root.get("help") is help_callable
    help_callable()
    text = "".join(output)
    assert "read_file" not in text
    assert "write_file" not in text
    assert "map_put" in text
    output.clear()
    root.get("help")("read_file")
    assert "No public helper or runtime name found: read_file" in "".join(output)
    for source in ["secret_get", 'import python', "eval(quote(read_file), empty_env())"]:
        assert policy_violation(Parser(lex(source), source=source).parse_program())


@pytest.mark.parametrize("consumer", [_emit_error, _write_stderr, _write_stdout])
def test_error_and_test_output_use_supplied_env_local_sink_then_system_fallback(consumer, capsys):
    output = []
    root = make_global_env([])
    name = "stdout" if consumer is _write_stdout else "stderr"
    root.set_host(name, GeniaOutputSink(name, writer=output.append), visibility="runtime-public")
    consumer(root, "root-message")
    assert output == ["root-message" + ("" if name == "stdout" else "\n")]
    output.clear()
    consumer(Env(root), "child-message")
    assert output == []  # Inherited sink is ignored by these current consumers.
    captured = capsys.readouterr()
    assert (captured.out if name == "stdout" else captured.err) == "child-message" + ("" if name == "stdout" else "\n")


def test_protected_entry_binding_is_visible_to_module_inspection_but_payload_is_redacted(tmp_path):
    root = make_global_env([])
    run_source('provider = config_provider([{kind: quote(values), values: {KEY: "P2_A_PAYLOAD_SENTINEL"}}]) |> unwrap_or(none)\nprotected_marker = secret_get(provider, "KEY", quote(use)) |> unwrap_or(none)', root)
    _, scope = load_module(tmp_path, root, "probe() = protected_marker")
    protected = root.get("protected_marker")
    assert scope.get("protected_marker") is protected
    session = StdioDebugSession(io.StringIO(), io.StringIO(), filename="entry.genia")
    session.frames.append(LogicalFrame(1, "module", scope, "module.genia", 1, 1))
    rendered = repr(session._variables("globals", 1))
    assert "protected_marker" in rendered
    assert "P2_A_PAYLOAD_SENTINEL" not in rendered
    with pytest.raises(TypeError) as error:
        run_source("protected_marker |> print", root)
    assert "P2_A_PAYLOAD_SENTINEL" not in str(error.value)


@pytest.mark.parametrize("name,source,call,result", [
    ("first", "first(x) = x", "first(41)", 41),
    ("map", "map(f, xs) = xs", "map((x) -> x + 1, [41])", [41]),
    ("rows", "rows() = 41", "rows()", 41),
])
def test_plain_child_definitions_shadow_parent_group_instead_of_write_through(name, source, call, result):
    root = make_global_env([])
    original = root.get(name)
    child = Env(root)
    run_source(source, child)
    assert run_source(call, child) == result
    assert child.values[name] is not original
    assert root.get(name) is original
    assert child.entry_scope() is root
    assert all(arm.closure is child for arm in child.values[name].values())
    if name == "rows":
        assert child.values[name].sorted_arities() == [0]
        with pytest.raises(TypeError, match="^No matching function: rows/1. Available: rows/0$"):
            run_source("rows(sheet([]))", child)


def test_plain_child_entry_main_is_ignored_by_current_entry_accessor():
    root = make_global_env([])
    child = Env(root)
    result = run_source("main() = 41", child)
    assert "main" in child.values and "main" not in root.values
    assert _resolve_program_result(result, child) is result
    assert run_source("main()", child) == 41


def test_repl_real_shared_root_lists_entry_runtime_autoload_and_redacts_protection(monkeypatch, capsys):
    commands = iter([
        'entry_marker = 17',
        'protected_marker = secret_get(config_provider([{kind: quote(values), values: {KEY: "P2_A_REPL_SENTINEL"}}]) |> unwrap_or(none), "KEY", quote(use)) |> unwrap_or(none)',
        'length([1, 2])', ':env', ':quit',
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(commands))
    monkeypatch.setattr("sys.stdin", io.StringIO())
    repl()  # Only terminal input is scripted; environment and rendering are real.
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "entry_marker = 17\n" in captured.out
    assert "length = " in captured.out
    assert "stdout = " in captured.out
    assert "protected_marker = " in captured.out
    assert "P2_A_REPL_SENTINEL" not in captured.out
