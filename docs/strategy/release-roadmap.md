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

## Current Release Focus

The active next release is **R2 — Native Test Kernel**.

R2 protects the R1 killer-workflow foundation by adding a small Genia-native testing surface for Genia-facing behavior.

---

## Release R1 — Killer Workflow Foundation ✓ COMPLETE

Theme:

> Make Outcome-aware validated data pipelines feel real, useful, and demonstrable.

**Status: Complete.** The R1 foundation has been implemented and demonstrated.

R1 proved the core pipeline model end-to-end:

```
messy records in → clear pipelines → Outcome-aware validation → clean records + diagnostics out
```

Delivered:

- Outcome value family: `some`, `none`, `err` with pipeline propagation
- Validation helpers: `validate_required`, `validate_field`, `validate_optional`, `validate_record`, `validate_each`
- `collect_validated` terminal helper for aggregating Outcome-aware pipeline results
- Flow / Seq / Sheet pieces supporting the data-pipeline story
- Diagnostic conventions for record/field failures
- Malformed record pipeline diagnostics (issue #398)
- End-to-end validated data pipeline demo (`examples/validated_pipeline_demo.genia`)
- Docs and tests tied to implemented behavior

Excluded from R1 (see R2, R5, or parking lot):

- general lifecycle system
- native unit test framework
- actors/concurrency expansion
- browser playground
- speculative value-template syntax
- CSV / JSONL record-parsing production helpers
- rich Sheet integration beyond minimal landing zone
- grouped diagnostic summaries and report helpers

---

## Release R2 — Native Test Kernel

Theme:

> Let Genia test Genia-facing behavior where Genia-level tests make sense.

R2 protects and exercises the R1 surface through native Genia tests.

**Scope note:** R2 is exclusively the native test kernel. Leftover R1 data-workflow hardening (CSV,
Sheets, diagnostics, report helpers) belongs to R5, not R2.

Primary outcomes:

- A small native test runner exists.
- Genia files can define and run multiple tests.
- Minimal assertions exist.
- Test output and exit codes are deterministic.
- A small part of the R1 validated-pipeline surface is covered by Genia-native tests.
- Pytest and shared specs remain authoritative for host/runtime/parser/spec-runner internals.

Planned R2 scope (not current behavior):

- `genia test <file>` or equivalent test runner entry point
- One small test declaration mechanism (`@test` or a `test_*` naming convention)
- Minimal assertion helpers — likely candidates include `assert_equal`, `assert_true`, `assert_some`,
  `assert_none`, `assert_err`; final names to be contract-defined
- Test discovery
- Deterministic `stdout`, `stderr`, and `exit_code` for: passing tests, failing assertions,
  runtime errors inside tests, and invalid tests
- First Genia-native tests covering a small subset of the R1 surface, such as `parse_jsonl_record`,
  `validate_required`, `validate_optional`, `validate_record`, `validate_each`,
  `collect_validated`, `validated_pipeline_demo`
- Any lifecycle behavior in R2 is test-runner-scoped only; possible minimal hooks may include
  `before_each` / `after_each` or equivalent test phases

### R2 Non-goals

R2 does not include CSV support, Sheet landing-zone work, `render_csv` / `write_csv`, report output,
diagnostic helper framework, value-template implementation, validation DSL, general lifecycle
machinery, actor lifecycle, server/request lifecycle, browser UI, parallel native tests, property
tests, snapshot tests, or full pytest migration. Shared semantic spec authority does not change.

Exit criteria:

1. `genia test <file>` or equivalent exists.
2. A Genia file can define and run multiple tests.
3. Minimal assertions exist.
4. Output and exit codes are deterministic.
5. A small set of R1 validated-pipeline behaviors are covered by Genia-native tests.
6. Docs clearly state pytest and shared specs still own host/runtime/parser/shared conformance internals.
7. Any lifecycle behavior is documented as partial and test-runner-scoped only.

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

This release picks up the data-workflow items deferred from R1. These items were deferred
because R1 proved the core model; they are not required for that proof and belong to production-quality polish.

Deferred R1 items now targeting R5:

- **#405** — post-R1 hardening (deferred from R1)
- **#393** — R5 hardening
- **#394** — conditional / deferred until concrete need is proven
- **#390** — CSV support (record ingestion from CSV files)
- **#395** — Sheet landing zone improvements
- **#396** — depends on #395; schedule after Sheet landing zone lands
- **#363 / #364** — depends on Sheet landing zone; schedule after #395

Possible additional includes:

- richer diagnostics
- grouped summaries
- report helpers
- Sheet aggregation helpers
- schema/shape inspection helpers
- better command-line ergonomics
- clearer examples for real-world records

Deferred candidates after the R1 demo proves the basic workflow:

- richer Sheet integration beyond the minimal R1 landing zone
- `validate_each/3` context merging, if R1 diagnostics reveal a concrete repeated need
- validation DSL exploration, only if plain helpers and value-template work prove insufficient

Excludes by default:

- actors
- browser-native runtime
- full static type system
- broad value-template implementation

---

## Parking Lot / Later

These are valuable, but not part of the near roadmap unless explicitly promoted:

- actor system
  - includes actor lifecycle, supervision, and actor-oriented runtime expansion
  - keep out of R2/R3 unless a narrow use case explicitly requires it
- browser playground runtime
  - useful as a future demo surface, not required for the first validated-data-pipeline release
- ants / simulation teaching demos
  - useful teaching material after the data-pipeline wedge is demonstrable
- full value-template system
  - **#87 / #89 / #91** — broad value-template / contract roadmap issues; future / parking lot
    unless explicitly promoted to a release
- refinement / shape / contract / variant roadmap
- validation DSL
  - do not create implementation tickets until helper-based validation proves insufficient
- multi-host implementation beyond contract scaffolding
- server mode
- notebook mode
- parallel native test execution
- **#399** — future design work; not R2 or near-term; belongs in parking lot until scope is defined
- **#102** — broad scope; should be split into smaller targeted tickets or updated before use
  as a release tracker; do not use as a release blocker in its current form

---

## Post-R1 Issue Disposition

This section records the classification of R1-adjacent issues after R1 completion.

| Issue | Classification | Notes |
|---|---|---|
| #374 | **Closed / completed** | Delivered as part of R1. |
| #405 | Post-R1 hardening → R5 | Keep open; schedule in R5. |
| #393 | R5 hardening | Keep open; schedule in R5. |
| #394 | Conditional / deferred | Keep open; promote when need is concrete. |
| #390 | R5 — CSV support | Keep open; schedule in R5. |
| #395 | R5 — Sheet landing zone | Keep open; schedule in R5. |
| #396 | R5 — after #395 | Keep open; depends on Sheet landing zone. |
| #363 / #364 | R5 — after Sheet landing zone | Keep open; schedule after #395. |
| #399 | Future design | Not R2; park until scope is defined. |
| #87 / #89 / #91 | Parking lot | Future / parking lot unless explicitly promoted. |
| #102 | Needs split or update | Do not use as a broad release blocker; split first. |

If an issue listed above is already closed, do not reopen it.

---

## Roadmap Rule for Agents

Before proposing new tickets, agents must classify the work as:

- current release
- next release
- infrastructure
- follow-up
- parking lot

If the work is parking-lot/future, do not create implementation tickets unless explicitly approved.
