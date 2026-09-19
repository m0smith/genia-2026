# R23 Release Truth Audit

Status: durable skeptical release-audit evidence for R23. Not a
source-of-truth document; `GENIA_STATE.md` remains final authority. This
file records **two** independent audit passes, kept in full as an honest
paper trail rather than overwritten:

1. **E23-7 (issue #931, PR #932) — original audit — FAIL.** Found one
   genuine leak (`json_stringify`'s diagnostic exposed the raw Python
   class name `"GeniaRational"`). See "E23-7 original audit" below.
2. **E23-8 (issue #933, PR #934) — repair** for that one finding: added a
   `GeniaRational -> "rational"` branch to `_runtime_type_name`
   (`src/genia/values.py`).
3. **E23-9 (issue #935) — fresh, independent re-audit — see verdict at
   the top of the "Re-audit after E23-8" section below** for the current,
   authoritative verdict. Read that section first; the E23-7 section
   beneath it is retained as historical record only.

## Re-audit after E23-8 (issue #935, E23-9) — verdict: FAIL

Audited commit: `37e66a8e` (`origin/main` tip at re-audit time; merges #934,
includes E23-1 through E23-6 plus the E23-7 audit doc and the E23-8 repair
-- test commit `e03c76bf`, docs commit `ec7d7abf`, fix commit `feda3a7d`).
This is a second, fully independent pass -- not a check that the one known
bug is fixed and a rubber stamp. Every contract section (§2-§11) was
re-derived from source and live-probed again from scratch, plus new
adversarial cases beyond the first audit's list (see below).

### Confirming the E23-8 repair itself

`genia -c 'print(json_stringify(1/3))'` now returns
`received: "rational"`, not `received: "GeniaRational"` -- confirmed live
against the audited commit, and confirmed with several further shapes
(`json_stringify` on a bare Rational, a Rational nested in a List, a
Rational nested in a Map -- all render `"rational"`/`"list"`/`"map"`
cleanly, never a raw Python class name).

`src/genia/values.py`'s `_runtime_type_name` (the one shared helper behind
every "expected X, received Y" diagnostic in the codebase -- confirmed by
grepping every call site across `builtins.py`, `callable.py`,
`configuration.py`, `evaluator.py`, `host_bridge.py`,
`http_annotation_binding.py`, `lifecycle_binding.py`, `lifecycle_plan.py`,
`lifecycle_scope.py`, `model.py`, `retrieval.py`,
`server_config_binding.py`, `server_route_binding.py`, `sheet.py`, and
`test_kernel.py`) now has a `GeniaRational -> "rational"` branch
immediately after `GeniaDecimal -> "decimal"`. Because this is the one
shared helper, the fix is comprehensive across every one of those call
sites, not merely `json_stringify` -- confirmed live for two more
call sites: `sum([1, 1/3])` now says "item 2 received rational" (not
"GeniaRational"), and `rational(1/2, 1)` now says "received rational".

### New adversarial cases tried beyond the first audit

- **Nested Map/List/Outcome across the JSON boundary**:
  `json_encode({items: [1, 1/4, 0.1, float64(1e21)], nested: {r: 1/3}})`,
  `json_encode(some({a: 1/4}))`, `json_encode(none("x", {a: 1/3}))` -- all
  clean, structured `err(...)`/portable `value_type` strings, no raw
  Python text anywhere.
- **Format-spec combined with a real JSON round-trip through Genia
  source** (not a direct Python-level function call): encode a Map with
  Decimal/Rational-equivalent/Integer/Float64 fields, decode it back via
  `json_decode` + `representation_match("json", ...)`, then apply a
  `.n`-precision format spec to the round-tripped Decimal field --
  produced the exact expected `"0.30"` with no error and no leak.
- **REPL-level (not `-c`) numeric echo for all four kinds**: piped
  `1+1`, `0.30000000000000004`, `1/3`, `float64(1e21)` into
  `python -m genia.interpreter`'s interactive loop (confirmed `1+1`
  evaluates to `2`, not merely echoing input, proving these are real
  `_emit_result` renders) -- Integer/Decimal/Rational/Float64 all render
  via the same canonical rules as `-c` mode.
- **Combined misuse in one JSON document**: an out-of-range Integer
  together with an unstable Decimal in the same array/object -- reports
  the first failure deterministically (`cause: integer_out_of_range`) with
  no leak, in both `[...]` and `{...}` shapes.
- **Negative-zero Float64 through JSON**: confirmed `float64(-0.0)`
  written as a *literal* collapses through Decimal's no-negative-zero
  identity to `float64(0.0)` (expected, matches the first audit's own
  documented reasoning for why it used multiplication instead), while a
  genuinely-computed negative zero (`float64(0.0) * float64(-1.0)`)
  correctly round-trips through both `json_encode` and `json_stringify` as
  `-0.0`, sign preserved.
- **Broad grep for every remaining raw-type-name risk**, not just
  `_runtime_type_name` call sites: searched `type(`, `__class__.__name__`,
  and `.__name__` across `numeric_runtime.py`, `_format_engine.py`,
  `builtins.py`'s JSON sections, and `values.py`. Found:
  - Four `type(value).__name__` sites remain in `numeric_runtime.py`:
    `_as_decimal` (line 253), `to_float64` (line 639), `exact` (line 683)
    -- all three already documented in `GENIA_STATE.md` §9.37 as
    pre-existing, out-of-scope, frozen R22 code -- **plus a fourth,
    previously undocumented site: `stable_json_decimal` (line 832),
    introduced in E23-3 (`ea4d993d`), an R23-era commit.** Traced every
    call site of `stable_json_decimal` (`builtins.py` lines 2062, 2161,
    2195): all three always pass an already-`isinstance`-guarded or
    internally-constructed `GeniaDecimal`, so this `TypeError` branch is a
    defensive invariant guard, not reachable through any public Genia
    entry point -- confirmed by direct read, the same class of "dead
    branch" the first audit already proved for `_strict_json_to_runtime`'s
    `AssertionError` guard. Not a bug; noted here because it was not
    previously documented as audited.
  - `values.py`'s `__class__.__name__ == "GeniaSheet"` branch (line 244)
    is unrelated -- a declassification-authority containment walk, not a
    type-name diagnostic.
  - No other numeric-diagnostic leak site found anywhere in the four
    files searched.

### Genuine discrepancy found: `GENIA_STATE.md` does not document E23-8's actual fix

E23-8's docs commit (`ec7d7abf`) edited `GENIA_STATE.md` §9.37, but only
to correct an unrelated count ("two" pre-existing R22
`type(value).__name__` sites -> "three", adding `to_float64`). It did
**not** add any description of E23-8's own primary, headline change --
the `GeniaRational -> "rational"` branch added to `_runtime_type_name` in
`src/genia/values.py` (`feda3a7d`), which is the actual runtime-behavior
fix for the bug E23-7 found. Confirmed by reading all of §9.37 in full:
the bullet titled **"One genuine leak found and fixed"** still describes
only E23-6's `_json_from_runtime` fallback fix; it was not updated (or a
new bullet added) to also describe the second genuine leak that E23-7
found and E23-8 fixed. Searching all of `GENIA_STATE.md` for
`_runtime_type_name` or a `GeniaRational -> "rational"` mention finds
nothing describing this fix anywhere in the document.

This is a real violation of `AGENTS.md`'s own "Non-Negotiable Rule
(CRITICAL)": *"Any change to language behavior, syntax, runtime
semantics, parser rules, or examples MUST also update: `GENIA_STATE.md`
... No exceptions."* `feda3a7d` is exactly such a change -- it alters the
observable diagnostic text `_runtime_type_name` produces for every
`GeniaRational` value across dozens of call sites throughout the codebase
(confirmed above), and `GENIA_STATE.md` -- the project's declared *final
authority* for implemented behavior -- does not narrate that this fix
happened. `GENIA_STATE.md` §9.37 as it stands currently undersells its own
release: it claims (accurately, at the time E23-6 landed) "one genuine
leak found and fixed," but as of the current commit a second, distinct
genuine leak (found by E23-7, fixed by E23-8) exists in the same release
and is not mentioned.

This is a narrow, docs-only gap -- the underlying runtime behavior is
correct, well-tested (`e03c76bf` asserts the exact `received` field
content, not merely the Outcome shape), and this audit found no other
behavioral defect anywhere in the release. But per this repository's own
explicit, "no exceptions" documentation-truth rule, and per this audit's
own instruction to "confirm E23-8's edits are internally consistent," this
is a genuine finding: E23-8's `GENIA_STATE.md` edit is not internally
consistent with E23-8's own code change.

A secondary, much smaller coverage observation (not blocking, noted for
completeness): `tests/unit/test_r23_e23_6_diagnostics_sweep.py`'s generic
`test_no_json_or_format_diagnostic_leaks_python_class_name` sweep -- the
test explicitly designed to catch exactly this class of leak across every
audited failure path -- collects only the `cause`, `value_type`, and
`message` context keys from its probed Outcomes; it never reads the
`received` key, which is the specific field the original bug (and its
fix) live in. The bug now has direct, exact regression coverage via a
dedicated test (`e03c76bf`'s
`test_json_stringify_rejects_non_terminating_rational_received_field_is_portable`),
so this is not a live gap for the known bug, but the *generic* sweep test
would not catch a similar future leak surfacing specifically through a
`received` field. Not required for this audit's verdict; worth a mention
for whoever picks up the recommended repair below.

### Validation battery, run fresh to completion at the re-audit commit

```
$ uv run ruff check .
All checks passed!

$ uv run pytest -n auto -q -m "not loopback"
4684 passed in 313.79s (0:05:13)

$ uv run pytest -n auto -q -m loopback
26 passed in 3.12s

$ uv run python -m tools.spec_runner
Summary: total=740 passed=740 failed=0 invalid=0

$ uv run python tools/gen_function_docs.py --check
Function reference is up to date.

$ uv run python tools/stage_docs_for_mkdocs.py && uv run mkdocs build --strict
Documentation built in 5.52 seconds

$ uv run pytest tests/doc/test_semantic_doc_sync.py tests/doc/test_roadmap_split.py tests/doc/test_composability_matrix_sync.py -q
116 passed in 0.29s
```

Every command ran to actual completion, not estimated. The
non-loopback-partition count (4684) is two higher than the first audit's
4682, consistent with the one new test function E23-8 added
(`e03c76bf`) plus incidental test additions from an unrelated,
already-merged PR (#929, Ollama/Groq chat example) in the commit range
between the two audits.

### Documentation truth check (fresh)

- `GENIA_STATE.md` §9.32-9.37: every behavioral sentence independently
  re-verified against current code and live probes; the one gap is the
  narrative-completeness issue described above (E23-8's own fix not
  narrated), not a false behavioral claim.
- `docs/releases/R23.md`: still accurately says "In progress -- E23-1
  through E23-6 complete; E23-7 release truth audit pending," correctly
  not claiming completion (E23-7's FAIL and E23-8's repair are not yet
  reflected, which is correct given R23 is still not complete).
- `docs/strategy/roadmap/r21-r24.md`, `docs/strategy/release-roadmap.md`:
  both still correctly say "In progress" / "E23-7 audit pending" --
  consistent with R23 not yet being complete.
- `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`: their R23-related
  sentences (safe-integer/`stable_json_decimal` boundary, compatibility
  JSON lexical-decode/encode behavior) re-checked against current code --
  all accurate, none overclaims.
- `docs/ai/LLM_CONTRACT.md`: no R23-specific content; nothing to check.

Because a genuine discrepancy was found, per this audit's own mandate, no
completion-marking documentation is touched in this branch:
`docs/releases/R23.md`, the roadmap docs, and `AGENTS.md`'s Product
Priority section are left exactly as found.

### Verdict: FAIL

One genuine discrepancy was found and independently confirmed: E23-8's own
`GENIA_STATE.md` edit does not document E23-8's own primary fix (the
`GeniaRational -> "rational"` branch added to `_runtime_type_name` in
`src/genia/values.py`) -- it edits an adjacent, unrelated sentence in the
same section instead. This is a real violation of `AGENTS.md`'s
"Non-Negotiable Rule (CRITICAL)" that any runtime-behavior change must
update `GENIA_STATE.md`, and it leaves `GENIA_STATE.md` §9.37 -- the
project's own final authority -- describing this release's diagnostics
story incompletely (it says "one genuine leak found and fixed" when two
now exist in this release's actual history).

Everything else audited in this fresh, independent pass holds cleanly:

- Every contract section §2 through §11 was independently re-derived and
  live-probed again from scratch (not merely re-checking the one known
  bug), including new adversarial cases beyond the first audit's list
  (nested-container JSON round-trips, format-spec-over-JSON-round-trip,
  REPL-level echo for all four numeric kinds, combined-misuse diagnostics,
  and a broad fresh grep for any sibling raw-type-name leak).
  Nothing else was found wrong.
- The corrected R22 spec fixture
  (`spec/eval/r22-mixed-exact-float64-rejected.yaml`) was independently
  re-verified: its updated expected output (`"rational"`, not
  `"GeniaRational"`) matches live execution of the exact same source
  through the CLI, byte for byte.
- The full validation battery (ruff, both pytest partitions, spec runner,
  doc-generation check, mkdocs strict build, and the three targeted
  doc-sync suites) is 100% green at the re-audited commit, run fresh to
  completion.
- A fourth, previously-undocumented defensive `type(value).__name__` site
  (`stable_json_decimal`, R23-era) was found and confirmed genuinely
  unreachable from any public Genia entry point -- not a bug.

This FAIL means:

- R23 is **not** marked complete by this audit. `docs/releases/R23.md`,
  the roadmap docs, and `AGENTS.md`'s Product Priority section are left
  unchanged.
- A narrow, documentation-only repair is recommended (not filed by this
  audit): add a bullet to `GENIA_STATE.md` §9.37 (or a short new
  subsection) describing E23-8's actual fix -- the `GeniaRational ->
  "rational"` branch added to `_runtime_type_name` in `src/genia/values.py`
  (commit `feda3a7d`, test commit `e03c76bf`), found by the E23-7 audit
  and repaired by E23-8 (issue #933) -- distinguishing it clearly from the
  adjacent, already-correct "two/three pre-existing sites" bullet, which
  describes different, deliberately-unfixed code. No runtime-code change
  is needed; the underlying fix is already correct and tested. Optionally,
  also add the `received` context key to
  `test_no_json_or_format_diagnostic_leaks_python_class_name`'s probed-key
  list in `tests/unit/test_r23_e23_6_diagnostics_sweep.py` so the generic
  sweep would catch a similar future leak in that field, though this is
  not required to resolve the blocking finding.

## E23-7 original audit

Audited commit: `9953f81ee355a1786857e846522979e18fd6f843` (merged #930,
`origin/main` tip at audit time; includes E23-1 through E23-6, PRs
#912, #914, #918, #922, #924, #930).

## Re-read sources

`AGENTS.md`; `GENIA_STATE.md` sections 9.32–9.37; `GENIA_RULES.md`;
`GENIA_REPL_README.md`; `README.md`; `docs/ai/LLM_CONTRACT.md`;
`docs/design/r23-numeric-representation-interchange-contract.md` (the
approved contract, re-read in full); `docs/releases/R23.md`;
`docs/strategy/roadmap/r21-r24.md`; `docs/strategy/release-roadmap.md`;
`docs/analysis/r21-release-truth-audit.md` and
`docs/analysis/r22-release-truth-audit.md` (rigor/format templates); the
source files implementing R23 directly (`src/genia/numeric_runtime.py`,
`src/genia/_format_engine.py`, `src/genia/builtins.py`'s JSON boundary
functions, `src/genia/utf8.py`, `src/genia/values.py`); shared evidence
(`tests/unit/test_r23_*.py`,
`spec/eval/json-representation-number-boundaries.yaml`).

## Independent re-derivation, section by section

### §2.1 Integer

Unchanged; Python's `str(int)` still governs. No dedicated code, none
needed. Confirmed no code change touches Integer rendering anywhere in
the R23 commit range.

### §2.2 Decimal

`_canonical_decimal_text` (`numeric_runtime.py:82`) implements the fixed/
scientific boundary literally: `adjusted_exponent = len(digits) +
exponent - 1`, fixed when `-6 <= adjusted_exponent <= 20`. Live-probed the
exact boundary with real Genia source (not just unit tests written by the
same author as the implementation):

```
1e20   -> 100000000000000000000.0   (adjusted_exponent = 20, fixed)
1e21   -> 1.0e+21                    (adjusted_exponent = 21, scientific)
1e-6   -> 0.000001                   (adjusted_exponent = -6, fixed)
1e-7   -> 1.0e-7                     (adjusted_exponent = -7, scientific)
500.0  -> 500.0                      (integral Decimal keeps .0)
```

All four boundary probes land exactly where the contract requires, one
step past each side confirmed switching correctly. `GeniaDecimal` has no
negative-zero identity (`_canonicalize` collapses any zero to `(0, 0)`) —
confirmed by decoding `-0.0` through strict JSON and observing it render
as plain `0.0`, matching contract §2.2's silence on negative Decimal zero
(only Float64 gets a signed-zero atom, correctly, per §2.4).

### §2.3 Rational

`GeniaRational.__repr__`/`__str__` render `<numerator>/<denominator>` with
no spaces; confirmed unchanged (E23-1 only retired the "pending R23"
comment). Live-probed `display(1/3)` -> `1/3`.

### §2.4 Float64

`format_float64` (`numeric_runtime.py:788`) matches the contract exactly:
NaN/inf handled before the finite path, signed zero handled explicitly
via `math.copysign`, and the finite path reuses CPython's own
correctly-rounded `repr(float)` parsed through `decimal.Decimal(...)
.as_tuple()` — the shortest round-trip spelling under round-to-nearest/
ties-to-even, matching the contract's algorithm precisely, not
approximated. Live-probed:

```
float64(0.1)   -> float64(0.1)
float64(1e21)  -> float64(1.0e+21)
float64(1e-7)  -> float64(1.0e-7)
float64(0.0)   -> float64(0.0)
float64(-0.0)  -> float64(-0.0)   (confirmed via 0.0 * a negative operand)
```

**Wrapper-usage boundary confirmed both directions.** The `float64(...)`
constructor atom is used everywhere display/debug renders a Float64
(`format_display`/`format_debug` in `utf8.py`, both explicitly routing
`float` through `format_float64`, confirmed by direct read) and is
confirmed **absent** from JSON output: `json_encode(float64(0.1))` emits
the bare JSON number `0.1`, not `float64(0.1)`, and `json_encode(float64
(1e21))` emits bare `1.0e+21` — the `float64(...)` wrapper never leaks
into JSON, matching contract §4.4 ("finite Float64 values are JSON-number
encodable using their canonical shortest-roundtrip decimal spelling",
i.e. the unwrapped digits only).

### §3 Rendering surfaces

Confirmed `utf8.py`'s `format_display`/`format_debug` is the one generic
dispatch every REPL/CLI final-value echo and JSON/error-context rendering
funnels through (direct read plus every probe above going through
`print`/CLI echo, which use exactly this path). No fallback to a host
dataclass repr was found anywhere in this audit's probing.

### §4.1 Integer JSON bounds

Live-probed the exact boundary both directions, encode and decode:

```
json_encode(9007199254740991)   -> some(9007199254740991, ...)
json_encode(9007199254740992)   -> err(json_number_out_of_range, {..., cause: integer_out_of_range})
json_encode(-9007199254740991)  -> some(-9007199254740991, ...)
json_encode(-9007199254740992)  -> err(json_number_out_of_range, {..., cause: integer_out_of_range})
json_decode("9007199254740991")  -> some(...)
json_decode("9007199254740992")  -> err(json_number_out_of_range, {..., cause: integer_out_of_range})
json_decode("-9007199254740991") -> some(...)
json_decode("-9007199254740992") -> err(json_number_out_of_range, {..., cause: integer_out_of_range})
```

Also confirmed the bound applies inside a nested container, not only at
the top level: `json_decode("[9007199254740992]")` rejects with the same
`integer_out_of_range` cause.

### §4.2 `stable_json_decimal`

Read `stable_json_decimal` (`numeric_runtime.py:805`) in full: converts
via native arbitrary-precision `int/int` true division (the same
correctly-rounded path `to_float64` uses), rejects overflow-to-infinity
and nonzero-underflow-to-zero as `False`, then compares canonical
`(coefficient, exponent)` tuples directly — valid because `GeniaDecimal`
is always already canonical on construction, so tuple equality is exactly
"mathematically equal" per the algorithm's steps 3–5. Live-probed the
predicate's effect end to end:

```
json_encode(0.1)                         -> some(0.1, ...)          (stable, accepted)
json_encode(0.1000000000000000000001)    -> err(..., decimal_unstable)  (unstable, rejected)
json_decode("1e-400")                    -> err(..., decimal_unstable)  (nonzero underflow to 0.0, rejected)
json_decode("1e400")                     -> err(..., decimal_unstable)  (overflow to infinity, rejected)
json_decode("0.30000000000000004")       -> decodes to exact GeniaDecimal `0.30000000000000004`, all digits preserved
```

The last probe is the sharpest possible check that decode never
transits host float first: `0.30000000000000004` decoded to the *exact*
18-significant-digit Decimal, not the binary64-rounded `0.3` a
float-first parse would silently produce.

### §4.3 Rational

`rational_terminating_decimal` (`numeric_runtime.py:850`) computes the
2/5-only-denominator termination test via integer trial division only —
confirmed by direct read, no `float(...)` cast anywhere in the function.
Live-probed:

```
json_encode(1/4)  -> some(0.25, ...)                                    (terminating, accepted)
json_encode(1/3)  -> err(unsupported_json_value, {..., value_type: rational})  (non-terminating, rejected — not rounded)
```

### §4.4 Float64

Covered above (§2.4 wrapper-boundary probes); NaN/infinity rejection
confirmed via the strict-encode `float_non_finite` cause path (unit
tests `test_r23_json_rational_float64_boundary.py`, independently
re-read, not merely trusted).

### §5 Generic JSON decode

Every fraction/exponent decode probe above (`0.30000000000000004`,
`1e-7`, `1e21`, boundary cases) produced an exact `GeniaDecimal`, never a
raw Python `float`. Adversarially probed every public JSON entry point
with non-finite spellings and malformed numeric tokens:

```
json_decode("NaN")       -> err(..., non_finite_constant)
json_decode("Infinity")  -> err(..., non_finite_constant)
json_decode("-Infinity") -> err(..., non_finite_constant)
```

Confirmed via direct source read that `_strict_json_to_runtime`'s dead
`float` branch is guarded by an `AssertionError` and is genuinely
unreachable (E23-3's scanner hooks `parse_float`/`parse_constant`
intercept every number/constant token before `json.loads` could ever
construct a raw Python `float`) — re-confirmed by the same class of fuzz
probing `tests/unit/test_r23_e23_6_diagnostics_sweep.py` already performs
(re-ran that file fresh, see below).

### §6 Compatibility JSON surfaces

Confirmed the decode-permissive / encode-extended design is genuinely
implemented, not merely documented:

```
json_parse("0.30000000000000004")  -> decodes to exact GeniaDecimal (permissive: this value fails strict json_decode's
                                       stability gate but still decodes here, per contract's "not require rejecting
                                       an unstable value" reading)
json_stringify(0.1)                -> "0.1"
json_stringify(1/4)                -> "0.25"
json_stringify(float64(1e21))      -> "1.0e+21"
```

`_parse_json_decimal_token` is confirmed the single shared lexical parser
behind both `_strict_json_decimal` (strict) and `_compat_json_decimal`
(compatibility) — direct source read confirms one function, two callers
with different strictness, matching contract §6's "reuse common lexical
... machinery" instruction literally, not just in spirit.

**Discrepancy found here — see "Genuine discrepancy" section below.**
`json_stringify`'s failure-context `received` field leaks the raw Python
implementation class name `"GeniaRational"` for the single most
predictable failure case this slice introduces: `json_stringify` on a
bare non-terminating Rational.

### §7 Format-spec

Re-derived the E23-2 `.n` half-up bug fix with a case specifically chosen
because naive float-based rounding disagrees with exact rounding:

```
format("{n:.2}", {n: float64(2.675)})  -> 2.67   (exact dyadic bits of the IEEE-754 double nearest 2.675 round down)
format("{n:.2}", {n: 2.675})           -> 2.68   (exact Decimal literal 2675e-3 rounds up, half-up, at the boundary digit)
format("{n:.2}", {n: 1/3})             -> 0.33   (exact Rational ratio rounded half-up)
```

The Float64/Decimal disagreement on the identical textual spelling
`2.675` is exactly the regression E23-2's PR claims to have fixed (a
naive `Decimal(repr(value))`-based path would have wrongly produced
`2.68` for the float64 case too, since CPython's shortest-round-trip text
for that float is `"2.675"`, not the float's true dyadic value). Live
probe confirms the fix holds at the audited commit, not merely at the
time E23-2 merged.

Grouping/zero-pad gating re-probed directly:

```
format("{n:,}", {n: float64(1234.5)})  -> raises "format-error: format spec ',' is not supported for this numeric representation"
```

This is the exact bug E23-2's own notes describe (`"flo,at6,4(1,234.5)"`
mangled output before the fix) — confirmed it now raises cleanly instead
of corrupting the wrapper text.

### §8 Error and diagnostic boundary

Re-ran the diagnostics-cleanliness sweep's own test file fresh (not
trusted from the prior slice's report — see validation battery below),
and independently probed beyond it. **This is where the one genuine
discrepancy in this audit was found** — see below.

Confirmed the `cause` context field for every `json_number_out_of_range`
scenario probed above (`integer_out_of_range`, `decimal_unstable`,
`non_finite_constant`, `rational_unstable` per source read) and confirmed
`reason` stays the single stable symbol across all of them, matching
E23-6's design.

### §9 Compatibility

R21/R22 regression suites (`test_r21_*`, `test_r22_*`) run as part of the
full battery below — all pass, no separate partial run needed since the
full suite includes them. No dedicated `test_r17_*`/`test_r18_*` module
prefix exists for pure R17 Integer semantics (R17 predates the current
per-release test-file naming convention and its coverage lives in the
general Integer/arithmetic test files), so R17 compatibility is verified
via the full regression run rather than a named partition; R18 is covered
by `test_r18_*` (3 files), R20 by `test_r20_open_functions_cross_module.py`
— all pass. Confirmed via direct source diff-reading that R23's own
commits (E23-1 through E23-6) touch only `numeric_runtime.py`,
`_format_engine.py`, `builtins.py`'s JSON functions, and `utf8.py`'s
`float` rendering branch — no diff to `evaluator.py`'s arithmetic dispatch,
`equality.py`, or `pattern_match.py` in the entire R23 commit range
(confirmed by `git log --oneline -L` on the relevant functions showing no
R23-era touch).

### §10 Non-goals

No JSON dialect change (still standard `json.loads`/`json.dumps` with
scanner hooks), no Rational literal syntax (`rational_from_integers`
remains an ordinary function call — confirmed no lexer/parser diff in the
R23 commit range), no Float64 suffix/raw-bit syntax, no locale-sensitive
formatting (format-spec code has no locale import), no new general
formatting language (the same `{field:spec}` template syntax, unchanged
grammar), no C++ host work (this repository only). All confirmed by
direct source read, not merely absence of a claim in the docs.

## Genuine discrepancy found

**`json_stringify`'s failure diagnostic leaks the raw Python
implementation class name `"GeniaRational"` for its own headline new
rejection case.**

Reproduced directly against the audited commit:

```
$ genia -c 'print(json_stringify(1/3))'
none("json-stringify-error", {source: "json_stringify", message: "json_stringify cannot represent a non-terminating rational as a JSON number", received: "GeniaRational"})
```

Root cause (`src/genia/builtins.py`, `json_stringify_fn`, around line
5043-5050):

```python
except (TypeError, ValueError) as exc:
    context = (
        GeniaMap()
        .put("source", "json_stringify")
        .put("message", str(exc))
        .put("received", _runtime_type_name(value))
    )
    return make_none("json-stringify-error", context)
```

This *does* call the portable `_runtime_type_name` helper (not a raw
`type(value).__name__` at this call site), but `_runtime_type_name`
itself (`src/genia/values.py:14`) has a branch for `GeniaDecimal` ->
`"decimal"` (added by E22-1) but **no branch for `GeniaRational`**
anywhere in its `isinstance`/class-name table (confirmed by direct read
of the full function body, lines 14–83). A `GeniaRational` value
therefore falls through every explicit branch and reaches the function's
final `return type(value).__name__` fallback, which is the raw CPython
class name `GeniaRational` — exactly the class of leak contract §8
prohibits ("Raw Python/... exception text must not cross portable
boundaries") and exactly the class of leak E19-3/E23-6's own diagnostics
sweep exists to close.

This is materially different from the two items E23-6's own PR (#930)
flagged as open and out of scope, and is **not** covered by the same
"pre-existing, pure-R22, untouched-by-R23" reasoning that applies to
those two items (see next section for that comparison):

- It is triggered through `json_stringify`, a function E23-5 (#923)
  directly modified in this exact release to add Rational/Decimal/Float64
  support, and whose non-terminating-Rational rejection is a headline,
  explicitly documented new R23 behavior (`GENIA_STATE.md` §9.36: "a
  non-terminating `GeniaRational`... remain[s] rejected").
- It is the *first* thing a user seforms when they hit the single most
  predictable failure mode this slice introduces — calling
  `json_stringify` directly on a non-terminating Rational, no nested
  container needed.
- E23-6's own PR explicitly claims (`GENIA_STATE.md` §9.37): "**One
  genuine leak found and fixed: compatibility `json_stringify`'s
  unsupported-value diagnostic.**" That fix (confirmed by direct read)
  corrected a *different*, deeper `_json_from_runtime` fallback branch
  (reached when a nested/unrecognized value type is encountered while
  walking a container) to use `_runtime_type_name` instead of a raw
  `type(value).__name__` call at that inner site. The outer
  `json_stringify_fn` except-handler already called `_runtime_type_name`
  before E23-6 (confirmed via `git log -L` — this call site is
  byte-for-byte unchanged since commit `9e9e0614`, predating R23
  entirely), so E23-6's sweep — which searched for raw
  `type(...).__name__` call sites — never found this one, because the
  bug is one level removed: the call site itself is already "correct"
  (calls the portable helper), but the portable helper's own type table
  is incomplete for a type (`GeniaRational`) that did not exist when this
  call site was written and was never added when R22 introduced
  `GeniaRational` or when R23's E23-4/E23-5 built substantial new
  Rational-JSON behavior on top of it.
- Confirmed **not** caught by the existing test suite:
  `test_json_stringify_rejects_non_terminating_rational` in
  `tests/unit/test_r23_compatibility_json_reconciliation.py` asserts only
  `is_none(result)`, never inspecting the `received` field's content, so
  this leak has zero regression coverage today.
- Confirmed the *sibling* strict `json_encode` path does **not** have
  this problem: `_strict_json_from_runtime`'s `GeniaRational` branch
  raises `_JsonBoundaryFailure("unsupported_json_value",
  value_type="rational")` with a hardcoded string, never routing through
  `_runtime_type_name` at all — so strict JSON encode's Rational
  rejection is clean; only the compatibility surface's generic exception
  handler is affected.

Root fix (not made by this audit, per the audit's own mandate — this
touches `src/genia/*.py` runtime behavior):

Add a `GeniaRational` branch to `_runtime_type_name`
(`src/genia/values.py`), e.g. `if isinstance(value, GeniaRational): return
"rational"`, mirroring the existing `GeniaDecimal -> "decimal"` branch
immediately above it. This is a narrow, one-line-shaped fix, but it is
runtime code, so it is out of this audit's own scope to apply.

## Comparison against E23-6's two acknowledged open items

Per the orchestration brief, E23-6's PR (#930) flagged two known gaps.
Both independently re-verified as genuinely pre-existing and genuinely
out of R23 scope — unlike the discrepancy above:

**(a) Two `type(value).__name__` leak sites in pure R22 arithmetic-misuse
code (`_as_decimal`, `exact`).** Confirmed by `git blame`/`git log -L`:
`_as_decimal` (numeric_runtime.py:253, from E22-1/`b759c469`) and `exact`
(numeric_runtime.py:683, from E22-1/`b759c469`) are both untouched by any
E23 commit. Live-probed both are reachable (`float64("hello")` ->
`"float64 expected a numeric value, received str"`; note: `"str"` here is
coincidentally an acceptable-looking word, not an alarming raw class
name, though still not the project's `_runtime_type_name` vocabulary).
**One correction to `GENIA_STATE.md`'s count**: a third such site exists
at the same vintage, `to_float64` (numeric_runtime.py:639, also from
E22-1/`b759c469`, "float64 expected a numeric value, received
{type(value).__name__}") — `GENIA_STATE.md` §9.37 names only "`_as_decimal`
and `exact`", omitting `to_float64`. All three are genuinely pre-existing,
pure-R22, untouched-by-any-R23-commit code (confirmed by `git log -L` on
each), so the *scoping* judgment ("out of R23's scope, not an R23 gap")
is correct even though the count of two vs. three is imprecise — this is
a minor, non-blocking documentation-precision note, not a behavior defect,
and not itself grounds to withhold a PASS. It is folded into this audit's
verdict as a documentation nit worth a follow-up mention, not a repair
issue.

**(b) `_runtime_type_name`'s generic fallback not covering all types.**
This is real and, per this audit's independent investigation, is the
*same underlying code gap* as the genuine discrepancy above — but the
orchestration brief's framing anticipated it as an abstract "not all
types covered" completeness gap in a shared helper, to be noted and left
for a future ticket. What this audit found is that this gap is not
merely a completeness nicety: it is concretely and reproducibly reachable
through R23's own new `json_stringify` non-terminating-Rational rejection
path — R23's own headline compatibility-JSON behavior — via a call site
(`json_stringify_fn`'s except-handler) that predates R23 but whose
observable failure text is a **new, R23-introduced regression in
practice**: before E23-5 (#923), `json_stringify` did not accept/attempt
`GeniaRational` at all, so this call site's `_runtime_type_name(value)`
branch was never reached for a `GeniaRational` value; E23-5 is what makes
this leak observable for the first time on this repository's history.
Because of that causal link, this audit does **not** extend item (b)'s
"leave for a future ticket" treatment to this specific, now-reachable
instance — see "Genuine discrepancy found" above and the verdict below.

## Shared evidence: validation battery run fresh, to completion

All commands run to completion at the audited commit
(`9953f81e`), on this audit's branch (`issue-931-e23-7-release-truth-audit`,
which is `origin/main` at this commit with no other diff at the time
these commands ran):

```
$ uv run ruff check .
All checks passed!

$ uv run pytest -n auto -q -m "not loopback"
4682 passed in 313.13s (0:05:13)

$ uv run pytest -n auto -q -m loopback
26 passed in 3.14s

$ uv run python -m tools.spec_runner
Summary: total=740 passed=740 failed=0 invalid=0

$ uv run python tools/gen_function_docs.py --check
Function reference is up to date.

$ uv run python tools/stage_docs_for_mkdocs.py
Staged docs for MkDocs in .../.tmp/mkdocs-docs

$ uv run mkdocs build --strict
Documentation built in 5.42 seconds   (exit code 0)

$ uv run pytest tests/doc/test_semantic_doc_sync.py tests/doc/test_roadmap_split.py tests/doc/test_composability_matrix_sync.py -q
116 passed in 0.27s
```

Every command ran to actual completion (the full-regression partition was
started in the background and its exact final line, `4682 passed in
313.13s (0:05:13)`, was captured on completion, not estimated or assumed).
No command was stopped partway.

## Documentation truth check

- `GENIA_STATE.md` §9.32–9.37: every sentence independently re-verified
  against the current merged code by direct source read and live
  probing above, with one precision nit noted (the "two" vs. three
  `type(value).__name__` sites in pure-R22 code, §9.37) — not a behavior
  claim, a count.
- `docs/releases/R23.md`: describes E23-1 through E23-6 accurately against
  the code; correctly states "E23-7 audit pending" (this audit).
- `docs/strategy/roadmap/r21-r24.md`, `docs/strategy/release-roadmap.md`:
  both describe R23 as in-progress (E23-1 through E23-6 merged, E23-7
  pending), consistent with the audited state — neither prematurely
  claims R23 complete.
- `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
  `docs/ai/LLM_CONTRACT.md`: read for consistency; none makes an R23
  claim that contradicts the code or `GENIA_STATE.md`.

Per this audit's own mandate, because a genuine discrepancy was found,
**no completion-marking documentation changes are made in this branch.**
`docs/releases/R23.md`, `docs/strategy/roadmap/r21-r24.md`,
`docs/strategy/release-roadmap.md`, and `AGENTS.md`'s Product Priority
section are left exactly as found — none of them are updated to claim R23
COMPLETE.

## Verdict

**FAIL.**

One genuine discrepancy between the approved R23 contract and actual
merged behavior was found and independently confirmed by direct source
read and live reproduction: `json_stringify`'s failure diagnostic leaks
the raw Python implementation class name `"GeniaRational"` (via
`_runtime_type_name`'s incomplete type table) for the single most
predictable failure case E23-5 introduces — calling `json_stringify`
directly on a non-terminating Rational. This is a real contract §8
("Raw Python/... exception text must not cross portable boundaries")
violation, is genuinely reachable from ordinary Genia source with no
adversarial construction required, is not covered by any existing test's
assertions, and is a *new-in-practice* regression surface specifically
because E23-5 is what made this previously-unreachable `_runtime_type_name`
gap observable for `GeniaRational` for the first time.

Everything else audited in this pass holds:

- Every contract section §2 through §10 was independently re-derived from
  source and live-probed (not merely read/trusted), and matches the
  contract precisely, including the exact fixed/scientific and JSON
  Integer boundary cases, the `.n` half-up rounding regression fix, the
  compatibility-JSON permissiveness design, and every non-goal.
- The full validation battery (ruff, both pytest partitions, spec runner,
  doc-generation check, mkdocs strict build, and the three targeted
  doc-sync suites) is 100% green at the audited commit, run fresh to
  completion.
- The two items E23-6's own PR flagged as open were independently
  re-verified: item (a) is confirmed genuinely pre-existing/out-of-scope
  (with a minor count-precision nit, non-blocking); item (b) is where
  this audit's one blocking finding lives — its scoping as a
  "leave for later" completeness gap does not hold for this specific,
  R23-reachable instance.

Per issue #931's acceptance criteria and this audit's own instructions,
this FAIL means:

- R23 is **not** marked complete by this audit. `docs/releases/R23.md`,
  the roadmap docs, and `AGENTS.md`'s Product Priority section are left
  unchanged.
- A narrow repair issue is recommended (not filed by this audit): add a
  `GeniaRational -> "rational"` branch to `_runtime_type_name`
  (`src/genia/values.py`), immediately alongside the existing
  `GeniaDecimal -> "decimal"` branch, following the same
  contract/design/failing-test/implementation/docs discipline as
  E23-1 through E23-6. The failing test should assert on the `received`
  field's exact string content for `json_stringify(1/3)` (currently
  untested), not merely on the Outcome shape. The repair should also
  correct `GENIA_STATE.md` §9.37's "two" pre-existing-leak-site count to
  three (including `to_float64`) as a documentation nit in the same
  change, since it touches the same paragraph.
