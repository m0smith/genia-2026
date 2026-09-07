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
R16 — Multi-Host Conformance Infrastructure
 |
 +----> R17 — Numeric & Ordered-Map Portability Contract
 |
 +----> R18 — Unicode, Float & Diagnostic Portability Contract
           |
           v
R19 — C++ Minimal Conforming Host
 |
 +----> R20 — C++ Stateful Runtime & Concurrency
 |
+----> R21 — C++ REPL & Data Bridges
           |
           v
R22 — C++ Flow, Pipe Mode & HTTP Serving
 |
 v
R23 — Sheet Record Pipelines
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

R16 is generic required infrastructure for every independently implemented
second host. It also establishes the planned external-host repository boundary,
contract-revision pinning, capability-aware conformance claims, and the
separation between pinned conformance and current-`main` compatibility described
in [`multi-host-conformance-policy.md`](multi-host-conformance-policy.md). R16 may
bootstrap `m0smith/genia-cpp`, but does not implement the real C++ interpreter.

R17 and R18 harden shared contracts in parallel; R19 depends on all three and is
the first planned production C++ implementation release. R19 through R22 place
C++ production implementation in `m0smith/genia-cpp`; `genia-2026` changes during
those releases only when authoritative contracts, shared specs, generic runner
infrastructure, or portability documentation require it. If C++ work exposes an
ambiguous portable behavior, the contract/spec is clarified upstream before the
host implementation proceeds rather than copying Python implementation details.

R20 and R21 extend the C++ host along mostly independent stateful and REPL/data-
bridge tracks. R22 consumes the implemented contracts it needs and closes only
the C++ capabilities it can prove. R23 consumes the explicit Sheet boundaries,
existing Flow/Outcome/validation composition, R14 repeated element lifecycle
semantics, R15 validated-value modeling where applicable, and R16 capability-aware
shared execution. Its placement after R22 avoids renumbering the C++ release arc;
it does not make every C++ implementation release a semantic prerequisite for
the R23 contract.

R8, R9, R10, R11, R12, R13, R14, and R15 are complete. R11, R12, R13, R14, and R15
APIs remain Experimental, Python is the only implemented host, and shared/multi-host
conformance remains Partial. R16 through R22 are planned and not active.
R10/R11/R12/R13 follow-ups require their own gates; R23 is planned and not active.
Every later release requires its own gates. Each later behavior slice requires its
own contract/design/test/implementation/documentation/audit gates; roadmap
placement is not implementation authority.
