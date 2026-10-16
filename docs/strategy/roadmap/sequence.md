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
R20 follow-up — Unified Function Model & Open-Function Repairs (#1067) ✓ HISTORICAL
 |              (unnumbered follow-up; does not expand R28)
 v
Pre-R29 semantic gate — function openness and immutable bindings (#1249 → #1250 → #1251)
 |              (unnumbered follow-up; decision/implementation/audit before R29)
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

F2/P2 (module/entry scope isolation) landed through
[#1247](https://github.com/m0smith/genia-2026/pull/1247).
[#1229](https://github.com/m0smith/genia-2026/issues/1229) owns final execution
closeout; #1220 and #1221 are complete and closed.
[#1230](https://github.com/m0smith/genia-2026/issues/1230) owned the temporary
module-to-entry fallback's retirement. The maintainer ruled that implicit module
lookup of entry variables must not become permanent, and the removal change
deletes the fallback and its strict switch; the R29 hard gate is satisfied when
that removal merges, with no exception mechanism used. Optional maintenance
debt is archived in [#1238](https://github.com/m0smith/genia-2026/issues/1238)
for measurement-led consideration alongside R34; it does not block P2 closeout
or R29. Minor residual observations remain in that record for consideration
when related code changes; no new implementation work is authorized here.

## Pre-R29 function-openness and immutable-binding semantics gate

This is an unnumbered **new semantic follow-up**, not a reopening of completed R20 or the historical #1067 work, and not an R28 expansion. Candidate syntax is `f(pattern) = expr` for open-by-default functions, `name =: expr` for immutable lexical bindings, and `f(pattern) =: expr` for closed functions. **None of these proposed changes is implemented or approved by roadmap placement.** Current `GENIA_STATE.md` and `GENIA_RULES.md` remain the behavior authority.

**Gate order:** [#1249](https://github.com/m0smith/genia-2026/issues/1249) is the pre-flight and contract decision; [#1250](https://github.com/m0smith/genia-2026/issues/1250) is approved-contract-only failing specs and bounded implementation; [#1251](https://github.com/m0smith/genia-2026/issues/1251) is integration, host-conformance, documentation truth, and skeptical audit. Do not start language-facing R29 implementation until #1249 explicitly resolves the default-openness, immutable-binding, closed-function clause, and module-extension authority questions, and #1251 records acceptance for any changes deemed prerequisites. R29 planning and independent maintenance may proceed in parallel.

**Hard invariant:** default local openness must not grant implicit cross-module mutation/extension rights. Existing R20 `extend`/`use` authority and dispatch remain in force unless an explicit approved contract changes them. #1067 deliberately excluded removing `open`; that historical constraint must not be silently rewritten. Carry the semantic dependency review forward at R32, R33, R38, and R41 pre-flights to avoid encoding unsettled syntax/IR semantics into new subsystems. Preserve the **independent** R29 implementation gate and 2026-12-14 checkpoint for module compatibility fallback [#1230](https://github.com/m0smith/genia-2026/issues/1230); do not absorb it into these issues. Unrelated cleanup and #1101 legacy documentation remediation remain release-aligned non-blockers.

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

### Named pipeline composition ergonomics (R29–R31, non-blocking)

[#1236](https://github.com/m0smith/genia-2026/issues/1236) is the near-term **contract/pre-flight gate** for named, reusable Flow/Seq pipeline transformations **and terminal operations**, scheduled alongside R29–R31 without blocking R29 intake. Coordinate with unified callable follow-up #1067, Outcome bind #1014, and count ergonomics #1208. Before any implementation, prove that existing `value |> stage` application remains unchanged and resolve source-free stage composition ambiguity: compare a minimal explicit `compose(...)` callable with a narrowly compatible composition syntax. Preserve lazy single-use Flow consumption, terminal input/output contracts, `some/none/err` behavior, observable effects/cleanup, portable Core IR, and Python/C++ shared-spec truth. This is planning only; no new pipeline-composition behavior is implemented by roadmap placement.

### Flow count ergonomics follow-up (R29–R31, non-blocking)

[#1208](https://github.com/m0smith/genia-2026/issues/1208) is a narrow follow-up alongside the R29–R31 data/Flow work, **not a gate for starting R29**. Verify existing `count` semantics and the surrounding pipeline before proposing any change. **Stage A:** prefer evidence-backed O(1) cardinality on intrinsically sized built-ins, without skipping Flow evaluation, errors or cleanup, and reconcile `count`/`length`/`map_count` without a breaking rename. **Stage B:** prove developer-defined countability using application-owned R20 open functions and ordinary values (not by extending the closed prelude `count`). **Stage C:** defer any transparent extension of standard `count`, `counted?` predicate, or new protocol unless a separately approved real use case justifies it. Preserve cross-host/shared-spec truth. R35's [shell-free listing/traversal acceptance case #1209](https://github.com/m0smith/genia-2026/issues/1209) reuses the established counting model. Neither ticket authorizes implementation or enlarges the release contract without pre-flight and phase gates.

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


### Release-aligned documentation debt

Scheduling decision [#1191](https://github.com/m0smith/genia-2026/issues/1191)
keeps [#1101](https://github.com/m0smith/genia-2026/issues/1101) as the
cross-repository completion owner. Initial policy/CI enforcement is delivered;
remaining legacy remediation is scheduled alongside feature work, not as a
separate cleanup campaign or a whole-backlog prerequisite for R29.

| Release home | Owned tech-debt task | Maintained areas |
|---|---|---|
| R29–R31 | [#1192](https://github.com/m0smith/genia-2026/issues/1192) | Data/Flow/Seq/prelude/builtin/value helpers and related examples/tests |
| R32, R35–R36 | [#1193](https://github.com/m0smith/genia-2026/issues/1193) | Providers/model/host adapters, resource IO, lifecycle and execution boundaries |
| R33–R34, R42 | [#1194](https://github.com/m0smith/genia-2026/issues/1194) | Parser/evaluator diagnostics, debugger/editor/session, format and performance tooling |
| R37–R38 | [#1195](https://github.com/m0smith/genia-2026/issues/1195) | Value lifetime, events/concurrency/message helpers and focused fixtures |
| R39 | [#1196](https://github.com/m0smith/genia-2026/issues/1196) | Test/conformance harnesses, protocol adapters, CI/build/scripts and residual test/example debt |
| R40 | [#1197](https://github.com/m0smith/genia-2026/issues/1197) | Protected values/authority/configuration and secret-focused fixtures |
| R41 | [#1198](https://github.com/m0smith/genia-2026/issues/1198) | AST/Core IR/lowering/WIT, numeric/value foundations and residual routing audit |

The release homes follow technical relevance, not numeric execution order:
R40 and R42 remain independently scheduled. Each package covers both repositories
where applicable. Shared files are routed by binding responsibility; no identity
should be claimed by two active slices. Unclassified maintained debt routes to
#1196 for evidence review, then moves to the applicable owner explicitly.

At each release pre-flight, select one narrow coherent slice from its package,
normally one source file or a closely coupled pair, favoring code already touched
by release work. This is a default small work budget, not a quota of findings or
permission to leave changed required bindings undocumented. New/changed code
must satisfy the existing ratchet in its own change. Do not widen a slice merely
to meet a count; unrelated debt does not delay feature acceptance.

The release audit records selected identities, owner, merged PR/check evidence,
remaining current baseline count and the next owned slice in the package issue.
Carry-forward debt stays open with its reason and owner; it never becomes an
implicit exemption or silently disappears. Existing exact baseline identities and
fingerprints remain authoritative inventory; this table is scheduling only.

#1198 performs the residual routing/quality review when R41 is active, not a
blanket requirement to exhaust every legacy gap before R41 ships. Any residual
work retains explicit follow-up ownership under #1101. Parent closure still
requires actual remediation or approved per-binding exemptions plus skeptical
prose-quality audit; releasing a feature or adding a schedule never closes debt.
