from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from hosts.python.exec_eval import run_eval_subprocess
from hosts.python.exec_ir import exec_ir

from .loader import LoadedSpec


@dataclass(frozen=True)
class ActualResult:
    stdout: str | None = None
    stderr: str | None = None
    exit_code: int | None = None
    ir: object | None = None


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def execute_spec(spec: LoadedSpec) -> ActualResult:
    if spec.category == "ir":
        result = exec_ir(SimpleNamespace(input={"source": spec.source}, stdin=None))
        return ActualResult(ir=result["ir"])

    result = run_eval_subprocess(spec.source, spec.stdin or None)
    return ActualResult(
        stdout=_normalize_text(result["stdout"]),
        stderr=_normalize_text(result["stderr"]),
        exit_code=result["exit_code"],
    )
