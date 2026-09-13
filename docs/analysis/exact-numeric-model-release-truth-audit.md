# Exact Numeric Model Skeptical Release Truth Audit (issue #838 Step 7)

Status: **NO-GO for R21 semantic implementation.** This is contract section
21's ("Implementation acceptance") required skeptical audit for the
separately-gated `docs/design/exact-numeric-model-contract.md`. It assumes
the implementation is wrong until proven correct, re-derives claims from the
actual code and a fresh full test/spec run on this branch, and states an
explicit go/no-go for R21 per `docs/design/r21-cpp-host-preflight.md`.

This audit finds the six landed slices (N-1, Steps 2-6) to be internally
correct, well-tested, and honestly documented. It finds the contract's own
section 21 acceptance bar is **not yet met**, for reasons already flagged
(not newly discovered) by Step 6's own agent and confirmed here by direct
testing rather than by trusting that flag. One real bug was found and fixed
during this audit (a line-length/formatting nit, not a semantic defect).

## 1. What was re-verified, and how

Branch `issue-838-exact-numeric-gate` at `4eb5c5c7` (Step 6's head) going
into this audit. Re-run fresh, in this session:

- Targeted numeric unit/spec tests: `tests/unit/test_numeric_arithmetic.py`,
  `test_numeric_comparison_evaluator_wiring.py`, `test_numeric_conversions.py`,
  `test_numeric_equality_comparison.py`, `test_numeric_rendering_and_boundaries.py`,
  `test_numeric_values.py`, `test_r18_structural_numeric_equality_791.py`,
  `tests/spec/test_exact_numeric_conversion_builtins_838.py`,
  `tests/spec/test_exact_numeric_equality_comparison_838.py` — **225/225
  passed**.
- `python -m tools.spec_runner` (in-process default adapter): **720/720
  passed**.
- `python -m tools.spec_runner --host 'python3 -m hosts.python.protocol_adapter'`
  (subprocess E16-1 protocol path, same Python reference host, different
  transport): **702 passed / 18 unsupported / 0 failed**, where the 18
  unsupported cases are the pre-existing, numeric-unrelated
  model-fixture/debug-stdio cases the protocol adapter cannot express yet
  (documented reason, unchanged by this issue). Zero divergence between the
  two paths on any numeric case — this is in-process/subprocess parity for
  the Python reference host, **not** independent second-host conformance
  (see §4).
- Full repository suite: `uv run pytest -n auto -q -m "not loopback"` ->
  **4503 passed, 2 failed** (`tests/unit/test_native_test_runner.py::TestNativeTestRunnerFileHandling::test_file_not_readable`
  and `::TestNativeTestRunnerExitCodes::test_exit_2_file_not_readable`), both
  the same pre-existing root-sandbox `chmod(0)` environment artifact
  documented before R14 and every release since — re-confirmed unrelated to
  numerics by reading the failing assertions (`chmod(0)` does not restrict
  root, so the test's own precondition does not hold in this sandbox).
  `uv run pytest -n auto -q -m loopback` -> **26 passed**.
- `uv run ruff check .` -> clean.
- `uv run pytest tests/doc/` -> **206/206 passed** (semantic-doc-sync
  guardrails, including `test_semantic_doc_sync.py`).

## 2. Skeptical code audit (Part A of the Step 7 charge)

Each item below was checked against the actual code and, where practical,
against running Genia source through `uv run genia`, not against prior
agents' summaries.

- **Python-number assumptions.** Grepped every `isinstance(x, (int, float))`-
  shaped check in `src/genia/*.py`. Outside `numeric_values.py`/`equality.py`/
  `evaluator.py`/`_format_engine.py` (all reviewed below), every remaining
  occurrence is in unrelated domains (R10/R11/R12 timeout/retry/dims
  validation, sheet cell typing, `debug_controller`) that never receive a
  Decimal/Rational/Float64 value and are out of this contract's scope; none
  silently mis-treats a new numeric kind as a legacy one.
- **Optimizer.** `src/genia/optimizer.py`'s `optimize_nth_style_recursion`
  matches literal patterns as `{"kind": "integer", "digits": "0"}` /
  `"1"` — the N-1 tagged Core IR shape, not a raw literal — confirming the
  N-1 fix is real and that no other optimizer code path pattern-matches
  numeric literals in the pre-N-1 untagged shape.
  `tests/unit/test_optimizer.py`'s one changed assertion
  (`result[0].expr.value == {"kind": "integer", "digits": "42"}`) is a
  correct migration, not a stale legacy-shape assertion papering over a
  regression.
- **Equality drift.** Read `src/genia/equality.py`'s numeric dispatch in
  full and exercised it live: `exact(1) == 1`, `exact(1) == rational(2,2)`,
  `1 == rational(2,2)`, `float64(1) == exact(1)`, `float64(0) == 0` all
  `true`; a legacy-float NaN and a Float64 NaN both remain non-reflexive;
  booleans are excluded before any numeric branch. Matches contract 10.1/10.2
  exactly.
- **Map-key drift.** `canonical_map_key` in `equality.py` collapses
  Decimal/Rational/Integer to one `("num", n)` or `("exact-ratio", n, d)`
  identity by exact mathematical value, and gives Float64 its own
  `("float64-inf", ...)` tag for infinities specifically so it never
  collides with a legacy-float infinity key — read and confirmed consistent
  with contract 10.3 and the module's own documented legacy-float boundary
  (see next item).
- **Decimal context/precision independence.** Confirmed by reading
  `numeric_values.py`'s `Decimal` dataclass: it stores a plain
  `(coefficient: int, exponent: int)` pair and every arithmetic operation
  (`add`/`subtract`/`multiply`/`divide`/`remainder`) computes on Python
  arbitrary-precision `int`s directly. `decimal.Decimal` is used exactly
  once, in `to_py_decimal`, an unused-by-arithmetic convenience method with
  its own docstring calling it "a host implementation tool" — arithmetic
  never touches Python's global `decimal.Context`/precision. Confirmed: no
  context dependence exists.
- **Accidental rounding / float() casts.** Grepped `float(` across
  `numeric_values.py` and `_format_engine.py`: every occurrence is either
  `float("inf")`/`float("-inf")` (sentinel construction, not a cast) or the
  return-type annotation of `_decimal_to_correctly_rounded_float`. No
  arithmetic path casts an exact value through a Python `float` unless the
  caller explicitly asked for Float64 (`construct_float64`,
  `_decimal_to_correctly_rounded_float`, both float-name-honest about it).
- **Fraction leakage.** `to_fraction`/`numeric_extended_value` return
  `fractions.Fraction` only as an internal comparison/precision-arithmetic
  intermediate; every public rendering path (`render_decimal`,
  `render_rational`, `render_float64`) builds its own text and never calls
  `repr(Fraction(...))` or lets one escape through `print`/`json_encode`/
  error messages. Confirmed by both code reading and live `print`/
  `debug_repr` probes.
- **Implicit Float64 mixing.** `_reject_float64_mix` is called at the top of
  `add`, `subtract`, `multiply`, `divide`, and `remainder` uniformly — every
  binary arithmetic op rejects an exact+Float64 mix with `NumericMisuseError`
  before doing any work. Comparisons (`compare_numeric`) deliberately do
  **not** reject the mix, per contract 10.2's explicit "this bridge applies
  to comparison/equality only" — verified this is the contract's own
  documented split, not an inconsistency.
- **Scientific-notation parsing.** Live-probed `1e10` -> `10000000000.0`,
  `1.5e-3` -> `0.0015`, `1E+5` -> `100000.0` — all correct (these are
  currently legacy-float decimal literals per the still-open literal-bridge
  gap in §3, so they render as host floats, which is the documented current
  behavior, not a bug).
- **Negative zero.** `float64(0) * float64(-1)` produces `float64(-0.0)`
  (correct IEEE-754 sign propagation); `exact(float64(-0.0))` produces
  Decimal `0.0` per the contract's explicit "+0.0/-0.0 -> Decimal zero" rule;
  `float64(-0.0) == float64(0)` is `true`. All confirmed live and match
  contract 6/10.2 exactly. A negative-zero Float64 is reachable only through
  Float64-domain arithmetic, never through `float64(...)` directly (which
  only accepts exact input), which is consistent with the contract.
- **Huge Integer values.** `999999999999999999999999999999 *
  999999999999999999999999999999` produces the exact 60-digit product with
  no truncation (Integer stays plain Python `int`; unaffected by this
  contract's changes, confirmed live).
- **Rational denominator normalization / zero denominator.** Read
  `Rational.__post_init__`: denominator sign is normalized to positive and
  numerator/denominator are divided by their gcd unconditionally.
  `rational(1, 0)` was run live and raises `NumericMisuseError` (surfaced to
  the CLI as `Error: rational denominator must be nonzero`), not a host
  `ZeroDivisionError`.
- **Decimal canonicalization.** `Decimal.__post_init__` strips every
  trailing base-10 zero from the coefficient and folds it into the exponent,
  and collapses zero to the single canonical `(0, 0)` representation
  unconditionally — read and confirmed; this cannot produce two distinct
  internal representations of the same Decimal value.
- **NaN/infinity leaks.** `json_encode` rejects a non-finite Float64
  (confirmed by reading `_strict_json_from_runtime`); no rendering path
  emits a bare Python `nan`/`inf` token (Float64 rendering spells them
  `float64(nan)`/`float64(inf)`/`float64(-inf)` explicitly).
- **JSON loss of exactness — characterized precisely.** Live-probed:
  `json_encode(rational(1,4))` -> `"0.25"`; `json_decode("0.25")` unwrapped
  via `representation_match("json", ...)` yields the plain host float
  `0.25`, and `0.25 == rational(1,4)` is **`false`** under `genia_equal`
  (the legacy-float/exact-family bridge is deliberately not established in
  this gate — see `equality.py`'s own comment on the point). The same holds
  for `exact(float64(2))` (Decimal `2.0`) round-tripping through JSON to a
  legacy float `2.0`, `2.0 == exact(float64(2))` is `false`. This is exactly
  the gap Step 6's agent already flagged (contract 13.5, decode side
  unimplemented) — this audit adds the concrete confirmation that the
  round-trip is not just "type-different" but **equality-visible**: a value
  written to JSON and read back is `!=` the value that was encoded, for any
  Decimal or terminating Rational. This is a real, user-visible exactness
  hole for any program that persists exact numeric values through the
  `json_encode`/`json_decode` boundary and later compares them.
- **Display/debug ambiguity.** No two distinct underlying values render
  identically: Decimal always retains a `.0`, Rational is always
  `n/d` (a shape no Integer/Decimal ever produces), and Float64 is always
  wrapped in the `float64(...)` atom. Confirmed by reading all three
  `render_*` functions together.
- **Host exception leakage.** Grepped `except ZeroDivisionError`/
  `except OverflowError` repo-wide: the only two `except OverflowError`
  sites are in `numeric_values.py` (`construct_float64`,
  `_decimal_to_correctly_rounded_float`), both translate to
  `NumericMisuseError` or a `None` sentinel, never re-raise or leak Python
  text. `5 % 0` (plain Integer) was probed live and raises
  `NumericMisuseError` ("exact remainder by zero"), not a bare
  `ZeroDivisionError`.
- **Parser/IR/evaluator agreement.** Spot-checked via the existing
  `spec/parse/exact-numeric-parse-*.yaml`, `spec/ir/exact-numeric-ir-*.yaml`
  suites (all passing in the 720/720 run above) plus the optimizer check
  above; no disagreement found between what the parser tags, the Core IR
  carries, and the evaluator interprets for integer/decimal/exponent/unary
  literal shapes.
- **In-process vs. subprocess-host parity.** See §1 — identical outcomes
  for every applicable numeric case across both paths. This is *not* the
  same as independent second-host conformance (§4).
- **Stale tests.** `tests/unit/test_optimizer.py`'s migrated assertion
  (above) was the only test found asserting a pre-N-1 shape; it was already
  correctly updated, not merely still passing by accident. No other stale
  legacy-shape assertion was found in the numeric-related test files.
- **Documentation overclaim.** Re-read `GENIA_STATE.md`'s "Exact Numeric
  Model" section (Steps 1-6) line by line against the code and the tests
  above. Every claim there is backed by a passing test or a direct code
  reference; no claim exceeds the evidence. `README.md`'s `json_encode`/
  `json_decode` paragraph already states the decode-side gap accurately.
  `GENIA_REPL_README.md`'s rendering-format claims match `render_decimal`/
  `render_rational`/`render_float64` exactly. No overclaim was found or
  needed fixing.

### Bug found and fixed

- `numeric_values.py`'s `construct_float64` had one line (106 columns)
  exceeding the repository's configured 100-column `ruff format` line
  length. `uv run ruff format --check .` flagged it (the file was not
  ruff-format-clean, though `ruff check .` — lint rules — was already
  clean, matching what prior slices' "ruff clean" claims meant by that
  phrase). Wrapped the `raise` call across three lines; no behavior change.
  `uv run ruff format --check src/genia/numeric_values.py` and
  `uv run ruff check src/genia/numeric_values.py` both now pass, and the
  targeted numeric test files were re-run afterward with no change in
  outcome. This audit did not attempt to reformat the ~246 other files in
  the repository that `ruff format --check .` also flags: that drift
  predates this issue, is repo-wide and unrelated to the exact-numeric
  model, and neither `AGENTS.md` nor `GENIA_STATE.md` names `ruff format
  --check` as a required gate (only `ruff check` is referenced by prior
  release audits) — fixing it is out of this audit's scope.

No other bug was found. Every other item above matched the contract and the
documented, already-disclosed scope boundary.

## 3. Genuine gaps left as documented blockers (not fixed here, per charge)

These were not newly discovered; they were already flagged by Step 6's
agent in `GENIA_STATE.md`. This audit's contribution is independently
confirming each is real (not just documented) and assessing R21 materiality:

1. **Legacy decimal-literal-to-float bridge still in place.** A bare `1.5`
   source literal still materializes, at evaluation time, through
   `numeric_literals.materialize_legacy_numeric` to a plain host `float`,
   not the contract's `Decimal` type. Confirmed live: `float64(1.5)` (a raw
   decimal literal) fails with "float64 expects an exact numeric value or
   Float64" because the literal is a legacy float, not an exact value.
   **R21-material:** yes — the R21 minimal capability floor's first vertical
   slice is exactly `parse-literal-number`, `unary-operators`,
   `arithmetic-basic` (`docs/design/r21-minimal-capability-floor.json`), and
   `r21-initial-execution-readiness.md` names `arithmetic-basic` as blocked
   specifically because it is numeric semantics gated on this contract. A
   C++ host implementing "parse a decimal literal" per the approved contract
   would have no matching Python reference-host behavior to conform to for
   the ordinary source-literal path, only for the explicit `exact(...)`/
   `float64(...)`/`rational(...)` builtin path.
2. **JSON decode of a fraction/exponent token to exact Decimal (contract
   13.5) is unimplemented; only encode-side landed in Step 6.** Confirmed
   live in §2 above, including the equality-visible round-trip loss.
   **R21-material:** contract section 21's acceptance list names "generic
   JSON boundary" as one whole item, not "encode only"; this is a literal
   gap against the contract's own stated implementation-acceptance
   criterion, independent of whether the R21 minimal capability floor's
   *first slice* happens to touch JSON (it does not — the floor's
   `explicitly_unsupported` list does not mention JSON, and JSON is not one
   of the three first-slice cases — but section 21 governs the whole gate,
   not just the first slice).
3. **The older `json_parse`/`json_stringify` pair is untouched** and does
   not handle Decimal/Rational/Float64 at all — confirmed by reading
   `json_parse_fn`/`_json_to_runtime`/`_json_from_runtime`, which never
   import or reference `numeric_values`. Lower materiality than (2): this
   pair is the pre-R9-hardening legacy surface, not the primary
   `json_encode`/`json_decode` boundary the contract targets, but it is a
   real, silent gap (Decimal/Rational/Float64 fed to `json_stringify` will
   go through generic Python `json.dumps`, which will raise a `TypeError`
   the caller cannot foresee from the contract).
4. **Precision contexts / transcendental approximation APIs (contract
   section 16) are unimplemented.** Confirmed unimplemented (no
   `precision_digits`/`rounding` construct or `sqrt`/`sin`/`log`/pi API
   exists anywhere in `src/genia/numeric_values.py` or `builtins.py`).
   **R21-material: no.** Section 16 itself states "Actual `sqrt`, `sin`,
   `log`, pi, or other transcendental APIs are not part of this gate," and
   the R21 minimal capability floor's first slice and explicit non-goals
   list (`r21-cpp-host-preflight.md` §11) do not require them. This gap is
   real but immaterial to R21's specific minimal-host requirements.
5. **No independent second-host conformance has been attempted for this
   contract.** Confirmed by cloning `m0smith/genia-cpp` (public, read-only)
   during this audit: it is bootstrap-only ("Status: bootstrap only. No C++
   interpreter is implemented here yet."), so no second real host exists to
   run the numeric spec suite against yet. This is not a defect in the
   Python reference host's work; it is a structural precondition of R21
   itself that cannot be satisfied by more Python-side work.
6. **Float64 scientific-notation leading-zero-stripping judgment call**
   (Step 6). Re-read `render_float64`: the exponent digits are
   `.lstrip("0") or "0"`, which the contract does not explicitly pin (the
   contract only says the inner text is "reformatted only for a lowercase
   `e`, an explicit exponent sign, no unnecessary exponent leading zeros,
   and a retained `.0`"). This reading is internally consistent (Python's
   own `repr(float)` never emits an exponent leading zero to begin with, so
   this code path is close to unreachable in practice — verified no
   spec/unit test currently exercises an input where it would matter) and
   does not contradict any written contract text. **Not a blocker**: it is
   a defensible interpretation of underspecified text, not an observed
   incorrect behavior.

## 4. R21 readiness re-evaluation (Part D)

Read `docs/design/r21-cpp-host-preflight.md`,
`docs/design/r21-initial-execution-readiness.md`,
`docs/design/r21-minimal-capability-floor.json`, and
`docs/strategy/release-roadmap.md`.

- `r21-cpp-host-preflight.md`'s final go/no-go: "Semantic C++ implementation
  is **NO-GO** until R19, R20, and the separately gated exact-numeric-model
  contract required by the minimal host are complete." R19/R20 are recorded
  complete elsewhere in `GENIA_STATE.md`; the exact-numeric-model contract
  is **not** complete per its own section 21 (gap 2 above).
- `r21-minimal-capability-floor.json`'s `status` is `"proposal_blocked"` and
  its `blocking_gates` list names `"exact_numeric_contract"` explicitly
  alongside `"genia_cpp_repository_verification"` (also still unresolved:
  the repository exists and is publicly readable, but is bootstrap-only —
  see gap 5 above).
- `m0smith/genia-cpp` was reachable (public repository, anonymous read) and
  was checked directly in this audit rather than assumed inaccessible: it
  contains only `AGENTS.md`, `README.md`, and a `bootstrap/` directory, with
  its own README stating no C++ interpreter exists yet.

### R21 semantic implementation: **NO-GO**

Concrete remaining blockers, in the order they should be closed:

1. Switch the decimal-literal source-classification path
   (`numeric_literals.materialize_legacy_numeric`) over to real `Decimal`
   construction, retiring the legacy float bridge for decimal-classified
   literals — this is the literal semantics R21's own first vertical slice
   (`parse-literal-number`/`arithmetic-basic`) needs a real reference
   behavior for.
2. Implement contract section 13.5 (JSON decode of a fraction/exponent
   token to exact Decimal), closing the equality-visible round-trip loss
   confirmed in §2/§3.
3. Decide and document the `json_parse`/`json_stringify` legacy pair's
   posture toward the new numeric kinds (either extend it or explicitly
   declare it out of scope with a normalized failure instead of a raw
   Python `TypeError`).
4. Re-run this contract's own section-21 skeptical audit to PASS once 1-3
   land, updating `GENIA_STATE.md` and this document accordingly.
5. Independently of 1-4: `m0smith/genia-cpp` needs to move past bootstrap
   before any second-host conformance evidence can exist at all; this is
   outside `genia-2026`'s repository boundary and cannot be resolved by
   further work here.

Transcendentals/precision contexts (contract section 16) are confirmed
**not** a blocker for R21's minimal capability floor (see gap 4 above) and
should not be added to this list without a separate roadmap decision
expanding R21's scope.

## 5. Scope discipline

Per the Step 7 charge, this audit implemented **no** new semantic slice: the
one code change made (§2's bug fix) is a formatting-only line wrap with an
unchanged AST/behavior, verified by re-running the affected file's full
test suite with an identical pass count before and after. No JSON decode
exactness, legacy-literal-bridge retirement, or transcendental work was
attempted. No C++ implementation was started or proposed beyond the
blocker list above.
