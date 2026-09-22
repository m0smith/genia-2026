# Genia Release Roadmap

Status: Planning guide — non-authoritative. This is not a language contract.

This is the canonical roadmap entrypoint. Detailed release planning is split into focused files under `docs/strategy/roadmap/` so active work can be edited without rewriting unrelated release history. This roadmap does not define implemented language behavior.

Implemented behavior remains defined by:

1. `GENIA_STATE.md`
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. `spec/*`

If roadmap material conflicts with implemented truth, `GENIA_STATE.md` wins.

## Release examples

Every implemented release (R1 onward) must have a published `docs/releases/<Rn>.md` page with one or more small, runnable examples for that release's headline behavior — see `docs/releases/README.md`. This is maintained during the documentation phase of each change, not created merely because a planned release is named. A release is not marked complete until its release page exists.

## Product north star

Genia's first killer workflow is:

> Outcome-aware validated data pipelines.

Plain-language promise:

> messy records in → clear pipelines → validated shaped output / reports + useful diagnostics

New release work should strengthen this workflow unless explicitly approved as infrastructure or parking-lot work.

## Promoted cross-cutting follow-up: Outcome Composition Ergonomics

Outcome composition ergonomics is promoted from idea capture to a **near-term
cross-cutting follow-up candidate** because it directly strengthens the killer
workflow and already affects HTTP/configuration/AI-composition examples.

The first gate must stay narrow:

- define a canonical full-Outcome bind/composition operation (working name:
  `flat_map_outcome`)
- `some(value)` invokes the supplied step and requires an Outcome result
- `none(...)` is preserved unchanged
- `err(...)` is preserved unchanged
- ordinary application code should not need pervasive `apply_raw` merely to
  express "continue on success; otherwise preserve the Outcome"
- preserve current direct-call and pipeline propagation semantics unless a later,
  separately approved contract proves that Outcome-consuming pipeline stages are
  required
- do not generalize this into arbitrary propagation-control annotations or a
  second invocation model
- do not use this helper to hide modeling errors where `none(...)` is intended
  as domain/configuration data; callees that intentionally consume absence must
  remain explicit about that boundary

This planning entry does **not** implement behavior, approve syntax, or assign a
release number. Before implementation it still requires the repository's
contract, design, failing-test, implementation, documentation, audit, and
distillation gates. Detailed parking-lot disposition is recorded in
[`roadmap/parking-lot.md`](roadmap/parking-lot.md).

## Promoted R20 follow-up

Open-function declaration ergonomics is promoted as an R20 follow-up design
candidate; scope and guardrails live in [`roadmap/parking-lot.md`](roadmap/parking-lot.md).

## Current state

R15 through R23 are complete (`docs/releases/R23.md`; E23-11's third,
independent skeptical release truth audit recorded PASS in
`docs/analysis/r23-release-truth-audit.md`, after two genuine, narrow
findings during the audit gate -- E23-7 and E23-9 -- were each repaired
and re-verified). Python remains the only implemented production host;
`m0smith/genia-cpp` is still a non-semantic bootstrap shell with no
interpreter. See the corresponding release pages and `GENIA_STATE.md` for
implemented truth.

## Post-R20 planning reset

Planning issue #845 records the decision not to merge PR #839 as one giant exact-numeric prerequisite branch. The approved numeric design is decomposed into three numbered releases before C++:

- **R21 — Numeric Source and Portable Representation**
- **R22 — Exact Numeric Runtime**
- **R23 — Numeric Representation and Interchange**
- **R24 — C++ Minimal Conforming Host**
- **R25 — C++ Stateful Runtime and Concurrency**
- **R26 — C++ REPL and Data Bridges**
- **R27 — C++ Flow, Pipe Mode, and HTTP Serving**
- **R28 — Genia MCP Server**
- **R29 — Sheet Record Pipelines**
- **R30 — Sheet Shaped Computation**
- **R31 — Relational Sheet Operations**
- **R32 — Database Data Boundary**
- **R33 — Developer Experience and Language Tooling**
- **R34 — Cross-Host Performance and Optimization Evidence**
- **R35 — Portable Storage and Resource Semantics**
- **R36 — Location-Independent Genia Execution**
- **R37 — Portable Actors, Messaging, and Supervision**
- **R38 — Genia-Native Conformance Tooling**
- **R39 — Configuration and Secret Hardening and Ergonomics**

The process correction is documented in `docs/analysis/exact-numeric-gate-postmortem.md`. New implementation is re-derived from current `main` in independently mergeable slices rather than mechanically cherry-picked from #839.

## Roadmap files

- **Completed releases R1–R14:** durable release summaries and runnable examples live in `docs/releases/R1.md` through `docs/releases/R14.md`.
- **R15 completed release detail:** [`roadmap/r15.md`](roadmap/r15.md)
- **R16–R20:** [`roadmap/r16-r20.md`](roadmap/r16-r20.md)
- **R21–R24:** [`roadmap/r21-r24.md`](roadmap/r21-r24.md)
- **R25–R29:** [`roadmap/r25-r29.md`](roadmap/r25-r29.md)
- **R30–R34:** [`roadmap/r30-r32.md`](roadmap/r30-r32.md)
- **R35–R37:** [`roadmap/r35-r37.md`](roadmap/r35-r37.md)
- **Cross-cutting host capability and external process architecture (planned,
  unnumbered):** [`../architecture/host-capability-taxonomy.md`](../architecture/host-capability-taxonomy.md)
  and [`../architecture/external-process-execution.md`](../architecture/external-process-execution.md)
- **R38:** [`roadmap/r38.md`](roadmap/r38.md)
- **R39:** [`roadmap/r39.md`](roadmap/r39.md)
- **Multi-host repository/conformance policy:** [`roadmap/multi-host-conformance-policy.md`](roadmap/multi-host-conformance-policy.md)
- **Release sequence and dependencies:** [`roadmap/sequence.md`](roadmap/sequence.md)
- **Parking lot and historical issue disposition:** [`roadmap/parking-lot.md`](roadmap/parking-lot.md)
- **Frozen pre-split repository snapshot:** `docs/strategy/roadmap/archive/release-roadmap-pre-split.md`. This is history only; it is intentionally not published as live roadmap content.

## Completed-release sync anchors

## Release R3 — Native Test Expansion Wave 1

R3 expanded native Genia test coverage. Its scope explicitly excluded
lifecycle generalization (see R4). Its durable release summary and runnable
example live in [`docs/releases/R3.md`](../releases/R3.md).

## Release R4 — Lifecycle Generalization

R4 kept lifecycle generalization separate from R3's native-test expansion. Its
durable release summary lives in [`docs/releases/R4.md`](../releases/R4.md).

- Release R7 — Web Serving Ergonomics ✓ COMPLETE
- Release R8 — Server Execution Mode ✓ COMPLETE
  - **Status: Complete.** Explicitly approved infrastructure work delivered after R7.
  - Bind-down principle: `@cors` → the R7 `cors` wrapper. No second mechanism.
- Release R9 — Value Templates & Representations ✓ COMPLETE
  - **Status: Complete.** E9-1 through E9-7 delivered the approved behavior; E9-8 completed the release truth audit.
- Release R10 — Configuration & Secrets ✓ COMPLETE
  - **Status: Complete. E10-1 through E10-8 delivered and audited.** Issue #586 approved the durable contract. R10/R11/R12/R13 follow-ups require their own gates.
- Release R11 — AI Composition ✓ COMPLETE; E11-1 through E11-8 complete
- Release R12 — Retrieval & Grounding ✓ COMPLETE
- Release R13 — Configuration Resolution Ergonomics ✓ COMPLETE
- Release R14 — Composable Lifecycles ✓ COMPLETE
- Release R15 — Validated Value Modeling ✓ COMPLETE
- Release R16 — Multi-Host Conformance Infrastructure ✓ COMPLETE
- Release R17 — Numeric and Ordered-Map Portability Contract ✓ COMPLETE
- Release R18 — Portable Value Equality ✓ COMPLETE
- Release R19 — Unicode and Diagnostic Portability Contract ✓ COMPLETE
- Release R20 — Open Functions and Extensible Pattern Dispatch ✓ COMPLETE
- Release R21 — Numeric Source and Portable Representation ✓ COMPLETE

## Release status

| Release | Theme | Status | Detail |
|---|---|---|---|
| R1 | Killer Workflow Foundation | Complete | `docs/releases/R1.md` |
| R2 | Native Test Kernel | Complete | `docs/releases/R2.md` |
| R3 | Native Test Expansion Wave 1 | Complete | `docs/releases/R3.md` |
| R4 | Lifecycle Generalization | Complete | `docs/releases/R4.md` |
| R5 | Native Test Migration / Genia-Facing Coverage Wave 1 | Complete | `docs/releases/R5.md` |
| R6 | Data Workflow Hardening | Complete | `docs/releases/R6.md` |
| R7 | Web Serving Ergonomics | Complete | `docs/releases/R7.md` |
| R8 | Server Execution Mode | Complete | `docs/releases/R8.md` |
| R9 | Value Templates & Representations | Complete | `docs/releases/R9.md` |
| R10 | Configuration & Secrets | Complete | `docs/releases/R10.md` |
| R11 | AI Composition | Complete | `docs/releases/R11.md` |
| R12 | Retrieval & Grounding | Complete | `docs/releases/R12.md` |
| R13 | Configuration Resolution Ergonomics | Complete | `docs/releases/R13.md` |
| R14 | Composable Lifecycles | Complete | `docs/releases/R14.md` |
| R15 | Validated Value Modeling | Complete | [`roadmap/r15.md`](roadmap/r15.md) |
| R16 | Multi-Host Conformance Infrastructure | Complete | `docs/releases/R16.md` |
| R17 | Numeric and Ordered-Map Portability Contract | Complete | `docs/releases/R17.md` |
| R18 | Portable Value Equality | Complete | `docs/releases/R18.md` |
| R19 | Unicode and Diagnostic Portability Contract | Complete | `docs/releases/R19.md` |
| R20 | Open Functions and Extensible Pattern Dispatch | Complete | `docs/releases/R20.md` |
| R21 | Numeric Source and Portable Representation | Complete | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R22 | Exact Numeric Runtime | Complete | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R23 | Numeric Representation and Interchange | Complete | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R24 | C++ Minimal Conforming Host | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R25 | C++ Stateful Runtime and Concurrency | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R26 | C++ REPL and Data Bridges | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R27 | C++ Flow, Pipe Mode, and HTTP Serving | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R28 | Genia MCP Server | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R29 | Sheet Record Pipelines | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R30 | Sheet Shaped Computation | Planned | [`roadmap/r30-r32.md`](roadmap/r30-r32.md) |
| R31 | Relational Sheet Operations | Planned | [`roadmap/r30-r32.md`](roadmap/r30-r32.md) |
| R32 | Database Data Boundary | Planned | [`roadmap/r30-r32.md`](roadmap/r30-r32.md) |
| R33 | Developer Experience and Language Tooling | Planned | [`roadmap/r30-r32.md`](roadmap/r30-r32.md) |
| R34 | Cross-Host Performance and Optimization Evidence | Planned | [`roadmap/r30-r32.md`](roadmap/r30-r32.md) |
| R35 | Portable Storage and Resource Semantics | Planned | [`roadmap/r35-r37.md`](roadmap/r35-r37.md) |
| R36 | Location-Independent Genia Execution | Planned | [`roadmap/r35-r37.md`](roadmap/r35-r37.md) |
| R37 | Portable Actors, Messaging, and Supervision | Planned | [`roadmap/r35-r37.md`](roadmap/r35-r37.md) |
| R38 | Genia-Native Conformance Tooling | Planned | [`roadmap/r38.md`](roadmap/r38.md) |
| R39 | Configuration and Secret Hardening and Ergonomics | Planned | [`roadmap/r39.md`](roadmap/r39.md) |

## Scheduling

The detailed dependency graph and its qualifications live in [`roadmap/sequence.md`](roadmap/sequence.md). Roadmap ordering never implements behavior and never skips the repository's contract, design, failing-test, implementation, documentation, audit, and distillation gates.
