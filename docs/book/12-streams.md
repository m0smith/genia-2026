# Chapter 12: Streams And Delayed Evaluation

Streams in Genia are a stdlib composition of:

- pairs (`cons`, `car`, `cdr`)
- promises (`delay(expr)`, `force(x)`)

They are not Flow values.

## Definition

A stream node is:

```genia
cons(head, delay(tail_expr))
```

The bundled stream prelude exposes this through:

- `stream_cons(head, tail_fn)`
- `stream_head(s)`
- `stream_tail(s)`
- `stream_map(f, s)`
- `stream_take(n, s)`
- `stream_filter(pred, s)`

## Implementation status

### ✅ Implemented

- stream construction in stdlib with pairs plus promises
- infinite recursive streams
- lazy mapped streams
- lazy filtered streams
- `stream_take` materialization to ordinary lists

### ⚠️ Partial

- laziness is explicit only
- stream tails are forced explicitly
- the current prelude is minimal and centered on infinite recursive streams

### ❌ Not implemented

- stream literals
- automatic forcing
- Flow integration
- lazy list literals

## Minimal example

```genia
ones() =
  stream_cons(1, () -> ones())

stream_take(3, ones())
```

Expected result:

```genia
[1, 1, 1]
```

## Edge case example

```genia
from(n) =
  stream_cons(n, () -> from(n + 1))

stream_take(5, stream_filter((x) -> x % 2 == 0, from(1)))
```

Expected result:

```genia
[2, 4, 6, 8, 10]
```

This works because the delayed tail is forced only as far as `stream_take` needs.

## Failure case example

```genia
stream_head(nil)
```

Expected behavior:

- raises `TypeError` because `stream_head` is just `car`, and `car` expects a pair

## `delay` / `force` interaction

`stream_cons` is defined with a zero-argument tail function so the tail expression stays unevaluated until the stream tail is forced.

```genia
stream_cons(head, tail_fn) =
  cons(head, delay(tail_fn()))
```

That means this is the intended shape:

```genia
from(n) =
  stream_cons(n, () -> from(n + 1))
```

and not:

```genia
cons(n, delay(from(n + 1)))
```

because the stdlib helper makes the delayed intent explicit and teachable.

## Streams vs Flow

- streams are pure delayed data
- Flow is the runtime pipeline/IO model
- streams are reusable because promise forcing memoizes
- Flow values are source-bound and single-use
