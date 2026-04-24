"""
IR generation execution for Genia Python host adapter.
"""

from genia.interpreter import Parser, lex, lower_program

from .ir_normalize import normalize_portable_ir


def exec_ir(case) -> dict:
    if isinstance(case.input, str):
        source = case.input
    elif isinstance(case.input, dict):
        source = case.input.get("source")
        if not isinstance(source, str):
            raise TypeError("ir case input.source must be a string")
    else:
        raise TypeError("ir case input must be a string or mapping")

    ast_nodes = Parser(lex(source)).parse_program()
    lowered = lower_program(ast_nodes)
    return {"ir": normalize_portable_ir(lowered)}
