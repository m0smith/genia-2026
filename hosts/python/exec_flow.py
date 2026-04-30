"""
Flow/pipe-mode execution for Genia Python host adapter.
"""

from .exec_eval import run_eval_subprocess


def exec_flow(case) -> dict:
    source = getattr(case, "source", None)
    if not isinstance(source, str):
        input_data = getattr(case, "input", None)
        if isinstance(input_data, str):
            source = input_data
        elif isinstance(input_data, dict):
            source = input_data.get("source")
            if not isinstance(source, str):
                raise TypeError("flow case input.source must be a string")
        else:
            raise TypeError("flow case source must be a string")

    stdin = getattr(case, "stdin", None)
    if stdin is not None and not isinstance(stdin, str):
        raise TypeError("flow case stdin must be a string when present")

    return run_eval_subprocess(source, stdin or None)
