# Exact Numeric Model — Resolved Design Decisions

Status: **Planning design — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

This document supplements `docs/design/exact-numeric-model-preflight.md`. It records the resolved working directions for the three design questions left open after the promotion/division, JSON, and exact↔Float64 boundary review. It changes no runtime behavior, parser/Core IR implementation, shared spec, or implemented-language truth.

## 1. Canonical Decimal and Rational rendering

### 1.1 Decimal semantic normalization

A Decimal value is modeled semantically as an arbitrary-precision integer coefficient and a base-10 exponent:

```text
value = coefficient × 10^exponent
```

The host representation is private. The semantic canonicalization rule is:

- zero canonicalizes to coefficient `0`, exponent `0`
- for nonzero values, remove all trailing decimal zero digits from the absolute coefficient and increase the exponent by the number removed
- sign belongs to the coefficient/value, not to a separate negative-zero state
- Decimal therefore has exactly one mathematical zero; negative zero is a Float64-only property
- lexical scale is not retained as numeric identity

Examples:

```text
1.0       -> coefficient 1, exponent 0, Decimal kind retained
1.00      -> coefficient 1, exponent 0, Decimal kind retained
123.4500  -> coefficient 12345, exponent -2
0.00100   -> coefficient 1, exponent -3
```

`1.0` and `1.00` therefore become the same Decimal value, while still remaining Decimal rather than Integer.

### 1.2 Decimal canonical display/debug

Decimal display and debug use the same canonical numeric atom text. A Decimal rendering must round-trip through the eventual Decimal literal grammar without consulting host float formatting.

Let:

- `digits` be the base-10 digits of the absolute nonzero canonical coefficient
- `adjusted_exponent = len(digits) + exponent - 1`

Use fixed notation when:

```text
-6 <= adjusted_exponent <= 20
```

and scientific notation otherwise.

Fixed notation rules:

- insert the decimal point according to the canonical exponent
- use no grouping separators
- use `.` as the decimal separator
- emit no insignificant trailing fractional zeros
- if the mathematical value is integral, append `.0` so Decimal remains visibly distinct from Integer

Examples:

```text
Decimal 0              -> 0.0
Decimal 1              -> 1.0
Decimal 1.25           -> 1.25
Decimal 0.000001       -> 0.000001
Decimal 1000000000000  -> 1000000000000.0
```

Scientific notation rules:

- exactly one coefficient digit before the decimal point
- remove insignificant trailing fractional zeros
- if there is only one significant digit, retain `.0`
- lowercase `e`
- exponent always has an explicit `+` or `-`
- exponent has no unnecessary leading zeros

Examples:

```text
1e21 Decimal     -> 1.0e+21
1.23e25 Decimal  -> 1.23e+25
1e-7 Decimal     -> 1.0e-7
```

The fixed/scientific thresholds are part of the portable rendering contract rather than a host formatter default.

### 1.3 Rational canonicalization and rendering

A Rational is represented semantically by arbitrary-precision Integer numerator and denominator values.

Canonicalization rules:

- denominator must be nonzero
- reduce numerator and denominator by their positive gcd
- denominator is always positive; any sign is carried by the numerator
- a reduced denominator of `1` canonicalizes to Integer, so a surviving Rational always has denominator greater than `1`

Canonical display/debug for a surviving Rational is:

```text
<numerator>/<denominator>
```

with no spaces and with both integers in canonical decimal Integer form.

Examples:

```text
2/6    -> 1/3
-2/6   -> -1/3
2/-6   -> -1/3
-2/-6  -> 1/3
6/3    -> Integer 2
```

Rational display is exact. Rendering a Rational as a rounded decimal requires an explicitly named formatting/approximation operation and is never ordinary display/debug behavior.

## 2. Portable Core IR representation

### 2.1 Preserve the frozen node family

The existing portable Core IR node family remains intact. Numeric work does not add `IrDecimal`, `IrRational`, or `IrFloat64` node families.

Source numeric constants continue to lower through `IrLiteral`. Ordinary division remains `IrBinary(op=SLASH)`. Explicit constructors/conversions such as future `rational(...)` and `float64(...)` spellings lower through ordinary `IrCall` unless a later separately approved syntax contract requires otherwise.

This preserves the established parser → portable Core IR → evaluator boundary and keeps host-local optimized numeric representation outside the shared contract.

### 2.2 Host-neutral numeric `IrLiteral` payload

The normalized portable representation of a numeric `IrLiteral` must not contain a host-native arbitrary integer, host Decimal object, or binary floating object whose serialization can change by host.

Numeric literal values use a tagged semantic payload inside the existing `value` field.

Integer:

```json
{
  "node": "IrLiteral",
  "value": {
    "kind": "integer",
    "digits": "123456789012345678901234567890"
  }
}
```

`digits` is canonical base-10 integer text with no leading zeros except `0`. Current unary-minus lowering remains authoritative: a surface negative literal may still lower as `IrUnary(MINUS, IrLiteral(...))` rather than embedding the sign into the positive literal payload.

Decimal:

```json
{
  "node": "IrLiteral",
  "value": {
    "kind": "decimal",
    "coefficient": "12345",
    "exponent": "-2"
  }
}
```

Both coefficient and exponent are encoded as canonical base-10 strings so the portable IR envelope itself imposes no host integer-width limit. Decimal payloads are semantically canonicalized before normalized IR comparison; `1.0`, `1.00`, and `100e-2` therefore lower to the same Decimal semantic payload when the eventual literal grammar classifies them as Decimal.

Float64, if a future approved source form materializes a Float64 constant directly in Core IR, is represented by its exact IEEE-754 binary64 bits rather than host decimal text:

```json
{
  "node": "IrLiteral",
  "value": {
    "kind": "float64",
    "bits": "3fb999999999999a"
  }
}
```

The bit string is exactly 16 lowercase hexadecimal digits in network/significance order. This preserves signed zero, infinities, and finite values exactly and avoids host formatting drift. A future contract must decide whether NaN payload/sign bits are semantically preserved or canonicalized before permitting direct Float64 literal payloads.

### 2.3 Rational does not require a portable literal payload initially

The first exact-numeric contract does not require a Rational literal syntax. `1 / 3` remains an ordinary `IrBinary(op=SLASH)` over Integer literals, and `rational(n, d)` remains an ordinary call if that constructor spelling is approved.

A host computes the Rational value during evaluation. Host-local constant folding may represent that value however it chooses after the portable Core IR boundary.

If a future release adds direct Rational literal syntax, it may extend the tagged `IrLiteral.value` payload with a rational kind; it still does not require a new Core IR node family.

### 2.4 Consequence for existing IR evidence

The numeric release will deliberately change normalized portable IR snapshots for numeric literals from untagged host values to tagged semantic payloads. That is a contract revision, not a new node-family revision. Existing nonnumeric `IrLiteral` payloads remain unchanged unless the implementation slice discovers a concrete portability reason to generalize the tagging scheme.

The TEST phase must update/add shared IR evidence only after the numeric contract is approved.

## 3. Irrational and transcendental precision

### 3.1 No implicit Float64 escape

Exact numeric operations never fall back to Float64 because an exact result is irrational or otherwise not representable by Integer/Decimal/Rational.

Examples such as `sqrt(2)`, `sin(1)`, `log(10)`, and mathematical constants such as π require an explicit approximation boundary. The host must not silently use a hardware double and wrap the result as Decimal.

### 3.2 No ambient/global precision

Genia does not acquire an ambient decimal precision or mutable process-global numeric context.

Approximation is controlled by an explicit immutable precision context value passed to the operation (exact source spelling/API remains a later contract detail).

The semantic context contains at least:

```text
precision_digits : positive Integer
rounding         : closed rounding mode
```

`precision_digits` means decimal **significant digits**, not digits after the decimal point.

The initial required rounding mode is:

```text
half_even
```

Additional rounding modes may be added later only by extending the closed set deliberately; hosts must not inherit whatever modes their decimal library happens to expose.

### 3.3 Result contract

An exact-input irrational/transcendental operation using an explicit precision context returns Decimal, never Float64 implicitly.

The returned Decimal is the correctly rounded exact mathematical result to the requested number of decimal significant digits using the requested rounding mode.

Examples of intended semantics, not final API spelling:

```text
sqrt(2, precision(50, half_even)) -> Decimal rounded to 50 significant digits
pi(precision(100, half_even))     -> Decimal rounded to 100 significant digits
sin(1, precision(40, half_even))  -> Decimal rounded to 40 significant digits
```

When the exact mathematical result is finitely representable in Decimal and requires fewer than the requested digits, no artificial noise is added; the canonical Decimal result is returned.

A host that cannot meet the contracted rounding guarantee must report the operation unsupported/fail through the approved capability boundary. It must not substitute host `double`, platform `libm`, or another lower-precision result and claim conformance.

### 3.4 Keep transcendental implementation out of the first exact-number release unless required

The exact-numeric release establishes the approximation boundary and context semantics so future work cannot accidentally introduce ambient or binary-float defaults. It need not implement a transcendental library merely to complete Integer/Decimal/Rational/Float64 foundations.

If no existing public Genia transcendental surface requires migration, actual `sqrt`/`sin`/`log`/π functions should be a separately scoped later release or capability slice with their own conformance evidence.

### 3.5 Float64 transcendental operations are a separate approximate domain

Future explicitly named Float64 math operations may use IEEE-754/binary64-oriented semantics and performance libraries, but their results stay Float64 and remain separate from the exact+precision-context Decimal path.

There is no automatic exact ↔ Float64 crossing simply because the operation is transcendental.

## 4. Resulting resolved model

With the earlier pre-flight decisions plus this document, the working numeric model now has these settled directions:

1. `Integer`, `Decimal`, and `Rational` are exact; `Float64` is explicit approximate binary64.
2. `+`, `-`, `*` use the exact promotion lattice `Integer < Decimal < Rational`.
3. `/` preserves exactness and introduces Rational when needed rather than rounding.
4. Decimal lexical scale is not value identity.
5. Rational is reduced canonically; denominator-one values collapse to Integer.
6. Generic JSON never rounds exact Genia values to force interoperability.
7. exact → Float64 is explicit round-to-nearest/ties-to-even with ordinary overflow failure.
8. finite Float64 → exact reconstructs the exact represented value as Decimal.
9. Decimal and Rational display/debug are canonical and host-neutral as specified above.
10. Numeric Core IR stays within `IrLiteral`/`IrBinary`/`IrCall`; tagged payloads remove host numeric serialization authority.
11. Irrational/transcendental approximation requires an explicit immutable decimal precision context; there is no ambient precision and no implicit Float64 fallback.

## 5. Still open before implementation

The dedicated numeric contract must still resolve or formally ratify:

- final source spelling for Decimal/Float64 constructors or literal suffixes
- exact portable JSON Decimal range/precision predicate
- detailed format-spec behavior beyond ordinary canonical display/debug
- resource-exhaustion/implementation-limit behavior for enormous coefficients, numerators, denominators, exponents, and requested precision
- whether direct Float64 NaN literal/IR payloads preserve or canonicalize NaN sign/payload bits
- exact capability/API surface for future transcendental functions, if any are included at all
- shared parse/IR/eval/error evidence after approval

## Go/no-go

**GO for incorporating these resolved decisions into the dedicated exact-numeric contract.**

**NO-GO for runtime/parser/Core IR/spec implementation until that contract is explicitly approved and the remaining boundary details above are resolved.**
