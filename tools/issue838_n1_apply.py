from pathlib import Path


def replace(path: str, old: str, new: str, count: int | None = None) -> None:
    p = Path(path)
    text = p.read_text()
    n = text.count(old)
    if count is not None and n != count:
        raise SystemExit(f"{path}: expected {count} occurrences, found {n}: {old!r}")
    if n == 0:
        raise SystemExit(f"{path}: pattern not found: {old!r}")
    p.write_text(text.replace(old, new))


Path("src/genia/numeric_literals.py").write_text(
    '''from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class NumericLiteral:
    kind: str
    digits: str | None = None
    coefficient: str | None = None
    exponent: str | None = None

    def portable_payload(self) -> dict[str, str]:
        if self.kind == "integer":
            if self.digits is None:
                raise ValueError("integer numeric literal is missing digits")
            return {"kind": "integer", "digits": self.digits}
        if self.kind == "decimal":
            if self.coefficient is None or self.exponent is None:
                raise ValueError("decimal numeric literal is incomplete")
            return {
                "kind": "decimal",
                "coefficient": self.coefficient,
                "exponent": self.exponent,
            }
        raise ValueError(f"unsupported numeric literal kind {self.kind!r}")


def parse_numeric_literal(text: str) -> NumericLiteral:
    lower = text.lower()
    has_exp = "e" in lower
    if has_exp:
        significand, exp_text = lower.split("e", 1)
        source_exp = int(exp_text)
    else:
        significand = text
        source_exp = 0

    if "." not in significand and not has_exp:
        digits = significand.lstrip("0") or "0"
        return NumericLiteral("integer", digits=digits)

    if "." in significand:
        whole, frac = significand.split(".", 1)
    else:
        whole, frac = significand, ""
    coeff_digits = (whole + frac).lstrip("0") or "0"
    exponent = source_exp - len(frac)
    if coeff_digits == "0":
        return NumericLiteral("decimal", coefficient="0", exponent="0")
    while coeff_digits.endswith("0"):
        coeff_digits = coeff_digits[:-1]
        exponent += 1
    return NumericLiteral(
        "decimal",
        coefficient=coeff_digits,
        exponent=str(exponent),
    )


def is_portable_numeric_payload(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    kind = value.get("kind")
    if kind == "integer":
        return set(value) == {"kind", "digits"} and isinstance(value.get("digits"), str)
    if kind == "decimal":
        return (
            set(value) == {"kind", "coefficient", "exponent"}
            and isinstance(value.get("coefficient"), str)
            and isinstance(value.get("exponent"), str)
        )
    return False


def materialize_legacy_numeric(value: Any) -> Any:
    """Temporary N-1 compatibility bridge behind portable Core IR.

    N-1 changes source classification and portable representation only. The
    following runtime slice replaces this bridge with exact runtime values.
    """
    if isinstance(value, NumericLiteral):
        value = value.portable_payload()
    if not is_portable_numeric_payload(value):
        return value
    if value["kind"] == "integer":
        return int(value["digits"])
    coefficient = int(value["coefficient"])
    exponent = int(value["exponent"])
    exact_decimal = Decimal(coefficient).scaleb(exponent)
    return float(exact_decimal)
'''
)

replace(
    "src/genia/lexer.py",
    '("NUMBER", r"\\d+(?:\\.\\d+)?"),',
    '("NUMBER", r"\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?"),',
    1,
)
replace(
    "src/genia/lexer.py",
    'NUMBER_RE = re.compile(r"\\d+(?:\\.\\d+)?")',
    'NUMBER_RE = re.compile(r"\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?")',
    1,
)
replace(
    "src/genia/lexer.py",
    '''        if number_match is not None:\n            text = number_match.group()\n            tokens.append(Token("NUMBER", text, pos))\n            pos += len(text)\n            continue\n''',
    '''        if number_match is not None:\n            text = number_match.group()\n            end = pos + len(text)\n            if end < length and source[end] in "eE":\n                raise SyntaxError(f"Invalid numeric exponent at {end}")\n            tokens.append(Token("NUMBER", text, pos))\n            pos = end\n            continue\n''',
    1,
)

replace(
    "src/genia/ast_nodes.py",
    "from typing import Any, Optional\n",
    "from typing import Any, Optional\n\nfrom .numeric_literals import NumericLiteral\n",
    1,
)
replace("src/genia/ast_nodes.py", "    value: int | float\n", "    value: NumericLiteral\n", 1)

replace(
    "src/genia/parser.py",
    "from .lexer import Token, SourceSpan, parse_string_literal, parse_glob_literal\n",
    "from .lexer import Token, SourceSpan, parse_string_literal, parse_glob_literal\nfrom .numeric_literals import parse_numeric_literal\n",
    1,
)
replace(
    "src/genia/parser.py",
    'Number(float(tok.text) if "." in tok.text else int(tok.text), span=self.span_for_tokens(tok, tok))',
    "Number(parse_numeric_literal(tok.text), span=self.span_for_tokens(tok, tok))",
    3,
)

replace(
    "src/genia/lowering.py",
    "return IrLiteral(node.value, span=node.span)",
    "return IrLiteral(node.value.portable_payload(), span=node.span)",
    1,
)
replace(
    "src/genia/lowering.py",
    "return IrPatLiteral(pattern.value)",
    "return IrPatLiteral(pattern.value.portable_payload())",
    1,
)

replace(
    "hosts/python/parse_adapter.py",
    "return {'kind': 'Literal', 'value': getattr(node, 'value', None)}",
    "return {'kind': 'Literal', 'value': getattr(node, 'value').portable_payload()}",
    1,
)
replace(
    "hosts/python/parse_adapter.py",
    "    if node_type == 'Var':\n",
    "    if node_type == 'Unary':\n        return {'kind': 'Unary', 'op': getattr(node, 'op', None), 'expr': normalize_ast(getattr(node, 'expr', None))}\n    if node_type == 'Var':\n",
    1,
)

replace(
    "hosts/python/ir_normalize.py",
    'return {"kind": "Literal", "value": expr.value}\n    if isinstance(expr, Boolean):',
    'return {"kind": "Literal", "value": expr.value.portable_payload()}\n    if isinstance(expr, Boolean):',
    1,
)

for branch_import in (
    "    from genia.utf8 import format_debug, format_display\n",
    "    from .utf8 import format_debug, format_display\n",
):
    helper_import = (
        "    from genia.numeric_literals import materialize_legacy_numeric\n"
        if "genia.utf8" in branch_import
        else "    from .numeric_literals import materialize_legacy_numeric\n"
    )
    replace("src/genia/evaluator.py", branch_import, branch_import + helper_import, 1)
replace(
    "src/genia/evaluator.py",
    "        if isinstance(node, IrLiteral):\n            return node.value\n",
    "        if isinstance(node, IrLiteral):\n            return materialize_legacy_numeric(node.value)\n",
    1,
)
replace(
    "src/genia/evaluator.py",
    "    if isinstance(node, Number):\n        return node.value\n",
    "    if isinstance(node, Number):\n        return materialize_legacy_numeric(node.value)\n",
    1,
)
replace(
    "src/genia/evaluator.py",
    "    if isinstance(pattern, Number):\n        return pattern.value\n",
    "    if isinstance(pattern, Number):\n        return materialize_legacy_numeric(pattern.value)\n",
    1,
)
replace(
    "src/genia/evaluator.py",
    "        if isinstance(node, IrLiteral):\n            return format_debug(node.value)\n",
    "        if isinstance(node, IrLiteral):\n            return format_debug(materialize_legacy_numeric(node.value))\n",
    1,
)

p = Path("src/genia/pattern_match.py")
text = p.read_text()
if "numeric_literals import materialize_legacy_numeric" not in text:
    if "from .equality import genia_equal" in text:
        text = text.replace(
            "from .equality import genia_equal",
            "from .equality import genia_equal\nfrom .numeric_literals import materialize_legacy_numeric",
        )
    elif "from genia.equality import genia_equal" in text:
        text = text.replace(
            "from genia.equality import genia_equal",
            "from genia.equality import genia_equal\nfrom genia.numeric_literals import materialize_legacy_numeric",
        )
    else:
        raise SystemExit("pattern_match.py equality import not found")
old = "if isinstance(pattern, IrPatLiteral):\n        return {} if genia_equal(pattern.value, arg) else None"
if old not in text:
    raise SystemExit("pattern_match literal branch not found")
text = text.replace(
    old,
    "if isinstance(pattern, IrPatLiteral):\n        expected = materialize_legacy_numeric(pattern.value)\n        return {} if genia_equal(expected, arg) else None",
)
p.write_text(text)

# TEST-phase migration of existing unit expectations to the approved tagged
# portable numeric payload. The implementation workflow does not commit tests;
# these rewrites only keep the focused regression execution aligned with the
# separately committed N-1 contract/test migration.
replace(
    "tests/unit/test_ir.py",
    "assert expr_stmt.expr.source.value == 3",
    'assert expr_stmt.expr.source.value == {"kind": "integer", "digits": "3"}',
    1,
)
replace(
    "tests/unit/test_ir.py",
    "assert expr_stmt.expr.items[0].value.value == 1",
    'assert expr_stmt.expr.items[0].value.value == {"kind": "integer", "digits": "1"}',
    1,
)
replace(
    "tests/unit/test_ir.py",
    "assert first.items[0].value == 0",
    'assert first.items[0].value == {"kind": "integer", "digits": "0"}',
    1,
)
replace(
    "tests/unit/test_ir.py",
    "assert expr_stmt.expr.left.value == 10",
    'assert expr_stmt.expr.left.value == {"kind": "integer", "digits": "10"}',
    1,
)
replace(
    "tests/unit/test_ir.py",
    "assert expr_stmt.expr.right.value == 2",
    'assert expr_stmt.expr.right.value == {"kind": "integer", "digits": "2"}',
    1,
)
