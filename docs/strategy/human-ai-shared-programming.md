# Human–AI Shared Programming — Genia Strategy

Status: **Long-term product vision / non-normative strategy**. This document is not a language contract and does not assert that the goals below have been achieved. Implemented behavior is governed by `GENIA_STATE.md`, then the repository's documented source-of-truth hierarchy.

## Goal

**Genia aims to be a shared programming language for humans and large language models, enabling both to express, understand, verify, and evolve computational ideas with greater clarity, reliability, and efficiency.**

The aim is not merely to generate smaller programs or use fewer model tokens. It is to minimize **total effort to a correct, verified, maintainable result** across a human–AI workflow: intent → executable expression → review → execution/tests → diagnosis → refinement.

Human authors and LLM collaborators should work in **one language with one set of semantics**, rather than inventing an AI-only dialect or adding a second syntax for an existing concept.

## Design criteria

Use these questions when evaluating *proposed* language, tool, and documentation work:

1. **Shared comprehensibility:** Can a person understand and review what a model produced, and can a model reliably work from human-authored Genia?
2. **Low ambiguity:** Does the change reinforce canonical patterns and the value-first model rather than introduce redundant ways to express the same computation?
3. **Composable meaning:** Can meaning be communicated through existing patterns, ordinary functions, values, Outcomes, contracts, and pipelines without hidden control flow?
4. **Inspectable failures:** Are behavior, assumptions, errors, and validation results explicit enough for both collaborators to identify and correct mistakes?
5. **Discoverable truth:** Can agents locate accurate, version-appropriate semantics in the source-of-truth docs, language profile, tested examples, and supported MCP interfaces, without guessing?
6. **Executable verification:** Can claims about a program be checked with tests and deterministic, reproducible evidence instead of trusting plausible-looking generated code?

These are evaluation principles, **not authorization for new syntax, builtins, tools, or endpoints**. Current support must be checked against `GENIA_STATE.md` and tests before an example or capability is described as implemented.

## Practical proving ground

Keep **Outcome-aware validated data pipelines** as Genia's first killer workflow:

```text
messy records in → clear pipelines → validated shaped output / reports + useful diagnostics
```

A useful future human–AI collaboration evaluation would ask a person and an LLM to jointly define input constraints, implement a transformation, inspect a deliberate failure, and repair it while preserving validation evidence. This is a proposed evaluation scenario, **not a claim of existing benchmark results**.

## Evidence and measures

Compare equivalent, scoped tasks across Genia and suitable baseline languages (for example Python) with the same inputs, success criteria, access to documentation, models, and review policy. Pre-register the task set, measure repeated trials, and report failures as well as successes.

Candidate measures:

- **Correctness:** proportion of outputs passing agreed behavioral and edge-case checks.
- **Human understanding:** ability to explain behavior, find defects, and safely modify another author's program.
- **LLM reliability:** compilation/execution validity, test success, hallucinated API or syntax rate, and correction rounds.
- **Collaboration:** number of human–model handoffs, clarification cycles, review time, and repair effort.
- **Total efficiency:** elapsed active effort and model/token cost **to a verified result**, not token count alone.
- **Maintenance:** ability to change requirements without regressions or semantic drift.

Avoid unsupported claims that Genia is already faster, more understandable, or better for LLMs than another language.

## Using the goal in future reviews

For proposed changes, ask: **Does this make the same program easier for both a human and an LLM to express, understand, verify, and change—without weakening Genia's canonical semantics or the killer workflow?**

Record a brief tradeoff answer in the relevant future strategy/preflight when material. Do **not** impose a new mandatory gate on an already-scoped release or expand R29 implicitly. Any concrete language or runtime change still follows contract, test, implementation, documentation-sync, and audit phases.

## Long-term principle: compilation and transpilation through Core IR

**Adopted architectural direction (post-R29 consideration, non-normative).**
Genia should be designed so that its **portable Core IR can support interpretation,
compilation, and source-to-source translation** without changing the language's
observable semantics. The same Genia program should have one meaning regardless
of whether a conforming backend interprets Core IR, compiles executable code, or
transpiles to another language.

This is a design criterion for future proposals, **not a claim that native
compilation or transpilation backends exist today**. The current Core IR
portability/conformance boundary remains governed by `GENIA_STATE.md` and
tests. Future implementations must account explicitly for capability/host gaps,
Outcomes and errors, protected values, evaluation and lifecycle ordering, and
cross-host conformance; a backend must not quietly redefine Genia semantics.

Keep **R41 portable Core IR artifacts** as the planned foundation for
compile-once, execute-on-conforming-host workflows. R41 does not automatically
authorize or require native code generation, LLVM, WebAssembly, JavaScript,
Python, C++, or another source-target backend. Any particular target requires
separate justification, approval, evidence and normal process phases.

**R29 is completely unaffected:** no added dependencies, implementation work,
acceptance criteria, release gates, or delivery requirements. This principle
does not expand R41's already approved scope either.

## Long-term principle: preserve safety across execution backends

**Adopted architectural direction (non-normative; apply to future backend
proposals after R29).** Every conforming Genia backend should preserve the
language's *defined* ownership, lifetime, concurrency, failure, and resource
safety guarantees. A backend must reject an unsupported or unsafe operation
rather than silently weaken the applicable contract. This applies whether it
interprets Core IR, compiles executable code, or transpiles to source in
another language.

This is a future design objective, **not a claim that Genia currently provides
Rust-style memory safety, static borrow checking, data-race freedom, or
cross-backend proof of safety**. Define the precise portable guarantees and
their scope before promising them. Distinguish language guarantees from
host-runtime implementation properties, tests, and unsupported host capabilities.
Future FFI/native boundaries, concurrency, resource lifetimes, optimizations,
and generated-code targets need explicit safety obligations and appropriate
negative, adversarial, and cross-host evidence where relevant.

**Process implication to evaluate after R29, not enacted here:** consider a
risk-triggered security review within the existing pre-flight / independent
review workflow for changes affecting untrusted inputs, execution authority,
protected values, declassification, filesystem/network/process effects,
deserialization, concurrency/FFI, or generated-code trust boundaries. A review
should identify assets, threat actors, trust boundaries, abuse cases, mitigations,
and residual risks with focused tests or analysis. Routine documentation and
low-risk internal changes should not require a heavyweight threat model.
Avoid a second approval bureaucracy or claiming an audit proves general safety.

**R29 has no new prerequisites, gates, review obligations, acceptance criteria,
or scope changes.** Any future process rule must be separately approved under
the existing process-change discipline.

## Post-R29 principle: human-owned laws, agent-produced evidence

**Timing: after R29 only.** This is a non-normative design principle inspired by
[Bend's law-driven development](https://github.com/bendlang/bend), not an R29
requirement, release dependency, acceptance criterion, pre-flight task, or
authorization to implement new language features. R29 scope, schedule,
contracts, tests, audits, documentation requirements, and readiness gates
remain exactly as already approved.

**Principle:** Human-approved behavioral laws/invariants define the intended
meaning; an AI collaborator may propose implementations and executable evidence
but must not silently weaken, rewrite, or redefine the law to make its work pass.
An independent review checks that the evidence actually supports the claim.

After R29, evaluate whether this distinction can strengthen Genia's existing
contract → failing-tests/specs → implementation → documentation → independent
audit workflow, reusing current tests and shared conformance evidence first.
Only investigate formal proofs or a dedicated law language if a separately
approved study demonstrates a concrete need. Do not require a new `LAWS`/
`PROOF` file convention, dependent type system, affine typing, termination
checker, compiler/runtime feature, new MCP tool, or additional process gate.

Potential later research (separate from the principle): Bend's pure,
ownership-aware fork-join parallelism and its explicit proof boundaries.
Do not mix this with R29, the R34 performance scope, or R38 actors without
their own future prioritization and approval.

## Development dogfooding: post-task tool review (proposed pilot)

After a substantive LLM-assisted development task, briefly inspect the *purpose* of agent-produced Python, Bash, JavaScript, jq, or similar support code. Identify data processing, validation, diagnostic, or report-generation steps that **might** have been expressed in current Genia. Do not assume Genia should replace Git, shell administration, host-specific utilities, or every working script.

Classify observations as: **already possible in Genia** (adoption/docs opportunity); **possible but awkward** (ergonomics); **not currently supported** (evidenced language/host/tooling gap); **better left to existing tools** (out of scope); or **unknown** (insufficient evidence). Verify any claimed current Genia equivalent against `GENIA_STATE.md`, real host support and runnable evidence; label proposed syntax as hypothetical. The review may report **no meaningful Genia opportunity**.

Keep the post-task note concise. Aggregate and deduplicate observations across tasks, then use the normal roadmap/preflight process to prioritize recurring or important proven gaps—never auto-promote one speculative example to a feature. Start with a bounded, opt-in pilot and evaluate review overhead and false positives before considering a broader process requirement. Do not retain credentials, sensitive logs, or unfiltered tool transcripts. See [pilot issue #1226](https://github.com/m0smith/genia-2026/issues/1226).

## Boundaries and references

- **Implemented semantics:** `GENIA_STATE.md`; supporting `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, and tests.
- **Agent discipline:** `AGENTS.md` and `docs/ai/LLM_CONTRACT.md`. Agent-facing documentation must remain synchronized with verified implementation.
- **Product focus:** `docs/strategy/killer-workflow.md`.
- **Roadmap classification:** `docs/strategy/release-roadmap.md` and `docs/process/08-roadmap-ticketing.md`.
- **Tracking:** https://github.com/m0smith/genia-2026/issues/1224.

This strategy creates **no new Genia behavior**, test obligation, or claim of achieved productivity improvements.
