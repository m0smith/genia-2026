# Chapter 11: Flow (Phase 1)

Genia now supports a minimal lazy Flow runtime model for stream-style pipelines.

Flow is a runtime value family, not a parser feature and not a special meaning of `|>` by itself.

This chapter is about runtime Flow values for pipelines and IO.
It is not the same thing as stdlib streams built from Pair + `delay` / `force`.

## Flow model

A Flow is:

- lazy
- pull-based
- source-bound
- single-use (consumable)

The pipeline operator is unchanged: `|>` still rewrites to ordinary calls in the AST→Core IR pass. Flow behavior starts at runtime when those calls produce or consume Flow values.

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

## `rules(..fns)`

`rules(..fns)` is a runtime/library Flow stage.

It does not add syntax, and it does not change the meaning of `|>`.

Each rule runs as `(record, ctx) -> none(...) | some(result)`.
The running `ctx` starts as `{}` and persists across input items.
Plain `none` is the no-effect result.

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
  value = parse_int(record)
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

## Implementation status

### ✅ Implemented

- lazy single-use flow values
- Flow as a first-class runtime value family (`<flow ...>`)
- `stdin |> lines` source binding
- flow-aware `map`, `filter`, `take`, `rules`
- `head/1` and `head/2` aliases (stdlib)
- `each`, `collect`, and `run`
- rule helper constructors in the prelude
- early termination on `take`/`head`
- `-p` / `--pipe` CLI wrapping for single stage expressions

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
