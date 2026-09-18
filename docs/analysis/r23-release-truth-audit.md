# R23 Release Truth Audit — E23-7 (issue #931)

Status: durable skeptical release-audit evidence for R23 (epic tracked via
issue #931 / E23-7). Not a source-of-truth document; `GENIA_STATE.md`
remains final authority. This audit re-derives R23's obligations
independently from the approved contract and merged `main`, rather than
trusting prior per-slice PR descriptions or `GENIA_STATE.md` prose.

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
