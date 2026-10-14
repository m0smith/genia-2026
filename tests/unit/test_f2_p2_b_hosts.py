"""Python-only B7–B10 host-path behavioral reds (§16.6, P2-C/P2-D).

Observations wrap real evaluation and construction. Terminal/protocol/transport
edges are scripted to remain offline; scopes and lookup are never replaced.
"""

import importlib
import io
from types import SimpleNamespace

import pytest

from genia import run_source
from genia.callable import DebugHooks
from genia.debug_controller import LogicalFrame, StdioDebugSession
from genia.environment import Env
from genia import interpreter
from genia.test_cli import _write_stderr, _write_stdout, discover_test_units, make_test_env
from genia.values import GeniaOutputSink
from hosts.python import mcp_worker
from hosts.python.mcp_worker_profile import DENIED_NAMES, prune_environment
from tests.unit.f2_p2_support import load_program_module, program_env, separated_scopes


@pytest.mark.parametrize("site", ["repl", "debug_stdio", "serve", "pipe", "command", "file", "native", "model_fixture", "grounded_fixture", "concurrency_fixture", "ollama", "mcp_worker", "mcp_host"])
def test_B8_B_all_13_program_construction_paths_register_entry(tmp_path, monkeypatch, site):
    """§16.6.2–4/A3: P2-C/D executes every listed host construction path in E."""
    seen = []
    original = interpreter.run_source

    def observe(source, env, **kwargs):
        """Record the actual caller-owned Env and still execute the real evaluator."""
        seen.append(env)
        return original(source, env, **kwargs)

    monkeypatch.setattr(interpreter, "run_source", observe)
    path = tmp_path / "entry.genia"
    path.write_text("entry_marker = 17", encoding="utf-8")
    if site in ("pipe", "command", "file"):
        mode = interpreter.ExecutionMode(kind=site, source="it" if site == "pipe" else "entry_marker = 17", program_path=str(path), script_args=[])
        monkeypatch.setattr("sys.stdin", io.StringIO("record\n"))
        assert interpreter._run_execution_mode(mode) == 0
    elif site == "repl":
        commands = iter(["entry_marker = 17", "entry_marker = 19", ":quit"])
        monkeypatch.setattr("builtins.input", lambda *_: next(commands))
        monkeypatch.setattr("sys.stdin", io.StringIO())
        interpreter.repl()
    elif site == "debug_stdio":
        monkeypatch.setattr(StdioDebugSession, "run", lambda self, work, **kw: work())
        interpreter.run_debug_stdio(str(path), command_stream=io.StringIO(), event_stream=io.StringIO(), error_stream=io.StringIO())
    elif site == "serve":
        assert interpreter._run_serve_file(str(path)) == 1  # No server descriptor, no listener.
    elif site == "native":
        e, _ = make_test_env()
        observe("entry_marker = 17", e)
    elif site.endswith("fixture"):
        module_name = {"model_fixture": "exec_model_fixture", "grounded_fixture": "exec_r12_grounded_fixture", "concurrency_fixture": "exec_r25_concurrency_fixture"}[site]
        e = importlib.import_module(f"hosts.python.{module_name}")._build_env()
        observe("entry_marker = 17", e)
    elif site == "ollama":
        from hosts.python import exec_ollama_chat

        path.write_text("run_chat(args, provider, authority) = none", encoding="utf-8")
        monkeypatch.setattr(exec_ollama_chat, "EXAMPLE", path)
        assert exec_ollama_chat.main([]) == 0
    elif site == "mcp_worker":
        import genia

        monkeypatch.setattr(genia, "run_source", observe)
        assert mcp_worker.execute_source("entry_marker = 17")["status"] == "completed"
    else:
        from hosts.python import mcp_host

        path.write_text("serve(revision, host) = none", encoding="utf-8")
        monkeypatch.setattr(mcp_host, "run_source", observe)
        monkeypatch.setattr(mcp_host, "LineMux", lambda fd: SimpleNamespace(provider=lambda: iter(())))
        monkeypatch.setattr(mcp_host, "RunCapability", lambda mux: SimpleNamespace(run=lambda *_: "unused"))
        monkeypatch.setattr(mcp_host.signal, "signal", lambda *_: None)
        monkeypatch.setattr("sys.stdin", SimpleNamespace(fileno=lambda: 0))
        assert mcp_host.main([str(path), "revision"]) == 0
    assert seen, f"construction site {site} did not execute a program"
    for e in seen:
        assert e is e.entry_scope() and e is not e.runtime_scope(), f"{site}: program still evaluated in shared R=E"
        assert e.parent is e.runtime_scope()
    if site == "repl":
        assert seen[0] is seen[1], "one persistent E per REPL session"


@pytest.mark.parametrize("observation", ["owner", "fixtures", "registrar", "list", "discovery", "runner"])
def test_B9_B_native_registration_discovery_and_execution_are_entry_owned(tmp_path, observation):
    """§8/§16.6.3: P2-C/D puts fixture, registrar, list and annotated tests in E."""
    e, registrations = make_test_env(fixture_bindings={"fixture_marker": 41})
    r = e.runtime_scope()
    module = load_program_module(tmp_path, e, '@test "module"\nprobe() = true')
    run_source('@test "entry"\nentry_test() = fixture_marker == 41\ntest("legacy", () -> fixture_marker == 41)', e)
    units = discover_test_units(e)
    if observation == "owner":
        assert e is not r and e.entry_scope() is e
    elif observation in ("fixtures", "registrar"):
        name = "fixture_marker" if observation == "fixtures" else "test"
        assert name in e.values and name not in r.values
    elif observation == "list":
        assert e._native_test_units is registrations
        assert not hasattr(r, "_native_test_units")
    elif observation == "discovery":
        assert [u.name for u in units] == ["legacy", "entry_test"]
        assert "entry_test" not in r.values
        assert module.exports["probe"].get(0).closure is not e
    else:
        from genia.test_kernel import run_test_suite

        suite = run_test_suite(units)
        assert suite["passed"] == 2
        assert units[0] is registrations[0]
        assert units[1].body.closure is e
        assert e is not r


def test_B7_B_worker_prunes_runtime_before_entry_registration(monkeypatch):
    """§16.6/§16.7: P2-D worker prunes R while unregistered, then evaluates empty E."""
    import genia

    phases = []
    original_run = genia.run_source

    def observe_prune(env):
        """Observe pre-registration owner and perform the actual security pruning."""
        phases.append(("prune", env, env.entry_scope()))
        prune_environment(env)

    def observe_run(source, env, **kwargs):
        """Capture E's initial state before any program binding can mask a leak."""
        phases.append(("run", env, dict(env.values)))
        return original_run(source, env, **kwargs)

    monkeypatch.setattr(mcp_worker, "prune_environment", observe_prune)
    monkeypatch.setattr(genia, "run_source", observe_run)
    assert mcp_worker.execute_source("length([1,2])")["status"] == "completed"
    assert [phase[0] for phase in phases] == ["prune", "run"]
    r = phases[0][1]
    e = phases[1][1]
    assert phases[0][2] is r
    assert e is not r and e.runtime_scope() is r
    assert phases[1][2] == {}
    assert not (set(r.values) & DENIED_NAMES)


@pytest.mark.parametrize("name", ["secret_get", "read_file"])
def test_B7_A_denied_names_do_not_regain_runtime_authority(tmp_path, name):
    """§16.7: P2-C/D distinguishes pruned builtin and manifest-owned prelude names."""
    s = separated_scopes(tmp_path, prune=prune_environment)
    assert name not in s.runtime.values
    try:
        run_source(f"{name}(x) = x", s.entry)
    except (NameError, TypeError, ValueError, RuntimeError):
        pass  # Contract permits rejection; it does not specify a new diagnostic.
    assert name not in s.runtime.values, "classification recreated a denied runtime binding"
    assert all(key[0] != name for key in s.runtime.autoloads)
    with pytest.raises(NameError, match="Undefined name:"):
        s.module.get(name)
    if name == "secret_get" and name in s.entry.values:
        assert run_source("secret_get(41)", s.entry) == 41


@pytest.mark.parametrize("consumer", [interpreter._emit_error, _write_stdout, _write_stderr])
def test_B10_B_host_sinks_read_runtime_even_from_child(consumer, capsys):
    """§16.6.3: P2-D repairs the existing inherited-sink failure without topology stubs."""
    output = []
    e = program_env()
    name = "stdout" if consumer is _write_stdout else "stderr"
    e.runtime_scope().values[name] = GeniaOutputSink(name, writer=output.append)
    consumer(Env(e), "message")
    assert output == ["message" + ("" if name == "stdout" else "\n")]
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_B10_B_repl_inspection_excludes_runtime_and_preserves_entry(monkeypatch, capsys):
    """§8/§16.1.4: P2-D :env sees ordinary and entry-declared runtime-owned names."""
    commands = iter(["entry_marker = 17", "log = 5", "length([1,2])", ":env", ":quit"])
    monkeypatch.setattr("builtins.input", lambda *_: next(commands))
    monkeypatch.setattr("sys.stdin", io.StringIO())
    interpreter.repl()
    out = capsys.readouterr().out
    assert "entry_marker = 17\n" in out and "log = 5\n" in out
    assert "stdout = " not in out and "length = " not in out


def test_B10_B_debugger_module_globals_use_module_unit(tmp_path):
    """§8/§16.6.1: P2-D globals are M while frame locals remain local."""
    e = program_env()
    run_source("entry_marker = 17", e)
    module = load_program_module(tmp_path, e, "module_marker = 23\nprobe() = module_marker")
    scope = module.exports["probe"].get(0).closure
    frame = Env(scope)
    frame.set("local_marker", 29)
    session = StdioDebugSession(io.StringIO(), io.StringIO(), filename="entry.genia")
    session.frames.append(LogicalFrame(1, "probe", frame, "module.genia", 1, 1))
    globals_view = {v["name"]: v["value"] for v in session._variables("globals", 1)}
    assert globals_view.get("module_marker") == "23", "debugger globals selected R instead of M"
    assert "entry_marker" not in globals_view and "stdout" not in globals_view
    assert [v["name"] for v in session._variables("locals", 1)] == ["local_marker"]


class Recorder(DebugHooks):
    """Capture actual frames for runtime debug ownership and stepping coverage."""

    def __init__(self):
        """Start an empty frame log."""
        self.frames = []

    def on_function_enter(self, fn_name, args, env, span):
        """Retain each real frame without modifying evaluation or ownership."""
        self.frames.append((fn_name, env))


def test_B10_A_debug_hooks_owned_by_runtime_reach_module_and_callbacks(tmp_path):
    """§16.6.3: P2-D stores hooks/mode on R and observes real M/prelude callbacks."""
    s = separated_scopes(tmp_path)
    recorder = Recorder()
    s.runtime.debug_hooks = recorder
    s.runtime.debug_mode = True
    s.load("probe(x) = x + 1", "callback_module")
    assert run_source("map(callback_module.probe, [41])", s.entry) == [42]
    assert any(name == "probe" and env.unit_scope().module_identity() == "callback_module" for name, env in recorder.frames)
    assert any(name == "map" and env.unit_scope() is s.runtime for name, env in recorder.frames)
    assert s.entry.debug_hooks is None and not s.entry.debug_mode


def test_B9_A_runtime_owned_entry_annotation_is_discovered_and_executed(tmp_path):
    """§16.1.4: P2-D native discovery includes an entry-declared unregistered helper."""
    from genia.test_kernel import run_test_suite

    s = separated_scopes(tmp_path)
    run_source('@test "runtime-owned entry test"\nmap_acc() = true', s.entry)
    units = discover_test_units(s.entry)
    assert [unit.name for unit in units] == ["map_acc"]
    assert units[0].body is s.runtime.get("map_acc").get(0)
    assert run_test_suite(units)["passed"] == 1


def test_B8_A_serve_discovery_includes_entry_declared_runtime_owned_handler(tmp_path):
    """§16.1.4/§8: P2-D serve view includes recorded R-owned declarations, never all R."""
    from genia.interpreter import Parser, lex, lower_program
    from genia.server_route_binding import discover_entry_file_route_bindings

    s = separated_scopes(tmp_path)
    source = '@route {method: "GET", path: "/entry"}\nmap_acc(request) = request'
    run_source(source, s.entry, filename="entry.genia")
    nodes = lower_program(Parser(lex(source), source=source, filename="entry.genia").parse_program())
    routes = discover_entry_file_route_bindings(nodes, s.entry, entry_source_identity="entry.genia")
    assert not routes.diagnostics and [route.path for route in routes.routes] == ["/entry"]
    assert routes.routes[0].handler is s.runtime.get("map_acc")


def test_B10_A_protected_entry_values_are_redacted_in_globals_and_diagnostics(tmp_path):
    """§16.6.5/R10: P2-D physical separation must preserve protected rendering sinks."""
    s = separated_scopes(tmp_path)
    source = 'protected_marker = secret_get(config_provider([{kind: quote(values), values: {KEY: "P2_B_PROTECTED_SENTINEL"}}]) |> unwrap_or(none), "KEY", quote(use)) |> unwrap_or(none)'
    run_source(source, s.entry)
    session = StdioDebugSession(io.StringIO(), io.StringIO(), filename="entry.genia")
    session.frames.append(LogicalFrame(1, "entry", Env(s.entry), "entry.genia", 1, 1))
    rendered = repr(session._variables("globals", 1))
    assert "protected_marker" in rendered and "P2_B_PROTECTED_SENTINEL" not in rendered
    with pytest.raises(TypeError) as failure:
        run_source("protected_marker |> print", s.entry)
    assert "P2_B_PROTECTED_SENTINEL" not in str(failure.value)
