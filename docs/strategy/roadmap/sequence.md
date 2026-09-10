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
R18 — Portable Value Equality
 |
 v
R19 — Unicode, Float & Diagnostic Portability Contract
 |
 v
R20 — Open Functions & Extensible Pattern Dispatch
 |
 v
R21 — C++ Minimal Conforming Host
 |
 +----> R22 — C++ Stateful Runtime & Concurrency
 |
 +----> R23 — C++ REPL & Data Bridges
           |
           v
R24 — C++ Flow, Pipe Mode & HTTP Serving
 |
 v
R25 — Sheet Record Pipelines
 |
 v
R26 — Sheet Shaped Computation
 |
 v
R27 — Relational Sheet Operations
 |
 v
R28 — Database Data Boundary
 |
 v
R29 — Developer Experience & Language Tooling
 |
 v
R30 — Cross-Host Performance & Optimization Evidence
 |
 v
R31 — Portable Storage & Resource Semantics
 |
 v
R32 — Location-Independent Genia Execution
 |
 v
R33 — Genia-Native Conformance Tooling
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
is the next planned foundational portability release and settles the equality
relation that R17 intentionally left separate from ordered-map iteration:
structural equality for ordinary immutable values, identity for logical runtime
entities, authority-aware opaque-token equality, protected-value non-oracle
behavior, legal-key reflexivity, NaN key exclusion, and equal-key hash/keying
consistency. R18 also permanently keeps `==` out of Open Function overloading so
future domain-specific equivalence remains an explicit predicate rather than
changing map/pattern/assertion semantics.

R19 then specifies the remaining Unicode, float-display, and diagnostic
portability surfaces. R20 promotes open functions / extensible pattern dispatch
from the parking lot into an explicit host-agnostic language-semantics release.
Its contract must settle local repeated-clause grouping, explicit cross-module
extension, deterministic dispatch and ambiguity behavior, provenance,
import-order independence, and inert import semantics before a second host
implements those rules; R20 must consume R18 rather than making `==` extensible.

R21 depends on R16, R17, R18, R19, and R20 and is the first planned production
C++ implementation release. R21 through R24 place C++ production implementation
in `m0smith/genia-cpp`; `genia-2026` changes during those releases only when
authoritative contracts, shared specs, generic runner infrastructure, or
portability documentation require it. If C++ work exposes an ambiguous portable
behavior, the contract/spec is clarified upstream before the host implementation
proceeds rather than copying Python implementation details.

R22 and R23 extend the C++ host along mostly independent stateful and REPL/data-
bridge tracks. R24 consumes the implemented contracts it needs and closes only
the C++ capabilities it can prove. R25 consumes the explicit Sheet boundaries,
existing Flow/Outcome/validation composition, R14 repeated element lifecycle
semantics, R15 validated-value modeling where applicable, and R16 capability-aware
shared execution. Its placement after R24 avoids interleaving the Sheet release
with the C++ host-parity arc; it does not make every C++ implementation release a
semantic prerequisite for the R25 contract.

R26 deepens R25's explicit Sheet boundary into shaped whole-column computation:
scalar lifting, shape conformance, column expressions, and narrowly defined
elemental lifting remain part of the same immutable value model. R27 then adds
relational Sheet operations such as grouping, summarization, ordering, and
explicit joins without creating SQL syntax or a parallel dataframe/query model.
R28 uses the resulting validated relational workflow as the basis for one narrow,
explicit database source/sink boundary, reusing R10/R13 protected configuration,
R14 lifecycle ownership, Flow/Seq processing, Outcomes, and Sheets rather than
inventing ORM or database-specific pipeline semantics.

R29 is a tooling release rather than a language-semantics release. It should make
the implemented parser/Core-IR/help/debugger truth easier to use through
formatting, navigation, diagnostics, and editor integration without creating an
editor-local language definition. R30 follows the second-host and shaped-data
work with reproducible cross-host performance evidence; optimization is allowed
only where measurements justify it and shared conformance proves no observable
semantic drift.

R31 is approved roadmap placement for a future portable Store/Location/resource
contract, not implemented behavior. It directly supports the killer workflow's
file/source boundary and the later Genia-native spec-runner migration. R31 keeps
Location as a Store-relative inert structural value, Store as an explicit bounded
identity-bearing capability value, and Revision as an authority-aware opaque
semantic token, all consuming R18 equality rather than inventing storage-local
comparison rules. Revision/resource observations remain provider-neutral and
portable concurrency is based on explicit preconditions rather than assumed
filesystem rename/locking semantics. It reserves future streaming-resource
behavior on the existing pull-based Flow model with bounded read-ahead,
downstream-demand-driven production, backpressure, and finalization, but does not
require storage streaming in the first acceptance slice. Its conceptual
dependencies are R10/R13 configuration/protection, R14 lifecycle ownership,
current Flow/Outcome behavior, R16 host-capability discipline, and R18 equality;
later cloud providers must preserve the same application-level contract rather
than adding provider-specific pipeline semantics.

R32 is approved roadmap placement for a future location-independent Execution
contract, not implemented behavior. It consumes R14 lifecycle ownership, R16 host
protocol/capability/revision lessons, and R18 identity/opaque-token equality;
separates inert work description from placement/authority/provider mechanics;
treats local execution as the first provider rather than the semantic model; and
consumes R31 storage authority when execution needs storage access rather than
defining filesystem behavior itself. Although numbered after R31, its core
execution semantics remain conceptually rooted in R14 + R16 + R18. Later
actor-distribution or durable-job work should reuse R32 rather than invent a
second launch/placement/compatibility model.

R33 depends on R18, R31, and R32 and is the planned Genia-native
conformance-tooling migration. Its storage/discovery stage MUST consume R31
rather than adding ad hoc local filesystem helpers. Its external-invocation stage
MUST consume R32 rather than adding an ad hoc subprocess API. Its comparison and
key semantics MUST consume R18 rather than adding runner-specific equality. The
Genia runner should first prove local-provider parity with the existing R16
runner and then prove provider-independence with one deliberately small remote
fixture: switching approved Store or execution provider/placement configuration
must not require changes to the runner program, shared cases, or conformance
semantics. Python runner/bootstrap infrastructure remains until independent
parity/evidence justifies a separate removal gate.

R8 through R17 are complete. R11, R12, R13, R14, and R15 APIs remain
Experimental, Python is the only implemented production host, and shared/multi-
host conformance remains Partial. R16's E16-0 through E16-8 sequence is complete
(issues #757-#765; epic #756 closed; skeptical audit PASS in
`docs/releases/R16.md`). No real second production host is implemented yet.
R18 through R33 are planned and not active. R10/R11/R12/R13 follow-ups require
their own gates. Every later release requires its own gates. Each later behavior
slice requires its own contract/design/test/implementation/documentation/audit
gates; roadmap placement is not implementation authority.
