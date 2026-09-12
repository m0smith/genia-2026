# Exact Numeric N-1 — Source Classification and Tagged Core IR Design

Status: **APPROVED IMPLEMENTATION DESIGN for issue #838 N-1.** This design implements only the first slice authorized by `docs/design/exact-numeric-model-contract.md`. It changes no runtime behavior by itself; `GENIA_STATE.md` remains final authority until implementation lands.

## 1. Slice boundary

This design covers only:

- lexer numeric token recognition
- parser numeric classification
- exact lexical Decimal normalization
- surface AST representation needed to retain numeric semantic kind
- tagged numeric `IrLiteral.value`
- numeric literal pattern payloads
- portable parse/IR normalization needed by shared specs

It does **not** implement runtime Decimal/Rational/Float64 arithmetic, promotion, division-result semantics, equality/key changes, JSON, rendering, formatting, resource limits, transcendentals, capabilities, or C++.

## 2. Lexer grammar

Replace the current `\d+(?:\.\d+)?` number grammar with exactly:

```regex
\d+(?:\.\d+)?(?:[eE][+-]?\d+)?
```

plus an explicit classification check that rejects an exponent suffix with no exponent digits instead of allowing a shorter valid NUMBER prefix followed by an identifier/operator token.

The accepted families are:

```text
DIGIT+
DIGIT+ "." DIGIT+
DIGIT+ [eE] [+-]? DIGIT+
DIGIT+ "." DIGIT+ [eE] [+-]? DIGIT+
```

The lexer must not accept `.5` or `5.` as NUMBER. Existing `.` identifier punctuation rules remain otherwise unchanged.

### 2.1 Malformed exponent handling

When scanning begins with digits and the immediately following source character after the matched integer/dotted portion is `e` or `E`, the lexer owns the exponent attempt. If the full exponent grammar is not satisfied, raise deterministic `SyntaxError` at the exponent position rather than tokenizing the leading numeric prefix followed by an identifier.

Examples rejected by the lexer:

```text
1e
1e+
1e-
1.2e
1.2e+
```

## 3. Surface AST numeric payload

Keep the existing `Number` AST node family. Do not add Decimal/Rational/Float64 AST node classes.

Change `Number.value` from host `int | float` authority to a small immutable semantic literal descriptor:

```text
NumericLiteral
  kind: "integer" | "decimal"
  digits: str | null
  coefficient: str | null
  exponent: str | null
```

A host may implement this descriptor as a frozen dataclass or equivalent private AST-support value. It is not a runtime Genia value and not a new portable Core IR node.

The AST descriptor is canonical before lowering.

### 3.1 Integer normalization

For an unsigned Integer token:

- parse base-10 lexically
- remove leading zeros
- if all digits are zero, canonical digits are `"0"`
- do not embed a sign

Examples:

```text
0    -> digits "0"
000  -> digits "0"
0012 -> digits "12"
```

### 3.2 Decimal normalization algorithm

For an unsigned accepted Decimal token:

1. Split exponent suffix if present; absent source exponent means `0`.
2. Split dotted significand if present.
3. Concatenate integer and fractional digits into an unsigned coefficient digit string.
4. Semantic exponent is `source_exponent - fractional_digit_count`.
5. Remove leading coefficient zeros for numeric normalization; all-zero coefficient becomes `0`.
6. If coefficient is zero, canonical descriptor is coefficient `"0"`, exponent `"0"`.
7. Otherwise remove trailing coefficient zeros and increase semantic exponent by the number removed.
8. Store coefficient and exponent as canonical base-10 strings with no leading plus sign or unnecessary leading zeros.

Examples:

```text
1.0      -> coefficient "1", exponent "0"
1.00     -> coefficient "1", exponent "0"
100e-2   -> coefficient "1", exponent "0"
123.4500 -> coefficient "12345", exponent "-2"
0.00100  -> coefficient "1", exponent "-3"
1e3      -> coefficient "1", exponent "3"
```

No step may construct a host Float64.

## 4. Parser integration

All existing NUMBER entry points use one helper, for example:

```text
parse_numeric_literal(token_text) -> NumericLiteral
```

This replaces the current repeated `float(tok.text) if "." in tok.text else int(tok.text)` logic in:

- expression prefix parsing
- general pattern atom parsing
- `none`-reason pattern atom parsing

Equivalent numeric source must therefore normalize identically in all three contexts.

Unary source signs remain existing `Unary(MINUS, Number(...))`; they are never folded into the Number descriptor.

## 5. Portable Core IR payload

`lower_node(Number)` produces the existing `IrLiteral` node with one of these values.

Integer:

```json
{
  "kind": "integer",
  "digits": "123"
}
```

Decimal:

```json
{
  "kind": "decimal",
  "coefficient": "12345",
  "exponent": "-2"
}
```

No host int/Decimal/float object crosses the normalized portable IR boundary for numeric literals.

`lower_pattern(Number)` uses the same tagged semantic numeric payload inside `IrPatLiteral` so literal-pattern equality later consumes the same mathematical numeric domain rather than a parser-host object.

Existing string, boolean, symbol, Option, list, map, and all other `IrLiteral` uses remain unchanged.

## 6. Operators and constructors

This slice changes no operator node family.

- `/` remains `IrBinary(op=SLASH, named_access=false)`.
- unary source minus remains `IrUnary(op=MINUS, ...)`.
- `rational(...)` remains `IrCall(IrVar("rational"), ...)`.
- `float64(...)` remains `IrCall(IrVar("float64"), ...)`.
- `exact(...)` remains `IrCall(IrVar("exact"), ...)`.

No parser special form is added for those names.

## 7. Parse normalization

The shared parse adapter must expose semantic numeric kind without host-object repr.

Normalize a Number AST as:

Integer:

```json
{
  "type": "Number",
  "value": {
    "kind": "integer",
    "digits": "123"
  }
}
```

Decimal:

```json
{
  "type": "Number",
  "value": {
    "kind": "decimal",
    "coefficient": "12345",
    "exponent": "-2"
  }
}
```

Use the existing parse-normalizer field naming conventions if they differ; the semantic payload above is fixed.

## 8. Portable IR normalization

The existing IR normalizer serializes the tagged numeric dictionary as the exact `IrLiteral.value` payload. It must not coerce `digits`, `coefficient`, or `exponent` to host JSON numbers.

Quoted-syntax normalization must represent the same semantic Number descriptor rather than a host float where quoted Number AST is normalized.

## 9. Compatibility impact

This slice deliberately changes parse/IR snapshots for numeric literals. That is the approved exact-numeric contract revision.

Runtime evaluation is not yet authorized to interpret the tagged payload as Decimal/Rational semantics in this slice. The implementation must either keep runtime materialization compatible with currently implemented behavior behind the portable IR boundary or limit changes strictly so existing runtime tests remain green until the next runtime slice.

The portable representation must not be weakened to preserve old host-native snapshots.

## 10. Stop conditions

Stop instead of guessing if implementation discovers that:

- exponent tokenization conflicts with an existing approved identifier grammar case
- parse/IR normalizers cannot represent the semantic descriptor without changing unrelated node families
- pattern literal lowering requires a new node family
- runtime code assumes `IrLiteral.value` is necessarily directly executable and cannot be adapted without entering the later runtime slice

Any such conflict is an upstream design issue, not permission to widen this implementation slice.
