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
R23 — Numeric Representation & Interchange ✓ COMPLETE
 |
 v
R24 — C++ Minimal Conforming Host ✓ COMPLETE
 |
 +----> R25 — C++ Stateful Runtime & Concurrency ✓ COMPLETE
 |
 +----> R26 — C++ REPL & Data Bridges ✓ COMPLETE
           |
           v
R27 — C++ Flow & Pipe Mode ✓ COMPLETE
 |
 +------------------------------+
 |                              |
 v                              v
R28 — Genia MCP Server         R42 — Persistent Interactive Sessions & Jupyter
 |
 v
R20 follow-up — Unified Function Model & Open-Function Repairs (#1067)
 |              (unnumbered follow-up; does not expand R28)
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
R32 — Portable Data Store Boundary
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
R37 — Unified Events & Subscriptions
 |
 v
R38 — Portable Actors, Messaging & Supervision
 |
 v
R39 — Genia-Native Conformance Tooling
 |
 v
R41 — Portable Core IR Artifacts

R40 — Configuration and Secret Hardening and Ergonomics
  (depends only on completed R10/R13; reservation number does not imply dependency on R14–R39 or R41)
```

This ordering does not imply that every release is a strict technical dependency of the next. Roadmap placement is planning authority only and never makes candidate behavior implemented.

R42 deliberately appears at its dependency position rather than after R41.
It consumes the completed R26 scripted-REPL foundation and R27's delivered
Flow/pipe lane, but does not depend on R28 MCP. Its next unreserved identifier
preserves the established R28 epic/E28 issue set and all other published
planning identifiers. R42 should land before R33 needs a reusable interactive
execution seam; R29–R32 do not depend on it and need not wait for it.

R16–R20 are complete portability foundations. R16 supplies the external-host protocol/capability/evidence boundary, R17 arbitrary-precision Integer and ordered-map portability, R18 portable equality/key semantics, R19 Unicode/diagnostic portability, and R20 open-function/extensible-pattern dispatch semantics.

## Exact numeric decomposition

Planning issue #845 supersedes the former single Exact Numeric Model prerequisite branch as an implementation vehicle. PR #839 is not merged. Its approved design and audit evidence are repartitioned into separately gated releases:

- **R21** — numeric source classification and tagged portable Core IR only.
- **R22** — Decimal/Rational/Float64 runtime values, arithmetic, conversions, comparison/equality integration, numeric misuse, and resource-limit semantics.
- **R23** — canonical numeric rendering, format presentation, strict JSON numeric behavior, lexical JSON Decimal decode, and compatibility JSON reconciliation.

The delivery postmortem is `docs/analysis/exact-numeric-gate-postmortem.md`. Each release is expected to use multiple independently mergeable PRs against current `main`; release audits run against merged `main`, and substantive findings become narrow repair PRs followed by fresh audit.

## C++ host arc

R24 is the completed first production C++ implementation release and depends on completed/audited R16–R23. C++ production implementation belongs in `m0smith/genia-cpp`; `genia-2026` remains authoritative for contracts, shared specs, conformance infrastructure, and portability documentation. The completed floor is deliberately bounded and is not Python feature parity.

R25 extended the C++ host with a bounded stateful runtime, and R26 completed
the bounded scripted REPL plus Bytes/UTF-8 and strict JSON data bridges. R27
delivered C++ Flow phase 1 and pipe mode against shared evidence; HTTP serving
and outbound HTTP were deferred (E27-3, E27-4) rather than partially claimed.

## MCP

R28 is the Genia MCP Server release (complete; `docs/releases/R28.md`). It is integration infrastructure, not a new language-semantics layer. Existing epic #700 and issues #701–#707 are the R28/E28-* issue set after renumbering.

R28 is placed after the C++ host expansion arc to keep that arc contiguous. Its own contract may still authorize an initial Python-reference-host implementation; roadmap position alone does not require complete cross-host parity.

## R20 unified-function follow-up

Issue #1067 is scheduled after R28 and before R29 as an unnumbered follow-up to
completed R20. It is not an R28 deliverable and does not renumber later releases.
The gate first repairs/re-validates R20 defects, separately evaluates module
entry-scope isolation, and only then permits a unified internal Function/Clause
contract/runtime refactor if the evidence still supports it. `open` remains
the explicit cross-module extensibility declaration; ordinary functions remain
closed by default. Portable repairs require shared evidence and accurate
Python/C++ conformance claims. Breaking Core IR consolidation remains deferred
to R41 or another separately approved versioned-IR gate.

## Interactive sessions and Jupyter

R42 is the planned persistent interactive-session and first-class Jupyter
kernel release. Issue #1045 is its umbrella. E42-0 defines the narrow
host-neutral session observations; E42-1 implements them in Python and makes
the existing REPL the first consumer; E42-2 adds the minimal Jupyter kernel;
and E42-3 hardens cross-mode behavior and synchronizes release truth. See
[`r42.md`](r42.md).

The session contract is portable where its observations are accepted into
shared conformance, but the initial Jupyter transport is Python-host tooling.
C++ Jupyter support is not a prerequisite, and C++ retains its R26 `repl`
claim without adopting a new API. Completion/inspection and rich display are
soft follow-ups, not blockers for the first kernel. MCP and Jupyter remain
independent: a later notebook may demonstrate MCP-backed work, but basic
kernel tests and examples must be offline and credential-free.

## Data workflow and tooling arc

R29 adds the explicit Sheet record-pipeline boundary. R30 deepens it into shaped whole-column computation. R31 adds relational Sheet operations. R32 adds the portable data-store boundary: ordinary Genia values, Flow, Sheet, Outcome, configuration/secrets, and lifecycle remain the application model while relational, document, key/value, immutable/temporal, query, transaction, and change-feed behavior is exposed only through truthful provider capabilities. R31 is compositional input to R32; it does not make R32 relational. SQLite is the planned embedded proving provider, with a deterministic non-relational fixture required to prevent SQL/table leakage. JDBC, ODBC, ADBC, and native clients are adapter mechanisms rather than language dependencies. The R32 contract must also reconcile naming/authority/lifecycle with R35's later Store/Location/resource architecture rather than create a competing generic Store concept. R33 is developer tooling derived from implemented parser/Core-IR/help/debugger truth. R34 adds reproducible cross-host performance evidence and permits optimization only when shared conformance proves no semantic drift.

After R32 is audited, heterogeneous real-provider proving (at minimum one client/server relational provider, one document or key/value provider, and one change-feed provider) is a separately gated follow-up release candidate rather than an implicit expansion of R32. MongoDB, DynamoDB, PostgreSQL through a standard adapter, ADBC, and Datomic are candidates, not roadmap commitments. See `docs/architecture/portable-data-store-survey.md`.

## Storage, execution, and dogfooding arc

R35 is the portable Store/Location/resource contract. R36 is the location-independent Execution contract. R37 establishes the unified event/subscription spine before R38 defines portable actors, so actor observability can reuse events without reducing actor mailboxes to pub/sub. R39 is the Genia-native conformance-tooling migration, including the Genia-native YAML parser for the contracted shared-spec profile. R41 then packages the existing Core IR portability boundary as stable versioned artifacts. These releases consume prior equality, lifecycle, Flow, host-protocol, and authority boundaries rather than inventing local substitutes.

### Host/Genia responsibility boundary for dogfooding migrations (planning only)

Python-to-Genia migrations in this arc follow one rule: Genia owns portable policy, composition, validation, transformation, orchestration, comparison, aggregation, and reporting; hosts own privileged capabilities, bootstrap, OS integration, external-protocol adapters, and the machinery that implements Genia itself. R28's native MCP server is the reference split. Migration is justified by the policy moved, not by Python lines removed, and no one-off host API is created solely to rewrite a tool.

Dependency note: R39's roadmap dependencies are R18, R35, and R36 (not R33). R33 tooling/introspection is the prerequisite only for the documentation-generation and lint-policy migrations, which also need R35 for writing outputs. R42 stays an independent branch. The host parity gate is part of R39 (see [`r39.md`](r39.md)); a Genia release-check program over evidence bundles is a parking-lot candidate. Rationale and inventory: `docs/analysis/python-to-genia-meaningful-migration-review.md` (non-authoritative).

R8 through R28 are complete; R29 through R42 remain planned and not active unless a specific gate says otherwise. Python remains the full-language reference host; C++ is the bounded R27 production host. Every later behavior slice requires its own contract/design/test/implementation/documentation/audit gates; roadmap placement is not implementation authority.

## Configuration and secret hardening

R40 promotes the outstanding candidates from
`docs/parking-lot/post-r13-configuration-followups.md` (C-1 through C-11) as
one numbered release. It is listed outside the main dependency chain above
because it depends only on completed R10 and R13, not on any release from
R14 onward; it is free to schedule and ship independently, subject to its
own contract/design/test/implementation/documentation/audit gates. See
`docs/strategy/roadmap/r40.md`.

## Required infrastructure — maintained code documentation (#1101)

Define the repository-wide standard and establish initial documentation CI
enforcement after R28, before new R29 implementation. Coordinate with the
unnumbered R20 follow-up #1067 without introducing a new release number.
Remediate existing gaps in bounded subsystem slices alongside roadmap work,
starting with MCP. The entire legacy backlog does not block R29. This work
does not reopen R28 or change language/runtime behavior.
