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

## Boundaries and references

- **Implemented semantics:** `GENIA_STATE.md`; supporting `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, and tests.
- **Agent discipline:** `AGENTS.md` and `docs/ai/LLM_CONTRACT.md`. Agent-facing documentation must remain synchronized with verified implementation.
- **Product focus:** `docs/strategy/killer-workflow.md`.
- **Roadmap classification:** `docs/strategy/release-roadmap.md` and `docs/process/08-roadmap-ticketing.md`.
- **Tracking:** https://github.com/m0smith/genia-2026/issues/1224.

This strategy creates **no new Genia behavior**, test obligation, or claim of achieved productivity improvements.
