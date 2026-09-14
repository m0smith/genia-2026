# Exact Numeric Model — Release Ownership

Status: **approved semantic-decision partition; not implemented by this document.** `GENIA_STATE.md` remains final authority for implemented behavior.

This document repartitions the approved Exact Numeric Model contract from issue #838 / PR #839 into numbered release ownership. It does **not** change the semantic decisions made there and does not claim the #839 implementation is merged.

Immutable design evidence used for this partition: PR #839 head `856616e66028f00c51fb7aea2df7d0527ce8996f`, especially `docs/design/exact-numeric-model-contract.md` at that revision.

## Shared model retained unchanged

The approved model remains:

- Integer — arbitrary-precision exact integer, preserving R17
- Decimal — arbitrary-precision exact base-10 value
- Rational — exact reduced ratio of arbitrary-precision integers
- Float64 — explicit IEEE-754 binary64 approximate value
- Integer, Decimal, and Rational form the exact family
- Float64 is explicit and is not the top of the exact promotion lattice
- source Decimal parsing is lexical/base-10 and must never pass through Float64
- no new numeric Core IR node family is introduced
- R18 remains authoritative for equality/key architecture
- R19 remains authoritative for diagnostic portability

## R21 — Numeric Source and Portable Representation

R21 owns the source/portable-representation portion of the approved contract.

Owned decisions:

- numeric lexical classification: Integer versus Decimal
- dotted and exponent Decimal forms
- source sign remains unary lowering, not part of the numeric token
- leading-dot/trailing-dot forms remain outside the approved numeric literal grammar
- source Decimal parsing is lexical/base-10
- portable Core IR node family remains unchanged
- numeric literals lower through `IrLiteral`
- `/` remains `IrBinary(op=SLASH)`
- numeric `IrLiteral.value` uses tagged semantic payloads
- Integer payload uses canonical unsigned base-10 `digits`
- Decimal payload uses canonical base-10 `coefficient` and `exponent` strings
- equivalent Decimal spellings normalize to the same portable payload
- no Rational literal payload and no direct Float64 literal payload in this release
- no `IrDecimal`, `IrRational`, or `IrFloat64` node family

Contract-source mapping from the #838 design: sections 1-2 and 11, plus only the compatibility/error language necessary to specify those boundaries.

R21 explicitly does **not** own runtime Decimal/Rational/Float64 arithmetic, conversions, cross-kind equality, rendering, JSON, or numeric field formatting.

Acceptance shape:

> A host can classify and lower numeric source into the same portable tagged Core IR without consulting Python numeric behavior.

## R22 — Exact Numeric Runtime

R22 owns the runtime numeric value model and mathematical behavior.

Owned decisions:

- Decimal semantic value and canonicalization
- Rational semantic value, reduction, positive denominator, and denominator-one collapse to Integer
- explicit Float64 semantic value
- `rational(numerator, denominator)` constructor behavior
- `float64(value)` exact-to-binary64 conversion behavior
- `exact(value)` Float64-to-exact behavior
- exact-family promotion for `+`, `-`, and `*`
- exact division and exact floor remainder
- Float64 arithmetic in the explicit approximate domain
- rejection of mixed exact/Float64 arithmetic unless the caller explicitly converts domains
- exact-family comparison by mathematical value
- finite Float64 comparison to exact values by the Float64 value's exact represented dyadic value
- NaN non-reflexivity/unordered behavior and R18 legal-key consequences
- numeric map-key equivalence remains the same relation as `==`
- booleans remain distinct from numbers
- arbitrary precision defines the mathematical domain while normalized `numeric-resource-limit` may represent implementation limits
- no ambient mutable precision context
- future approximation/transcendental work may not silently fall back to binary float
- deterministic numeric misuse/error classes remain normalized under R19 diagnostic rules

Contract-source mapping from the #838 design: sections 3-10 and 15-18, excluding presentation/interchange details owned by R23.

R22 explicitly does **not** own JSON transport policy or display/format spelling.

Acceptance shape:

> Equivalent numeric computations and comparisons produce the same mathematical values and portable failures across conforming hosts, independent of host integer/float/library defaults.

## R23 — Numeric Representation and Interchange

R23 owns the boundaries that turn numeric values into textual/data representations or reconstruct them from those approved boundaries.

Owned decisions:

- canonical Decimal display/debug rendering
- canonical Rational display/debug rendering
- explicit constructor-shaped Float64 display/debug rendering
- strict generic JSON Integer safe-range behavior retained from R9
- `stable_json_decimal` policy
- generic JSON acceptance/rejection for Decimal, Rational, and Float64
- lexical JSON fraction/exponent decode directly to exact Decimal without a binary-float intermediate
- JSON never directly constructs Rational
- non-finite Float64 values remain rejected by generic JSON
- existing numeric format-spec presentation integrates Decimal/Rational/Float64 without changing their value kinds
- `.n` presentation continues decimal half-up behavior
- formatting starts from the exact Decimal/Rational value or exact dyadic Float64 value rather than an arbitrary host formatter
- compatibility JSON entry points must not preserve a contradictory host-float numeric model
- R19 diagnostic normalization continues to govern all representation/interchange failures

Contract-source mapping from the #838 design: sections 12-14 and the representation/interchange portions of sections 17 and 19.

Acceptance shape:

> Display/debug, formatting, and JSON boundaries preserve the approved numeric distinctions and never reintroduce host binary-float semantics implicitly.

## Cross-release invariants

The following are unchanged throughout R21-R23:

- R17 arbitrary-precision Integer semantics stay authoritative.
- R18 equality/key architecture stays authoritative; R22 extends the numeric cases within that architecture rather than creating a second equality model.
- R19 Unicode and diagnostic portability stay authoritative.
- R20 open-function semantics are unaffected.
- Generic JSON remains an interoperability boundary, not arbitrary-precision numeric transport.
- No Rational literal syntax, Float64 suffix/raw-bit source syntax, approximate equality, user-overloadable equality, ambient decimal context, complex/units/dimensions, or transcendental APIs are introduced by this partition.

## Delivery discipline

Each release is implemented through multiple independently mergeable PRs against current `main` as appropriate. A release audit runs against merged `main`. Defects discovered by the audit become narrow repair issues/PRs and require a fresh audit.

The #839 implementation branch is evidence, not a cherry-pick plan.

R24 — C++ Minimal Conforming Host — may consume the completed R21-R23 contracts and shared evidence but must not use C++ implementation choices to fill semantic gaps.
