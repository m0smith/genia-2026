# Chapter 11: Flow (Phase 1)

Genia now supports a minimal lazy Flow runtime model for stream-style pipelines.

## Flow model

A Flow is:

- lazy
- pull-based
- source-bound
- single-use (consumable)

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
- `head(flow)` is an alias of `take(1, flow)`
- `head(n, flow)` is an alias of `take(n, flow)`

These stop upstream pulling as soon as the limit is reached.

## `stdin` vs `input()`

- `stdin` is stream input for flows
- `input()` remains interactive prompt input

## Implementation status

### ✅ Implemented

- lazy single-use flow values
- `stdin |> lines` source binding
- flow-aware `map`, `filter`, `take`
- `head/1` and `head/2` aliases (stdlib)
- `each`, `collect`, and `run`
- early termination on `take`/`head`

### ⚠️ Partial

- cancellation/backpressure is limited to downstream early-stop via `take`/`head`

### ❌ Not implemented

- async stream scheduling
- multi-source/multi-port flow stages
- generalized push-based stream runtime
