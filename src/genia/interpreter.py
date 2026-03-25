#!/usr/bin/env python3
"""
Minimal Genia REPL / interpreter prototype.

Need to implement soon:
And I would say this requires:

- list values
- list patterns
- wildcard _
- rest pattern ..
- recursion

Implemented subset:
- numbers, booleans, nil, strings
- arithmetic: + - * / %
- comparison: < <= > >= == !=
- variables and function calls
- function definitions: name(args) = expr
- function definitions with blocks: name(args) { ... }
- case expressions in function bodies and as final expression in blocks
- pattern matching against the full argument tuple
- single-argument pattern shorthand: 0 -> 1 is treated like (0) -> 1
- guards: pattern ? condition -> result
- blocks with newline or ; expression separators
- builtins: log(...), help()

Not yet implemented:
- lambdas
- lists/maps/destructuring beyond tuple-parameter patterns
- pipelines
- member access / indexing
- modules
"""
from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Optional


# -----------------------------
# Lexer
# -----------------------------

TOKEN_SPEC = [
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("STRING", r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\''),
    ("ARROW", r"->"),
    ("EQEQ", r"=="),
    ("NE", r"!="),
    ("LE", r"<="),
    ("GE", r">="),
    ("AND", r"&&"),
    ("OR", r"\|\|"),
    ("ASSIGN", r"="),
    ("LT", r"<"),
    ("GT", r">"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("STAR", r"\*"),
    ("SLASH", r"/"),
    ("PERCENT", r"%"),
    ("BANG", r"!"),
    ("QMARK", r"\?"),
    ("PIPE", r"\|"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("LBRACK", r"\["),
    ("RBRACK", r"\]"),
    ("DOTDOT", r"\.\."),
    ("COMMA", r","),
    ("SEMI", r";"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t\r]+"),
    ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("MISMATCH", r"."),
]
TOKEN_RE = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))


@dataclass
class Token:
    kind: str
    text: str
    pos: int


def lex(source: str) -> list[Token]:
    tokens: list[Token] = []
    for m in TOKEN_RE.finditer(source):
        kind = m.lastgroup
        text = m.group()
        if kind == "SKIP":
            continue
        if kind == "MISMATCH":
            raise SyntaxError(f"Unexpected character {text!r} at {m.start()}")
        tokens.append(Token(kind, text, m.start()))
    tokens.append(Token("EOF", "", len(source)))
    return tokens


# -----------------------------
# AST
# -----------------------------

class Node:
    pass


@dataclass
class Number(Node):
    value: int | float


@dataclass
class String(Node):
    value: str


@dataclass
class Boolean(Node):
    value: bool


@dataclass
class Nil(Node):
    pass


@dataclass
class Var(Node):
    name: str


@dataclass
class Unary(Node):
    op: str
    expr: Node


@dataclass
class Binary(Node):
    left: Node
    op: str
    right: Node


@dataclass
class Call(Node):
    fn: Node
    args: list[Node]


@dataclass
class ExprStmt(Node):
    expr: Node


@dataclass
class Block(Node):
    exprs: list[Node]


@dataclass
class ListLiteral(Node):
    items: list[Node]


@dataclass
class ListPattern(Node):
    items: list[Node]


@dataclass
class WildcardPattern(Node):
    pass


@dataclass
class RestPattern(Node):
    name: str | None


@dataclass
class TuplePattern(Node):
    items: list[Node]


@dataclass
class CaseClause(Node):
    pattern: Node
    guard: Optional[Node]
    result: Node


@dataclass
class CaseExpr(Node):
    clauses: list[CaseClause]


@dataclass
class Lambda(Node):
    params: list[str]
    body: Node


@dataclass
class Assign(Node):
    name: str
    expr: Node


@dataclass
class FuncDef(Node):
    name: str
    params: list[str]
    body: Node


# -----------------------------
# Parser
# -----------------------------

PRECEDENCE = {
    "OR": 10,
    "AND": 20,
    "EQEQ": 30,
    "NE": 30,
    "LT": 40,
    "LE": 40,
    "GT": 40,
    "GE": 40,
    "PLUS": 50,
    "MINUS": 50,
    "STAR": 60,
    "SLASH": 60,
    "PERCENT": 60,
}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self, offset: int = 0) -> Token:
        return self.tokens[self.i + offset]

    def at(self, *kinds: str) -> bool:
        return self.peek().kind in kinds

    def eat(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise SyntaxError(f"Expected {kind}, got {tok.kind} at {tok.pos}")
        self.i += 1
        return tok

    def maybe(self, kind: str) -> Optional[Token]:
        if self.at(kind):
            return self.eat(kind)
        return None

    def skip_separators(self) -> None:
        while self.at("NEWLINE", "SEMI"):
            self.i += 1

    def parse_program(self) -> list[Node]:
        out: list[Node] = []
        self.skip_separators()
        while not self.at("EOF"):
            out.append(self.parse_toplevel())
            self.skip_separators()
        return out

    def try_parse_function_header(self) -> tuple[str, list[str]] | None:
        if not (self.at("IDENT") and self.peek(1).kind == "LPAREN"):
            return None

        save = self.i
        try:
            name = self.eat("IDENT").text
            self.eat("LPAREN")
            params: list[str] = []
            if not self.at("RPAREN"):
                while True:
                    params.append(self.eat("IDENT").text)
                    if not self.maybe("COMMA"):
                        break
            self.eat("RPAREN")

            if self.at("ASSIGN", "LBRACE"):
                return name, params

            self.i = save
            return None
        except SyntaxError:
            self.i = save
            return None

    def parse_toplevel(self) -> Node:
        header = self.try_parse_function_header()
        if header is not None:
            name, params = header

            if self.at("ASSIGN"):
                self.eat("ASSIGN")
                self.skip_separators()
                body = self.parse_function_body_after_intro()
                return FuncDef(name, params, body)

            if self.at("LBRACE"):
                body = self.parse_block(allow_final_case=True)
                return FuncDef(name, params, body)

            raise SyntaxError("Internal parser error: expected function body")

        if self.at("IDENT") and self.peek(1).kind == "ASSIGN":
            name = self.eat("IDENT").text
            self.eat("ASSIGN")
            self.skip_separators()
            expr = self.parse_expr()
            return Assign(name, expr)

        expr = self.parse_expr()
        return ExprStmt(expr)

    def parse_function_body_after_intro(self) -> Node:
        if self.looks_like_case_start():
            return self.parse_case_expr(single_param_shorthand_ok=True)
        return self.parse_expr()

    def parse_block(self, allow_final_case: bool) -> Block:
        self.eat("LBRACE")
        exprs: list[Node] = []
        self.skip_separators()
        while not self.at("RBRACE"):
            if allow_final_case and self.looks_like_case_start():
                case_expr = self.parse_case_expr(single_param_shorthand_ok=True)
                exprs.append(case_expr)
                self.skip_separators()
                if not self.at("RBRACE"):
                    raise SyntaxError("Case expression must be final in a block")
                break
            exprs.append(self.parse_expr())
            self.skip_separators()
        self.eat("RBRACE")
        return Block(exprs)

    def looks_like_case_start(self) -> bool:
        # single param shorthand cases: 0 ->, name ->, [x, y] ->, name ? ... ->
        # tuple case: ( ... ) ->
        # We only detect enough for v0.1.
        if self.at("NUMBER", "STRING", "IDENT"):
            j = self.i + 1
            while self.tokens[j].kind == "NEWLINE":
                j += 1
            if self.tokens[j].kind in {"ARROW", "QMARK"}:
                return True
        if self.at("LPAREN", "LBRACK"):
            open_kind = self.peek().kind
            close_kind = "RPAREN" if open_kind == "LPAREN" else "RBRACK"
            depth = 0
            j = self.i
            while True:
                tok = self.tokens[j]
                if tok.kind == open_kind:
                    depth += 1
                elif tok.kind == close_kind:
                    depth -= 1
                    if depth == 0:
                        j += 1
                        while self.tokens[j].kind == "NEWLINE":
                            j += 1
                        return self.tokens[j].kind in {"ARROW", "QMARK"}
                elif tok.kind == "EOF":
                    return False
                j += 1
        return False

    def parse_case_expr(self, single_param_shorthand_ok: bool) -> CaseExpr:
        clauses = [self.parse_case_clause(single_param_shorthand_ok)]
        while self.maybe("PIPE"):
            self.skip_separators()
            clauses.append(self.parse_case_clause(single_param_shorthand_ok))
        return CaseExpr(clauses)

    def parse_case_clause(self, single_param_shorthand_ok: bool) -> CaseClause:
        pattern = self.parse_pattern(single_param_shorthand_ok)
        guard = None
        if self.maybe("QMARK"):
            guard = self.parse_expr()
        self.eat("ARROW")
        result = self.parse_expr()
        return CaseClause(pattern, guard, result)

    def parse_pattern(self, single_param_shorthand_ok: bool) -> Node:
        if self.at("LPAREN"):
            self.eat("LPAREN")
            items: list[Node] = []
            if not self.at("RPAREN"):
                while True:
                    items.append(self.parse_pattern_atom())
                    if not self.maybe("COMMA"):
                        break
            self.eat("RPAREN")
            return TuplePattern(items)
        atom = self.parse_pattern_atom()
        if single_param_shorthand_ok:
            return atom
        return TuplePattern([atom])

    def parse_pattern_atom(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text))
        if tok.kind == "STRING":
            self.i += 1
            return String(eval(tok.text))
        if tok.kind == "DOTDOT":
            self.i += 1
            if self.at("IDENT"):
                name = self.eat("IDENT").text
                if name == "_":
                    return RestPattern(None)
                return RestPattern(name)
            return RestPattern(None)
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True)
            if tok.text == "false":
                return Boolean(False)
            if tok.text == "nil":
                return Nil()
            if tok.text == "_":
                return WildcardPattern()
            return Var(tok.text)
        if tok.kind == "LBRACK":
            self.i += 1
            items: list[Node] = []
            saw_rest = False
            if not self.at("RBRACK"):
                while True:
                    item = self.parse_pattern_atom()
                    if saw_rest:
                        raise SyntaxError("..rest must be the final item in a list pattern")
                    items.append(item)
                    if isinstance(item, RestPattern):
                        saw_rest = True
                    if not self.maybe("COMMA"):
                        break
            self.eat("RBRACK")
            return ListPattern(items)
        raise SyntaxError(f"Invalid pattern at {tok.pos}")

    def parse_expr(self, min_prec: int = 0) -> Node:
        left = self.parse_prefix()
        while True:
            tok = self.peek()
            if tok.kind == "LPAREN":
                left = self.finish_call(left)
                continue
            prec = PRECEDENCE.get(tok.kind)
            if prec is None or prec < min_prec:
                break
            op = tok.kind
            self.i += 1
            right = self.parse_expr(prec + 1)
            left = Binary(left, op, right)
        return left

    def parse_prefix(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text))
        if tok.kind == "STRING":
            self.i += 1
            return String(eval(tok.text))
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True)
            if tok.text == "false":
                return Boolean(False)
            if tok.text == "nil":
                return Nil()
            return Var(tok.text)
        if tok.kind in ("MINUS", "BANG"):
            self.i += 1
            return Unary(tok.kind, self.parse_expr(70))
        if tok.kind == "LPAREN":
            save = self.i
            try:
                self.i += 1
                params: list[str] = []
                if not self.at("RPAREN"):
                    while True:
                        params.append(self.eat("IDENT").text)
                        if not self.maybe("COMMA"):
                            break
                self.eat("RPAREN")
                if self.at("ARROW"):
                    self.eat("ARROW")
                    body = self.parse_expr()
                    return Lambda(params, body)
                self.i = save
            except SyntaxError:
                self.i = save

            self.i += 1
            expr = self.parse_expr()
            self.eat("RPAREN")
            return expr
        if tok.kind == "LBRACK":
            return self.parse_list_literal()
        if tok.kind == "LBRACE":
            return self.parse_block(allow_final_case=False)
        raise SyntaxError(f"Unexpected token {tok.kind} at {tok.pos}")

    def parse_list_literal(self) -> ListLiteral:
        self.eat("LBRACK")
        items: list[Node] = []
        if not self.at("RBRACK"):
            while True:
                items.append(self.parse_expr())
                if not self.maybe("COMMA"):
                    break
        self.eat("RBRACK")
        return ListLiteral(items)

    def finish_call(self, fn: Node) -> Node:
        self.eat("LPAREN")
        args: list[Node] = []
        if not self.at("RPAREN"):
            while True:
                args.append(self.parse_expr())
                if not self.maybe("COMMA"):
                    break
        self.eat("RPAREN")
        return Call(fn, args)


# -----------------------------
# Runtime
# -----------------------------

class Env:
    def __init__(self, parent: Optional[Env] = None):
        self.parent = parent
        self.values: dict[str, Any] = {}

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise NameError(f"Undefined name: {name}")

    def set(self, name: str, value: Any) -> None:
        self.values[name] = value

    def define_function(self, fn: "GeniaFunction") -> None:
        existing = self.values.get(fn.name)
        if existing is None:
            self.values[fn.name] = {fn.arity: fn}
            return
        if not isinstance(existing, dict) or not all(isinstance(k, int) for k in existing):
            raise TypeError(f"Cannot define function {fn.name}/{fn.arity}: name already bound to non-function value")
        if fn.arity in existing:
            raise TypeError(f"Duplicate function definition: {fn.name}/{fn.arity}")
        existing[fn.arity] = fn


@dataclass
class GeniaFunction:
    name: str
    params: list[str]
    body: Node
    closure: Env

    @property
    def arity(self) -> int:
        return len(self.params)

    def __call__(self, *args: Any) -> Any:
        if len(args) != self.arity:
            raise TypeError(f"{self.name} expected {self.arity} args, got {len(args)}")
        frame = Env(self.closure)
        for p, a in zip(self.params, args):
            frame.set(p, a)
        return Evaluator(frame).eval_function_body(self.params, args, self.body)

    def __repr__(self) -> str:
        return f"<function {self.name}/{self.arity}>"


class Evaluator:
    def __init__(self, env: Env):
        self.env = env

    def eval_program(self, nodes: Iterable[Node]) -> Any:
        result = None
        for node in nodes:
            result = self.eval(node)
        return result

    def eval_function_body(self, params: list[str], args: tuple[Any, ...], body: Node) -> Any:
        if isinstance(body, CaseExpr):
            return self.eval_case_expr(args, body)
        if isinstance(body, Block):
            # If the final expr is a case expr, it matches against function args.
            
            for expr in body.exprs[:-1]:
                self.eval(expr)
            if not body.exprs:
                return None
            last = body.exprs[-1]
            if isinstance(last, CaseExpr):
                return self.eval_case_expr(args, last)
            return self.eval(last)
        return self.eval(body)

    def eval_case_expr(self, args: tuple[Any, ...], case_expr: CaseExpr) -> Any:
        for clause in case_expr.clauses:
            match_env = self.match_pattern(clause.pattern, args)
            if match_env is None:
                continue
            local = Env(self.env)
            for k, v in match_env.items():
                local.set(k, v)
            if clause.guard is not None and not Evaluator(local).eval(clause.guard):
                continue
            return Evaluator(local).eval(clause.result)
        raise RuntimeError(f"No matching case for arguments {args!r}")

    def match_pattern(self, pattern: Node, args: tuple[Any, ...]) -> Optional[dict[str, Any]]:
        # full parameter tuple matching
        if isinstance(pattern, TuplePattern):
            if len(pattern.items) != len(args):
                return None
            env: dict[str, Any] = {}
            for pat, arg in zip(pattern.items, args):
                sub = self.match_pattern_atom(pat, arg)
                if sub is None:
                    return None
                for k, v in sub.items():
                    if k in env and env[k] != v:
                        return None
                    env[k] = v
            return env
        # single-parameter shorthand
        if len(args) != 1:
            return None
        return self.match_pattern_atom(pattern, args[0])

    def match_pattern_atom(self, pattern: Node, arg: Any) -> Optional[dict[str, Any]]:
        if isinstance(pattern, Number):
            return {} if pattern.value == arg else None
        if isinstance(pattern, String):
            return {} if pattern.value == arg else None
        if isinstance(pattern, Boolean):
            return {} if pattern.value == arg else None
        if isinstance(pattern, Nil):
            return {} if arg is None else None
        if isinstance(pattern, WildcardPattern):
            return {}
        if isinstance(pattern, RestPattern):
            return {pattern.name: arg} if pattern.name is not None else {}
        if isinstance(pattern, Var):
            return {pattern.name: arg}
        if isinstance(pattern, ListPattern):
            if not isinstance(arg, list):
                return None

            rest_index = None
            for i, pat in enumerate(pattern.items):
                if isinstance(pat, RestPattern):
                    rest_index = i
                    break

            if rest_index is None:
                if len(pattern.items) != len(arg):
                    return None
                env: dict[str, Any] = {}
                for pat, item in zip(pattern.items, arg):
                    sub = self.match_pattern_atom(pat, item)
                    if sub is None:
                        return None
                    for k, v in sub.items():
                        if k in env and env[k] != v:
                            return None
                        env[k] = v
                return env

            prefix = pattern.items[:rest_index]
            rest_pat = pattern.items[rest_index]

            if len(arg) < len(prefix):
                return None

            env: dict[str, Any] = {}
            for pat, item in zip(prefix, arg[:len(prefix)]):
                sub = self.match_pattern_atom(pat, item)
                if sub is None:
                    return None
                for k, v in sub.items():
                    if k in env and env[k] != v:
                        return None
                    env[k] = v

            sub = self.match_pattern_atom(rest_pat, arg[len(prefix):])
            if sub is None:
                return None
            for k, v in sub.items():
                if k in env and env[k] != v:
                    return None
                env[k] = v
            return env
        raise RuntimeError(f"Unsupported pattern: {pattern!r}")

    def eval(self, node: Node) -> Any:
        if isinstance(node, ExprStmt):
            return self.eval(node.expr)
        if isinstance(node, Number):
            return node.value
        if isinstance(node, String):
            return node.value
        if isinstance(node, Boolean):
            return node.value
        if isinstance(node, Nil):
            return None
        if isinstance(node, ListLiteral):
            return [self.eval(item) for item in node.items]
        if isinstance(node, Var):
            return self.env.get(node.name)
        if isinstance(node, Unary):
            value = self.eval(node.expr)
            if node.op == "MINUS":
                return -value
            if node.op == "BANG":
                return not truthy(value)
            raise RuntimeError(f"Unknown unary operator {node.op}")
        if isinstance(node, Binary):
            return self.eval_binary(node)
        if isinstance(node, Call):
            fn = self.env.get(node.fn.name) if isinstance(node.fn, Var) else self.eval(node.fn)
            args = [self.eval(a) for a in node.args]
            if isinstance(fn, dict) and all(isinstance(k, int) for k in fn):
                arity = len(args)
                target = fn.get(arity)
                if target is None:
                    available = ", ".join(f"{target_fn.name}/{n}" for n, target_fn in sorted(fn.items()))
                    callee = node.fn.name if isinstance(node.fn, Var) else "function"
                    raise TypeError(f"No matching function: {callee}/{arity}. Available: {available}")
                return target(*args)
            return fn(*args)
        if isinstance(node, Block):
            local = Env(self.env)
            result = None
            ev = Evaluator(local)
            for expr in node.exprs:
                result = ev.eval(expr)
            return result
        if isinstance(node, Lambda):
            params = node.params
            body = node.body
            closure = self.env

            def fn(*args):
                if len(args) != len(params):
                    raise TypeError(f"lambda expected {len(params)} args, got {len(args)}")
                frame = Env(closure)
                for p, a in zip(params, args):
                    frame.set(p, a)
                return Evaluator(frame).eval(body)

            return fn

        if isinstance(node, Assign):
            value = self.eval(node.expr)
            self.env.set(node.name, value)
            return value

        if isinstance(node, FuncDef):
            fn = GeniaFunction(node.name, node.params, node.body, self.env)
            self.env.define_function(fn)
            return fn
        if isinstance(node, CaseExpr):
            raise RuntimeError("Standalone case expressions are only valid as function bodies or final block expressions")
        raise RuntimeError(f"Unknown node: {node!r}")

    def eval_binary(self, node: Binary) -> Any:
        left = self.eval(node.left)
        if node.op == "AND":
            return left and self.eval(node.right)
        if node.op == "OR":
            return left or self.eval(node.right)
        right = self.eval(node.right)
        match node.op:
            case "PLUS":
                return left + right
            case "MINUS":
                return left - right
            case "STAR":
                return left * right
            case "SLASH":
                return left / right
            case "PERCENT":
                return left % right
            case "LT":
                return left < right
            case "LE":
                return left <= right
            case "GT":
                return left > right
            case "GE":
                return left >= right
            case "EQEQ":
                return left == right
            case "NE":
                return left != right
            case _:
                raise RuntimeError(f"Unknown binary operator {node.op}")


def truthy(value: Any) -> bool:
    return bool(value)


# -----------------------------
# Builtins / REPL
# -----------------------------

def make_global_env(stdin_data: Optional[list[str]] = None) -> Env:
    env = Env()

    def log(*args: Any) -> Any:
        print(*args)
        return args[-1] if args else None

    def print_fn(*args: Any) -> Any:
        print(*args)
        return args[-1] if args else None

    def help_fn() -> None:
        print(
            """
Genia prototype help
--------------------
Examples:
  1 + 2 * 3
  square(x) = x * x
  square(5)

  fact(n) =
    0 -> 1 |
    n -> n * fact(n - 1)

  fact2(n) {
    log(n)
    0 -> 1 |
    n -> n * fact2(n - 1)
  }

  add() = 0

  add(x, y) =
    (0, y) -> y |
    (x, 0) -> x |
    (x, y) -> x + y

  print(stdin)
  count([1, 2, 3])
  print([1, 2, 3])

  first_pair(xs) =
    [a, b] -> a + b

  describe(xs) =
    [] -> "empty" |
    [x] -> "one" |
    [x, y] -> "two"

Commands:
  :quit   exit
  :env    show defined names
  :help   show this help
""".strip()
        )
    env.set("log", log)
    env.set("print", print_fn)
    env.set("stdin", [] if stdin_data is None else stdin_data)
    env.set("help", help_fn)
    env.set("pi", math.pi)
    env.set("e", math.e)
    env.set("true", True)
    env.set("false", False)
    env.set("nil", None)
    return env


def is_complete(source: str) -> bool:
    brace = paren = bracket = 0
    in_str: Optional[str] = None
    esc = False
    for ch in source:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'"):
            in_str = ch
        elif ch == '{':
            brace += 1
        elif ch == '}':
            brace -= 1
        elif ch == '(':
            paren += 1
        elif ch == ')':
            paren -= 1
        elif ch == '[':
            bracket += 1
        elif ch == ']':
            bracket -= 1
    if in_str or brace > 0 or paren > 0 or bracket > 0:
        return False
    # If the last nonblank line ends with =, |, -> or ?, keep reading.
    lines = [ln.rstrip() for ln in source.splitlines() if ln.strip()]
    if not lines:
        return True
    last = lines[-1].rstrip()
    return not (last.endswith("=") or last.endswith("|") or last.endswith("->") or last.endswith("?"))


def run_source(source: str, env: Env) -> Any:
    tokens = lex(source)
    parser = Parser(tokens)
    nodes = parser.parse_program()
    return Evaluator(env).eval_program(nodes)


def repl() -> None:
    env = make_global_env([])
    print("Genia prototype REPL. Type :help for examples, :quit to exit.")
    buf = ""
    while True:
        try:
            prompt = "... " if buf else ">>> "
            line = input(prompt)
        except EOFError:
            print()
            break
        if not buf and line.strip() == ":quit":
            break
        if not buf and line.strip() == ":help":
            env.get("help")()
            continue
        if not buf and line.strip() == ":env":
            for k in sorted(env.values):
                print(f"{k} = {env.values[k]!r}")
            continue
        buf += line + "\n"
        if not is_complete(buf):
            continue
        source = buf
        buf = ""
        if not source.strip():
            continue
        try:
            result = run_source(source, env)
            if result is not None:
                print(repr(result))
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        stdin_data = sys.stdin.read().splitlines()
        env = make_global_env(stdin_data)
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            result = run_source(f.read(), env)
        if result is not None:
            print(repr(result))
    else:
        repl()
