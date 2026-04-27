# === GENIA PRE-FLIGHT ===

CHANGE NAME: <short name of change>

---

You are working in the Genia repo.

Before doing anything, read:
- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md

GENIA_STATE.md is the final authority when files conflict.

Do not invent implemented behavior.
Do not expand scope.
Do not introduce new syntax unless the spec explicitly requires it.
Keep documentation truthful and current.
If this change affects behavior, update relevant tests and docs.

---

--------------------------------
HARD STOP — PRE-FLIGHT ONLY
--------------------------------

You MUST STOP after producing the pre-flight output.

You are NOT allowed to:
- create branches
- run tests
- write spec files
- modify any files
- run the spec runner
- commit anything
- proceed to spec/design/implementation/audit

If you do any of the above, the response is INVALID.

After pre-flight, WAIT for the next prompt.

Do NOT assume the next step.

If you find yourself writing YAML, code, or running commands,
you have already gone too far. Stop immediately.

---

0. BRANCH

---

Branch required:
YES

Branch type:
[ ] feature
[ ] fix
[ ] refactor
[ ] docs
[ ] exp

Branch slug: <short-kebab-name>

Expected branch: <branch-type>/<branch-slug>

Base branch:
main

Rules:

* No work begins on `main`
* Branch must be created before Spec
* One branch per change

---

1. SCOPE LOCK

---

## Change includes:

## Change does NOT include:

---

2. SOURCE OF TRUTH

---

Authoritative files:

* GENIA_STATE.md (final authority)
* GENIA_RULES.md
* README.md
* AGENTS.md

## Additional relevant:

## Notes:

---

3. FEATURE MATURITY

---

Stage:
[ ] Experimental
[ ] Partial
[ ] Stable

## How this must be described in docs:

---

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

4. CONTRACT vs IMPLEMENTATION

---

## Contract (portable semantics):

## Implementation (Python today):

## Not implemented:

---

5. TEST STRATEGY

---

## Core invariants:

## Expected behaviors:

## Failure cases:

## How this will be tested:

---

6. EXAMPLES

---

## Minimal example:

## Real example (if applicable):

---

7. COMPLEXITY CHECK

---

Is this:
[ ] Adding complexity
[ ] Revealing structure

## Justification:

---

8. CROSS-FILE IMPACT

---

## Files that must change:

*

Risk of drift:
[ ] Low
[ ] Medium
[ ] High

---

9. PHILOSOPHY CHECK

---

Does this:

* preserve minimalism? YES / NO
* avoid hidden behavior? YES / NO
* keep semantics out of host? YES / NO
* align with pattern-matching-first? YES / NO

## Notes:

---

10. PROMPT PLAN

---

Will use full pipeline?
YES

Steps:

* Preflight
* Spec
* Design
* Test
* Implementation
* Docs
* Audit

---

## FINAL GO / NO-GO

Ready to proceed?
YES / NO

## If NO, what is missing:
