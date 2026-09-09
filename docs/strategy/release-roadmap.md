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

**R15 — Validated Value Modeling** is complete. E15-0 / issue #726 completed its contract, roadmap reconciliation, and capability-inventory gate through PR #738; **#728 / E15-1** through **#736 / E15-9** are delivered, with E15-9's skeptical release truth audit recording a PASS verdict.

**R16 — Multi-Host Conformance Infrastructure** is the active release. Epic
**#756** tracks R16 and **#757 / E16-0** is the completed contract/
current-state-inventory/protocol-decisions gate. Its contract is
`docs/design/r16-multi-host-conformance-infrastructure-contract.md`.
Activating the roadmap and approving the contract does **not** implement
any R16 runtime behavior; **no generic multi-host runner exists yet and all
conformance is still validated against the Python reference host only**,
exactly as `GENIA_STATE.md` §0 states. **#758 / E16-1** (versioned
host-adapter protocol and failure taxonomy), **#759 / E16-2** (generic
external-host execution path in `tools/spec_runner`), **#760 / E16-3**
(host capability advertisement and per-case requirements), **#761 /
E16-4** (contract revision pinning and current-main compatibility
reporting), **#762 / E16-5** (Python reference host proven through
the subprocess protocol), **#763 / E16-6** (external-host repository
boundary; [`m0smith/genia-cpp`](https://github.com/m0smith/genia-cpp)
bootstrapped), and **#764 / E16-7** (conformance evidence reporting and
external-host CI contract) are delivered. The default in-process Python
path remains unchanged and available as a developer-optimization path.
The next authorized step is **#765 / E16-8 preflight only**.

Detailed R15 scope and issue order: [`roadmap/r15.md`](roadmap/r15.md).
Detailed R16 scope: [`roadmap/r16-r20.md`](roadmap/r16-r20.md).

## Roadmap files

- **Completed releases R1–R14:** durable release summaries and runnable examples live in `docs/releases/R1.md` through `docs/releases/R14.md`.
- **R15 completed release detail:** [`roadmap/r15.md`](roadmap/r15.md)
- **R16–R20:** [`roadmap/r16-r20.md`](roadmap/r16-r20.md)
- **R21–R24:** [`roadmap/r21-r24.md`](roadmap/r21-r24.md)
- **R25–R29:** [`roadmap/r25-r29.md`](roadmap/r25-r29.md)
- **Multi-host repository/conformance policy:** [`roadmap/multi-host-conformance-policy.md`](roadmap/multi-host-conformance-policy.md)
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
- Release R15 — Validated Value Modeling ✓ COMPLETE. E15-0 through E15-9 are implemented and audited; R15 is complete.
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
| R15 | Validated Value Modeling | Complete | [`roadmap/r15.md`](roadmap/r15.md) |
| R16 | Multi-Host Conformance Infrastructure | Active (E16-0 contract complete) | [`roadmap/r16-r20.md`](roadmap/r16-r20.md) |
| R17 | Numeric and Ordered-Map Portability Contract | Planned | [`roadmap/r16-r20.md`](roadmap/r16-r20.md) |
| R18 | Unicode, Float, and Diagnostic Portability Contract | Planned | [`roadmap/r16-r20.md`](roadmap/r16-r20.md) |
| R19 | Open Functions and Extensible Pattern Dispatch | Planned | [`roadmap/r16-r20.md`](roadmap/r16-r20.md) |
| R20 | C++ Minimal Conforming Host | Planned | [`roadmap/r16-r20.md`](roadmap/r16-r20.md) |
| R21 | C++ Stateful Runtime and Concurrency | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R22 | C++ REPL and Data Bridges | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R23 | C++ Flow, Pipe Mode, and HTTP Serving | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R24 | Sheet Record Pipelines | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R25 | Sheet Shaped Computation | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R26 | Relational Sheet Operations | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R27 | Database Data Boundary | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R28 | Developer Experience and Language Tooling | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R29 | Cross-Host Performance and Optimization Evidence | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |

## Scheduling

The detailed dependency graph and its qualifications live in [`roadmap/sequence.md`](roadmap/sequence.md). Roadmap ordering never implements behavior and never skips the repository's contract, design, failing-test, implementation, documentation, audit, and distillation gates.
