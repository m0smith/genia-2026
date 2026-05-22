# Genia Release Roadmap

Status: Planning guide — non-authoritative. This is not a language contract.

This document orders upcoming Genia releases. It does not define implemented language behavior.
Planned items must not be documented as implemented behavior.

Implemented behavior remains defined by:

1. GENIA_STATE.md
2. GENIA_RULES.md
3. GENIA_REPL_README.md
4. README.md
5. spec/*

This roadmap exists to help LLM agents and maintainers keep planning, issue creation, and release sequencing aligned with the current product direction.

## Product North Star

Genia's first killer workflow is:

> Outcome-aware validated data pipelines.

Plain-language promise:

> messy records in → clear pipelines → validated shaped output / reports + useful diagnostics

New release work should strengthen this workflow unless explicitly approved as infrastructure or parking-lot work.

---

## Release R1 — Killer Workflow Foundation

Theme:

> Make Outcome-aware validated data pipelines feel real, useful, and demonstrable.

Primary outcomes:

- JSONL / CSV / stdin record ingestion path feels smooth.
- Outcome-aware validation helpers are coherent.
- Diagnostics are useful for record/field failures.
- Flow / Seq / Sheet pieces support the data-pipeline story.
- Examples show messy records becoming clean shaped output.

Includes:

- record parsing helpers
- validation helper polish
- collect validated rows
- diagnostic conventions
- Sheet landing-zone improvements
- docs/examples tied to real behavior

Excludes:

- general lifecycle system
- native unit test framework
- actors/concurrency expansion
- browser playground
- speculative value-template syntax

Exit criteria:

- A small but convincing end-to-end validated data pipeline demo exists.
- The demo is backed by tests/specs.
- Docs describe only implemented behavior.

---

## Release R2 — Native Test Kernel

Theme:

> Let Genia test Genia where Genia-level tests make sense.

Primary outcomes:

- Genia-native tests can cover pipeline, Outcome, validation, and Sheet-facing behavior.
- Native tests complement pytest/specs; they do not replace all Python tests.
- The first lifecycle shape is introduced through testing only.

Includes:

- `genia test` execution mode or equivalent test runner entry point
- `@test`
- minimal assertions
- test discovery
- deterministic test result reporting
- minimal module/test lifecycle:
  - init
  - module_before
  - test_before
  - test
  - test_after
  - module_after
  - finalize
- test-scope annotations only:
  - setup
  - teardown
  - test

Excludes:

- arbitrary custom lifecycle definitions
- server/request/actor lifecycles
- parallel native test execution
- property testing
- snapshot testing
- full pytest migration
- changing shared semantic spec authority

Exit criteria:

- Genia-native tests cover part of the validated data pipeline surface.
- Python pytest remains responsible for host/runtime/parser/spec-runner internals.
- Lifecycle semantics are documented as partial and test-runner-scoped.

---

## Release R3 — Lifecycle Generalization

Theme:

> Extract the proven test lifecycle shape into a portable lifecycle contract.

Primary outcomes:

- Lifecycle plans become portable Genia-level data/contracts.
- Annotation discovery is phase-driven and explicit.
- Execution modes can eventually use lifecycle plans without making import/load behavior spooky.

Includes:

- lifecycle plan shape
- phase shape
- scope model
- cleanup rules
- failure rules
- annotation binding model
- source-order / reverse-source-order execution rules
- portable docs for execution-mode lifecycle proposals

Excludes:

- server mode implementation
- actor lifecycle implementation
- arbitrary plugin system
- YAML lifecycle runner unless separately approved
- lifecycle behavior not exercised by tests

Exit criteria:

- Lifecycle is documented as a general model.
- Test lifecycle remains the first implemented consumer.
- No annotations execute merely because they exist.

---

## Release R4 — Native Test Expansion / Pytest Migration Wave 1

Theme:

> Move appropriate Genia-facing tests into Genia-native tests.

Primary outcomes:

- More prelude and language-facing behavior is tested in Genia.
- Python tests remain for Python host internals.
- The split between native tests and pytest is explicit.

Move candidates:

- Outcome helpers
- validation helpers
- Flow/Seq visible behavior
- Sheet helper behavior
- prelude-level utilities
- examples intended to be Genia-facing

Keep in pytest:

- parser internals
- IR normalization
- host adapter behavior
- CLI harness internals
- spec runner implementation
- Python-specific exceptions and plumbing

Exit criteria:

- Native test suite proves useful without duplicating every pytest.
- Documentation explains what belongs in native tests vs pytest.

---

## Release R5 — Data Workflow Hardening

Theme:

> Make validated pipelines feel production-useful.

Possible includes:

- richer diagnostics
- grouped summaries
- report helpers
- Sheet aggregation helpers
- schema/shape inspection helpers
- better command-line ergonomics
- clearer examples for real-world records

Excludes by default:

- actors
- browser-native runtime
- full static type system
- broad value-template implementation

---

## Parking Lot / Later

These are valuable, but not part of the near roadmap unless explicitly promoted:

- actor system
- browser playground runtime
- ants / simulation teaching demos
- full value-template system
- refinement / shape / contract / variant roadmap
- multi-host implementation beyond contract scaffolding
- server mode
- notebook mode
- parallel native test execution

---

## Roadmap Rule for Agents

Before proposing new tickets, agents must classify the work as:

- current release
- next release
- infrastructure
- follow-up
- parking lot

If the work is parking-lot/future, do not create implementation tickets unless explicitly approved.