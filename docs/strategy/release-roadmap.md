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

## Current state

**R15 — Validated Value Modeling** is complete. E15-0 / issue #726 completed its contract, roadmap reconciliation, and capability-inventory gate through PR #738; **#728 / E15-1** through **#736 / E15-9** are delivered, with E15-9's skeptical release truth audit recording a PASS verdict.

**R16 — Multi-Host Conformance Infrastructure** is complete. Epic **#756** is closed; **#757 / E16-0** through **#765 / E16-8** are delivered, and `docs/releases/R16.md` records the skeptical release truth audit PASS. The implemented generic runner is `python -m tools.spec_runner --host '<command>'`; capability-aware selection, exact contract-revision identity, Python-reference subprocess parity, the external `m0smith/genia-cpp` bootstrap boundary, and deterministic conformance evidence are all landed. Python remains the only implemented production host; the C++ repository is still a non-semantic bootstrap shell with no interpreter.

**R17 — Numeric and Ordered-Map Portability Contract** is complete. Epic **#776** covers **#777 / E17-0** through **#780 / E17-3**; its approved contract, shared semantic cases, authoritative documentation, release page, and skeptical audit are delivered. The audit verdict is PASS.

**R18 — Portable Value Equality** is complete. Epic **#789** covers **#790 / E18-0** through **#797 / E18-7**; its approved contract, shared semantic cases, authoritative documentation, release page, and skeptical audit are delivered. The audit verdict is PASS. It settles host-independent structural, identity-bearing, and opaque-token equality, protected-value non-oracle behavior, legal-key reflexivity, map equality, and internal key consistency. It added no C++ host, no user-overloadable `==`, no token-domain syntax or minting API, and no storage `Revision`; map iteration order remains the R17 contract. See `docs/releases/R18.md`.

**R19 — Unicode and Diagnostic Portability Contract is complete.** It settled code-point string semantics, strict UTF-8 boundary/decode behavior, deterministic debug escaping, and a diagnostic-wording leak audit. R19 does not own Decimal/Rational/explicit Float64 semantics. See `docs/releases/R19.md`.

**R20 — Open Functions and Extensible Pattern Dispatch is complete.** It adds one identity-bearing open function interface concept: local repeated/grouped pattern clauses accumulate deterministically, and separately authored modules extend an interface only through explicit `extend`/`use` contribution and selection — never through ordinary import. See `docs/releases/R20.md`.

## Post-R20 planning reset

Planning issue #845 records the decision not to merge PR #839 as one giant exact-numeric prerequisite branch. The approved numeric design is decomposed into three numbered releases before C++:

- **R21 — Numeric Source and Portable Representation**
- **R22 — Exact Numeric Runtime**
- **R23 — Numeric Representation and Interchange**
- **R24 — C++ Minimal Conforming Host**

The postmortem is `docs/analysis/exact-numeric-gate-postmortem.md`; semantic ownership is `docs/design/exact-numeric-release-ownership.md`. New implementation is re-derived from current `main` in independently mergeable slices rather than mechanically cherry-picked from #839.

**R28 — Genia MCP Server** remains an explicit planned release. Existing epic #700 and issues #701-#707 are renumbered to R28/E28-* while preserving their substantive MCP scope.

## Roadmap files

- **Completed releases R1–R14:** durable release summaries and runnable examples live in `docs/releases/R1.md` through `docs/releases/R14.md`.
- **R15 completed release detail:** [`roadmap/r15.md`](roadmap/r15.md)
- **R16–R20:** [`roadmap/r16-r20.md`](roadmap/r16-r20.md)
- **R21–R24:** [`roadmap/r21-r24.md`](roadmap/r21-r24.md)
- **R25–R29:** [`roadmap/r25-r29.md`](roadmap/r25-r29.md)
- **R30–R34:** [`roadmap/r30-r32.md`](roadmap/r30-r32.md)
- **R35–R37:** [`roadmap/r35-r37.md`](roadmap/r35-r37.md)
- **Multi-host repository/conformance policy:** [`roadmap/multi-host-conformance-policy.md`](roadmap/multi-host-conformance-policy.md)
- **Release sequence and dependencies:** [`roadmap/sequence.md`](roadmap/sequence.md)
- **Parking lot and historical issue disposition:** [`roadmap/parking-lot.md`](roadmap/parking-lot.md)
- **Frozen pre-split repository snapshot:** `docs/strategy/roadmap/archive/release-roadmap-pre-split.md`. This is history only; it is intentionally not published as live roadmap content.

## Release R3 — Native Test Expansion Wave 1

Historical semantic-sync anchor only. R3 delivered Native Test Expansion while explicitly excluding **lifecycle generalization (see R4)**. Detailed completed-release history and runnable examples live in `docs/releases/R3.md`; the frozen pre-split roadmap preserves the full original planning text.

## Release R4 — Lifecycle Generalization

Historical semantic-sync anchor only. R4 separately delivered Lifecycle Generalization. Detailed history lives in the release page and frozen archive.

## Completed-release sync anchors

These short anchors are intentionally retained in the canonical index because documentation-integrity tests use them to detect release-status drift. Detailed history lives in the release pages and frozen archive.

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
- Release R18 — Portable Value Equality ✓ COMPLETE. E18-0 through E18-7 are delivered and audited; R18 is complete.
- Release R19 — Unicode and Diagnostic Portability Contract ✓ COMPLETE.
- Release R20 — Open Functions and Extensible Pattern Dispatch ✓ COMPLETE.
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
| R18 | Portable Value Equality | Complete | `docs/releases/R18.md` |
| R19 | Unicode and Diagnostic Portability Contract | Complete | `docs/releases/R19.md` |
| R20 | Open Functions and Extensible Pattern Dispatch | Complete | `docs/releases/R20.md` |
| R21 | Numeric Source and Portable Representation | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R22 | Exact Numeric Runtime | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
| R23 | Numeric Representation and Interchange | Planned | [`roadmap/r21-r24.md`](roadmap/r21-r24.md) |
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
| R37 | Genia-Native Conformance Tooling | Planned | [`roadmap/r35-r37.md`](roadmap/r35-r37.md) |

## Scheduling

The detailed dependency graph and its qualifications live in [`roadmap/sequence.md`](roadmap/sequence.md). Roadmap ordering never implements behavior and never skips the repository's contract, design, failing-test, implementation, documentation, audit, and distillation gates.
