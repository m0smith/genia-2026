from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from hosts.python import parse_and_normalize
from hosts.python.exec_cli import exec_cli
from hosts.python.exec_eval import run_eval_subprocess
from hosts.python.exec_flow import exec_flow
from hosts.python.exec_ir import exec_ir

from .loader import LoadedSpec


@dataclass(frozen=True)
class ActualResult:
    stdout: str | None = None
    stderr: str | None = None
    exit_code: int | None = None
    ir: object | None = None
    parse: object | None = None


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _strip_trailing_newlines(text: str) -> str:
    return text.rstrip("\n")


def execute_spec(spec: LoadedSpec) -> ActualResult:
    if spec.category == "parse":
        result = parse_and_normalize(spec.source)
        return ActualResult(parse=result)

    if spec.category == "ir":
        result = exec_ir(SimpleNamespace(input={"source": spec.source}, stdin=None))
        return ActualResult(ir=result["ir"])

    if spec.category == "cli":
        result = exec_cli(spec)
        return ActualResult(
            stdout=_strip_trailing_newlines(_normalize_text(result["stdout"])),
            stderr=_strip_trailing_newlines(_normalize_text(result["stderr"])),
            exit_code=result["exit_code"],
        )

    if spec.category == "flow":
        result = exec_flow(spec)
        return ActualResult(
            stdout=_normalize_text(result["stdout"]),
            stderr=_normalize_text(result["stderr"]),
            exit_code=result["exit_code"],
        )

    result = run_eval_subprocess(spec.source, spec.stdin or None)
    return ActualResult(
        stdout=_normalize_text(result["stdout"]),
        stderr=_normalize_text(result["stderr"]),
        exit_code=result["exit_code"],
    )
