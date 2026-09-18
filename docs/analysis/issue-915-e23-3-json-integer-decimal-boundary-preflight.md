# Issue #915 Preflight — E23-3 Strict Generic JSON Boundary for Integer and Decimal

Status: process artifact for issue #915 (E23-3). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority. This file records the
preflight review required by `docs/process/run-change.md` before
implementation, against the already-approved
`docs/design/r23-numeric-representation-interchange-contract.md` (§4.1,
§4.2, §5, §8), building on the merged E23-1 (issue #911, commit `992a8de`)
canonical renderer and E23-2 (issue #913, commit `9d41b5b`) format-spec
integration.

## Scope

Implement contract §4.1 (Integer), §4.2 (`stable_json_decimal`), §5
(decode, Integer/Decimal only), and §8 (diagnostics, this slice only)
for the **strict generic JSON boundary only** — see investigation finding 1
below for why that is `_json_decode`/`_json_encode` (Genia-facing
`json_decode`/`json_encode`) and not `json_parse`/`json_stringify`.

Out of scope: Rational/Float64 JSON policy (E23-4 — left exactly as found,
see finding 3); compatibility `json_parse`/`json_stringify`/`json_pretty`/
`parse_jsonl_record` (E23-5 — untouched, see finding 1); full diagnostics
sweep and release-truth/docs sync beyond this slice's own truth (E23-6);
release audit (E23-7). R22 arithmetic/equality are untouched. E23-1's
rendering functions and E23-2's format-spec code are not modified.

## Investigation findings

1. **Two JSON code paths confirmed, with a clear "strict" vs
   "compatibility" split.** `src/genia/builtins.py` has two independent
   families:
   - Strict generic JSON: `json_decode_fn`/`json_encode_fn` (registered as
     `_json_decode`/`_json_encode`, autoloaded as public `json_decode`/
     `json_encode` from `std/prelude/json.genia`). These already use a
     dedicated strict path: `json.loads(text, object_pairs_hook=
     _strict_json_object, parse_int=_strict_json_int, parse_float=
     _strict_json_float, parse_constant=_reject_json_constant)` for
     decode, and `_strict_json_from_runtime` + `json.dumps(...,
     allow_nan=False)` for encode, with a `_JsonBoundaryFailure` exception
     normalized into `err(reason, context)` via `_json_boundary_err`. This
     is E23-3/E23-4/E23-5's target boundary — GENIA_STATE.md already
     labels it "the Experimental portable R9 JSON representation
     boundary".
   - Compatibility JSON: `json_parse_fn`/`json_stringify_fn` (public
     `json_parse`/`json_stringify`/`json_pretty`), using plain
     `json.loads`/`json.dumps` with no strict hooks, `_json_to_runtime`/
     `_json_from_runtime` (which only accept bare Python
     `bool`/`int`/`float`/`str`, not `GeniaDecimal`), and `none(...)`
     failure shape instead of `err(...)`. GENIA_STATE.md already labels
     these "legacy ... retain their compatibility behavior". This slice
     does not touch `json_parse_fn`/`json_stringify_fn`/
     `_json_to_runtime`/`_json_from_runtime` at all — that reconciliation
     is explicitly E23-5's job per the contract's own §6 heading and this
     ticket's scope note. Passing a `GeniaDecimal` to `json_stringify`
     today already raises `TypeError("json_stringify expected a
     JSON-compatible value...")` (`_json_from_runtime`'s final `raise`);
     this slice leaves that exactly as found.

2. **`_strict_json_float`'s `parse_float` hook already receives the raw
   lexical JSON number token text**, not a pre-parsed host float: Python's
   `json.scanner` matches the number regex and, when a fraction or
   exponent is present, calls `parse_float(matched_text)` with that exact
   substring before any host float materializes elsewhere in the pipeline
   (the *current* implementation happens to immediately call
   `float(text)` inside that hook — that is exactly the "goes through
   `float()`" gap E23-3 must close, and it is fully containable to
   rewriting this one hook function to build a `GeniaDecimal` from the
   token text directly, never calling `float(...)` on the token). Integer
   -form tokens already go through `_strict_json_int` (`int(text)` +
   `_JSON_SAFE_INTEGER` bound check) unchanged — Integer behavior already
   matches contract §4.1/§5 exactly and needs no change beyond continuing
   to reuse the single existing `_JSON_SAFE_INTEGER = 9_007_199_254_740_991`
   module constant (no new literal).

3. **Current Rational/Float64 JSON behavior (documented, not touched):**
   `_strict_json_from_runtime` (encode) and `_strict_json_to_runtime`
   (decode) have no `GeniaRational` branch at all today — encoding a
   Rational falls through to the final `raise _JsonBoundaryFailure(
   "unsupported_json_value", value_type=_runtime_type_name(value))`, i.e.
   Rational is currently rejected from strict JSON encode outright (not
   silently rounded). There is no decode path that can ever produce a
   Rational (contract §5: "JSON never directly constructs Rational" — already
   true and unaffected). Float64 (`float`) already has a real branch in
   both `_strict_json_to_runtime`/`_strict_json_from_runtime` today
   (`isinstance(value, float)` + `math.isfinite` check) predating this
   slice; once this slice changes fraction/exponent *decode* to produce
   `GeniaDecimal` instead of `float`, that pre-existing Float64 branch
   becomes reachable on decode only if a `float` literal is ever produced
   there another way (it will not be, post this slice, since `parse_float`
   is the only way `json.loads` manufactures a Python float and this slice
   repoints it at `GeniaDecimal`), so it becomes dead code on the decode
   side but is left in place untouched — removing it is E23-4's call, not
   this slice's, and it remains live/correct for `float`-encode from
   Genia source (`float64(...)` literal values) either way. Documented
   here for E23-4's author; not fixed or removed in this slice.

4. **`stable_json_decimal` does not exist yet** (confirmed by repository
   grep before writing tests): this slice introduces it from scratch in
   `src/genia/numeric_runtime.py`, next to `GeniaDecimal` and its existing
   `_float_shortest_roundtrip_coefficient_exponent`/
   `_canonical_decimal_text` helpers (already implementing exactly the
   "shortest-roundtrip decimal for finite binary64 bits" step the
   predicate's step 3 needs, from E23-1). The predicate is implemented by
   converting `d` to its exact `(numerator, denominator)` fraction (the
   existing `GeniaDecimal._as_fraction()` accessor) and computing
   `numerator / denominator` in Python — this is the same correctly-
   rounded round-to-nearest/ties-to-even conversion `to_float64` already
   documents and relies on (native arbitrary-precision `int / int` true
   division), raising `OverflowError` exactly on overflow-to-infinity
   (caught and turned into `False`) and returning an exact `0.0` on
   underflow when `d` is nonzero (also `False`). Steps 3-5 (recompute the
   shortest-roundtrip decimal for those bits, reparse it, compare) reuse
   `_float_shortest_roundtrip_coefficient_exponent` and are collapsed to a
   direct canonical `(coefficient, exponent)` tuple comparison against
   `d`'s own already-canonical fields — valid because `GeniaDecimal`'s
   constructor already canonicalizes (§2.2/`_canonicalize`: zero is always
   exactly `(0, 0)`, and a nonzero coefficient's magnitude has no trailing
   base-10 zeros), so canonical form is a unique representative of
   mathematical value and tuple equality *is* the "mathematically equal"
   check the contract's step 5 asks for, with no separate re-parse-then-
   compare step needed.

5. **Encode needs a raw (unquoted) canonical-text JSON number token**,
   which Python's `json.dumps` cannot natively emit for a custom type:
   `float.__repr__`/`int.__repr__` are the only numeric renderers the
   stdlib encoder calls, and subclassing does not intercept this (the
   encoder binds `float.__repr__`/calls `repr()` on `int`/`float`
   directly, verified interactively against CPython 3.11's `json.encoder`
   before writing this doc). `decimal.Decimal` is not natively JSON-
   serializable either (`TypeError: Object of type Decimal is not JSON
   serializable`, also verified interactively). The implementation
   therefore has `_strict_json_from_runtime` return a unique per-value
   ASCII sentinel string (`uuid.uuid4().hex`-based, so the encoder places
   it as an ordinary, correctly-escaped JSON string literal) for each
   JSON-number-encodable `GeniaDecimal`, and `json_encode_fn` performs one
   final exact-text substitution of each quoted sentinel for its raw
   canonical Decimal spelling (`repr(GeniaDecimal)`, i.e. E23-1's
   `_canonical_decimal_text`) after `json.dumps` returns. This never
   changes existing output for any other value kind (string/int/bool/
   null/list/map), never rounds the emitted Decimal text, and is
   confined to `json_encode_fn`/`_strict_json_from_runtime` — no new
   general-purpose JSON serializer is introduced, and container
   traversal/nesting-depth/duplicate-key/Unicode-scalar checks are
   entirely unchanged.

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?**
   Reference-host (Python) strict generic JSON encode/decode:
   `json_decode_fn`/`json_encode_fn`, `_strict_json_int`,
   `_strict_json_float` (replaced by a lexical `GeniaDecimal`-producing
   hook), `_strict_json_to_runtime`, `_strict_json_from_runtime`, all in
   `src/genia/builtins.py`, plus a new `stable_json_decimal` predicate in
   `src/genia/numeric_runtime.py`. No Core IR, lexer/parser, or R22
   arithmetic/equality machinery is touched. Compatibility
   `json_parse`/`json_stringify` are untouched (finding 1).

2. **Does this change alter the minimal portable Core IR node family?**
   No. This is boundary-conversion logic between JSON text and already-
   existing runtime values (`int`, `GeniaDecimal`); no new Core IR node.

3. **Does this change require a host-native binary float at any point in
   the new code path?**
   Only internally and transiently inside `stable_json_decimal` itself,
   exactly as the contract's own algorithm specifies (step 1: "Convert `d`
   to IEEE-754 binary64"): it is the *subject* of the stability check, not
   a value that survives into the decoded/encoded Genia-visible result.
   Decode never calls `float(token_text)` anywhere in the lexical path —
   the raw JSON number token text goes directly to an integer
   coefficient/exponent pair via string slicing/`int(...)`, and only that
   already-constructed exact `GeniaDecimal` is (separately) tested for
   stability by converting *it* to binary64 for the predicate's own
   purpose. Encode never rounds through a host float either.

4. **Does this change require another host implementation (Node/Java/Rust/
   Go/C++) to consult Python-specific behavior to reproduce it?**
   No new cross-host obligation beyond what the contract's algorithm
   already specifies in host-independent terms (round-to-nearest/ties-to-
   even binary64 conversion, shortest-roundtrip decimal spelling,
   re-parse-and-compare). The lexical JSON-number-token grammar (optional
   `-`, integer digits, optional `.` fraction digits, optional exponent)
   is the JSON standard's own grammar, not a Python idiom. The one Python-
   specific *implementation* detail (the `uuid.uuid4().hex` sentinel /
   text-substitution mechanism for injecting a raw JSON number token past
   `json.dumps`) is a private reference-host implementation seam, not
   portable Genia semantics — another host emits the same canonical
   Decimal token text directly, however its own JSON writer allows raw
   number injection.

5. **Does this change affect R16 multi-host conformance infrastructure, R17
   arbitrary-precision Integer, R18 equality/map-key, R19 diagnostics, or
   R20 open functions?**
   R17 Integer semantics unchanged (only the existing R9 safe-integer
   interval check is reused, no new literal). R18 equality/map-key
   unchanged. R19: every new rejection (Integer out of range at decode
   already existed; Decimal failing `stable_json_decimal` at encode or
   decode; a decode token that turns out non-finite/malformed) raises
   through the existing `_JsonBoundaryFailure` -> `_json_boundary_err`
   normalization already used by every other JSON boundary rejection —
   reusing the existing `json_number_out_of_range` reason (the closest
   existing member of the already-documented, small, closed reason
   vocabulary at `GENIA_STATE.md`'s JSON section) rather than inventing a
   new diagnostic channel, per this ticket's explicit instruction. R20
   open functions unaffected.

6. **Is any part of this change host-local-only (Python reference host
   convenience) rather than portable?**
   The `uuid.uuid4().hex` sentinel-substitution mechanism (finding 5) is
   this reference host's own device for working around `json.dumps`'s
   inability to emit an arbitrary-precision raw number token; the
   *portable* requirement is only the final JSON text's exact byte
   content (the canonical Decimal spelling appears as an unquoted JSON
   number), which is what tests pin — not this mechanism.

7. **What new portable evidence must exist for another host to reproduce
   this behavior without reading Python source?**
   `tests/unit/test_r23_json_integer_decimal_boundary.py`: Integer R9-
   boundary accept/reject at decode and encode; `stable_json_decimal`
   unit cases (stable, unstable/excess-precision, overflow, underflow);
   encode round-trips a stable Decimal to its exact canonical text as a
   raw JSON number (never a string, never rounded) and rejects an
   unstable Decimal with a normalized diagnostic; decode of a
   fraction/exponent token produces the exact lexically-parsed Decimal
   (proven via a case where `float(token)`-then-`Decimal(float)` would
   differ from lexical parsing) and rejects an unstable token the same
   way; an integer-form token always decodes to Integer, never Decimal;
   round-trip property tests (encode then decode, exact R18 equality
   against the original); nested-container cases.

## Conclusion

Preflight is complete. The strict/compatibility JSON split (finding 1) is
already established and unambiguous in existing code and GENIA_STATE.md
wording, so this slice's boundary is precisely `_json_decode`/
`_json_encode` and their private `_strict_json_*` helpers, leaving
`json_parse`/`json_stringify` (E23-5) and Rational/Float64 JSON policy
(E23-4, finding 3) exactly as found. `stable_json_decimal` is new
(finding 4, confirmed absent by grep) and is implemented as one reusable
`numeric_runtime.py` predicate rather than inline JSON code, called once
each from decode and encode. The one non-obvious implementation detail —
injecting a raw arbitrary-precision JSON number token past `json.dumps`
(finding 5) — is a private, documented reference-host mechanism with no
portable-semantics leakage. Proceeding directly against the already-
approved R23 contract (§4.1, §4.2, §5, §8) — no new contract-
reconciliation commit needed.
