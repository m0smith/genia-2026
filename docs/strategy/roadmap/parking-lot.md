# Parking Lot and Historical Issue Disposition

Status: Planning history — non-authoritative. `GENIA_STATE.md` remains final authority for implemented behavior.

## Parking Lot / Later

These are valuable, but not part of the near roadmap unless explicitly promoted:

- actor system
  - includes actor lifecycle, supervision, and actor-oriented runtime expansion
  - keep out of R5 unless a narrow use case explicitly requires it
- open functions / extensible pattern dispatch
  - future language-semantics candidate for allowing named functions to accumulate independently declared pattern clauses and, later, for modules to explicitly contribute additional clauses to a shared function interface
  - motivating local example:

    ```genia
    gcd(a, 0) = a
    gcd(a, b) = gcd(b, a % b)
    ```

  - motivating cross-module interface example, syntax deliberately not yet locked:

    ```genia
    # common/storage surface
    get(MemoryStore(store), key) = memory_get(store, key)

    # future database module contribution
    extend get(Database(db), key) = db_get(db, key)
    ```

  - required invariants before promotion:
    - local repeated compatible clauses form one named-function group rather than accidental rebinding
    - cross-module extension must be explicit; importing a module must not silently overwrite or mutate an unrelated visible function
    - dispatch remains pattern-based and preserves existing fixed-arity-over-varargs precedence
    - unrelated module import order must not decide dispatch results
    - when multiple cross-module clauses match and no deterministic specificity rule chooses one, evaluation must fail with a deterministic ambiguity error
    - each contributed clause retains module provenance for diagnostics, introspection, and future reload/unload design
    - loading/importing a module remains inert with respect to lifecycle activation, resource acquisition, and network/process side effects
    - the semantic contract must be host-agnostic and shared-spec driven; no Python-only dispatch rule may define the feature
  - open functions are the first concept; a named protocol/interface layer, if ever needed, should be considered separately after the dispatch mechanism proves useful
  - do not treat the example `extend` spelling, protocol syntax, specificity algorithm, module unloading, or implementation strategy as approved design
  - keep out of R16 unless an approved pre-flight demonstrates that multi-host conformance infrastructure actually depends on it
- browser playground runtime
  - useful as a future demo surface, not required for the first validated-data-pipeline release
- ants / simulation teaching demos
  - useful teaching material after the data-pipeline wedge is demonstrable
- value-template work outside the focused R9 structural/representation scope
  - R9 is complete; new Template work requires later-release or follow-up classification
- refinement / shape / contract / variant work beyond the subset required to prove R9
- validation DSL
  - do not create implementation tickets until helper-based validation proves insufficient
- Node, Java, Rust, and Go host implementation beyond contract scaffolding
  - generic runner and shared portability hardening are promoted to R16–R18
  - C++ host implementation is promoted to R19–R22
- server mode
  - **Web ergonomics promoted to R7**, and the **serve execution mode promoted to R8** (Server Execution Mode — the second R4 lifecycle consumer, `@server`/`@route`/`@cors` bound to R7 primitives). Idea capture: `docs/parking-lot/web-backend-cfm-app.md` (R7) and `docs/parking-lot/server-execution-mode.md` (R8). Anything beyond those two remains parked.
- notebook mode
- parallel native test execution
- **#102** — broad scope; should be split into smaller targeted tickets or updated before use as a release tracker; do not use as a release blocker in its current form

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
