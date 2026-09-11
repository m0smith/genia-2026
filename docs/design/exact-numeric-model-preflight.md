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

This document does not implement those kinds, choose final syntax, or revise current truth.

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
- exact division must preserve an exact result rather than silently round
- no conforming host may substitute binary floating point for Decimal or Rational because it is convenient

### Rational closes the division gap

Supporting Rational changes the preferred division model.

Instead of failing or rounding when an exact quotient has no finite decimal expansion, exact division can produce an exact Rational.

Candidate result-normalization direction, subject to contract approval:

- results equivalent to an Integer may normalize to Integer
- results with an exact finite base-10 representation may normalize to Decimal when that preserves the approved operation/result-kind rules
- otherwise exact quotients remain Rational

The exact promotion/normalization matrix is an approval blocker; this pre-flight does not lock it.

### Mathematical equality across exact numeric kinds

R18 currently defines an Integer/float bridge because current fractional values are binary floats. This future release must explicitly reconcile R18 rather than bypass it.

Preferred direction:

- booleans remain distinct from numbers
- numerically equal Integer, Decimal, and Rational values compare equal
- Decimal lexical scale is not numeric identity (`1.0 == 1.00`)
- equal exact numeric values have identical map-key equivalence
- equality remains pure, host-independent, and non-user-overloadable

Whether and how explicit `Float64` participates in exact cross-kind equality must be separately specified. A likely rule is equality only when the Float64 value exactly denotes the same mathematical value, preserving the spirit of R18's current Integer/float bridge.

### Decimal is not Java BigDecimal semantics

Java `BigDecimal` is an implementation analogy, not the Genia contract.

In particular, Genia should not inherit scale-sensitive `BigDecimal.equals()` semantics. Numeric identity should be mathematical, while presentation scale belongs to formatting unless a later concrete use case justifies additional metadata.

### Explicit approximate hardware floating point

`Float64` is expected to expose IEEE-754 binary64 behavior deliberately, including the realities that exact-number defaults avoid:

- finite approximation
- signed zero
- infinities where supported
- NaN/non-reflexivity
- hardware/library performance characteristics

Conversions between exact numeric kinds and `Float64` must be explicit and precisely specified, including rounding behavior and whether exact conversion back exposes the exact decimal value represented by the binary64 bits.

Future `Float32`/`bfloat16`/other hardware-oriented types are outside the first contract unless concrete interoperability needs justify them.

## Required contract decisions

Before implementation, the release must pin at least:

1. literal syntax/classification for Decimal and explicit Float64
2. Rational construction/syntax (do not assume `1/3` is a literal; it may remain division)
3. arithmetic promotion/result-kind matrix across Integer/Decimal/Rational
4. exact division normalization rules
5. zero/sign rules for exact numeric kinds
6. canonical Decimal and Rational representations/rendering
7. equality and legal-map-key behavior across exact kinds and Float64
8. conversion semantics between exact kinds and Float64
9. overflow/resource-exhaustion model for arbitrarily large coefficients/numerators/denominators
10. JSON encode/decode compatibility and exactness boundaries
11. format-spec behavior for Decimal/Rational/Float64
12. transcendental/irrational operations and explicit precision/rounding contexts
13. Core IR representation sufficient for independent hosts
14. shared conformance evidence proving all of the above without Python numeric defaults

## Rational-specific regrets to address explicitly

Rational values solve exact non-terminating division but introduce their own costs:

- numerator/denominator growth can be large
- canonical reduction via gcd costs time
- map-key hashing/canonicalization must agree with mathematical equality
- formatting must distinguish exact rational form from rounded decimal presentation
- JSON has no native rational kind, so boundary policy must be explicit
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

R19 should proceed with Unicode and diagnostic portability only.

The existing R19 float inventory remains useful as evidence of current Python-host behavior and of what must eventually be migrated or preserved for explicit `Float64`, but R19 must not canonize that behavior as the default fractional-number model.

## Relationship to the C++ host

The first semantic C++ host must not begin numeric implementation until this numeric contract is approved and complete. Otherwise the current Python binary-float accident risks becoming de facto multi-host Genia semantics.

## Non-goals of this pre-flight

- no implementation
- no release renumbering
- no final syntax
- no arbitrary-precision rational library selection
- no arbitrary-precision decimal library selection
- no C++ library choice
- no approximate equality
- no complex numbers
- no units/dimensions
- no transcendental API design

## Go/no-go

**GO for dedicated numeric-model contract exploration.**

**NO-GO for implementation until the promotion/division/equality/representation/boundary decisions above are explicitly approved through its own release gate.**
