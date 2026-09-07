# R15 Kickoff — Validated Value Modeling

Status: **Historical — R15 is complete (E15-0 through E15-9). Planning-only; non-authoritative.**

This document prepares R15 for its first process gate. It does not define implemented language behavior. `GENIA_STATE.md` remains final authority.

## Tracking

- Epic: #725 — R15 — Validated Value Modeling
- First gate: #726 — E15-0 — contract, roadmap reconciliation, and capability inventory
- Detailed planning: `docs/strategy/r15-validation-modeling.md`

## Start condition

R14 is release-complete. R15 is therefore the current release to prepare, but **only E15-0 is authorized to begin**. No E15-1+ behavior is implemented or authorized by this kickoff.

E15-0 must reconcile the current implementation against R9, R10, R13, and R14 before locking the R15 contract.

## Required source reading

Before work begins, read completely and follow:

1. `AGENTS.md`
2. `GENIA_STATE.md`
3. `GENIA_RULES.md`
4. `GENIA_REPL_README.md`
5. `README.md`
6. `docs/strategy/killer-workflow.md`
7. `docs/strategy/release-roadmap.md`
8. `docs/strategy/r15-validation-modeling.md`
9. `docs/process/08-roadmap-ticketing.md`
10. relevant R9/R10/R13/R14 contract/design documents
11. `docs/design/composability-matrix.md`

When sources conflict, follow the truth hierarchy in `AGENTS.md`; `GENIA_STATE.md` is final authority for implemented behavior.

## E15-0 decisions that must be locked before E15-1

- inspectable Template descriptions are inert and supported-constructor-only; arbitrary callable Templates remain opaque
- defaults are explicit and missing-only; present invalid values do not fall back
- normalization/conversion remains an ordinary explicit transformation, not Template coercion
- accumulated validation is explicit and cannot alter ordinary first-match pattern semantics
- diagnostic paths and ordering are deterministic and cannot reveal protected payloads
- lazy Flow validation remains bounded and does not over-pull or buffer an entire source implicitly
- Template → JSON Schema is faithful for a declared subset or fails explicitly; no approximation
- structural alternatives use an explicit discriminator and deterministic one-branch selection without nominal variant identity
- recursive Template references use an explicit validation-local environment and deterministic bounds; no global registry or lifecycle/config ambient state
- Template descriptions, diagnostics, defaults, and schema generation preserve R10 protected-value boundaries
- R13 configuration and R14 lifecycle context remain explicit; validation metadata must not become dependency injection

## Scope boundary

R15 extends the existing R9 Template/representation model. It must not create:

- `BaseModel`-style model instances
- a parallel validation result hierarchy
- broad implicit coercion
- nominal variants, constructors, or exhaustiveness checking
- a general validation DSL
- lifecycle-owned validation state
- ambient configuration lookup
- arbitrary cyclic object-graph validation
- approximate JSON Schema generation

The structural-discrimination portion of #92 may be reconciled into R15; the nominal ADT portion remains deferred.

## Process stop

E15-0 is contract/preflight work only. It may update planning/contract/process artifacts and reconcile roadmap status, but it must not claim or implement E15-1+ runtime behavior.

The next authorization after an approved E15-0 handoff is **E15-1 only**.

## Documentation discipline

Any Codex/agent prompt used for R15 must explicitly require keeping the repository documentation current as work lands, especially `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, the release roadmap, release examples, and the composability matrix where affected. Planned behavior must never be written into implemented-truth docs before it is implemented and tested.
