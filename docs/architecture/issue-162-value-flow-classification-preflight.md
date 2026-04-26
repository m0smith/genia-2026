# Issue #162 — Value-vs-Flow Classification (Deferred Slice) Preflight

---

## 0. BRANCH

Branch required:
YES

Branch type:
[x] feature
[ ] fix
[ ] refactor
[ ] docs
[ ] exp

Branch slug: issue-162-value-flow-classification

Expected branch: issue-162-value-flow-classification

Base branch:
main

Rules:
- No work begins on `main`
- Branch must be created before Spec
- One branch per change

Status: CONFIRMED — branch `issue-162-value-flow-classification` exists and is current.

---

## 1. SCOPE LOCK

### Change includes:
- Classify every public prelude function as: **value**, **Flow**, **bridge**, or **stage/combinator**
- Add shared spec coverage (`spec/flow/` and `spec/eval/`) for common Flow/value misuse error cases
- Add shared spec coverage for `map`/`filter`/`each` boundary behavior in pipe mode vs value mode
- Unit tests proving misuse produces documented, actionable error messages
- GENIA_STATE.md update: add a canonical classification table

### Change does NOT include:
- Changes to runtime semantics for any prelude function
- New prelude functions or removal of existing ones
- Option-aware helper consistency (separate deferred slice)
- Broader docs truth synchronization beyond the classification table
- Pipe-mode guidance coverage (separate deferred slice)

---

## 2. SOURCE OF TRUTH

Authoritative files read:
- `AGENTS.md`
- `GENIA_STATE.md` (final authority)
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`

Additional relevant files:
- `src/genia/std/prelude/flow.genia`
- `src/genia/std/prelude/list.genia`
- `src/genia/std/prelude/option.genia`
- `src/genia/std/prelude/map.genia`
- `spec/flow/` (existing error specs)
- `tests/test_flow_phase1.py`

If files conflict, `GENIA_STATE.md` wins.

---

## 3. CURRENT PRELUDE SURFACE INVENTORY

### Flow functions (accept and/or return GeniaFlow)

| Function | Input | Output | Notes |
|---|---|---|---|
| `lines(source)` | list / string / Flow | Flow | primary value→Flow bridge |
| `tick()` | — | Flow | ticks forever |
| `tick(count)` | int | Flow | ticks `count` times |
| `tee(flow)` | Flow | `[Flow, Flow]` | returns list pair |
| `merge(flow1, flow2)` | Flow, Flow | Flow | |
| `merge(pair)` | `[Flow, Flow]` | Flow | consumes tee result |
| `zip(flow1, flow2)` | Flow, Flow | Flow of `[a, b]` pairs | |
| `zip(pair)` | `[Flow, Flow]` | Flow of `[a, b]` pairs | consumes tee result |
| `scan(step, initial_state)` | fn, value | stage fn (Flow→Flow) | curried |
| `scan(step, initial_state, flow)` | fn, value, Flow | Flow | uncurried |
| `keep_some(flow)` | Flow | Flow | filters none values |
| `keep_some(stage, flow)` | fn, Flow | Flow | maps then filters |
| `keep_some_else(stage, dead_handler)` | fn, fn | stage fn | curried |
| `keep_some_else(stage, dead_handler, flow)` | fn, fn, Flow | Flow | uncurried |
| `rules(..fns)` | fns | stage fn | pattern dispatch |
| `refine(..steps)` | fns | stage fn | alias for rules |
| `each(f, flow)` | fn, Flow | Flow | side-effecting |
| `collect(flow)` | Flow | list | Flow→value bridge |
| `run(flow)` | Flow | nil | Flow→nil bridge |

### Value functions (operate on plain Genia values only)

**list.genia:**
`list`, `first`, `first_opt`, `last`, `rest`, `empty?`, `nil?`,
`append`, `length`, `reverse`, `reduce`, `map`, `filter`,
`count`, `find_opt`, `any?`, `nth`, `nth_opt`, `take`, `head`

**option.genia:**
`some`, `none?`, `some?`, `get`, `get?`, `map_some`, `flat_map_some`,
`then_get`, `then_first`, `then_nth`, `then_find`, `or_else`, `or_else_with`,
`unwrap_or`, `absence_reason`, `absence_context`, `absence_meta`,
`is_some?`, `is_none?`

**map.genia:**
`map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`,
`map_items`, `map_item_key`, `map_item_value`, `map_keys`, `map_values`

### Ambiguity / misuse risk zones

| Function | Risk | Reason |
|---|---|---|
| `map(f, xs)` | HIGH | value fn; passing a Flow as `xs` in pipe mode should fail with a clear error |
| `filter(predicate, xs)` | HIGH | value fn; same risk as `map` |
| `reduce(f, acc, xs)` | MEDIUM | value fn; no Flow equivalent exists; misuse in pipe mode must error |
| `each(f, flow)` | MEDIUM | Flow fn; passing a list instead of Flow should error |
| `collect(flow)` | LOW | bridge; well-understood |
| `first(xs)` / `last(xs)` | MEDIUM | value fn; must not silently accept Flow |

---

## 4. FEATURE MATURITY

Stage:
[ ] Experimental
[x] Partial
[ ] Stable

### How this must be described in docs:
- Classification table is documentary, not a new language feature.
- Spec additions test existing error behavior, not new behavior.

---

## 5. CONTRACT vs IMPLEMENTATION

### Contract (portable semantics):
- No change to contract for any existing function.
- Adds documentation of the existing contract in GENIA_STATE.md.

### Implementation (Python today):
- No implementation change unless a misuse path produces a crash (Python exception) instead of a Genia-level error. If found, a minimal fix will be scoped into this slice.

### Not implemented:
- No new prelude functions.
- No semantic behavior changes.

---

## 6. TEST STRATEGY

### Core invariants to cover:
1. Passing a Flow where a value list is expected (`map(f, flow)`) produces a runtime error, not a crash
2. Passing a list where a Flow is expected (`each(f, [1,2,3])`) produces a runtime error, not a crash
3. Using a value function as a bare pipe stage (`|> reduce(...)`) produces the pipe-mode error
4. `collect` and `run` are the only documented Flow→value bridges; no other path silently crosses

### Spec files to add:
- `spec/eval/map-on-flow-type-error.yaml` — `map(f, flow)` → error
- `spec/eval/filter-on-flow-type-error.yaml` — `filter(f, flow)` → error
- `spec/flow/each-on-list-type-error.yaml` — `each(f, list)` → error
- `spec/flow/pipe-reduce-stage-error.yaml` — `stdin |> lines |> reduce(...)` → pipe-mode error

### Failure cases:
- Any of the above produces a Python traceback instead of a Genia error message

### Unit tests:
- One parametrized test covering all four misuse cases with `assert exit_code != 0` and `assert error_message in stderr`

---

## 7. EXAMPLES

### Minimal example (value/Flow boundary):
```genia
# WRONG: map is a value function
[1, 2, 3] |> lines |> map(x -> x + 1)   # ERROR: pipe stage received Flow, not list

# RIGHT: use each for side effects on Flow
[1, 2, 3] |> lines |> each(print)

# RIGHT: collect first, then map over values
[1, 2, 3] |> lines |> collect |> map(x -> x + 1)
```

### Real example (what the spec cases will test):
```genia
# Error case — map given a Flow:
f = tick(3)
map(x -> x, f)
# Expected: stderr contains type error, exit_code != 0

# Error case — each given a list:
each(print, [1, 2, 3])
# Expected: stderr contains type error, exit_code != 0
```

---

## 8. COMPLEXITY CHECK

Is this:
[ ] Adding complexity
[x] Revealing structure

### Justification:
- Makes the existing boundary explicit and tested without changing semantics.

---

## 9. CROSS-FILE IMPACT

### Files that must change:
- `docs/architecture/issue-162-value-flow-classification-preflight.md` (this file)

### Files expected to change in later phases:
- `GENIA_STATE.md` — add classification table
- `spec/eval/map-on-flow-type-error.yaml` (new)
- `spec/eval/filter-on-flow-type-error.yaml` (new)
- `spec/flow/each-on-list-type-error.yaml` (new)
- `spec/flow/pipe-reduce-stage-error.yaml` (new)
- `tests/test_spec_ir_runner_blackbox.py` — register 4 new spec names
- Possibly `src/genia/interpreter.py` if any misuse path produces an uncaught Python exception

Risk of drift:
[ ] Low
[x] Medium
[ ] High

Medium because the type-error behavior for `map(f, flow)` and `each(f, list)` needs to be confirmed at research phase — may require a small interpreter guard.

---

## 10. PHILOSOPHY CHECK

Does this:
- preserve minimalism? YES — no new functions added
- avoid hidden behavior? YES — the whole point is to document and test boundary behavior
- keep semantics out of host? YES — no semantic changes
- align with pattern-matching-first? YES — classification table directly informs pattern usage

---

## 11. PROMPT PLAN

Will use full pipeline?
YES

Steps:
1. Preflight (this artifact) ← CURRENT
2. Spec — define YAML spec cases for misuse boundaries
3. Design — confirm whether interpreter guards are needed, document fix plan
4. Test — write failing unit tests before implementation
5. Implementation — add guards if needed; must reference failing-test SHA
6. Docs — update GENIA_STATE.md classification table
7. Audit — verify all phases complete, all specs pass

---

## FINAL GO / NO-GO

Ready to proceed?
YES (for Spec phase only — do not begin Spec until user explicitly prompts)
