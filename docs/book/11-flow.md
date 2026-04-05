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
- flow-aware `map`, `filter`, `take`
- `head/1` and `head/2` aliases (stdlib)
- `each`, `collect`, and `run`
- early termination on `take`/`head`
- `-p` / `--pipe` CLI wrapping for single stage expressions

### ⚠️ Partial

- cancellation/backpressure is limited to downstream early-stop via `take`/`head`
- pipe mode is intentionally narrow:
  - it expects a single stage expression
  - explicit `stdin` and explicit `run` are rejected
  - no `pipe(...)` helper exists in this phase

### ❌ Not implemented

- async stream scheduling
- multi-source/multi-port flow stages
- generalized push-based stream runtime
