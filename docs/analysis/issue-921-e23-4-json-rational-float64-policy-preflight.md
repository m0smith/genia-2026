# Issue #921 Preflight — E23-4 Strict Generic JSON Boundary for Rational and Float64

Status: process artifact for issue #921 (E23-4). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority. This file records the
preflight review required by `docs/process/run-change.md` before
implementation, against the already-approved
`docs/design/r23-numeric-representation-interchange-contract.md` (§4.3,
§4.4, relevant parts of §5, §8), building on merged E23-1 (issue #911,
commit `992a8de`), E23-2 (issue #913, commit `9d41b5b`), and E23-3 (issue
#915, PR #918, commit `2543960`).

## Scope

Implement contract §4.3 (Rational), §4.4 (Float64), the Rational/Float64
portions of §5 (decode: confirm neither is ever produced), and §8
(diagnostics, this slice's new rejections only) for the **strict generic
JSON boundary only** (`_json_decode`/`_json_encode`, i.e. `json_decode_fn`/
`json_encode_fn` in `src/genia/builtins.py`).

Out of scope: compatibility `json_parse`/`json_stringify`/`json_pretty`/
`parse_jsonl_record` (E23-5 — untouched, see finding 1); full diagnostics
sweep and release-truth/docs sync beyond this slice's own truth (E23-6);
release audit (E23-7). R22 arithmetic/equality untouched. E23-1's
rendering functions and E23-2's format-spec code are not modified except
that `format_float64` now delegates its finite-value digit computation to
a small extracted helper (`float64_finite_canonical_text`) shared with the
new JSON encode path, so the two surfaces cannot independently drift —
`format_float64`'s own observable output is unchanged (verified by the
untouched behavior of every existing `format_float64`/E23-1 test).
E23-3's Integer/Decimal JSON paths are not modified except to call the
existing `stable_json_decimal` (read-only reuse, as instructed).

## Investigation findings

1. **Compatibility JSON confirmed still untouched.** Same two-family split
   E23-3's preflight documented: `json_parse_fn`/`json_stringify_fn`
   (public `json_parse`/`json_stringify`/`json_pretty`) use plain
   `json.loads`/`json.dumps` with `_json_to_runtime`/`_json_from_runtime`,
   which pass a bare Python `float` straight through unchanged (no
   `stable_json_decimal`/canonical-text involvement at all) and have no
   `GeniaDecimal`/`GeniaRational` branch. This slice does not touch either
   function or their private helpers — E23-5's job, per the contract's own
   §6 heading and the ticket's scope note.

2. **`_strict_json_from_runtime` (encode) had a pre-existing but
   contract-inconsistent Float64 branch, and no Rational branch at all,**
   confirmed by reading `src/genia/builtins.py` before writing tests:
   - `isinstance(value, GeniaRational)`: absent. Encoding a Rational fell
     through to the function's final `raise _JsonBoundaryFailure(
     "unsupported_json_value", value_type=_runtime_type_name(value))`
     (matching E23-3's preflight finding 3) — i.e. every Rational was
     unconditionally rejected, terminating or not. This is the gap §4.3
     closes: a terminating, `stable_json_decimal`-satisfying Rational must
     now encode successfully.
   - `isinstance(value, float)`: present, but returned the raw Python
     `float` value for `json.dumps` to serialize with its own
     `float.__repr__` binding after only an `isfinite` check. Two
     problems relative to §4.4: (a) `float.__repr__`'s fixed/scientific
     notation threshold does not match R23's own canonical
     `_canonical_decimal_text` fixed/scientific rule (`-6 <= adjusted
     exponent <= 20` fixed, else scientific with `e+`/`e-`) for every
     magnitude, so the emitted digit text could silently diverge from
     `format_float64`'s canonical spelling for large/small values; (b) it
     used `json.dumps`'s native float serialization instead of routing
     through the same shared canonical-text computation `format_float64`
     already implements, so the two surfaces could independently drift.
     Both are fixed by extracting `format_float64`'s finite-value digit
     computation into `float64_finite_canonical_text` (in
     `numeric_runtime.py`) and having JSON encode inject that exact text
     as a raw number token via the same sentinel-substitution mechanism
     E23-3 already built for Decimal, rather than letting `json.dumps`
     re-derive digits itself.

3. **`_strict_json_to_runtime` (decode) had a genuinely dead-but-reachable-
   looking `isinstance(value, float)` branch,** confirmed by tracing
   `json_decode_fn`'s `json.loads(...)` call: it registers
   `parse_int=_strict_json_int` (every integer-form token becomes Integer),
   `parse_float=_strict_json_decimal` (every fraction/exponent token
   becomes an exact `GeniaDecimal`, raising `_JsonBoundaryFailure` if
   unstable), and `parse_constant=_reject_json_constant` (`NaN`/`Infinity`/
   `-Infinity` tokens are rejected outright, before reaching
   `_strict_json_to_runtime` at all). Since these three hooks cover every
   way `json.loads` can produce a number, nothing in `parsed` can ever be
   a raw Python `float` by the time `_strict_json_to_runtime` walks it —
   the branch was unreachable dead code left over from before E23-3
   repointed `parse_float`. Per the ticket's explicit instruction ("make
   its unreachability explicit... don't leave a silently inconsistent
   branch"), this slice replaces the branch body with a `raise
   AssertionError(...)` defensive guard plus a comment explaining exactly
   why it cannot fire today, rather than silently returning a value or
   deleting the branch outright (deletion would remove the guard against
   a future scanner-hook regression silently reintroducing host-float
   decode). There is and was no `GeniaRational` branch anywhere in decode
   — contract §5's "JSON never directly constructs Rational" needed no
   code change, only confirmation.

4. **Computing a Rational's exact terminating-Decimal equivalent needs new
   number-theory logic, not present anywhere in `numeric_runtime.py`.**
   `GeniaRational` is always already reduced (`gcd(numerator, denominator)
   == 1`, `denominator > 1` — construction only through
   `rational_from_integers`, which collapses a reduced denominator of 1
   back to a plain Integer). The standard base-10-termination test is:
   after reduction, `denominator`'s only prime factors are 2 and/or 5.
   Implemented as `rational_terminating_decimal` by trial-dividing
   `denominator` by 2 then 5, counting each; if a remainder other than 1
   survives, the ratio is non-terminating (`None`). Otherwise, letting `k
   = max(twos, fives)`, multiplying `numerator` by the complementary
   powers of 2 and 5 (`2 ** (k - twos) * 5 ** (k - fives)`) turns the
   denominator into exactly `10 ** k` (since `2**k * 5**k == 10**k`), so
   `GeniaDecimal(numerator * that_factor, -k)` is the exact equivalent —
   pure integer arithmetic throughout, no `float(...)` cast anywhere
   (verified by a dedicated AST-based test, since a docstring merely
   *saying* "no float cast" is not evidence). `1/6` (denominator `2*3`)
   and `5/12` (denominator `4*3`) are explicit non-terminating test cases
   precisely because they still carry a factor of 2 — the "only 2 and 5,
   nothing else" predicate, not "has a factor of 2 or 5", is what must be
   correct.

5. **A terminating Rational can still fail `stable_json_decimal`,** exactly
   as an already-terminating Decimal literal can (E23-3 precedent): the
   exact equivalent Decimal may have more significant digits than
   binary64 round-trip precision preserves. This slice reuses
   `stable_json_decimal` unchanged (read-only reuse, per the ticket) on
   the computed equivalent Decimal, and deliberately assigns a *different*
   diagnostic reason than the "cannot be represented at all" case (finding
   6) so the two failure modes stay distinguishable.

6. **Diagnostic reason choice for the two distinct Rational rejection
   modes (contract §8):** a non-terminating ratio (e.g. `1/3`) can never
   be represented as a JSON number *at all*, regardless of magnitude or
   precision — this is categorically the same situation as any other
   JSON-incompatible value kind, so it reuses the existing
   `unsupported_json_value` reason (with `value_type="rational"`,
   matching the shape every other `unsupported_json_value` rejection in
   this file already carries) rather than the numeric-domain reason. A
   terminating ratio whose exact Decimal equivalent fails
   `stable_json_decimal` *is*, in principle, representable as a number —
   it only fails the same binary64-round-trip stability predicate an
   equivalent unstable Decimal literal would — so it reuses
   `json_number_out_of_range`, identical to Decimal's own rejection for
   that same predicate failure one branch above it in
   `_strict_json_from_runtime`. This mirrors the existing file's own
   established split between `unsupported_json_value` (wrong kind
   entirely) and `json_number_out_of_range` (right kind, failed numeric
   predicate) rather than inventing a third reason.

7. **NaN/Infinity Float64 rejection already normalizes correctly** via the
   pre-existing `isfinite` check (finding 2); this slice keeps that check
   ahead of the new canonical-text computation and confirms (by test) that
   `json_encode_fn`'s `try`/`except (_JsonBoundaryFailure, TypeError,
   ValueError)` structure means a non-finite value never reaches
   `json.dumps(..., allow_nan=False)` in the first place, so that
   `allow_nan=False` guard is genuinely defense-in-depth here, not the
   primary rejection mechanism (the primary mechanism is this
   `isfinite`-triggered `_JsonBoundaryFailure`, normalized the same way
   every other JSON boundary rejection is).

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?**
   Reference-host (Python) strict generic JSON encode/decode:
   `_strict_json_from_runtime` (new `GeniaRational` branch, rewritten
   `float` branch) and `_strict_json_to_runtime` (dead-branch-made-
   explicit) in `src/genia/builtins.py`, plus two new pure functions in
   `src/genia/numeric_runtime.py`: `rational_terminating_decimal` and
   `float64_finite_canonical_text` (the latter also now used internally by
   the unchanged-output `format_float64`). No Core IR, lexer/parser, or
   R22 arithmetic/equality machinery is touched. Compatibility
   `json_parse`/`json_stringify` remain untouched (finding 1).

2. **Does this change alter the minimal portable Core IR node family?**
   No. Boundary-conversion logic between JSON text and already-existing
   runtime values (`GeniaRational`, `float`/Float64); no new Core IR node.

3. **Does this change require a host-native binary float at any point in
   the new code path?**
   Only exactly where the contract already requires it: `float64` values
   are themselves the host binary64 representation by definition (§4.4's
   own subject), and `rational_terminating_decimal`'s finiteness test and
   exact-Decimal construction are pure integer arithmetic with no
   `float(...)` cast at all (finding 4, machine-checked). The only
   `float`-typed value that ever crosses this new code is an
   already-existing genuine Float64 runtime value being encoded as
   itself, never an approximation introduced by this change.

4. **Does this change require another host implementation (Node/Java/Rust/
   Go/C++) to consult Python-specific behavior to reproduce it?**
   No new cross-host obligation beyond the contract's own host-independent
   algorithm (§4.3's 2/5-prime-factor termination test is elementary
   number theory; §4.4's "canonical shortest-roundtrip decimal spelling"
   is the same computation E23-1 already specifies host-independently).
   The sentinel-substitution mechanism reused for Float64 (finding 2) is
   the same private reference-host implementation seam E23-3's preflight
   already documented as non-portable — another host emits the same
   canonical text directly however its own JSON writer allows raw number
   injection.

5. **Does this change affect R16 multi-host conformance infrastructure, R17
   arbitrary-precision Integer, R18 equality/map-key, R19 diagnostics, or
   R20 open functions?**
   R17 Integer semantics unchanged. R18 equality/map-key unchanged (a
   round-trip test confirms cross-kind Decimal/Rational equality via the
   existing `genia_equal`, not a new equality rule). R19: both new
   rejection modes route through the existing `_JsonBoundaryFailure` ->
   `_json_boundary_err` normalization already used by every other JSON
   boundary rejection, reusing two already-established reasons
   (`unsupported_json_value`, `json_number_out_of_range` — finding 6) with
   no new diagnostic channel. R20 open functions unaffected.

6. **Is any part of this change host-local-only (Python reference host
   convenience) rather than portable?**
   The sentinel-substitution injection mechanism (same as E23-3, now also
   used for Float64) is this reference host's own device; the portable
   requirement is only the final JSON text's exact byte content, which is
   what tests pin.

7. **What new portable evidence must exist for another host to reproduce
   this behavior without reading Python source?**
   `tests/unit/test_r23_json_rational_float64_boundary.py`:
   `rational_terminating_decimal` unit cases (exact 2/5-only-denominator
   values including negative numerators; explicit non-2/5-factor
   rejections including denominators that still carry a factor of 2, e.g.
   6 and 12, to prove the predicate is "only 2 and 5" not "has a factor of
   2 or 5"; a large-prime-denominator case; an AST-based no-`float()`-cast
   proof); encode of several terminating Rationals to their exact decimal
   text; encode rejection of non-terminating Rationals with
   `unsupported_json_value` and of a terminating-but-unstable Rational
   with `json_number_out_of_range`; confirmation that decoding an encoded
   Rational's JSON form always yields a Decimal, never a Rational, and
   that this Decimal is R18-equal to the original Rational; Float64 encode
   of several finite values (including large/small magnitudes needing
   scientific notation, and signed zero) matching `format_float64`'s
   digits exactly with the `float64(...)` wrapper stripped; Float64 NaN/
   Infinity encode rejection with a normalized diagnostic, not a raw
   Python exception; confirmation that every JSON fraction/exponent decode
   token still produces `GeniaDecimal`, never `float`; and Genia-source-
   level round-trip cases through `1 / 3` (rejected) and `1 / 4` (accepted)
   exact division.

## Conclusion

Preflight is complete. The strict/compatibility JSON split (finding 1)
remains exactly as E23-3 left it, so this slice's boundary is precisely
the `GeniaRational` and `float` branches of `_strict_json_from_runtime`/
`_strict_json_to_runtime` and their `numeric_runtime.py` support. The
pre-existing Float64 branches (findings 2-3) were contract-inconsistent
(encode) and dead (decode) respectively, not merely "not yet implemented"
— both are corrected/made-explicit rather than left in place, per the
ticket's own explicit instruction to investigate and resolve exactly this.
`rational_terminating_decimal` is new, pure-integer, and independently
testable (finding 4). The two Rational diagnostic reasons are a
deliberate, documented choice reusing existing reason vocabulary rather
than inventing new diagnostics (finding 6). Proceeding directly against
the already-approved R23 contract (§4.3, §4.4, §5, §8) — no new
contract-reconciliation commit needed.
