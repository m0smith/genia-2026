# Minimal Python parse adapter for shared parse contract
# All normalization logic is here. No raw AST escapes.

from src.genia.interpreter import lex, Parser  # Correct parser import for Genia parse contract

# Contract-defined AST projection

def normalize_ast(node):
    # Deterministic, idempotent projection to contract shape
    if isinstance(node, list):
        # For parse_program, return the first node for single-statement programs
        if len(node) == 1:
            return normalize_ast(node[0])
        # If multiple nodes, return a list of normalized nodes (not expected in current contract)
        return [normalize_ast(n) for n in node]
    if node is None:
        return None
    # Map Genia AST class names to contract kinds
    node_type = type(node).__name__
    if node_type == 'ExprStmt':
        # Unwrap expression statements to their inner expression
        return normalize_ast(getattr(node, 'expr', None))
    if node_type == 'Number':
        return {'kind': 'Literal', 'value': getattr(node, 'value', None)}
    if node_type == 'Var':
        return {'kind': 'Var', 'name': getattr(node, 'name', None)}
    if node_type == 'Assign':
        return {
            'kind': 'Assign',
            'name': getattr(node, 'name', None),
            'value': normalize_ast(getattr(node, 'expr', None))
        }
    if node_type == 'FuncDef':
        # Params: ordered list of parameter names (no rest param for contract)
        params = list(getattr(node, 'params', []))
        # Only plain names, no extra structure
        params = [str(p) for p in params]
        # Normalize body to contract shape only
        body = normalize_ast(getattr(node, 'body', None))
        return {
            'kind': 'FuncDef',
            'name': getattr(node, 'name', None),
            'params': params,
            'body': body
        }
    if node_type == 'Binary':
        op_symbol_map = {
            'PLUS': '+',
            'MINUS': '-',
            'STAR': '*',
            'SLASH': '/',
            'PERCENT': '%',
            'LT': '<',
            'LE': '<=',
            'GT': '>',
            'GE': '>=',
            'EQEQ': '==',
            'NE': '!=',
            'AND': '&&',
            'OR': '||',
            'PIPE_FWD': '|>',
        }
        op = getattr(node, 'op', None)
        op_str = op_symbol_map.get(op, op)
        return {
            'kind': 'Binary',
            'op': op_str,
            'left': normalize_ast(getattr(node, 'left', None)),
            'right': normalize_ast(getattr(node, 'right', None))
        }
    # Add more node kinds as contract expands
    # Fallback: only include kind
    return {'kind': node_type}


def parse_and_normalize(source, filename="<memory>"):
    try:
        tokens = lex(source)
        parser = Parser(tokens, source=source, filename=filename)
        ast = parser.parse_program()
        return {"kind": "ok", "ast": normalize_ast(ast)}
    except Exception as e:
        etype = type(e).__name__
        msg = str(e)
        return {"kind": "error", "type": etype, "message": msg}
