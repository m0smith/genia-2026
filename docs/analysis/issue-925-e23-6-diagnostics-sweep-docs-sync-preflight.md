# Issue #925 Preflight — E23-6 Diagnostics Normalization Sweep + Docs/Release Truth Sync

Status: process artifact for issue #925 (E23-6). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority. This file records the
preflight review required by `docs/process/run-change.md` against the
already-approved
`docs/design/r23-numeric-representation-interchange-contract.md` (§8,
"Error and diagnostic boundary", plus a full re-read of §2-§7), building on
merged E23-1 (issue #911), E23-2 (issue #913), E23-3 (issue #915, PR #918),
E23-4 (issue #921, PR #922), and E23-5 (issue #923, PR #924, latest `main`
commit `ed3e3ef`).

## Scope

Part A: audit every failure path touched or introduced by E23-1 through
E23-5 (`src/genia/numeric_runtime.py`, `src/genia/_format_engine.py`, the
JSON sections of `src/genia/builtins.py`) for raw host-exception-text leaks
across the portable diagnostic boundary (R19's domain), make the
diagnostic-reason judgment call E23-3/E23-4 deferred, and confirm the
`AssertionError` dead-code guard E23-4 added is genuinely unreachable via
every public JSON entry point. Fix any genuine leak/bug found, narrowly,
with failing-test-first discipline.

Part B: synchronize `docs/releases/R23.md` (new), `GENIA_STATE.md`
(consistency pass over 9.32-9.36 plus a new diagnostics-sweep section),
`GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
`docs/ai/LLM_CONTRACT.md`, `docs/strategy/roadmap/r21-r24.md`,
`docs/strategy/release-roadmap.md`, cheatsheet pages, and the composability
matrix per their respective sync rules.

Out of scope: the E23-7 release audit itself; any new numeric semantics or
R22 arithmetic/equality change; marking R23 complete.

## Investigation findings (Part A)

1. **Format-spec `format-error: ...` raise sites (E23-2,
   `src/genia/_format_engine.py`) are already clean.** Every raise in
   `apply_format_spec`/`_require_plain_numeral_text`/
   `_exact_ratio_for_precision` constructs its message from a fixed string
   plus the format spec text or a field name (`spec!r`, `field`) -- never
   `str(exc)` of a caught Python exception, never a bare
   `type(value).__name__`. These raises are plain `ValueError`/`TypeError`
   that reach the evaluator as an ordinary host exception (a *misuse*
   diagnostic, not a data-level Outcome), exactly the same surfacing
   mechanism every pre-existing format-spec error already used before
   E23-2 (confirmed by reading the surrounding non-numeric spec branches,
   e.g. `<>^` alignment, `,` grouping, which predate R23 and use the
   identical `format-error: ...` / raw `ValueError` pattern). This is
   consistent with R19's diagnostic-portability convention documented in
   `GENIA_STATE.md`'s E19-3/E19-4 entries: a misuse-shaped failure
   surfaces as a host exception with a portable, Genia-authored message,
   not a wrapped Python exception's `str()`. No change needed.

2. **Strict JSON `_JsonBoundaryFailure`/`_json_boundary_err` raise sites
   (E23-3/E23-4, `src/genia/builtins.py`) never leak raw exception text.**
   Every `_JsonBoundaryFailure(...)` construction uses a fixed reason
   string plus structured keyword context (`key=`, `value_type=`, `line=`,
   `column=`), never `str(exc)` of a caught Python exception. Confirmed by
   reading every one of the 10 non-pragma raise sites plus the two
   `# pragma: no cover - defensive` unreachable ones.

3. **Diagnostic-reason judgment call (E23-3/E23-4's own deferred
   question), decided by this slice: RATIFY `json_number_out_of_range`'s
   reuse across Integer-range, Decimal/Rational-stability, and
   Float64-non-finite rejections, but add a non-breaking additive `cause`
   context field to disambiguate.** Renaming or splitting the `reason`
   symbol itself would be a genuine behavior change: existing tests
   (`tests/unit/test_r23_json_integer_decimal_boundary.py`,
   `test_r23_json_rational_float64_boundary.py`) and any downstream Genia
   code pattern-matching on `result.reason` depend on the exact symbol
   `json_number_out_of_range`, and the contract's own §8 wording groups
   "generic JSON numeric-domain rejection" and "invalid/non-finite generic
   JSON number cases" without mandating distinct reason strings. Splitting
   the reason string is therefore rejected as out of the "clearer
   diagnostics, not new behavior" boundary the ticket sets. Instead,
   `_JsonBoundaryFailure` already accepts arbitrary keyword context (see
   its `**context: Any` constructor, unchanged), so this slice adds one
   additive `cause` field -- `"integer_out_of_range"`,
   `"decimal_unstable"`, `"rational_unstable"`, `"float_non_finite"`, or
   `"non_finite_constant"` (the `nan`/`Infinity`/`-Infinity` JSON literal
   rejection) -- to every real (non-pragma) `json_number_out_of_range`
   raise site, both encode and decode, strict boundary only. This is a
   pure additive context-map key: existing `str(result.reason) ==
   "json_number_out_of_range"` assertions are untouched (verified: no
   existing test asserts the full context map's exact key set for these
   cases, only the reason symbol), and a diagnostic consumer that wants
   the finer distinction can now read `cause` without any existing
   consumer's pattern match breaking.

4. **Compatibility JSON (E23-5) `none("json-stringify-error", ...)`
   errors: one genuine leak found and fixed.** `json_stringify_fn`'s
   `except (TypeError, ValueError)` handler puts `str(exc)` into the
   returned context's `"message"` field (a pre-existing, R19/E19-4-blessed
   pattern for this specific class-C debugging-detail field -- see
   `GENIA_STATE.md` E19-4's note that `str(exc)` in a handful of
   `builtins.py` Outcome context maps, including this one, was reviewed
   and confirmed incidental class-C detail, not part of the portable
   diagnostic contract). However, the message *content* itself leaked a
   raw Python class name: `_json_from_runtime`'s final fallback raise
   (`src/genia/builtins.py`, extended in scope by E23-5's rewrite of this
   exact function) read
   `f"json_stringify expected a JSON-compatible value, got
   {type(value).__name__}"` -- using Python's own `type(...).__name__`
   instead of the portable `_runtime_type_name(value)` table every sibling
   "expected X, received Y" diagnostic in this file already uses (e.g. the
   equivalent final raise in `_strict_json_from_runtime` two functions
   below it, and `_ensure_zip_entry` above it). This is exactly the class
   of leak E19-3 already normalized elsewhere (see `GENIA_STATE.md`'s
   E19-3 note: "the large 'expected X, received Y' family already renders
   via `_runtime_type_name`"), just missed in this one call this slice's
   own scope now covers because E23-5 rewrote this function's body around
   it. **Fixed**: replaced `type(value).__name__` with
   `_runtime_type_name(value)`.
   Two sibling raises in `numeric_runtime.py` (`_as_decimal`'s
   `f"cannot combine GeniaDecimal with {type(value).__name__}"` and
   `exact`'s `f"exact expected a numeric value, received
   {type(value).__name__}"`) have the identical shape but are confirmed
   by `git blame` to be pure R22 (E22-1/E22-5) arithmetic-misuse code,
   never touched by any E23 slice -- out of this slice's scope (R22
   arithmetic/equality is explicitly frozen by this ticket's non-goals).
   Left unchanged; noted here as a candidate for a future, separately
   scoped R22-diagnostics ticket if one is ever opened.

5. **The E23-4 `AssertionError` dead-code guard in
   `_strict_json_to_runtime`'s `float` branch is confirmed genuinely
   unreachable through every public JSON entry point.** The five bindings
   under `src/genia/builtins.py`'s env setup are `_json_parse`,
   `_json_decode`, `_parse_jsonl_record`, `_json_stringify`, `_json_encode`
   (`json_pretty` is prelude sugar delegating to `json_stringify`, per
   `src/genia/std/prelude/json.genia`). Only `_json_decode` (`json_decode_fn`)
   ever calls `_strict_json_to_runtime`. `json_decode_fn`'s `json.loads`
   call registers `parse_float=_strict_json_decimal` (every fraction/
   exponent token becomes an exact `GeniaDecimal` before a raw Python
   `float` could ever be constructed) and `parse_constant=
   _reject_json_constant` (`nan`/`Infinity`/`-Infinity` tokens raise
   `_JsonBoundaryFailure` immediately, never reaching
   `_strict_json_to_runtime` at all) -- so no host `float` value can ever
   appear in the `parsed` tree `_strict_json_to_runtime` walks. Proof test
   added (`tests/unit/test_r23_e23_6_diagnostics_sweep.py`): fuzzes
   `_json_decode` with a broad set of adversarial fraction/exponent/
   large/small/negative/zero number tokens, plus explicit `NaN`/
   `Infinity`/`-Infinity` literals, and asserts the branch is never
   reached (each call either returns a decoded value or an `err(...)`
   Outcome, never raises `AssertionError`); a second, direct unit test
   calls `_strict_json_to_runtime` with a bare Python `float` argument
   directly (bypassing the public entry point on purpose) and confirms
   the guard *does* fire there, proving the guard's own code is live and
   correctly wired, not simply dead from a typo. No bug found; the
   guard is confirmed sound as documented.

6. **Bare `except Exception`/swallow-and-rethrow sweep.** `grep -rn
   "except.*:" src/genia/numeric_runtime.py src/genia/_format_engine.py`
   and a manual read of every `except` clause in the JSON sections of
   `src/genia/builtins.py` touched by E23-3/E23-4/E23-5 found zero bare
   `except Exception` and zero swallow-and-rethrow-with-leaked-internals
   pattern. `numeric_runtime.py`/`_format_engine.py` contain no `except`
   clause at all in the E23-1/E23-2 code (both are pure computation with
   no I/O to catch failures from). The JSON boundary's `except` clauses
   are all narrowly typed (`json.JSONDecodeError`, `_JsonBoundaryFailure`,
   `RecursionError`, `UnicodeDecodeError`, `(TypeError, ValueError)`), each
   converting to a structured, reason-coded Outcome/`none(...)`/`err(...)`
   context, never re-raising the caught exception's raw text unmodified.

## Decisions ratified without code change

- Format-spec diagnostics (finding 1): already sound, no change.
- Strict JSON boundary structure (finding 2): already sound, no change.
- `json_number_out_of_range` reason-string reuse (finding 3): ratified as
  sufficient at the `reason` level; refined additively via a new `cause`
  context field (see implementation commit).
- `AssertionError` guard (finding 5): confirmed correctly unreachable via
  every public path; proof tests added, no runtime-code change to the
  guard itself.
- R22 `type(value).__name__` sites in `numeric_runtime.py` (finding 4):
  confirmed out of E23-1..E23-5 scope; deliberately left unchanged.

## Decision requiring a narrow code change

- `_json_from_runtime`'s final fallback `TypeError` (finding 4): fixed to
  use `_runtime_type_name(value)` instead of `type(value).__name__`,
  matching every sibling diagnostic in the same file and R19's existing
  `_runtime_type_name` convention. This is the one genuine, narrowly
  scoped bug this sweep found and fixes.

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?**
   Reference-host (Python) JSON boundary diagnostics only:
   `_json_from_runtime`'s unsupported-value `TypeError` message
   (`src/genia/builtins.py`), and additive `cause` context keys on the
   existing `json_number_out_of_range` `_JsonBoundaryFailure` raise sites
   (same file, strict boundary only). No Core IR, lexer/parser,
   `numeric_runtime.py`, or `_format_engine.py` code is modified.

2. **Does this change alter the minimal portable Core IR node family?**
   No. Both changes are diagnostic-text/context-map content only; no
   function signature, no new public Genia-level builtin, no Outcome
   shape change (`none(...)`/`err(...)` construction sites and their
   `reason` symbols are unchanged; only context map contents change,
   additively for `cause`, and the `message` field's text content for the
   compatibility-encode fallback).

3. **Does this change require a host-native binary float at any point in
   the new code path?**
   No. Purely diagnostic-text and context-map changes.

4. **Does this change require another host implementation (Node/Java/
   Rust/Go/C++) to consult Python-specific behavior to reproduce it?**
   No new cross-host obligation. The portable requirement was always that
   the `_runtime_type_name` table (a Genia-authored, host-independent type
   name set) is what appears in a diagnostic, not a host's native type
   name -- this change brings one call site into conformance with a rule
   every other host must already follow. The new `cause` context field is
   an additive, self-descriptive string constant with no host-specific
   meaning.

5. **Does this change affect R16 multi-host conformance infrastructure,
   R17 arbitrary-precision Integer, R18 equality/map-key, R19
   diagnostics, or R20 open functions?**
   This change directly serves R19 diagnostic portability (closing one
   more `_runtime_type_name`-bypass leak, the same class E19-3 already
   fixed elsewhere) without introducing new mechanism. R16/R17/R18/R20
   unaffected -- no new Outcome shape, no new reason symbol, no arithmetic
   or equality change.

6. **Is any part of this change host-local-only (Python reference host
   convenience) rather than portable?**
   No. Both changes make reference-host diagnostic output *more* portable
   (removing a Python-specific class-name leak; adding a portable,
   host-independent `cause` string), not less.

7. **What new portable evidence must exist for another host to reproduce
   this behavior without reading Python source?**
   `tests/unit/test_r23_e23_6_diagnostics_sweep.py`: (a) a direct proof
   that no exception message raised anywhere along the E23-1..E23-5 code
   paths (format-spec misuse, strict JSON encode/decode misuse,
   compatibility JSON encode misuse) contains a raw Python type-name
   fragment (`"GeniaDecimal"`, `"GeniaRational"`, `<class '"`, etc.); (b)
   `json_stringify`'s rejection of an unsupported runtime kind now reports
   the portable type name, not the Python class name; (c) each
   `json_number_out_of_range` scenario (Integer range, Decimal/Rational
   instability, Float64 non-finite, NaN/Infinity JSON literal) carries the
   expected additive `cause` context value, while `reason` stays
   `json_number_out_of_range` for all of them (proving no breaking
   rename); (d) the `AssertionError` guard's confirmed unreachability
   through every public JSON entry point, plus a direct proof the guard
   itself is live code (fires when called out-of-band).

## Conclusion

Preflight is complete. The sweep found the strict JSON boundary and
format-spec diagnostics already sound (no change), ratified the
`json_number_out_of_range` reuse with a non-breaking additive refinement,
confirmed the E23-4 `AssertionError` guard is genuinely unreachable and
correctly wired, and found and fixed one genuine, narrowly-scoped leak in
compatibility JSON's unsupported-value diagnostic. No new numeric
semantics, no R22 change, no Outcome-shape change. Proceeding directly
against the already-approved R23 contract §8 -- no new contract-
reconciliation commit needed.
