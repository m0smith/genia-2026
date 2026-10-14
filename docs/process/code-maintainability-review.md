# Code Quality & Human-Maintainability Review

Status: required **process gate** for changes following the full lifecycle in [run-change.md](run-change.md). This is not a new Genia semantic contract, test phase, or release gate.

## Position and responsibility

Run this review **after implementation and its tests have been committed, before documentation synchronization and the independent truth audit**. A reviewer other than the implementer is preferred where available. If the same person or agent must review, disclose that limitation and perform a distinct skeptical pass of the actual diff. A summary-only or self-certification review is insufficient.

The reviewer checks whether a competent human maintainer can safely understand, debug, extend, and change the code. Passing tests is necessary evidence but does not by itself pass this review. The final truth audit remains independently required.

## Inspect the actual code

Review the changed diff together with adjacent call sites, existing local conventions, tests, and relevant architectural contracts. Apply the categories that genuinely matter to the change:

- **Readability:** direct control flow, meaningful names, small comprehensible units, clear invariants, non-misleading comments; public and non-obvious functions have useful documentation, including argument, return, error, and side-effect contracts as applicable.
- **Cohesion and architecture:** each module/function has a clear responsibility; changes fit existing abstractions and do not duplicate mechanisms, smuggle host-specific semantics into portable boundaries, or bypass designated interfaces.
- **Complexity and duplication:** avoid needless indirection, speculative generality, sprawling conditionals, repeated logic, hidden state, and clever tricks that obscure reasoning. Prefer proportionate, localized changes.
- **Idiomatic implementation:** follow established Python, C++, and Genia conventions, as applicable; check lifetime/ownership, mutation, resource cleanup, recursion/Flow/Outcome usage, error normalization, and diagnostic hygiene where relevant.
- **Testability and change safety:** tests exercise meaningful failure paths and exposed contracts; dependencies and side effects remain controllable; the code is debuggable; no tests are weakened merely to make a patch pass.
- **Scope and operational fitness:** no unrelated refactoring or formatting churn; performance, boundedness, concurrency, security/privacy, and resource handling receive attention according to risk.

This is a **substantive maintainability** gate, not a subjective style contest. Automated formatting and lint checks may support the review but cannot substitute for it. For low-risk documentation-only or trivial non-code edits, record a brief **not applicable** determination with rationale rather than inventing code-review evidence. Changes that skip full pre-flight under run-change.md do not automatically require a heavyweight new phase.

## Evidence and handoff

Use the established `.genia/process/tmp/handoffs/<change-slug>/` handoff convention and record a maintainability-review handoff after the implementation handoff, without replacing existing contract/design/test/docs/audit artifacts. Include:

- Issue/PR, commit or diff range reviewed, affected paths and tests considered.
- Reviewer identity and independence (or disclosed limitation).
- Checklist areas assessed and any deliberately not applicable, with reasons.
- Findings with **severity (blocking / non-blocking)**, exact file/line or diff location, explanation, and actionable correction.
- Disposition of each finding: fixed and re-reviewed, or non-blocking follow-up with a tracked issue/reference and owner as appropriate.
- One explicit verdict: **PASS**, **PASS WITH NON-BLOCKING FINDINGS**, or **FAIL**.

**FAIL blocks progression to docs sync and merge.** Fix blocking findings and re-review the relevant diff before changing the verdict. **PASS WITH NON-BLOCKING FINDINGS** may proceed only when each deferred item is explicitly recorded and owned/tracked; do not silently discard findings. A **PASS** requires no blocking or untracked findings. A pending or missing review is not a PASS.

## Boundaries

Do not change language behavior, design contracts, conformance expectations, or documentation truth to make code superficially cleaner. If the review finds a genuine semantic/design issue, return to the appropriate earlier phase and update tests and authoritative docs through the normal process. Keep this gate distinct from security review, testing, documentation synchronization, and the final skeptical truth audit. For reviews spanning the C++ host repository, retain the same recorded judgment and portability constraints in the affected repository.
