"""Python debugger and REPL inspection use explicit compatibility seams."""

import io

from genia.debug_controller import LogicalFrame, StdioDebugSession
from genia.environment import Env
from genia.interpreter import repl


def test_debugger_globals_select_compatibility_owner_and_locals_stay_local():
    local = Env()
    local.set("local", 3)
    globals_env = Env()
    globals_env.set("compatible", 7)
    local.inspection_globals_scope = lambda: globals_env
    session = StdioDebugSession(io.StringIO(), io.StringIO(), filename="entry.genia")
    session.frames.append(LogicalFrame(1, "nested", local, "entry.genia", 1, 1))
    assert session._variables("globals", 1) == [{"name": "compatible", "value": "7", "type": "number"}]
    assert session._variables("locals", 1) == [{"name": "local", "value": "3", "type": "number"}]


def test_debugger_initial_frame_uses_entry_accessor():
    local = Env()
    entry = Env()
    local.entry_scope = lambda: entry
    session = StdioDebugSession(io.StringIO(), io.StringIO(), filename="entry.genia")
    session.ensure_root_frame(local)
    assert session.frames[0].env is entry
    session.ensure_root_frame(local)
    assert len(session.frames) == 1


def test_repl_env_uses_inspection_owner(monkeypatch, capsys):
    import genia.interpreter as interpreter
    from genia.builtins import make_global_env

    env = make_global_env()
    inspected = Env()
    inspected.set("visible", 29)
    env.inspection_globals_scope = lambda: inspected
    commands = iter([":env", ":quit"])
    monkeypatch.setattr(interpreter, "make_program_env", lambda *_args: env)
    monkeypatch.setattr("builtins.input", lambda *_args: next(commands))
    monkeypatch.setattr("sys.stdin", io.StringIO())
    repl()
    assert capsys.readouterr().out == "visible = 29\n"
