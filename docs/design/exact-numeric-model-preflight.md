# Exact Numeric Model Pre-flight

Status: **Planning contract — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

Release number: **TBD.** This work is intentionally split from R19 and must receive its own release/contract gate before implementation. It must complete before the first conforming C++ host is allowed to freeze the current Python binary-float model into a second production host.

## Purpose

Replace the accidental assumption that ordinary fractional Genia numbers are IEEE-754 binary64 values with an explicit numeric model designed around exactness by default.

The intended direction is:

- `Integer` — arbitrary precision, exact; preserves R17
- `Decimal` — arbitrary-precision base-10 exact numeric values for ordinary decimal-point/exponent literals
- `Rational` — exact reduced ratios of arbitrary-precision integers, including non-terminating decimal results such as `1 / 3`
- `Float64` — explicit IEEE-754 binary64 approximate values for interoperability/performance when the program deliberately accepts binary floating-point semantics

This document does not implement those kinds, choose final source syntax, or revise current truth.

## Why this is separate from R19

R19 began as portability hardening for Unicode, float rendering, and diagnostics. Once ordinary decimal literals are reconsidered as exact Decimal values and Rational is added, the work affects far more than rendering:

- lexer/parser literal classification
- Core IR numeric representation
- arithmetic result kinds
- division
- equality and map-key equivalence
- formatting/rendering
- JSON and host boundaries
- conversions to/from hardware floating point
- shared conformance evidence
- second-host implementation strategy

That is a semantic release, not a formatter patch.

## Design intent

### Exactness by default

Operations over the exact family must not silently lose precision.

At minimum:

- integer arithmetic remains mathematically exact
- finite Decimal addition/subtraction/multiplication are exact
- Rational values retain exact numerator/denominator meaning
- exact division preserves an exact result rather than silently rounding
- no conforming host may substitute binary floating point for Decimal or Rational because it is convenient

### Exact numeric family and promotion

Working contract direction for ordinary exact arithmetic:

```text
Integer < Decimal < Rational
```

This is a promotion relation, not a statement about mathematical importance or storage representation.

For `+`, `-`, and `*`:

| Left / Right | Integer | Decimal | Rational |
|---|---|---|---|
| Integer | Integer | Decimal | Rational |
| Decimal | Decimal | Decimal | Rational |
| Rational | Rational | Rational | Rational |

Additional invariants:

- Decimal results remain Decimal even when mathematically integral.
- Rational values are reduced canonically with a positive denominator.
- A Rational whose reduced denominator is `1` canonicalizes to Integer.
- Ordinary exact arithmetic never promotes to `Float64` implicitly.

### Rational closes the division gap

Supporting Rational changes the preferred division model.

Exact `/` must preserve the mathematical quotient without rounding.

Working division matrix:

| Left / Right | Integer | Decimal | Rational |
|---|---|---|---|
| Integer | Integer when evenly divisible; otherwise Rational | Decimal when exact quotient terminates in base 10; otherwise Rational | Rational |
| Decimal | Decimal when exact quotient terminates in base 10; otherwise Rational | Decimal when exact quotient terminates in base 10; otherwise Rational | Rational |
| Rational | Rational | Rational | Rational |

Canonical denominator-one Rational results collapse to Integer. Decimal results do not collapse merely because their fractional component becomes zero.

Examples of the intended result-kind rule:

```text
6 / 3       -> Integer 2
1 / 2       -> Rational 1/2
1 / 3       -> Rational 1/3
1.0 / 2     -> Decimal 0.5
1.0 / 3     -> Rational 1/3
(1 / 3) * 3 -> Integer 1
```

Division by exact zero is a deterministic exact-numeric error/misuse boundary; exact numbers do not produce infinity or NaN.

### Mathematical equality across exact numeric kinds

R18 currently defines an Integer/float bridge because current fractional values are binary floats. This future release must explicitly reconcile R18 rather than bypass it.

Working direction:

- booleans remain distinct from numbers
- numerically equal Integer, Decimal, and Rational values compare equal
- Decimal lexical scale is not numeric identity (`1.0 == 1.00`)
- equal exact numeric values have identical map-key equivalence
- equality remains pure, host-independent, and non-user-overloadable

Conceptually, internal key/equality normalization may use a reduced mathematical ratio for exact-number identity, but that representation remains private and does not imply that every runtime exact value becomes Rational.

### Decimal is not Java BigDecimal semantics

Java `BigDecimal` is an implementation analogy, not the Genia contract.

In particular, Genia should not inherit scale-sensitive `BigDecimal.equals()` semantics. Numeric identity is mathematical; presentation scale belongs to formatting unless a later concrete use case justifies additional metadata.

### Explicit approximate hardware floating point

`Float64` exposes IEEE-754 binary64 behavior deliberately, including the realities that exact-number defaults avoid:

- finite approximation
- signed zero
- infinities where supported
- NaN/non-reflexivity
- hardware/library performance characteristics

`Float64` is not the top of the exact promotion lattice. Mixed exact/Float64 arithmetic must not silently convert an exact operand to Float64. A program that wants approximate arithmetic must cross the conversion boundary explicitly.

Future `Float32`/`bfloat16`/other hardware-oriented types are outside the first contract unless concrete interoperability needs justify them.

## JSON boundary decision

### Preserve generic JSON as an interoperability boundary

The current R9 JSON contract deliberately uses a narrower portable numeric domain than Genia's internal Integer domain. It rejects integers outside `[-9007199254740991, 9007199254740991]` and rejects non-finite/overflow binary64 JSON numbers. The exact-numeric release must not silently erase that interoperability decision merely because Genia itself gains larger exact number kinds.

RFC 8259 permits implementations to impose number range/precision limits and specifically identifies binary64 range/precision and the `[-(2^53)+1, (2^53)-1]` integer interval as important interoperability guidance. Genia's existing R9 boundary is therefore a deliberate transport policy rather than evidence that internal arithmetic should be binary64.

### Working generic `json_encode` policy

Generic `json_encode` remains an interoperability-oriented JSON sink.

- Integer: encodable as a JSON number only inside the existing R9 safe-integer interval.
- Decimal: encodable as a JSON number only when the exact Decimal value lies inside the approved R9 interoperable numeric domain that this release will define precisely; encoding must never silently round the Decimal.
- Rational: not generically JSON-number encodable unless it has an exact finite decimal representation and that exact Decimal representation satisfies the same interoperable-domain rule. A non-terminating Rational such as `1/3` is rejected rather than rounded.
- Float64: finite values may use the explicitly approved Float64 JSON rule; NaN and infinities remain outside JSON number syntax and are rejected.

The contract phase must pin the exact decimal range/precision predicate used by the retained interoperable JSON domain. The key rule is already decided: **generic JSON serialization either preserves the exact numeric value under the approved JSON-domain policy or rejects it; it never rounds an exact Genia number merely to make it fit JSON.**

### Working generic `json_decode` policy

JSON numeric tokens are parsed from their decimal lexical spelling without first passing through host binary floating point.

- integer-form token -> Integer, subject to the retained R9 safe-integer acceptance boundary
- fraction/exponent token -> exact Decimal derived from the token's base-10 value, subject to the retained portable JSON-domain range/precision boundary
- JSON never directly produces Rational because every valid JSON number token denotes a finite base-10 decimal value
- non-finite spellings remain invalid JSON

The future implementation must therefore avoid a host parser path that first converts JSON fractions to binary64 and only afterward constructs Decimal.

### Exact values outside the generic JSON domain

The exact numeric model does not force generic JSON to become an arbitrary-precision interchange protocol.

Applications that need lossless arbitrary Integer/Decimal/Rational interchange must use an explicit representation/schema rather than smuggling values through lossy JSON numbers. Candidate explicit encodings belong to later R9 representation/schema work or the numeric contract if concrete proving cases require them; examples could be tagged JSON objects or strings, but this pre-flight intentionally does not choose one.

This separation preserves both goals:

- Genia arithmetic is exact by default.
- Generic JSON remains conservative about ecosystem interoperability.

## Exact <-> Float64 conversion decision

### Exact to Float64

Conversion from Integer, Decimal, or Rational to `Float64` is explicit.

Working rule:

1. Interpret the exact source as its mathematical real value.
2. Convert to IEEE-754 binary64 using round-to-nearest, ties-to-even.
3. If the magnitude exceeds the largest finite binary64 value, fail deterministically rather than silently produce infinity unless a later explicitly named saturating/IEEE conversion operation is approved.
4. An exact mathematical zero converts to positive zero; the exact family has no negative-zero identity to preserve.

This makes the ordinary conversion boundary safe by default while still allowing a later explicitly named low-level conversion to expose raw IEEE overflow behavior if a real interoperability need appears.

The conversion is deterministic and host-independent; a host's default cast is acceptable only when it is proven to implement the contracted result for the source domain.

### Float64 to exact

A finite `Float64` has one exact mathematical dyadic-rational value. Because its denominator is a power of two, that value also has a finite base-10 decimal expansion.

The default exact conversion from finite Float64 therefore returns the exact Decimal value represented by the Float64 bits, **not** the shortest human decimal that would round back to the same Float64.

Example semantic distinction:

```text
Float64 produced from Decimal 0.1
-> exact(Float64) yields
   Decimal 0.1000000000000000055511151231257827021181583404541015625
not Decimal 0.1
```

This is intentional: exact conversion reveals the value actually represented by the approximate number and never fabricates precision that was already lost.

Rules:

- finite Float64 -> exact Decimal representing the binary64 value exactly
- +0.0 -> exact Decimal zero
- -0.0 -> exact Decimal zero; sign-of-zero is a Float64-only property and is lost when crossing into the exact family
- NaN -> deterministic conversion failure
- +infinity/-infinity -> deterministic conversion failure

If callers want a short human-facing decimal that round-trips to the same Float64, that is a distinct formatting or explicitly named approximation operation, not the exact conversion.

### Rational and direct Float64 conversion

Rational -> Float64 follows the same explicit correctly-rounded rule as any exact source; it need not detour through Decimal.

Float64 -> Rational need not be a separate primitive in the first contract because exact Float64 -> Decimal is always possible for finite binary64 values. A later `rational(...)` conversion can convert that Decimal exactly if a Rational carrier is specifically desired.

### Mixed arithmetic

No automatic bridge is introduced by conversion support.

Examples of intended policy:

```text
Decimal + Float64  -> reject mixed exact/approximate arithmetic
Rational * Float64 -> reject mixed exact/approximate arithmetic
Float64 + Float64  -> IEEE-754 Float64 arithmetic
```

The caller chooses the semantic domain explicitly by converting one side first.

### Equality with Float64

The contract phase must reconcile R18's current Integer/float equality rule with the new exact family. Preferred direction:

- Float64 may compare equal to an exact numeric value only when the finite Float64's exact mathematical value equals that exact value.
- no lossy conversion of the exact operand to Float64 may be used to decide equality
- NaN remains unequal to every value, including itself
- +0.0 and -0.0 remain Float64-equal to exact zero if the R18 bridge is generalized as expected

This keeps equality mathematical while arithmetic promotion remains explicit.

## Other required contract decisions

Before implementation, the dedicated release must still pin at least:

1. final literal syntax/classification for Decimal and explicit Float64
2. final Rational construction spelling (do not assume a new literal; `/` plus `rational(n,d)` may be sufficient)
3. zero/sign representation rules for Decimal and Rational
4. canonical Decimal and Rational display/debug rendering
5. exact portable JSON decimal range/precision predicate that preserves the intended R9 interoperability boundary
6. format-spec behavior for Decimal/Rational/Float64
7. resource-exhaustion behavior for arbitrarily large coefficients/numerators/denominators
8. transcendental/irrational operations and explicit precision/rounding contexts
9. Core IR representation sufficient for independent hosts
10. shared conformance evidence proving all of the above without Python numeric defaults

The promotion/division matrix, generic JSON no-silent-rounding rule, and default exact<->Float64 conversion direction are no longer open design questions in this pre-flight; the dedicated contract must express them byte/bit-exactly and reconcile existing implemented behavior before implementation.

## Rational-specific regrets to address explicitly

Rational values solve exact non-terminating division but introduce their own costs:

- numerator/denominator growth can be large
- canonical reduction via gcd costs time
- map-key hashing/canonicalization must agree with mathematical equality
- formatting must distinguish exact rational form from rounded decimal presentation
- JSON has no native rational kind, so generic JSON rejects non-terminating Rational values unless an explicit representation is used
- transcendental functions still require approximation even when the input is Rational

These are acceptable costs only if the contract makes them visible and deterministic rather than implicit.

## Relationship to completed releases

The future numeric release must preserve or deliberately supersede, through an explicit later contract:

- R17 arbitrary-precision Integer semantics
- R18 one canonical `==`, map-key equivalence, boolean separation, protection rules, and non-user-overloadability
- R9 JSON representation boundaries
- R16 multi-host evidence discipline

Completed R17/R18 history remains truthful. A later release may extend the numeric family and supersede specific current float assumptions; it must not rewrite history as though Decimal/Rational were already implemented.

## Relationship to R19

R19 proceeds with Unicode and diagnostic portability only.

The existing R19 float inventory remains useful as evidence of current Python-host behavior and of what must eventually be migrated or preserved for explicit `Float64`, but R19 must not canonize that behavior as the default fractional-number model.

## Relationship to the C++ host

The first semantic C++ host must not begin numeric implementation until this numeric contract is approved and complete. Otherwise the current Python binary-float accident risks becoming de facto multi-host Genia semantics.

## Non-goals of this pre-flight

- no implementation
- no release renumbering
- no final source syntax
- no arbitrary-precision rational library selection
- no arbitrary-precision decimal library selection
- no C++ library choice
- no approximate equality
- no complex numbers
- no units/dimensions
- no transcendental API design
- no generic arbitrary-precision JSON-number promise

## Go/no-go

**GO for dedicated numeric-model contract exploration using the working promotion/division, JSON, and exact<->Float64 boundary decisions recorded here.**

**NO-GO for implementation until the remaining representation/Core-IR/formatting/resource/transcendental decisions are explicitly approved through the dedicated release gate.**
