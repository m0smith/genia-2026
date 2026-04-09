# Chapter 11: Flow (Phase 1)

Genia now supports a minimal lazy Flow runtime model for stream-style pipelines.

Flow is a runtime value family.
It composes through the same explicit pipeline form as ordinary value pipelines, but Flow values still come only from explicit Flow helpers.

This chapter is about runtime Flow values for pipelines and IO.
It is not the same thing as stdlib streams built from Pair + `delay` / `force`.

The canonical public Flow helper surface now lives in `std/prelude/flow.genia`:

- `lines`
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

## Reusable stages

Any function of shape `(flow) -> flow` can be reused as a stage.

### Minimal example

```genia
clean(flow) =
  flow |> lines |> map(trim) |> filter((x) -> x != "")

stdin |> clean |> each(print) |> run
```

### Edge case example

```genia
stdin |> lines |> take(0) |> collect
```

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
In this phase, the lazy Flow kernel stays host-backed while the rule orchestration/defaulting/validation path is primarily implemented in `std/prelude/flow.genia`.

### Minimal example

```genia
keep_a_names(record, ctx) =
  (record, ctx) ? starts_with(record, "a") == true -> rule_emit(upper(record)) |
  (_, _) -> rule_skip()

["ada", "grace", "alan"] |> lines |> rules(keep_a_names) |> collect
```

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

## `keep_some_else`

`keep_some_else(stage, dead_handler)` is an explicit Flow-stage helper for Option-returning per-item transforms.

It keeps successful values on the main flow and routes rejected original inputs to a dead-letter handler.

### Minimal example

```genia
bad = ref([])

remember_dead(x) = ref_update(bad, (xs) -> append(xs, [x]))

["10", "oops", "20"] |> lines |> keep_some_else(parse_int, remember_dead) |> collect
```

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

Expected behavior:

- main output is `[40]`
- `"a"`, `"b"`, and `"c"` are sent to `log`
- all supported `none(...)` shapes count as dead-letter results

### Failure case example

```genia
bad(x) = x + 1

[1, 2, 3] |> lines |> keep_some_else(bad, log) |> collect
```

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

Expected result:

```genia
[10, 20]
```

### Edge case example

```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect
```

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

Expected behavior:

- runtime error explaining that `keep_some` expected Option items (`some(...)` or `none(...)`)

## `collect |> sum`

`collect` is the explicit bridge from Flow to an ordinary list.

`sum` stays explicit too:

- it expects a plain list of numbers
- it does not auto-unwrap `some(...)`
- it does not silently skip `none(...)`

### Minimal example

```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect |> sum
```

Expected result:

```genia
30
```

### Edge case example

```genia
["10", "oops", "20"] |> lines |> map((row) -> unwrap_or(0, row |> parse_int)) |> collect |> sum
```

Expected result:

```genia
30
```

### Failure case example

```genia
["10", "oops", "20"] |> lines |> map(parse_int) |> collect |> sum
```

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

Expected behavior:

- prints only `a`

Recommended mental model:

- write the middle of the flow only
- pipe mode provides `stdin |> lines` automatically
- pipe mode runs the final flow automatically
- if you need the inner value of `some(...)` inside a stage, use explicit helpers such as `flat_map_some(...)`, `map_some(...)`, or `then_*`

### Edge case example

```bash
genia --pipe 'head(1) |> each(print)'
```

Expected behavior:

- exits normally
- prints nothing when stdin is empty

### Failure case example

```bash
genia -p 'head(1) |> each(print) |> run'
```

Expected behavior:

- exits with a clear error because pipe mode expects a stage expression and adds `run` automatically

```bash
genia -p 'collect'
```

Expected behavior:

- exits with a clear error because the stage expression must still produce a flow for the automatic final `run`

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
- pipelines preserve explicit `some(...)`
- a top-level `none(...)` from a stage stops the rest of the pipeline
- use `flat_map_some(...)`, `map_some(...)`, or `then_*` when the next step needs the inner value
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
printf 'a b c d 5 x\n1 2 3 4 6 y\nshort\n' | genia -c 'stdin |> lines |> rules((r, _) -> split_whitespace(r) |> nth(4) |> flat_map_some(parse_int) |> flat_map_some(rule_emit)) |> collect |> sum'
```

Expected output:

```text
11
```

This example skips malformed rows naturally:

- `split_whitespace(r) |> nth(4)` returns `none(...)` when the field is missing
- `flat_map_some(parse_int)` only parses present fields
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
- public Flow helpers exposed through prelude wrappers in `std/prelude/flow.genia`
- flow-aware `map`, `filter`, `take`, `rules`
- `head/1` and `head/2` aliases (stdlib)
- `each`, `collect`, and `run`
- rule helper constructors in the prelude
- host Flow kernel kept minimal while `rules` semantics mostly live in prelude
- early termination on `take`/`head`
- `-p` / `--pipe` CLI wrapping for single stage expressions
- clear runtime errors for invalid flow-source misuse instead of leaked Python iterator errors

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
