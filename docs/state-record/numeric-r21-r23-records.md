# R21-R23 numeric record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Sections 9.21-9.37, ticket by ticket.
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B239: baseline lines 4860-4910

Moved from GENIA_STATE.md@d401f322, lines 4860-4910 (ledger row B239, moved, sha256 7fe9fc53ec58743b)

~~~~~markdown
## 9.21) R21 E21-1 numeric source classification and lexical exactness (issue #853)

Implements only the source-classification portion of
`docs/design/r21-numeric-source-portable-representation-contract.md`
(sections 2-3). Numeric source literals now classify as Integer or Decimal
source purely lexically, with zero host binary-float construction during
classification:

- `DIGIT+` classifies as Integer source.
- `DIGIT+ "." DIGIT+`, `DIGIT+` exponent (`e`/`E`, optional `+`/`-` sign,
  `DIGIT+`), and `DIGIT+ "." DIGIT+` exponent all classify as Decimal
  source. Exponent forms (`1e3`, `1E+3`, `1.25e-2`) are newly accepted as
  numeric literals — the lexer previously had no exponent support at all,
  so `1e3` mis-tokenized as `NUMBER "1"` followed by `IDENT "e3"` and could
  not parse as a number.
- `.5` (leading dot) and `5.` (trailing dot) remain rejected: neither is an
  R21 numeric literal, and both already produced a deterministic
  `SyntaxError` from the existing bare-`.` punctuation gap.
- A malformed exponent (`1e`, `1e+`, with no digits after the marker) is
  now a deterministic `SyntaxError("Malformed exponent in numeric literal
  at <pos>")` raised by the lexer, instead of silently leaving a dangling
  `e`/`E` for the next token.
- New `src/genia/numeric_source.py`: `classify_numeric_literal(text)`
  performs the lexical classification and, for Decimal source, canonical
  base-10 `(coefficient, exponent)` normalization (value = coefficient ×
  10^exponent; zero normalizes to `("0", "0")`; trailing base-10 zeros are
  stripped from the magnitude with a matching exponent increase). This
  function uses only string slicing and Python `int` arithmetic on
  exponent offsets — it never calls `float(...)`.
- The `Number` AST node gains `source_kind` (`"integer"`/`"decimal"`),
  `digits` (Integer only), and `coefficient`/`exponent` (Decimal only)
  fields carrying this classification. These are inert metadata in this
  ticket, consumed by a later ticket when it changes the Core IR
  `IrLiteral` payload shape; `Number.value` (the existing evaluator-facing
  `int`/`float`) and all current evaluator/runtime numeric behavior are
  unchanged.
- No Core IR or `IrLiteral` payload change; the frozen minimal portable
  Core IR node family in `docs/architecture/core-ir-portability.md` is
  unchanged. No evaluator/runtime Decimal arithmetic, equality, or
  map-key behavior is introduced.
- Shared evidence: 11 new `spec/parse/*` cases (9 accept, 2 reject) covering
  Integer classification, dotted/exponent-only/dotted-exponent Decimal
  classification, equivalent Decimal spellings, malformed-exponent
  rejection, and leading/trailing-dot rejection — proven identical through
  both the in-process path and the R16 subprocess protocol adapter.

Explicit limitations: no tagged `IrLiteral` payload (a later R21 ticket),
no Decimal/Rational/Float64 runtime arithmetic or conversions, no
equality/map-key change, and no rendering/formatting/JSON behavior (later
releases own each of those).

~~~~~

## B240: baseline lines 4911-4953

Moved from GENIA_STATE.md@d401f322, lines 4911-4953 (ledger row B240, moved, sha256 2e0b781819cd52c3)

~~~~~markdown
## 9.22) R21 E21-2 tagged portable numeric IrLiteral payloads (issue #854)

Implements section 4 of `docs/design/r21-numeric-source-portable-representation-contract.md`, consuming the E21-1 (9.21) classification:

- Integer and Decimal numeric source now lower through the existing
  `IrLiteral` node with a canonical tagged payload instead of a bare host
  number: `{"kind": "integer", "digits": "<canonical unsigned decimal
  text>"}` or `{"kind": "decimal", "coefficient": "<canonical text>",
  "exponent": "<canonical text>"}` (value = coefficient × 10^exponent).
  Every payload field is a string; no host-native binary float appears in
  the portable payload. Huge Integers preserve exact digits; equivalent
  Decimal spellings (`1.0`, `1.00`, `100e-2`) normalize to the identical
  tagged payload while remaining Decimal kind.
- Source sign remains outside the payload: `-1.25` still lowers as
  `IrUnary(MINUS, ...)` wrapping the positive tagged literal. `/` remains
  ordinary `IrBinary(op=SLASH)`, unaffected by this change.
- No new Core IR node family: `IrLiteral` is reused unchanged from the
  frozen minimal portable node family. `IrPatLiteral` (numeric literals
  in case-pattern position) is intentionally untouched by this ticket —
  only expression-position `IrLiteral` gets the tagged payload, matching
  contract section 4's scope.
- Evaluator compatibility shim (not new runtime semantics): the
  evaluator's existing `IrLiteral` handling unwraps the tagged payload
  back into exactly the same `int`/`float` value it produced before this
  ticket (`int(digits)` for Integer; `float(coefficient + "e" +
  exponent)` for Decimal — the same mathematical value as the original
  source spelling, so it rounds to the same binary64 result). All
  existing arithmetic/display/evaluation behavior for numeric literals is
  observably unchanged. This is compatibility strictly required by
  E21-2's own payload-shape change, not R22 runtime Decimal/Rational/
  Float64 materialization, arithmetic, or conversion semantics — none of
  which is implemented.
- Shared evidence: 7 new `spec/ir/*` cases (Integer/Decimal tagged
  payload shape, huge Integer, equivalent Decimal spellings,
  unary-negative lowering, slash staying ordinary binary) plus migration
  of the pre-existing numeric-literal `spec/ir/*` fixtures to the tagged
  shape, proven identical through both the in-process path and the R16
  subprocess protocol adapter.

Explicit limitations: no Decimal/Rational/Float64 runtime value, arithmetic,
equality, or map-key change; no rendering/formatting/JSON behavior (R23);
no C++ host implementation (R24).

~~~~~

## B241: baseline lines 4954-5015

Moved from GENIA_STATE.md@d401f322, lines 4954-5015 (ledger row B241, moved, sha256 5009e244d0d2b0cd)

~~~~~markdown
## 9.23) R22 E22-1 exact Decimal runtime materialization (issue #887)

Implements section 2 of `docs/design/r22-exact-numeric-runtime-contract.md`,
retiring the R21 E21-2 (9.22) evaluator compatibility shim for Decimal
payloads and replacing it with a genuine exact runtime value:

- Decimal-classified numeric source (R21 tagged `IrLiteral` payload)
  now materializes to `GeniaDecimal` (`src/genia/numeric_runtime.py`):
  an exact `coefficient × 10^exponent` value over two arbitrary-precision
  Python ints. Materialization consumes the already-canonical R21 payload
  strings directly and never transits host binary64.
- Canonicalization: zero is `(0, 0)`; otherwise trailing base-10 zeros are
  stripped from the coefficient's magnitude and the exponent increases by
  the count removed; sign is carried by the coefficient; there is no
  Decimal negative-zero identity. Decimal kind is retained even when the
  mathematical value is integral (`1.0` stays Decimal, distinct from
  Integer `1`, though the two compare equal — see below).
- Integer source is unchanged: still a Python `int` (R17 unaffected).
- Arithmetic: `GeniaDecimal` supports exact `+ - *` and unary negation,
  both Decimal-with-Decimal and Decimal-with-Integer, computed via exact
  rational cross-multiplication (never host float). This is the minimum
  needed for the new value to participate in existing evaluator arithmetic
  dispatch (`src/genia/evaluator.py` `eval_binary`, which calls the native
  operators directly) without regressing prior Decimal-literal arithmetic;
  it is not yet the full Integer/Decimal/Rational promotion lattice
  (Rational does not exist until E22-2; the full lattice is E22-3/E22-4).
  `/` and `%` are not yet implemented for `GeniaDecimal` (E22-4).
- Equality/comparison (R18, `src/genia/equality.py`): `GeniaDecimal`
  participates in the one existing R18 numeric cross-kind bridge —
  `1 == 1.0`, `1.0 == 1.00` hold by exact mathematical value, matching
  contract section 10.1. A bare host `float` does not bridge with
  `GeniaDecimal` (R22's only exact/approximate bridge is the explicit
  Float64 domain, not implemented until E22-5/E22-7). Map keys
  (`canonical_map_key`): an equal-valued Decimal and Integer share one
  key bucket; a non-integral Decimal keys on its exact reduced fraction.
- Compatibility hardening required for this slice to be mergeable in
  isolation (not new R22 policy, only recognizing the new value kind at
  existing generic-numeric dispatch points): format-spec numeric
  precision/grouping (`src/genia/_format_engine.py`), CSV cell rendering
  (`src/genia/sheet.py`), shell-stage stdin materialization
  (`src/genia/evaluator.py`), JSON Schema `"number"` type matching
  (`src/genia/builtins.py`), and R12 retrieval/rerank finite-score
  validation (`src/genia/retrieval.py`) all now recognize `GeniaDecimal`.
  Display/debug text for `GeniaDecimal` (its Python `__repr__`) was a
  placeholder at this slice's landing; R23 E23-1 (section 9.32) later made
  it the canonical rendering contract.
- R18 conformance test seam: three pre-existing R18 NaN-rejection
  conformance cases (issue #792) previously reached a host float NaN as
  an accidental byproduct of Decimal literals overflowing through the
  retired float shim; exact Decimal arithmetic is arbitrary precision and
  never overflows, closing that path. `src/genia/builtins.py` adds
  `__r18_conformance_test_only_nan`, a private, non-public host test seam
  used solely to keep that already-approved R18 evidence testable — it is
  not part of the R22 numeric surface, which exposes no public NaN/
  infinity/raw-bit constructor (contract section 4).

Explicit limitations: no Rational (E22-2); no `/` or `%` on `GeniaDecimal`
(E22-4); no explicit Float64 domain or `float64`/`exact` conversions
(E22-5/E22-6); no cross-kind Float64 comparison bridge (E22-7); no
`numeric-resource-limit` normalization (E22-8); no canonical Decimal
display/JSON (R23); no C++ host implementation (R24).

~~~~~

## B242: baseline lines 5016-5049

Moved from GENIA_STATE.md@d401f322, lines 5016-5049 (ledger row B242, moved, sha256 94f3c0ecabb11a5e)

~~~~~markdown
## 9.24) R22 E22-2 Rational runtime value and rational(...) (issue #888)

Implements section 3 of `docs/design/r22-exact-numeric-runtime-contract.md`:

- New `GeniaRational` runtime value (`src/genia/numeric_runtime.py`): an
  exact reduced ratio of two arbitrary-precision Integers. Constructed only
  through `rational_from_integers(numerator, denominator)`, which enforces
  the canonical form: nonzero denominator (else `TypeError`), gcd
  reduction, positive denominator (sign carried by the numerator), and a
  reduced denominator of `1` collapses to a plain Integer rather than a
  `GeniaRational` instance.
- New builtin `rational(numerator, denominator)`: both arguments must be
  Integer (Python `int`, never `bool`, `GeniaDecimal`, or float); a
  non-Integer argument or zero denominator is deterministic numeric misuse
  (`TypeError`, surfaced as `Error: ...` at the CLI). `rational(2, 4)` →
  `1/2`; `rational(-2, -4)` → `1/2`; `rational(2, -4)` → `-1/2`;
  `rational(2, 2)` → Integer `1`.
- Deliberately not wired into R18 equality/map-key reconciliation in this
  slice — `GeniaRational` is not yet a recognized R18 numeric kind, so
  `rational(1,2) == rational(1,2)` currently falls to R18's identity-only
  "unclassified terminal" fallback rather than comparing by mathematical
  value. Nothing in existing code or specs produces a `GeniaRational` value
  before this ticket, so this has no regression surface; full R18
  numeric-kind reconciliation for Rational lands in E22-7. Rational
  arithmetic (`+ - * / %`) is E22-3/E22-4, not this slice.
- Shared evidence: 3 new `spec/*` cases (1 eval covering construction/
  reduction, 2 error covering zero-denominator and non-Integer-argument
  misuse), proven identical through both the in-process path and the R16
  subprocess protocol adapter.

Explicit limitations: no Rational arithmetic; no Rational participation in
`==`/map keys (E22-7); no canonical Rational display/JSON (R23); no Rational
literal syntax (non-goal, contract section 15).

~~~~~

## B243: baseline lines 5050-5084

Moved from GENIA_STATE.md@d401f322, lines 5050-5084 (ledger row B243, moved, sha256 2b489c250c97a61d)

~~~~~markdown
## 9.25) R22 E22-3 exact-family +, -, *, and unary negation (issue #889)

Implements section 6 of `docs/design/r22-exact-numeric-runtime-contract.md`:
the full `Integer < Decimal < Rational` promotion lattice for `+`, `-`, `*`,
and unary negation.

- Integer/Integer arithmetic is native Python `int` arithmetic (unchanged,
  R17).
- Integer/Decimal and Decimal/Decimal arithmetic (E22-1's `GeniaDecimal`
  dunders) is unchanged: exact, and Decimal participation retains Decimal
  kind even for a mathematically integral result (`1.5 + 0.5` is Decimal
  `2`, not Integer `2`).
- Any operand that is a `GeniaRational` produces a Rational result
  (`src/genia/numeric_runtime.py` `_rational_binop`/`_rational_mul`,
  reached via Python's binary-operator protocol: `GeniaDecimal`'s dunders
  return `NotImplemented` for a `GeniaRational` operand so Python retries
  through `GeniaRational`'s reflected method). Results are exact-fraction
  cross-multiplication, then reduced and denominator-one-collapsed to
  Integer through the same `rational_from_integers` E22-2 already
  established (e.g. `rational(1,2) + rational(1,2)` is Integer `1`,
  `1 + rational(1,2)` is Rational `3/2`).
- Unary negation is defined for `GeniaDecimal` (E22-1) and now
  `GeniaRational`, preserving each value's own domain.
- Comparison/equality (`< <= > >= == !=`) between `GeniaRational` and any
  other exact kind is not implemented in this slice (E22-7); `/` and `%`
  are E22-4.
- Shared evidence: 1 new `spec/eval/*` case covering the full lattice,
  proven identical through both the in-process path and the R16 subprocess
  protocol adapter.

Explicit limitations: no `/` or `%` for Rational (E22-4); no Float64
(E22-5/E22-6); no Rational comparison/equality/map-key integration (E22-7);
no `numeric-resource-limit` normalization (E22-8); no canonical display/JSON
(R23).

~~~~~

## B244: baseline lines 5085-5129

Moved from GENIA_STATE.md@d401f322, lines 5085-5129 (ledger row B244, moved, sha256 53d7504a3a58bb78)

~~~~~markdown
## 9.26) R22 E22-4 exact division and floor remainder (issue #890)

Implements sections 7 and 8 of
`docs/design/r22-exact-numeric-runtime-contract.md`: exact `/` and floor
`%` for the Integer/Decimal/Rational exact family.

- `/` (`src/genia/numeric_runtime.py` `exact_divide`) follows the
  division-result table precisely: pure Integer/Integer division is
  Integer when evenly divisible, otherwise **Rational** -- never Decimal,
  even when the reduced denominator would otherwise terminate in base 10
  (`1 / 2` is Rational `1/2`, not Decimal `0.5`). A Decimal operand
  participating (and no Rational) yields Decimal when the reduced quotient
  terminates in base 10 (denominator has no prime factors other than 2 and
  5) -- retaining Decimal kind even for an integral quotient, matching
  E22-3's established `+`/`-`/`*` rule -- otherwise Rational. Any Rational
  operand always yields Rational (subject to E22-2's existing
  denominator-one collapse to Integer). The evaluator's `SLASH` case
  (`eval_binary` in `src/genia/evaluator.py`) now dispatches to
  `exact_divide` whenever both operands are exact-family
  (`is_exact_numeric`); non-exact operand pairs are unchanged (native `/`,
  `TypeError` → `none("type-error", ...)`).
- `%` (`exact_remainder`) is floor remainder: `q = floor(left / right);
  left % right = left - q * right`, computed via the exact rational
  quotient's floor and then reusing E22-1/E22-3's already-established `-`
  and `*` dunders across Integer/Decimal/Rational -- so its result kind
  follows the same promotion rule as `+`/`-`/`*` (section 6), not the
  division-domain-selection rule. The evaluator's `PERCENT` case dispatches
  the same way.
- Division/remainder by exact zero raises `ZeroDivisionError` with a
  deterministic, host-independent message (`"exact division by zero"` /
  `"exact remainder by zero"`) -- deliberately a different exception type
  than the evaluator's generic mixed-type `TypeError` handling, so it is
  not silently converted to a returned `none(...)` value: this preserves
  already-established pre-R22 behavior where zero division terminates
  evaluation (e.g. actor handler failure via `tests/unit/test_actors.py`).
- Shared evidence: 4 new `spec/*` cases (2 eval -- the six required proof
  examples from contract section 7, and positive/negative floor-remainder
  combinations from section 8 -- and 2 error, division/remainder by zero),
  proven identical through both the in-process path and the R16 subprocess
  protocol adapter.

Explicit limitations: no Float64 (E22-5/E22-6); no comparison/equality or
R18 map-key integration for Rational (E22-7); no `numeric-resource-limit`
normalization (E22-8); no canonical display/JSON (R23).

~~~~~

## B245: baseline lines 5130-5178

Moved from GENIA_STATE.md@d401f322, lines 5130-5178 (ledger row B245, moved, sha256 17ffe2d6362bfcf2)

~~~~~markdown
## 9.27) R22 E22-5 explicit Float64 value and conversions (issue #891)

Implements sections 4 and 5 of
`docs/design/r22-exact-numeric-runtime-contract.md`: `float64(...)` and
`exact(...)`.

- Float64 has no dedicated wrapper class: a Python `float` already is
  exactly one IEEE-754 binary64 bit pattern, which is precisely what the
  contract defines Float64 to be, and R18 already treats host `float` as a
  first-class Genia kind with correct NaN/signed-zero/infinity equality
  semantics.
- `float64(value)` (`src/genia/numeric_runtime.py` `to_float64`): accepts
  Integer/Decimal/Rational or an existing Float64 (returned unchanged).
  Exact input converts via Python's `numerator / denominator` true division
  on the value's exact `(numerator, denominator)` fraction -- CPython
  specifies and implements this as correctly rounded to the nearest
  representable float, ties-to-even, which is exactly round-to-nearest
  ties-to-even. Exact magnitude beyond the largest finite binary64 value
  fails with `OverflowError` (Python's own big-int true division already
  raises this) rather than silently producing infinity. Exact mathematical
  zero converts to positive Float64 zero (no exact value is ever
  negative-zero: Integer 0, canonical zero-identity-free `GeniaDecimal`,
  and the fact that `GeniaRational` can never itself be zero together
  guarantee this).
- `exact(value)` (`exact`): Integer/Decimal/Rational unchanged. A finite
  Float64 converts to the Decimal denoting the *exact* real value its
  binary64 bits represent, via `float.as_integer_ratio()` (CPython
  guarantees this is the exact, unrounded fraction; the denominator is
  always a power of two) scaled by the matching power of five into an
  exact power-of-ten denominator -- never through float repr/str text.
  Float64 `+0.0`/`-0.0` both convert to canonical Decimal zero. NaN and
  +/-infinity are deterministic conversion failures (`ValueError`).
  Reproduces the contract's own worked example exactly:
  `exact(float64(0.1))` denotes
  `0.1000000000000000055511151231257827021181583404541015625`.
- Both are registered as ordinary Genia builtins (`float64`, `exact`) via
  `_host_function_group` in `src/genia/builtins.py`, documented in
  `src/genia/host_builtin_docs.py`.
- Shared evidence: 3 new `spec/*` cases (1 eval covering the round-trip
  including the exact `0.1` proof, 2 error covering magnitude overflow and
  NaN rejection -- the latter via the private R18 conformance test seam,
  since R22 exposes no public NaN constructor), proven identical through
  both the in-process path and the R16 subprocess protocol adapter.

Explicit limitations: no Float64 arithmetic (E22-6); no mixed exact/Float64
rejection enforcement yet (E22-6); no Float64 participation in R18
comparison/equality bridge (E22-7); no `numeric-resource-limit`
normalization (E22-8); no canonical display/JSON (R23).

~~~~~

## B246: baseline lines 5179-5222

Moved from GENIA_STATE.md@d401f322, lines 5179-5222 (ledger row B246, moved, sha256 08c2dc2e9f8ec56a)

~~~~~markdown
## 9.28) R22 E22-6 Float64 arithmetic and mixed-domain rejection (issue #892)

Implements section 9 of
`docs/design/r22-exact-numeric-runtime-contract.md`.

- Float64-with-Float64 unary `-`, `+`, `-`, `*`, `/`, `%` needed no new
  implementation: a Python `float` already is one IEEE-754 binary64 value,
  and its native operators already are round-to-nearest-ties-to-even. `%`
  is Python's native float floor remainder, which already matches the
  contract's "floor remainder over represented operands, rounded to
  binary64" definition.
- Division/remainder by Float64 zero (`src/genia/evaluator.py`
  `eval_binary`'s `SLASH`/`PERCENT` cases) now raises a deterministic,
  explicitly-authored `ZeroDivisionError` (`"float64 division by zero"` /
  `"float64 remainder by zero"`) before reaching Python's native operator
  -- Python's native float division/remainder by zero already raises
  `ZeroDivisionError` rather than silently producing infinity/NaN, so this
  only replaces its message text with one this project authors, matching
  E22-4's exact-family precedent.
- Mixed exact/Float64 arithmetic is now explicitly rejected
  (`src/genia/numeric_runtime.py` `is_mixed_exact_and_float64`, checked at
  the top of every arithmetic case in `eval_binary`): Python's own numeric
  tower otherwise lets a bare `int` freely interoperate with `float`
  (e.g. `1 + 2.5` previously silently produced a host float), which is
  exactly the R22 contract's mixed-domain violation for plain Integer;
  `GeniaDecimal`/`GeniaRational` mixing with `float` already failed
  correctly via the existing type-mismatch `TypeError` path (E22-1/E22-2),
  so this closes the one remaining gap. Rejected in both operand orders
  and for all five binary arithmetic operators, returning the same
  `none("type-error", ...)` value the evaluator already returns for any
  other type mismatch -- not a new diagnostic tag. The caller must
  explicitly choose a domain with `float64(...)` or `exact(...)` first.
  Comparison operators are unaffected (out of this slice's scope --
  E22-7 owns the exact/Float64 comparison bridge).
- Shared evidence: 4 new `spec/*` cases (2 eval -- Float64-with-Float64
  arithmetic, and mixed-domain rejection across all five operators/both
  orders/all three exact kinds -- and 2 error, division/remainder by
  Float64 zero), proven identical through both the in-process path and the
  R16 subprocess protocol adapter.

Explicit limitations: no Float64 in R18 comparison/equality bridge (E22-7);
no `numeric-resource-limit` normalization (E22-8); no canonical
display/JSON (R23).

~~~~~

## B247: baseline lines 5223-5271

Moved from GENIA_STATE.md@d401f322, lines 5223-5271 (ledger row B247, moved, sha256 a09d92b9dd9aa15e)

~~~~~markdown
## 9.29) R22 E22-7 mathematical comparison, equality, and R18 map-key reconciliation (issue #893)

Implements section 10 of `docs/design/r22-exact-numeric-runtime-contract.md`,
integrating Decimal/Rational/Float64 into R18's single equality/key
relation (`docs/design/r18-portable-value-equality-contract.md`) rather
than introducing a second relation.

- **10.1 exact family**: `src/genia/equality.py` `_numeric_equal` is
  rewritten around one uniform exact-fraction cross-multiplication
  (`_exact_fraction`) covering Integer/Decimal/Rational (including plain
  Integer/Integer), replacing the previous pairwise special-cased
  functions. `1 == 1.0`, `1.0 == 1.00`, and `1 == rational(2, 2)` all hold.
  Ordering (`< <= > >=`) is a new `numeric_order` function
  (`src/genia/numeric_runtime.py`) reused by `GeniaDecimal`'s existing
  comparison dunders (now generalized beyond Integer/Decimal) and new
  `GeniaRational` comparison dunders -- Python's own operator-reflection
  protocol (`NotImplemented` → the other operand's reflected method) makes
  every Integer/Decimal/Rational pairing resolve correctly without new
  evaluator dispatch.
- **10.2 Float64 bridge**: the same `numeric_order`/`_numeric_equal`
  machinery treats a finite Float64 by its own exact represented value
  (`float.as_integer_ratio()`, CPython-guaranteed exact) cross-multiplied
  against the exact operand's fraction -- the exact operand is never
  rounded to Float64. `+0.0`/`-0.0` equal exact zero. NaN is unequal to
  everything including itself and every ordered comparison involving it is
  `false` (not raised). Infinities use extended-real ordering (below every
  finite value when negative, above when positive). This bridge is
  equality/comparison only; E22-6's mixed-domain arithmetic rejection is
  unaffected and unchanged.
- **10.3 map keys**: `canonical_map_key` now produces one unified
  `("num-fraction", numerator, denominator)` bucket (always in lowest
  terms) for any non-integral Decimal, Rational, or float, so an
  equal-valued key of any of those three kinds collides into the same
  entry; an integral value of any kind still collapses into the existing
  `("num", int_value)` bucket. NaN remains an illegal key (no exact value
  can ever be NaN, so this only constrains the Float64 side). Infinities
  keep their own distinct-by-sign bucket and never collide with any finite
  key.
- Shared evidence: 3 new `spec/*` eval cases (exact-family equality,
  exact-family-and-Float64 ordering, and cross-kind map-key collision
  including through `float64(...)`), proven identical through both the
  in-process path and the R16 subprocess protocol adapter. The full
  pre-existing R18 spec/test suite (`tests/spec/test_r18_*.py`,
  `tests/unit/test_r18_*.py`) was re-run and remains green with zero
  changes required to its expectations.

Explicit limitations: no `numeric-resource-limit` normalization (E22-8);
no canonical display/JSON (R23).

~~~~~

## B248: baseline lines 5272-5315

Moved from GENIA_STATE.md@d401f322, lines 5272-5315 (ledger row B248, moved, sha256 3ec71362ff5a5dcf)

~~~~~markdown
## 9.30) R22 E22-8 numeric misuse, resource limits, and diagnostic normalization (issue #894)

Implements sections 11 and 13 of
`docs/design/r22-exact-numeric-runtime-contract.md`. Primarily a
verification slice: every deterministic numeric-misuse family introduced
by E22-1 through E22-7 was audited directly through the CLI and confirmed
already free of raw host exception text (exact/Float64 division and
remainder by zero, invalid `rational(...)` arguments/zero denominator,
invalid `float64`/`exact` conversion, mixed exact/Float64 arithmetic,
illegal NaN map key) -- no changes were needed to any of those paths.

- `numeric-resource-limit` (`src/genia/numeric_runtime.py`
  `NumericResourceLimitError`, `_check_resource_limit`): a private,
  non-public bound (default 14,000 bits) on a `GeniaDecimal` coefficient/
  exponent or `GeniaRational` numerator/denominator's magnitude, checked
  on raw input before any expensive canonicalization/gcd work. The bound
  is deliberately kept below CPython's own int-to-decimal-text conversion
  guard (`sys.get_int_max_str_digits()`, 4300 digits by default) --
  auditing this slice's own construction paths surfaced a genuine
  pre-existing gap: `GeniaDecimal`'s canonicalization converts the
  coefficient to base-10 text to strip trailing zeros, and for an
  astronomically large coefficient this previously hit Python's guard
  directly, leaking a raw `ValueError` mentioning
  `sys.set_int_max_str_digits` -- exactly the "raw host/library text
  crosses the portable boundary" failure R22 forbids. The resource check
  now runs first and pre-empts that leak with this project's own
  deterministic `"numeric-resource-limit"` diagnostic.
- A private, non-Genia-source-reachable test seam
  (`_numeric_resource_limit_test_seam`, a context manager) temporarily
  lowers the bound for deterministic test coverage, per contract section
  11's own allowance that the threshold is a host/test detail, never
  public Genia semantics; shared conformance never depends on its value.
  `NumericResourceLimitError` propagates uncaught (like zero-division)
  rather than being silently converted to a returned value, consistent
  with the established precedent that numeric misuse terminates
  evaluation rather than the caller continuing past it.
- Explicitly not disguised as numeric overflow (`OverflowError`, reserved
  for `float64`'s genuine binary64 magnitude overflow) or a type mismatch
  (`TypeError`) -- it is its own exception kind.

Explicit limitations: no canonical display/JSON (R23); the resource-limit
bound applies only to `GeniaDecimal`/`GeniaRational` construction, not to
R17 plain Integer arithmetic, which remains fully unbounded as before.

~~~~~

## B249: baseline lines 5316-5375

Moved from GENIA_STATE.md@d401f322, lines 5316-5375 (ledger row B249, moved, sha256 7a4534e5d5b95565)

~~~~~markdown
## 9.31) R22 E22-9 cross-surface conformance and compatibility hardening (issue #895)

Audits the whole merged R22 runtime model (E22-1..E22-8) across surfaces
outside the evaluator's core arithmetic dispatch and repairs the
compatibility defects genuinely caused by R22. Per
`docs/design/r22-exact-numeric-runtime-contract.md`, no R23 rendering/JSON
policy is introduced by this slice.

Genuine defects found and fixed:

- **Quoted/metacircular literal materialization**
  (`src/genia/evaluator.py` `quote_node`, `quasiquote_node`'s internal
  `qq`): both reconstructed a quoted `Number` AST node by returning its raw
  `node.value` -- the pre-R21 evaluator-facing field, which for a
  decimal-source literal is still a bare Python `float`. Ordinary
  (non-quoted) evaluation instead lowers `Number` through the R21 tagged
  `IrLiteral` payload into a genuine `GeniaDecimal` via
  `numeric_literal_runtime_value`. `quote(1.5)` therefore silently produced
  a Float64 instead of a Decimal, and any later `eval` of that quoted
  structure carried the wrong runtime kind permanently. Both call sites now
  route a `Number` node through
  `numeric_literal_runtime_value(numeric_literal_payload(node))`, matching
  ordinary evaluation exactly.
- **Metacircular self-evaluating-literal predicate**
  (`src/genia/builtins.py` `syntax_self_evaluating_fn`, backing
  `self_evaluating?` in `std/prelude/eval.genia`): recognized only Python
  `bool`/`int`/`float`/`str` as self-evaluating, so `eval(<GeniaDecimal>,
  env)` or `eval(<GeniaRational>, env)` unconditionally raised
  `"metacircular eval does not support expression"` even though the value
  was already a legitimate self-evaluating literal. Now also recognizes
  `GeniaDecimal`/`GeniaRational`.
- **Sheets `render_csv` scalar rendering** (`src/genia/sheet.py`
  `_csv_scalar_text`): accepted `GeniaDecimal` (fixed in E22-1) but not
  `GeniaRational`, which is a separate dataclass, not a `GeniaDecimal`
  subclass -- a Rational-valued cell crashed `render_csv`. Now accepts
  both.
- **Retrieval finite-score gating** (`src/genia/retrieval.py`
  `_is_finite_score`): accepted `GeniaDecimal` (fixed in E22-1) but not
  `GeniaRational`, silently treating a perfectly valid, always-finite
  Rational evidence score as not finite. Now accepts both.

Audited and confirmed already correct, no change needed: optimizer/
constant-folding (`src/genia/optimizer.py` has no arithmetic constant
folding at all; its only numeric-literal-aware logic already calls
`numeric_literal_runtime_value` on the tagged payload rather than raw dict
inspection); pattern matching (`src/genia/pattern_match.py` already
dispatches literal-pattern comparison through the shared `genia_equal`
relation, not raw `==`); `json_encode` (already produces a clean R19-style
diagnostic for an unsupported-for-JSON `GeniaDecimal`/`GeniaRational`
rather than crashing -- JSON policy itself remains R23); host subprocess
protocol adapter (round-trips exact numeric kinds through the same
`format_debug`/print machinery the evaluator's core dispatch already uses
correctly, not a separate numeric-aware marshalling path); CLI/Flow
execution (no numeric-type-specific logic of their own).

Explicit limitations: no canonical display/JSON (R23); `json_stringify`'s
existing (pre-R22, applies to every unsupported-for-JSON type, not
Decimal/Rational-specific) diagnostic-message shape was not touched, since
it is not a defect this slice's scope attributes to R22.

~~~~~

## B250: baseline lines 5376-5428

Moved from GENIA_STATE.md@d401f322, lines 5376-5428 (ledger row B250, moved, sha256 1efb54285ba5e081)

~~~~~markdown
## 9.32) R23 E23-1 canonical numeric rendering (issue #911)

Implements sections 2-3 of
`docs/design/r23-numeric-representation-interchange-contract.md`: canonical
display/debug rendering for Integer, Decimal, Rational, and Float64.

- **Decimal** (`src/genia/numeric_runtime.py` `GeniaDecimal.__repr__`/
  `__str__`, via new shared `_canonical_decimal_text`): fixed notation when
  `-6 <= adjusted_exponent <= 20` (`adjusted_exponent = len(digits) +
  exponent - 1`), else scientific; no insignificant trailing fractional
  zeros; `.0` suffix when mathematically integral (e.g. `500.0`, not the
  prior placeholder's bare `500`); scientific form has exactly one digit
  before `.`, lowercase `e`, explicit `+`/`-` exponent sign, no
  unnecessary exponent leading zeros. Display and debug are identical.
- **Rational** (`src/genia/numeric_runtime.py` `GeniaRational.__repr__`/
  `__str__`): unchanged text (`<numerator>/<denominator>`, no spaces) --
  it already matched the contract before this slice; only the "pending
  R23" comment was retired.
- **Float64** (`src/genia/numeric_runtime.py`, new `format_float64`):
  `float64(<shortest-roundtrip-decimal>)`. The inner decimal is obtained
  by parsing CPython's own correctly-rounded `repr(float)` (guaranteed
  shortest text that round-trips to the identical binary64 bits under
  round-to-nearest/ties-to-even) through `decimal.Decimal(...).as_tuple()`
  into a coefficient/exponent pair, then rendered with the same
  `_canonical_decimal_text` helper Decimal uses. Signed zero renders
  `float64(0.0)`/`float64(-0.0)` (Float64, unlike Decimal, has a real
  sign-of-zero distinction). Non-finite values render `float64(nan)`,
  `float64(inf)`, `float64(-inf)`.
- **Integer**: no change. Python's own `str(int)` already satisfied
  contract section 2.1; confirmed by tests, not rewritten.
- **Rendering-surface wiring** (`src/genia/utf8.py` `format_display`/
  `format_debug` -- the one generic rendering dispatch every user-facing
  and debug output surface already funnels through, including the REPL/
  CLI final-value echo in `src/genia/interpreter.py` `_emit_result`):
  gained an explicit `float` branch calling `format_float64` instead of
  falling through to Python's own `str(float)`/`repr(float)`. Decimal and
  Rational needed no dispatch change -- they already route through that
  same fallback via their own (now canonical) `__str__`/`__repr__`.
- Shared evidence: `tests/unit/test_r23_canonical_numeric_rendering.py`
  (fixed/scientific boundary cases at `adjusted_exponent` exactly -6 and
  20 and one past each side, trailing-zero stripping, Rational sign
  normalization, Float64 signed zero/non-finite/shortest-round-trip
  spelling, and a REPL/CLI-echo-path-level test running real Genia source
  through the evaluator).

Explicit limitations: no field-format-spec integration (existing
`_format_engine.py` `.n`/`,`/width behavior is unchanged, E23-2); no JSON
encode/decode changes, no `stable_json_decimal`, no compatibility JSON
reconciliation (E23-3/E23-4/E23-5); no R19 diagnostic-normalization work
beyond what already existed (no render path in scope raised for values in
scope); R22 arithmetic/equality/comparison are unchanged -- this slice is
rendering-only.

~~~~~

## B251: baseline lines 5429-5442

Moved from GENIA_STATE.md@d401f322, lines 5429-5442 (ledger row B251, moved, sha256 c21fca292cc56394)

~~~~~markdown
## 9.33) R23 E23-2 field-format-spec integration (issue #913)

Implements section 7 of
`docs/design/r23-numeric-representation-interchange-contract.md`:
`src/genia/_format_engine.py`'s existing `apply_format_spec` field-format
system now works correctly against the E23-1 canonical Decimal/Rational/
Float64 renderer (issue #911). No new formatting language; the existing
template/placeholder system (`{field:spec}`) is unchanged. Presentation
only -- no numeric kind or value is ever mutated by a format spec.

- **Alignment/width** (`<n`/`>n`/`^n`): unchanged -- it already operated
  on `format_display(value)`, i.e. the canonical text, so Decimal/
  Rational/Float64 already padded/centered correctly with no code change
  needed here.
~~~~~

## B252: baseline lines 5443-5467

Moved from GENIA_STATE.md@d401f322, lines 5443-5467 (ledger row B252, moved, sha256 2b492bd6dd5af278)

~~~~~markdown
- **`.n` precision** (half-up, preserving the existing format-surface
  rule): reworked to compute from each kind's exact value instead of a
  Decimal-text round trip.
  - `GeniaRational` is now a recognized numeric kind for format specs at
    all (`_NUMERIC_TYPES` was missing it entirely before this slice, so
    every numeric spec -- including `.n` -- raised `format-error: ...
    requires numeric value` for a Rational operand). `.n` now rounds the
    exact `numerator/denominator` ratio to `n` places via arbitrary-
    precision integer `divmod` (never `decimal.Decimal` division, whose
    bounded context precision cannot correctly round an arbitrary
    repeating ratio like `1/3`, and never a `float(...)` cast).
  - `GeniaDecimal` now rounds from its own `coefficient`/`exponent`
    (via the existing `decimal_as_fraction` accessor) through the same
    integer `divmod` routine, per the contract's literal "operates
    directly on exact coefficient/exponent" wording.
  - Float64 (`float`) now rounds from `value.as_integer_ratio()` --
    the exact binary64 bit-pattern ratio -- instead of
    `Decimal(repr(value))`. **Bug fix**: the prior `repr(value)`-based
    path double-rounded (CPython's shortest-round-trip decimal text
    is not the float's exact dyadic value), e.g. `2.675`'s exact bits
    round to `2.67` at 2 places, but the old path rounded the text
    `"2.675"` up to `2.68`. NaN/infinity now raise a normalized
    `format-error: ... requires a finite numeric value` diagnostic
    instead of `float.as_integer_ratio()`'s raw `OverflowError`/
    `ValueError`.
~~~~~

## B253: baseline lines 5468-5486

Moved from GENIA_STATE.md@d401f322, lines 5468-5486 (ledger row B253, moved, sha256 e20511be68db0093)

~~~~~markdown
- **Zero-padding** (`0n`) and **grouping** (`,`): now gated to canonical
  text that is a plain numeral (`-?\d+(\.\d+)?`) via a new
  `_require_plain_numeral_text` helper, raising the existing
  `format-error: ...` diagnostic pattern instead of applying digit-
  position-counting presentation logic to a shape it doesn't fit.
  Integer and GeniaDecimal-in-fixed-notation canonical text are plain
  numerals and are unaffected (identical output to before this slice).
  GeniaRational's `<numerator>/<denominator>` atom, Float64's
  `float64(...)` atom, and GeniaDecimal-in-scientific-notation text are
  not plain numerals and now raise instead of being reformatted.
  **Bug fix**: before this slice, grouping a `float64(...)`-wrapped
  value (e.g. `format("{n:,}", {n: float64(1234.5)})`) returned the
  corrupted string `"flo,at6,4(1,234.5)"` -- grouping's thousands-
  separator logic ran over the whole wrapper text introduced by E23-1's
  canonical Float64 rendering. This is the one place this slice's fix
  reaches past a pure `_format_engine.py`-local change: the wrapper text
  itself (`format_float64` in `src/genia/numeric_runtime.py`) is
  unmodified; only `_format_engine.py`'s own zero-pad/grouping gate
  changed, so the mangling case now raises a normalized diagnostic.
~~~~~

## B254: baseline lines 5487-5508

Moved from GENIA_STATE.md@d401f322, lines 5487-5508 (ledger row B254, moved, sha256 f81af4165aac4342)

~~~~~markdown
- Shared evidence:
  `tests/unit/test_r23_format_spec_numeric_integration.py` (width/
  alignment on Decimal/Rational/Float64 canonical text; zero-pad/
  grouping acceptance on plain-numeral text and rejection on Rational/
  Float64/scientific-Decimal text; `.n` half-up precision for Decimal,
  Rational -- including a repeating-decimal case and a genuine decimal
  tie from a terminating fraction -- and Float64 -- including the
  `2.675` exact-dyadic-vs-shortest-repr case and NaN/infinity rejection;
  `Format(...)` value parity for a Rational `.n` case).

Explicit limitations: no JSON encode/decode changes, no
`stable_json_decimal`, no compatibility JSON reconciliation (E23-3/
E23-4/E23-5); no full diagnostics-normalization sweep (E23-6) --
format-spec misuse continues to raise the same pre-existing
`ValueError("format-error: ...")` pattern this file already used, not a
new diagnostic mechanism; release audit not performed (E23-7); R22
arithmetic/equality/comparison are unchanged; E23-1's own canonical
rendering functions (`GeniaDecimal.__repr__`/`__str__`,
`GeniaRational.__repr__`/`__str__`, `format_float64`,
`_canonical_decimal_text`) are unmodified -- this slice only changes how
`_format_engine.py` consumes their already-canonical output.

~~~~~

## B255: baseline lines 5509-5525

Moved from GENIA_STATE.md@d401f322, lines 5509-5525 (ledger row B255, moved, sha256 9208c2de14820f08)

~~~~~markdown
## 9.34) R23 E23-3 strict generic JSON boundary for Integer and Decimal (issue #915)

Implements sections 4.1, 4.2, 5, and 8 (this slice only) of
`docs/design/r23-numeric-representation-interchange-contract.md` against
the strict generic JSON boundary only (`json_decode`/`json_encode`, i.e.
`_json_decode`/`_json_encode` in `src/genia/builtins.py`) -- the
compatibility `json_parse`/`json_stringify`/`json_pretty`/
`parse_jsonl_record` surface is a separately maintained code path
(`_json_to_runtime`/`_json_from_runtime`, plain `json.loads`/`json.dumps`
with no strict hooks, `none(...)` failure shape) and is untouched here
(E23-5).

- **Integer** (section 4.1): unchanged behavior, confirmed and reused --
  `_strict_json_int` already bounded decode to the single existing
  `_JSON_SAFE_INTEGER = 9_007_199_254_740_991` module constant; encode's
  `_strict_json_from_runtime` already bounded the same interval. No new
  literal was introduced.
~~~~~

## B256: baseline lines 5526-5539

Moved from GENIA_STATE.md@d401f322, lines 5526-5539 (ledger row B256, moved, sha256 f7bc3be603b426d6)

~~~~~markdown
- **`stable_json_decimal(d)`** (section 4.2, new): added to
  `src/genia/numeric_runtime.py`, next to `GeniaDecimal`. Converts `d`'s
  exact `(numerator, denominator)` fraction (`GeniaDecimal._as_fraction()`)
  to binary64 via native arbitrary-precision `int / int` true division
  (the same correctly-rounded round-to-nearest/ties-to-even conversion
  `to_float64` documents), returning `False` on overflow-to-infinity
  (`OverflowError`) or on a nonzero value underflowing to `0.0`; otherwise
  reuses E23-1's `_float_shortest_roundtrip_coefficient_exponent` to
  recompute the shortest-roundtrip decimal for those binary64 bits and
  compares its canonical `(coefficient, exponent)` directly against `d`'s
  own already-canonical fields (valid because `GeniaDecimal.__init__`
  already canonicalizes on construction, so canonical form is a unique
  representative of mathematical value and tuple equality is exactly the
  contract's "mathematically equal" check).
~~~~~

## B257: baseline lines 5540-5563

Moved from GENIA_STATE.md@d401f322, lines 5540-5563 (ledger row B257, moved, sha256 9a1bfd0d22c9aec9)

~~~~~markdown
- **Decode** (section 5): `json_decode`'s `parse_float` scanner hook
  (`_strict_json_decimal`, replacing the former `_strict_json_float`)
  parses the raw JSON fraction/exponent token text directly into an exact
  `GeniaDecimal` coefficient/exponent via a lexical regex over the token's
  sign/integer/fraction/exponent digit groups -- `float(...)` is never
  called anywhere in this path. The resulting `GeniaDecimal` must satisfy
  `stable_json_decimal`; otherwise decode raises the existing
  `_JsonBoundaryFailure("json_number_out_of_range")`, normalized the same
  way as every other JSON boundary rejection. Integer-form tokens are
  unaffected (still `_strict_json_int` -> Integer). `NaN`/`Infinity`
  spellings remain invalid JSON syntax, unchanged.
- **Encode** (section 4.2): `_strict_json_from_runtime` gained a
  `GeniaDecimal` branch: rejects (via the same `json_number_out_of_range`
  reason) any Decimal failing `stable_json_decimal`, never rounding or
  degrading it to a string. A stable Decimal is never itself JSON-
  serializable as a raw token by `json.dumps` (it binds `float.__repr__`/
  `int.__repr__` directly and has no `decimal.Decimal` support), so the
  reference host emits a unique per-value ASCII sentinel string
  (`uuid.uuid4().hex`-based) in the value's place and `json_encode_fn`
  performs one final exact-text substitution of each quoted sentinel for
  its raw canonical Decimal spelling (E23-1's `repr(GeniaDecimal)`) once
  `json.dumps` has produced the full document text. This changes no
  output for any other value kind and adds no new general-purpose JSON
  serializer.
~~~~~

## B258: baseline lines 5564-5580

Moved from GENIA_STATE.md@d401f322, lines 5564-5580 (ledger row B258, moved, sha256 4d65d6e2ae4752c7)

~~~~~markdown
- **Diagnostics** (section 8, this slice only): every new rejection above
  raises through the existing `_JsonBoundaryFailure` ->
  `_json_boundary_err` normalization already used by every other JSON
  boundary failure, reusing the existing `json_number_out_of_range`
  reason (no new diagnostic channel or reason string introduced).
- Shared evidence: `tests/unit/test_r23_json_integer_decimal_boundary.py`
  (R9 Integer-boundary accept/reject at encode and decode;
  `stable_json_decimal` unit cases -- stable, excess-precision-unstable,
  overflow, underflow; exact-canonical-text raw-number encode and
  rejection of an unstable Decimal; lexical fraction/exponent decode,
  including a case demonstrating decode does not go through
  `Decimal(float(token))`; round-trip and nested-container cases);
  `spec/eval/json-representation-number-boundaries.yaml` updated to
  reflect that a JSON fraction token now decodes to the canonical Decimal
  atom (`1.5`) rather than the prior placeholder Float64 atom
  (`float64(1.5)`).

~~~~~

## B259: baseline lines 5581-5598

Moved from GENIA_STATE.md@d401f322, lines 5581-5598 (ledger row B259, moved, sha256 9d250975893f0b05)

~~~~~markdown
Explicit limitations (left exactly as found, later R23 slices): Rational
JSON policy is unaffected -- `_strict_json_from_runtime` still has no
`GeniaRational` branch at all, so encoding a Rational still falls through
to `unsupported_json_value` (Rational is not silently rounded, but is not
yet accepted either); decode still never constructs a Rational. Float64
(`float`) JSON handling in `_strict_json_to_runtime`/
`_strict_json_from_runtime` is unmodified and, on the decode side, is now
unreachable in practice (nothing manufactures a Python `float` there any
more once fraction/exponent tokens decode to `GeniaDecimal`) but remains
live for `float64(...)`-literal Genia values on encode; reconciling
either is E23-4. Compatibility `json_parse`/`json_stringify` are entirely
untouched (E23-5); a `GeniaDecimal` passed to `json_stringify` still
raises `TypeError("json_stringify expected a JSON-compatible value...")`
exactly as before. No full diagnostics-normalization sweep beyond this
slice's own new rejections (E23-6); release audit not performed (E23-7).
R22 arithmetic/equality/comparison are unchanged. E23-1's rendering
functions and E23-2's format-spec code are called, never edited.

~~~~~

## B260: baseline lines 5599-5629

Moved from GENIA_STATE.md@d401f322, lines 5599-5629 (ledger row B260, moved, sha256 1846f32ec9b6da62)

~~~~~markdown
## 9.35) R23 E23-4 strict generic JSON boundary for Rational and Float64 (issue #921)

Implements sections 4.3, 4.4, the Rational/Float64 parts of section 5, and
section 8 (this slice's new rejections) of
`docs/design/r23-numeric-representation-interchange-contract.md` against
the same strict generic JSON boundary E23-3 (section 9.34) established
(`json_decode`/`json_encode`, i.e. `_json_decode`/`_json_encode` in
`src/genia/builtins.py`). Compatibility `json_parse`/`json_stringify`/
`json_pretty`/`parse_jsonl_record` remain untouched (E23-5).

- **Rational** (section 4.3): `rational_terminating_decimal(value)`
  (new, `src/genia/numeric_runtime.py`) computes a `GeniaRational`'s exact
  equivalent `GeniaDecimal` using only integer arithmetic (no
  `float(...)` cast) when its already-reduced denominator's only prime
  factors are 2 and/or 5 (the standard base-10-termination test), else
  returns `None` (e.g. `1/3`, `2/7`, and `1/6`/`5/12` -- both of which
  still carry a non-2/5 factor of 3 despite also carrying a factor of 2).
  `_strict_json_from_runtime` (encode) gained a `GeniaRational` branch:
  a non-terminating Rational rejects with `unsupported_json_value`
  (`value_type="rational"`) -- it cannot be represented as a JSON number
  at all, the same reason any other non-numeric-JSON kind gets; a
  terminating Rational whose exact Decimal equivalent fails the reused
  (read-only) `stable_json_decimal` predicate rejects with
  `json_number_out_of_range`, identical to Decimal's own rejection for
  the same predicate failure; a terminating, stable Rational encodes its
  exact Decimal equivalent's canonical text via the same sentinel-
  substitution mechanism E23-3 built for Decimal. Decode is unaffected --
  JSON never directly constructs a Rational (confirmed, not changed):
  decoding an encoded Rational's JSON form yields a `GeniaDecimal`, which
  R18 cross-kind equality (`genia_equal`) still compares mathematically
  equal to the original Rational.
~~~~~

## B261: baseline lines 5630-5645

Moved from GENIA_STATE.md@d401f322, lines 5630-5645 (ledger row B261, moved, sha256 9d78dabb5d2a8016)

~~~~~markdown
- **Float64** (section 4.4): `float64_finite_canonical_text(value)` (new,
  `numeric_runtime.py`) is `format_float64`'s finite-value digit
  computation extracted into its own function, so display/debug rendering
  and JSON encode share one computation instead of two -- `format_float64`
  itself now calls it and its observable output is unchanged. The
  previously-existing but contract-inconsistent Float64 encode branch
  (which let `json.dumps` re-derive digits from `float.__repr__`, whose
  fixed/scientific notation threshold does not match R23's own canonical
  rule for every magnitude) is rewritten to inject
  `float64_finite_canonical_text`'s exact text via the same sentinel-
  substitution mechanism, so encoded JSON numbers always match
  `format_float64`'s canonical spelling with the `float64(...)` wrapper
  stripped. NaN/infinity are rejected with `json_number_out_of_range`
  before `json.dumps(..., allow_nan=False)` ever sees them (that
  `allow_nan=False` guard is defense-in-depth, not the primary
  rejection).
~~~~~

## B262: baseline lines 5646-5662

Moved from GENIA_STATE.md@d401f322, lines 5646-5662 (ledger row B262, moved, sha256 3044663d6b7439cc)

~~~~~markdown
- **Decode never produces Float64** (section 5): confirmed, not a
  behavior change. `_strict_json_to_runtime`'s pre-existing `float`
  branch (flagged as dead in E23-3's own section 9.34 note) is genuinely
  unreachable -- `json_decode`'s scanner hooks (`parse_float` ->
  `GeniaDecimal`, `parse_constant` -> reject) intercept every JSON
  number/constant token before `json.loads` could ever construct a raw
  Python `float` for this function to see. Its body is now an explicit
  `AssertionError`-guarded comment documenting exactly why, rather than a
  silently inconsistent live-looking branch left in place.
- **Diagnostics** (section 8, this slice's new rejections): both new
  Rational failure modes and the corrected Float64 non-finite rejection
  raise through the existing `_JsonBoundaryFailure` ->
  `_json_boundary_err` normalization already used by every JSON boundary
  failure, reusing two already-established reasons
  (`unsupported_json_value` for "cannot be represented at all",
  `json_number_out_of_range` for "right kind, failed the numeric
  stability predicate") -- no new diagnostic channel or reason string.
~~~~~

## B263: baseline lines 5663-5678

Moved from GENIA_STATE.md@d401f322, lines 5663-5678 (ledger row B263, moved, sha256 20bf2784db988bb6)

~~~~~markdown
- Shared evidence: `tests/unit/test_r23_json_rational_float64_boundary.py`
  (`rational_terminating_decimal` unit cases including negative
  numerators, non-2/5-factor denominators that still carry a factor of 2,
  and a large-prime-denominator case, plus an AST-based no-`float()`-cast
  proof; encode of several terminating Rationals to exact decimal text;
  encode rejection of non-terminating and terminating-but-unstable
  Rationals with their respective distinct reasons; decode-never-
  constructs-Rational and R18 cross-kind-equality round-trip cases;
  Float64 encode of finite values -- including magnitudes needing
  scientific notation and signed zero -- matching `format_float64`
  exactly; Float64 NaN/Infinity encode rejection with a normalized
  diagnostic, not a raw Python exception; confirmation every JSON
  fraction/exponent decode token still produces `GeniaDecimal`, never
  `float`; Genia-source-level `1 / 3` reject / `1 / 4` accept round
  trips via exact division).

~~~~~

## B264: baseline lines 5679-5687

Moved from GENIA_STATE.md@d401f322, lines 5679-5687 (ledger row B264, moved, sha256 98f6de6964b80152)

~~~~~markdown
Explicit limitations (left exactly as found, later R23 slices):
compatibility `json_parse`/`json_stringify` were entirely untouched by
this slice -- reconciled by E23-5 (section 9.36 below). No full
diagnostics-normalization sweep beyond this slice's own new rejections
(E23-6); release audit not performed (E23-7). R22 arithmetic/equality/
comparison are unchanged. E23-1's rendering functions and E23-2's
format-spec code are extended by one shared helper, never otherwise
edited -- `format_float64`'s own output is unchanged.

~~~~~

## B265: baseline lines 5688-5718

Moved from GENIA_STATE.md@d401f322, lines 5688-5718 (ledger row B265, moved, sha256 34e113016b208f0f)

~~~~~markdown
## 9.36) R23 E23-5 compatibility JSON reconciliation (issue #923)

Implements section 6 ("Compatibility JSON surfaces") of
`docs/design/r23-numeric-representation-interchange-contract.md` against
the compatibility JSON surface only -- `json_parse`/`json_stringify`/
`json_pretty` (`json_parse_fn`/`json_stringify_fn`, backed by
`_json_to_runtime`/`_json_from_runtime` in `src/genia/builtins.py`) and
`parse_jsonl_record` (`parse_jsonl_record_fn`). The strict generic JSON
boundary (`json_decode`/`json_encode`, E23-3/E23-4, sections 9.34-9.35) is
frozen and is only called into (reused functions), never modified, except
for one pure internal delegation described below.

- **Decode -- one shared lexical parser, two callers with different
  strictness.** E23-3's `_strict_json_decimal` regex/coefficient/exponent
  parsing was extracted into a shared `_parse_json_decimal_token(text)`
  (byte-for-byte identical logic, `float(...)` never called). Strict
  decode's `_strict_json_decimal` now calls it and still enforces
  `stable_json_decimal` -- unchanged observable behavior. A new
  `_compat_json_decimal(text)` calls the same shared parser but
  deliberately does **not** enforce `stable_json_decimal`, and is
  registered as the `parse_float` hook on both `json_parse`'s and
  `parse_jsonl_record`'s `json.loads` calls. A JSON fraction/exponent
  number token therefore always decodes to an exact `GeniaDecimal` through
  both compatibility entry points, never a raw Python `float`, satisfying
  contract section 6's "must not silently materialize fraction/exponent
  numbers as host Float64" and its "reuse common lexical numeric
  conversion machinery ... rather than duplicate competing parsers"
  instruction with a single parser function, not two. `_json_to_runtime`
  gained a `GeniaDecimal` passthrough branch so decoded values flow into
  Genia runtime data unchanged; integer-form tokens are unaffected
  (`json`'s default `int` parsing, unchanged).
~~~~~

## B266: baseline lines 5719-5748

Moved from GENIA_STATE.md@d401f322, lines 5719-5748 (ledger row B266, moved, sha256 adf4b4c928dbcf08)

~~~~~markdown
- **Decode permissiveness decision (deliberate):** compatibility decode
  does not gate on `stable_json_decimal`. Before this slice,
  `json_parse`/`parse_jsonl_record` never rejected any syntactically valid
  JSON number regardless of precision; this preserves that documented
  "legacy tolerance" character (`none(...)` only for outright parse/type
  failures) rather than introducing a new strict-validation rejection mode
  with no test or doc precedent. Contract section 6's own wording requires
  only that decode not silently produce host Float64 -- it does not
  require rejecting an unstable value -- so a `GeniaDecimal` that would
  fail strict `json_decode`'s stability gate still decodes successfully
  through `json_parse`/`parse_jsonl_record`.
- **Encode -- `json_stringify` now accepts `GeniaDecimal`/terminating
  `GeniaRational`/finite Float64,** reusing E23-3/E23-4's canonical-text
  computations (`repr(GeniaDecimal)`, `rational_terminating_decimal`,
  `float64_finite_canonical_text`) and the same sentinel-substitution
  injection mechanism, factored into a shared `_json_number_sentinel`
  helper. This closes an asymmetry this slice's own decode fix would
  otherwise introduce: since `json_parse` now *produces* `GeniaDecimal`
  for every fraction/exponent token, `json_stringify(json_parse(text))`
  would otherwise immediately regress for any document containing a
  decimal number. Matching the decode permissiveness decision above,
  compatibility encode of `GeniaDecimal`/a terminating `GeniaRational`
  does **not** enforce `stable_json_decimal` -- it always emits the exact
  canonical decimal text, whatever its precision. Only values that cannot
  be represented as a JSON number at all -- a non-terminating
  `GeniaRational`, or a non-finite Float64 -- remain rejected, via this
  surface's existing `none("json-stringify-error", ...)` failure shape
  (unchanged from before this slice; still distinct from strict
  `json_encode`'s `err(...)` shape, which this slice does not unify --
  out of scope).
~~~~~

## B267: baseline lines 5749-5764

Moved from GENIA_STATE.md@d401f322, lines 5749-5764 (ledger row B267, moved, sha256 9e06773f07a98110)

~~~~~markdown
- **Encode -- Float64 canonical-digit unification.** A bare Python `float`
  handed to `json_stringify` previously serialized through `json.dumps`'s
  own `float.__repr__`, whose fixed/scientific notation threshold does not
  match R23's canonical rule (E23-1) for every magnitude -- the same
  contract-inconsistency E23-4 fixed for strict encode. `_json_from_runtime`'s
  `float` branch now renders through `float64_finite_canonical_text` via
  the same sentinel mechanism, so a Float64's JSON number text is now
  identical whether it reaches JSON through `json_encode` or
  `json_stringify`, directly closing contract section 6's "must not
  preserve a second contradictory host-float numeric model" for this
  case. NaN/Infinity remain rejected (unchanged `math.isfinite` guard).
- **`parse_jsonl_record`** shares the exact same `_compat_json_decimal`
  hook as `json_parse` (confirmed it previously called `json.loads` with
  no hook of its own, independently missing the same numeric fix); its
  pre-existing `_jsonl_value_type` helper already classified `GeniaDecimal`
  alongside `int`/`float` as `"number"`, now genuinely reachable.
~~~~~

## B268: baseline lines 5765-5779

Moved from GENIA_STATE.md@d401f322, lines 5765-5779 (ledger row B268, moved, sha256 80af106ed177d2ce)

~~~~~markdown
- Shared evidence:
  `tests/unit/test_r23_compatibility_json_reconciliation.py` (fraction/
  exponent tokens decoding to exact `GeniaDecimal` via `json_parse` and
  `parse_jsonl_record`, including a precision case that fails strict
  `json_decode`'s stability gate but still decodes here; a direct
  source-level proof that `json_parse` and `json_decode` share the same
  `_parse_json_decimal_token` function rather than duplicating parsing
  logic; `json_stringify` encode of `GeniaDecimal`/terminating
  `GeniaRational`/finite Float64, including an unstable-precision case;
  rejection of a non-terminating `GeniaRational` and a non-finite float
  with the existing `none(...)` shape; a `json_stringify(json_parse(...))`
  round-trip case; a Float64 encode case proving `json_stringify`'s digits
  now match `format_float64`/strict `json_encode`'s canonical spelling
  rather than `float.__repr__`'s).

~~~~~

## B269: baseline lines 5780-5790

Moved from GENIA_STATE.md@d401f322, lines 5780-5790 (ledger row B269, moved, sha256 ed6a607a8b778c5e)

~~~~~markdown
Explicit limitations (left exactly as found): the `none(...)`-vs-`err(...)`
failure-shape difference between compatibility and strict JSON is an
approved pre-existing difference and is not unified by this slice. No
full diagnostics-normalization sweep beyond this slice's own new
rejections until E23-6 (section 9.37 below); release audit not performed
until E23-7 completes across the whole release. R22 arithmetic/equality/
comparison are unchanged. Strict `json_decode`/`json_encode`
(`_strict_json_to_runtime`/`_strict_json_from_runtime`) are unmodified
except for `_strict_json_decimal` delegating to the newly-shared
`_parse_json_decimal_token`, with identical observable behavior.

~~~~~

## B270: baseline lines 5791-5807

Moved from GENIA_STATE.md@d401f322, lines 5791-5807 (ledger row B270, moved, sha256 a7937abb5c0b2c76)

~~~~~markdown
## 9.37) R23 E23-6 diagnostics normalization sweep + docs/release truth sync (issue #925)

Implements section 8 ("Error and diagnostic boundary") of
`docs/design/r23-numeric-representation-interchange-contract.md` as a full
sweep across every failure path touched or introduced by E23-1 through
E23-5 (sections 9.32-9.36), per
`docs/analysis/issue-925-e23-6-diagnostics-sweep-docs-sync-preflight.md`.
This is a diagnostics-cleanliness and documentation-truth slice, not a
new-behavior slice.

- **Format-spec (E23-2) diagnostics: confirmed already sound, no change.**
  Every `format-error: ...` raise in `src/genia/_format_engine.py`
  constructs its message from a fixed string plus the format spec text or
  field name, never `str(exc)` of a caught Python exception, and surfaces
  as an ordinary host `ValueError`/`TypeError` misuse diagnostic exactly
  the way every pre-existing (pre-R23) format-spec error already did --
  consistent with R19's diagnostic-portability convention.
~~~~~

## B271: baseline lines 5808-5825

Moved from GENIA_STATE.md@d401f322, lines 5808-5825 (ledger row B271, moved, sha256 35dff9affa228b5d)

~~~~~markdown
- **Strict JSON boundary (E23-3/E23-4) structure: confirmed already
  sound, no change.** Every `_JsonBoundaryFailure` construction uses a
  fixed reason string plus structured keyword context, never wrapped raw
  exception text.
- **`json_number_out_of_range` reason-reuse judgment call (deferred by
  E23-3/E23-4): ratified as sufficient at the `reason` level, refined
  additively.** Splitting the reason symbol itself (e.g. into separate
  Integer-range/Decimal-instability/Float64-non-finite reasons) was
  rejected as a genuine, unnecessary behavior change -- existing tests and
  any downstream Genia code pattern-matching on `result.reason` depend on
  the exact symbol `json_number_out_of_range`. Instead, every real
  (non-defensive) `json_number_out_of_range` raise site -- strict encode
  and decode, both integer-range and numeric-stability/non-finite
  rejections -- now additionally carries a `cause` context field
  (`integer_out_of_range`, `decimal_unstable`, `rational_unstable`,
  `float_non_finite`, or `non_finite_constant` for a rejected
  `NaN`/`Infinity`/`-Infinity` JSON literal), a purely additive context-map
  key that breaks no existing `reason`-symbol assertion.
~~~~~

## B272: baseline lines 5826-5840

Moved from GENIA_STATE.md@d401f322, lines 5826-5840 (ledger row B272, moved, sha256 846f736bfb3530c5)

~~~~~markdown
- **The first of two genuine leaks found and fixed across this release:
  compatibility `json_stringify`'s unsupported-value diagnostic.** (See
  the second, `GeniaRational -> "rational"` leak, documented further
  below and fixed by issue #933's E23-8 repair.) `_json_from_runtime`'s
  final fallback
  `TypeError` (extended in scope by E23-5's rewrite of this function, see
  section 9.36) read a raw Python `type(value).__name__` instead of the
  portable `_runtime_type_name` table every sibling "expected X, received
  Y" diagnostic in `src/genia/builtins.py` already uses (including the
  equivalent final raise in `_strict_json_from_runtime`) -- exactly the
  class of leak E19-3 already normalized elsewhere (E19-3's note: "the
  large 'expected X, received Y' family already renders via
  `_runtime_type_name`"), missed here only because it predates R23 and
  E23-5's rewrite left this one call unchanged. Fixed: now uses
  `_runtime_type_name(value)`.
~~~~~

## B273: baseline lines 5841-5868

Moved from GENIA_STATE.md@d401f322, lines 5841-5868 (ledger row B273, moved, sha256 d826abbc1a0493f1)

~~~~~markdown
- **A sibling `type(value).__name__` shape exists in three pure R22
  arithmetic-misuse raises** (`numeric_runtime.py`'s `_as_decimal`, `exact`,
  and `to_float64`; corrected from an earlier "two" count by issue #933's
  E23-8 repair audit finding), confirmed by `git blame` to be E22-1/E22-5
  code never touched by any E23 slice. Left unchanged -- out of this
  ticket's R23-only scope (R22 arithmetic/equality is explicitly frozen);
  noted as a candidate for a future, separately scoped ticket if one is
  ever opened. This bullet is distinct from, and must not be conflated
  with, the E23-8 fix documented immediately below: the three sites here
  are deliberately-unfixed pre-existing R22 code, not a second instance of
  the same leak E23-8 fixed.
- **A second, distinct genuine leak, found by the E23-7 skeptical release
  truth audit and fixed by issue #933's E23-8 repair: `json_stringify`'s
  diagnostics raw-leaked the Python class name `"GeniaRational"` instead
  of the portable type name `"rational"`.** `_runtime_type_name` in
  `src/genia/values.py` had no branch for `GeniaRational`, so any
  `_json_from_runtime`/`_strict_json_from_runtime` "expected X, received
  Y" diagnostic over an unsupported rational value fell through to a raw
  Python `type(value).__name__` string instead of the same portable
  vocabulary (`"integer"`, `"decimal"`, `"float64"`, ...) every sibling
  runtime type already renders through `_runtime_type_name`. Fixed by
  adding a `GeniaRational -> "rational"` branch to `_runtime_type_name`
  (implementation commit `feda3a7d`, failing-test commit `e03c76bf`, both
  landed via the now-merged E23-8 branch/PR history). This is a second,
  independent instance of the same "expected X, received Y" leak class
  E23-6 fixed for compatibility `json_stringify` above -- not a
  duplicate of that fix and not the same finding as the three deferred
  R22 `numeric_runtime.py` sites in the bullet above.
~~~~~

## B274: baseline lines 5869-5887

Moved from GENIA_STATE.md@d401f322, lines 5869-5887 (ledger row B274, moved, sha256 6d525bf029786df7)

~~~~~markdown
- **E23-4's `AssertionError` dead-code guard in
  `_strict_json_to_runtime`'s `float` branch: confirmed genuinely
  unreachable through every public JSON entry point** (`_json_parse`,
  `_json_decode`, `_parse_jsonl_record`, `_json_stringify`, `_json_encode`;
  `json_pretty` is prelude sugar over `json_stringify`). Only
  `_json_decode` ever calls `_strict_json_to_runtime`, and its
  `parse_float=_strict_json_decimal`/`parse_constant=
  _reject_json_constant` scanner hooks guarantee no raw Python `float`
  ever reaches the tree it walks. Proven by fuzzing `_json_decode` with a
  broad adversarial set of fraction/exponent/large/small/negative/zero
  numeric tokens plus explicit `NaN`/`Infinity`/`-Infinity` literals: no
  call ever raises `AssertionError`. No bug found; no runtime-code change
  to the guard.
- **Bare `except Exception`/swallow-and-rethrow sweep: none found.** No
  bare `except Exception` or `except:` clause exists in
  `numeric_runtime.py` or `_format_engine.py` (neither performs I/O); every
  JSON-boundary `except` clause is narrowly typed and converts to a
  structured, reason-coded Outcome, never re-raising caught exception text
  unmodified.
~~~~~

## B275: baseline lines 5888-5900

Moved from GENIA_STATE.md@d401f322, lines 5888-5900 (ledger row B275, moved, sha256 f2071ce599a3d00b)

~~~~~markdown
- Shared evidence: `tests/unit/test_r23_e23_6_diagnostics_sweep.py`
  (format-spec/strict-JSON diagnostic-cleanliness proofs that pass
  immediately against unmodified code; the `cause` context-field value for
  every `json_number_out_of_range` scenario, with `reason` unchanged;
  compatibility `json_stringify`'s unsupported-value message now reporting
  a portable type name; a broad `AssertionError`-unreachability fuzz
  sweep across every public JSON entry point; a direct proof the guard
  itself is live code, not dead from a typo).

Explicit limitations: no new numeric semantics; no Outcome-shape change;
no R22 arithmetic/equality change; R23 is not marked complete by this
slice -- the E23-7 skeptical release truth audit is still pending.

~~~~~
