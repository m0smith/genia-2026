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
 +----> R17 — Numeric & Ordered-Map Portability Contract
 |
 +----> R18 — Unicode, Float & Diagnostic Portability Contract
           |
           v
R19 — Open Functions & Extensible Pattern Dispatch
 |
 v
R20 — C++ Minimal Conforming Host
 |
 +----> R21 — C++ Stateful Runtime & Concurrency
 |
 +----> R22 — C++ REPL & Data Bridges
           |
           v
R23 — C++ Flow, Pipe Mode & HTTP Serving
 |
 v
R24 — Sheet Record Pipelines
 |
 v
R25 — Sheet Shaped Computation
 |
 v
R26 — Relational Sheet Operations
 |
 v
R27 — Database Data Boundary
 |
 v
R28 — Developer Experience & Language Tooling
 |
 v
R29 — Cross-Host Performance & Optimization Evidence
 |
 v
R30 — Location-Independent Genia Execution
 |
 v
R31 — Genia-Native Conformance Tooling
```

This ordering does not imply that every release is a strict technical dependency
of the next. The main semantic chain begins with R9: R10 consumes R9
representations; R11 consumes R9 structured values plus R10
configuration/secrets; R12 builds on R11 AI composition. R13 is a focused
post-R10 ergonomics release that preserves R10 semantics. R14 consumes R13's
configuration-resolution ergonomics and builds on the R4/R8 lifecycle/server
foundation while preserving R10 protected-value boundaries. R15 extends R9's
Template foundation with explicitly planned validated-value modeling while
remaining independent of R14's HTTP implementation.

R16 is complete required infrastructure for independently implemented second
hosts. It establishes the external-host repository boundary, contract-revision
pinning, capability-aware conformance claims, deterministic evidence, and the
separation between pinned conformance and current-`main` compatibility described
in [`multi-host-conformance-policy.md`](multi-host-conformance-policy.md). The
generic `tools/spec_runner --host` path is implemented and proven against the
Python reference host and the non-semantic `m0smith/genia-cpp` bootstrap
placeholder. R16 does not implement a real C++ interpreter.

R17 has completed its shared numeric and ordered-map portability contract. R18
is the next planned portability-contract release. R19 then promotes
open functions / extensible pattern dispatch from the parking lot into an
explicit host-agnostic language-semantics release. Its contract must settle local
repeated-clause grouping, explicit cross-module extension, deterministic dispatch
and ambiguity behavior, provenance, import-order independence, and inert import
semantics before a second host implements those rules.

R20 depends on R16, R17, R18, and R19 and is the first planned production C++
implementation release. R20 through R23 place C++ production implementation in
`m0smith/genia-cpp`; `genia-2026` changes during those releases only when
authoritative contracts, shared specs, generic runner infrastructure, or
portability documentation require it. If C++ work exposes an ambiguous portable
behavior, the contract/spec is clarified upstream before the host implementation
proceeds rather than copying Python implementation details.

R21 and R22 extend the C++ host along mostly independent stateful and REPL/data-
bridge tracks. R23 consumes the implemented contracts it needs and closes only
the C++ capabilities it can prove. R24 consumes the explicit Sheet boundaries,
existing Flow/Outcome/validation composition, R14 repeated element lifecycle
semantics, R15 validated-value modeling where applicable, and R16 capability-aware
shared execution. Its placement after R23 avoids interleaving the Sheet release
with the C++ host-parity arc; it does not make every C++ implementation release a
semantic prerequisite for the R24 contract.

R25 deepens R24's explicit Sheet boundary into shaped whole-column computation:
scalar lifting, shape conformance, column expressions, and narrowly defined
elemental lifting remain part of the same immutable value model. R26 then adds
relational Sheet operations such as grouping, summarization, ordering, and
explicit joins without creating SQL syntax or a parallel dataframe/query model.
R27 uses the resulting validated relational workflow as the basis for one narrow,
explicit database source/sink boundary, reusing R10/R13 protected configuration,
R14 lifecycle ownership, Flow/Seq processing, Outcomes, and Sheets rather than
inventing ORM or database-specific pipeline semantics.

R28 is a tooling release rather than a language-semantics release. It should make
the implemented parser/Core-IR/help/debugger truth easier to use through
formatting, navigation, diagnostics, and editor integration without creating an
editor-local language definition. R29 follows the second-host and shaped-data
work with reproducible cross-host performance evidence; optimization is allowed
only where measurements justify it and shared conformance proves no observable
semantic drift.

R30 is approved roadmap placement for a future location-independent Execution
contract, not implemented behavior. It consumes R14 lifecycle ownership and R16
host protocol/capability/revision lessons, separates inert work description from
placement/authority/provider mechanics, treats local execution as the first
provider rather than the semantic model, and explicitly excludes actor mailbox,
durable-job, scheduler, retry, arbitrary-closure-shipping, shell, storage, and
equality semantics. Although numbered after R29, its conceptual dependency is
R14 + R16; later actor-distribution or durable-job work should reuse R30 rather
than invent a second launch/placement/compatibility model.

R31 depends on R30 and is the planned Genia-native conformance-tooling migration.
Its external-invocation stage MUST consume R30 rather than adding an ad hoc
subprocess API. It must also consume separately approved storage/resource
discovery and equality/comparison contracts for the runner's remaining boundary
needs. The Genia runner should first prove local-provider parity with the existing
R16 runner and then prove provider-independence with one deliberately small remote
fixture: switching execution provider/placement must not require changes to the
runner program, shared cases, or conformance semantics. Python runner/bootstrap
infrastructure remains until independent parity/evidence justifies a separate
removal gate.

R8 through R17 are complete. R11, R12, R13, R14, and R15 APIs remain
Experimental, Python is the only implemented production host, and shared/multi-
host conformance remains Partial. R16's E16-0 through E16-8 sequence is complete
(issues #757-#765; epic #756 closed; skeptical audit PASS in
`docs/releases/R16.md`). No real second production host is implemented yet.
R18 through R31 are planned and not active. R10/R11/R12/R13 follow-ups require
their own gates. Every later release requires its own gates. Each later behavior
slice requires its own contract/design/test/implementation/documentation/audit
gates; roadmap placement is not implementation authority.
