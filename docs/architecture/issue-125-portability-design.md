# Issue #125 Design — Require Portability Analysis in Pre-Flight

**Phase:** design
**Branch:** `issue-125-portability-preflight`
**Issue:** #125 — Require portability analysis in pre-flight for all features
**Scope:** Documentation/process only. No runtime behavior changes.

---

## 1. Purpose

Translate the approved spec into exact file edits. Three files change. No new files. No runtime files.

---

## 2. Scope Lock

Follows spec exactly. Three files:

- `docs/process/00-preflight.md` — insert section `3a. PORTABILITY ANALYSIS`
- `docs/process/run-change.md` — add portability-analysis requirement note at step 2
- `docs/process/llm-prompts.md` — add portability analysis block to preflight prompt section

No other files change. No test files. No `GENIA_STATE.md`. No spec YAML.

---

## 3. Architecture Overview

All three files are plain Markdown. All changes are additive text insertions. No existing text is deleted or altered except where the insertion point requires it. No new directories or file types are introduced.

The implementation phase can apply all three edits as direct text insertions at specified line offsets. Order of edits: `00-preflight.md` first (it is the primary artifact), then `run-change.md`, then `llm-prompts.md`.

---

## 4. File Changes

### Modified files

1. `docs/process/00-preflight.md` — insert new section `3a. PORTABILITY ANALYSIS`
2. `docs/process/run-change.md` — extend step 2 with portability analysis note
3. `docs/process/llm-prompts.md` — add portability analysis block to preflight prompt section

### New files

None.

### Removed files

None.

---

## 5. Exact Edit Specifications

---

### 5.1 `docs/process/00-preflight.md`

**Current section boundary (from last committed state):**

Section 3 ends with:

```markdown
## How this must be described in docs:

---

4. CONTRACT vs IMPLEMENTATION
```

**Insertion:** After the `---` that closes section 3 and before the `4. CONTRACT vs IMPLEMENTATION` heading, insert the full `3a. PORTABILITY ANALYSIS` block.

**Exact text to insert** (insert as a new block, preserving one blank line before and after the surrounding `---` separators):

```markdown
3a. PORTABILITY ANALYSIS

---

Required for every pre-flight. All seven fields must be answered before the spec phase begins.
Do not use "TBD" or defer any field. Ground answers in GENIA_STATE.md facts only.

## Portability zone:

What architectural zone does this change primarily affect?
Choose one or more:
- `language contract` — behavior all hosts must implement; enters shared spec
- `Core IR` — introduces or modifies a portable IR node family
- `prelude` — behavior lives in .genia stdlib; portable if no host calls
- `Python reference host` — Python-only, host-backed behavior
- `host adapter` — the run_case harness boundary
- `shared spec` — affects spec/* YAML case assertions
- `docs/tests only` — no runtime or contract change

If multiple zones: note whether the change is split per the one-zone-per-change rule (AGENTS.md)
or explicitly justified.

## Core IR impact:

Does this change introduce or modify portable Core IR node families?
- `none` — change does not affect Ir* node families
- `yes — <name the affected Ir* node families and whether added or modified>`

Vague or deferred answers are not allowed.

## Capability categories affected:

Which shared spec categories does this change affect?
List one or more from: parse, ir, eval, cli, flow, error
Or: `none` — for pure docs/process changes

## Shared spec impact:

Does this change require new or updated shared spec YAML cases?
- `none — no new shared spec cases required`
- `new cases required in spec/<category>/` — describe what observable behavior they will assert
- `existing cases may need update in spec/<category>/` — describe what is expected to change

Must be consistent with Capability categories affected above.

## Python reference host impact:

Does this change alter Python reference host behavior?
- `none — Python host behavior is unchanged`
- `yes — <describe which files in src/genia/ or hosts/python/ change and what behavior changes>`

Label Python-host-only behavior explicitly. Do not claim it is a language contract change.

## Host adapter impact:

Does this change alter the host adapter boundary (hosts/python/adapter.py::run_case)?
- `none — host adapter interface is unchanged`
- `yes — <describe what changes at the adapter boundary>`

## Future host impact:

What would a future non-Python host need to implement for this feature?
- If portability zone includes language contract, Core IR, or prelude (without host calls):
  describe what the future host must implement to pass the relevant shared spec cases.
- If portability zone is Python reference host only:
  `Python-host-only; future hosts are not affected in the current phase.`
- If portability zone is docs/tests only:
  `none — no future host impact.`

Do not claim future hosts are implemented. Do not claim they currently pass any spec cases.

---

Example (process-only change):

  Portability zone: docs/tests only
  Core IR impact: none
  Capability categories affected: none
  Shared spec impact: none
  Python reference host impact: none
  Host adapter impact: none
  Future host impact: none — no future host impact.

---
```

**Resulting section order after edit:**

```
3. FEATURE MATURITY
  ...
  ---

3a. PORTABILITY ANALYSIS
  ...
  ---

4. CONTRACT vs IMPLEMENTATION
  ...
```

---

### 5.2 `docs/process/run-change.md`

**Current content (full file):**

```markdown
# Running a Genia Change

For every issue:

1. Create branch: `issue-<number>-<short-name>`
2. Run preflight prompt
3. Commit preflight
4. Run spec prompt
5. Commit spec
6. Run design prompt
7. Commit design
8. Run failing-test prompt
9. Commit failing tests
10. Run implementation prompt
11. Commit implementation
12. Run docs prompt
13. Commit docs
14. Run audit prompt
15. Commit audit or audit fixes

Do not merge until audit passes.
```

**Edit:** Expand step 2 to add a sub-note about portability analysis. Replace the single-line step 2 with the following:

Replace:
```markdown
2. Run preflight prompt
3. Commit preflight
```

With:
```markdown
2. Run preflight prompt
   - Pre-flight must include a completed PORTABILITY ANALYSIS block (section 3a).
   - All seven portability fields must be answered before the spec phase begins.
   - Incomplete portability analysis is grounds for blocking the spec step.
3. Commit preflight
```

**Resulting file after edit:**

```markdown
# Running a Genia Change

For every issue:

1. Create branch: `issue-<number>-<short-name>`
2. Run preflight prompt
   - Pre-flight must include a completed PORTABILITY ANALYSIS block (section 3a).
   - All seven portability fields must be answered before the spec phase begins.
   - Incomplete portability analysis is grounds for blocking the spec step.
3. Commit preflight
4. Run spec prompt
5. Commit spec
6. Run design prompt
7. Commit design
8. Run failing-test prompt
9. Commit failing tests
10. Run implementation prompt
11. Commit implementation
12. Run docs prompt
13. Commit docs
14. Run audit prompt
15. Commit audit or audit fixes

Do not merge until audit passes.
```

---

### 5.3 `docs/process/llm-prompts.md`

**Current content (full file):**

```markdown
# Genia LLM Prompt Templates

## Universal Header

Before doing anything, read and follow:

- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md

GENIA_STATE.md is final authority.

Run:

```bash
./scripts/check-genia-branch.sh
```

Do not work on main.
Do not continue into another phase.

# Phase Rule

This prompt is for phase: <PHASE>.

Allowed commit prefix: <PREFIX>.

You may only modify files needed for this phase.
Stop after committing this phase.


Then add phase-specific sections below it for `preflight`, `spec`, `design`, `test`, `implementation`, `doc-sync`
```

**Edit:** Append a new `## Preflight Phase` section at the end of the file. The file currently ends with a trailing note about phase-specific sections. Replace the trailing note and add the explicit section content.

Replace the final line:
```markdown
Then add phase-specific sections below it for `preflight`, `spec`, `design`, `test`, `implementation`, `doc-sync`
```

With:
```markdown
Add phase-specific sections below the Universal Header and Phase Rule for each phase.

## Preflight Phase

After completing sections 0 (BRANCH), 1 (SCOPE LOCK), 2 (SOURCE OF TRUTH), and 3 (FEATURE MATURITY),
complete section 3a (PORTABILITY ANALYSIS) before proceeding to section 4.

All seven portability fields are required. Do not leave any field blank or deferred.

Required fields:

- `Portability zone:` — one or more of: language contract, Core IR, prelude, Python reference host, host adapter, shared spec, docs/tests only
- `Core IR impact:` — `none` or `yes — <named Ir* node families>`
- `Capability categories affected:` — subset of parse, ir, eval, cli, flow, error — or `none`
- `Shared spec impact:` — `none` or `new/updated cases required in spec/<category>/`
- `Python reference host impact:` — `none` or `yes — <description>`
- `Host adapter impact:` — `none` or `yes — <description>`
- `Future host impact:` — forward-looking note grounded in current GENIA_STATE.md facts

Rules:
- Do not use "TBD" or defer any field.
- Do not claim Node.js, Java, Rust, Go, or C++ hosts are implemented.
- Do not claim a Python-host-only behavior is part of the language contract unless GENIA_STATE.md says so.
- Answer `Core IR impact:` with `none` or a named Ir* family — no vague answers.

Do not proceed to spec until section 3a is complete.
```

**Resulting file after edit (full):**

```markdown
# Genia LLM Prompt Templates

## Universal Header

Before doing anything, read and follow:

- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md

GENIA_STATE.md is final authority.

Run:

```bash
./scripts/check-genia-branch.sh
```

Do not work on main.
Do not continue into another phase.

# Phase Rule

This prompt is for phase: <PHASE>.

Allowed commit prefix: <PREFIX>.

You may only modify files needed for this phase.
Stop after committing this phase.

Add phase-specific sections below the Universal Header and Phase Rule for each phase.

## Preflight Phase

After completing sections 0 (BRANCH), 1 (SCOPE LOCK), 2 (SOURCE OF TRUTH), and 3 (FEATURE MATURITY),
complete section 3a (PORTABILITY ANALYSIS) before proceeding to section 4.

All seven portability fields are required. Do not leave any field blank or deferred.

Required fields:

- `Portability zone:` — one or more of: language contract, Core IR, prelude, Python reference host, host adapter, shared spec, docs/tests only
- `Core IR impact:` — `none` or `yes — <named Ir* node families>`
- `Capability categories affected:` — subset of parse, ir, eval, cli, flow, error — or `none`
- `Shared spec impact:` — `none` or `new/updated cases required in spec/<category>/`
- `Python reference host impact:` — `none` or `yes — <description>`
- `Host adapter impact:` — `none` or `yes — <description>`
- `Future host impact:` — forward-looking note grounded in current GENIA_STATE.md facts

Rules:
- Do not use "TBD" or defer any field.
- Do not claim Node.js, Java, Rust, Go, or C++ hosts are implemented.
- Do not claim a Python-host-only behavior is part of the language contract unless GENIA_STATE.md says so.
- Answer `Core IR impact:` with `none` or a named Ir* family — no vague answers.

Do not proceed to spec until section 3a is complete.
```

---

## 6. Data Shapes

No data structures involved. All changes are Markdown text insertions.

The seven-field portability block is a flat list of labeled fields with free-form answers constrained by the valid-value sets defined in the spec. No machine-parseable structure is introduced.

---

## 7. Control Flow

Not applicable — these are static document edits.

Logical reading order after implementation:

1. An agent receives a preflight prompt.
2. The agent reads `docs/process/00-preflight.md` (the updated template).
3. The agent sees section `3a. PORTABILITY ANALYSIS` with all seven fields.
4. The agent fills in all seven fields before proceeding to section 4.
5. A reviewer checks that all seven fields are present and non-deferred.
6. If any field is missing or deferred, the pre-flight is returned for correction before spec begins.

---

## 8. Error Handling Design

Pre-flight errors are human/agent-review errors, not runtime errors.

A pre-flight is considered incomplete (blocking the spec step) when:
- Section `3a. PORTABILITY ANALYSIS` is absent from the document.
- Any of the seven field labels is absent.
- Any field contains `"TBD"` or `"to be determined"`.
- Any field claims a non-Python host is implemented.

Detection mechanism: manual review by the agent or human running the audit or reviewing the spec commit. No automated test change in this issue.

---

## 9. Integration Points

### `docs/process/00-preflight.md` ↔ agent prompts

Agents that use the preflight template will see the new section and be prompted to fill it in. The design does not require agents to re-read any additional docs; the template is self-contained.

### `docs/process/run-change.md` ↔ human/agent workflow

Humans or agents following the step-by-step checklist see the portability requirement at step 2, before the spec commit at step 5.

### `docs/process/llm-prompts.md` ↔ agent prompt construction

Agents constructing LLM prompts from this template will include the portability analysis block in their preflight phase prompt. This makes the seven fields explicit in the prompt context itself, not just in the filled-in template.

### No integration with runtime, interpreter, CLI, Flow, or spec runner

---

## 10. Test Design Input

The spec determined that no machine-asserted test change is required for this issue. `tests/test_semantic_doc_sync.py` guards semantic facts in `docs/contract/semantic_facts.json`; it does not guard process doc structure.

For the test phase, the commit will document:
- The invariants from the spec (section 9) serve as the manual review checklist.
- No new test functions are added to `tests/test_semantic_doc_sync.py` in this issue.
- The full test suite is run after implementation to confirm no accidental regressions.

---

## 11. Doc Impact

### `GENIA_STATE.md`

No change required. This issue does not alter any implemented language behavior or host capability.

### Process docs (the three target files)

All three are updated as specified in section 5 above.

### Architecture docs

The pre-flight document (`docs/architecture/issue-125-portability-preflight.md`) and spec document (`docs/architecture/issue-125-portability-spec.md`) already exist on this branch from prior phases. The design document (this file) is the third architecture artifact. No further architecture docs are needed.

### Existing pre-flight docs for closed issues

Not updated. The spec explicitly excludes retroactive updates to pre-flight documents on closed issues.

---

## 12. Constraints

Must:
- Follow existing Markdown style used in `docs/process/*.md` (flat headings, bullet lists, fenced code for examples).
- Preserve all existing content in the three target files; add only, do not remove.
- Keep the new section self-contained so agents can fill it in without consulting a separate document.
- Use truthful language throughout: "Python reference host only", "planned future hosts".

Must NOT:
- Add a new phase to the pipeline.
- Change section numbers 4–10 in `docs/process/00-preflight.md`.
- Add machine-asserted test coverage in this issue.
- Mention unimplemented hosts as if they exist.
- Introduce any runtime, IR, or spec runner changes.

---

## 13. Complexity Check

Classification: Minimal and Necessary.

Justification: Three small text additions to three existing Markdown files. No new files. No runtime changes. The most complex part is the `00-preflight.md` insertion, which is a self-contained block of approximately 60 lines.

---

## 14. Final Check

- Matches spec exactly: YES — all seven fields, section label `3a`, placement between 3 and 4, workflow note at step 2, LLM prompt addition all match spec decisions.
- No new behavior introduced: YES — document-only changes.
- Structure is clear and implementable: YES — section 5 gives exact replacement strings for each edit.
- Ready for implementation without ambiguity: YES — the implementation phase can apply the three edits directly from this document.
