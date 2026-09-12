import bisect
from typing import Optional
from .ast_nodes import (
    AnnotatedNode,
    Annotation,
    Assign,
    Binary,
    Block,
    Boolean,
    Call,
    CaseClause,
    CaseExpr,
    Delay,
    ErrPattern,
    ExprStmt,
    FuncDef,
    GlobPattern,
    ImportStmt,
    Lambda,
    ListLiteral,
    ListPattern,
    MapLiteral,
    MapPattern,
    NamedPatternDef,
    NamedPatternUse,
    Nil,
    Node,
    NoneOption,
    Number,
    OpenExtendDef,
    OpenFuncDef,
    OpenUseDef,
    QuasiQuote,
    Quote,
    RestPattern,
    ShellStage,
    SomePattern,
    Spread,
    String,
    TuplePattern,
    Unary,
    Unquote,
    UnquoteSplicing,
    Var,
    WildcardPattern,
)
from .lexer import Token, SourceSpan, parse_string_literal, parse_glob_literal

PRECEDENCE = {
    "PIPE_FWD": 5,
    "OR": 10,
    "AT_CHECK": 15,
    "AT_ASSERT": 15,
    "AND": 20,
    "AMP": 25,
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

RESERVED_LITERAL_IDENTIFIERS = frozenset({"true", "false", "nil", "none"})


class Parser:
    def __init__(self, tokens: list[Token], source: str = "", filename: str = "<memory>"):
        self.tokens = tokens
        self.source = source
        self.filename = filename
        self.i = 0
        # R20 open functions: names declared `open` earlier in this module's
        # top-level clause run, so a later bare pattern-headed clause with
        # the same name is recognized as a repeated clause rather than an
        # ordinary function header (openness is declared, never inferred).
        self._open_names: set[str] = set()
        self._line_starts = [0]
        for idx, ch in enumerate(source):
            if ch == "\n":
                self._line_starts.append(idx + 1)

    def _line_col(self, pos: int) -> tuple[int, int]:
        line_idx = bisect.bisect_right(self._line_starts, pos) - 1
        line_start = self._line_starts[line_idx]
        return line_idx + 1, pos - line_start + 1

    def span_for_tokens(self, start_tok: Token, end_tok: Token) -> SourceSpan:
        end_pos = end_tok.pos + max(len(end_tok.text) - 1, 0)
        line, col = self._line_col(start_tok.pos)
        end_line, end_col = self._line_col(end_pos)
        return SourceSpan(self.filename, line, col, end_line, end_col)

    def merge_spans(self, start: SourceSpan | None, end: SourceSpan | None) -> SourceSpan | None:
        if start is None:
            return end
        if end is None:
            return start
        return SourceSpan(start.filename, start.line, start.column, end.end_line, end.end_column)

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

    def next_non_newline_token(self) -> Token:
        j = self.i
        while self.tokens[j].kind == "NEWLINE":
            j += 1
        return self.tokens[j]

    def skip_separators(self) -> None:
        while self.at("NEWLINE", "SEMI"):
            self.i += 1

    def skip_newlines(self) -> None:
        while self.at("NEWLINE"):
            self.i += 1

    def validate_parameter_name(self, tok: Token, *, context: str, allow_wildcard: bool = False) -> str:
        name = tok.text
        if name in RESERVED_LITERAL_IDENTIFIERS:
            raise SyntaxError(f"{context} cannot use reserved literal {name!r} as a parameter at {tok.pos}")
        if name == "_" and not allow_wildcard:
            raise SyntaxError(f"{context} cannot use '_' as a parameter name at {tok.pos}")
        return name

    def function_header_has_body_starter(self, start_index: int) -> bool:
        j = start_index + 1
        if j >= len(self.tokens) or self.tokens[j].kind != "LPAREN":
            return False
        depth = 0
        while j < len(self.tokens):
            kind = self.tokens[j].kind
            if kind == "LPAREN":
                depth += 1
            elif kind == "RPAREN":
                depth -= 1
                if depth == 0:
                    j += 1
                    while j < len(self.tokens) and self.tokens[j].kind == "NEWLINE":
                        j += 1
                    return j < len(self.tokens) and self.tokens[j].kind in {"ASSIGN", "ARROW", "LBRACE"}
            elif kind == "EOF":
                return False
            j += 1
        return False

    def parenthesized_intro_has_arrow(self, start_index: int) -> bool:
        if start_index >= len(self.tokens) or self.tokens[start_index].kind != "LPAREN":
            return False
        j = start_index
        depth = 0
        while j < len(self.tokens):
            kind = self.tokens[j].kind
            if kind == "LPAREN":
                depth += 1
            elif kind == "RPAREN":
                depth -= 1
                if depth == 0:
                    j += 1
                    while j < len(self.tokens) and self.tokens[j].kind == "NEWLINE":
                        j += 1
                    return j < len(self.tokens) and self.tokens[j].kind == "ARROW"
            elif kind == "EOF":
                return False
            j += 1
        return False

    def parse_program(self) -> list[Node]:
        out: list[Node] = []
        self.skip_separators()
        while not self.at("EOF"):
            node = self.parse_toplevel()
            if not self._merge_open_toplevel(out, node):
                out.append(node)
            self.skip_separators()
        return out

    def _merge_open_toplevel(self, out: list[Node], node: Node) -> bool:
        """R20: a contiguous run of top-level clauses for the same open
        interface (or the same extend target) merges into one AST node so
        grouped and repeated local clause syntax normalize identically
        (contract section 3.1). Merging only the immediately preceding
        top-level node enforces the contiguous-run scoping decision recorded
        in docs/design/r20-open-functions-syntax-ir-design.md section 4."""
        if not out:
            return False
        previous = out[-1]
        if (
            isinstance(node, OpenFuncDef)
            and isinstance(previous, OpenFuncDef)
            and previous.name == node.name
        ):
            previous.clauses.extend(node.clauses)
            previous.span = self.merge_spans(previous.span, node.span)
            return True
        if (
            isinstance(node, OpenExtendDef)
            and isinstance(previous, OpenExtendDef)
            and previous.target_module_alias == node.target_module_alias
            and previous.target_name == node.target_name
        ):
            previous.clauses.extend(node.clauses)
            previous.span = self.merge_spans(previous.span, node.span)
            return True
        return False

    def parse_parameter_list(
        self,
        *,
        context: str,
        allow_wildcard: bool = False,
    ) -> tuple[list[str], str | None]:
        params: list[str] = []
        rest_param: str | None = None
        if self.at("RPAREN"):
            return params, rest_param
        while True:
            if self.at("DOTDOT"):
                dotdot = self.eat("DOTDOT")
                if rest_param is not None:
                    raise SyntaxError(f"{context} can only have one rest parameter at {dotdot.pos}")
                if not self.at("IDENT"):
                    bad = self.peek()
                    raise SyntaxError(f"Invalid {context.lower()} rest parameter token {bad.text!r} ({bad.kind}) at {bad.pos}")
                rest_tok = self.eat("IDENT")
                rest_param = self.validate_parameter_name(rest_tok, context=context, allow_wildcard=allow_wildcard)
                self.skip_newlines()
                if self.at("COMMA"):
                    comma = self.eat("COMMA")
                    raise SyntaxError(f"{context} rest parameter must be final at {comma.pos}")
                break

            if not self.at("IDENT"):
                bad = self.peek()
                raise SyntaxError(f"Invalid {context.lower()} parameter token {bad.text!r} ({bad.kind}) at {bad.pos}")
            param_tok = self.eat("IDENT")
            params.append(self.validate_parameter_name(param_tok, context=context, allow_wildcard=allow_wildcard))
            if not self.maybe("COMMA"):
                break
            self.skip_newlines()
            if self.at("RPAREN"):
                break
            self.skip_newlines()
        return params, rest_param

    def parse_lambda_parameter_pattern(self) -> tuple[Node, list[str], str | None]:
        items: list[Node] = []
        params: list[str] = []
        rest_param: str | None = None
        if self.at("RPAREN"):
            return TuplePattern(items), params, rest_param
        while True:
            item = self.parse_pattern_atom()
            if isinstance(item, RestPattern):
                if rest_param is not None:
                    raise SyntaxError("Lambda can only have one rest parameter")
                rest_param = item.name
            items.append(item)
            if isinstance(item, Var):
                params.append(item.name)
            self.skip_newlines()
            if not self.maybe("COMMA"):
                break
            self.skip_newlines()
            if self.at("RPAREN"):
                break
            if rest_param is not None:
                raise SyntaxError("Lambda rest parameter must be final")
        return TuplePattern(items), params, rest_param

    def try_parse_function_header(self) -> tuple[str, list[str], str | None, Token] | None:
        if not (self.at("IDENT") and self.peek(1).kind == "LPAREN"):
            return None

        save = self.i
        try:
            name_token = self.eat("IDENT")
            name = name_token.text
            self.eat("LPAREN")
            self.skip_newlines()
            params, rest_param = self.parse_parameter_list(context="Function definition")
            self.eat("RPAREN")
            self.skip_newlines()

            if self.at("ASSIGN", "ARROW", "LBRACE"):
                return name, params, rest_param, name_token

            self.i = save
            return None
        except SyntaxError:
            self.i = save
            if self.function_header_has_body_starter(save):
                raise
            return None

    def parse_toplevel(self) -> Node:
        if self.at("AT"):
            annotations = self.parse_prefix_annotations()
            target = self.try_parse_bindable_toplevel()
            if target is None:
                bad = self.peek()
                raise SyntaxError(
                    "Prefix annotations must be followed by a top-level function definition "
                    f"or simple-name assignment, got {bad.text!r} ({bad.kind}) at {bad.pos}"
                )
            return AnnotatedNode(
                annotations,
                target,
                span=self.merge_spans(annotations[0].span, target.span),
            )

        import_stmt = self.try_parse_import_stmt()
        if import_stmt is not None:
            return import_stmt

        bindable = self.try_parse_bindable_toplevel()
        if bindable is not None:
            return bindable

        expr = self.parse_expr()
        if isinstance(expr, Var) and expr.name == "Format" and self.at("STRING"):
            raise SyntaxError('Format constructor requires call syntax: Format("...")')
        if self.at("ASSIGN"):
            raise SyntaxError("Assignment target must be a simple name")
        return ExprStmt(expr, span=expr.span)

    def try_parse_import_stmt(self) -> ImportStmt | None:
        if self.at("IDENT") and self.peek().text == "import":
            import_tok = self.eat("IDENT")
            self.skip_newlines()
            if not self.at("IDENT"):
                bad = self.peek()
                raise SyntaxError(f"import expected a module name identifier, got {bad.text!r} ({bad.kind}) at {bad.pos}")
            module_tok = self.eat("IDENT")
            module_name = module_tok.text
            alias = module_name
            end_tok = module_tok
            self.skip_newlines()
            if self.at("IDENT") and self.peek().text == "as":
                self.eat("IDENT")
                self.skip_newlines()
                if not self.at("IDENT"):
                    bad = self.peek()
                    raise SyntaxError(f"import as expected an alias identifier, got {bad.text!r} ({bad.kind}) at {bad.pos}")
                end_tok = self.eat("IDENT")
                alias = end_tok.text
            return ImportStmt(module_name, alias, span=self.span_for_tokens(import_tok, end_tok))
        return None

    def try_parse_bindable_toplevel(self) -> Node | None:
        named_pattern = self.try_parse_named_pattern_def()
        if named_pattern is not None:
            return named_pattern

        open_related = self.try_parse_open_related_toplevel()
        if open_related is not None:
            return open_related

        header = self.try_parse_function_header()
        if header is not None:
            name, params, rest_param, name_tok = header

            if self.at("ASSIGN"):
                self.eat("ASSIGN")
                self.skip_separators()
                docstring: str | None = None
                if self.at("STRING"):
                    save = self.i
                    candidate = parse_string_literal(self.eat("STRING").text)
                    if self.at_expr_start():
                        docstring = candidate
                    else:
                        self.i = save
                body = self.parse_function_body_after_intro(len(params))
                return FuncDef(
                    name,
                    params,
                    rest_param,
                    docstring,
                    body,
                    span=self.merge_spans(self.span_for_tokens(name_tok, name_tok), body.span),
                )

            if self.at("LBRACE"):
                body = self.parse_block(allow_final_case=True)
                return FuncDef(
                    name,
                    params,
                    rest_param,
                    None,
                    body,
                    span=self.merge_spans(self.span_for_tokens(name_tok, name_tok), body.span),
                )

            if self.at("ARROW"):
                self.eat("ARROW")
                self.skip_separators()
                body = self.parse_expr()
                return FuncDef(
                    name,
                    params,
                    rest_param,
                    None,
                    body,
                    span=self.merge_spans(self.span_for_tokens(name_tok, name_tok), body.span),
                )

            raise SyntaxError("Internal parser error: expected function body")

        assign = self.try_parse_name_assignment()
        if assign is not None:
            return assign
        return None

    def try_parse_named_pattern_def(self) -> NamedPatternDef | None:
        if not (self.at("IDENT") and self.peek().text == "pattern"):
            return None

        pattern_tok = self.eat("IDENT")
        self.skip_newlines()
        if not self.at("IDENT"):
            bad = self.peek()
            raise SyntaxError(f"pattern expected a name identifier, got {bad.text!r} ({bad.kind}) at {bad.pos}")
        name_tok = self.eat("IDENT")
        name = name_tok.text
        self.skip_newlines()
        self.eat("LPAREN")
        self.skip_newlines()

        if not self.at("IDENT"):
            raise SyntaxError(f"named pattern {name} expects exactly one parameter")
        param_tok = self.eat("IDENT")
        param = self.validate_parameter_name(param_tok, context="Named pattern")
        self.skip_newlines()
        if self.at("COMMA"):
            raise SyntaxError(f"named pattern {name} expects exactly one parameter")
        self.eat("RPAREN")
        self.skip_newlines()
        self.eat("ASSIGN")
        self.skip_separators()
        body = self.parse_function_body_after_intro(1)
        return NamedPatternDef(name, param, body, span=self.merge_spans(self.span_for_tokens(pattern_tok, name_tok), body.span))

    # ------------------------------------------------------------------
    # R20 open functions and extensible pattern dispatch
    # ------------------------------------------------------------------

    def try_parse_open_related_toplevel(self) -> Node | None:
        if self.at("IDENT") and self.peek().text == "open":
            save = self.i
            open_tok = self.eat("IDENT")
            self.skip_newlines()
            if not (self.at("IDENT") and self.peek(1).kind == "LPAREN"):
                self.i = save
                return None
            return self._parse_open_pattern_clause(open_tok=open_tok)

        if self.at("IDENT") and self.peek().text == "extend":
            save = self.i
            extend_tok = self.eat("IDENT")
            self.skip_newlines()
            parsed = self._try_parse_extend_clause(extend_tok)
            if parsed is not None:
                return parsed
            self.i = save
            return None

        if self.at("IDENT") and self.peek().text == "use":
            save = self.i
            use_tok = self.eat("IDENT")
            self.skip_newlines()
            parsed = self._try_parse_use_stmt(use_tok)
            if parsed is not None:
                return parsed
            self.i = save
            return None

        if self.at("IDENT") and self.peek(1).kind == "LPAREN" and self.peek().text in self._open_names:
            if not self._header_looks_like_open_clause():
                return None
            return self._parse_open_pattern_clause(open_tok=None)

        return None

    def _header_looks_like_open_clause(self) -> bool:
        """Speculatively confirm `name(<pattern-list>)` is followed by
        `? guard =`, `=`, or `{` before committing to clause parsing — a
        bare call expression like `gcd(48, 18)` used as an ordinary
        top-level statement must remain an ordinary call, not a rejected
        clause attempt."""
        save = self.i
        try:
            self.i += 1  # the name identifier
            self.i += 1  # the opening LPAREN
            depth = 1
            while depth > 0:
                if self.at("EOF"):
                    return False
                kind = self.peek().kind
                if kind == "LPAREN":
                    depth += 1
                elif kind == "RPAREN":
                    depth -= 1
                self.i += 1
            self.skip_newlines()
            return self.at("QMARK", "ASSIGN", "LBRACE")
        finally:
            self.i = save

    def _open_header_is_trivial(self, pattern: TuplePattern) -> bool:
        """True when every item is a plain identifier bind (a trailing rest
        pattern allowed) — i.e. the header adds no dispatch constraint of its
        own, exactly like an ordinary FuncDef parameter list."""
        items = pattern.items
        for index, item in enumerate(items):
            if isinstance(item, RestPattern):
                if index != len(items) - 1:
                    return False
                continue
            if not isinstance(item, Var):
                return False
        return True

    def _parse_open_clause_list(self, header_tok: Token) -> list[CaseClause]:
        """Shared header parsing for `open`/repeated/`extend` clauses: an
        already-consumed name token is followed by `(<pattern-list>)`, an
        optional `? guard`, then `= body` or `{ block }`. Reuses the
        existing lambda-parameter pattern parser verbatim (R20 adds no new
        pattern grammar). A grouped case-with-`|` body over a trivial
        (plain-identifier) header is flattened here into one IrCaseClause per
        arm so grouped and repeated local clause syntax normalize to an
        identical ordered clause list (contract §3.1, design doc §2.1)."""
        self.eat("LPAREN")
        self.skip_newlines()
        pattern, _params, rest_param = self.parse_lambda_parameter_pattern()
        self.eat("RPAREN")
        self.skip_newlines()
        guard: Node | None = None
        if self.at("QMARK"):
            self.eat("QMARK")
            self.skip_newlines()
            guard = self.parse_expr()
            self.skip_newlines()
        fixed_arity = len(pattern.items) - (1 if rest_param is not None else 0)
        if self.at("LBRACE"):
            body = self.parse_block(allow_final_case=True)
        else:
            self.eat("ASSIGN")
            self.skip_separators()
            body = self.parse_function_body_after_intro(fixed_arity)

        case_expr: CaseExpr | None = None
        if isinstance(body, CaseExpr):
            case_expr = body
        elif isinstance(body, Block) and len(body.exprs) == 1 and isinstance(body.exprs[0], CaseExpr):
            case_expr = body.exprs[0]

        if case_expr is not None:
            if guard is not None:
                raise SyntaxError(
                    f"open clause with a grouped case body cannot also have a header guard at {header_tok.pos}"
                )
            if not self._open_header_is_trivial(pattern):
                raise SyntaxError(
                    "open clause with a grouped case body requires plain identifier parameters "
                    f"(dispatch belongs in the case arms) at {header_tok.pos}"
                )
            return [CaseClause(arm.pattern, arm.guard, arm.result, span=arm.span) for arm in case_expr.clauses]

        clause = CaseClause(pattern, guard, body, span=self.merge_spans(self.span_for_tokens(header_tok, header_tok), body.span))
        return [clause]

    def _parse_open_pattern_clause(self, *, open_tok: Optional[Token]) -> OpenFuncDef:
        name_tok = self.eat("IDENT")
        name = name_tok.text
        if open_tok is not None:
            if name in self._open_names:
                raise SyntaxError(
                    f"open-function-redeclaration: {name!r} is already declared open in this module at {name_tok.pos}"
                )
            self._open_names.add(name)
        clauses = self._parse_open_clause_list(name_tok)
        start_tok = open_tok if open_tok is not None else name_tok
        span = self.merge_spans(self.span_for_tokens(start_tok, start_tok), clauses[-1].span)
        return OpenFuncDef(name, clauses, None, span=span)

    def _try_parse_extend_clause(self, extend_tok: Token) -> OpenExtendDef | None:
        if not (self.at("IDENT") and "." in self.peek().text and self.peek(1).kind == "LPAREN"):
            return None
        qualified_tok = self.eat("IDENT")
        parts = qualified_tok.text.split(".")
        if len(parts) != 2 or not all(parts):
            raise SyntaxError(f"extend target must be spelled alias.name at {qualified_tok.pos}")
        alias, target_name = parts
        clauses = self._parse_open_clause_list(qualified_tok)
        span = self.merge_spans(self.span_for_tokens(extend_tok, extend_tok), clauses[-1].span)
        return OpenExtendDef(alias, target_name, clauses, span=span)

    def _try_parse_use_stmt(self, use_tok: Token) -> OpenUseDef | None:
        if not self.at("IDENT"):
            return None
        name_tok = self.eat("IDENT")
        self.skip_newlines()
        if not (self.at("IDENT") and self.peek().text == "from"):
            return None
        self.eat("IDENT")
        self.skip_newlines()
        if not self.at("IDENT"):
            bad = self.peek()
            raise SyntaxError(f"use ... from expected a module alias identifier, got {bad.text!r} ({bad.kind}) at {bad.pos}")
        base_alias_tok = self.eat("IDENT")
        self.skip_newlines()
        if not (self.at("IDENT") and self.peek().text == "with"):
            bad = self.peek()
            raise SyntaxError(f"use ... from {base_alias_tok.text} expected 'with' at {bad.pos}")
        self.eat("IDENT")
        self.skip_newlines()
        contribution_aliases: list[str] = []
        last_tok = base_alias_tok
        while True:
            if not self.at("IDENT"):
                bad = self.peek()
                raise SyntaxError(f"use ... with expected a contribution module alias, got {bad.text!r} ({bad.kind}) at {bad.pos}")
            last_tok = self.eat("IDENT")
            contribution_aliases.append(last_tok.text)
            self.skip_newlines()
            if not self.maybe("COMMA"):
                break
            self.skip_newlines()
        span = self.merge_spans(self.span_for_tokens(use_tok, use_tok), self.span_for_tokens(last_tok, last_tok))
        return OpenUseDef(name_tok.text, base_alias_tok.text, name_tok.text, contribution_aliases, span=span)

    def parse_prefix_annotations(self) -> list[Annotation]:
        annotations: list[Annotation] = []
        while self.at("AT"):
            start_tok = self.eat("AT")
            if not self.at("IDENT"):
                bad = self.peek()
                raise SyntaxError(f"Annotation expected a name identifier, got {bad.text!r} ({bad.kind}) at {bad.pos}")
            name_tok = self.eat("IDENT")
            if not self.at_expr_start():
                bad = self.peek()
                raise SyntaxError(f"Annotation @{name_tok.text} expected a value expression, got {bad.text!r} ({bad.kind}) at {bad.pos}")
            value = self.parse_expr()
            end_tok = self.peek(-1)
            annotations.append(
                Annotation(
                    name_tok.text,
                    value,
                    span=self.span_for_tokens(start_tok, end_tok),
                )
            )
            if not self.at("NEWLINE", "SEMI", "EOF"):
                bad = self.peek()
                raise SyntaxError(
                    f"Annotation @{name_tok.text} must end at a newline before its target, got {bad.text!r} ({bad.kind}) at {bad.pos}"
                )
            self.skip_separators()
        return annotations

    def try_parse_name_assignment(self) -> Assign | None:
        if not (self.at("IDENT") and self.peek(1).kind == "ASSIGN"):
            return None
        name_tok = self.eat("IDENT")
        name = name_tok.text
        self.eat("ASSIGN")
        self.skip_separators()
        expr = self.parse_expr()
        return Assign(name, expr, span=self.merge_spans(self.span_for_tokens(name_tok, name_tok), expr.span))

    def at_expr_start(self) -> bool:
        return self.at("NUMBER", "STRING", "IDENT", "MINUS", "BANG", "LPAREN", "LBRACK", "LBRACE")

    def leading_parenthesized_item_count_before_arrow(self) -> int | None:
        if not self.at("LPAREN"):
            return None
        j = self.i + 1
        nested_depth = 0
        item_count = 0
        in_item = False
        opening_kinds = {"LPAREN", "LBRACK", "LBRACE"}
        matching_close = {"LPAREN": "RPAREN", "LBRACK": "RBRACK", "LBRACE": "RBRACE"}
        close_stack: list[str] = []
        while j < len(self.tokens):
            tok = self.tokens[j]
            kind = tok.kind
            if nested_depth == 0 and kind == "RPAREN":
                if in_item:
                    item_count += 1
                j += 1
                while j < len(self.tokens) and self.tokens[j].kind == "NEWLINE":
                    j += 1
                if j >= len(self.tokens) or self.tokens[j].kind != "ARROW":
                    return None
                return item_count
            if kind == "EOF":
                return None
            if nested_depth == 0 and kind == "NEWLINE":
                j += 1
                continue
            if nested_depth == 0 and kind == "COMMA":
                if in_item:
                    item_count += 1
                    in_item = False
                j += 1
                continue

            in_item = True
            if kind in opening_kinds:
                close_stack.append(matching_close[kind])
                nested_depth += 1
            elif close_stack and kind == close_stack[-1]:
                close_stack.pop()
                nested_depth -= 1
            j += 1
        return None

    def parse_function_body_after_intro(self, param_count: int) -> Node:
        parenthesized_case = self.try_parse_parenthesized_case_expr(param_count)
        if parenthesized_case is not None:
            return parenthesized_case
        if self.looks_like_case_start():
            leading_tuple_arity = self.leading_parenthesized_item_count_before_arrow()
            if leading_tuple_arity is not None and leading_tuple_arity != param_count:
                return self.parse_expr()
            return self.parse_case_expr(single_param_shorthand_ok=True)
        return self.parse_expr()

    def try_parse_parenthesized_case_expr(self, param_count: int) -> Node | None:
        if not self.at("LPAREN"):
            return None
        save = self.i
        try:
            self.eat("LPAREN")
            self.skip_separators()
            if not self.looks_like_case_start():
                self.i = save
                return None
            leading_tuple_arity = self.leading_parenthesized_item_count_before_arrow()
            if leading_tuple_arity is not None and leading_tuple_arity != param_count:
                self.i = save
                return None
            case_expr = self.parse_case_expr(single_param_shorthand_ok=True)
            self.skip_separators()
            self.eat("RPAREN")
            return case_expr
        except SyntaxError:
            self.i = save
            return None

    def parse_block(self, allow_final_case: bool) -> Block:
        start = self.eat("LBRACE")
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
            assign = self.try_parse_name_assignment()
            if assign is not None:
                exprs.append(assign)
            else:
                expr = self.parse_expr()
                if self.at("ASSIGN"):
                    raise SyntaxError("Assignment target must be a simple name")
                exprs.append(expr)
            self.skip_separators()
        end = self.eat("RBRACE")
        return Block(exprs, span=self.span_for_tokens(start, end))

    def looks_like_case_start(self) -> bool:
        # single param shorthand cases: 0 ->, name ->, [x, y] ->, name ? ... ->
        # tuple case: ( ... ) ->
        # We only detect enough for v0.1.
        if self.at("IDENT") and self.peek(1).kind == "LPAREN":
            depth = 0
            j = self.i + 1
            while True:
                tok = self.tokens[j]
                if tok.kind == "LPAREN":
                    depth += 1
                elif tok.kind == "RPAREN":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        while self.tokens[j].kind == "NEWLINE":
                            j += 1
                        return self.tokens[j].kind in {"ARROW", "QMARK"}
                elif tok.kind == "EOF":
                    return False
                j += 1
        if self.at("NUMBER", "STRING", "IDENT", "GLOB"):
            j = self.i + 1
            while self.tokens[j].kind == "NEWLINE":
                j += 1
            if self.tokens[j].kind in {"ARROW", "QMARK"}:
                return True
        if self.at("LPAREN", "LBRACK", "LBRACE"):
            open_kind = self.peek().kind
            close_kind = {"LPAREN": "RPAREN", "LBRACK": "RBRACK", "LBRACE": "RBRACE"}[open_kind]
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
        return CaseExpr(clauses, span=self.merge_spans(clauses[0].span, clauses[-1].span))

    def parse_case_clause(self, single_param_shorthand_ok: bool) -> CaseClause:
        pattern = self.parse_pattern(single_param_shorthand_ok)
        guard = None
        if self.maybe("QMARK"):
            guard = self.parse_expr()
        self.eat("ARROW")
        result = self.parse_expr()
        return CaseClause(pattern, guard, result, span=self.merge_spans(pattern.span, result.span))

    def parse_pattern(self, single_param_shorthand_ok: bool) -> Node:
        if self.at("LPAREN"):
            start = self.eat("LPAREN")
            items: list[Node] = []
            if not self.at("RPAREN"):
                while True:
                    items.append(self.parse_pattern_atom())
                    if not self.maybe("COMMA"):
                        break
            end = self.eat("RPAREN")
            return TuplePattern(items, span=self.span_for_tokens(start, end))
        atom = self.parse_pattern_atom()
        if single_param_shorthand_ok:
            return atom
        return TuplePattern([atom], span=atom.span)

    def parse_pattern_atom(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "STRING":
            self.i += 1
            return String(parse_string_literal(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "GLOB":
            self.i += 1
            return GlobPattern(parse_glob_literal(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "DOTDOT":
            self.i += 1
            if self.at("IDENT"):
                name = self.eat("IDENT").text
                if name == "_":
                    return RestPattern(None, span=self.span_for_tokens(tok, tok))
                return RestPattern(name, span=self.span_for_tokens(tok, tok))
            return RestPattern(None, span=self.span_for_tokens(tok, tok))
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True, span=self.span_for_tokens(tok, tok))
            if tok.text == "false":
                return Boolean(False, span=self.span_for_tokens(tok, tok))
            if tok.text == "nil":
                return Nil(span=self.span_for_tokens(tok, tok))
            if tok.text == "none":
                if self.at("LPAREN"):
                    return self.finish_none_pattern(tok)
                return NoneOption(span=self.span_for_tokens(tok, tok))
            if tok.text == "some" and self.at("LPAREN"):
                start = self.eat("LPAREN")
                self.skip_newlines()
                inner = self.parse_pattern_atom()
                self.skip_newlines()
                context: Node | None = None
                if self.at("COMMA"):
                    self.eat("COMMA")
                    self.skip_newlines()
                    context = self.parse_pattern_atom()
                    self.skip_newlines()
                    if self.at("COMMA"):
                        comma = self.eat("COMMA")
                        raise SyntaxError(f"some(...) pattern expects at most 2 inner patterns at {comma.pos}")
                end = self.eat("RPAREN")
                return SomePattern(inner, context, span=self.span_for_tokens(tok, end))
            if tok.text == "err" and self.at("LPAREN"):
                start = self.eat("LPAREN")
                self.skip_newlines()
                if self.at("RPAREN"):
                    raise SyntaxError(f"err(...) pattern expects 1 or 2 inner patterns at {self.peek().pos}")
                reason = self.parse_none_reason_pattern_atom()
                self.skip_newlines()
                context: Node | None = None
                if self.at("COMMA"):
                    self.eat("COMMA")
                    self.skip_newlines()
                    context = self.parse_pattern_atom()
                    self.skip_newlines()
                    if self.at("COMMA"):
                        comma = self.eat("COMMA")
                        raise SyntaxError(f"err(...) pattern expects at most 2 inner patterns at {comma.pos}")
                end = self.eat("RPAREN")
                return ErrPattern(reason, context, span=self.span_for_tokens(tok, end))
            if tok.text == "_":
                return WildcardPattern(span=self.span_for_tokens(tok, tok))
            if self.at("LPAREN"):
                self.eat("LPAREN")
                self.skip_newlines()
                if self.at("RPAREN"):
                    raise SyntaxError(f"named pattern {tok.text} expects exactly one pattern argument")
                inner = self.parse_pattern_atom()
                self.skip_newlines()
                if self.at("COMMA"):
                    raise SyntaxError(f"named pattern {tok.text} expects exactly one pattern argument")
                end = self.eat("RPAREN")
                return NamedPatternUse(tok.text, inner, span=self.span_for_tokens(tok, end))
            return Var(tok.text, span=self.span_for_tokens(tok, tok))
        if tok.kind == "LBRACK":
            start = self.eat("LBRACK")
            items: list[Node] = []
            saw_rest = False
            self.skip_newlines()
            if not self.at("RBRACK"):
                while True:
                    item = self.parse_pattern_atom()
                    if saw_rest:
                        raise SyntaxError("..rest must be the final item in a list pattern")
                    items.append(item)
                    if isinstance(item, RestPattern):
                        saw_rest = True
                    self.skip_newlines()
                    if not self.maybe("COMMA"):
                        break
                    self.skip_newlines()
            end = self.eat("RBRACK")
            return ListPattern(items, span=self.span_for_tokens(start, end))
        if tok.kind == "LBRACE":
            return self.parse_map_pattern()
        raise SyntaxError(f"Invalid pattern token {tok.text!r} ({tok.kind}) at {tok.pos}")

    def parse_none_reason_pattern_atom(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "STRING":
            self.i += 1
            return String(parse_string_literal(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True, span=self.span_for_tokens(tok, tok))
            if tok.text == "false":
                return Boolean(False, span=self.span_for_tokens(tok, tok))
            if tok.text == "nil":
                return Nil(span=self.span_for_tokens(tok, tok))
            if tok.text == "none":
                return NoneOption(span=self.span_for_tokens(tok, tok))
            if tok.text == "_":
                return WildcardPattern(span=self.span_for_tokens(tok, tok))
            return Var(tok.text, span=self.span_for_tokens(tok, tok))
        raise SyntaxError(f"none(...) reason pattern expects a literal, symbol label, or _ at {tok.pos}")

    def finish_none_pattern(self, none_tok: Token) -> Node:
        self.eat("LPAREN")
        self.skip_newlines()
        if self.at("RPAREN"):
            raise SyntaxError(f"none(...) pattern expects 1 or 2 inner patterns at {self.peek().pos}")
        reason = self.parse_none_reason_pattern_atom()
        self.skip_newlines()
        context: Node | None = None
        if self.at("COMMA"):
            self.eat("COMMA")
            self.skip_newlines()
            context = self.parse_pattern_atom()
            self.skip_newlines()
            if self.at("COMMA"):
                comma = self.eat("COMMA")
                raise SyntaxError(f"none(...) pattern expects at most 2 inner patterns at {comma.pos}")
        end = self.eat("RPAREN")
        return NoneOption(reason, context, span=self.span_for_tokens(none_tok, end))

    def finish_none_expr(self, none_tok: Token) -> Node:
        self.eat("LPAREN")
        self.skip_newlines()
        if self.at("RPAREN"):
            raise SyntaxError(f"none(...) expects 1 or 2 arguments at {self.peek().pos}")
        reason = self.parse_expr()
        self.skip_newlines()
        context: Node | None = None
        if self.at("COMMA"):
            self.eat("COMMA")
            self.skip_newlines()
            context = self.parse_expr()
            self.skip_newlines()
            if self.at("COMMA"):
                comma = self.eat("COMMA")
                raise SyntaxError(f"none(...) expects at most 2 arguments at {comma.pos}")
        end = self.eat("RPAREN")
        return NoneOption(reason, context, span=self.span_for_tokens(none_tok, end))

    def parse_expr(self, min_prec: int = 0) -> Node:
        left = self.parse_prefix()
        while True:
            tok = self.peek()
            if tok.kind == "NEWLINE":
                next_tok = self.next_non_newline_token()
                if next_tok.kind == "PIPE_FWD":
                    self.skip_newlines()
                    tok = self.peek()
                else:
                    break
            if tok.kind == "LPAREN":
                left = self.finish_call(left)
                continue
            prec = PRECEDENCE.get(tok.kind)
            if prec is None or prec < min_prec:
                break
            op = tok.kind
            self.i += 1
            if op == "PIPE_FWD":
                self.skip_newlines()
            right = self.parse_expr(prec + 1)
            left = Binary(left, op, right, span=self.merge_spans(left.span, right.span))
        return left

    def parse_prefix(self) -> Node:
        tok = self.peek()
        if tok.kind == "NUMBER":
            self.i += 1
            return Number(float(tok.text) if "." in tok.text else int(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "STRING":
            self.i += 1
            return String(parse_string_literal(tok.text), span=self.span_for_tokens(tok, tok))
        if tok.kind == "SHELL_STAGE":
            self.i += 1
            return ShellStage(tok.text, span=self.span_for_tokens(tok, tok))
        if tok.kind == "IDENT":
            self.i += 1
            if tok.text == "true":
                return Boolean(True, span=self.span_for_tokens(tok, tok))
            if tok.text == "false":
                return Boolean(False, span=self.span_for_tokens(tok, tok))
            if tok.text == "nil":
                return Nil(span=self.span_for_tokens(tok, tok))
            if tok.text == "none":
                if self.at("LPAREN"):
                    return self.finish_none_expr(tok)
                return NoneOption(span=self.span_for_tokens(tok, tok))
            if "." in tok.text:
                return self.parse_dotted_identifier_expr(tok)
            return Var(tok.text, span=self.span_for_tokens(tok, tok))
        if tok.kind in ("MINUS", "BANG"):
            self.i += 1
            expr = self.parse_expr(70)
            return Unary(tok.kind, expr, span=self.merge_spans(self.span_for_tokens(tok, tok), expr.span))
        if tok.kind == "LPAREN":
            save = self.i
            start = self.peek()
            try:
                self.i += 1
                self.skip_newlines()
                pattern, params, rest_param = self.parse_lambda_parameter_pattern()
                self.eat("RPAREN")
                self.skip_newlines()
                if self.at("ARROW"):
                    self.eat("ARROW")
                    self.skip_newlines()
                    body = self.parse_expr()
                    return Lambda(
                        params,
                        rest_param,
                        body,
                        span=self.merge_spans(self.span_for_tokens(start, start), body.span),
                        pattern=pattern,
                    )
                self.i = save
            except SyntaxError:
                self.i = save
                if self.parenthesized_intro_has_arrow(save):
                    raise

            self.i += 1
            self.skip_newlines()
            expr = self.parse_expr()
            self.skip_newlines()
            self.eat("RPAREN")
            return expr
        if tok.kind == "LBRACK":
            return self.parse_list_literal()
        if tok.kind == "LBRACE":
            return self.parse_brace_expr()
        raise SyntaxError(f"Unexpected token {tok.text!r} ({tok.kind}) at {tok.pos}")

    def parse_dotted_identifier_expr(self, tok: Token) -> Node:
        parts = tok.text.split(".")
        if len(parts) == 2 and all(parts):
            span = self.span_for_tokens(tok, tok)
            return Binary(
                Var(parts[0], span=span),
                "SLASH",
                Var(parts[1], span=span),
                named_access=True,
                span=span,
            )
        if parts and parts[-1] == "":
            raise SyntaxError(f"named access requires an identifier after '.' at {tok.pos}")
        return Var(tok.text, span=self.span_for_tokens(tok, tok))

    def parse_brace_expr(self) -> Node:
        save = self.i
        try:
            return self.parse_map_literal()
        except SyntaxError:
            self.i = save
            return self.parse_block(allow_final_case=False)

    def parse_list_literal(self) -> ListLiteral:
        start = self.eat("LBRACK")
        self.skip_newlines()
        items: list[Node] = []
        self.skip_separators()
        if not self.at("RBRACK"):
            while True:
                if self.at("DOTDOT"):
                    dotdot = self.eat("DOTDOT")
                    expr = self.parse_expr()
                    items.append(Spread(expr, span=self.merge_spans(self.span_for_tokens(dotdot, dotdot), expr.span)))
                else:
                    items.append(self.parse_expr())
                self.skip_separators()
                if not self.maybe("COMMA"):
                    break
                self.skip_newlines()
                if self.at("RBRACK"):
                    break
                self.skip_newlines()
        self.skip_newlines()
        end = self.eat("RBRACK")
        return ListLiteral(items, span=self.span_for_tokens(start, end))

    def parse_map_literal_key(self) -> Node:
        if self.at("IDENT"):
            tok = self.eat("IDENT")
            return Var(tok.text, span=self.span_for_tokens(tok, tok))
        if self.at("STRING"):
            tok = self.eat("STRING")
            return String(parse_string_literal(tok.text), span=self.span_for_tokens(tok, tok))
        tok = self.peek()
        raise SyntaxError(f"Invalid map key token {tok.text!r} ({tok.kind}) at {tok.pos}")

    def parse_map_literal(self) -> MapLiteral:
        start = self.eat("LBRACE")
        self.skip_newlines()
        items: list[tuple[Node, Node]] = []
        if not self.at("RBRACE"):
            while True:
                key = self.parse_map_literal_key()
                self.skip_newlines()
                self.eat("COLON")
                self.skip_newlines()
                value = self.parse_expr()
                items.append((key, value))
                self.skip_separators()
                if not self.maybe("COMMA"):
                    break
                self.skip_newlines()
                if self.at("RBRACE"):
                    break
                self.skip_newlines()
        self.skip_newlines()
        end = self.eat("RBRACE")
        return MapLiteral(items, span=self.span_for_tokens(start, end))

    def parse_map_pattern(self) -> MapPattern:
        start = self.eat("LBRACE")
        self.skip_newlines()
        items: list[tuple[str, Node]] = []
        if not self.at("RBRACE"):
            while True:
                if self.at("IDENT"):
                    key_tok = self.eat("IDENT")
                    key = key_tok.text
                    if self.maybe("COLON"):
                        self.skip_newlines()
                        value_pattern = self.parse_pattern_atom()
                    else:
                        value_pattern = Var(key, span=self.span_for_tokens(key_tok, key_tok))
                    items.append((key, value_pattern))
                elif self.at("STRING"):
                    key_tok = self.eat("STRING")
                    key = parse_string_literal(key_tok.text)
                    if not self.maybe("COLON"):
                        raise SyntaxError(f"Map pattern shorthand is only allowed for identifier keys at {key_tok.pos}")
                    self.skip_newlines()
                    value_pattern = self.parse_pattern_atom()
                    items.append((key, value_pattern))
                else:
                    bad = self.peek()
                    raise SyntaxError(f"Invalid map pattern key token {bad.text!r} ({bad.kind}) at {bad.pos}")

                self.skip_newlines()
                if not self.maybe("COMMA"):
                    break
                self.skip_newlines()
                if self.at("RBRACE"):
                    break
                self.skip_newlines()
        end = self.eat("RBRACE")
        return MapPattern(items, span=self.span_for_tokens(start, end))

    def parse_quoted_form(self) -> Node:
        assign = self.try_parse_name_assignment()
        if assign is not None:
            return assign
        if not self.at("LPAREN") and self.looks_like_case_start():
            return self.parse_case_expr(single_param_shorthand_ok=True)
        expr = self.parse_expr()
        if self.at("ASSIGN"):
            raise SyntaxError("Assignment target must be a simple name")
        return expr

    def finish_call(self, fn: Node) -> Node:
        self.eat("LPAREN")
        self.skip_newlines()
        if isinstance(fn, Var) and fn.name in {"quote", "quasiquote"}:
            if self.at("RPAREN"):
                raise SyntaxError(f"{fn.name}(...) expects exactly one argument")
            expr = self.parse_quoted_form()
            self.skip_separators()
            if self.maybe("COMMA"):
                raise SyntaxError(f"{fn.name}(...) expects exactly one argument")
            self.skip_newlines()
            end = self.eat("RPAREN")
            if isinstance(fn, Var) and fn.name == "quote":
                return Quote(expr, span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
            return QuasiQuote(expr, span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
        args: list[Node] = []
        self.skip_separators()
        if not self.at("RPAREN"):
            while True:
                if self.at("DOTDOT"):
                    dotdot = self.eat("DOTDOT")
                    expr = self.parse_expr()
                    args.append(Spread(expr, span=self.merge_spans(self.span_for_tokens(dotdot, dotdot), expr.span)))
                else:
                    args.append(self.parse_expr())
                self.skip_separators()
                if not self.maybe("COMMA"):
                    break
                self.skip_newlines()
                if self.at("RPAREN"):
                    break
                self.skip_newlines()
        self.skip_newlines()
        end = self.eat("RPAREN")
        if isinstance(fn, Var) and fn.name == "delay":
            if len(args) != 1:
                raise SyntaxError("delay(...) expects exactly one argument")
            if isinstance(args[0], Spread):
                raise SyntaxError("delay(...) does not accept spread arguments")
            return Delay(args[0], span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
        if isinstance(fn, Var) and fn.name == "unquote":
            if len(args) != 1:
                raise SyntaxError("unquote(...) expects exactly one argument")
            if isinstance(args[0], Spread):
                raise SyntaxError("unquote(...) does not accept spread arguments")
            return Unquote(args[0], span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
        if isinstance(fn, Var) and fn.name == "unquote_splicing":
            if len(args) != 1:
                raise SyntaxError("unquote_splicing(...) expects exactly one argument")
            if isinstance(args[0], Spread):
                raise SyntaxError("unquote_splicing(...) does not accept spread arguments")
            return UnquoteSplicing(args[0], span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
        return Call(fn, args, span=self.merge_spans(fn.span, self.span_for_tokens(end, end)))
