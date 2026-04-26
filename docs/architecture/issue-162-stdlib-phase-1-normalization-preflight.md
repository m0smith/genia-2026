# Issue #162 Preflight - Stdlib Phase 1 Normalization

=== GENIA PRE-FLIGHT ===

CHANGE NAME:
Stdlib Phase 1 Normalization

## 0. BRANCH

Starting branch:
`main`

Working branch:
`issue-162-stdlib-phase-1-normalization`

Branch status:
newly created for this preflight phase.

## 1. SCOPE LOCK

Change includes:

- inventorying public/prelude functions used in common pipelines
- identifying value functions vs Flow functions vs option-aware helpers
- identifying public tuple leakage or host-shaped values
- identifying pair-like return shapes
- identifying docs/tests/spec files affected
- coordinating with issue #140

Change does NOT include:

- implementation
- failing tests
- docs sync
- tuple destructuring
- making tuples public Genia values
- new syntax
- value templates/type features
- broad Flow redesign
- repo-wide rename

## 2. SOURCE OF TRUTH

Authoritative files read:

- `AGENTS.md`
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- GitHub issue #162
- GitHub issue #140

Relevant current behavior:

- Prelude/std functions: public helpers are autoloaded from `src/genia/std/prelude/*.genia`, with thin Genia wrappers over host primitives where needed. `GENIA_STATE.md` lists public families for list, fn, cli, map, ref, process, io, randomness, flow, option, string, syntax, and metacircular evaluator helpers.
- Collections: list helpers include `list`, `first`, `last`, `rest`, `append`, `length`, `reverse`, `reduce`, `map`, `filter`, `count`, `find_opt`, `any?`, `nth`, `take`, `head`, `drop`, and `range`. `map` and `filter` are polymorphic across lists and flows; reducers such as `sum`, `count`, and `reduce` are value-side list operations.
- Maps: map helpers are `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`, `map_items`, `map_item_key`, `map_item_value`, `map_keys`, and `map_values`. `GENIA_STATE.md` says `map_items` returns `[key, value]` pairs in insertion order, and `map_item_key` / `map_item_value` expect that shape.
- Pairs: `cons`, `car`, `cdr`, `pair?`, and `null?` exist as immutable pair primitives. Quoted list-like forms and stdlib streams use pairs ending in `nil`. Ordinary list literals remain separate list values. Current docs do not make Python tuples a public Genia value type.
- Options: `none`, `none(reason)`, `none(reason, context)`, and `some(value)` are implemented. Canonical maybe helpers include `get`, `first`, `last`, `nth`, string `find`, `find_opt`, `parse_int`, `map_get`, callable map/string lookup, slash map access, and `cli_option`. Pipeline `some(x)` lifts through ordinary stages and `none(...)` short-circuits; explicit helpers include `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`, `unwrap_or`, `or_else`, `or_else_with`, `absence_reason`, `absence_context`, and `absence_meta`.
- Flows/pipelines: raw values stay values; flows stay flows; only explicit bridges cross the boundary. Value-to-Flow bridges include `lines` and `tick`; Flow-to-value/effect bridges are `collect` and `run`. Flow functions include `keep_some`, `keep_some_else`, `scan`, `rules`/`refine`, `each`, `tee`, `merge`, `zip`, and `head`; `map` and `filter` are polymorphic. `zip` emits `[left, right]` pairs. `scan` step functions must return `[next_state, output]`.
- Normalized errors: shared specs compare normalized `stdout`, `stderr`, and `exit_code` for eval, cli, flow, and error categories. Error coverage is initial and exact at the observable surface; Flow misuse and pipe-mode guidance already have documented clear diagnostics.

## 3. CURRENT STATE

Relevant prelude files:

- `src/genia/std/prelude/list.genia`
- `src/genia/std/prelude/map.genia`
- `src/genia/std/prelude/option.genia`
- `src/genia/std/prelude/flow.genia`
- `src/genia/std/prelude/string.genia`
- `src/genia/std/prelude/fn.genia`
- `src/genia/std/prelude/cli.genia`
- `src/genia/std/prelude/file.genia`
- `src/genia/std/prelude/stream.genia`

Public functions likely affected:

- Value/list helpers: `map`, `filter`, `reduce`, `sum`, `count`, `first`, `last`, `nth`, `take`, `head`, `drop`, `reverse`, `find_opt`, `range`.
- Map helpers: `map_items`, `map_item_key`, `map_item_value`, `map_keys`, `map_values`, plus `map_get` for Option shape.
- Pair-like shape helpers: `zip`, `tee`, `merge(pair)`, `scan`, `map_items`, `map_item_key`, `map_item_value`, and any public helper that consumes or returns 2-slot structures.
- Option helpers: `some`, `none?`, `some?`, `get`, `get?`, `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`, `unwrap_or`, `or_else`, `or_else_with`, `absence_reason`, `absence_context`, `absence_meta`.
- Flow helpers: `lines`, `tick`, `tee`, `merge`, `zip`, `scan`, `keep_some`, `keep_some_else`, `rules`, `refine`, `each`, `collect`, `run`.
- Common pipeline helpers: `parse_int`, `split_whitespace`, `fields`, `inspect`, `trace`, `tap`, and CLI pipe-mode guidance around `map(parse_int)` / `keep_some(parse_int)`.

Existing tests/specs touching this area:

- Specs: `spec/eval/map-items.yaml`, `spec/eval/map-keys.yaml`, `spec/eval/map-values.yaml`, `spec/eval/pipeline-call-shape-basic.yaml`, `spec/eval/pipeline-map-sum.yaml`, `spec/eval/pipeline-option-some-lift.yaml`, `spec/eval/pipeline-option-none-short-circuit.yaml`, `spec/flow/*.yaml`, and pipe-mode cases under `spec/cli/`.
- Tests: `tests/test_maps.py`, `tests/test_pairs.py`, `tests/test_option.py`, `tests/test_option_semantics.py`, `tests/test_flow_phase1.py`, `tests/test_flow_unix_scenarios.py`, `tests/test_cli_pipe_mode.py`, `tests/test_cli_stdlib.py`, `tests/test_stdlib_prelude_basics.py`, `tests/test_stream_prelude.py`, `tests/test_fn_stdlib.py`, `tests/test_json_stdlib.py`, and cheatsheet validation tests.
- Case data: `tests/cases/option/*`, `tests/cases/flow/*`, `tests/data/pipeline_flow_vs_value_cases.json`, `tests/data/cheatsheet_core_cases.json`, `tests/data/cheatsheet_quick_reference_cases.json`, `tests/data/cheatsheet_unix_to_genia_cases.json`, and `tests/data/cheatsheet_unix_power_mode_cases.json`.

Docs that currently describe this behavior:

- `GENIA_STATE.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/cheatsheet/piepline-flow-vs-value.md`
- `docs/cheatsheet/core.md`
- `docs/cheatsheet/quick-reference.md`
- `docs/cheatsheet/unix-power-mode.md`
- `docs/cheatsheet/unix-to-genia.md`
- `docs/host-interop/*`
- `docs/contract/semantic_facts.json` and `tests/test_semantic_doc_sync.py` if protected wording changes

Issue #140 overlap:

- #140 is the narrower pair-like shape issue. It targets public tuple leakage and standardizes visible pair-like values as `[key, value]` / `[a, b]` lists.
- #162 is broader: it includes #140's shape concern but also inventories and clarifies the stdlib surface, value-vs-Flow behavior, and option-aware helper consistency.

## 4. FEATURE MATURITY

Classification:
Partial.

Notes:

- The runtime and prelude are implemented in the Python reference host, but the shared semantic-spec surface remains partial by category.
- Flow shared coverage is active but first-wave only; broader helper behavior is not fully covered by shared specs.
- Docs later must describe this as normalization of the current implemented stdlib surface, not as a new stable multi-host stdlib guarantee.
- Host-only helpers must remain labeled as Python reference host behavior where applicable.

## 5. CONTRACT vs IMPLEMENTATION

Portable language contract:

- Public structured values should be Genia-pattern-matchable when visible.
- Public pair-like values should use ordinary 2-element lists, not Python tuples.
- Option pipeline behavior stays explicit: `some(x)` lifts through ordinary pipeline stages, `none(...)` short-circuits, and recovery happens through explicit helpers.
- Flow/value crossing remains explicit through documented bridges such as `lines`, `collect`, and `run`.
- Core IR remains the portability boundary; host-local optimized/runtime structures are not public contract.

Python reference host implementation details:

- Public prelude functions are loaded from `src/genia/std/prelude/*.genia`.
- Host-backed primitives in `src/genia/interpreter.py` implement map, option, flow, string, file/zip, and other helper kernels.
- `GeniaMap.items()` currently returns list-shaped `[key, value]` entries even though its Python type annotation says `list[tuple[Any, Any]]`.
- `tee` currently returns a Python tuple of two `GeniaFlow` values internally; `merge(pair)` and `zip(pair)` accept tuple or list pairs.
- Python host boundary conversion maps Python list/tuple to Genia list recursively.

Internal-only host/runtime details that must not leak publicly:

- Python tuples used for dispatch args, parser/IR internals, map key freezing, debug bookkeeping, host bridge internals, and `tee` internals.
- AST/IR tuple-shaped implementation fields.
- Host opaque handles, process/ref/cell/actor internals, Python exceptions beyond documented normalized user-facing errors.

## 6. TEST STRATEGY

Later TEST phase should cover:

- Shape consistency for public structured values from `map_items`, `zip`, `scan`, `tee`-derived `zip`/`merge`, and common helper compositions.
- No public tuple leakage in eval output, runtime values returned by public APIs, and public helper docs/examples.
- Pair-like values as 2-element lists where applicable, especially `map_items(m) -> [[key, value], ...]` and `zip(flow1, flow2) -> [[left, right], ...]`.
- `map_item_key` / `map_item_value` against valid list pairs and clear behavior for invalid shapes.
- Value vs Flow misuse: bare per-item helpers receiving whole Flow, reducers receiving Flow, Flow helpers receiving lists after `collect`, and `keep_some` receiving raw non-Option flow items.
- Option behavior: `some(...)` pipeline lifting remains unchanged; `none(...)` short-circuits; `keep_some` and `keep_some_else` unwrap/drop/route only at their explicit Flow helper boundary.
- Regression tests for common pipelines: `stdin |> lines |> map(split_whitespace) |> map((r) -> nth(4, r)) |> keep_some`, parse/filter/sum with `parse_int`, `map_items |> map(map_item_key)`, and `tee |> zip |> collect`.

Do not write these tests in preflight.

## 7. CROSS-FILE IMPACT

Likely spec impact:

- `spec/eval/map-items.yaml`
- `spec/eval/map-keys.yaml`
- `spec/eval/map-values.yaml`
- `spec/eval/pipeline-*`
- `spec/flow/*.yaml`
- `spec/cli/pipe_mode_*.yaml`
- possibly new `spec/eval` or `spec/flow` cases for shape normalization

Likely tests impact:

- `tests/test_maps.py`
- `tests/test_pairs.py`
- `tests/test_flow_phase1.py`
- `tests/test_option_semantics.py`
- `tests/test_cli_pipe_mode.py`
- `tests/test_flow_unix_scenarios.py`
- `tests/test_stdlib_prelude_basics.py`
- cheatsheet validation tests and data under `tests/data/`

Likely source/prelude/runtime impact:

- `src/genia/interpreter.py`
- `src/genia/std/prelude/map.genia`
- `src/genia/std/prelude/flow.genia`
- `src/genia/std/prelude/list.genia`
- `src/genia/std/prelude/option.genia`
- `src/genia/std/prelude/fn.genia`
- possibly `src/genia/utf8.py` if display normalization is affected

Likely docs impact:

- `GENIA_STATE.md`
- `GENIA_RULES.md` if invariants need clarification
- `GENIA_REPL_README.md`
- `README.md`
- `docs/cheatsheet/piepline-flow-vs-value.md`
- `docs/cheatsheet/core.md`
- `docs/cheatsheet/quick-reference.md`
- `docs/cheatsheet/unix-power-mode.md`
- `docs/cheatsheet/unix-to-genia.md`
- `docs/host-interop/*` if host boundary tuple/list wording changes

Semantic doc sync impact:

- `docs/contract/semantic_facts.json` only if protected cross-doc facts need new or changed wording.
- `tests/test_semantic_doc_sync.py` only if semantic facts are added or existing protected wording changes.

## 8. DEPENDENCIES / OVERLAP

Relationship to issue #140:

- #140 directly owns the pair-like public value conversion and tuple leakage concern.
- #162 should not duplicate #140's implementation if #140 remains open.
- #162 should use #140 as a dependency or sibling for the narrow pair-shape changes, then focus on broader stdlib contract classification and consistency.

Recommendation:

- Split #162 into subtasks.
- Do #140 first or as the first subtask of #162 if maintainers decide to close #140 through this work.
- After #140's shape contract is settled, continue #162 with value-vs-Flow and option-helper normalization.

## 9. COMPLEXITY CHECK

Is this adding complexity or revealing structure?

- Revealing structure. The intended direction is to make the existing public surface smaller, clearer, and more pattern-matchable.

Is the issue too large for one development cycle?

- Yes, if treated as implementation for all stdlib families at once.

Should it be split into subtasks?

- Yes.

Smallest useful subtasks:

1. Public pair-like shape contract: map items, zip outputs, tee-derived pair consumers, scan return validation wording, and no tuple leakage checks. Coordinate or merge with #140.
2. Value-vs-Flow classification: public inventory and targeted misuse diagnostics/spec cases for common pipelines.
3. Option-aware helper consistency: direct Option helpers vs Flow Option-routing helpers; preserve current pipeline lifting/short-circuit semantics.
4. Docs/spec sync: update only implemented and tested behavior, including semantic doc facts only if needed.

## 10. RISK OF DRIFT

Drift risks:

- Docs claiming a broader stable stdlib contract than the current Python reference host and shared specs prove.
- Accidentally making Python tuple behavior public while fixing tuple leakage.
- Conflating Flow functions, value functions, polymorphic helpers, and bridge helpers.
- Changing semantics while "cleaning up" helper names or implementation shape.
- Broad rename risk, especially around `rules`/`refine`, `rule_*`/`step_*`, `get?`, and compatibility aliases.
- Host-only behavior losing required `PYTHON REFERENCE HOST` / Python-host-only labeling.
- Updating examples without matching executable tests or shared specs.

## 11. PHILOSOPHY CHECK

- preserves minimalism? YES. The desired result is fewer surprising public shapes.
- avoids hidden behavior? YES, if Flow/value and Option behavior are explicit rather than context-magic.
- keeps semantics out of host adapters? YES, if behavior is defined in `GENIA_STATE.md`/spec first and host code only implements it.
- aligns with pattern-first design? YES. Visible structured values should be pattern-matchable as Genia lists/maps/options.
- respects Core IR as portability boundary? YES, provided tuple cleanup does not alter AST/IR internals or host-local optimized nodes as public contract.

## 12. PROMPT PLAN

Recommended next prompts:

- Spec prompt: define the smallest observable contract for pair-like list shapes, value-vs-Flow classification, and option-aware helper boundaries, with explicit #140 coordination.
- Design prompt: choose exact implementation boundaries and affected helper families without broad rename or Flow redesign.
- Failing-test prompt: add failing tests/spec cases only for the approved spec/design scope.
- Implementation prompt: implement only behavior covered by the failing-test commit and reference that commit SHA.
- Docs prompt: synchronize `GENIA_STATE.md` first, then aligned docs/cheatsheets only for implemented behavior.
- Audit prompt: run shared specs, targeted pytest suites, semantic doc sync, and check for tuple/public-shape drift.

Do not produce those prompts in this phase.

## FINAL GO / NO-GO

GO for proceeding to spec, with split-scope discipline.

Blockers:

- No truth blocker for spec phase.
- Scope blocker if #162 is attempted as one broad implementation pass.
- Coordination decision needed: either make #140 the first dependency/subtask or explicitly close #140 through the pair-like shape subtask of #162.

Recommended branch name:
`issue-162-stdlib-phase-1-normalization`

Recommended commit message:
`preflight(stdlib): assess phase 1 normalization scope for issue #162`
