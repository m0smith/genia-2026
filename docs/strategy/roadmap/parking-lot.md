# Parking Lot and Historical Issue Disposition

Status: Planning history — non-authoritative. `GENIA_STATE.md` remains final authority for implemented behavior.

## Parking Lot / Later

These are valuable, but not part of the near roadmap unless explicitly promoted:

- actor system
  - includes actor lifecycle, supervision, and actor-oriented runtime expansion
  - keep out of R5 unless a narrow use case explicitly requires it
- open functions / extensible pattern dispatch — **promoted to planned R19**
  - R19 now owns the local repeated-clause and explicit cross-module extension contract described in [`r16-r20.md`](r16-r20.md)
  - historical motivating local example:

    ```genia
    gcd(a, 0) = a
    gcd(a, b) = gcd(b, a % b)
    ```

  - historical motivating cross-module interface example, syntax deliberately not yet locked:

    ```genia
    # common/storage surface
    get(MemoryStore(store), key) = memory_get(store, key)

    # future database module contribution
    extend get(Database(db), key) = db_get(db, key)
    ```

  - promoted invariants retained by R19:
    - local repeated compatible clauses form one named-function group rather than accidental rebinding
    - cross-module extension must be explicit; importing a module must not silently overwrite or mutate an unrelated visible function
    - dispatch remains pattern-based and preserves existing fixed-arity-over-varargs precedence
    - unrelated module import order must not decide dispatch results
    - when multiple cross-module clauses match and no deterministic specificity rule chooses one, evaluation must fail with a deterministic ambiguity error
    - each contributed clause retains module provenance for diagnostics, introspection, and future reload/unload design
    - loading/importing a module remains inert with respect to lifecycle activation, resource acquisition, and network/process side effects
    - the semantic contract must be host-agnostic and shared-spec driven; no Python-only dispatch rule may define the feature
  - open functions remain the first concept; a named protocol/interface layer, if ever needed, stays separate from R19 unless its own later gate promotes it
  - the example `extend` spelling, protocol syntax, specificity algorithm, module unloading, and implementation strategy remain unapproved until the R19 contract/design gates settle them
- browser playground runtime
  - useful as a future demo surface, not required for the first validated-data-pipeline release
- ants / simulation teaching demos
  - useful teaching material after the data-pipeline wedge is demonstrable
- value-template work outside the focused R9/R15 structural and validated-value scope
  - R9 and R15 are complete; new Template work requires later-release or follow-up classification
- nominal variants / closed constructor identity / exhaustiveness
  - R15 delivered structural discriminated alternatives only
  - nominal variant identity, constructor objects or syntax, sealed/closed nominal hierarchies, and exhaustiveness checking remain deferred
  - do not smuggle this work into R25/R26 shaped or relational Sheet semantics
- broad function contracts beyond the Template/validation boundaries already implemented
  - promote only when a concrete API-boundary use case proves the need
- purity / effect metadata
  - R25 may define only the minimum observable independence rules required for shaped computation
  - do not add `pure`, effect rows, an effect type system, or optimizer-facing user syntax unless concrete optimization/tooling use cases prove that existing semantics are insufficient
- module instances / initialized components
  - future distinction: import/load remains inert definition/namespace loading; explicit initialization may later create independent runtime instances with lifecycle-owned resources
  - do not mutate the module cache into runtime instance state
  - exact `init`/`start`/`stop` naming and module-instance representation remain unapproved
- validation DSL
  - do not create implementation tickets until helper-based validation proves insufficient
- Node, Java, Rust, and Go host implementation beyond contract scaffolding
  - generic runner and shared portability hardening are promoted to R16–R18
  - open-function semantics are promoted to R19 before the first second-host implementation
  - C++ host implementation is promoted to R20–R23
- server mode
  - **Web ergonomics promoted to R7**, and the **serve execution mode promoted to R8** (Server Execution Mode — the second R4 lifecycle consumer, `@server`/`@route`/`@cors` bound to R7 primitives). Idea capture: `docs/parking-lot/web-backend-cfm-app.md` (R7) and `docs/parking-lot/server-execution-mode.md` (R8). Anything beyond those two remains parked.
- notebook mode
- parallel native test execution
- package manager / public package registry
  - R28 may improve local project/tooling ergonomics but must not introduce package-distribution semantics without separate ecosystem pressure and its own contract/process work
- **#102** — broad scope; should be split into smaller targeted tickets or updated before use as a release tracker; do not use as a release blocker in its current form

## Promoted post-R24 data-workflow work

The following ideas are no longer parking-lot-only and now have planned release homes in [`r25-r29.md`](r25-r29.md):

- shaped whole-column computation, scalar lifting, and shape conformance → **R25**
- grouping, summarization, ordering, and explicit joins over Sheets → **R26**
- one explicit parameterized database source/sink boundary → **R27**
- formatter/editor/navigation/diagnostic tooling hardening → **R28**
- reproducible Python/C++ performance evidence and evidence-driven optimization → **R29**

Roadmap placement does not approve syntax or behavior; each release still requires its own contract/design/failing-test/implementation/documentation/audit gates.

---

## Post-R1 Issue Disposition

This section records the classification of R1-adjacent issues after R1 completion.

| Issue | Classification | Notes |
|---|---|---|
| #374 | **Closed / completed** | Delivered as part of R1. |
| #405 | R6 diagnostic-context hardening | Keep open; schedule in R6. |
| #393 | R6 diagnostics hardening | Keep open; schedule in R6. |
| #394 | Conditional / deferred | Keep open; promote when need is concrete. |
| #390 | R6 — CSV support | Keep open; schedule in R6. |
| #395 | R6 — Sheet landing zone | Keep open; schedule in R6. |
| #396 | R6 — after #395 | Keep open; depends on Sheet landing zone. |
| #363 | R6 — delivered | `row_get(row, column_name)` ergonomic row access shipped. |
| #364 | R6 — after Sheet landing zone | Keep open; schedule after #395. |
| #399 | R9 E9-1 — delivered | Minimal callable Template foundation implemented over Outcome matchers. |
| #87 / #89 / #90 | R9 — delivered | R9 epic, open-shape, and exact-shape work completed through the approved E9 sequence. |
| #91 | Later release / follow-up | Broad function contracts were not required by R9 and are not a release blocker. |
| #92 | Partially delivered (R15 E15-5 / #732); remainder deferred | Only structural discriminator-directed validation was promoted into R15 as `alternatives(discriminator, branches)`. Nominal variant identity, constructor objects/syntax, sealed/closed nominal hierarchies, and exhaustiveness checking remain deferred and are not implemented. |
| #102 | Needs split or update | Do not use as a broad release blocker; split first. |

If an issue listed above is already closed, do not reopen it.

Possible future generated-helper idea:

- record-derived `with_*` helper generation
  - possible future opt-in form: `@derive(quote(withers))`
  - generated helpers must be namespaced under the record/template
  - generated helpers must not create global `with_*` functions
