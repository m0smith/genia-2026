# Issue #125 Preflight: Require Portability Analysis in Pre-Flight

=== GENIA PRE-FLIGHT ===

CHANGE NAME:
Require portability analysis in pre-flight for all features

Date: 2026-04-27

Parent epic:
#115 — Minimize Host Porting Surface via Prelude + IR + Capability Boundaries

## 0. Branch

- Starting branch: `main`
- Working branch: `issue-125-portability-preflight`
- Branch status: newly created from `main`

## 1. Scope Lock

### Change includes:

- Extending the existing pre-flight template (`docs/process/00-preflight.md`) so every future feature explicitly answers portability-impact questions before spec/design/implementation begins.
- Requiring analysis of:
  - prelude vs host responsibility
  - Core IR impact (does this change enter Core IR or stay host-local?)
  - shared semantic spec impact (which spec categories are affected: parse, ir, eval, cli, flow, error?)
  - affected capability categories: parse, ir, eval, cli, flow, error
  - host adapter impact (does Python reference host adapter change?)
  - Python reference host behavior impact
  - future-host portability risk (what would a non-Python host need to implement?)
- Updating workflow guidance (`docs/process/run-change.md`, `docs/process/llm-prompts.md`) so portability analysis is required before spec begins.
- Looking for any existing PR/review checklist and updating it only if it clearly exists and is relevant.

### Change does NOT include:

- Implementing a new language feature.
- Changing Genia semantics.
- Adding a new host.
- Changing Core IR behavior.
- Adding new shared spec cases (except process/checklist examples already part of docs).
- A repo-wide documentation rewrite.
- Creating speculative portability promises.
- Changing any runtime behavior.

## 2. Source of Truth

Authoritative sources, in repository order:

1. `GENIA_STATE.md` (final authority)
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. `spec/*`
6. `docs/host-interop/*`
7. `docs/architecture/*`
8. implementation (`src/*`, `hosts/*`)
9. `docs/process/run-change.md`

If these files conflict, `GENIA_STATE.md` wins.

Additional relevant files:

- `docs/process/00-preflight.md` — the current pre-flight template to be extended
- `docs/process/run-change.md` — the workflow guide to be updated
- `docs/process/llm-prompts.md` — agent prompt templates to be updated
- `docs/host-interop/HOST_INTEROP.md` — shared host contract doc
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md` — capability tracking doc
- `docs/host-interop/HOST_PORTING_GUIDE.md` — porting guidance
- `docs/architecture/core-ir-portability.md` — Core IR boundary doc (if present)
- `docs/contract/semantic_facts.json` — protected semantic facts (if any wording changes)
- `tests/test_semantic_doc_sync.py` — doc sync tests (if semantic facts change)
- Prior issue preflight docs under `docs/architecture/` for pattern consistency

### Notes:

- `AGENTS.md` already requires the full phase pipeline and identifies Core IR as the portability boundary. This change enforces that boundary analysis happens at pre-flight, not only at implementation time.
- `GENIA_STATE.md` states Python is the only implemented host; all other hosts are planned/scaffolded only. The portability analysis requirement must not imply those hosts are implemented.
- This change is process/documentation work only. No runtime behavior changes.

## 3. Feature Maturity

Stage: Partial / Process-level

How this must be described in docs:

- As a required planning discipline for future changes.
- Not as a completed multi-host implementation.
- Not as a guarantee that future hosts exist or are ready.
- Not as a claim that every current behavior is already portable across all planned hosts.
- As a strengthening of the existing "Core IR as portability boundary" discipline already stated in `AGENTS.md`.

## 4. Contract vs Implementation

### Contract (what becomes required):

- Every feature pre-flight must explicitly classify portability impact before spec/design/implementation begins.
- Every feature must identify whether its behavior belongs in:
  - language contract (portable, all hosts)
  - Core IR (portability boundary node families)
  - prelude (`.genia` stdlib, portable if no host calls)
  - Python reference host (Python-only, host-backed)
  - host adapter (shared interface boundary)
  - shared semantic specs (`spec/*`)
  - docs/tests only
- Every feature must identify which shared spec categories are affected: parse, ir, eval, cli, flow, error.
- Every feature must state what a future non-Python host would need to implement.

### Implementation (what changes in docs/process):

- Update `docs/process/00-preflight.md` to include a required "PORTABILITY ANALYSIS" section.
- Update `docs/process/run-change.md` to state portability analysis is mandatory before spec.
- Update `docs/process/llm-prompts.md` to include portability analysis in the preflight prompt block.
- Optionally update any PR/review checklist if one is found in the repository.

### Not implemented:

- No new host.
- No new Core IR node.
- No new language syntax.
- No runtime behavior change.
- No new shared spec cases (beyond any doc examples that are not machine-asserted).

## 5. Test Strategy

### Core invariants:

- The pre-flight template requires a portability analysis section.
- Workflow guidance references portability analysis as a mandatory preflight step.
- No docs claim new host support.
- No docs imply Core IR changed.

### Expected behaviors after this change:

Future agents using the pre-flight template must be prompted to explicitly answer:

- Does this change affect parse / ir / eval / cli / flow / error spec categories?
- Is this behavior prelude-level or host-level?
- Does this enter Core IR? If so, which node families?
- Does this need new shared semantic spec cases?
- Does the Python reference host behavior change?
- What would future hosts need to implement for this feature?
- Is this change confined to one zone (language contract / Core IR / host adapters / docs)?

### Failure cases:

- Template omits portability analysis section.
- Docs imply Node/Java/Rust/Go/C++ hosts are implemented.
- Workflow guidance allows implementation before portability analysis.
- Process docs conflict with `AGENTS.md` phase order.
- Portability section is present but does not require answers to the required questions.

### How this will be tested:

- Run existing doc/semantic sync tests (`tests/test_semantic_doc_sync.py`) if they cover process doc content.
- Search for references to the old pre-flight template across the repository and confirm they are updated or intentionally left unchanged.
- Run targeted tests around docs/process validation if such tests exist.
- Run full test suite if practical to confirm no accidental runtime regressions.
- Manual review: compare updated template against `AGENTS.md` to confirm alignment.

## 6. Examples

### Minimal example of what the new portability analysis section requires:

A future feature pre-flight includes a `PORTABILITY ANALYSIS` block such as:

```
PORTABILITY ANALYSIS

Portability zone: prelude
Core IR impact: none — no new IR nodes required
Shared spec impact: eval cases required (spec/eval/)
Capability categories affected: eval
Python reference host impact: uses existing runtime behavior; no new builtins
Host adapter impact: none
Future host impact: any future host must implement the same prelude function behavior via its own prelude or stdlib layer
```

### Real example — a flow-related feature:

```
PORTABILITY ANALYSIS

Portability zone: prelude (Flow stage helper)
Core IR impact: none unless lowering changes — Flow stages do not lower to new IR nodes
Shared spec impact: spec/flow/ case required
Capability categories affected: flow
Python reference host impact: Python reference host only today; new prelude function backed by existing Flow kernel
Host adapter impact: none — Flow kernel already in place
Future host impact: future hosts must implement the lazy pull-based Flow kernel to pass the new spec/flow/ case
```

## 7. Complexity Check

Classification: Revealing structure.

Justification:

- This does not add language complexity.
- It makes the portability boundary explicit at the planning stage, before work starts.
- It reduces future multi-host drift by surfacing host-vs-language decisions at preflight rather than at implementation.
- It does not change the number of phases required; it adds one required section to an existing phase.

## 8. Cross-File Impact

### Files that may need change:

- `docs/process/00-preflight.md` — add required PORTABILITY ANALYSIS section
- `docs/process/run-change.md` — note portability analysis is required before spec
- `docs/process/llm-prompts.md` — include portability analysis in preflight prompt block
- PR/review checklist docs only if present in repository (search required in spec phase)
- `docs/contract/semantic_facts.json` — only if protected wording changes; expected: no change
- `tests/test_semantic_doc_sync.py` — only if semantic facts or doc sync expectations change; expected: no change

### Files that must NOT change during this phase (pre-flight only):

- All files above remain unmodified until spec or later phases.
- No implementation files.
- No spec YAML files.
- No `GENIA_STATE.md` update expected (process-only change).

Risk of drift: Medium

Why: This touches process docs that guide future agent behavior. It must align with `AGENTS.md`, `GENIA_STATE.md`, and host-portability docs. It is easy to accidentally imply future hosts are real or that portability is fully achieved today.

## 9. Philosophy Check

- preserve minimalism? YES — adds one required section to an existing template; no new phases
- avoid hidden behavior? YES — the whole point is to surface portability decisions explicitly
- keep semantics out of host? YES — this reinforces the existing rule; does not change it
- align with pattern-matching-first? N/A — process-only change

Notes:

- This strengthens the existing "Core IR as portability boundary" discipline already stated in `AGENTS.md`.
- This should prevent features from quietly becoming Python-only semantics because no one asked the portability question.
- The required portability analysis text must use truthful language: "Python reference host only", "planned future hosts", "not yet implemented".

## 10. Prompt Plan

Will use full required pipeline?
YES

Phases (one prompt, one commit each):

1. preflight — this document
2. spec — define exact required fields, their location in the template, and what counts as sufficient analysis
3. design — identify specific wording and placement in each affected doc
4. test — commit failing tests for any doc-validation test changes (if applicable)
5. implementation — update the actual template and workflow docs
6. docs sync — verify alignment across all touched docs
7. audit — confirm alignment in examined areas, no false portability claims, no phase-skipping

Each phase must be a separate prompt and a separate commit.
Do not continue beyond this preflight until explicitly prompted.

## 11. Final GO / NO-GO

Decision: GO for spec phase.

Blockers: None.

Spec-phase cautions:

- Define exactly which fields belong in the portability analysis section (required vs optional).
- Define where in the template the section appears (placement matters for workflow order).
- Define what counts as sufficient portability analysis for a process-only change vs a runtime behavior change.
- Confirm whether `tests/test_semantic_doc_sync.py` covers any pre-flight template content (if not, decide whether to add coverage).
- Do not imply future hosts exist in any example text.
- Do not add portability claims that exceed what `GENIA_STATE.md` says is implemented.

Recommended next prompt:

- `SPEC for #125`

Files likely touched in later phases:

- `docs/process/00-preflight.md`
- `docs/process/run-change.md`
- `docs/process/llm-prompts.md`
- possibly `docs/contract/semantic_facts.json` (unlikely)
- possibly `tests/test_semantic_doc_sync.py` (only if doc sync assertions change)
- possibly any PR checklist doc discovered during spec phase
