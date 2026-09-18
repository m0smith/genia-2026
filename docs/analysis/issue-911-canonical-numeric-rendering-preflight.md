# Issue #911 Preflight — E23-1 Canonical Numeric Rendering

Status: process artifact for issue #911 (E23-1). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority. This file records the
preflight review required by `docs/process/run-change.md` before
implementation, for the already-approved
`docs/design/r23-numeric-representation-interchange-contract.md` (§2, §3).

## Scope

Implement only canonical display/debug rendering for Integer, Decimal,
Rational, and Float64 per contract §2-3:

- Decimal fixed/scientific selection via `adjusted_exponent`, no
  insignificant trailing fractional zeros, `.0` suffix when integral,
  lowercase `e`, explicit exponent sign, no unnecessary exponent leading
  zeros.
- Rational's `<numerator>/<denominator>` atom (display == debug).
- Float64's `float64(<shortest-roundtrip-decimal>)` atom, signed zero, and
  non-finite spellings.
- Integer: confirm existing canonical rendering already satisfies the
  contract; no rewrite unless a real bug is found.
- Wire the canonical atoms into every rendering surface that currently
  lacks them (REPL/CLI final-value echo, generic display/debug dispatch),
  with no host dataclass/repr leakage.

Out of scope (later R23 slices, per issue #911): field-format-spec
integration (E23-2), JSON encode/decode and `stable_json_decimal` (E23-3/
E23-4), compatibility JSON (E23-5), diagnostics/docs sync (E23-6), audit
(E23-7). R22 arithmetic, equality, and the numeric runtime's mathematical
model are frozen and unchanged; only text rendering of already-computed
values changes.

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?**
   Reference-host (Python) numeric-value-to-text rendering only: the
   `GeniaDecimal.__repr__`/`__str__` and `GeniaRational.__repr__`/`__str__`
   methods in `src/genia/numeric_runtime.py`, a new `format_float64`
   function in the same module, and the `format_display`/`format_debug`
   dispatch in `src/genia/utf8.py` that every evaluator/REPL/CLI output
   surface already funnels through. It does not touch Core IR, lexing/
   parsing, or the R22 arithmetic/equality/comparison machinery.

2. **Does this change alter the minimal portable Core IR node family?**
   No. Core IR is unaffected; this is purely a post-evaluation textual
   rendering concern.

3. **Does this change require a host-native binary float at any point in
   the new rendering code path?**
   Only for Float64 itself, which the R22 contract already defines as
   "a Python float already is exactly one IEEE-754 binary64 bit pattern" --
   i.e. Float64 IS host binary64 by design, not something this slice
   introduces. Decimal and Rational rendering operate purely on the
   already-exact arbitrary-precision `coefficient`/`exponent` or
   `numerator`/`denominator` integers; no `float(...)` call is introduced
   for those two kinds. For Float64's shortest-round-trip decimal spelling,
   this uses `repr(value)` (CPython's own correctly-rounded shortest
   round-trip textual spelling, guaranteed to parse back to the identical
   bits) parsed exactly via `decimal.Decimal(repr(value))` into an exact
   coefficient/exponent pair -- never a second, independent, potentially
   inconsistent decimal-formatting algorithm.

4. **Does this change require another host implementation (Node/Java/Rust/
   Go/C++) to consult Python-specific behavior to reproduce it?**
   No new cross-host obligation beyond what R22's Float64-is-host-binary64
   decision already implies. The Decimal fixed/scientific rule (adjusted
   exponent threshold, digit placement, trailing-zero stripping) is
   specified in the contract in host-independent arithmetic/string terms
   and is reproducible from the contract text alone. The Float64 "shortest
   round-trip decimal" requirement is itself host-independent (IEEE-754
   binary64 shortest round-trip is a well-defined, standard algorithm,
   e.g. Grisu/Ryu-class algorithms); this reference host happens to satisfy
   it via CPython's built-in correctly-rounded `repr(float)`, but another
   host must independently implement (or reuse a library for) the same
   well-defined shortest-round-trip guarantee -- it does not need to consult
   CPython internals to do so.

5. **Does this change affect R16 multi-host conformance infrastructure, R17
   arbitrary-precision Integer, R18 equality/map-key, R19 diagnostics, or
   R20 open functions?**
   No behavioral change to any of those. Integer rendering is verified,
   not rewritten. No equality/map-key/comparison code path is touched.
   No new diagnostic/error path is introduced (this slice adds a rendering
   function, not a new failure mode); R19 diagnostic normalization is
   unaffected because no render path in scope currently raises here for
   values in scope.

6. **Is any part of this change host-local-only (Python reference host
   convenience) rather than portable?**
   The specific mechanism (`decimal.Decimal(repr(value))` as the way this
   reference host obtains a correctly-rounded shortest-round-trip decimal)
   is a host-local implementation detail; the *portable* requirement is
   the contract's own "shortest decimal spelling that rounds to the
   identical binary64 bits under round-to-nearest/ties-to-even" text, which
   is host-independent and must be what any conformance evidence checks
   against (the rendered digits/value), not the Python mechanism used to
   produce them.

7. **What new portable evidence must exist for another host to reproduce
   this behavior without reading Python source?**
   New focused unit tests (`tests/unit/test_r23_canonical_numeric_rendering.py`)
   pinning exact expected canonical strings for Decimal fixed/scientific
   boundary cases, Rational spelling, Float64 shortest-round-trip spelling
   (including signed zero and non-finite), and Integer, plus a REPL/CLI-
   level test proving the final-value echo path uses this canonical
   renderer. These pin the contract's observable text output directly and
   are reproducible by any host implementation without reading this
   reference host's Python source.

## Conclusion

Preflight is complete. This change is pure reference-host rendering logic
behind host-independent, contract-specified text output; no Core-IR or
cross-host-machinery leakage found. Proceeding directly against the
already-approved R23 contract (§2-3) -- no new contract-reconciliation
commit is needed for this slice, per issue #911 ("already an approved
planning contract; not implementation").
