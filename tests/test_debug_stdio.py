import io
import json
from pathlib import Path

from genia.interpreter import run_debug_stdio


def run_session(tmp_path: Path, source: str, commands: list[dict]) -> tuple[int, list[dict], str]:
    program = tmp_path / "program.genia"
    program.write_text(source, encoding="utf-8")
    stdin = io.StringIO("\n".join(json.dumps(cmd) for cmd in commands) + "\n")
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_debug_stdio(str(program), command_stream=stdin, event_stream=stdout, error_stream=stderr)
    events = [json.loads(line) for line in stdout.getvalue().splitlines() if line.strip()]
    return code, events, stderr.getvalue()


def stopped_events(events: list[dict]) -> list[dict]:
    return [event for event in events if event.get("event") == "stopped"]


def test_entry_stop_and_initialized(tmp_path: Path):
    code, events, _ = run_session(tmp_path, "x = 1\nx\n", [{"command": "continue"}])
    assert code == 0
    assert events[0] == {"event": "initialized"}
    assert events[1]["event"] == "stopped"
    assert events[1]["reason"] == "entry"


def test_breakpoint_hit_and_termination(tmp_path: Path):
    source = "x = 1\nx = 2\nx\n"
    code, events, _ = run_session(
        tmp_path,
        source,
        [
            {"command": "setBreakpoints", "breakpoints": [{"file": str((tmp_path / 'program.genia').resolve()), "line": 2}]},
            {"command": "continue"},
            {"command": "continue"},
        ],
    )
    assert code == 0
    stops = stopped_events(events)
    assert any(stop["reason"] == "breakpoint" and stop["line"] == 2 for stop in stops)
    assert events[-1] == {"event": "terminated", "exitCode": 0}


def test_step_in_and_step_over(tmp_path: Path):
    source = "inc(x) = x + 1\ninc(4)\n"
    code, events, _ = run_session(
        tmp_path,
        source,
        [
            {"command": "setBreakpoints", "breakpoints": [{"file": str((tmp_path / 'program.genia').resolve()), "line": 2}]},
            {"command": "continue"},
            {"command": "stepIn"},
            {"command": "stepOver"},
            {"command": "disconnect"},
        ],
    )
    assert code == 0
    stops = stopped_events(events)
    assert any(stop["reason"] == "step" for stop in stops)
    breakpoint_stop = next(stop for stop in stops if stop["reason"] == "breakpoint")
    step_stop = next(stop for stop in stops if stop["reason"] == "step")
    assert step_stop["frameId"] != breakpoint_stop["frameId"]


def test_stack_trace_and_scopes_variables(tmp_path: Path):
    source = "g(x) = x + 1\nf(x) = g(x)\nf(5)\n"
    frame_probe = {"command": "scopes", "frameId": 0}
    locals_probe = {"command": "variables", "scope": "locals", "frameId": 0}
    globals_probe = {"command": "variables", "scope": "globals", "frameId": 0}
    code, events, _ = run_session(
        tmp_path,
        source,
        [
            {"command": "setBreakpoints", "breakpoints": [{"file": str((tmp_path / 'program.genia').resolve()), "line": 3}]},
            {"command": "continue"},
            {"command": "stepIn"},
            {"command": "stackTrace"},
            frame_probe,
            locals_probe,
            globals_probe,
            {"command": "disconnect"},
        ],
    )
    assert code == 0

    stack = next(event for event in events if event.get("responseTo") == "stackTrace")
    frame_names = [frame["name"] for frame in stack["frames"]]
    assert "f" in frame_names

    scopes = next(event for event in events if event.get("responseTo") == "scopes")
    assert {scope["name"] for scope in scopes["scopes"]} == {"locals", "globals"}

    locals_vars = [event for event in events if event.get("responseTo") == "variables" and any(v["name"] == "x" for v in event["variables"])]
    assert locals_vars
    globals_vars = [event for event in events if event.get("responseTo") == "variables" and any(v["name"] == "f" for v in event["variables"])]
    assert globals_vars


def test_autoloaded_file_stop_location(tmp_path: Path):
    source = "count([1, 2, 3])\n"
    code, events, _ = run_session(
        tmp_path,
        source,
        [
            {"command": "setBreakpoints", "breakpoints": [{"file": str((tmp_path / 'program.genia').resolve()), "line": 1}]},
            {"command": "continue"},
            {"command": "stepIn"},
            {"command": "disconnect"},
        ],
    )
    assert code == 0
    stops = stopped_events(events)
    assert any("std/prelude/list.genia" in stop["file"] for stop in stops)


def test_output_event_is_emitted(tmp_path: Path):
    code, events, _ = run_session(
        tmp_path,
        'print("hello")\n',
        [{"command": "continue"}],
    )
    assert code == 0
    outputs = [event for event in events if event.get("event") == "output"]
    assert outputs and outputs[0]["output"] == "hello\n"
