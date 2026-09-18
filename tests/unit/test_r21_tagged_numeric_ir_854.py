"""E21-2 (issue #854): tagged portable numeric IrLiteral payloads.

Covers docs/design/r21-numeric-source-portable-representation-contract.md
section 4: numeric source lowers through the existing IrLiteral node with a
canonical tagged payload, unary minus stays outside the payload, and / stays
ordinary IrBinary(op=SLASH). No new Core IR node family is introduced.

The evaluator-compatibility-shim tests below were updated by R22 E22-1
(issue #887): that ticket retires the float() shim for Decimal payloads
and replaces it with genuine GeniaDecimal runtime materialization per
docs/design/r22-exact-numeric-runtime-contract.md section 2, exactly as
this module's own R21 docstring anticipated ("This is a pure
compatibility shim required by E21-2 ... It introduces no new runtime
numeric kind" -- E22-1 is the ticket that introduces it).
"""
from __future__ import annotations

from src.genia.ast_nodes import Number
from src.genia.ir import IrBinary, IrLiteral, IrUnary
from src.genia.lexer import lex
from src.genia.lowering import lower_node
from src.genia.numeric_runtime import GeniaDecimal
from src.genia.numeric_source import numeric_literal_payload, numeric_literal_runtime_value
from src.genia.parser import Parser


def _lower_expr(source: str):
    tokens = lex(source)
    parser = Parser(tokens, source=source, filename="<test>")
    program = parser.parse_program()
    node = program[0]
    node = getattr(node, "expr", node)
    return lower_node(node)


# ---------------------------------------------------------------------------
# numeric_literal_payload
# ---------------------------------------------------------------------------

def test_integer_payload_shape() -> None:
    n = Number(42, source_kind="integer", digits="42")
    assert numeric_literal_payload(n) == {"kind": "integer", "digits": "42"}


def test_decimal_payload_shape() -> None:
    n = Number(1.25, source_kind="decimal", coefficient="125", exponent="-2")
    assert numeric_literal_payload(n) == {"kind": "decimal", "coefficient": "125", "exponent": "-2"}


def test_huge_integer_payload_preserves_exact_digits() -> None:
    huge = "123456789012345678901234567890"
    n = Number(int(huge), source_kind="integer", digits=huge)
    assert numeric_literal_payload(n) == {"kind": "integer", "digits": huge}


def test_equivalent_decimal_spellings_produce_identical_payload() -> None:
    a = Number(1.0, source_kind="decimal", coefficient="1", exponent="0")
    b = Number(1.0, source_kind="decimal", coefficient="1", exponent="0")
    assert numeric_literal_payload(a) == numeric_literal_payload(b)


# ---------------------------------------------------------------------------
# numeric_literal_runtime_value (evaluator compatibility shim)
# ---------------------------------------------------------------------------

def test_runtime_value_integer_roundtrip() -> None:
    assert numeric_literal_runtime_value({"kind": "integer", "digits": "42"}) == 42
    assert isinstance(numeric_literal_runtime_value({"kind": "integer", "digits": "42"}), int)


def test_runtime_value_decimal_roundtrip() -> None:
    value = numeric_literal_runtime_value({"kind": "decimal", "coefficient": "125", "exponent": "-2"})
    assert isinstance(value, GeniaDecimal)
    assert value.coefficient == 125
    assert value.exponent == -2


def test_runtime_value_huge_integer_exact() -> None:
    huge = "123456789012345678901234567890"
    assert numeric_literal_runtime_value({"kind": "integer", "digits": huge}) == int(huge)


def test_no_function_in_module_calls_float() -> None:
    """float() must never appear in numeric_source.py.

    R22 E22-1 retires the evaluator-compatibility shim that used to call
    float() for Decimal payloads; Decimal materialization now goes
    through GeniaDecimal exclusively (int()-only, never float())."""
    import ast
    import inspect

    import src.genia.numeric_source as module

    tree = ast.parse(inspect.getsource(module))
    module_level_functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    functions_calling_float = []
    for fn in module_level_functions:
        calls = [
            node
            for node in ast.walk(fn)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "float"
        ]
        if calls:
            functions_calling_float.append(fn.name)
    assert functions_calling_float == []


# ---------------------------------------------------------------------------
# Lowering: Number -> IrLiteral with tagged payload
# ---------------------------------------------------------------------------

def test_lowering_integer_literal() -> None:
    ir = _lower_expr("42")
    assert isinstance(ir, IrLiteral)
    assert ir.value == {"kind": "integer", "digits": "42"}


def test_lowering_decimal_dotted_literal() -> None:
    ir = _lower_expr("1.25")
    assert isinstance(ir, IrLiteral)
    assert ir.value == {"kind": "decimal", "coefficient": "125", "exponent": "-2"}


def test_lowering_decimal_exponent_only_literal() -> None:
    ir = _lower_expr("1e3")
    assert isinstance(ir, IrLiteral)
    assert ir.value == {"kind": "decimal", "coefficient": "1", "exponent": "3"}


def test_lowering_huge_integer_literal_exact_digits() -> None:
    huge = "123456789012345678901234567890"
    ir = _lower_expr(huge)
    assert isinstance(ir, IrLiteral)
    assert ir.value == {"kind": "integer", "digits": huge}


def test_lowering_equivalent_decimal_spellings_identical_payload() -> None:
    ir1 = _lower_expr("1.00")
    ir2 = _lower_expr("100e-2")
    assert ir1.value == ir2.value == {"kind": "decimal", "coefficient": "1", "exponent": "0"}


def test_lowering_unary_negative_wraps_positive_tagged_literal() -> None:
    ir = _lower_expr("-1.25")
    assert isinstance(ir, IrUnary)
    assert ir.op == "MINUS"
    assert isinstance(ir.expr, IrLiteral)
    assert ir.expr.value == {"kind": "decimal", "coefficient": "125", "exponent": "-2"}


def test_lowering_slash_remains_ordinary_binary() -> None:
    ir = _lower_expr("10 / 2")
    assert isinstance(ir, IrBinary)
    assert ir.op == "SLASH"
    assert ir.left.value == {"kind": "integer", "digits": "10"}
    assert ir.right.value == {"kind": "integer", "digits": "2"}


def test_lowering_no_host_native_float_in_payload() -> None:
    """The tagged payload must contain only strings, never a Python float."""
    ir = _lower_expr("1.25e-2")
    for v in ir.value.values():
        assert not isinstance(v, float)


# ---------------------------------------------------------------------------
# Evaluator: unchanged observable numeric behavior
# ---------------------------------------------------------------------------

def test_eval_integer_literal_unchanged() -> None:
    from genia import make_global_env, run_source

    assert run_source("42", make_global_env()) == 42


def test_eval_decimal_literal_materializes_genia_decimal() -> None:
    # `genia` (not `src.genia`) is the namespace run_source is loaded
    # under here, matching the rest of this test's existing convention;
    # compare structurally rather than via `src.genia`-imported isinstance
    # to avoid a spurious dual-namespace class-identity mismatch.
    from genia import make_global_env, run_source

    value = run_source("1.25", make_global_env())
    assert type(value).__name__ == "GeniaDecimal"
    assert value.coefficient == 125
    assert value.exponent == -2


def test_eval_decimal_exponent_literal_materializes_genia_decimal() -> None:
    from genia import make_global_env, run_source

    value = run_source("1e3", make_global_env())
    assert type(value).__name__ == "GeniaDecimal"
    assert value.coefficient == 1
    assert value.exponent == 3


def test_eval_arithmetic_over_decimal_and_integer_literals() -> None:
    from genia import make_global_env, run_source

    assert run_source("1 + 2", make_global_env()) == 3
    sum_value = run_source("1.5 + 2.5", make_global_env())
    assert type(sum_value).__name__ == "GeniaDecimal"
    assert sum_value.coefficient == 4
    assert sum_value.exponent == 0
    assert run_source("10 / 2", make_global_env()) == 5.0
