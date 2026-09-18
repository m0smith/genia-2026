# Issue #923 Preflight — E23-5 Compatibility JSON Reconciliation

Status: process artifact for issue #923 (E23-5). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority. This file records the
preflight review required by `docs/process/run-change.md` against the
already-approved
`docs/design/r23-numeric-representation-interchange-contract.md` (§6,
"Compatibility JSON surfaces"), building on merged E23-1 (issue #911),
E23-2 (issue #913), E23-3 (issue #915, PR #918), and E23-4 (issue #921,
PR #922).

## Scope

Implement contract §6 for the compatibility JSON surface only:
`json_parse`/`json_stringify`/`json_pretty` (`json_parse_fn`/
`json_stringify_fn`, backed by `_json_to_runtime`/`_json_from_runtime` in
`src/genia/builtins.py`) and `parse_jsonl_record`
(`parse_jsonl_record_fn`, which was confirmed to share `_json_to_runtime`
but not the numeric decode hook -- see finding 1). The strict generic JSON
boundary (`json_decode`/`json_encode`, `_strict_json_to_runtime`/
`_strict_json_from_runtime`) is frozen (E23-3/E23-4) and is only called
into, never modified.

Out of scope: unifying the `none(...)`-vs-`err(...)` failure-shape
difference between compatibility and strict JSON (an approved
pre-existing non-numeric difference); a full diagnostics-normalization
sweep and release-example/docs truth sync beyond this slice's own truth
(E23-6); release audit (E23-7). R22 arithmetic/equality untouched.

## Investigation findings

1. **`parse_jsonl_record_fn` shares `_json_to_runtime` with `json_parse_fn`
   but calls `json.loads(text)` with no `parse_float` hook of its own** --
   confirmed by reading both functions side by side before any change.
   Both therefore needed the same fix (finding 2's shared hook), not two
   independent ones; `parse_jsonl_record`'s existing `_jsonl_value_type`
   helper already classified `GeniaDecimal` alongside `int`/`float` as
   `"number"`, which turned out to be forward-looking dead code until this
   slice made it reachable.

2. **Decode: a single lexical parser, reused by both strict and
   compatibility hooks, with the stability gate as the only difference.**
   E23-3's `_strict_json_decimal` was split into a shared
   `_parse_json_decimal_token(text)` (pure lexical regex ->
   coefficient/exponent -> `GeniaDecimal`, unchanged from E23-3, `float()`
   never called) plus two thin callers: `_strict_json_decimal` (unchanged
   behavior -- calls the shared parser, then still enforces
   `stable_json_decimal`) and a new `_compat_json_decimal` (calls the same
   shared parser, deliberately *without* the stability check). Both
   `json_parse_fn` and `parse_jsonl_record_fn` now register
   `parse_float=_compat_json_decimal` on their `json.loads` calls. This
   satisfies contract §6's explicit instruction ("reuse common lexical
   numeric conversion machinery ... rather than duplicate competing
   parsers") literally: there is exactly one regex/token parser
   (`_JSON_NUMBER_TOKEN_RE` + `_parse_json_decimal_token`) in the file,
   shared by decode paths.

3. **Decode permissiveness decision (deliberate, documented): compatibility
   decode does not enforce `stable_json_decimal`.** Before this change,
   `json_parse`/`parse_jsonl_record` never rejected any syntactically
   valid JSON number, regardless of precision -- they simply handed back
   whatever `float(...)` produced. Their whole documented contract
   (`docs/std/prelude/json.genia`'s own `@doc` strings) is "parse JSON
   text" returning `none(...)` only for outright parse/type failures, in
   contrast to strict `json_decode`'s `err(reason, context)` shape for
   deliberate semantic rejections (already out of scope to unify, per the
   ticket). Making compatibility decode newly reject numbers that fail
   `stable_json_decimal` would be a new failure mode with no precedent in
   the existing tests
   (`tests/unit/test_json_stdlib.py`) or docs, and would work against
   compatibility mode's documented purpose ("legacy tolerance"). The
   contract's own wording is narrower than strict validation: §6 requires
   only that decode "must not silently materialize fraction/exponent
   numbers as host Float64" -- it does not require rejecting an unstable
   value. Decision: `_compat_json_decimal` always succeeds for any token
   the JSON scanner already recognized as a number, producing an exact
   `GeniaDecimal` (never a Python `float`), with no stability gate. This
   is the "more permissive" reading the ticket explicitly allows, and is
   the reading that best preserves compatibility JSON's existing observed
   behavior of never rejecting a syntactically valid document.

4. **`_json_to_runtime` needed a `GeniaDecimal` passthrough branch** --
   without it, a `GeniaDecimal` produced by the new `parse_float` hook
   would hit `_json_to_runtime`'s final `raise TypeError(...)` (it only
   special-cased `bool`/`int`/`float`/`str`). Added as the first branch
   (before the general `bool, int, float, str` tuple check) so a Decimal
   flows straight through into Genia runtime values (list/map recursion
   already handles arbitrary Any).

5. **Encode: `json_stringify` could not encode `GeniaDecimal`/
   `GeniaRational` at all before this slice** (confirmed: `_json_from_runtime`
   raised `TypeError` for any value outside bare `bool`/`int`/`float`/
   `str`/`None`/list/map, exactly as issue #923's own research stated).
   Two options were weighed: (a) leave numeric-kind encode unsupported,
   treating it as an already-approved nonnumeric-representation-boundary
   difference; or (b) extend `_json_from_runtime` to accept
   `GeniaDecimal`/`GeniaRational`/Float64, reusing E23-3/E23-4's
   canonical-text + sentinel-injection encode machinery. Decision: **(b)**,
   because option (a) would introduce a new decode/encode asymmetry this
   very slice would itself create: after finding 2-3, `json_parse` now
   *produces* `GeniaDecimal` for every fraction/exponent token, so
   `json_stringify(json_parse(text))` would immediately break for any
   JSON document containing a decimal number -- a regression in
   compatibility JSON's own round-trip usability introduced by this
   slice's own decode fix, not a pre-existing, independently-approved
   boundary. Implementation: `_json_from_runtime` gained `GeniaDecimal`/
   `GeniaRational`/`float` branches, reusing a small extracted
   `_json_number_sentinel(canonical_text, decimal_sentinels)` helper (the
   same sentinel-substitution mechanism `_strict_json_from_runtime`
   already implements inline) so the substitution device itself is not
   duplicated either. Consistent with finding 3's decode permissiveness
   decision, compatibility encode of `GeniaDecimal`/a terminating
   `GeniaRational` does **not** enforce `stable_json_decimal` -- it always
   emits the value's exact canonical decimal text (E23-1's `repr`), even
   for a precision that would not round-trip through binary64 cleanly.
   Only the two cases that cannot be represented as a JSON number *at
   all* -- a non-terminating `GeniaRational`, or a non-finite Float64 --
   still raise (as `TypeError`/`ValueError`, matching this surface's
   existing `none("json-stringify-error", ...)` failure shape, not
   strict's `err(...)`).

6. **Encode: Float64 (bare Python `float`) unification.** Before this
   slice, a `float` value handed to `json_stringify` passed straight
   through to `json.dumps`, which serializes it via `float.__repr__` --
   whose fixed/scientific notation threshold does not match R23's
   canonical `_canonical_decimal_text` rule (E23-1) for every magnitude,
   the same contract-inconsistency E23-4 fixed for strict encode. Per the
   ticket's explicit prompt ("a Float64 value that DOES get
   compatibility-encoded ... must not go through a path that diverges
   from R23 canonical digits without you having deliberately decided
   that's fine for THIS surface"), the deliberate decision here is **not**
   fine to leave diverging: `_json_from_runtime`'s `float` branch now
   renders through the same `float64_finite_canonical_text` (E23-4,
   `numeric_runtime.py`) strict encode uses, via the same sentinel
   mechanism, so a Float64's JSON number text is now identical whether it
   reaches JSON through `json_encode` or `json_stringify`. This directly
   satisfies §6's "must not preserve a second contradictory host-float
   numeric model" for the one case (an already-existing Float64 runtime
   value) where compatibility JSON legitimately does still involve a
   genuine host float. NaN/Infinity remain rejected (unchanged
   `math.isfinite` guard, now raising before the canonical-text call
   rather than before a `json.dumps` call).

7. **The strict JSON boundary (`_strict_json_from_runtime`/
   `_strict_json_to_runtime`, `json_decode_fn`/`json_encode_fn`) is
   untouched** -- confirmed by diffing: only `_strict_json_decimal`'s body
   changed shape (delegates to the new shared `_parse_json_decimal_token`
   instead of inlining the regex match), with byte-for-byte identical
   observable behavior (same regex, same stability check, same exception).
   No other line in the strict functions changed.

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?**
   Reference-host (Python) compatibility JSON parse/stringify:
   `json_parse_fn`, `parse_jsonl_record_fn`, `json_stringify_fn`, and
   their shared private helpers `_json_to_runtime`/`_json_from_runtime`,
   plus the new shared decode helper `_parse_json_decimal_token` and
   `_compat_json_decimal` hook, and the new shared encode sentinel helper
   `_json_number_sentinel`, all in `src/genia/builtins.py`. No Core IR,
   lexer/parser, or R22 arithmetic/equality machinery is touched. No new
   function in `numeric_runtime.py` -- this slice calls existing E23-3/
   E23-4 functions (`stable_json_decimal`, `rational_terminating_decimal`,
   `float64_finite_canonical_text`) only, never modifying them.

2. **Does this change alter the minimal portable Core IR node family?**
   No. Boundary-conversion logic between JSON text and already-existing
   runtime values (`GeniaDecimal`, `GeniaRational`, `float`/Float64); no
   new Core IR node, no new public Genia-level function (`json_parse`/
   `json_stringify`/`json_pretty`/`parse_jsonl_record` keep their existing
   signatures and Outcome shapes).

3. **Does this change require a host-native binary float at any point in
   the new code path?**
   Only where a genuine Float64 value already existed as itself (finding
   6) -- never as an approximation manufactured from a JSON fraction/
   exponent token. `_parse_json_decimal_token` (shared by both strict and
   compatibility decode) never calls `float(...)`, unchanged from E23-3.

4. **Does this change require another host implementation (Node/Java/Rust/
   Go/C++) to consult Python-specific behavior to reproduce it?**
   No new cross-host obligation beyond the contract's own host-independent
   requirement (§6: compatibility decode must produce exact decimal
   values for fraction/exponent tokens, not host float; compatibility
   encode of a numeric kind, where supported, must match the same
   canonical text strict encode would produce). The sentinel-substitution
   mechanism is this reference host's own device (same non-portable seam
   E23-3/E23-4 already documented); the portable requirement is only the
   final JSON text's exact byte content, which is what the new tests pin.

5. **Does this change affect R16 multi-host conformance infrastructure, R17
   arbitrary-precision Integer, R18 equality/map-key, R19 diagnostics, or
   R20 open functions?**
   R17 Integer unchanged (compatibility Integer decode/encode paths
   untouched by this slice). R18 unaffected (no new equality rule; a
   round-trip test confirms decode/encode symmetry through existing
   `genia_equal`/direct value comparison, not new semantics). R19: no new
   diagnostic reason string -- decode failures still return
   `none("json-parse-error"/"invalid_jsonl_record", context)` exactly as
   before (the new `_JsonBoundaryFailure` catch clauses in `json_parse_fn`/
   `parse_jsonl_record_fn` are defensive-only, matching
   `_parse_json_decimal_token`'s own `# pragma: no cover` -- the JSON
   scanner already guarantees the regex always matches, so this branch is
   unreachable exactly as its strict-mode counterpart is); encode failures
   still return `none("json-stringify-error", context)` exactly as
   before, now additionally reachable for a non-terminating Rational or a
   non-finite float ("cannot represent this at all"), a `TypeError`/
   `ValueError`-shaped failure like every existing `json_stringify`
   rejection. R20 open functions unaffected.

6. **Is any part of this change host-local-only (Python reference host
   convenience) rather than portable?**
   The sentinel-substitution injection mechanism (shared with strict
   encode) is this reference host's own device; the portable requirement
   is only the final JSON text's exact byte content, which is what tests
   pin. `parse_float=` as a `json.loads` scanner hook is likewise a
   CPython `json` module convenience -- the portable requirement is only
   that a fraction/exponent token decodes to an exact Decimal value, not
   the specific hook mechanism used to achieve that in Python.

7. **What new portable evidence must exist for another host to reproduce
   this behavior without reading Python source?**
   `tests/unit/test_r23_compatibility_json_reconciliation.py`: a
   fraction/exponent token decoded via `json_parse` is an exact
   `GeniaDecimal`, never a Python `float` (including a case at a
   precision that would fail `stable_json_decimal`, to prove the
   permissive-decode decision); a direct unit-level proof that
   `json_parse`'s and `json_decode`'s `parse_float` hooks both delegate to
   the same shared `_parse_json_decimal_token` function object (not a
   black-box behavioral inference); `json_stringify` encoding of
   `GeniaDecimal`/terminating `GeniaRational`/finite Float64 values,
   including a precision case that would fail strict `json_encode`'s
   `stable_json_decimal` gate but still succeeds here; `json_stringify`
   rejection of a non-terminating `GeniaRational` and of a non-finite
   Float64 with the existing `none("json-stringify-error", ...)` shape;
   a `json_stringify(json_parse(text))` round-trip case proving the
   decode/encode asymmetry finding 5 identified is resolved;
   `parse_jsonl_record`'s decode of a fraction/exponent-bearing line
   producing the same exact `GeniaDecimal`, not a Python `float`; a
   Float64 encode case proving `json_stringify`'s digits now match
   `format_float64`'s (and strict `json_encode`'s) canonical spelling
   rather than `float.__repr__`'s.

## Conclusion

Preflight is complete. Contract §6's two directives -- "must not silently
materialize fraction/exponent numbers as host Float64" (decode) and
"reuse common lexical numeric conversion machinery ... rather than
duplicate competing parsers" -- are both satisfied by a single shared
lexical parser (`_parse_json_decimal_token`) with two thin, deliberately
different-strictness callers (finding 2-3). The encode-scope decision
(finding 5) is driven by an asymmetry this slice's own decode fix would
otherwise introduce, not by a mechanical re-litigation of every existing
approved compatibility/strict difference; the Float64 canonical-text
unification (finding 6) directly closes the "second contradictory
host-float numeric model" §6 names. `parse_jsonl_record` (finding 1) was
confirmed to share the same underlying numeric decode gap and is fixed by
the same shared hook. The strict JSON boundary is confirmed unmodified
except for one pure internal delegation with identical observable
behavior (finding 7). Proceeding directly against the already-approved
R23 contract §6 -- no new contract-reconciliation commit needed.
