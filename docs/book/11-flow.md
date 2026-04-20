# Chapter 11: Flow (Phase 1)

Genia now supports a minimal lazy Flow runtime model for stream-style pipelines.

Flow is a runtime value family.
It composes through the same explicit pipeline form as ordinary value pipelines, but Flow values still come only from explicit Flow helpers.

This chapter is about runtime Flow values for pipelines and IO.
It is not the same thing as stdlib streams built from Pair + `delay` / `force`.

The canonical public Flow helper surface now lives in `src/genia/std/prelude/flow.genia`:

- `lines`
- `tick` (experimental)
- `tee`
- `merge`
- `zip`
- `scan`
- `keep_some`
- `keep_some_else`
- `rules`
- `each`
- `collect`
- `run`

The host runtime keeps the minimal Flow kernel in this phase:

- lazy pull-based single-use flow mechanics
- source-bound stdin/runtime integration
- sink/materialization boundaries

The public prelude layer carries the user-facing helper surface, and `rules(..fns)` orchestration/defaulting/validation now primarily live there.

## Flow model

A Flow is:

- lazy
- pull-based
- source-bound
- single-use (consumable)

`|>` lowers to an explicit pipeline node in Core IR.
Flow behavior starts when those stages produce or consume Flow values at runtime.
Option-aware pipeline semantics still apply to ordinary values, but they do not create implicit Value↔Flow conversion and they do not change the single-use Flow kernel contract.

## Flow rules

- Flows are lazy, pull-based, source-bound, and single-use.
- Value/Flow crossing stays explicit:
  - `lines` creates a Flow
  - `tick` creates a tick Flow for discrete step progression (experimental)
  - `collect` materializes to a value
  - `run` consumes for effects
- `take` and `head` are short-circuiting consumers:
  - they stop upstream pulling as soon as the limit is satisfied
  - generator-backed upstream work is closed promptly when downstream stops early
- `run` consumes a Flow to completion unless downstream output terminates early through a quiet broken pipe
- pipe mode is only a wrapper for the middle Flow stages:
  - `genia -p 'stage_expr'` means `stdin |> lines |> <stage_expr> |> run`
  - omit explicit `stdin`
  - omit explicit `run`

## Flow vs Value: the one rule

> Raw values stay values.  Flows stay flows.  Only explicit bridges cross the boundary.

Option behavior (`some` / `none`) composes with this rule but does not erase it.

## Pipeline + Option invariants (canonical)

These are the exact invariants enforced by the pipeline evaluator.
They apply in all modes (file, `-c`, `-p`).

### Raw values stay raw

A non-Option value entering a pipeline stays non-Option through all stages:

- `5 |> add1 |> double` returns `12` (a raw number, never wrapped in `some`)
- `[1,2,3] |> map(f) |> sum` returns a raw number
- No implicit Option promotion occurs

### `some(x)` auto-lifts through ordinary stages

When the pipeline carries `some(x)` and the next stage is not explicitly Option-aware:

1. The stage receives `x` (unwrapped)
2. If the stage returns a non-Option value `y`, the pipeline wraps it back as `some(y)`
3. If the stage returns `some(...)` or `none(...)`, that result is preserved as-is

Example: `some(5) |> add1 |> double` returns `some(12)`.

### `none(...)` short-circuits absolutely

When the pipeline carries `none(...)`, all remaining stages are skipped — including Option-aware stages:

- `none("stop") |> add1 |> unwrap_or(0)` returns `none("stop")` (not `0`)
- Recovery must wrap the whole pipeline: `unwrap_or(0, expr |> stages)`

### `none(...)` metadata is preserved exactly

Short-circuited `none(reason, context)` values pass through unchanged:

- Reason string is preserved
- Context map is preserved (no fields dropped)
- The returned value is the same `none(...)`, not a new one

### Final result preserves Option structure

The pipeline does not strip or add Option wrappers at the boundary:

- `5 |> add1` returns `6` (raw)
- `some(5) |> add1` returns `some(6)` (Option preserved)
- `none("x") |> add1` returns `none("x")` (Option preserved)

### Flow vs Value is orthogonal to Option

Option propagation works the same in both value and flow worlds:

- Value world: `some(x) |> f` auto-lifts; `none(...) |> f` short-circuits
- Flow world: per-item Options use `keep_some` / `keep_some_else`; pipeline-level short-circuit applies to the pipeline value itself

### Helper classification

Every pipeline-visible function fits one of these categories:

| Category | Direction | Examples |
| --- | --- | --- |
| Value function | list → value | `reduce`, `sum`, `count`, `first`, `last`, `nth` |
| Flow function | flow → flow | `keep_some`, `keep_some_else`, `scan`, `rules`, `each`, `tee`, `merge`, `zip`, `head` |
| Polymorphic | list → list or flow → flow | `map`, `filter` |
| Bridge: source | value → flow | `lines`, `tick` |
| Bridge: materialize | flow → value | `collect` |
| Bridge: consume | flow → effect | `run` |

There are exactly three bridge shapes and nothing else crosses the boundary:

- `lines(source)` / `tick()` / `tick(count)` — **create** a flow
- `collect(flow)` — **materialize** a flow into a list
- `run(flow)` — **consume** a flow for side effects

### Minimal value-only pipeline

```genia
[3, 1, 4, 1, 5] |> filter((x) -> x > 2) |> map((x) -> x * 10) |> sum
```

Expected result: `120`

No flow is created. `filter` and `map` work on the list directly. `sum` reduces the list.

### Minimal flow-only pipeline

```genia
["hello", "world"] |> lines |> map(upper) |> each(print) |> run
```

Expected output:

```
HELLO
WORLD
```

`lines` creates a flow. `map(upper)` transforms each item lazily. `each(print)` adds side effects. `run` consumes the flow.

### Explicit bridge pipeline

```genia
["3", "bad", "7"] |> lines |> keep_some(parse_int) |> collect |> sum
```

Expected result: `10`

`lines` bridges value → flow. `keep_some(parse_int)` filters in the flow world. `collect` bridges flow → value. `sum` reduces the resulting list.

### Option + Flow composition

```genia
["10", "oops", "20"] |> lines |> map(parse_int) |> keep_some |> collect |> sum
```

Expected result: `30`

`parse_int` returns `some(int)` or `none(...)`. `keep_some` unwraps `some(v)` items and drops `none(...)` items. This happens in the flow world. `collect` and `sum` happen in the value world.

## Real-time input (`stdin_keys`)

**LANGUAGE CONTRACT:**
- `stdin_keys` is not part of the shared portability contract

**PYTHON REFERENCE HOST:**
- `stdin_keys` is a Python-host-only host-backed Flow source for key-by-key input

- `stdin` remains line-oriented through `stdin |> lines`
- `stdin_keys` is key-oriented and does not require pressing Enter in interactive terminals
- `stdin_keys` is still a single-use Flow source
- runtime behavior is cross-platform:
  - Windows uses console key reads
  - POSIX terminals use raw mode and restore terminal settings on completion/early stop
  - non-interactive stdin falls back to character-by-character reads

### Minimal example

```genia
stdin_keys |> each(handle_input) |> run
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- `handle_input` is called once per key event

### Edge case example

```genia
stdin_keys |> head(3) |> collect
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- returns exactly the first three key events
- stops upstream key reads early

### Failure case example

```genia
x = stdin_keys
x |> collect
x |> collect
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- second consume raises `RuntimeError: Flow has already been consumed`

## Experimental tick-based execution

Genia now includes an experimental tick source helper for discrete-time flow execution.

- `tick()` emits `0, 1, 2, ...` (unbounded)
- `tick(count)` emits `0..count-1` (bounded)

This is intended for deterministic step-driven scenarios such as:

- simulation loops
- game update loops
- automation polling/control loops

The helper is intentionally minimal in this phase:

- no scheduler is introduced
- no new syntax is introduced
- no implicit conversion between Value and Flow is introduced
- the reproducible ants demos use explicit `rng(seed)` state threading inside a pure `step(world) -> world2` model; the terminal UI uses blocking CLI-controlled frame stepping (`--steps`, `--delay`) rather than `tick` or `stdin_keys`, and it does not add a simulation framework

### Minimal example

```genia
tick(5) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[0, 1, 2, 3, 4]
```
Classification: **Likely valid** (not directly tested)


### Edge case example

```genia
tick() |> head(4) |> scan((state, _) -> [state + 1, state + 1], 0) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[1, 2, 3, 4]
```
Classification: **Likely valid** (not directly tested)


### Failure case example

```genia
tick("bad") |> collect
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- runtime `TypeError` explaining that `tick` expected an integer count

## Multi-flow helpers

Genia now includes small explicit fan-out/fan-in helpers for Flow values:

- `tee(flow) -> (flow1, flow2)`
- `merge(flow1, flow2) -> flow`
- `zip(flow1, flow2) -> flow`

These helpers preserve the same lazy pull-based flow model and do not materialize full lists.

### Minimal example

```genia
["a", "b", "c"] |> lines |> tee |> merge |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
["a", "b", "c", "a", "b", "c"]
```

### Edge case example

```genia
["a", "b", "c"] |> lines |> tee |> zip |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[["a", "a"], ["b", "b"], ["c", "c"]]
```

### Failure case example

```genia
tee(["a", "b"])
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- runtime `TypeError` explaining that `tee` expects a flow value

## `scan`

`scan(step, initial_state)` applies a stateful step function over a flow.

For each input item, `step(state, item)` must return a two-item list:

- `[next_state, output]`

`next_state` is carried forward internally to the next item.
Only `output` is emitted on the output flow.

### Minimal example

```genia
[1, 2, 3, 4] |> lines |> scan((state, x) -> [state + x, state + x], 0) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[1, 3, 6, 10]
```

### Edge case example

```genia
window2(state, x) = {
  next = [..state, x]
  trimmed =
    (next) ? count(next) > 2 -> drop(count(next) - 2, next) |
    (next) -> next
  [trimmed, trimmed]
}

[1, 2, 3, 4] |> lines |> scan(window2, []) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[[1], [1, 2], [2, 3], [3, 4]]
```

### Failure case example

```genia
[1] |> lines |> scan((state, x) -> state + x, 0) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- runtime `TypeError` explaining that `scan` expected `[next_state, output]`

## Reusable stages

Any function of shape `(flow) -> flow` can be reused as a stage.

## Pipeline debugging identity helpers

The function prelude now includes three helpers for observing pipelines without changing values:

- `inspect(value)` logs `value` and returns it unchanged
- `trace(label, value)` logs `label` and `value`, then returns `value` unchanged
- `tap(fn, value)` runs `fn(value)` for side effects and returns `value` unchanged

These helpers do not force Flow materialization by themselves.
When they receive a Flow value, they log/forward the Flow handle and preserve lazy single-use behavior.

### Minimal example

```genia
stdin |> lines |> map(parse_int) |> keep_some |> collect |> trace("after parse") |> sum
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- logs `after parse [..numbers..]`
- returns the same sum as the pipeline without `trace`

### Minimal example

```genia
clean(flow) =
  flow |> lines |> map(trim) |> filter((x) -> x != "")

stdin |> clean |> each(print) |> run
```
Classification: **Likely valid** (not directly tested)


### Edge case example

```genia
stdin |> lines |> take(0) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[]
```

This must not pull any upstream items.

### Failure case example

```genia
x = stdin |> lines
x |> run
x |> run
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- second consume raises `RuntimeError: Flow has already been consumed`
- invalid flow-source misuse raises a clear Genia-facing runtime error instead of leaking a raw Python iterator error

## `rules(..fns)`

`rules(..fns)` is a runtime/library Flow stage.

It does not add syntax.
Flow stages still move Flow values explicitly; Option-aware `|>` semantics do not create implicit Value↔Flow bridges.

Each rule runs as `(record, ctx) -> none(...) | some(result)`.
The running `ctx` starts as `{}` and persists across input items.
Plain `none` is the no-effect result.
In this phase, the lazy Flow kernel stays host-backed while the rule orchestration/defaulting/validation path is primarily implemented in `src/genia/std/prelude/flow.genia`.

### Minimal example

```genia
keep_a_names(record, ctx) =
  (record, ctx) ? starts_with(record, "a") == true -> rule_emit(upper(record)) |
  (_, _) -> rule_skip()

["ada", "grace", "alan"] |> lines |> rules(keep_a_names) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
["ADA", "ALAN"]
```

### Edge case example

```genia
running_total(record, ctx) = {
  total = unwrap_or(0, get("sum", ctx))
  value = unwrap_or(0, record |> parse_int)
  next = total + value
  rule_step(record, map_put(ctx, "sum", next), [next])
}

["1", "2", "3"] |> lines |> rules(running_total) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[1, 3, 6]
```

This shows that `ctx` carries forward across items and that one input item may emit one output item without changing pipeline syntax.

### Failure case example

```genia
bad(record, ctx) = some({ emit: record })

["1"] |> lines |> rules(bad) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- runtime error prefixed with `invalid-rules-result:`
- message explains that `emit` must be a list

### ✅ Implemented

- `rules(..fns)` as an ordinary Flow stage
- zero-rule identity behavior
- `emit`, `record`, `ctx`, and `halt` result fields
- persistent `ctx` across input items
- rule helper constructors:
  - `rule_skip`
  - `rule_emit`
  - `rule_emit_many`
  - `rule_set`
  - `rule_ctx`
  - `rule_halt`
  - `rule_step`
- contract validation with `invalid-rules-result:` runtime errors

### ⚠️ Partial

- the initial running `ctx` is fixed to `{}` in this phase
- rule contract validation is structural only:
  - `emit` must be a list
  - `halt` must be a boolean
  - `record` and `ctx` remain user-shaped values

### ❌ Not implemented

- a built-in stage-construction-time helper for seeding `ctx`
- async or multi-source rule scheduling

## `take` / `head`

- `take(n, flow)` returns at most `n` items
- `head(flow)` is the prelude alias `take(1, flow)`
- `head(n, flow)` is the prelude alias `take(n, flow)`

These stop upstream pulling as soon as the limit is reached.
Generator-backed upstream work is also closed promptly when the limit is satisfied.

## `keep_some_else`

`keep_some_else(stage, dead_handler)` is an explicit Flow-stage helper for Option-returning per-item transforms.

It keeps successful values on the main flow and routes rejected original inputs to a dead-letter handler.

### Minimal example

```genia
bad = ref([])

remember_dead(x) = ref_update(bad, (xs) -> append(xs, [x]))

["10", "oops", "20"] |> lines |> keep_some_else(parse_int, remember_dead) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[10, 20]
```

And `ref_get(bad)` becomes:

```genia
["oops"]
```

### Edge case example

```genia
stage(x) =
  ("a") -> none |
  ("b") -> none("missing-key") |
  ("c") -> none("missing-key", { key: "name" }) |
  ("4") -> some(40)

["a", "b", "c", "4"] |> lines |> keep_some_else(stage, log) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- main output is `[40]`
- `"a"`, `"b"`, and `"c"` are sent to `log`
- all supported `none(...)` shapes count as dead-letter results

### Failure case example

```genia
bad(x) = x + 1

[1, 2, 3] |> lines |> keep_some_else(bad, log) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- runtime error explaining that `keep_some_else` expected `some(...)` or `none(...)`

### Notes

- this helper is explicit local routing, not a change to `|>`
- `some(...)` is unwrapped only inside this helper
- `dead_handler` is a handler call, not a second live output flow in this phase

## `keep_some`

`keep_some` is the no-dead-letter convenience form built on top of `keep_some_else`.

Use it when you want to keep successful Option values and silently drop `none(...)` items.

### Minimal example

```genia
["10", "oops", "20"] |> lines |> map(parse_int) |> keep_some |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[10, 20]
```

### Edge case example

```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
[10, 20]
```

This is equivalent to using `keep_some_else(parse_int, (_) -> nil)` for the same flow.

`keep_some(parse_int)` still calls `parse_int` with the original raw row.
Only the helper itself unwraps `some(...)` on success.

### Failure case example

```genia
["a", "b"] |> lines |> keep_some |> collect
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- runtime error explaining that `keep_some` expected Option items (`some(...)` or `none(...)`)

## `collect |> sum`

`collect` is the explicit bridge from Flow to an ordinary list.

`sum` stays explicit too:

- it expects a plain list of numbers
- it does not accept Option values as numeric items
- it does not silently skip `none(...)`

### Minimal example

```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect |> sum
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
30
```

### Edge case example

```genia
["10", "oops", "20"] |> lines |> map((row) -> unwrap_or(0, row |> parse_int)) |> collect |> sum
```
Classification: **Likely valid** (not directly tested)


Expected result:

```genia
30
```

### Failure case example

```genia
["10", "oops", "20"] |> lines |> map(parse_int) |> collect |> sum
```
Classification: **Likely valid** (not directly tested)


Expected behavior:

- runtime error explaining that `sum` expected plain numbers
- message points toward `keep_some(...)`, `keep_some_else(...)`, `flat_map_some(...)`, or `unwrap_or(...)`

## `stdin` vs `input()`

- `stdin` is stream input for flows
- `stdin |> lines` binds lazily and reads incrementally
- `stdin()` materializes the full remaining input into a cached list
- `input()` remains interactive prompt input
- `each(print)` writes flow output to `stdout`
- quiet downstream `stdout` broken-pipe termination is treated as normal completion in command/file execution
- that quiet broken-pipe path also stops generator-backed flow work promptly instead of continuing to pull upstream input

## CLI pipe mode

Pipe mode is an explicit CLI wrapper for common Unix-style flow usage.

It does not change `|>` semantics.

It only builds this runtime-level wrapper:

```genia
stdin |> lines |> <stage_expr> |> run
```

### Minimal example

```bash
printf 'a\nb\n' | genia -p 'head(1) |> each(print)'
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- prints only `a`

Recommended mental model:

- write the middle of the flow only
- pipe mode provides `stdin |> lines` automatically
- pipe mode runs the final flow automatically
- unbound `stdin` and unbound `run` are reserved in pipe mode and rejected with clear errors
- lambda/local bindings named `stdin` or `run` are allowed
- pipe-mode stages still receive the current Flow; use `map(...)`, `filter(...)`, `each(...)`, `keep_some(...)`, or `keep_some_else(...)` when you want per-item work
- value reducers such as `sum` and `count` belong in `-c` / file mode after an explicit `collect`
- if you need the inner value of `some(...)` inside a stage, use explicit helpers such as `flat_map_some(...)`, `map_some(...)`, or `then_*`

### Edge case example

```bash
genia --pipe 'head(1) |> each(print)'
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- exits normally
- prints nothing when stdin is empty
- stops promptly when downstream stages such as `head(1)` have already produced enough output

### Failure case example

```bash
genia -p 'head(1) |> each(print) |> run'
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- exits with a clear error because pipe mode expects a stage expression and adds `run` automatically

```bash
genia -p 'collect'
```

Expected behavior:

- exits with a clear error because the stage expression must still produce a flow for the automatic final `run`
- the error points you toward `-c` when you tried to finish with a value such as `collect |> sum`

## Unix-style scenarios

These examples are small on purpose.
They are meant to feel like real shell work, not toy syntax demos.

### Clean and print non-blank lines

```bash
printf '  alpha  \n\n beta\n' | genia -p 'map(trim) |> filter((line) -> line != "") |> each(print)'
```

Expected output:

```text
alpha
beta
```

### Parse rows with explicit Option handling

```bash
printf '10\noops\n20\n' | genia -p 'map((row) -> unwrap_or("bad", row |> parse_int |> flat_map_some((n) -> some(n + 1)))) |> each(print)'
```

Expected output:

```text
11
bad
21
```

This is the current Option-aware shell style:

- `parse_int` returns `some(int)` or `none("parse-error", ...)`
- ordinary pipeline stages lift over `some(...)` automatically; lifted non-Option results are wrapped back into `some(...)`, and Option stage results are preserved as-is
- a top-level `none(...)` from a stage stops the rest of the pipeline
- use `flat_map_some(...)`, `map_some(...)`, or `then_*` when you need explicit Option-aware control
- use `unwrap_or(...)` inside the stage expression when you want to recover to an ordinary value and keep the flow moving

### Dead-letter routing for bad rows

```bash
printf '10\noops\n20\n' | genia -p 'keep_some_else(parse_int, log) |> map((n) -> n * n) |> each(print)'
```

Expected output:

```text
100
400
```

Expected stderr:

```text
oops
```

### Sum a numeric column from whitespace-separated rows

Use `-c` or a script when you want a final value such as a sum.
Pipe mode is only for middle stage expressions that still produce a flow.

```bash
printf 'a b c d 5 x\n1 2 3 4 6 y\nshort\n' | genia -c 'stdin |> lines |> rules((r, _) -> split_whitespace(r) |> nth(4) |> parse_int |> flat_map_some(rule_emit)) |> collect |> sum'
```

Expected output:

```text
11
```

This example skips malformed rows naturally:

- `split_whitespace(r) |> nth(4)` returns `none(...)` when the field is missing
- `parse_int` is an ordinary stage, so the pipeline lifts it over `some(field)` automatically
- `flat_map_some(rule_emit)` only emits matching numeric values

### Stop early

```bash
printf 'first\nsecond\nthird\n' | genia -p 'head(1) |> each(print)'
```

Expected output:

```text
first
```

This should stop upstream reading as soon as the first line is printed.

## Implementation status

### ✅ Implemented

- lazy single-use flow values
- Flow as a first-class runtime value family (`<flow ...>`)
- `stdin |> lines` source binding
- public Flow helpers exposed through prelude wrappers in `src/genia/std/prelude/flow.genia`
- flow-aware `map`, `filter`, `take`, `scan`, `rules`
- experimental discrete tick source helper: `tick`, `tick(count)`
- `head/1` and `head/2` aliases (stdlib)
- `each`, `collect`, and `run`
- rule helper constructors in the prelude
- host Flow kernel kept minimal while `rules` semantics mostly live in prelude
- early termination on `take`/`head`
- `-p` / `--pipe` CLI wrapping for single stage expressions
- clear runtime errors for invalid flow-source misuse instead of leaked Python iterator errors
- shell pipeline stage `$(command)` (**Python-host-only**; see [Chapter 15](15-reference-host-and-portability.md))

### ⚠️ Partial

- cancellation/backpressure is limited to downstream early-stop via `take`/`head`
- `rules(..fns)` starts with a fixed empty-map `ctx`
- pipe mode is intentionally narrow:
  - it expects a single stage expression
  - explicit `stdin` and explicit `run` are rejected
  - no `pipe(...)` helper exists in this phase

### ❌ Not implemented

- async stream scheduling
- multi-source/multi-port flow stages
- generalized push-based stream runtime
