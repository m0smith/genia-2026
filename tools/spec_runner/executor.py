from __future__ import annotations

from dataclasses import dataclass

from hosts.python.exec_eval import run_eval_subprocess

from .loader import LoadedSpec


@dataclass(frozen=True)
class ActualResult:
    stdout: str
    stderr: str
    exit_code: int


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def execute_spec(spec: LoadedSpec) -> ActualResult:
    result = run_eval_subprocess(spec.source, spec.stdin or None)
    return ActualResult(
        stdout=_normalize_text(result["stdout"]),
        stderr=_normalize_text(result["stderr"]),
        exit_code=result["exit_code"],
    )
