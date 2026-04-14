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

- `none(...)` short-circuits and preserves reason/context metadata
- ordinary stages lift over `some(x)` automatically
- lifted non-Option results are wrapped back into `some(...)`; Option stage results are preserved as-is
- direct calls still receive explicit `some(...)` values unchanged
- explicitly Option-aware helpers (`unwrap_or`, `map_some`, `flat_map_some`, `then_*`) still receive Option values directly

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

Aggregation reminder:

- `sum(xs)` expects plain numbers, not raw Option values
- use `keep_some(...)`, `keep_some_else(...)`, or per-item `unwrap_or(...)` before `collect |> sum`
- Flow values are single-use, and `head` / `take` stop upstream pulling promptly
- `collect` and `run` are the explicit bridge points out of Flow

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

- file/`-c` mode dispatch: call `main(argv())` when `main/1` exists, else call `main()` when `main/0` exists
- pipe mode bypasses `main` and wraps as `stdin |> lines |> <stage_expr> |> run`
- in `-p`, use Flow stages such as `map(...)`, `filter(...)`, `each(...)`, `keep_some(...)`, or `keep_some_else(...)` for per-item work
- use `-c` or file mode for final collected values such as `sum` or `count`
- when no `-c`/`-p` mode is selected, the first non-mode argument must be a source file path (`--` stops option parsing for dash-prefixed literals)

[case: quick-cli-main-argv]
```genia
main(args) = args
main(argv())
```

## Actors

- `actor(initial_state, handler)` — create a message-passing actor
- `actor_send(actor, msg)` — fire-and-forget
- `actor_call(actor, msg)` — synchronous request-reply
- `actor_stop(actor)`, `actor_restart(actor, new_state)` — lifecycle
- `actor_state`, `actor_status`, `actor_alive?`, `actor_failed?`, `actor_error` — inspection

Handler returns `["ok", new_state]` or `["reply", new_state, response]`.

[case: quick-actor-call]
```genia
handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
a = actor(0, handler)
actor_call(a, 5)
```

## Web

- `import web` exposes the phase-1 HTTP helper surface
- `web/serve_http(config, handler)` starts the current blocking phase-1 HTTP server bridge
- `web/get(path, handler)` and `web/post(path, handler)` create exact-path routes
- `web/route_request(routes)` builds a handler from those routes
- `web/response(status, headers, body)` builds a response map directly
- `web/json(body)`, `web/text(body)`, `web/ok(body)`, `web/ok_text(text)`, `web/bad_request(message)`, and `web/not_found()` build response maps
- request maps currently include `method`, `path`, `query`, `headers`, `body`, `raw_body`, and `client`
- response maps currently include `status`, `headers`, and `body`

## `@doc` Quick Reference

Use `@doc` for short binding contracts, not long essays.
Canonical formatting rules live in `docs/style/doc-style.md`.

[case: quick-doc-single-line]
```genia
@doc "Adds one to x."
inc(x) -> x + 1
doc("inc")
```

```genia
@doc """
Returns first item.

## Returns
- some(value) when `xs` is non-empty
- none("empty-list") when `xs` is empty
"""
first_or_none(xs) =
  [] -> none("empty-list") |
  [x, .._] -> some(x)
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
