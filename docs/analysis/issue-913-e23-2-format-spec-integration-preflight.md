# Issue #913 Preflight — E23-2 Field-Format-Spec Integration

Status: process artifact for issue #913 (E23-2). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority. This file records the
preflight review required by `docs/process/run-change.md` before
implementation, against the already-approved
`docs/design/r23-numeric-representation-interchange-contract.md` (§7),
building on the merged E23-1 canonical renderer (issue #911, commit
`992a8de`).

## Scope

Implement contract §7 only: make `src/genia/_format_engine.py`'s existing
field-format-spec system (`apply_format_spec`) correct against the now-
canonical Decimal/Rational/Float64 display text, for:

- alignment/width (`<n`/`>n`/`^n`) on canonical rendered text
- zero-padding (`0n`) and grouping (`,`) where the represented shape
  supports them
- `.n` precision, half-up, computed from each kind's exact value
  (Decimal coefficient/exponent, Rational numerator/denominator, Float64's
  exact dyadic bit value), never introducing a `float(...)` cast of a
  GeniaDecimal/GeniaRational

Out of scope (later R23 slices): JSON boundary (E23-3/E23-4), compatibility
JSON (E23-5), a full diagnostics-normalization sweep (E23-6), release audit
(E23-7). R22 arithmetic/equality/comparison are untouched. E23-1's
rendering functions (`GeniaDecimal.__repr__`, `GeniaRational.__repr__`,
`format_float64`, `_canonical_decimal_text`) are called, never edited,
except for one minimal, explicitly-called-out fix described below.

## Investigation findings (drove the design below)

1. `_NUMERIC_TYPES = (int, float, GeniaDecimal)` in `_format_engine.py`
   omits `GeniaRational` entirely, so today every field-format spec other
   than plain width/align (`.n`, `0n`, `,`) raises `format-error: ...
   requires numeric value` for a Rational operand -- including `.n`, which
   the contract requires to work (round the exact ratio). This is a gap,
   not intentional Rational protection.
2. `.n` precision for a plain Python `float` currently does
   `Decimal(repr(value))` then quantizes half-up. `repr(value)` is
   CPython's shortest-round-trip decimal spelling, not the float's exact
   dyadic value, so this double-rounds: e.g. `2.675` (exact bits
   `2.67499999999999982236431605997495353221893310546875`) reprs as
   `"2.675"`, which then rounds *up* to `2.68` at 2 places, while the
   contract's "exact dyadic value" rule requires `2.67`. This is the exact
   double-rounding failure mode contract §7 calls out and needs a real fix.
3. `.n` precision for `GeniaDecimal` already goes through
   `Decimal(repr(value))` too, but `GeniaDecimal.__repr__` (post-E23-1) is
   itself exact canonical decimal text (fixed or scientific), and Python's
   `Decimal(...)` string constructor parses both forms exactly, so this
   path is already exact for Decimal today -- no float ever enters it.
   The implementation below still moves Decimal onto the same exact
   coefficient/exponent-derived integer ratio as Rational, both for
   contract-literal fidelity ("operates directly on exact
   coefficient/exponent") and to share one arbitrary-precision half-up
   rounding routine instead of depending on `decimal.Decimal`'s bounded
   context precision for Rational (a repeating-ratio like `1/3` cannot be
   rounded correctly to `.n` through `Decimal` division without also
   fixing the context precision high enough per-call; plain integer
   `divmod` arithmetic is exact and simpler).
4. Zero-padding/grouping operate on `format_display(value)` text. Probed
   directly against this branch's format engine before any change:
   `format("{n:,}", {n: float64(1234.5)})` returns the value
   `"flo,at6,4(1,234.5)"` -- grouping's digit-counting-from-the-right logic
   runs over the whole `float64(1234.5)` wrapper text (introduced by
   E23-1's new `float64(...)` canonical atom) and mangles it. This is a
   real, reproducible format-spec-interaction bug against already-merged
   E23-1 output, not a hypothetical: it is fixed by *gating* zero-pad/
   grouping in `_format_engine.py` to canonical text that is a plain
   numeral (`-?\d+(\.\d+)?`), raising the same normalized
   `format-error: ...` diagnostic used elsewhere for unsupported
   combinations instead of mangling text. This also correctly covers
   Rational's `<numerator>/<denominator>` atom and Decimal's scientific-
   notation atom (`1.5e+21`) under the same rule, matching contract §7's
   "Rational's atom is not silently reinterpreted... to apply unrelated
   padding/grouping" and the general "where the represented shape supports
   them" qualifier. E23-1's `format_float64`/`_canonical_decimal_text`
   themselves are not modified -- only `_format_engine.py`'s own
   zero-pad/grouping gate is added.

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?**
   Reference-host (Python) presentation-only formatting:
   `src/genia/_format_engine.py`'s `apply_format_spec` and its private
   helpers. It calls (never edits) the E23-1 canonical renderer
   (`format_display`/`format_debug` in `src/genia/utf8.py`,
   `GeniaDecimal`/`GeniaRational`/`format_float64` in
   `src/genia/numeric_runtime.py`). No Core IR, lexer/parser, or R22
   arithmetic/equality machinery is touched.

2. **Does this change alter the minimal portable Core IR node family?**
   No. Field-format specs are a post-evaluation, presentation-only string
   transform.

3. **Does this change require a host-native binary float at any point in
   the new code path?**
   Only for Float64 itself (already host binary64 by R22 design). The new
   `.n` precision path for Float64 uses Python `float.as_integer_ratio()`,
   which returns the *exact* numerator/denominator of the IEEE-754 bit
   pattern (no rounding, no intermediate decimal-text round trip) -- this
   is the host-independent "exact dyadic value" the contract requires, not
   an arbitrary host decimal formatter. Decimal and Rational precision use
   their own exact integer coefficient/exponent or numerator/denominator
   directly; no `float(...)` cast of either is introduced anywhere in this
   slice (verified by grep across the diff during self-review).

4. **Does this change require another host implementation (Node/Java/Rust/
   Go/C++) to consult Python-specific behavior to reproduce it?**
   No new cross-host obligation. `float.as_integer_ratio()`'s result (the
   exact reduced binary64 mantissa/exponent as an integer ratio) is a
   direct, host-independent consequence of the IEEE-754 bit pattern, and
   the half-up rounding of an exact `(numerator, denominator, n)` triple
   to `n` decimal places via integer `divmod` and a `remainder*2 >=
   denominator` tie rule is ordinary, host-independent integer arithmetic,
   reproducible from the contract text and this document alone.

5. **Does this change affect R16 multi-host conformance infrastructure, R17
   arbitrary-precision Integer, R18 equality/map-key, R19 diagnostics, or
   R20 open functions?**
   No equality/map-key/comparison/arithmetic code path is touched (R22
   frozen, per scope). R19: this slice raises `ValueError("format-error:
   ...")` for new unsupported-combination cases, matching the exact
   existing diagnostic-normalization pattern already used by every other
   `apply_format_spec` failure in this file (confirmed against
   `tests/unit/test_format_field_specs_169.py`'s existing
   `pytest.raises((ValueError, TypeError), match="format-error")`
   assertions) -- no raw Python/decimal exception text crosses the
   boundary.

6. **Is any part of this change host-local-only (Python reference host
   convenience) rather than portable?**
   `float.as_integer_ratio()` is a CPython convenience method; the
   *portable* requirement is its host-independent result (the bit
   pattern's exact rational value), which is what tests pin, not the
   method name itself. The plain-numeral regex gate
   (`-?\d+(\.\d+)?`) for zero-pad/grouping is this reference host's
   mechanism for the portable rule "operates on canonical text where that
   text is a plain numeral"; another host must reproduce the *rule* (reject
   zero-pad/grouping on a wrapped or slash-shaped canonical atom), not this
   exact regex.

7. **What new portable evidence must exist for another host to reproduce
   this behavior without reading Python source?**
   `tests/unit/test_r23_format_spec_numeric_integration.py`, pinning:
   width/alignment on Decimal/Rational/Float64 canonical text; zero-pad
   and grouping on plain-numeral Decimal/Integer text (unchanged) and
   their rejection (normalized diagnostic, not mangled text) on Rational,
   Float64, and scientific-notation Decimal text; `.n` half-up precision
   for Decimal (exact coefficient/exponent), Rational (exact ratio,
   including a repeating-decimal case), and Float64 (a value, `2.675`,
   that provably differs between exact-dyadic and shortest-round-trip-text
   rounding); and one Rational case proving the `<numerator>/<denominator>`
   atom is never reinterpreted as Decimal shape for padding.

## Conclusion

Preflight is complete. This is reference-host format-spec logic operating
on already-canonical (E23-1), host-independent rendered text and each
kind's own already-exact value representation; no Core-IR or cross-host
Python-specific leakage found. One real bug against already-merged E23-1
output (grouping mangling the `float64(...)` wrapper) and one real
double-rounding bug (float `.n` precision via `repr()` instead of the
exact dyadic value) are fixed as part of this slice, both flagged
explicitly above and in the implementation commit. Proceeding directly
against the already-approved R23 contract (§7) -- no new
contract-reconciliation commit needed.
