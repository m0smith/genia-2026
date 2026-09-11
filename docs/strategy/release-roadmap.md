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

**R16 — Multi-Host Conformance Infrastructure** is complete. Epic **#756** is
closed; **#757 / E16-0** through **#765 / E16-8** are delivered, and
`docs/releases/R16.md` records the skeptical release truth audit PASS. The
implemented generic runner is `python -m tools.spec_runner --host '<command>'`;
capability-aware selection, exact contract-revision identity, Python-reference
subprocess parity, the external `m0smith/genia-cpp` bootstrap boundary, and
deterministic conformance evidence are all landed. Python remains the only
implemented production host; the C++ repository is still a non-semantic
bootstrap shell with no interpreter.

**R17 — Numeric and Ordered-Map Portability Contract** is complete. Epic
**#776** covers **#777 / E17-0** through **#780 / E17-3**; its approved
contract, three shared semantic cases, authoritative documentation, release
page, and skeptical audit are delivered. The audit verdict is PASS.

**R18 — Portable Value Equality** is the active release. Epic **#789** covers
**#790 / E18-0** through **#797 / E18-7**; E18-0 through E18-6 are delivered, and
the E18-7 skeptical release audit is the remaining gate. It settles
host-independent structural, identity-bearing, and opaque-token equality,
protected-value non-oracle behavior, legal-key reflexivity, map equality, and
internal key consistency before later portability work and a second host consume
those rules. It added no C++ host, no user-overloadable `==`, no token-domain
syntax or minting API, and no storage `Revision`; map iteration order remains the
R17 contract. See `docs/releases/R18.md`.

Detailed R15 scope and issue order: [`roadmap/r15.md`](roadmap/r15.md).
Detailed R16-R21 scope: [`roadmap/r16-r20.md`](roadmap/r16-r20.md).

## Roadmap files

- **Completed releases R1–R14:** durable release summaries and runnable examples live in `docs/releases/R1.md` through `docs/releases/R14.md`.
- **R15 completed release detail:** [`roadmap/r15.md`](roadmap/r15.md)
- **R16–R21:** [`roadmap/r16-r20.md`](roadmap/r16-r20.md)
- **R22–R25:** [`roadmap/r21-r24.md`](roadmap/r21-r24.md)
- **R26–R30:** [`roadmap/r25-r29.md`](roadmap/r25-r29.md)
- **R31–R33:** [`roadmap/r30-r32.md`](roadmap/r30-r32.md)
- **Multi-host repository/conformance policy:** [`roadmap/multi-host-conformance-policy.md`](roadmap/multi-host-conformance-policy.md)
- **Release sequence and dependencies:** [`roadmap/sequence.md`](roadmap/sequence.md)
- **Parking lot and historical issue disposition:** [`roadmap/parking-lot.md`](roadmap/parking-lot.md)
- **Frozen pre-split repository snapshot:** `docs/strategy/roadmap/archive/release-roadmap-pre-split.md`. This is history only; it is intentionally not published as live roadmap content.

## Release R3 — Native Test Expansion Wave 1

Historical semantic-sync anchor only. R3 delivered Native Test Expansion while explicitly excluding **lifecycle generalization (see R4)**. Detailed completed-release history and runnable examples live in `docs/releases/R3.md`; the frozen pre-split roadmap preserves the full original planning text.

## Release R4 — Lifecycle Generalization

Historical semantic-sync anchor only. R4 separately delivered Lifecycle Generalization. Detailed history lives in the release page and frozen archive.

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
- Release R16 — Multi-Host Conformance Infrastructure ✓ COMPLETE. E16-0 through E16-8 are delivered and audited; R16 is complete.
- Release R17 — Numeric and Ordered-Map Portability Contract ✓ COMPLETE. E17-0 through E17-3 are delivered and audited; R17 is complete.
- Release R18 — Portable Value Equality — ACTIVE. E18-0 through E18-6 are delivered; the E18-7 skeptical release audit is the remaining gate before R18 is recorded complete.
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
| R16 | Multi-Host Conformance Infrastructure | Complete | `docs/releases/R16.md` |
| R17 | Numeric and Ordered-Map Portability Contract | Complete | `docs/releases/R17.md` |
| R18 | Portable Value Equality | E18-0–E18-6 delivered; E18-7 audit pending | `docs/releases/R18.md` |
| R19 | Unicode, Float, and Diagnostic Portability Contract | Planned | [`roadmap/r16-r20.md`](roadmap/r16-r20.md) |
| R20 | Open Functions and Extensible Pattern Dispatch | Planned | [`roadmap/r16-r20.md`](roadmap/r16-r20.md) |
| R21 | C++ Minimal Conforming Host | Planned | [`roadmap/r16-r20.md`](roadmap/r16-r20.md) |
| R22 | C++ Stateful Runtime and Concurrency | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R23 | C++ REPL and Data Bridges | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R24 | C++ Flow, Pipe Mode, and HTTP Serving | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R25 | Sheet Record Pipelines | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R26 | Sheet Shaped Computation | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R27 | Relational Sheet Operations | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R28 | Database Data Boundary | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R29 | Developer Experience and Language Tooling | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R30 | Cross-Host Performance and Optimization Evidence | Planned | [`roadmap/r25-r29.md`](roadmap/r25-r29.md) |
| R31 | Portable Storage and Resource Semantics | Planned | [`roadmap/r30-r32.md`](roadmap/r30-r32.md) |
| R32 | Location-Independent Genia Execution | Planned | [`roadmap/r30-r32.md`](roadmap/r30-r32.md) |
| R33 | Genia-Native Conformance Tooling | Planned | [`roadmap/r30-r32.md`](roadmap/r30-r32.md) |

## Scheduling

The detailed dependency graph and its qualifications live in [`roadmap/sequence.md`](roadmap/sequence.md). Roadmap ordering never implements behavior and never skips the repository's contract, design, failing-test, implementation, documentation, audit, and distillation gates.
