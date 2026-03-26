from __future__ import annotations

import json
from typing import Any, TextIO


def read_json_line(stream: TextIO) -> dict[str, Any] | None:
    line = stream.readline()
    if line == "":
        return None
    text = line.strip()
    if not text:
        return {}
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Debug command must be a JSON object")
    return value


def write_json_line(stream: TextIO, payload: dict[str, Any]) -> None:
    stream.write(json.dumps(payload, separators=(",", ":")) + "\n")
    stream.flush()
