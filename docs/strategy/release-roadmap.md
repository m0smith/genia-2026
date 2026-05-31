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

## Release R2 — Native Test Kernel ✓ COMPLETE

Theme:

> Let Genia test Genia where Genia-level tests make sense.

Primary outcomes:

- Genia-native tests can cover pipeline, Outcome, validation, and Sheet-facing behavior.
- Native tests complement pytest/specs; they do not replace all Python tests.
- The Python reference host has a minimal native test kernel, CLI entry point, and assertion-helper surface.
- A Genia-native fixture covers part of the validated data pipeline surface.

R2 protects and exercises the R1 surface through native Genia tests.

- `genia test <file>` execution mode
- legacy `genia --test <file>` mode
- current `test(name, body)` registration path
- minimal assertions
- file-level test discovery through registered test units
- deterministic test result reporting
- selected shared CLI native-test outcomes
- one native validated-pipeline fixture

Primary outcomes:

- arbitrary custom lifecycle definitions
- annotation-driven native test discovery
- setup/teardown annotations
- generalized module/test lifecycle hooks
- server/request/actor lifecycles
- parallel native test execution
- property testing
- snapshot testing
- full pytest migration
- changing shared semantic spec authority

Exit criteria:

- Genia-native tests cover part of the validated data pipeline surface.
- Python pytest remains responsible for host/runtime/parser/spec-runner internals.
- Native-test behavior is documented as Experimental, Python reference host only.

---

## Release R3 — Native Test Expansion Wave 1

Theme:

> Grow native test coverage over Genia-facing behavior without touching parser/IR/host internals.

Desired test syntax:

```genia
@test("basic math works")
test1() = assert_eq(1+1, 2)
```

R2 currently uses the implemented `test(name, body)` call form. R3 plans to adopt the annotation + named-function style as the preferred authoring shape after it is separately contracted, tested, implemented, and reflected in `GENIA_STATE.md`. The planned annotation carries the human-readable description; the function name is intended for identification and filtering.

Primary outcomes:

- Validation helpers are covered by native tests.
- Outcome constructors and rendering behavior are tested at the Genia level.
- JSONL helper behavior is exercised by native tests.
- One or two pipeline examples demonstrate native tests on real workflow behavior.
- Planned preferred tests are authored in the `@test("description") / name() = body` form only after that surface exists.

Includes:

- planned `@test("description")` annotation + named-function syntax work
- native tests for validation helpers
- native tests for Outcome constructors and rendering
- native tests for JSONL helper behavior
- one or two end-to-end pipeline example tests

Excludes:

- parser internals
- IR normalization
- host adapter behavior
- lifecycle generalization (see R4)
- pytest migration (see R5)
- setup/teardown, fixtures, parameterization, broad discovery, or multi-host claims

Exit criteria:

- Native tests use the `@test("description") / name() = body` syntax after that syntax is implemented and documented as current behavior.
- Native tests cover validation helpers, Outcome constructors/rendering, and JSONL helper behavior.
- At least one pipeline example is backed by a native test.
- No parser, IR, or host internals are touched.

---

## Release R4 — Lifecycle Generalization

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

## Release R5 — Native Test Expansion / Pytest Migration Wave 1

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

## Release R6 — Data Workflow Hardening

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

- possible file-search helper for CLI-native data workflow setup
  - direct call shape: `find(root, opts)`
  - options are represented as a plain validated options record
  - initial file-search results should compose with Flow/Seq-style pipelines

- Option Record Pattern for APIs with many optional settings
  - default options value
  - plain options record
  - pure modifier functions
  - final validation before execution

- file-search options as the first concrete example:
  - `default_find_options()`
  - `with_pattern(...)`
  - `with_max_depth(...)`
  - `with_follow_symlinks(...)`
  - `validate_find_options(...)`

- diagnostics for unknown or invalid options

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

- record-derived `with_*` helper generation
  - possible future opt-in form: `@derive(quote(withers))`
  - generated helpers must be namespaced under the record/template
  - generated helpers must not create global `with_*` functions
  - promote only after multiple APIs prove the manual Option Record Pattern is valuable

- automatic global `with_*` helper generation
  - rejected by default: risks namespace collisions, unclear origin, and excessive implicit API surface

---

## Roadmap Rule for Agents

Before proposing new tickets, agents must classify the work as:

- current release
- next release
- infrastructure
- follow-up
- parking lot

If the work is parking-lot/future, do not create implementation tickets unless explicitly approved.
