# R21 — Numeric Source and Portable Representation Contract

Status: **PLANNED CONTRACT — semantic decisions carried forward from issue #838 / PR #839 design evidence; not implemented by this document.** `GENIA_STATE.md` remains final authority for implemented behavior.

This contract owns only numeric source classification and the portable parse/lowering/Core-IR boundary. Runtime exact-number semantics belong to R22. Rendering, formatting, and JSON interchange belong to R23.

Immutable source design evidence: PR #839 head `856616e66028f00c51fb7aea2df7d0527ce8996f`, especially `docs/design/exact-numeric-model-contract.md` sections 1, 2, and 11.

## 1. Purpose

A conforming host must be able to determine what numeric value class the programmer wrote and lower it into host-independent portable Core IR without consulting Python `int`/`float`, C++ arithmetic defaults, or another host implementation.

R21 does not require Decimal/Rational/Float64 runtime arithmetic to be implemented.

## 2. Numeric lexical forms

```text
integer          := DIGIT+
decimal-dotted   := DIGIT+ "." DIGIT+
exponent         := ("e" | "E") ("+" | "-")? DIGIT+
decimal-exp      := DIGIT+ exponent
decimal-dot-exp  := DIGIT+ "." DIGIT+ exponent
```

Classification:

- `integer` -> Integer
- `decimal-dotted` -> Decimal
- `decimal-exp` -> Decimal
- `decimal-dot-exp` -> Decimal

Examples:

```text
1        -> Integer
1.0      -> Decimal
1.25     -> Decimal
1e3      -> Decimal
1E+3     -> Decimal
1.25e-2  -> Decimal
```

Leading-dot and trailing-dot forms such as `.5` and `5.` are not numeric literals in this contract. An exponent marker requires at least one digit after its optional sign.

The source sign is not part of the numeric token. Existing unary lowering remains authoritative: `-1.25` is unary minus applied to the positive Decimal literal.

There is no Rational literal and no direct Float64 literal/suffix/raw-bits syntax in R21.

## 3. Lexical exactness

Decimal source parsing is lexical/base-10. A Decimal-classified source literal must never be classified or normalized by first converting its spelling through binary64.

Equivalent spellings preserve Decimal kind while normalizing to the same semantic payload. Examples include `1.0`, `1.00`, and `100e-2`.

## 4. Portable Core IR

The portable Core IR node family remains unchanged.

- numeric source literals lower through `IrLiteral`
- `/` remains `IrBinary(op=SLASH)`
- unary minus remains `IrUnary(MINUS, ...)`
- future calls such as `rational(...)`, `float64(...)`, and `exact(...)` remain ordinary `IrCall` nodes and do not require numeric-specific call nodes
- no `IrDecimal`, `IrRational`, or `IrFloat64` node family is introduced

### 4.1 Integer payload

```json
{
  "kind": "integer",
  "digits": "123456789012345678901234567890"
}
```

`digits` is canonical unsigned base-10 text for the positive source literal, with no leading zeros except `0`. Source minus remains outside the payload as unary lowering.

### 4.2 Decimal payload

```json
{
  "kind": "decimal",
  "coefficient": "12345",
  "exponent": "-2"
}
```

Both fields are canonical base-10 strings.

Decimal canonicalization for the payload follows the approved mathematical representation:

- value is `coefficient × 10^exponent`
- zero -> coefficient `0`, exponent `0`
- otherwise remove every trailing base-10 zero from the absolute coefficient and increase exponent by the count removed
- sign is carried by the coefficient
- lexical scale is not retained
- Decimal kind is retained even when the mathematical value is integral

Equivalent Decimal spellings therefore lower to the same tagged payload.

## 5. Parse/Core-IR evidence

R21 shared evidence must cover at least:

- Integer classification
- dotted Decimal classification
- exponent-only Decimal classification
- dotted-exponent Decimal classification
- equivalent Decimal spelling normalization
- invalid exponent forms
- rejected leading-dot/trailing-dot forms
- unary negative lowering
- huge Integer tagged payloads
- `/` remaining ordinary slash binary IR
- no host-native binary float in the portable numeric payload

## 6. Compatibility boundaries

R17 remains authoritative for arbitrary-precision Integer semantics. R18 equality and legal-key rules are not changed in R21. R19 diagnostic portability remains authoritative. R20 open functions are unaffected.

R21 may require parser/IR fixtures and adapters to understand the tagged payload, but it must not silently claim the R22 runtime value model or R23 representation/interchange behavior.

## 7. Non-goals

- Decimal/Rational/Float64 runtime arithmetic
- `rational`, `float64`, or `exact` runtime conversion semantics
- cross-kind numeric equality/comparison changes
- map-key reconciliation for new runtime numeric kinds
- canonical Decimal/Rational/Float64 display
- numeric format-spec behavior
- JSON numeric encode/decode behavior
- precision contexts/transcendentals
- C++ host implementation

## 8. Acceptance

R21 is complete only when the implemented reference host and shared parse/IR evidence allow an independent host to classify and lower numeric source into the same canonical tagged portable Core IR without consulting another host's numeric implementation.
