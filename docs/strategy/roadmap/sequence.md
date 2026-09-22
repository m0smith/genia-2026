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
R21 — Numeric Source & Portable Representation ✓ COMPLETE
 |
 v
R22 — Exact Numeric Runtime ✓ COMPLETE
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

R38 — Configuration and Secret Hardening and Ergonomics
  (depends only on completed R10/R13; not chained through R14–R37)

R39 — Portable Core IR Artifacts
  (depends on the R16 portability boundary and a sufficiently conforming second host; intended to turn Core IR into a compiler-independent deployable artifact contract)
```

This ordering does not imply that every release is a strict technical dependency of the next. Roadmap placement is planning authority only and never makes candidate behavior implemented.

R16–R20 are complete portability foundations. R16 supplies the external-host protocol/capability/evidence boundary, R17 arbitrary-precision Integer and ordered-map portability, R18 portable equality/key semantics, R19 Unicode/diagnostic portability, and R20 open-function/extensible-pattern dispatch semantics.

## Exact numeric decomposition

Planning issue #845 supersedes the former single Exact Numeric Model prerequisite branch as an implementation vehicle. PR #839 is not merged. Its approved design and audit evidence are repartitioned into separately gated releases:

- **R21** — numeric source classification and tagged portable Core IR only.
- **R22** — Decimal/Rational/Float64 runtime values, arithmetic, conversions, comparison/equality integration, numeric misuse, and resource-limit semantics.
- **R23** — canonical numeric rendering, format presentation, strict JSON numeric behavior, lexical JSON Decimal decode, and compatibility JSON reconciliation.

The delivery postmortem is `docs/analysis/exact-numeric-gate-postmortem.md`. Each release is expected to use multiple independently mergeable PRs against current `main`; release audits run against merged `main`, and substantive findings become narrow repair PRs followed by fresh audit.

## C++ host arc

R24 is the first planned production C++ implementation release and depends on completed/audited R16–R23. C++ production implementation belongs in `m0smith/genia-cpp`; `genia-2026` remains authoritative for contracts, shared specs, conformance infrastructure, and portability documentation. If C++ work exposes semantic ambiguity, clarify it upstream before continuing rather than copying Python behavior.

R25 and R26 extend the C++ host along mostly independent stateful and REPL/data-bridge tracks. R27 consumes the approved contracts needed for Flow, pipe mode, and HTTP serving and closes only capabilities it can prove.

## MCP

R28 is the planned Genia MCP Server release. It is integration infrastructure, not a new language-semantics layer. Existing epic #700 and issues #701–#707 are the R28/E28-* issue set after renumbering.

R28 is placed after the C++ host expansion arc to keep that arc contiguous. Its own contract may still authorize an initial Python-reference-host implementation; roadmap position alone does not require complete cross-host parity.

## Data workflow and tooling arc

R29 adds the explicit Sheet record-pipeline boundary. R30 deepens it into shaped whole-column computation. R31 adds relational Sheet operations. R32 adds one explicit database data boundary. R33 is developer tooling derived from implemented parser/Core-IR/help/debugger truth. R34 adds reproducible cross-host performance evidence and permits optimization only when shared conformance proves no semantic drift.

## Storage, execution, and dogfooding arc

R35 is the portable Store/Location/resource contract. R36 is the location-independent Execution contract. R37 is the Genia-native conformance-tooling migration, including the Genia-native YAML parser for the contracted shared-spec profile. These releases consume prior equality, lifecycle, host-protocol, and authority boundaries rather than inventing local substitutes.

R8 through R23 are complete. R24 through R39 remain planned and not active unless a specific gate says otherwise. Python remains the only implemented production host. Every later behavior slice requires its own contract/design/test/implementation/documentation/audit gates; roadmap placement is not implementation authority.

## Configuration and secret hardening

R38 promotes the outstanding candidates from
`docs/parking-lot/post-r13-configuration-followups.md` (C-1 through C-11) as
one numbered release. It is listed outside the main dependency chain above
because it depends only on completed R10 and R13, not on any release from
R14 onward; it is free to schedule and ship independently, subject to its
own contract/design/test/implementation/documentation/audit gates. See
`docs/strategy/roadmap/r38.md`.


## Portable Core IR artifacts

R39 turns the existing Core IR portability boundary into a stable, versioned, deployable artifact contract. It is infrastructure work rather than a new semantic layer: the artifact serializes supported Core IR plus the metadata required to validate, link, and execute it without requiring a Genia source compiler in the runtime host. The release is intentionally positioned after the second-host foundation so the contract can be proved across independent hosts rather than inferred from Python alone. A future browser host is a motivating proving consumer, but browser implementation itself is outside R39. See `docs/strategy/roadmap/r39.md`.
