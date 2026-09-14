# Release Sequence and Dependencies

Status: Planning guide — non-authoritative. `GENIA_STATE.md` remains final authority for implemented behavior.

The scheduling sequence is:

```text
R8  — Server Execution Mode
 |
 v
R9  — Value Templates & Representations
 |
 v
R10 — Configuration & Secrets ✓ COMPLETE
 |
 v
R11 — AI Composition
 |
 v
R12 — Retrieval & Grounding
 |
 v
R13 — Configuration Resolution Ergonomics
 |
 v
R14 — Composable Lifecycles
 |
 v
R15 — Validated Value Modeling
 |
 v
R16 — Multi-Host Conformance Infrastructure ✓ COMPLETE
 |
 v
R17 — Numeric & Ordered-Map Portability Contract ✓ COMPLETE
 |
 v
R18 — Portable Value Equality ✓ COMPLETE
 |
 v
R19 — Unicode & Diagnostic Portability Contract ✓ COMPLETE
 |
 v
R20 — Open Functions & Extensible Pattern Dispatch ✓ COMPLETE
 |
 v
R21 — Numeric Source & Portable Representation
 |
 v
R22 — Exact Numeric Runtime
 |
 v
R23 — Numeric Representation & Interchange
 |
 v
R24 — C++ Minimal Conforming Host
 |
 +----> R25 — C++ Stateful Runtime & Concurrency
 |
 +----> R26 — C++ REPL & Data Bridges
           |
           v
R27 — C++ Flow, Pipe Mode & HTTP Serving
 |
 v
R28 — Genia MCP Server
 |
 v
R29 — Sheet Record Pipelines
 |
 v
R30 — Sheet Shaped Computation
 |
 v
R31 — Relational Sheet Operations
 |
 v
R32 — Database Data Boundary
 |
 v
R33 — Developer Experience & Language Tooling
 |
 v
R34 — Cross-Host Performance & Optimization Evidence
 |
 v
R35 — Portable Storage & Resource Semantics
 |
 v
R36 — Location-Independent Genia Execution
 |
 v
R37 — Genia-Native Conformance Tooling
```

This ordering does not imply that every release is a strict technical dependency of the next. Roadmap placement is planning authority only and never makes candidate behavior implemented.

R16 is complete required infrastructure for independently implemented second hosts. It establishes the external-host repository boundary, contract-revision pinning, capability-aware conformance claims, deterministic evidence, and separation between pinned conformance and current-main compatibility.

R17 and R18 are complete portability foundations. R17 establishes arbitrary-precision Integer and ordered-map portability. R18 establishes the shared equality/key model, including structural, identity-bearing, and opaque-token semantics, legal-key reflexivity, protected-value non-oracle behavior, and key/hash consistency.

R19 is complete and owns Unicode/string and diagnostic portability. R20 is complete and owns host-agnostic open-function/extensible-pattern dispatch semantics.

## Exact numeric decomposition

Planning issue #845 supersedes the former single Exact Numeric Model prerequisite branch as an implementation vehicle. PR #839 is not merged. Its design and audit evidence inform three separately numbered releases:

- **R21** owns numeric source classification and tagged portable Core IR only.
- **R22** owns Decimal/Rational/Float64 runtime values, arithmetic, conversions, comparison/equality integration, numeric misuse, and resource-limit semantics.
- **R23** owns canonical numeric rendering, format presentation, strict JSON numeric behavior, lexical JSON Decimal decode, and compatibility JSON reconciliation.

The approved semantic decisions are partitioned in `docs/design/exact-numeric-release-ownership.md`; the delivery postmortem is `docs/analysis/exact-numeric-gate-postmortem.md`.

Each release may consist of multiple independently mergeable PRs against current `main`. Release audits run against merged `main`; substantive findings become narrow repair issues/PRs followed by fresh audit.

## C++ host arc

R24 is the first planned production C++ implementation release and depends on completed/audited R16-R23. C++ production implementation belongs in `m0smith/genia-cpp`; `genia-2026` remains authoritative for language contracts, shared specs, generic conformance infrastructure, and portability documentation. If C++ implementation exposes semantic ambiguity, clarify upstream before continuing rather than copying Python behavior.

R25 and R26 extend the C++ host along mostly independent stateful and REPL/data-bridge tracks. R27 consumes the approved contracts it needs for Flow, pipe mode, and HTTP serving and closes only capabilities it can prove.

## MCP

R28 is the planned Genia MCP Server release. It is integration infrastructure, not a new language semantics layer. It adapts existing parse/execution/capability behavior through governed MCP tools, explicit authority limits, structured results/diagnostics, and official-client parity evidence. Existing epic #700 and issues #701-#707 are the R28/E28-* issue set after renumbering.

R28 is placed after the C++ host expansion arc to keep that arc contiguous. MCP implementation may still initially use the Python reference host where the approved R28 contract says so; roadmap position does not require MCP to wait for complete cross-host parity unless its own gate makes that a concrete dependency.

## Data workflow and tooling arc

R29 consumes the existing Sheet/Flow/Outcome/validation/lifecycle foundations to add an explicit Sheet record-pipeline boundary without introducing AWK syntax or implicit Sheet Seq compatibility.

R30 deepens that boundary into shaped whole-column computation. R31 adds deterministic relational Sheet operations. R32 adds one explicit database data boundary using existing configuration/secrets, lifecycle, Flow, Outcome, and Sheet machinery rather than an ORM or database-specific pipeline model.

R33 is a developer-tooling release derived from implemented parser/Core-IR/help/debugger truth. R34 follows the second-host and data-workflow work with reproducible cross-host performance evidence and permits optimization only where measurements justify it and shared conformance proves no semantic drift.

## Storage, execution, and dogfooding arc

R35 is the planned portable Store/Location/resource contract. It consumes R18 equality, R10/R13 protection/configuration, R14 lifecycle ownership, current Flow/Outcome behavior, and R16 capability discipline. It keeps resource identity, authority, revisions, and provider mechanics separate; future cloud providers must preserve the same application-level contract.

R36 is the planned location-independent Execution contract. It consumes R14 lifecycle ownership, R16 compatibility lessons, R18 identity/opaque semantics, and R35 storage authority where needed. Local execution is the first provider, not the semantic model.

R37 is the planned Genia-native conformance-tooling migration. It consumes R18 equality, R35 discovery/loading, and R36 external invocation. It includes a Genia-native YAML parser for the contracted shared-spec profile and must not invent ad hoc filesystem, subprocess, or equality semantics to complete the migration.

R8 through R20 are complete. R21 through R37 remain planned and not active unless a specific issue/roadmap gate says otherwise. Python remains the only implemented production host. Every later behavior slice requires its own contract/design/test/implementation/documentation/audit gates; roadmap placement is not implementation authority.
