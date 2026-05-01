"""Error and diagnostic helpers for the Python reference host."""

from __future__ import annotations

import re


class GeniaQuietBrokenPipe(Exception):
    """Internal signal used when output sinks hit a broken pipe."""


def format_exception_text(exc: BaseException) -> str:
    message = str(exc).strip()
    name = type(exc).__name__
    return f"{name}: {message}" if message else name


def _extract_pipe_stage_name(message: str) -> str | None:
    match = re.search(r" at (.+?) \[", message)
    return match.group(1) if match else None


def _format_pipe_mode_error(exc: Exception) -> str:
    message = str(exc)
    if message == "-p/--pipe expects a single stage expression":
        return "Pipe mode expression must be a single stage expression, not a full program"
    if message == "-p/--pipe stage expression must omit stdin; it is added automatically":
        return "Do not use stdin in pipe mode; stdin is provided automatically"
    if message == "-p/--pipe stage expression must omit run; it is added automatically":
        return "Do not use run in pipe mode; run is implicit in pipe mode"
    if "Flow has already been consumed" in message:
        return "Flow values are single-use and cannot be reused after consumption"
    if "run expected a flow, received " in message:
        received = message.rsplit("received ", 1)[1]
        detail = f"Pipe mode stage must produce a flow; received {received}"
        if received in {"int", "float", "bool", "string", "list", "map"}:
            return (
                f"{detail}. Use -c/--command when you want a final value "
                "such as `collect |> sum` or `collect |> count`."
            )
        if received in {"some", "none"}:
            return (
                f"{detail}. Pipe mode expects a Flow stage, not a final Option value. "
                "Use keep_some(...), keep_some_else(...), per-item unwrap_or(...), or switch to -c/--command."
            )
        return detail
    if "stage received flow;" in message:
        stage_name = _extract_pipe_stage_name(message)
        if re.search(
            r"expected a (string|number|integer|bool), received flow\b",
            message,
        ):
            parts = [message]
            parts.append("Pipe mode passes a Flow through each stage, not one item at a time.")
            if stage_name:
                parts.append(f"Did you mean: map({stage_name}) or keep_some({stage_name})")
            else:
                parts.append("Wrap per-item functions with map(...) or keep_some(...).")
            return "\n".join(parts)
        if "expected a list, received flow" in message:
            parts = [message]
            parts.append("Pipe mode passes a Flow, not a materialized list.")
            if stage_name:
                parts.append(f"Did you mean: collect |> {stage_name}")
            parts.append("Or use -c/--command for the full pipeline.")
            return "\n".join(parts)
        return (
            f"{message}. Pipe mode stages receive a Flow, not one row at a time. "
            "Use Flow stages such as map(...), filter(...), head(...), each(...), or keep_some(...); "
            "use -c/--command for reducers such as sum or count."
        )
    if "received some" in message:
        return (
            f"{message}. "
            "If this stage is intentionally Option-aware, keep explicit helpers such as flat_map_some(...), map_some(...), or then_* in place."
        )
    return message
