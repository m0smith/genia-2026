"""
Normalization layer for Genia Python host adapter.
"""
from typing import Any

def _normalize_text(value: Any) -> str:
    text = value if isinstance(value, str) else str(value)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _normalize_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_value(value[key]) for key in sorted(value, key=str)}
    return type(value).__name__


def normalize_result(raw: dict, case) -> Any:
    return {
        "success": int(raw.get("exit_code", 0)) == 0,
        "stdout": _normalize_text(raw.get("stdout", "")),
        "stderr": _normalize_text(raw.get("stderr", "")),
        "exit_code": int(raw.get("exit_code", 0)),
        "result": _normalize_value(raw.get("result")),
        "error": _normalize_value(raw.get("error")),
        "ir": _normalize_value(raw.get("ir")),
    }
