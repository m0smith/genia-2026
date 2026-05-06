from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TextIO

from .debug_protocol import read_json_line, write_json_line
from .callable import DebugHooks
from .environment import Env
from .lexer import SourceSpan
from .values import GeniaRef


class DebugDisconnect(Exception):
    pass


@dataclass
class LogicalFrame:
    id: int
    name: str
    env: Env
    file: str
    line: int
    column: int


class StdioDebugSession(DebugHooks):
    def __init__(self, command_stream: TextIO, event_stream: TextIO, *, filename: str) -> None:
        self.command_stream = command_stream
        self.event_stream = event_stream
        self.main_filename = filename
        self.breakpoints: set[tuple[str, int]] = set()
        self.frames: list[LogicalFrame] = []
        self.env_to_frame: dict[int, LogicalFrame] = {}
        self.next_frame_id = 1
        self.step_mode = "continue"
        self.step_depth = 0
        self.resume_skip_key: tuple[str, int, int] | None = None

    def run(self, execute: Callable[[], Any], *, error_stream: TextIO) -> int:
        self.emit({"event": "initialized"})
        try:
            self.pause(reason="entry", file=self.main_filename, line=1, column=1)
            execute()
            self.emit({"event": "terminated", "exitCode": 0})
            return 0
        except DebugDisconnect:
            self.emit({"event": "terminated", "exitCode": 0})
            return 0
        except Exception as exc:  # noqa: BLE001
            self.emit({"event": "error", "message": str(exc)})
            self.emit({"event": "terminated", "exitCode": 1})
            print(exc, file=error_stream)
            return 1

    def emit(self, payload: dict[str, Any]) -> None:
        write_json_line(self.event_stream, payload)

    def emit_stdout_output(self, output: str) -> None:
        self.emit({"event": "output", "category": "stdout", "output": output})

    def normalize_file(self, filename: str) -> str:
        return str(Path(filename).resolve())

    def on_function_enter(
        self,
        fn_name: str,
        args: tuple[Any, ...],  # noqa: ARG002
        env: Env,
        span: SourceSpan | None,
    ) -> None:
        file = self.main_filename
        line = 1
        column = 1
        if span is not None:
            file = span.filename
            line = span.line
            column = span.column
        frame = LogicalFrame(
            id=self.next_frame_id,
            name=fn_name,
            env=env,
            file=file,
            line=line,
            column=column,
        )
        self.next_frame_id += 1
        self.frames.append(frame)
        self.env_to_frame[id(env)] = frame
        if self.step_mode in {"step_in", "step_over", "step_out"}:
            self.pause(reason="step", file=file, line=line, column=column)

    def on_function_exit(
        self,
        fn_name: str,  # noqa: ARG002
        result: Any,  # noqa: ARG002
        env: Env,
        span: SourceSpan | None,  # noqa: ARG002
    ) -> None:
        frame = self.env_to_frame.pop(id(env), None)
        if frame is not None and self.frames and self.frames[-1].id == frame.id:
            self.frames.pop()

    def before_node(self, node: Any, env: Env) -> None:
        span = getattr(node, "span", None)
        if span is None:
            return
        frame = self._frame_for_env(env)
        frame.file = span.filename
        frame.line = span.line
        frame.column = span.column

        if type(node).__name__ not in {"IrExprStmt", "IrCall", "IrAssign"}:
            return

        depth = len(self.frames)
        location_key = (self.normalize_file(span.filename), span.line, depth)
        if self.resume_skip_key == location_key:
            self.resume_skip_key = None
            return

        if (self.normalize_file(span.filename), span.line) in self.breakpoints:
            self.pause(reason="breakpoint", file=span.filename, line=span.line, column=span.column)
            return

        if self.step_mode == "step_in":
            self.pause(reason="step", file=span.filename, line=span.line, column=span.column)
        elif self.step_mode == "step_over" and depth <= self.step_depth:
            self.pause(reason="step", file=span.filename, line=span.line, column=span.column)
        elif self.step_mode == "step_out" and depth < self.step_depth:
            self.pause(reason="step", file=span.filename, line=span.line, column=span.column)

    def after_node(self, node: Any, env: Env, result: Any) -> None:  # noqa: ARG002
        pass

    def pause(self, *, reason: str, file: str, line: int, column: int) -> None:
        frame = self.frames[-1]
        self.emit({
            "event": "stopped",
            "reason": reason,
            "file": file,
            "line": line,
            "frameId": frame.id,
        })
        while True:
            raw = self._read_command()
            if raw is None:
                raise DebugDisconnect()
            if not raw:
                continue
            command = raw.get("command")
            if command == "setBreakpoints":
                self._set_breakpoints(raw)
                self.emit({"responseTo": "setBreakpoints", "breakpoints": sorted(self.breakpoints)})
                continue
            if command == "stackTrace":
                self.emit({"responseTo": "stackTrace", "frames": self._stack_trace()})
                continue
            if command == "scopes":
                self.emit({"responseTo": "scopes", "scopes": [{"name": "locals"}, {"name": "globals"}]})
                continue
            if command == "variables":
                scope = str(raw.get("scope", "locals"))
                frame_id = int(raw.get("frameId", frame.id))
                self.emit({"responseTo": "variables", "variables": self._variables(scope, frame_id)})
                continue
            if command == "continue":
                self.step_mode = "continue"
                self.resume_skip_key = (self.normalize_file(file), line, len(self.frames))
                return
            if command == "stepIn":
                self.step_mode = "step_in"
                self.resume_skip_key = (self.normalize_file(file), line, len(self.frames))
                return
            if command == "stepOver":
                self.step_mode = "step_over"
                self.step_depth = len(self.frames)
                self.resume_skip_key = (self.normalize_file(file), line, len(self.frames))
                return
            if command == "stepOut":
                self.step_mode = "step_out"
                self.step_depth = len(self.frames)
                self.resume_skip_key = (self.normalize_file(file), line, len(self.frames))
                return
            if command == "disconnect":
                raise DebugDisconnect()
            self.emit({"event": "error", "message": f"Unknown command: {command}"})

    def _set_breakpoints(self, command: dict[str, Any]) -> None:
        entries = command.get("breakpoints", [])
        new_set: set[tuple[str, int]] = set()
        for entry in entries:
            if isinstance(entry, dict) and "file" in entry and "line" in entry:
                new_set.add((self.normalize_file(str(entry["file"])), int(entry["line"])))
        self.breakpoints = new_set

    def _read_command(self) -> dict[str, Any] | None:
        try:
            return read_json_line(self.command_stream)
        except Exception as exc:  # noqa: BLE001
            self.emit({"event": "error", "message": f"Invalid JSON command: {exc}"})
            return {}

    def _frame_for_env(self, env: Env) -> LogicalFrame:
        current: Env | None = env
        while current is not None:
            found = self.env_to_frame.get(id(current))
            if found is not None:
                return found
            current = current.parent
        return self.frames[0]

    def _stack_trace(self) -> list[dict[str, Any]]:
        return [
            {
                "id": frame.id,
                "name": frame.name,
                "file": frame.file,
                "line": frame.line,
                "column": frame.column,
            }
            for frame in reversed(self.frames)
        ]

    def _variables(self, scope: str, frame_id: int) -> list[dict[str, str]]:
        frame = next((item for item in self.frames if item.id == frame_id), self.frames[-1])
        values: dict[str, Any]
        if scope == "globals":
            values = frame.env.root().values
        else:
            values = frame.env.values
        return [self._variable(name, value) for name, value in sorted(values.items())]

    def _variable(self, name: str, value: Any) -> dict[str, str]:
        return {
            "name": name,
            "value": self._safe_value(value),
            "type": self._value_type(value),
        }

    def _safe_value(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        try:
            return repr(value)
        except Exception:  # noqa: BLE001
            return "<unrepresentable>"

    def _value_type(self, value: Any) -> str:
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, GeniaRef):
            return "ref"
        if callable(value):
            return "function"
        if isinstance(value, dict):
            return "object"
        return "unknown"

    def ensure_root_frame(self, env: Env) -> None:
        if self.frames:
            return
        frame = LogicalFrame(
            id=self.next_frame_id,
            name="<module>",
            env=env.root(),
            file=self.main_filename,
            line=1,
            column=1,
        )
        self.next_frame_id += 1
        self.frames.append(frame)
        self.env_to_frame[id(frame.env)] = frame
