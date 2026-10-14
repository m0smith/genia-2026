"""Python-only B11/B12 real-scope integration reds, §16.5/6 (#1220/#1221).

P2-D owns consumer results; P2-C supplies the explicitly missing registration.
Mutation cases first verify the real observation, then inject the wrong owner
at that consumer's accessor seam. A caller-created child cannot pass setup.
"""

import ast
import io

import pytest

from genia import run_source
from genia.debug_controller import LogicalFrame, StdioDebugSession
from genia.environment import Env
from genia import interpreter
from genia.interpreter import Parser, lex, lower_program
from genia.server_config_binding import discover_entry_file_server_config_binding
from genia.server_route_binding import discover_entry_file_route_bindings
from genia.test_cli import _write_stderr, _write_stdout, discover_test_units
from genia.values import GeniaOutputSink
from hosts.python.mcp_worker_profile import prune_environment
from tools import gen_function_docs, lint_doc
from tests.unit.f2_p2_support import ROOT, separated_scopes, wrong_accessor


def test_B11_B_catalogue_source_guard_rejects_implicit_root():
    """§16.5.2: P2-D must remove root calls outside environment.py, notably help."""
    violations = []
    for path in sorted((ROOT / "src/genia").glob("*.py")):
        if path.name == "environment.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "root":
                violations.append(f"{path.relative_to(ROOT)}:{node.lineno}:root")
    assert not violations, "§16.5 runtime accessor required: " + ", ".join(violations)


def test_B11_B_autoload_reads_use_runtime_or_reviewed_runtime_constructor():
    """§16.5.2: P2-D keeps catalogue ownership explicit, without banning R setup."""
    # env in make_global_env is R by construction; MCP profile binds root through
    # runtime_scope; tools bind env through runtime_scope. These are reviewed,
    # named receivers, never a blanket exception for entry/module autoloads.
    allowlist = {
        "src/genia/builtins.py": {"env"},
        "hosts/python/mcp_worker_profile.py": {"runtime"},
        "tools/gen_function_docs.py": {"env", "root"},
    }
    paths = [ROOT / name for name in allowlist] + [ROOT / "tools/lint_doc.py"]
    violations = []
    for path in paths:
        relative = str(path.relative_to(ROOT))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Attribute) or node.attr != "autoloads" or not isinstance(node.ctx, ast.Load):
                continue
            receiver = node.value
            explicit = isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Attribute) and receiver.func.attr == "runtime_scope"
            reviewed = isinstance(receiver, ast.Name) and receiver.id in allowlist.get(relative, set())
            if not explicit and not reviewed:
                violations.append(f"{relative}:{node.lineno}:{ast.unparse(receiver)}.autoloads")
    assert not violations, "§16.5 catalogue must use R: " + ", ".join(violations)


@pytest.mark.parametrize("pruned", [False, True])
def test_B11_A_help_overview_identical_from_R_E_M_and_pruned_R(tmp_path, pruned):
    """§16.5.3: P2-D takes catalogue/sink from R regardless of lookup evaluation."""
    s = separated_scopes(tmp_path, prune=prune_environment if pruned else None)
    run_source("entry_custom(x) = x", s.entry)
    s.load("module_custom(x) = x\nprobe() = help()", "help_module")
    texts = []
    for scope, source in [(s.runtime, "help()"), (s.entry, "help()"), (s.entry, "help_module.probe()")]:
        s.output.clear()
        run_source(source, scope)
        texts.append("".join(s.output))
    assert texts[0] and texts[0] == texts[1] == texts[2]
    assert "map_put" in texts[0]
    assert "entry_custom" not in texts[0] and "module_custom" not in texts[0]
    assert "map_acc" not in texts[0]  # Manifest ownership does not mean catalogue membership.
    assert ("read_file" not in texts[0]) if pruned else ("read_file" in texts[0])


def test_B11_A_wrong_catalogue_owner_empty_control_is_discriminating(tmp_path, monkeypatch):
    """§16.5.3/#1220: P2-D R-catalogue observation rejects an E catalogue mutation."""
    s = separated_scopes(tmp_path)
    run_source("help()", s.entry)
    expected = "".join(s.output)
    assert "map_put" in expected and not s.entry.autoloads
    # Change only the runtime catalogue consulted by the helper, retaining the
    # same R/E/M and public callable. This is the specific empty-E regression.
    monkeypatch.setattr(s.runtime, "autoloads", s.entry.autoloads)
    s.output.clear()
    run_source("help()", s.entry)
    with pytest.raises(AssertionError):
        assert "".join(s.output) == expected


def observe_boundary(boundary, s, monkeypatch):
    """Drive the real consumer and assert a sentinel owner observation.

    Called unchanged before/after accessor mutation. No fake consumer or
    substituted lookup implementation is used; setup creates real unit state.
    """
    r, e, m = s.runtime, s.entry, s.module
    if boundary == "main":
        assert interpreter._resolve_program_result(None, r) == 41
    elif boundary == "native":
        assert [u.name for u in discover_test_units(r)] == ["entry_test"]
    elif boundary == "serve":
        source = '@server {port: 0}\napp = {}\n@route {method: "GET", path: "/entry"}\nhandler(request) = request'
        nodes = lower_program(Parser(lex(source), source=source, filename="entry.genia").parse_program())
        owner = r.entry_scope()
        config = discover_entry_file_server_config_binding(nodes, owner, entry_source_identity="entry.genia")
        routes = discover_entry_file_route_bindings(nodes, owner, entry_source_identity="entry.genia")
        assert not config.diagnostics and config.binding is not None
        assert not routes.diagnostics and [route.path for route in routes.routes] == ["/entry"]
        assert owner.get("web") is e.values["web"]
    elif boundary.startswith("debug"):
        owner = e if boundary == "debug_entry" else m
        frame = Env(owner)
        frame.set("local_marker", 29)
        session = StdioDebugSession(io.StringIO(), io.StringIO(), filename="entry.genia")
        session.frames.append(LogicalFrame(1, "probe", frame, "unit.genia", 1, 1))
        view = {item["name"] for item in session._variables("globals", 1)}
        expected = "entry_marker" if boundary == "debug_entry" else "module_marker"
        assert expected in view and "stdout" not in view and "local_marker" not in view
        if boundary == "debug_entry":
            assert "log" in view, "entry-declared runtime-owned name absent from E view"
        assert [item["name"] for item in session._variables("locals", 1)] == ["local_marker"]
    elif boundary in ("error_sink", "stdout_sink", "stderr_sink"):
        consumer = {"error_sink": interpreter._emit_error, "stdout_sink": _write_stdout, "stderr_sink": _write_stderr}[boundary]
        s.output.clear()
        consumer(e, "boundary-message")
        assert s.output == ["boundary-message" + ("" if boundary == "stdout_sink" else "\n")]
    elif boundary == "generator":
        monkeypatch.setattr(gen_function_docs, "make_global_env", lambda *_: e)
        records = {record["name"]: record for record in gen_function_docs.collect()}
        assert "map" in records and "map_acc" not in records
    elif boundary == "linter":
        import genia.builtins

        monkeypatch.setattr(genia.builtins, "make_global_env", lambda *_: e)
        assert "map" in lint_doc._runtime_public_names()
        assert "map" in lint_doc._runtime_public_prelude_names()
    elif boundary == "reflection":
        assert run_source('doc("entry_subject")', e.unit_scope()) == "entry docs"
    elif boundary == "mcp_prune":
        prune_environment(e)
        assert "secret_get" not in r.values and "entry_marker" in e.values
    else:
        raise ValueError(f"unknown boundary: {boundary}")


BOUNDARIES = {
    "main": ("runtime", "entry_scope"),
    "native": ("runtime", "entry_scope"),
    "serve": ("runtime", "entry_scope"),
    "debug_entry": ("entry", "inspection_globals_scope"),
    "debug_module": ("module", "inspection_globals_scope"),
    "error_sink": ("entry", "runtime_scope"),
    "stdout_sink": ("entry", "runtime_scope"),
    "stderr_sink": ("entry", "runtime_scope"),
    "generator": ("entry", "runtime_scope"),
    "linter": ("entry", "runtime_scope"),
    "reflection": ("entry", "unit_scope"),
    "mcp_prune": ("entry", "runtime_scope"),
}


@pytest.mark.parametrize("boundary", list(BOUNDARIES))
@pytest.mark.parametrize("wrong_owner", ["runtime", "entry", "module"])
def test_B12_A_real_consumers_discriminate_wrong_accessors(tmp_path, monkeypatch, boundary, wrong_owner):
    """§16.6.5/#1221: P2-D consumer evidence needs nonaliased R/E/M controls.

    The equal-owner parameter is the positive control; other parameters must
    fail the identical observation after a wrong-owner accessor injection.
    """
    s = separated_scopes(tmp_path, prepare=lambda r: [
        r.set_host("stdout", GeniaOutputSink("stdout", writer=lambda text: s.output.append(text)), visibility="runtime-public"),
        r.set_host("stderr", GeniaOutputSink("stderr", writer=lambda text: s.output.append(text)), visibility="runtime-public"),
    ])
    run_source('entry_marker = 17\nlog = 5\n@doc "entry docs"\nentry_subject(x) = x\nmain() = 41\n@test "entry"\nentry_test() = true', s.entry)
    if boundary == "serve":
        run_source('import web\n@server {port: 0}\napp = {}\n@route {method: "GET", path: "/entry"}\nhandler(request) = request', s.entry, filename="entry.genia")
    origin, accessor = BOUNDARIES[boundary]
    owner = getattr(s, origin)
    correct = getattr(owner, accessor)()
    replacement = getattr(s, wrong_owner)
    # Use separate monkeypatch contexts: tooling factory patches must not leak
    # from the positive observation into setup/mutation or another boundary.
    with monkeypatch.context() as positive:
        observe_boundary(boundary, s, positive)
    if replacement is correct:
        return
    if boundary == "mcp_prune":
        # Positive pruning already removed denied keys; restore test-only sentinel
        # directly for the second observation without installing host authority.
        s.runtime.values["secret_get"] = object()
    with monkeypatch.context() as negative:
        wrong_accessor(negative, owner, accessor, replacement)
        if boundary.startswith("debug"):
            # Frames inherit inspection ownership via unit_scope in P2; inject
            # the frame accessor itself when checking the real debugger seam.
            original = Env.inspection_globals_scope

            def wrong_frame_scope(frame):
                """Return the wrong unit only for descendants of the tested owner."""
                return replacement if frame.parent is owner else original(frame)

            negative.setattr(Env, "inspection_globals_scope", wrong_frame_scope)
        with pytest.raises(AssertionError):
            observe_boundary(boundary, s, negative)


@pytest.mark.parametrize("wrong_owner", ["runtime", "entry", "module"])
def test_B12_A_actual_repl_discriminates_wrong_inspection_owner(tmp_path, monkeypatch, wrong_owner):
    """§16.6.5: P2-D :env mutation uses the actual constructed REPL session scope.

    Only terminal input is scripted. Observation wraps real evaluation, then
    injects the wrong inspection accessor before the next :env command.
    """
    separated_scopes(tmp_path)  # A-class API gate and non-aliasing control.
    original = interpreter.run_source

    def session(mutate):
        """Run one real REPL session and return captured :env text and actual E."""
        output = []
        seen = []
        commands = iter(["entry_marker = 17", ":env", ":quit"])
        with monkeypatch.context() as patch:
            def observe(source, e, **kwargs):
                """Execute unchanged source, then instrument the real session owner."""
                result = original(source, e, **kwargs)
                r = e.runtime_scope()
                seen.append(e)
                module = s_module(e)
                r.values["stdout"] = GeniaOutputSink("stdout", writer=output.append)
                if mutate:
                    replacement = {"runtime": r, "entry": e, "module": module}[wrong_owner]
                    patch.setattr(e, "inspection_globals_scope", lambda: replacement)
                return result

            def s_module(e):
                """Load a real sibling M in this same execution for the wrong-unit variant."""
                (tmp_path / "repl_module.genia").write_text("module_marker = 23\nprobe() = module_marker", encoding="utf-8")
                original("import repl_module", e, filename=str(tmp_path / "entry.genia"))
                return e.get("repl_module").exports["probe"].get(0).closure

            patch.setattr(interpreter, "run_source", observe)
            patch.setattr("builtins.input", lambda *_: next(commands))
            patch.setattr("sys.stdin", io.StringIO())
            interpreter.repl()
        assert len(seen) == 1 and seen[0] is not seen[0].runtime_scope()
        return "".join(output)

    def assert_view(text):
        """The same observation must pass for E and fail for either wrong owner."""
        assert "entry_marker = 17" in text
        assert "stdout = " not in text and "module_marker = " not in text

    assert_view(session(False))
    if wrong_owner == "entry":
        assert_view(session(True))
    else:
        with pytest.raises(AssertionError):
            assert_view(session(True))
