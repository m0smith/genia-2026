"""
Normalization layer for Genia Python host adapter.
"""
from typing import Any

def normalize_result(raw: dict, case) -> Any:
    # TODO: Normalize stdout, stderr, exit_code, result, ir, error
    # Example normalization (stub):
    return {
        "success": True,
        "stdout": raw.get("stdout", ""),
        "stderr": raw.get("stderr", ""),
        "exit_code": raw.get("exit_code", 0),
        "result": raw.get("result"),
        "error": raw.get("error"),
        "ir": raw.get("ir"),
    }
