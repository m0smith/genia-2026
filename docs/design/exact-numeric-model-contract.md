# Exact Numeric Model Contract

Status: **IMPLEMENTATION-READY CONTRACT — issue #838 contract gate approved; behavior is not implemented merely by this document.** `GENIA_STATE.md` remains final authority for implemented behavior.

This is a separately gated prerequisite for R21. It is intentionally not assigned a release number and does not renumber R21 or later roadmap releases.

## 1. Purpose and boundary

Genia's ordinary numeric model is exact by default. A conforming host must implement the semantics below from this contract and shared evidence, not from Python `int`/`float`, C++ arithmetic defaults, a decimal library's context, or another host's implementation.

The numeric kinds are:

- **Integer** — arbitrary-precision exact integer; preserves R17.
- **Decimal** — arbitrary-precision exact base-10 value.
- **Rational** — exact reduced ratio of arbitrary-precision integers.
- **Float64** — explicit IEEE-754 binary64 approximate value.

Integer, Decimal, and Rational form the **exact family**. Float64 is a separate explicit approximate domain, not the top of the exact promotion lattice.

This contract deliberately preserves the existing portable Core IR node family and the R17/R18/R19 architecture. It supersedes only the earlier assumption that ordinary fractional source values are host binary floats.

## 2. Source classification

The numeric lexical forms are:

```text
integer          := DIGIT+
decimal-dotted   := DIGIT+ "." DIGIT+
exponent         := ("e" | "E") ("+" | "-")? DIGIT+
decimal-exp      := DIGIT+ exponent
decimal-dot-exp  := DIGIT+ "." DIGIT+ exponent
```

Classification is semantic:

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

Leading-dot and trailing-dot forms such as `.5` and `5.` are not numeric literals in this contract. An exponent marker must have at least one digit after its optional sign.

A source sign is not part of the numeric token. Existing unary lowering remains authoritative: `-1.25` is unary minus applied to the positive Decimal literal.

There is no Float64 literal suffix and no Rational literal in this gate.

## 3. Decimal semantic value

A Decimal is the mathematical value

```text
coefficient × 10^exponent
```

where coefficient and exponent are arbitrary-precision integers.

Canonicalization:

- zero -> coefficient `0`, exponent `0`
- otherwise remove every trailing base-10 zero from the absolute coefficient and increase exponent by the count removed
- the sign is carried by the coefficient
- there is no Decimal negative-zero identity
- lexical scale is not retained
- Decimal kind is retained even when the canonical mathematical value is integral

Therefore `1.0`, `1.00`, and `100e-2` are the same Decimal value but remain Decimal rather than Integer.

Source Decimal parsing must be lexical/base-10. It must never pass through Float64.

## 4. Rational semantic value

A Rational is `(numerator, denominator)` over arbitrary-precision Integers.

Canonicalization:

- denominator must be nonzero
- divide numerator and denominator by their positive gcd
- denominator is positive
- sign is carried by numerator
- reduced denominator `1` canonicalizes to Integer
- a surviving Rational therefore has denominator greater than `1`

No Rational literal syntax is introduced.

The ordinary constructor is:

```text
rational(numerator, denominator)
```

Both arguments must be Integers. Zero denominator is deterministic numeric misuse. The constructor performs the canonicalization above.

## 5. Float64 semantic value

Float64 is exactly one IEEE-754 binary64 bit pattern and is an explicit approximate numeric domain.

The first gate introduces no Float64 literal suffix or raw-bits constructor. Ordinary construction/conversion is:

```text
float64(value)
```

Accepted input is an exact numeric value or an existing Float64. Float64 input is returned unchanged. Exact input is converted using IEEE-754 round-to-nearest, ties-to-even. If the exact magnitude exceeds the largest finite binary64 value, conversion fails instead of silently producing infinity. Exact mathematical zero converts to positive Float64 zero.

The first gate does not expose a public spelling that deliberately constructs NaN, infinity, or arbitrary NaN payload/sign bits. If such a value enters through an already-approved host boundary, its behavior is governed by sections 9, 10, 12, and 13; NaN payload/sign are not Genia value identity in this gate.

## 6. Float64 -> exact conversion

The ordinary exact conversion is:

```text
exact(value)
```

- Integer/Decimal/Rational -> unchanged exact value
- finite Float64 -> Decimal denoting the exact real value represented by the binary64 bits
- Float64 +0.0/-0.0 -> Decimal zero
- Float64 NaN -> conversion failure
- Float64 +/-infinity -> conversion failure

The conversion does not return the shortest human decimal that would round back to the same Float64. It returns the exact represented dyadic value as a finite Decimal expansion.

Example:

```text
exact(float64(0.1))
```

returns Decimal

```text
0.1000000000000000055511151231257827021181583404541015625
```

when the Float64 was produced from exact Decimal `0.1`.

## 7. Exact arithmetic

For `+`, `-`, and `*`, exact arithmetic uses the promotion relation:

```text
Integer < Decimal < Rational
```

| Left / Right | Integer | Decimal | Rational |
|---|---|---|---|
| Integer | Integer | Decimal | Rational |
| Decimal | Decimal | Decimal | Rational |
| Rational | Rational | Rational | Rational |

Rules:

- arithmetic is mathematically exact
- Decimal participation retains Decimal for Integer/Decimal-only `+`, `-`, `*`, including mathematically integral results
- Rational results are reduced after each public operation
- denominator-one Rational results canonicalize to Integer
- exact arithmetic never implicitly produces Float64

## 8. Exact division and remainder

### 8.1 Division

Exact `/` preserves the mathematical quotient.

| Left / Right | Integer | Decimal | Rational |
|---|---|---|---|
| Integer | Integer when evenly divisible; otherwise Rational | Decimal when the exact quotient terminates in base 10; otherwise Rational | Rational |
| Decimal | Decimal when the exact quotient terminates in base 10; otherwise Rational | Decimal when the exact quotient terminates in base 10; otherwise Rational | Rational |
| Rational | Rational | Rational | Rational |

A quotient terminates in base 10 exactly when its reduced denominator has no prime factors other than `2` and `5`.

Examples:

```text
6 / 3       -> Integer 2
1 / 2       -> Rational 1/2
1 / 3       -> Rational 1/3
1.0 / 2     -> Decimal 0.5
1.0 / 3     -> Rational 1/3
(1 / 3) * 3 -> Integer 1
```

Division by exact zero is deterministic numeric misuse. Exact values never produce infinity or NaN from division.

### 8.2 Remainder

For exact numeric operands, `%` is the exact floor-remainder operation:

```text
q = floor(left / right)
left % right = left - q * right
```

with the same exact-family promotion rule as `+`, `-`, `*` before canonical Rational denominator-one collapse. Division by zero is deterministic numeric misuse.

## 9. Float64 arithmetic

Arithmetic mixing Float64 with any exact numeric operand is rejected. Callers choose the domain explicitly with `float64(...)` or `exact(...)` first.

Float64 with Float64 supports existing numeric operators in the approximate domain:

- unary `-`
- `+`, `-`, `*`, `/`, `%`
- numeric comparisons

Each arithmetic result is IEEE-754 binary64 round-to-nearest/ties-to-even. `%` uses the floor-remainder definition over the represented operands and rounds the final real result to binary64. Division/remainder by Float64 zero is deterministic numeric misuse rather than a host-dependent exception or implicit infinity/NaN production.

NaN remains unordered and non-reflexive. Infinities, when present through an approved host boundary, order below/above finite values in the IEEE sense.

## 10. Numeric comparisons and equality

Booleans are not numbers.

### 10.1 Exact family

Integer, Decimal, and Rational compare by mathematical value for `==`, `!=`, `<`, `<=`, `>`, and `>=`.

Consequences:

- `1 == 1.0`
- `1.0 == 1.00`
- `1 == rational(2, 2)` after canonicalization

### 10.2 Float64 bridge

A finite Float64 is compared to an exact numeric value by the Float64's exact represented mathematical dyadic value. The exact operand must never be rounded to Float64 merely to compare it.

- finite Float64 may equal an exact number only when those mathematical values are identical
- `+0.0` and `-0.0` compare equal to exact zero
- NaN compares unequal to every value including itself
- ordered comparisons involving NaN are false
- infinities compare in the usual extended-real order when present

This bridge applies to comparison/equality only. It does not authorize mixed exact/Float64 arithmetic.

### 10.3 Map-key equivalence

R18 remains authoritative for map-key architecture:

- legal numeric keys use the same equality relation as `==`
- equal legal numeric keys have identical internal key equivalence/hash behavior
- NaN is not a legal map key because it is not reflexively equal
- any structural key containing NaN in an equality-relevant position remains illegal

No second SameValueZero-style relation is introduced.

## 11. Portable Core IR

The portable Core IR node family remains unchanged.

Numeric source literals lower through `IrLiteral`. `/` remains `IrBinary(op=SLASH)`. `rational(...)`, `float64(...)`, and `exact(...)` are ordinary `IrCall` nodes.

Numeric `IrLiteral.value` uses tagged semantic payloads.

Integer:

```json
{
  "kind": "integer",
  "digits": "123456789012345678901234567890"
}
```

`digits` is canonical unsigned base-10 text for the positive source literal, with no leading zeros except `0`; source minus remains `IrUnary(MINUS, ...)`.

Decimal:

```json
{
  "kind": "decimal",
  "coefficient": "12345",
  "exponent": "-2"
}
```

Both fields are canonical base-10 strings. Equivalent source Decimal spellings normalize to the same payload.

The first gate has no Rational literal payload and no direct Float64 literal payload. A later direct Float64 literal/raw-bit surface, if approved, must use exact 16-lowercase-hex-bit payloads and separately settle NaN payload policy.

No `IrDecimal`, `IrRational`, or `IrFloat64` node family is added.

## 12. Canonical display/debug rendering

### 12.1 Integer

Existing canonical decimal Integer rendering is preserved.

### 12.2 Decimal

Let `digits` be the absolute canonical coefficient digits and

```text
adjusted_exponent = len(digits) + exponent - 1
```

Use fixed notation when `-6 <= adjusted_exponent <= 20`; otherwise use scientific notation.

Fixed notation:

- `.` decimal separator
- no grouping
- no insignificant trailing fractional zeros
- append `.0` when mathematically integral so Decimal remains visibly distinct from Integer

Scientific notation:

- exactly one digit before `.`
- remove insignificant trailing fractional zeros
- retain `.0` when there is only one significant digit
- lowercase `e`
- explicit `+`/`-` exponent sign
- no unnecessary exponent leading zeros

Display and debug use this same canonical Decimal atom.

### 12.3 Rational

A surviving Rational renders exactly as:

```text
<numerator>/<denominator>
```

with no spaces. Display and debug are identical.

### 12.4 Float64

A Float64 renders as an explicit constructor-shaped atom so copying the rendering never silently changes domains:

```text
float64(<shortest-roundtrip-decimal>)
```

The inner finite decimal is the shortest decimal spelling that rounds to the identical binary64 bits under round-to-nearest/ties-to-even, using lowercase `e` and explicit exponent sign when scientific notation is used. Integral finite values retain `.0`. Signed zero renders `float64(0.0)` or `float64(-0.0)`.

If NaN/infinity arrive through an approved host boundary, render `float64(nan)`, `float64(inf)`, or `float64(-inf)`; these spellings are diagnostic/rendering atoms only in this gate and do not add source constructors for those values.

Display and debug use the same Float64 atom.

## 13. Generic JSON boundary

Generic JSON remains an interoperability boundary, not an arbitrary-precision numeric transport.

### 13.1 Integer

An Integer is accepted as a JSON number only in the existing R9 interval:

```text
[-9007199254740991, 9007199254740991]
```

Outside that interval generic JSON rejects it.

### 13.2 Decimal binary64-stability predicate

Define `stable_json_decimal(d)` for exact Decimal `d`:

1. Convert `d` to IEEE-754 binary64 using round-to-nearest/ties-to-even.
2. If conversion overflows to infinity, or a nonzero `d` underflows to zero, return false.
3. Compute the canonical **shortest round-trip decimal** for those finite binary64 bits: the decimal spelling using the fewest significant decimal digits that parses under round-to-nearest/ties-to-even to the identical bits; if more than one shortest candidate exists, choose the candidate mathematically closest to the represented binary64 value, and break an exact tie by an even final significand digit.
4. Parse that decimal spelling exactly as a Decimal.
5. Return true exactly when that Decimal is mathematically equal to `d`.

This predicate is host-independent. It accepts common values such as exact Decimal `0.1` because `0.1` is the canonical shortest round-trip spelling of the corresponding binary64 value, while rejecting Decimal values whose additional decimal information would be lost by the retained binary64-oriented generic JSON boundary.

A Decimal may be encoded as a JSON number exactly when `stable_json_decimal(d)` is true. Encoding emits the exact canonical Decimal value and never rounds it merely to fit JSON.

### 13.3 Rational

A Rational is generic-JSON encodable only when its exact value has a finite base-10 Decimal representation and that Decimal satisfies `stable_json_decimal`.

A non-terminating Rational such as `1/3` is rejected rather than rounded.

### 13.4 Float64

Finite Float64 values are JSON-number encodable using their canonical shortest round-trip decimal spelling. NaN and infinities are rejected.

### 13.5 Decode

JSON number tokens are consumed lexically:

- integer-form token -> Integer, only within the R9 safe-integer interval
- fraction/exponent token -> exact Decimal, only when it satisfies `stable_json_decimal`
- JSON never directly constructs Rational
- non-finite spellings remain invalid JSON

No conforming implementation may parse a JSON fraction to host binary floating point first and then construct Decimal.

## 14. Existing format-spec behavior

Canonical display/debug is section 12. Existing field-format syntax remains presentation only and does not mutate numeric kind/value.

- alignment/width operates on canonical rendered text
- zero-padding and grouping remain numeric presentation operations
- `.n` means `n` digits after the decimal point for numeric values and rounds presentation using decimal **half-up**, preserving the existing format-surface rule
- Decimal formatting operates directly on its exact coefficient/exponent
- Rational formatting rounds the exact ratio only for the presentation result
- Float64 formatting starts from the exact dyadic value represented by its bits; it does not start from an implementation's approximate decimal formatter

No new general formatting language is introduced by this gate.

## 15. Resource limits

Arbitrary precision defines the valid mathematical domain, not infinite machine resources.

A conforming host may impose implementation/resource limits on coefficient size, numerator/denominator size, exponent magnitude, gcd work, allocation, or requested approximation precision, provided:

- the limit is not presented as numeric overflow or as a smaller Genia numeric domain
- portable conformance cases do not depend on a specific machine threshold
- failure is normalized as `numeric-resource-limit`
- raw host/library/allocator/OS text does not cross the portable boundary
- a host must not silently round/truncate to avoid the resource failure

## 16. Precision contexts and transcendentals

The approximation boundary is defined now so later work cannot introduce implicit binary-float fallback.

An approximation precision context is immutable and contains at least:

```text
precision_digits : positive Integer
rounding         : half_even
```

`precision_digits` means decimal significant digits. There is no ambient or mutable global precision context.

Exact-input irrational/transcendental approximation, when a later approved API exists, returns Decimal correctly rounded to the requested significant digits. A host unable to satisfy that guarantee must report the operation unsupported/failure rather than substitute `double`/`libm`.

Actual `sqrt`, `sin`, `log`, pi, or other transcendental APIs are **not part of this gate**.

## 17. Error and diagnostic boundary

The following are deterministic numeric misuse/error classes:

- exact division/remainder by zero
- Float64 division/remainder by zero
- invalid `rational` arguments or zero denominator
- invalid `float64`/`exact` conversion
- mixed exact/Float64 arithmetic
- generic JSON numeric-domain rejection
- `numeric-resource-limit`

R19's diagnostic portability rules continue to apply. Python/C++/decimal/rational library exception strings are not portable Genia diagnostics.

Exact wording is pinned by the TEST/error phase where the current shared error surface requires exact stderr.

## 18. Capabilities

Integer/Decimal/Rational/Float64 foundations defined here are core semantics and do not receive a new optional host capability merely to permit partial conformance.

Later transcendental/accelerated/specialized approximate math may introduce separately approved capabilities if concrete host variance requires them.

## 19. Compatibility and supersession

- **R9:** generic JSON remains conservative; this contract replaces host-float fractional parsing with the explicit section-13 predicate without rewriting R9 history.
- **R17:** arbitrary-precision Integer and ordered-map semantics remain unchanged.
- **R18:** one equality/key relation, boolean separation, non-overloadability, protection rules, identity/opaque families, and legal-key reflexivity remain unchanged; this contract generalizes R18's current Integer/float numeric bridge to the exact family plus explicit Float64.
- **R19:** Unicode and diagnostic portability remain unchanged; this contract owns Decimal/Rational/Float64 semantics and canonical rendering that R19 explicitly deferred.
- **R20:** open-function semantics are unaffected.
- **R21:** C++ implements this contract after the reference-host gate is completed; C++ does not redefine it.

Completed release history must remain truthful. Documentation must describe Decimal/Rational/explicit Float64 as implemented only after the corresponding implementation and evidence land.

## 20. Non-goals

- new Core IR node families
- Float32/bfloat16/complex/units/dimensions
- approximate equality
- user-overloadable equality
- Rational literal syntax
- Float64 suffix/raw-bit source syntax
- public NaN payload/sign construction semantics
- ambient decimal context
- transcendental API implementation
- arbitrary-precision generic JSON-number transport
- C++ implementation in this gate

## 21. Implementation acceptance

The gate is implementation-complete only when the Python reference host and portable shared evidence implement the contracted foundational behavior needed by R21, including source classification/tagged Core IR, runtime exact values/arithmetic/division, equality/key reconciliation, explicit Float64 conversions/domain behavior, generic JSON boundary, canonical rendering/format integration, portable diagnostics/hardening, implemented-truth documentation, and a skeptical release audit with PASS.

A second host may not use current Python behavior to fill any gap in this contract.
