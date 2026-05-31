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

Sequencing notes:

- Finish the end-to-end diagnostics path before broadening validation ergonomics.
- `validate_each/3` context merging is an R1 follow-up only after parse → validate → collect diagnostic preservation proves the needed context shape.
- Minimal Sheet integration belongs late in R1 only as a landing zone for validated records and diagnostics.
- Rich Sheet/report behavior belongs to R5 unless required for the R1 demo.
- Do not start validation DSL work in R1.

Exit criteria:

- A small but convincing end-to-end validated data pipeline demo exists.
- The demo is backed by tests/specs.
- Docs describe only implemented behavior.

---

## Release R2 — Native Test Kernel ✓ COMPLETE

Theme:

> Let Genia test Genia where Genia-level tests make sense.

Primary outcomes:

- Genia-native tests can cover pipeline, Outcome, validation, and Sheet-facing behavior.
- Native tests complement pytest/specs; they do not replace all Python tests.
- The Python reference host has a minimal native test kernel, CLI entry point, and assertion-helper surface.
- A Genia-native fixture covers part of the validated data pipeline surface.

Includes:

- `genia test <file>` execution mode
- legacy `genia --test <file>` mode
- current `test(name, body)` registration path
- minimal assertions
- file-level test discovery through registered test units
- deterministic test result reporting
- selected shared CLI native-test outcomes
- one native validated-pipeline fixture

Excludes:

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

Implemented annotation-driven test syntax (issue #458):

```genia
@test "basic math works"
test1() = assert_eq(1+1, 2)
```

R2 introduced the `test(name, body)` call form. R3 adds `@test "description"` annotation-driven native test discovery (issue #458): `@test` annotated zero-argument functions are discovered after legacy `test(name, body)` registrations and run through the same native test kernel. The annotation carries the human-readable description; the function name is the test identifier.

Primary outcomes:

- `@test "description"` annotation-driven native test discovery is implemented (issue #458). ✓ done
- Validation helpers are covered by native tests.
- Outcome constructors and rendering behavior are tested at the Genia level.
- JSONL helper behavior is exercised by native tests.
- One or two pipeline examples demonstrate native tests on real workflow behavior.

Includes:

- `@test "description"` annotation + named-function discovery (issue #458) ✓ implemented
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

- Native tests use the `@test "description" / name() = body` form for annotation-driven discovery. The annotation syntax is implemented and documented as current behavior (issue #458). ✓ done
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

Possible includes:

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
  - keep out of R1 unless a narrow validated-pipeline use case explicitly requires it
- browser playground runtime
  - useful as a future demo surface, not required for the first validated-data-pipeline release
- ants / simulation teaching demos
  - useful teaching material after the data-pipeline wedge is demonstrable
  - not a release blocker for R1
- full value-template system
- refinement / shape / contract / variant roadmap
- validation DSL
  - do not create implementation tickets until helper-based validation proves insufficient
- multi-host implementation beyond contract scaffolding
- server mode
- notebook mode
- parallel native test execution

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
