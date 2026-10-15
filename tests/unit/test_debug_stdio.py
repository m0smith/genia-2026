"""Python stdio debugger observations, including pre-isolation F2 scope views.

Globals currently show the shared root even for a module-declared function.
These host-tool observations must not be mistaken for future D3 unit visibility.
"""

import io
import json
from pathlib import Path

import pytest

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


@pytest.mark.parametrize("origin", ["entry", "module", "module_nested"])
def test_function_globals_are_unit_scoped_and_locals_are_frame_bindings(tmp_path: Path, origin):
    """Pin unit-scoped globals across entry, module and nested module call frames.

    F2/P2-D (contract 16.6.1): before, every frame showed the shared root (entry
    names plus runtime names). Now an entry frame shows the entry scope and a
    module frame shows its own module scope; runtime bindings appear in neither.
    """
    body = "probe(parameter) = {\n  local_marker = parameter\n  local_marker\n}\n"
    if origin == "entry":
        source = "entry_marker = 17\n" + body + "probe(23)\n"
        stop_file = tmp_path / "program.genia"
        stop_line = 3
    else:
        stop_file = tmp_path / "scope_fixture.genia"
        if origin == "module":
            module_source = "module_marker = 41\n" + body
            invocation = "scope_fixture.probe(23)\n"
            stop_line = 3
        else:
            module_source = (
                "module_marker = 41\n"
                "probe(parameter, captured) = {\n"
                "  local_marker = parameter\n"
                "  local_marker + captured\n"
                "}\n"
                "wrapper(captured) = {\n"
                "  result = probe(23, captured)\n"
                "  result\n"
                "}\n"
            )
            invocation = "scope_fixture.wrapper(11)\n"
            stop_line = 3
        stop_file.write_text(module_source, encoding="utf-8")
        source = "entry_marker = 17\nimport scope_fixture\n" + invocation

    code, events, stderr = run_session(tmp_path, source, [
        {"command": "setBreakpoints", "breakpoints": [{"file": str(stop_file.resolve()), "line": stop_line}]},
        {"command": "continue"},
        {"command": "stackTrace"},
        {"command": "variables", "scope": "locals"},
        {"command": "variables", "scope": "globals"},
        {"command": "disconnect"},
    ])

    assert code == 0, stderr
    assert stderr == ""
    stops = stopped_events(events)
    assert stops[-1]["reason"] == "breakpoint"
    assert Path(stops[-1]["file"]).resolve() == stop_file.resolve()
    assert stops[-1]["line"] == stop_line
    stack = next(event for event in events if event.get("responseTo") == "stackTrace")
    assert stack["frames"][0]["name"] == "probe"
    assert stack["frames"][0]["id"] == stops[-1]["frameId"]
    assert stack["frames"][0]["id"] != stack["frames"][-1]["id"]
    locals_response, globals_response = [event for event in events if event.get("responseTo") == "variables"]
    expected_locals = [{"name": "parameter", "value": "23", "type": "number"}]
    if origin == "module_nested":
        expected_locals.insert(0, {"name": "captured", "value": "11", "type": "number"})
        assert [frame["name"] for frame in stack["frames"][:2]] == ["probe", "wrapper"]
    assert locals_response["variables"] == expected_locals
    globals_rows = globals_response["variables"]
    assert [row["name"] for row in globals_rows] == sorted(row["name"] for row in globals_rows)
    globals_by_name = {row["name"]: row for row in globals_rows}
    assert {"stdout", "stderr", "doc", "meta", "help"}.isdisjoint(globals_by_name)
    assert {"parameter", "local_marker", "captured"}.isdisjoint(globals_by_name)
    if origin == "entry":
        assert globals_by_name["entry_marker"] == {"name": "entry_marker", "value": "17", "type": "number"}
        assert globals_by_name["probe"]["type"] == "function"
        assert "module_marker" not in globals_by_name
    else:
        assert globals_by_name["module_marker"] == {"name": "module_marker", "value": "41", "type": "number"}
        assert globals_by_name["probe"]["type"] == "function"
        assert "entry_marker" not in globals_by_name and "scope_fixture" not in globals_by_name
        assert ("wrapper" in globals_by_name) == (origin == "module_nested")


def test_prelude_frame_globals_are_runtime_bindings_not_entry_bindings(tmp_path: Path):
    """Prelude frames show runtime globals (F2/P2-D); entry bindings are not visible; locals stay in the frame.

    Before P2-D the shared root made entry_marker appear among a prelude frame's globals.
    """
    source = "entry_marker = 17\ncount([1, 2])\n"
    code, events, stderr = run_session(tmp_path, source, [
        {"command": "setBreakpoints", "breakpoints": [{"file": str((tmp_path / "program.genia").resolve()), "line": 2}]},
        {"command": "continue"},
        {"command": "stepIn"},
        {"command": "stackTrace"},
        {"command": "variables", "scope": "locals"},
        {"command": "variables", "scope": "globals"},
        {"command": "disconnect"},
    ])
    assert code == 0
    assert stderr == ""
    assert stopped_events(events)[-1]["reason"] == "step"
    assert "std/prelude/list.genia" in stopped_events(events)[-1]["file"]
    stack = next(event for event in events if event.get("responseTo") == "stackTrace")
    assert stack["frames"][0]["name"] == "count"
    locals_response, globals_response = [event for event in events if event.get("responseTo") == "variables"]
    locals_by_name = {row["name"]: row for row in locals_response["variables"]}
    assert "entry_marker" not in locals_by_name
    assert any(row["value"] == "[1, 2]" for row in locals_by_name.values())
    globals_by_name = {row["name"]: row for row in globals_response["variables"]}
    assert "entry_marker" not in globals_by_name
    assert globals_by_name["count"]["type"] == "function" and "stdout" in globals_by_name
    assert locals_by_name.keys().isdisjoint(globals_by_name)
