# Writing

You are working in:

https://github.com/m0smith/genia-2026

Mission

Turn the completed Python-Only to C++ Portability Audit into a concrete, reviewable portability-preparation architecture and execution plan for Genia.

This is primarily an architecture, documentation, conformance-design, and issue-planning task.

DO NOT begin implementing C++ capability families.

DO NOT widen R24.

DO NOT renumber the roadmap.

DO NOT silently change Genia semantics.

The purpose is to make the distinction explicit between:

1. portable Genia semantics currently implemented only by the Python reference host,

2. portable semantics whose shared conformance evidence is incomplete,

3. host capabilities with portable Genia-visible contracts,

4. genuinely Python-specific interoperability,

5. Python implementation details,

6. intentionally nonportable behavior,

7. unresolved architectural decisions.

The result should make R24–R27 safer to implement without allowing Python implementation mechanisms to become accidental Genia semantics.

---

Execution recommendation

Use Claude Code with the strongest available reasoning model.

Recommended:

- model: Claude Opus-class model

- reasoning/thinking: high

- mode: repository-wide architecture/review work

- implementation autonomy: LOW for runtime behavior, HIGH for documentation analysis and issue planning

This task benefits more from careful reconciliation than from coding speed.

Use subagents where useful, but the lead agent must reconcile all conclusions against the authoritative repository documents before accepting them.

Good parallel discovery tracks are:

1. documentation/status drift

2. shared spec/conformance gaps

3. host capability registry and "requires" metadata

4. Core IR portability enforcement

5. R11/R12 provider fixture portability

6. lifecycle/concurrency portability evidence

7. roadmap/dependency reconciliation

These discovery tracks may run in parallel.

Decisions, roadmap edits, issue decomposition, and final conclusions must be integrated serially by the lead agent.

If subagents disagree, return to the authoritative sources rather than averaging their conclusions.

---

Mandatory repository discipline

Before doing anything else:

1. Confirm the current branch.

2. Confirm the working tree status.

3. Fetch/update knowledge of "main".

4. DO NOT work directly on "main".

5. Create and switch to a dedicated branch, for example:

   "portability-preparation-plan"

   or, if an issue already exists:

   "issue-<number>-portability-preparation"

6. Report the branch being used.

Do not merge or rebase unless explicitly asked.

Do not modify "m0smith/genia-cpp" in this task.

---

Required reading

Read completely before proposing changes:

- "AGENTS.md"
- "GENIA_STATE.md"
- "GENIA_RULES.md"
- "GENIA_REPL_README.md"
- "README.md"
- "docs/ai/LLM_CONTRACT.md"
- "docs/process/run-change.md"
- "docs/process/08-roadmap-ticketing.md"
- "docs/strategy/killer-workflow.md"
- "docs/strategy/release-roadmap.md"
- relevant files under "docs/strategy/roadmap/", especially:
  - R21–R24
  - R25–R29
  - release sequence/dependencies
  - multi-host conformance policy
- relevant "docs/host-interop/*"
- relevant "docs/architecture/*"
- current host capability registry
- generic spec-runner/host-adapter protocol
- current shared "spec/**"
- relevant Python implementation only when needed to distinguish mechanism from semantics

Also locate and read the repository copy of the Python-Only to C++ Portability Audit if it has been committed.

If it has not been committed, STOP and report that fact rather than reconstructing the audit from memory.

"GENIA_STATE.md" is final authority for implemented behavior.

Planning documents do not implement behavior.

Implementation mechanisms do not define semantics.

---

Audit baseline

The portability audit reconciled approximately 43 capability families into these categories:

- P1 — portable contract; Python implementation only
- P2 — portable in principle; specification/conformance incomplete
- P3 — host capability with portable Genia semantics
- P4 — genuine Python interoperability
- P5 — Python implementation detail
- P6 — intentionally nonportable under current architecture
- P7 — architectural decision required

Do not blindly trust those labels.

Verify the load-bearing classifications against current "main".

The audit is input evidence, not a new semantic authority.

---

Architectural principle

Use this rule throughout:

«Genia portability requires equivalent observable behavior, not equivalent host implementation mechanisms.»

Python mechanisms such as:

- classes
- closures
- generators
- exceptions
- threads
- queues
- "urllib"
- "pathlib"
- "json"
- Python reflection
- Python package/resource layout

must not become normative merely because the Python reference host currently uses them.

A future C++ host may use completely different native mechanisms while satisfying the same Genia-visible contract.

Conversely, do not call something portable merely because it would be easy to implement in C++.

Portability requires an adequate contract and adequate cross-host conformance evidence.

---

Scope

Produce a portability-preparation plan spanning R24–R27 and later explicitly-owned work where necessary.

The preparation effort must NOT become another numbered release unless existing repository policy absolutely requires that. Prefer a cross-cutting infrastructure/preparation track associated with the releases it unblocks.

R24 remains:

C++ Minimal Conforming Host

Do not enlarge its pinned floor merely because the audit discovered additional portable behavior.

R25–R27 may consume preparation work when their capability families become relevant.

R35 remains the durable owner of portable Store/Location/resource semantics unless current authoritative docs say otherwise.

---

Phase 1 — Reconcile the audit against current main

Create a master reconciliation matrix.

For every audited capability family record:

- capability
- audit classification
- authoritative current status
- portable semantic contract?
- Python-only implementation mechanism?
- shared conformance evidence?
- external-host-capable evidence?
- host capability required?
- current roadmap owner
- missing prerequisite
- recommended action
- whether audit classification still stands

Pay special attention to:

- parser/lowering/Core IR
- evaluator/core values
- Flow/Seq
- CLI
- REPL
- help/doc metadata
- native tests
- lifecycle planning and scope-tree data
- configuration
- environment and ".env"
- R11 model providers
- R12 retrieval providers
- lifecycle runtime
- outbound HTTP
- inbound HTTP
- refs
- processes/mailboxes
- cells/actors
- bytes/UTF-8
- strict JSON
- compatibility JSON/JSONL
- CSV
- ZIP
- ResourceRef/filesystem
- bare file helpers
- seeded random Flow
- base seeded RNG
- unseeded random/sleep
- shell stage
- Python FFI
- module/source acquisition
- terminal capabilities
- Python-only optimizer/runtime internals

Do not infer features that are not currently implemented.

---

Phase 2 — Documentation drift

Verify the audit's documentation-drift findings.

At minimum investigate:

1. whether Core IR portability documentation still says the generic multi-host runner is unimplemented;
2. UTF-8 encode/decode classification;
3. seeded randomness wording;
4. "doc_help" classification;
5. R11/R12 Python-host wording versus portable callable/value/Outcome semantics;
6. R14 lifecycle wording versus Python implementation mechanics;
7. configuration snapshot/provider wording;
8. strict JSON versus compatibility JSON/ZIP grouping;
9. CLI helper wording;
10. optional manifest capability / "requires" metadata.

Classify each as:

- genuine drift
- no longer present
- wording ambiguity
- semantic disagreement requiring human decision

Documentation fixes must not claim capabilities are implemented in C++.

Keep these concepts visibly separate:

- portable contract
- Python reference implementation
- shared conformance evidence
- host capability
- optional capability
- planned portability

---

Phase 3 — Resolve or isolate P7 decisions

Investigate the two major architectural decisions identified by the audit.

A. Base seeded RNG

Determine exactly what current authorities promise.

Answer:

- Does same seed require the same exact sequence across conforming hosts?
- Or is only deterministic behavior within a host required?
- Are the Flow RNG helpers intentionally weaker than base RNG?
- Is the algorithm/state transition intended to be normative?
- Would exact cross-host vectors strengthen Genia's portability goals or unnecessarily freeze an implementation algorithm?

Do NOT silently choose a semantic answer if authoritative documents conflict.

If there is a genuine conflict, write a decision document/ADR-style proposal with alternatives, consequences, and recommendation for human approval.

B. Bare file helpers

Determine the intended future of:

- "read_file"
- "write_file"

Evaluate three possibilities:

1. promote them into portable semantics;
2. permanently classify them as host-specific convenience APIs;
3. treat them as legacy helpers eventually superseded by R35 Store/Location/resource semantics.

Do not port them merely because doing so is mechanically easy.

Protect the existing R35 architecture from accidental duplication.

If human approval is required, create a decision proposal rather than changing semantics.

---

Phase 4 — Systematic capability metadata

Design a systematic model for optional host capabilities and shared-spec applicability.

Audit current capability advertisements and YAML "requires" usage.

The goal is:

- a host advertises only capabilities it implements;
- a shared case declares capabilities it genuinely requires;
- unsupported remains UNSUPPORTED;
- unsupported must never count as PASS;
- base portable semantics remain distinguishable from optional host capabilities.

[Continue by reading the remainder of the original task context from this file. The source uploaded to ChatGPT is authoritative for the full task instructions.]