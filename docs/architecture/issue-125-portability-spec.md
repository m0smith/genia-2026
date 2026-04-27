# Issue #125 Spec — Require Portability Analysis in Pre-Flight

**Phase:** spec
**Branch:** `issue-125-portability-preflight`
**Issue:** #125 — Require portability analysis in pre-flight for all features
**Scope:** Process/documentation only. No runtime behavior changes.

---

## 1. Source of Truth

Final authority: `GENIA_STATE.md`

Supporting:
- `GENIA_RULES.md`
- `AGENTS.md` (defines the phase pipeline and Core IR as portability boundary)
- `docs/process/00-preflight.md` (the template to be extended)
- `docs/process/run-change.md` (the workflow guide to be updated)
- `docs/process/llm-prompts.md` (the agent prompt guide to be updated)
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md` (capability taxonomy)
- `docs/host-interop/HOST_INTEROP.md` (shared host contract doc)

Relevant existing truths:
- Python is the only implemented host and is the reference host.
- `AGENTS.md` already states Core IR is the portability boundary and that a change should affect only ONE zone whenever possible.
- The current pre-flight template (`docs/process/00-preflight.md`) does not include a portability analysis section.
- The current workflow guide (`docs/process/run-change.md`) does not name portability analysis as a required step.
- Future hosts (Node.js, Java, Rust, Go, C++) are planned only; no runnable implementations exist.

---

## 2. Scope Decision

### Included in this spec

- Define the exact required portability-analysis fields that every pre-flight must contain.
- Define the placement of the PORTABILITY ANALYSIS block within the pre-flight template.
- Define valid values and required answer forms for each field.
- Define what counts as sufficient portability analysis for each class of change.
- Define what must never be claimed in the portability analysis section.
- Define how the requirement is propagated into workflow guidance docs.
- Define how the requirement will be validated (manual review criteria and any test assertions).

### Explicitly excluded from this spec

- Implementing a new language feature.
- Adding a new host.
- Changing Core IR.
- Changing runtime behavior.
- Adding new shared spec YAML cases.
- Changing `GENIA_STATE.md` implementation facts.
- Changing any file in `src/`, `hosts/`, `tests/`, or `spec/`.
- Design, implementation, failing tests, or docs-sync work (later phases).

---

## 3. Behavior Definition

### What this change does

It extends two process artifacts and one agent-prompt artifact so that portability impact is a required analysis at pre-flight time, not an optional consideration at implementation time:

- `docs/process/00-preflight.md` — template agents fill out for every change
- `docs/process/run-change.md` — human/agent workflow checklist
- `docs/process/llm-prompts.md` — LLM prompt template blocks

### Inputs

The author of a pre-flight (human or agent) must answer every field in the PORTABILITY ANALYSIS block before the pre-flight is considered complete.

### Outputs

A pre-flight document that:
- Contains a PORTABILITY ANALYSIS block with every required field answered.
- Answers are grounded in `GENIA_STATE.md` facts — no speculation about unimplemented hosts.
- Identifies at least one portability zone for the change.
- Explicitly states whether Core IR is affected.
- Explicitly states which shared spec categories, if any, must be updated.

### State changes

No runtime state changes. The template files are text documents. The workflow guides are human/agent-readable instructions.

---

## 4. PORTABILITY ANALYSIS Block — Required Fields

The PORTABILITY ANALYSIS block is a required new section in `docs/process/00-preflight.md`.

### Placement

The block appears as a new numbered section between the existing section 3 (FEATURE MATURITY) and the existing section 4 (CONTRACT vs IMPLEMENTATION).

The existing sections 4 through 10 retain their current labels. The new section is labeled:

```
3a. PORTABILITY ANALYSIS
```

Using label `3a` avoids renumbering existing sections and preserves backward compatibility with prior issue references that use section numbers 4–10.

### Required fields (every pre-flight must answer all seven)

---

**Field 1: Portability zone**

Label: `Portability zone:`

Required: YES

Definition: Identifies which architectural zone this change primarily affects.

Valid values (one or more, comma-separated):

- `language contract` — behavior all hosts must implement; enters shared spec
- `Core IR` — change introduces or modifies a portable IR node family
- `prelude` — behavior lives in `.genia` stdlib source; portable if no host calls
- `Python reference host` — Python-only, host-backed behavior
- `host adapter` — the shared harness boundary (`run_case` interface)
- `shared spec` — affects what `spec/*` YAML cases assert
- `docs/tests only` — no runtime or contract change; process, documentation, or test-only

Rule: At least one value must be stated. If multiple zones are affected, the pre-flight must note whether the change is being split per the `AGENTS.md` one-zone-per-change rule or explicitly justified.

---

**Field 2: Core IR impact**

Label: `Core IR impact:`

Required: YES

Required answer form:
- `none` — change does not affect portable Core IR node families
- `yes — <describe which node families or lowering rules change>` — change introduces or modifies portable IR nodes

Rule: "none" is the correct answer for any change confined to prelude, host-backed behavior, docs, or tests. "yes" requires naming the affected `Ir*` node families and whether the change is an addition or modification.

Forbidden answer: vague statements like "possibly" or "TBD". A pre-flight cannot proceed to spec if this is unresolved.

---

**Field 3: Capability categories affected**

Label: `Capability categories affected:`

Required: YES

Valid values: one or more from the fixed set, or "none":
- `parse`
- `ir`
- `eval`
- `cli`
- `flow`
- `error`
- `none` (for pure docs/process changes)

Rule: List every category whose shared spec observable surface changes. If the answer is "none", state it explicitly. Do not omit this field.

---

**Field 4: Shared spec impact**

Label: `Shared spec impact:`

Required: YES

Required answer form: One of:
- `none — no new shared spec cases required`
- `new cases required in spec/<category>/` — state which category directories will need new YAML cases and what observable behavior they will assert
- `existing cases may need update in spec/<category>/` — describe what is expected to change

Rule: This field must be answered consistently with field 3 (Capability categories affected). If a capability category is listed as affected, shared spec impact cannot be "none" unless a justification is given (e.g., the change is prelude-only and existing spec cases already cover it).

---

**Field 5: Python reference host impact**

Label: `Python reference host impact:`

Required: YES

Required answer form: One of:
- `none — Python host behavior is unchanged`
- `yes — <describe what changes in the Python reference host>` — describe which files in `src/genia/` or `hosts/python/` change and what behavior changes

Rule: This must be answered honestly. Python-host-only behavior must be labeled as such. Do not claim something is a "language contract" change if it only affects the Python implementation.

---

**Field 6: Host adapter impact**

Label: `Host adapter impact:`

Required: YES

Required answer form: One of:
- `none — host adapter interface is unchanged`
- `yes — <describe what changes at the adapter boundary>`

Rule: The host adapter boundary is `hosts/python/adapter.py::run_case(spec: LoadedSpec) -> ActualResult`. Changes to this interface or the normalization contract it enforces must be stated here.

---

**Field 7: Future host impact**

Label: `Future host impact:`

Required: YES

Required answer form:
- If the portability zone includes `language contract`, `Core IR`, or `prelude` (without host calls): describe what a future non-Python host must implement to pass the relevant shared spec cases.
- If the portability zone is `Python reference host` only: state `Python-host-only; future hosts are not affected in the current phase.`
- If the portability zone is `docs/tests only`: state `none — no future host impact.`

Rule: This field must not claim that future hosts are implemented or that they currently pass any spec cases. It is a forward-looking planning note grounded in honest current status.

---

## 5. Sufficient Portability Analysis — By Change Class

The following defines what counts as sufficient analysis for each class of change:

### Process/documentation-only change

Sufficient when:
- Portability zone is `docs/tests only` (or a mix that includes it but no runtime zones)
- Core IR impact is `none`
- Capability categories affected is `none`
- Shared spec impact is `none`
- Python reference host impact is `none`
- Host adapter impact is `none`
- Future host impact is `none`

### Prelude-only change (`.genia` stdlib, no host calls)

Sufficient when:
- Portability zone includes `prelude`
- Core IR impact is stated (usually `none` for pure prelude)
- Capability categories affected lists at least `eval` (since prelude functions are exercised in eval)
- Shared spec impact states whether existing eval/flow cases cover the behavior or new cases are needed
- Python reference host impact states whether the prelude change is implemented via new `.genia` source only or requires a new Python-backed builtin
- Future host impact states that any future host loading the same prelude `.genia` source will inherit the behavior without additional host implementation (or explicitly notes any host-backed dependency)

### Python-host-backed runtime change

Sufficient when:
- Portability zone includes `Python reference host` and is clearly labeled as such
- Core IR impact is explicitly `none` unless the change enters Core IR
- Capability categories affected lists all affected categories
- Python reference host impact describes the specific files and behaviors changing
- Future host impact explicitly states the behavior is Python-host-only in the current phase and that future hosts must implement equivalent host-backed support to pass the relevant spec cases

### Core IR change

Sufficient when:
- Portability zone includes `Core IR`
- Core IR impact names the specific `Ir*` node families affected
- Capability categories affected includes `ir` at minimum
- Shared spec impact states that `spec/ir/` cases will need to cover the new or modified node families
- Future host impact explicitly describes what a new host's lowering pass must produce for the affected forms

### Language contract change (new syntax or semantics)

Sufficient when:
- Portability zone includes `language contract`
- Core IR impact is explicitly answered (YES with detail, or NO with justification)
- All affected capability categories are listed
- Shared spec impact names which category directories require new cases
- Python reference host impact describes the implementation changes
- Future host impact describes the full required host implementation surface

---

## 6. What Must Never Be Claimed

The portability analysis section must not contain any of the following:

- Claims that Node.js, Java, Rust, Go, C++, or browser-native hosts are implemented or passing spec cases. They are planned/scaffolded only.
- Claims that a Core IR change has been validated against multiple hosts. Only the Python reference host is implemented.
- Claims that prelude behavior is "fully portable" without acknowledging any host-backed dependencies.
- Vague or deferred answers such as "TBD", "to be determined in spec", or "depends on implementation". Every field must be answered at pre-flight time.
- Claims that a Python-host-only behavior is part of the language contract unless `GENIA_STATE.md` already states it as such.
- Claims of future host support that exceed what `GENIA_STATE.md` states as planned.

Any pre-flight containing the above is considered incomplete and must be revised before spec begins.

---

## 7. Workflow Guide Requirements

### `docs/process/run-change.md` — required addition

The workflow guide must add an explicit note at step 2 (Run preflight prompt) stating:

> Pre-flight must include a PORTABILITY ANALYSIS block (section 3a). The portability analysis must be complete before the spec phase begins. Incomplete portability analysis is grounds for blocking the spec step.

### `docs/process/llm-prompts.md` — required addition

The preflight section of the LLM prompt template must include:

> After section 3 (FEATURE MATURITY), complete section 3a (PORTABILITY ANALYSIS). All seven fields are required. Do not proceed to spec without answering them.

The LLM prompt must also list the seven required fields by name so an agent can produce a conforming pre-flight without consulting a separate document.

---

## 8. Validation

### How the requirement is validated

**Manual review (primary):**

Before a spec phase commit is accepted, a reviewer (human or audit agent) checks that the committed pre-flight document contains section `3a. PORTABILITY ANALYSIS` with all seven field labels present and non-empty answers.

**Prohibited answer strings (audit check):**

Any pre-flight containing the following strings fails the portability analysis validation check:
- `"TBD"` in any portability field
- `"to be determined"` in any portability field
- `"Node.js is implemented"` or equivalent host-availability claims
- `"Java is implemented"` / `"Rust is implemented"` / `"Go is implemented"` / `"C++ is implemented"`
- `"all hosts"` used without qualification (must be `"all currently implemented hosts"` or equivalent)

**No machine-asserted test change required for this issue:**

`tests/test_semantic_doc_sync.py` covers protected semantic facts in `docs/contract/semantic_facts.json`. The pre-flight template (`docs/process/00-preflight.md`) is not currently a source of machine-asserted facts. Adding test coverage for the template structure is out of scope for this issue. A future issue may add such coverage if the process docs grow in stability and importance.

---

## 9. Invariants

Every pre-flight document in this repository must, after this change is implemented:

1. Contain a section labeled `3a. PORTABILITY ANALYSIS`.
2. Contain all seven field labels: `Portability zone:`, `Core IR impact:`, `Capability categories affected:`, `Shared spec impact:`, `Python reference host impact:`, `Host adapter impact:`, `Future host impact:`.
3. Provide a non-empty answer for each field.
4. Not claim unimplemented hosts are implemented.
5. Not use deferred answers (TBD) in any field.
6. Answer `Core IR impact:` with either `none` or a named node family — no vague answers.
7. Answer `Future host impact:` consistently with the `Portability zone:` answer.

Workflow guidance invariants:

8. `docs/process/run-change.md` must state portability analysis is required before spec.
9. `docs/process/llm-prompts.md` must include the portability analysis block in its preflight section.

---

## 10. Examples

### Minimal example — process-only change

```
3a. PORTABILITY ANALYSIS

Portability zone: docs/tests only
Core IR impact: none
Capability categories affected: none
Shared spec impact: none
Python reference host impact: none
Host adapter impact: none
Future host impact: none — no future host impact.
```

### Example — prelude-only change (new `map` helper)

```
3a. PORTABILITY ANALYSIS

Portability zone: prelude
Core IR impact: none
Capability categories affected: eval
Shared spec impact: new cases required in spec/eval/ to cover the new helper's observable output
Python reference host impact: none — implemented as pure .genia prelude code; no new Python builtin required
Host adapter impact: none
Future host impact: any future host that autoloads the same prelude .genia source will inherit this behavior without additional host implementation.
```

### Example — Python-host-only runtime change (HTTP serving)

```
3a. PORTABILITY ANALYSIS

Portability zone: Python reference host
Core IR impact: none
Capability categories affected: none (no shared spec coverage for HTTP serving in this phase)
Shared spec impact: none — HTTP serving is Python-host-only and not covered by shared semantic specs
Python reference host impact: yes — modifies serve_http builtin behavior in src/genia/
Host adapter impact: none — adapter interface is unchanged
Future host impact: Python-host-only in the current phase. Future hosts that support HTTP serving must implement equivalent host-backed primitives; no shared spec cases exist today for this capability.
```

### Example — Flow-stage feature (affects shared spec)

```
3a. PORTABILITY ANALYSIS

Portability zone: prelude, shared spec
Core IR impact: none — Flow stages do not introduce new Core IR nodes
Capability categories affected: flow
Shared spec impact: new cases required in spec/flow/ to prove observable behavior of the new stage
Python reference host impact: yes — new prelude .genia source backed by the existing Python Flow kernel; no new Python builtin required
Host adapter impact: none
Future host impact: any future host implementing the lazy pull-based Flow kernel and loading the same prelude source must pass the new spec/flow/ cases.
```

---

## 11. Non-Goals

- This spec does not define machine-asserted test coverage for the pre-flight template structure.
- This spec does not add a new host or capability.
- This spec does not change Core IR.
- This spec does not change runtime behavior.
- This spec does not rename existing sections 4–10 of the pre-flight template.
- This spec does not require retroactive updates to existing pre-flight documents already committed on closed issues.

---

## 12. Implementation Boundary

This spec describes documentation structure and workflow guidance — no host-specific behavior is involved. The required output of the implementation phase is:

- Updated `docs/process/00-preflight.md` with the `3a. PORTABILITY ANALYSIS` section, all seven field labels, field definitions, and valid-value guidance.
- Updated `docs/process/run-change.md` with a note that portability analysis is required before spec.
- Updated `docs/process/llm-prompts.md` with the seven field names in the preflight prompt block.

No runtime files, spec YAML files, or test files change as a result of this spec.

---

## 13. Doc Requirements

No `GENIA_STATE.md` update is required. This change does not alter any implemented language behavior or host capability.

The updated pre-flight template must:
- Label the new section `3a. PORTABILITY ANALYSIS` (not "OPTIONAL", not "IF APPLICABLE")
- Mark each field as required with a brief definition
- Include the valid-value lists for fields 1, 2, and 3
- Include one minimal process-change example inline so agents can confirm the format
- Not claim future hosts are implemented

---

## 14. Complexity Check

Classification: Minimal and Necessary.

Justification:
- Seven fields added to a template. No new phases. No new runtime behavior.
- The fields formalize questions that should already be answered at pre-flight but are currently implicit.
- The benefit is proportional: catching host-vs-language boundary confusion at planning time costs nothing compared to discovering it at implementation or audit time.

---

## 15. Final Check

- No implementation details: YES — spec describes only what the template must contain and what the workflow docs must say, not how to edit them.
- No scope expansion: YES — confined to process doc changes in `docs/process/`.
- Consistent with `GENIA_STATE.md`: YES — all examples and field definitions are grounded in current implemented-host facts.
- Behavior is precise and testable: YES — the seven fields are named; valid values are listed; prohibited answers are listed; placement is specified.
