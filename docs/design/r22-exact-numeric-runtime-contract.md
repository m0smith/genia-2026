# R22 — Exact Numeric Runtime Contract

Status: **APPROVED PLANNING CONTRACT — not implemented by this document.** `GENIA_STATE.md` remains final authority for implemented behavior.

R22 consumes R21's numeric source/Core-IR contract and owns the runtime numeric value model, arithmetic, conversions, comparison/equality integration, and numeric misuse/resource-limit semantics. Textual rendering and JSON/format interchange belong to R23.

The decisions below carry forward the approved Exact Numeric Model design work from issue #838 / PR #839 as historical design evidence; this merged contract is the release-owned planning authority for R22.

## 1. Numeric domains

The runtime numeric kinds are:

- **Integer** — arbitrary-precision exact integer; preserves R17
- **Decimal** — arbitrary-precision exact base-10 value
- **Rational** — exact reduced ratio of arbitrary-precision Integers
- **Float64** — explicit IEEE-754 binary64 approximate value

Integer, Decimal, and Rational form the exact family. Float64 is a separate explicit approximate domain, not the top of the exact promotion lattice.

Booleans are not numbers.

## 2. Decimal value

A Decimal is the mathematical value:

```text
coefficient × 10^exponent
```

with arbitrary-precision Integer coefficient and exponent.

Canonicalization:

- zero -> coefficient `0`, exponent `0`
- otherwise remove every trailing base-10 zero from the absolute coefficient and increase exponent by the count removed
- sign is carried by coefficient
- no Decimal negative-zero identity
- lexical scale is not retained
- Decimal kind remains Decimal even when the mathematical value is integral

Decimal source materialization consumes R21's exact tagged payload and must never pass through Float64.

## 3. Rational value

A Rational is `(numerator, denominator)` over arbitrary-precision Integers.

Canonicalization:

- denominator must be nonzero
- divide numerator and denominator by their positive gcd
- denominator is positive
- sign is carried by numerator
- reduced denominator `1` canonicalizes to Integer
- a surviving Rational therefore has denominator greater than `1`

Constructor:

```text
rational(numerator, denominator)
```

Both arguments must be Integers. Zero denominator is deterministic numeric misuse.

## 4. Float64 value

Float64 is exactly one IEEE-754 binary64 bit pattern and is an explicit approximate domain.

Ordinary construction/conversion:

```text
float64(value)
```

Accepted input is an exact numeric value or an existing Float64. Existing Float64 is returned unchanged. Exact input converts using round-to-nearest, ties-to-even. Exact magnitude exceeding largest finite binary64 fails rather than silently becoming infinity. Exact mathematical zero converts to positive Float64 zero.

R22 exposes no direct public NaN/infinity/raw-bit constructor. If such a Float64 enters through an already-approved host boundary, its arithmetic/comparison behavior follows this contract.

## 5. Float64 to exact

```text
exact(value)
```

- Integer/Decimal/Rational -> unchanged
- finite Float64 -> Decimal denoting the exact real value represented by its binary64 bits
- Float64 +0.0/-0.0 -> Decimal zero
- NaN -> conversion failure
- +/-infinity -> conversion failure

The conversion returns the exact represented dyadic value as a finite Decimal expansion, not merely the shortest human spelling that round-trips to the Float64.

For example, exact conversion of the Float64 produced from Decimal `0.1` denotes:

```text
0.1000000000000000055511151231257827021181583404541015625
```

## 6. Exact arithmetic

For `+`, `-`, and `*`, exact arithmetic uses:

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
- denominator-one Rational results collapse to Integer
- exact arithmetic never implicitly produces Float64

## 7. Exact division

Exact `/` preserves the mathematical quotient.

| Left / Right | Integer | Decimal | Rational |
|---|---|---|---|
| Integer | Integer when evenly divisible; otherwise Rational | Decimal when exact quotient terminates in base 10; otherwise Rational | Rational |
| Decimal | Decimal when exact quotient terminates in base 10; otherwise Rational | Decimal when exact quotient terminates in base 10; otherwise Rational | Rational |
| Rational | Rational | Rational | Rational |

A reduced quotient terminates in base 10 exactly when its denominator has no prime factors other than `2` and `5`.

Examples:

```text
6 / 3       -> Integer 2
1 / 2       -> Rational 1/2
1 / 3       -> Rational 1/3
1.0 / 2     -> Decimal 0.5
1.0 / 3     -> Rational 1/3
(1 / 3) * 3 -> Integer 1
```

Division by exact zero is deterministic numeric misuse.

## 8. Exact remainder

For exact numeric operands, `%` is floor remainder:

```text
q = floor(left / right)
left % right = left - q * right
```

It uses the same exact-family promotion rule as `+`, `-`, and `*` before Rational denominator-one collapse. Zero divisor is deterministic numeric misuse.

## 9. Float64 arithmetic

Arithmetic mixing Float64 with any exact numeric operand is rejected. The caller chooses the domain explicitly with `float64(...)` or `exact(...)` first.

Float64 with Float64 supports:

- unary `-`
- `+`, `-`, `*`, `/`, `%`
- numeric comparisons

Arithmetic is IEEE-754 binary64 round-to-nearest/ties-to-even. `%` uses floor-remainder over represented operands and rounds the final real result to binary64. Division/remainder by Float64 zero is deterministic numeric misuse rather than host-specific exception behavior or implicit infinity/NaN production.

NaN remains unordered and non-reflexive. Infinities, when present through an approved boundary, use usual extended-real ordering.

## 10. Equality and comparison

### 10.1 Exact family

Integer, Decimal, and Rational compare by mathematical value for `==`, `!=`, `<`, `<=`, `>`, and `>=`.

Consequences include:

```text
1 == 1.0
1.0 == 1.00
1 == rational(2, 2)
```

### 10.2 Float64 bridge

A finite Float64 compares to an exact numeric value by the exact represented mathematical dyadic value of the Float64. The exact operand must never be rounded to Float64 merely to compare it.

- finite Float64 equals an exact value only when mathematical values are identical
- +0.0 and -0.0 compare equal to exact zero
- NaN is unequal to every value including itself
- ordered comparisons involving NaN are false
- infinities use usual extended-real ordering when present

This bridge is for equality/comparison only and does not authorize mixed-domain arithmetic.

### 10.3 Map keys

R18 remains authoritative:

- legal numeric keys use the same equality relation as `==`
- equal legal numeric keys must have identical internal key/hash equivalence
- NaN is not a legal key because it is not reflexively equal
- structural keys containing NaN in an equality-relevant position remain illegal

No second SameValueZero-style relation is introduced.

## 11. Resource limits

Arbitrary precision defines the valid mathematical domain, not infinite machine resources.

A host may impose implementation/resource limits on coefficient size, numerator/denominator size, exponent magnitude, gcd work, allocation, or requested approximation precision provided:

- the failure is not presented as numeric overflow or a smaller language domain
- shared conformance does not depend on a machine-specific threshold
- failure is normalized as `numeric-resource-limit`
- raw host/library/allocator/OS text does not cross the portable boundary
- the host never silently rounds/truncates to avoid the failure

## 12. Precision and future transcendentals

Any future approximation precision context is immutable and contains at least:

```text
precision_digits : positive Integer
rounding         : half_even
```

`precision_digits` means decimal significant digits. There is no ambient mutable global precision context.

Future exact-input irrational/transcendental approximation must return Decimal correctly rounded to the requested significant digits or report unsupported/failure. A host must not substitute `double`/`libm` merely because exact approximation is inconvenient.

R22 does not introduce `sqrt`, `sin`, `log`, pi, or other transcendental APIs.

## 13. Error boundary

Deterministic numeric misuse/error classes include:

- exact division/remainder by zero
- Float64 division/remainder by zero
- invalid `rational` arguments or zero denominator
- invalid `float64`/`exact` conversion
- mixed exact/Float64 arithmetic
- `numeric-resource-limit`

R19 diagnostic portability remains authoritative. Raw Python/C++/numeric-library exception strings are not portable Genia diagnostics.

JSON-domain rejection belongs to R23 rather than R22.

## 14. Compatibility

- R17 Integer semantics remain unchanged.
- R18 owns equality/key architecture; R22 extends only the numeric cases inside that architecture.
- R19 owns diagnostic portability.
- R20 open functions are unaffected.
- R21 owns source classification/tagged Core IR and is not reopened by R22.

## 15. Non-goals

- canonical display/debug spelling
- field-format presentation
- generic JSON encode/decode
- Rational literal syntax
- Float64 literal suffix/raw-bit syntax
- public NaN payload/sign construction semantics
- approximate equality
- user-overloadable equality
- ambient decimal context
- Float32/bfloat16/complex/units/dimensions
- transcendental API implementation
- C++ host implementation

## 16. Acceptance

R22 is complete only when the reference host and shared evidence implement the approved runtime kinds, exact arithmetic/division/remainder, explicit Float64 conversions/domain behavior, equality/comparison/key reconciliation, normalized numeric failures, and compatibility hardening needed so another host can reproduce the same mathematical semantics without consulting Python implementation details.
