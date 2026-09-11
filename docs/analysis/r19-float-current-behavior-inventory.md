# Float Rendering Current-Behavior Inventory

Status: **Planning analysis — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

This inventory was created during R19 E19-0 and records current Python reference-host float rendering behavior. It is now retained as input to the separate exact-numeric-model workstream rather than as an R19 implementation target.

R19 no longer owns float canonicalization. See `docs/design/exact-numeric-model-preflight.md`.

## Current implementation facts

General rendering is in `src/genia/utf8.py`:

- `format_display(value)` has no explicit float branch; floats fall through to Python `str(value)`.
- `format_debug(value)` has no explicit float branch; floats fall through to Python `repr(value)`.
- On current Python, `str(float)` and `repr(float)` generally use Python's shortest-round-trip-style decimal rendering, but that is a Python implementation/library contract, not Genia semantic authority.

The format engine adds more numeric rendering behavior:

- numeric precision formatting builds `Decimal(repr(value))` and rounds with `ROUND_HALF_UP` to the requested decimal places.
- zero-padding starts from `format_display(value)`.
- grouping starts from `format_display(value)` and then groups the integer part.

Therefore a future host cannot reproduce current numeric output reliably by choosing arbitrary `printf`, iostream, `to_chars`, or library defaults.

## Why the original F1 blocker was split out

The initial R19 draft treated the problem as canonical binary64 rendering. During E19-0 review, the preferred language direction changed:

- ordinary decimal-point/exponent numbers should be exact arbitrary-precision Decimal values rather than implicit binary64
- exact Rational values should represent non-terminating exact quotients such as `1 / 3`
- IEEE-754 binary64 should remain available explicitly as `Float64` (final syntax/name subject to contract)

That change affects literal semantics, Core IR, arithmetic, division, equality, map keys, JSON boundaries, conversions, and formatting. It therefore requires its own semantic release rather than an R19 rendering patch.

## Current float inventory matrix

| Surface | Python reference-host behavior today | Future numeric-contract question |
|---|---|---|
| Ordinary fractional literal | becomes Python `float` | Reclassify ordinary decimal literals as exact Decimal. |
| Ordinary float display | Python `str(float)` | Specify only for explicit Float64 after numeric model is approved. |
| Float debug rendering | Python `repr(float)` | Specify only for explicit Float64 after numeric model is approved. |
| Integral-looking float | Python commonly emits `1.0` | Decide explicit Float64 rendering separately from Decimal rendering. |
| Negative zero | Python preserves `-0.0` | Remains relevant to explicit Float64, not exact Decimal identity. |
| Exponent marker/sign/digits | Python formatting rules | Must become explicit for Float64 if retained. |
| Exponent switch threshold | Python threshold/algorithm | Must become explicit for Float64 if retained. |
| NaN / infinities | Python `nan`, `inf`, `-inf` | Belong to explicit Float64 semantics, not exact Decimal/Rational. |
| Precision spec | `Decimal(repr(value))`, then quantize ROUND_HALF_UP | Must be redesigned/reconciled across Decimal/Rational/Float64. |
| Zero padding/grouping | based on ordinary display text | Must follow the approved numeric rendering model. |

## Relationship to R17/R18

Current implemented truth remains unchanged until a later numeric release lands.

Today R18 owns:

- Integer/float exact cross-kind equality
- signed-zero equality
- infinity and NaN equality behavior
- legal map-key behavior for current floats

The future numeric release must explicitly supersede/reconcile those current float assumptions rather than silently reinterpret completed R18 history.

Preferred future direction, not yet implemented:

- Integer, Decimal, and Rational participate in exact mathematical cross-kind equality
- Decimal lexical scale is not numeric identity
- exact numeric map-key equivalence follows exact mathematical equality
- explicit Float64 participates only under a precisely specified bridge, likely when it exactly denotes the same mathematical value
- NaN remains non-reflexive only within explicit hardware-float semantics

## Evidence retained for the future numeric release

The following binary64 cases remain useful for explicit Float64 portability:

- `0.0`
- `-0.0`
- `1.0`
- ordinary finite fraction
- precision-sensitive values such as binary64 `0.1`
- exponent-switch boundaries
- minimum/maximum normal/subnormal representatives where practical
- `inf`, `-inf`, `nan`
- nested display/debug contexts

Additional exact-number evidence will be required for Decimal and Rational and is not defined by this inventory.

## Implementation-impact locations for the future numeric release

At minimum:

- lexer/parser numeric literal classification
- portable Core IR numeric representation
- evaluator arithmetic/division
- `src/genia/equality.py`
- map-key canonicalization
- `src/genia/utf8.py`
- `src/genia/_format_engine.py`
- JSON encode/decode boundaries
- host adapters/interop conversions
- shared parse/IR/eval/error/CLI evidence

## Non-goals of this inventory

- no runtime changes
- no final Decimal/Rational/Float64 syntax
- no promotion matrix
- no final Float64 rendering algorithm
- no library selection
