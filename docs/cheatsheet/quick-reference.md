# Genia Quick Reference

Implemented features only.

Validation: runnable snippets include `[case: <id>]` markers and are executed by pytest.

## Evaluation Model

- expression-oriented
- immutable by default
- pattern matching is primary branching
- pipeline operator: `|>`
- explicit absence values: `some(...)`, `none(...)`
- Flow values are lazy, pull-based, single-use

## Core Syntax

[case: quick-core-syntax]
```genia
inc(x) = x + 1
(x) -> x + 1
x = 10
```

Pattern examples:

```genia
sum([]) = 0
sum([x, ..rest]) = x + sum(rest)
head([x, .._]) = x
```

## Option / Absence

[case: quick-option-constructors]
```genia
some(42)
none
none("missing-key")
none("missing-key", {key: "name"})
```

Pipeline rule reminder:

- `none(...)` short-circuits
- `some(...)` is preserved (not auto-unwrapped)

Common helpers:

- `get(key, target)` / `get?(key, target)`
- `map_some(f, opt)`
- `flat_map_some(f, opt)`
- `then_get`, `then_first`, `then_nth`, `then_find`
- `unwrap_or(default, opt)`

## Lists

- `first(xs)`, `last(xs)`, `rest(xs)`
- `map(f, xs)`, `filter(pred, xs)`, `reduce(f, acc, xs)`
- `count(xs)`, `length(xs)`
- `nth(index, xs)` / `nth_opt(index, xs)`

Correct `nth` shape:

[case: quick-lists-nth]
```genia
nth(2, [10, 20, 30])
```

## Maps

```genia
m = {a: 1, b: 2}
get("a", m)
m/"a"        # invalid (rhs must be bare identifier)
m/a           # slash named access
```

Callable map projection:

[case: quick-maps-callable-projection]
```genia
{a: 1} |> "a"
```

## Flow

Core helpers:

- `lines(source)`
- `keep_some(flow)`
- `keep_some(stage, flow)`
- `keep_some_else(stage, dead_handler, flow)`
- `rules(..fns)`
- `each(fn, flow)`
- `collect(flow)`
- `run(flow)`

Examples:

[case: quick-flow-keep-some]
```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect
```

[case: quick-flow-keep-some-else]
```genia
["10", "oops", "20"] |> lines |> keep_some_else(parse_int, log) |> collect
```

## CLI

```bash
genia -c '1 + 2'
cat file.txt | genia -p 'head(5) |> each(print)'
```

## Operators

- arithmetic: `+ - * / %`
- compare: `== != < <= > >=`
- boolean: `&& || !`
- pipeline: `|>`

## Code-as-Data

[case: quick-code-as-data]
```genia
quote(x + 1)
quasiquote([1, unquote(x)])
```

## Common Gotchas

- `none` in arithmetic propagates absence
- `stdin |> lines` alone has no effect until consumed
- `nth` requires two arguments

Use:

[case: quick-gotcha-consume-stdin]
```genia
stdin |> lines |> each(print) |> run
```
