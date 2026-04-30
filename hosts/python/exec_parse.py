"""Parse-only execution for Genia Python host adapter."""

from .parse_adapter import parse_and_normalize


def exec_parse(case) -> dict:
    if isinstance(case.input, dict):
        source = case.input["source"]
    else:
        source = case.input
    return parse_and_normalize(source)
