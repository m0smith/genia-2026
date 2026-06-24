# === GENIA PRE-FLIGHT (issue #492 r4-result-policy-include-flags) ===

Follow docs/process/llm-system-prompt.md.

CHANGE NAME: issue #492 r4-result-policy-include-flags
CHANGE SLUG: issue-492-r4-result-policy-include-flags

GENIA_STATE.md is final authority.

HARD STOP: Pre-flight only. No branch creation beyond the existing feature
branch, no file edits, no tests, no contract, no commit.

---

## 0. BRANCH

Branch required: YES
Branch type: feature
Branch slug: r4-result-policy-include-flags
Expected branch: feature/issue-492-r4-result-policy-include-flags
Base branch: main

Status: branch already exists and is checked out. Confirmed not on `main`.
One branch, one change.

---

## 1. SCOPE LOCK

Includes:
- Review `result_policy` normalization in `src/genia/lifecycle_plan.py`
  (`_normalize_result_policy`).
- Decide and lock the intended contract for explicit boolean
  `include_phase`, `include_scope`, `include_role`, and
  `include_source_location` values.
- Make accepted explicit values preserved in normalized output (per the
  decision in section 4 below).
- Add/update tests in `tests/unit/test_lifecycle_plan.py` to lock the
  behavior, including explicit `false`.
- Update lifecycle docs only if the documented contract wording needs
  clarification (`GENIA_STATE.md` 9.3, `docs/architecture/lifecycle.md`).

Excludes:
- No lifecycle runner.
- No cleanup execution.
- No phase execution.
- No setup/teardown annotation behavior.
- No native-test lifecycle hooks.
- No command/file/pipe/repl lifecycle behavior.
- No parser, IR, evaluator, builtins, CLI, or prelude changes.
- No change to `failure_order` handling or to `cleanup` / `failure_policy`
  normalization.

---

## 2. SOURCE OF TRUTH

Authoritative:
- GENIA_STATE.md (section 9.3 - Lifecycle plan data-shape support)
- GENIA_RULES.md
- README.md
- AGENTS.md

Additional relevant:
- `src/genia/lifecycle_plan.py` (`_normalize_result_policy`, `_require_boolean`)
- `tests/unit/test_lifecycle_plan.py` (result_policy tests, lines ~358-426)
- `docs/architecture/lifecycle.md` (line ~152)
- Merged issue #451 (introduced root policy normalization); this is its audit
  follow-up.

Notes:
- GENIA_STATE.md 9.3 currently states: "Result policy validation preserves
  deterministic failure observability fields." The current code does NOT
  preserve explicit values - it validates type only and emits hardcoded
  defaults. This is the gap to close.

---

## 3. FEATURE MATURITY

Stage:
[x] Experimental
[ ] Partial
[ ] Stable

Doc wording: "Experimental, Python reference host only." No maturity change;
this is a correctness fix within an existing experimental utility.

---

## 3a. Portability Analysis

Follow docs/process/extensions/portability-analysis.md.

- Portability zone: Python reference host internal utility (data-shape
  validation/normalization). No surface-language or cross-host change.
- Core IR impact: none. No `Ir*` node families touched.
- Capability categories affected: none (no capability surface; inert data
  validation only).
- Shared spec impact: none to the portable lifecycle-plan data shape. The
  boolean `include_*` fields already exist in the shape; only the host
  normalization of accepted values changes (default -> preserved explicit
  value).
- Python reference host impact: `src/genia/lifecycle_plan.py`
  `_normalize_result_policy` and its unit tests.
- Host adapter impact: none.
- Future host impact: none. Any future host that implements the same data
  shape must preserve explicit accepted booleans - consistent with the
  clarified contract.

---

## 4. CONTRACT vs IMPLEMENTATION

Portable contract:
- A lifecycle plan `result_policy` is inert data. `include_phase`,
  `include_scope`, `include_role`, and `include_source_location` are optional
  boolean observability fields describing which fields a result record would
  include. Each defaults to `true` when absent.

Decision (locks the audit ambiguity):
- These observability fields accept either boolean. Both `true` and `false`
  are valid, and the explicit accepted value is PRESERVED in normalized
  output. Silent normalization of explicit `false` to `true` is a defect.
- Rationale: unlike `failure_policy.preserve_*` and the cleanup-eligibility
  fields (which guard failure observability and MUST stay at a fixed value),
  the `include_*` flags are presentation toggles for result records. A caller
  asking to omit a field is a legitimate, portable choice, not an unsafe one.
  Validation already accepts both booleans; preservation simply makes accepted
  input match normalized output.

Python implementation today:
- `_normalize_result_policy` builds `normalized` with hardcoded
  `include_* = True`, then loops the four fields calling `_require_boolean`
  for type validation only. The validated value is never written back, so an
  explicit `false` validates and then reverts to `true`.

Not implemented (and out of scope):
- No execution of result policy. No result-record emission. These fields
  remain inert data.

---

## 5. TEST STRATEGY

Core invariants:
- Absent `include_*` field -> normalized `true`.
- Explicit `include_* = true` -> normalized `true`.
- Explicit `include_* = false` -> normalized `false` (currently failing /
  missing coverage; this is the regression to lock).
- Non-boolean `include_*` -> `ValueError` with path-specific diagnostic
  `invalid lifecycle plan at plan.result_policy.<field>: expected boolean,
  got <type>` (unchanged).

Expected behavior:
- Each of the four fields preserved independently; mixing explicit `true`/
  `false` across fields preserves each as given.

Failure cases:
- Symbol / non-boolean values for any include field still rejected.
- `failure_order` other than `observed_order` still rejected (unchanged).
- Unknown result-policy fields still rejected (unchanged).

Test approach:
- Extend `tests/unit/test_lifecycle_plan.py`. Add explicit-`false`
  preservation assertions to the existing normalization test (or a new
  focused test), keep existing default and rejection tests green. Run:
  `UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py -v`

---

## 6. EXAMPLES

Minimal:
- Input `result_policy: { include_phase: false }` -> normalized
  `include_phase = false`, other three default `true`.

Real:
- A compact result policy that drops scope and source location:
  `result_policy: { include_scope: false, include_source_location: false }`
  -> normalized preserves both `false`; `include_phase`/`include_role` `true`.

---

## 7. COMPLEXITY CHECK

[ ] Adding complexity
[x] Revealing structure

Justification: The fix removes a silent override - it makes normalized output
honor validated input. Net code change is to write the accepted value instead
of discarding it. No new control structures or abstractions.

---

## 8. CROSS-FILE IMPACT

Files likely to change:
- `src/genia/lifecycle_plan.py` (`_normalize_result_policy`)
- `tests/unit/test_lifecycle_plan.py`
- Possibly `GENIA_STATE.md` 9.3 and `docs/architecture/lifecycle.md` (wording
  clarification only, if needed)

Risk of drift:
[x] Low
[ ] Medium
[ ] High

Doc/code drift is the actual bug here; closing it reduces drift. The
GENIA_STATE wording "preserves deterministic failure observability fields"
should be confirmed/clarified to match the preserve-explicit decision.

---

## 9. DOC DISTILLATION CHECK

Creates process artifacts? [ ] YES  [x] NO (handoffs only; not committed)
Adds docs/design or docs/architecture files? [ ] YES  [x] NO (edits existing
wording at most)
Doc drift risk: [x] Low  [ ] Medium  [ ] High

---

## 10. PHILOSOPHY CHECK

- preserves minimalism? YES - smaller, more honest normalization.
- avoids hidden behavior? YES - removes a hidden override of explicit input.
- keeps semantics out of host? YES - no execution semantics added; inert data.
- aligns with pattern-matching-first? YES - no change to evaluation model.

Notes: Aligns the host normalization with the stated portable contract.

---

## KILLER WORKFLOW ALIGNMENT

Does this change directly strengthen Outcome-aware validated data pipelines?

[ ] Yes
[x] Indirectly
[ ] No

How: Strengthens **validation** and **diagnostics** correctness for the R4
lifecycle-plan data shape - accepted input must equal normalized output, with
deterministic path-specific diagnostics on rejection. R4 (portable lifecycle
contract) is the active release; this is an audit follow-up that keeps the
contract truthful. It does not add lifecycle machinery (which is parking-lot);
it only corrects data-shape normalization fidelity.

Reference: docs/strategy/killer-workflow.md

---

## 11. PROMPT PLAN

Pipeline: Preflight -> Contract -> Design -> Test -> Implementation -> Docs ->
Audit -> Distillation.

---

## FINAL GO / NO-GO

Ready to proceed? YES

Open decision now locked (section 4): explicit accepted booleans are
preserved; `false` is valid and must not normalize to `true`.

Missing: nothing blocking. Contract phase confirms GENIA_STATE 9.3 wording is
consistent with the preserve decision.
