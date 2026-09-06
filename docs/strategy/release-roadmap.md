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

## Current release

**R15 — Validated Value Modeling** is active. E15-0 / issue #726 completed its contract, roadmap reconciliation, and capability-inventory gate through PR #738. **#728 / E15-1**, **#729 / E15-2**, and **#730 / E15-3 — accumulated path-aware validation diagnostics** are delivered. The next authorized work item is **#731 / E15-4 — faithful supported Template → JSON Schema generation**.

Detailed R15 scope and issue order: [`roadmap/r15.md`](roadmap/r15.md).

## Roadmap files

- **Completed releases R1–R14:** durable release summaries and runnable examples live in `docs/releases/R1.md` through `docs/releases/R14.md`.
- **R15 active release:** [`roadmap/r15.md`](roadmap/r15.md)
- **R16–R19:** [`roadmap/r16-r19.md`](roadmap/r16-r19.md)
- **R20–R23:** [`roadmap/r20-r23.md`](roadmap/r20-r23.md)
- **Release sequence and dependencies:** [`roadmap/sequence.md`](roadmap/sequence.md)
- **Parking lot and historical issue disposition:** [`roadmap/parking-lot.md`](roadmap/parking-lot.md)
- **Frozen pre-split repository snapshot:** `docs/strategy/roadmap/archive/release-roadmap-pre-split.md`. This is history only; it is intentionally not published as live roadmap content.

## Release R3 — Native Test Expansion Wave 1

Historical semantic-sync anchor only. R3 delivered Native Test Expansion while explicitly excluding **lifecycle generalization (see R4)**. Detailed completed-release history and runnable examples live in `docs/releases/R3.md`; the frozen pre-split roadmap preserves the full original planning text.

## Release R4 — Lifecycle Generalization

Historical semantic-sync anchor only. R4 separately delivered Lifecycle Generalization. Detailed completed-release history and runnable examples live in `docs/releases/R4.md`; the frozen pre-split roadmap preserves the full original planning text.

## Completed-release sync anchors

These short anchors are intentionally retained in the canonical index because existing documentation-integrity tests use them to detect release-status drift. Detailed history lives in the release pages and frozen archive.

- Release R7 — Web Serving Ergonomics ✓ COMPLETE
- Release R8 — Server Execution Mode. **Status: Complete.** Explicitly approved infrastructure work delivered after R7. `@cors` → the R7 `cors` wrapper. No second mechanism.
- Release R9 — Value Templates & Representations. **Status: Complete.** E9-1 through E9-7 delivered; E9-8 completed the release truth audit.
- Release R10 — Configuration & Secrets ✓ COMPLETE. **Status: Complete. E10-1 through E10-8 delivered and audited.** Issue #586 approved the durable R10 contract.
- Release R11 — AI Composition ✓ COMPLETE. E11-1 through E11-8 complete.
- Release R12 — Retrieval & Grounding ✓ COMPLETE. E12-1 through E12-9 complete.
- Release R13 — Configuration Resolution Ergonomics ✓ COMPLETE. E13-1 through E13-8 are complete.
- Release R14 — Composable Lifecycles ✓ COMPLETE. E14-1 through E14-15 are implemented; R14 is complete.
- R10/R11/R12/R13 follow-ups require their own gates.

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
| R15 | Validated Value Modeling | **Active** | [`roadmap/r15.md`](roadmap/r15.md) |
| R16 | Multi-Host Spec Runner | Planned | [`roadmap/r16-r19.md`](roadmap/r16-r19.md) |
| R17 | Numeric and Ordered-Map Portability Contract | Planned | [`roadmap/r16-r19.md`](roadmap/r16-r19.md) |
| R18 | Unicode, Float, and Diagnostic Portability Contract | Planned | [`roadmap/r16-r19.md`](roadmap/r16-r19.md) |
| R19 | C++ Minimal Conforming Host | Planned | [`roadmap/r16-r19.md`](roadmap/r16-r19.md) |
| R20 | C++ Stateful Runtime and Concurrency | Planned | [`roadmap/r20-r23.md`](roadmap/r20-r23.md) |
| R21 | C++ REPL and Data Bridges | Planned | [`roadmap/r20-r23.md`](roadmap/r20-r23.md) |
| R22 | C++ Flow, Pipe Mode, and HTTP Serving | Planned | [`roadmap/r20-r23.md`](roadmap/r20-r23.md) |
| R23 | Sheet Record Pipelines | Planned | [`roadmap/r20-r23.md`](roadmap/r20-r23.md) |

## Scheduling

The detailed dependency graph and its qualifications live in [`roadmap/sequence.md`](roadmap/sequence.md). Roadmap ordering never implements behavior and never skips the repository's contract, design, failing-test, implementation, documentation, audit, and distillation gates.
