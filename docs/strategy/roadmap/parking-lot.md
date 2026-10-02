# Parking Lot and Historical Issue Disposition

Status: Planning history — non-authoritative. `GENIA_STATE.md` remains final authority for implemented behavior.

## Parking Lot / Later

These are valuable, but not part of the near roadmap unless explicitly promoted:

- Outcome composition ergonomics — **promoted to a near-term cross-cutting follow-up candidate**
  - motivating problem: ordinary application code should not need pervasive `apply_raw` to express full-Outcome composition
  - first contract candidate: a canonical full-Outcome bind/composition helper, working name `flat_map_outcome`
  - intended narrow behavior: `some(value)` invokes the step; `none(...)` and `err(...)` are preserved unchanged
  - preserve the existing distinction between direct-call propagation and pipeline short-circuiting; this item does not authorize a pipeline stage that intercepts `err(...)`
  - do not broaden `flat_map_some`, add arbitrary propagation-control annotations, or create a second invocation model
  - configuration/domain values that intentionally encode absence must remain explicit; this helper must not become a workaround for unclear modeling
  - directly supports the Outcome-aware validated-data-pipeline north star and later HTTP, AI, storage, and database composition
  - no release number is assigned yet; schedule through the normal contract/design/failing-test/implementation/docs/audit/distillation gates before implementation
- HTTP server and outbound HTTP portable contracts
  - R27 deliberately deferred both surfaces after contract-decision issues #1041 and #1043; see `docs/analysis/r27-http-server-decision.md` and `docs/analysis/r27-outbound-http-decision.md`
  - future work needs its own release assignment before implementation starts
  - server prerequisites include a portable request/response shape, listener authority model, a test-runner route for served requests, and C++ support for import, annotations, serve mode, and sockets
  - outbound prerequisites include host authority/declassification, a deterministic transport fixture mechanism, protected values, lifecycle/config interaction, and cross-host failure-taxonomy evidence
  - do not treat either capability as an R27 follow-up implementation task
- actor system
  - includes actor lifecycle, supervision, and actor-oriented runtime expansion
  - keep out of R5 unless a narrow use case explicitly requires it
- execution realizations / transport-independent distributed execution
  - long-term direction: Genia describes logical computation separately from physical execution topology and infrastructure realization
  - desired development path is local-first execution that may later move to processes, workers, durable queues, brokers, or cloud infrastructure without rewriting application-level transformation/business logic when the required semantics remain compatible
  - local collections, local queues, SQS, Kafka, and other transports must not be treated as inherently equivalent; ordering, delivery, durability, acknowledgement, replay, partitioning, retry, and failure guarantees must remain explicit
  - placement may eventually be abstracted; distributed failure semantics must not be hidden
  - future work will need a portable-value boundary for values crossing execution boundaries, but no such new language mechanism is approved here
  - effects, retries, idempotency, and uncertain completion must be addressed before distributed effectful work is promoted
  - local realizations should remain first-class and may eventually support distributed-failure simulation for testing
  - deployment may eventually use Ansible, Terraform, Kubernetes, cloud APIs, or another provisioning mechanism; none is part of Genia semantics
  - host portability and execution distribution are separate axes
  - do not create implementation tickets until a concrete workflow demonstrates the need and a contract answers the semantic questions in `docs/architecture/execution-realization.md`
- unified Function model and open-function repairs — **promoted as the primary R20 follow-up; issue #1067**
  - schedule after R28 and before R29 without assigning a new release number or expanding R28
  - preserve ordinary functions as closed by default and preserve `open` as the explicit declaration that an API is a cross-module extension point
  - first re-validate and repair the concrete R20 defects recorded by PR #1066: contribution identity/storage and export leakage, open-function/view TCO, per-stratum Outcome/none-awareness, grouped-header binder behavior, open docstrings, and diagnostics
  - gate module entry-scope isolation separately because it affects the broader module model and needs a compatibility survey
  - only after those repairs, contract/design a single internal Function/Clause dispatch model if evidence still shows a material simplification; do not require a breaking portable Core IR change
  - preserve `extend` and `use` semantics unless a separately approved contract changes them
  - require shared conformance evidence and exact Python/C++ capability claims for every portable semantic repair
  - defer breaking Core IR consolidation to R41 or another separately approved versioned-IR gate
  - `docs/analysis/unified-function-model-contract-gate-DRAFT.md` is proposed/non-authoritative input; #1067 is GO for contract/evidence and NO-GO for implementation until its missing decisions/evidence are closed
- open-function declaration ergonomics — **optional later R20 surface-design candidate, subordinate to #1067**
  - keep ordinary functions closed by default; do not make every function an open multimethod
  - preserve the architectural meaning of `open`: the declaring API is intentionally an extension point
  - clause-less declarations such as `open f(x)` and grouped declaration shorthand may be reconsidered only after #1067 settles the underlying Function model
  - any syntax work requires its own gate and must not change dispatch, ambiguity, provenance, linking, `extend`, or `use` implicitly
  - protocols, traits, typeclasses, implementation blocks, nominal interface identity, implicit conformance, and receiver dispatch remain parked separately
- open functions / extensible pattern dispatch — **promoted to planned R20**
  - R20 now owns the local repeated-clause and explicit cross-module extension contract described in [`r16-r20.md`](r16-r20.md)
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

  - promoted invariants retained by R20:
    - local repeated compatible clauses form one named-function group rather than accidental rebinding
    - cross-module extension must be explicit; importing a module must not silently overwrite or mutate an unrelated visible function
    - dispatch remains pattern-based and preserves existing fixed-arity-over-varargs precedence
    - unrelated module import order must not decide dispatch results
    - when multiple cross-module clauses match and no deterministic specificity rule chooses one, evaluation must fail with a deterministic ambiguity error
    - each contributed clause retains module provenance for diagnostics, introspection, and future reload/unload design
    - loading/importing a module remains inert with respect to lifecycle activation, resource acquisition, and network/process side effects
    - the semantic contract must be host-agnostic and shared-spec driven; no Python-only dispatch rule may define the feature
  - open functions remain the first concept; a named protocol/interface layer, if ever needed, stays separate from R20 unless its own later gate promotes it
  - the example `extend` spelling, protocol syntax, specificity algorithm, module unloading, and implementation strategy remain unapproved until the R20 contract/design gates settle them
- browser playground runtime
  - useful as a future demo surface, not required for the first validated-data-pipeline release
- ants / simulation teaching demos
  - useful teaching material after the data-pipeline wedge is demonstrable
- value-template work outside the focused R9/R15 structural and validated-value scope
  - R9 and R15 are complete; new Template work requires later-release or follow-up classification
- nominal variants / closed constructor identity / exhaustiveness
  - R15 delivered structural discriminated alternatives only
  - nominal variant identity, constructor objects or syntax, sealed/closed nominal hierarchies, and exhaustiveness checking remain deferred
  - do not smuggle this work into R30/R31 shaped or relational Sheet semantics
- broad function contracts beyond the Template/validation boundaries already implemented
  - promote only when a concrete API-boundary use case proves the need
- purity / effect metadata
  - R30 may define only the minimum observable independence rules required for shaped computation
  - do not add `pure`, effect rows, an effect type system, or optimizer-facing user syntax unless concrete optimization/tooling use cases prove that existing semantics are insufficient
- module instances / initialized components
  - future distinction: import/load remains inert definition/namespace loading; explicit initialization may later create independent runtime instances with lifecycle-owned resources
  - do not mutate the module cache into runtime instance state
  - exact `init`/`start`/`stop` naming and module-instance representation remain unapproved
- validation DSL
  - do not create implementation tickets until helper-based validation proves insufficient
- Node, Java, Rust, and Go host implementation beyond contract scaffolding
  - generic runner and shared portability hardening are promoted to R16–R18
  - open-function semantics are promoted to R20 before the first second-host implementation
  - C++ host implementation is promoted to R21–R24
- server mode
  - **Web ergonomics promoted to R7**, and the **serve execution mode promoted to R8** (Server Execution Mode — the second R4 lifecycle consumer, `@server`/`@route`/`@cors` bound to R7 primitives). Idea capture: `docs/parking-lot/web-backend-cfm-app.md` (R7) and `docs/parking-lot/server-execution-mode.md` (R8). Anything beyond those two remains parked.
- notebook mode
- parallel native test execution
- package manager / public package registry
  - R33 may improve local project/tooling ergonomics but must not introduce package-distribution semantics without separate ecosystem pressure and its own contract/process work
- **#102** — broad scope; should be split into smaller targeted tickets or updated before use as a release tracker; do not use as a release blocker in its current form

## Selective Non-Strict Evaluation / Call-by-Need

**Classification:** Follow-up candidate; release unassigned.

**Problem:** Genia's boolean `&&` and `||` currently motivate expected
short-circuit behavior, but implementing those operators as isolated evaluator
special cases may miss a more composable language feature.

**Research direction:** keep Genia eager by default while investigating
selectively non-strict parameters with call-by-need behavior. A delayed
argument would not be evaluated before the call, would be evaluated only if the
callee demands it, and would be evaluated at most once. This is a design
hypothesis, not approved behavior.

The pre-flight must compare at least:

- direct `&&`/`||` short-circuit special-casing
- explicit thunk/closure APIs
- macro/special-form approaches
- selective call-by-name parameters
- selective call-by-need parameters
- global non-strict/normal-order evaluation as a control case, not the presumed
  Genia direction

Required semantic questions include evaluation order and at-most-once
guarantees; how skipped expressions suppress effects, errors, and capability
acquisition; interaction with ordinary `none`/`err` propagation and
`apply_raw`; lexical-environment capture; lifecycle expiration and authority
retention; protected-value non-leakage; whether delayed computations may
escape; diagnostic behavior; Core IR representation; and identical portable
behavior across Python and C++ hosts.

The first proving cases should include `false && rhs` and `true || rhs`
without evaluating `rhs`, plus demanded cases that evaluate `rhs` exactly
once. Tests must also cover skipped errors/effects, Outcome interactions,
lifecycle/capability boundaries, nesting/precedence, and shared-host
conformance.

**Non-goals:** this entry does not approve global laziness, normal-order
evaluation, a first-class Promise/Delay value, new truthiness rules, operator
overloading, syntax, Core IR nodes, or a release number. It must not expand R28.

Promotion requires a Genia Change Pre-Flight, best-in-breed language survey,
architecture decision, contract, failing shared specs, implementation,
documentation synchronization, and skeptical truth audit.

## Promoted post-R24 data-workflow work

The following ideas are no longer parking-lot-only and now have planned release homes in the current roadmap (see [`r30-r32.md`](r30-r32.md) and the release sequence):

- shaped whole-column computation, scalar lifting, and shape conformance → **R30**
- grouping, summarization, ordering, and explicit joins over Sheets → **R31**
- portable data-store/provider boundary, including explicit source/sink capabilities → **R32**
- formatter/editor/navigation/diagnostic tooling hardening → **R33**
- reproducible Python/C++ performance evidence and evidence-driven optimization → **R34**

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
