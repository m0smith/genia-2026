# R23 — Numeric Representation and Interchange Contract

Status: **APPROVED PLANNING CONTRACT — not implemented by this document.** `GENIA_STATE.md` remains final authority for implemented behavior.

R23 consumes R21 and R22 and owns canonical numeric rendering, existing field-format presentation, strict generic JSON numeric behavior, lexical JSON Decimal decode, and compatibility JSON reconciliation.

The decisions below carry forward the approved Exact Numeric Model design work from issue #838 / PR #839 as historical design evidence; this merged contract is the release-owned planning authority for R23.

## 1. Purpose

Exact runtime values must cross textual and JSON boundaries without silently changing numeric domain or reintroducing host binary-float semantics.

R23 does not redefine R22 mathematical values or arithmetic.

## 2. Canonical display/debug rendering

### 2.1 Integer

Existing canonical decimal Integer rendering is preserved.

### 2.2 Decimal

Let `digits` be the absolute canonical coefficient digits and:

```text
adjusted_exponent = len(digits) + exponent - 1
```

Use fixed notation when:

```text
-6 <= adjusted_exponent <= 20
```

Otherwise use scientific notation.

Fixed notation rules:

- `.` decimal separator
- no grouping
- no insignificant trailing fractional zeros
- append `.0` when mathematically integral so Decimal remains visibly distinct from Integer

Scientific notation rules:

- exactly one digit before `.`
- remove insignificant trailing fractional zeros
- retain `.0` when there is only one significant digit
- lowercase `e`
- explicit `+`/`-` exponent sign
- no unnecessary exponent leading zeros

Display and debug use the same canonical Decimal atom.

### 2.3 Rational

A surviving Rational renders exactly:

```text
<numerator>/<denominator>
```

with no spaces. Display and debug are identical.

### 2.4 Float64

Float64 renders as an explicit constructor-shaped atom:

```text
float64(<shortest-roundtrip-decimal>)
```

The inner finite decimal is the shortest decimal spelling that rounds to the identical binary64 bits under round-to-nearest/ties-to-even. Use lowercase `e` and explicit exponent sign in scientific notation. Integral finite values retain `.0`.

Signed zero renders:

```text
float64(0.0)
float64(-0.0)
```

If NaN/infinity arrive through an approved boundary, rendering is:

```text
float64(nan)
float64(inf)
float64(-inf)
```

These are rendering atoms only; R23 does not add source constructors for non-finite values.

Display and debug use the same Float64 atom.

## 3. Rendering surfaces

The canonical atoms above govern ordinary user-facing and debug numeric rendering wherever the existing surface delegates to the canonical renderer, including REPL/CLI final-value echo and equivalent normalized host-adapter result rendering.

No surface may fall back to a host dataclass/object/debug representation that exposes implementation structure instead of portable numeric text.

## 4. Generic JSON boundary

Generic JSON remains an interoperability boundary, not arbitrary-precision numeric transport.

### 4.1 Integer

Integer is accepted as a JSON number only in the existing R9 interval:

```text
[-9007199254740991, 9007199254740991]
```

Outside that interval generic JSON rejects it.

### 4.2 Decimal stability predicate

Define `stable_json_decimal(d)` for exact Decimal `d`:

1. Convert `d` to IEEE-754 binary64 using round-to-nearest/ties-to-even.
2. If conversion overflows to infinity, or nonzero `d` underflows to zero, return false.
3. Compute the canonical shortest-roundtrip decimal for those finite binary64 bits: the decimal spelling using the fewest significant digits that parses to the identical bits; if more than one shortest candidate exists, choose the one mathematically closest to the represented binary64 value and break an exact tie by an even final significand digit.
4. Parse that decimal spelling exactly as Decimal.
5. Return true exactly when that Decimal is mathematically equal to `d`.

A Decimal may encode as a JSON number exactly when `stable_json_decimal(d)` is true. Encoding emits the exact canonical Decimal value and never rounds it merely to fit JSON.

This accepts common exact Decimal values such as `0.1` when that is the canonical shortest-roundtrip decimal for the corresponding binary64 value, while rejecting Decimal values whose additional information would be lost by the retained binary64-oriented generic JSON boundary.

### 4.3 Rational

A Rational is generic-JSON encodable only when its exact value has a finite base-10 Decimal representation and that Decimal satisfies `stable_json_decimal`.

A non-terminating Rational such as `1/3` is rejected rather than rounded.

### 4.4 Float64

Finite Float64 values are JSON-number encodable using their canonical shortest-roundtrip decimal spelling. NaN and infinities are rejected.

## 5. Generic JSON decode

JSON number tokens are consumed lexically:

- integer-form token -> Integer, only within the R9 safe-integer interval
- fraction/exponent token -> exact Decimal, only when it satisfies `stable_json_decimal`
- JSON never directly constructs Rational
- non-finite spellings remain invalid JSON

A conforming implementation must not parse a JSON fraction/exponent token to host binary floating point first and then construct Decimal.

## 6. Compatibility JSON surfaces

Any older public JSON parse/stringify compatibility entry points must not preserve a second contradictory host-float numeric model.

Where strict generic JSON and compatibility JSON intentionally differ for already-approved nonnumeric representation behavior, those differences may remain. Their numeric token interpretation, however, must not silently materialize fraction/exponent numbers as host Float64.

Implementation should reuse common lexical numeric conversion machinery where semantics are common rather than duplicate competing parsers.

## 7. Existing format-spec behavior

Canonical display/debug is the base presentation. Existing field-format syntax remains presentation only and does not mutate numeric kind/value.

- alignment/width operates on canonical rendered text
- zero-padding and grouping remain numeric presentation operations where the represented shape supports them
- `.n` means `n` digits after the decimal point and rounds presentation using decimal **half-up**, preserving the existing format-surface rule
- Decimal formatting operates directly on exact coefficient/exponent
- Rational formatting rounds the exact ratio only for the presentation result
- Float64 formatting starts from the exact dyadic value represented by its bits, not from an arbitrary host decimal formatter

Rational's canonical `<numerator>/<denominator>` atom is not silently reinterpreted as a Decimal shape merely to apply unrelated padding/grouping behavior.

No new general formatting language is introduced.

## 8. Error and diagnostic boundary

Deterministic representation/interchange failures include:

- generic JSON numeric-domain rejection
- invalid/non-finite generic JSON number cases
- compatibility-surface numeric misuse where applicable

R19 diagnostic portability remains authoritative. Raw Python/C++/JSON-library/decimal-library exception text must not cross portable boundaries.

## 9. Compatibility

- R9 retains the conservative generic JSON safe-integer boundary.
- R17 Integer semantics remain unchanged.
- R18 equality/key semantics remain unchanged.
- R19 owns Unicode and diagnostic portability.
- R21 owns source classification/tagged Core IR.
- R22 owns the runtime mathematical value model.
- R20 open functions are unaffected.

## 10. Non-goals

- arbitrary-precision generic JSON-number transport
- new JSON dialect
- changing R22 arithmetic or equality
- Rational literal syntax
- Float64 suffix/raw-bit syntax
- public NaN payload/sign construction semantics
- representation-facet redesign unrelated to numeric interoperability
- locale-sensitive formatting
- new general formatting language
- C++ host implementation

## 11. Acceptance

R23 is complete only when the reference host and shared evidence prove canonical Decimal/Rational/Float64 rendering, existing field-format integration, strict JSON encode/decode including lexical Decimal decode, compatibility JSON reconciliation, and portable failure normalization without implicit host binary-float semantics.
