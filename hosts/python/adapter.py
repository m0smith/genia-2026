"""
Python Host Adapter for Genia Shared Spec Contract

Implements: run_case(case: SpecCase) -> SpecResult

- Category-specific execution paths
- Normalization layer
- Thin bridge to src/genia/interpreter.py
"""
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Optional, List, Literal, Union

from .exec_parse import exec_parse
from .exec_ir import exec_ir
from .exec_eval import exec_eval
from .exec_cli import exec_cli
from .exec_flow import exec_flow
from .normalize import normalize_result

@dataclass
class SpecCase:
    id: str
    category: Literal["parse", "ir", "eval", "cli", "flow", "error"]
    input: Union[str, dict]
    args: Optional[List[str]] = None
    stdin: Optional[str] = None
    expected: Optional[dict] = None

@dataclass
class SpecResult:
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    result: Optional[Any] = None
    error: Optional[dict] = None
    ir: Optional[dict] = None


def run_case(case: SpecCase) -> SpecResult:
    """
    Dispatches a spec case to the correct execution path and normalizes the result.
    """
    if case.category == "parse":
        raw = exec_parse(case)
    elif case.category == "ir":
        raw = exec_ir(case)
    elif case.category == "eval":
        raw = exec_eval(case)
    elif case.category == "cli":
        if not isinstance(case.input, dict):
            raise TypeError("cli case input must be a mapping")
        raw = exec_cli(
            SimpleNamespace(
                file=case.input.get("file"),
                command=case.input.get("command"),
                stdin=case.input.get("stdin", ""),
                argv=case.input.get("argv", []),
                debug_stdio=case.input.get("debug_stdio", False),
            )
        )
    elif case.category == "flow":
        raw = exec_flow(case)
    elif case.category == "error":
        raw = exec_eval(case)  # error cases use eval path, expect error normalization
    else:
        raise ValueError(f"Unknown spec case category: {case.category}")
    return normalize_result(raw, case)
