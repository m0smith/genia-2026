# Issue #151 Verification Preflight

=== GENIA PRE-FLIGHT ===

CHANGE NAME:
Verify #151 stdlib contract shared specs

Date: 2026-04-26

## 0. Branch

- Starting branch: `main`
- Working branch: `issue-151-stdlib-contract-shared-specs-preflight`
- Branch status: newly created locally from `main`
- Base observed locally: `2b7e5bb` (`origin/main`, `main`)

## 1. Issue Status

- GitHub issue: #151, "Subtask for #116: Add stdlib contract shared specs"
- Observed status: `OPEN`
- Observed state reason: `REOPENED`
- Closed: no
- Close reason: not visible because the issue is open
- Parent relationship: issue body says `Parent: #116`
- Parent issue #116: open; goal is to expand shared spec coverage across parse, IR, CLI, flow, errors, pipeline, options, pattern matching, and stdlib contract tests
- Current main contains an earlier #151 phase trail, but that trail is a no-behavior-change/process trail, not the stdlib shared-spec work requested by the #151 issue body

## 2. Scope Lock

This verification includes:

- locating shared specs for stdlib behavior
- checking coverage for `map`, `filter`, `first`, and related contract-level functions
- checking runner behavior tests where applicable
- checking docs/spec synchronization
- identifying gaps or drift

This verification does NOT include:

- implementation
- adding new specs
- changing docs outside this preflight artifact
- changing runtime behavior
- new language semantics
- broad stdlib normalization

## 3. Source Of Truth

Authoritative files read:

- `AGENTS.md`
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `spec/README.md`
- `spec/eval/README.md`
- `spec/flow/README.md`
- `spec/cli/README.md`
- issue #151
- parent issue #116

Relevant documented behavior:

- `GENIA_STATE.md` is final authority.
- Python is the only implemented host and the reference host.
- Active executable shared spec categories are `parse`, `ir`, `eval`, `cli`, `flow`, and `error`, with partial/initial coverage labels where applicable.
- Shared eval specs compare normalized `stdout`, `stderr`, and `exit_code`.
- Shared flow specs compare normalized `stdout`, `stderr`, and `exit_code` for first-wave observable Flow behavior.
- Shared CLI specs compare normalized `stdout`, `stderr`, and `exit_code` for deterministic file, command, and pipe modes; REPL is excluded.
- `GENIA_REPL_README.md` documents public stdlib helpers including `reduce`, `map`, `filter`, `first`, `last`, `nth`, `find_opt`, `range`, and Flow transforms including `lines`, `map`, `filter`, `take`, and `rules`.
- `GENIA_RULES.md` documents canonical list access helpers: `first(list) -> some(value) | none("empty-list")`, `last(list) -> some(value) | none("empty-list")`, and `nth(index, list) -> some(value) | none("index-out-of-bounds", { index: i, length: n })`.
- `GENIA_RULES.md` also documents Flow phase-1 helpers including `lines`, `map`, `filter`, `take`, `rules`, `each`, `run`, and `collect`.
- `AGENTS.md` requires phase isolation: preflight, spec, design, test, implementation, docs, audit, each as a separate prompt and commit.

Drift note:

- `GENIA_RULES.md` section "Observable Spec Contract" still says only `eval`, `ir`, and `cli` are active and other categories are scaffold-only. That conflicts with `GENIA_STATE.md`, `README.md`, and `spec/README.md`, which say `parse`, `flow`, and `error` are active too. Because `GENIA_STATE.md` is final authority, this is a doc sync risk, not a source of behavior truth.

## 4. Current Repo Inspection

Relevant `spec/` directories:

- `spec/eval/`: active eval shared specs.
- `spec/flow/`: active first-wave Flow shared specs.
- `spec/cli/`: active CLI shared specs.
- `spec/ir/`, `spec/error/`, and `spec/parse/`: active non-stdlib-adjacent shared spec categories in current main.

Stdlib-adjacent shared spec files observed:

- `spec/eval/pipeline-map-sum.yaml`: list pipeline using `map` and `sum`.
- `spec/eval/map-items.yaml`: `map_items` over persistent maps.
- `spec/eval/map-keys.yaml`: `map_keys` over persistent maps.
- `spec/eval/map-values.yaml`: `map_values` over persistent maps.
- `spec/eval/map-items-map-item-key-pipeline.yaml`: `map_items(...) |> map(map_item_key)`.
- `spec/eval/map-items-map-item-value-pipeline.yaml`: `map_items(...) |> map(map_item_value)`.
- `spec/eval/first-on-flow-type-error.yaml`: misuse of value helper `first` against a Flow.
- `spec/eval/reduce-on-flow-type-error.yaml`: misuse of `reduce` against a Flow.
- `spec/eval/each-on-list-type-error.yaml`: misuse of Flow sink `each` against a list.
- `spec/flow/flow-keep-some-parse-int.yaml`: Flow `map(parse_int) |> keep_some |> collect`.
- `spec/flow/count-as-pipe-stage-type-error.yaml`: value helper/reducer misuse in Flow mode.
- `spec/cli/pipe_mode_map_parse_int.yaml`: pipe mode accepts `map(parse_int) |> keep_some |> each(print)`.
- `spec/cli/command_mode_collect_sum.yaml`: command mode final value using `map(parse_int)`, `keep_some`, `collect`, and `sum`.

Runner behavior tests observed:

- `tests/test_spec_ir_runner_blackbox.py` asserts discovery/execution for selected eval, CLI, flow, error, and IR cases.
- `tests/test_cli_shared_spec_runner.py` asserts CLI shared spec loading, execution, normalization, runner integration, and selected CLI fixture behavior.
- `tests/test_issue_151_phase_docs.py` only checks phase artifact presence and phase-plan ordering; it does not verify stdlib shared spec coverage.

Related unit tests observed:

- `tests/test_stdlib_prelude_basics.py` covers local runtime behavior for `first`, `last`, `nth`, `map`, and `filter`.
- `tests/test_autoload.py` covers autoload behavior for list helpers and higher-order `map`/`filter`.
- `tests/test_flow_phase1.py`, `tests/test_flow_unix_scenarios.py`, and CLI pipe-mode tests cover Flow/CLI use of `map`, `filter`, `keep_some`, and related helpers.

History observed locally:

- `cb81d19` merged PR #158 from a branch named `codex/address-preflight-issue-#151`.
- `0b422b0` is `audit(process): verify issue #151 no-delta trail issue #151`.
- The #151 commit changed only process/architecture artifacts and a targeted artifact test. It did not add stdlib shared spec YAML files.
- Current main later contains issue #162 stdlib normalization work, including value-vs-Flow boundary specs that overlap with some #151-adjacent concerns.

## 5. Expected Contract Coverage

Current specs cover:

- `map`: partial. Covered in eval via list pipeline with `sum`, map-item key/value pipelines, CLI pipe-mode parse usage, and Flow `map(parse_int)` usage.
- `filter`: partial to not present as direct shared contract. It appears in docs and host-local tests, but no direct shared spec file was found for list `filter` or Flow `filter`.
- `first`: partial. Covered as a Flow misuse error in `spec/eval/first-on-flow-type-error.yaml`; normal list behavior and empty-list absence are covered by host-local tests, not shared specs.
- Related contract-level functions: partial. `sum`, `reduce`, `keep_some`, `collect`, map-item helpers, map key/value helpers, and Flow/value boundary cases have some shared coverage. `last`, `nth`, `find_opt`, `range`, and direct empty/edge cases are not covered as a focused stdlib shared contract inventory.
- Normal behavior: partial for `map`; not sufficiently covered for `filter` and `first`.
- Edge cases: partial in host-local tests, limited in shared specs.
- Errors/misuse cases: partial shared coverage exists for Flow/value boundary misuse (`first` on Flow, `reduce` on Flow, `each` on list, `count` as Flow stage).
- Flow interactions: partial shared coverage exists for Flow `map(parse_int) |> keep_some`, CLI pipe-mode map usage, and value-vs-Flow boundary errors. Direct Flow `filter` shared coverage was not found.

## 6. Gap Analysis

Classification: RECOVERY NEEDED

Gaps:

- Area: issue status
  - Missing behavior: issue #151 is not closed; it is open/reopened.
  - Why it matters: the user's premise that #151 was closed completed is no longer true in GitHub.
  - Handling: keep #151 open or use it as the recovery issue.

- Area: issue #151 phase trail
  - Missing behavior: the existing phase trail is a no-delta process trail, not executable stdlib shared specs.
  - Why it matters: it can make #151 look completed without delivering the issue body's stated purpose.
  - Handling: recovery under #151 is appropriate.

- Area: `spec/eval/`
  - Missing behavior: focused shared eval specs for normal list `map`, list `filter`, `first([..])`, `first([])`, and likely `last`/`nth`.
  - Why it matters: host-local tests do not define portable shared contract for future hosts.
  - Handling: recovery under #151.

- Area: `spec/flow/`
  - Missing behavior: direct shared Flow `filter` behavior and direct Flow `map` behavior beyond `parse_int`/`keep_some`.
  - Why it matters: `map`/`filter` are dual value/Flow helpers; shared specs should pin both observable surfaces.
  - Handling: recovery under #151 or a scoped subtask if #151 is split.

- Area: runner guard tests
  - Missing behavior: discovery/execution assertions for direct stdlib contract spec names, because those files do not yet exist.
  - Why it matters: future deletion or omission would not be caught by runner tests.
  - Handling: later TEST phase for #151 recovery.

- Area: docs sync
  - Missing behavior: `GENIA_RULES.md` has stale active-category wording that conflicts with `GENIA_STATE.md`.
  - Why it matters: source-of-truth hierarchy resolves the conflict, but contributors may read stale rules.
  - Handling: docs follow-up; can be part of docs sync if #151 recovery touches shared-spec docs, or a separate doc-sync issue if kept narrow.

## 7. Contract vs Implementation

Portable shared spec contract:

- Lives under `spec/*`.
- Observable surfaces are category-scoped and normalized by the shared spec runner.
- Covered stdlib behavior should be asserted through shared YAML specs and runner tests, not inferred from Python internals.

Python reference host behavior:

- Implemented in `src/genia/`, `tests/`, and `src/genia/std/prelude/`.
- Host-local tests demonstrate current behavior for `map`, `filter`, `first`, `last`, `nth`, and Flow helpers.
- Python is currently the only implemented host, but Python behavior alone is not enough to define new portable coverage unless recorded in shared specs and aligned with `GENIA_STATE.md`.

Internal implementation details:

- Prelude wrappers, runtime helper internals, autoload mechanics, and host Flow kernel details must not define language behavior by themselves.
- Host-local tests and implementation comments can support confidence but do not replace shared spec contract files.

## 8. Test Strategy For Recovery, If Needed

Later TEST phase should add failing tests before implementation/docs work. It should cover:

- Shared spec discovery includes direct stdlib contract case names.
- Eval shared specs for list `map` normal behavior and empty-list behavior.
- Eval shared specs for list `filter` normal behavior and empty-list/no-match behavior.
- Eval shared specs for `first([value, ...]) -> some(value)` rendering and `first([]) -> none("empty-list")`.
- Related eval specs for `last`, `nth`, and perhaps `range`/`find_opt` if the recovery scope keeps "related contract-level functions."
- Flow shared specs for direct `map` and direct `filter` over `stdin |> lines`.
- Error/misuse shared specs only where behavior is already defined in `GENIA_STATE.md`/`GENIA_RULES.md`.
- Runner blackbox assertions that name the new shared specs explicitly.

Do not write those tests in this preflight phase.

## 9. Doc Sync Risk

Docs claim:

- Shared specs exist for active categories: yes, aligned across `GENIA_STATE.md`, `README.md`, and `spec/README.md`.
- Stdlib helpers exist: yes, documented in `GENIA_REPL_README.md`, `README.md`, and `GENIA_RULES.md`.
- Focused stdlib contract shared spec coverage exists: no explicit doc claim found that direct `map`/`filter`/`first` shared specs already exist.

Drift flagged:

- `GENIA_RULES.md` says only `eval`, `ir`, and `cli` are active and others are scaffold-only in one section. This conflicts with final authority `GENIA_STATE.md`.
- `README.md` current shared flow status omits `flow-keep-some-parse-int`, `flow-tee-zip-list-pairs`, `flow-zip-list-pairs`, and `count-as-pipe-stage-type-error` in one later summary even though earlier sections and `GENIA_STATE.md` include broader first-wave Flow coverage. This is lower risk but should be checked during docs sync.

## 10. Relationship To Current Work

- #116 is the parent issue and remains open. It tracks broader shared spec expansion, including stdlib contract tests.
- #140 was not inspected as part of this preflight because #151/#116 were the required GitHub sources and no local reference clearly tied #140 to this stdlib slice.
- #162 Stdlib Phase 1 Normalization is relevant. Current main includes #162 work and value-vs-Flow boundary shared specs such as `first-on-flow-type-error`, `reduce-on-flow-type-error`, and `count-as-pipe-stage-type-error`. That work overlaps with stdlib contract recovery but does not replace direct normal-behavior shared specs for `map`, `filter`, and `first`.

Recommendation:

- #151 should remain open.
- Recovery should continue under #151 unless maintainers prefer splitting direct stdlib shared specs into a narrower child issue.

## 11. Final Go / No-Go

Decision: RECOVERY NEEDED

Blockers:

- Issue #151 is open/reopened, not closed completed.
- Current main contains a no-delta #151 process trail, not the requested executable stdlib shared spec work.
- Direct shared specs for `filter` and normal `first` behavior were not found.
- Direct shared specs for normal list `map` behavior are partial and indirect.

Recommended next prompt:

- "Spec phase for issue #151 recovery: define executable shared spec inventory for stdlib contract coverage without introducing new semantics."

Recommended branch name:

- `issue-151-stdlib-contract-shared-specs-spec`

Recommended commit message for this preflight phase:

- `preflight(stdlib): verify issue #151 shared specs completion`

Steps:

- Preflight
- Spec
- Design
- Test
- Implementation
- Docs
- Audit

