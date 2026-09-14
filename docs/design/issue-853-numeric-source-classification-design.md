# Issue #853 Design — E21-1 Numeric Source Classification

Status: process design artifact for issue #853. Implements only §2/§3 of
`docs/design/r21-numeric-source-portable-representation-contract.md`.
`GENIA_STATE.md` remains final authority once implemented.

## New module: `src/genia/numeric_source.py`

Pure, host-independent lexical classification with zero `float()` calls:

- `classify_numeric_literal(text: str) -> NumericSource` where
  `NumericSource` is a small frozen dataclass with `kind` (`"integer"` or
  `"decimal"`), `digits` (Integer only — canonical unsigned decimal text,
  no leading zeros except `"0"`), `coefficient`/`exponent` (Decimal only —
  canonical base-10 text per contract §4.2: value = coefficient × 10^exponent,
  zero normalizes to `("0", "0")`, trailing zeros stripped from the
  magnitude with a matching exponent increase).
- Canonicalization uses only string slicing and Python `int` arithmetic on
  exponent offsets — `int` is itself an arbitrary-precision base-10 type in
  the reference host, not a binary-float approximation, so this satisfies
  "never constructs a host binary float".
- This module is deliberately reusable unchanged by E21-2 when it builds the
  tagged `IrLiteral` payload.

## Lexer change (`src/genia/lexer.py`)

Replace the single-regex `NUMBER_RE` greedy match (which does not recognize
exponents at all today) with explicit staged matching:

1. match `\d+` (mandatory integer part)
2. optionally match `\.\d+` immediately following (fractional part)
3. if the next character is `e`/`E`, require a full `[eE][+-]?\d+` match;
   if that fails, raise `SyntaxError` naming the malformed exponent
   deterministically instead of silently leaving a dangling `e`/`E` for the
   next token to choke on

This makes `1e3`, `1E+3`, and `1.25e-2` lex as one `NUMBER` token (previously
`1e3` lexed as `NUMBER "1"` + `IDENT "e3"`, which was simply unparseable).
`5.` still lexes as `NUMBER "5"` followed by a bare `.`, which the existing
punctuation table rejects (no single-dot token exists) — this already gives
a deterministic rejection with no lexer change needed there. `.5` already
hits "Unexpected character '.'" since `.` is not an identifier-start and no
single-dot punctuation token exists.

## AST change (`src/genia/ast_nodes.py`)

Extend `Number` with new, all-defaulted fields so every existing call site
stays source-compatible:

```python
@dataclass
class Number(Node):
    value: int | float
    span: SourceSpan | None = None
    source_kind: str = "integer"
    digits: str | None = None
    coefficient: str | None = None
    exponent: str | None = None
```

`value` (the existing `int`/`float` runtime value used by the current
evaluator/display path) is left untouched by this ticket — R21 does not
change evaluator/runtime Decimal behavior (R22's boundary). Only the new
`source_kind`/`digits`/`coefficient`/`exponent` fields are populated from
`classify_numeric_literal`, purely as inert classification metadata that
E21-2 will consume when it changes `IrLiteral` payload shape.

## Parser change (`src/genia/parser.py`)

All three `NUMBER` handling sites (`parse_pattern_atom`,
`parse_none_reason_pattern_atom`, `parse_prefix`) call
`classify_numeric_literal(tok.text)` once and build `Number` with both the
existing `value` and the new classification fields. The existing
`"." in tok.text` decimal-detection heuristic is replaced by checking
`source.kind == "decimal"` so exponent-only forms (`1e3`, no `.`) are
correctly treated as Decimal when constructing the legacy `value` float too.

## No lowering/Core-IR change

`lowering.py`'s `IrLiteral(node.value, ...)` call for `Number` nodes is
unchanged in this ticket — E21-2 owns replacing it with the tagged payload
built from the new AST fields.

## Evidence

- new `tests/unit/test_r21_numeric_source_classification_853.py` covering
  the classification module, lexer exponent handling/malformed rejection,
  and parser AST field population
- new `spec/parse/*` YAML cases for representative Integer/Decimal forms,
  equivalent Decimal spellings, malformed exponents, and leading/trailing
  dot rejection, wired into `spec/manifest.json`
