
# Genia Core Cheatsheet

Dense reference of currently implemented features.
If anything here disagrees with GENIA_STATE.md, GENIA_STATE.md wins.

Validation: runnable snippets include `[case: <id>]` markers and are executed by pytest.

## Language Forms

| Category | Forms | Notes |
| --- | --- | --- |
| literals | `1`, `"x"`, `true`, `false`, `nil`, `none`, `[a, b]`, `{k: v}` | `nil` normalizes to `none("nil")` |
| function | `f(x) = expr` | named functions are first-class |
| lambda | `(x) -> expr`, `(..xs) -> expr` | varargs lambda supported |
| assignment | `name = expr` | lexical define/rebind |
| annotations | `@doc "..."`, `@meta {...}`, `@since "..."`, `@deprecated "..."`, `@category "..."` | top-level function/assignment metadata |
| block | `{ expr1 expr2 ... }` | returns final expression |
| pipeline | `x |> f |> g` | explicit pipeline IR stage list |
| quote | `quote(expr)`, `quasiquote(expr)` | programs-as-data helpers exist |
| delay | `delay(expr)` + `force(promise)` | stream prelude uses this |
| import | `import mod`, `import mod as alias` | module value + slash access |

## Pattern Matching

| Pattern | Example |
| --- | --- |
| wildcard | `_` |
| binding | `x` |
| literal | `0`, `"ok"`, `true` |
| tuple | `(x, y)` |
| list + rest | `[x, ..rest]` |
| map (partial) | `{name}`, `{name: n}` |
| option constructor | `some(x)`, `none`, `none(reason)`, `none(reason, ctx)` |
| guard | `(x) ? x > 0 -> ...` |

## Pipeline Rules

| Rule | Meaning |
| --- | --- |
| `x |> f` | `f(x)` |
| `x |> f(y)` | `f(y, x)` |
| callable rhs | `record |> "name"` behaves like `"name"(record)` |
| none short-circuit | `none(...)` skips remaining stages |
| some lifting | ordinary stages lift over `some(x)` automatically |
| lifted result | non-Option `y` becomes `some(y)`; Option results are preserved |
| explicit option stages | helpers such as `unwrap_or`, `map_some`, `flat_map_some`, and `then_*` still receive Option values directly |

Use explicit Option helpers when you need exact wrap-vs-flat-map control.

## Option And Absence

| Constructor / Helper | Shape |
| --- | --- |
| constructors | `some(value)`, `none`, `none(reason)`, `none(reason, context)` |
| predicates | `some?(x)`, `none?(x)`, `is_some?(x)`, `is_none?(x)` |
| map access | `get(key, target)`, `get?(key, target)` |
| option chaining | `map_some(f, opt)`, `flat_map_some(f, opt)` |
| chain helpers | `then_get(key, target)`, `then_first(target)`, `then_nth(index, target)`, `then_find(needle, target)` |
| recovery | `unwrap_or(default, opt)`, `or_else(opt, fallback)`, `or_else_with(opt, thunk)` |
| metadata | `absence_reason(opt)`, `absence_context(opt)`, `absence_meta(opt)` |

## List And Sequence Helpers

| Group | Helpers |
| --- | --- |
| construction / shape | `list()`, `empty?(xs)`, `nil?(x)`, `append(xs, ys)` |
| basic | `first(xs)`, `first_opt(xs)`, `last(xs)`, `rest(xs)` |
| indexed / slicing | `nth(index, xs)`, `nth_opt(index, xs)`, `take(n, xs)`, `drop(n, xs)`, `head(flow_or_list)` |
| transforms | `map(f, xs)`, `filter(pred, xs)`, `reduce(f, acc, xs)`, `reverse(xs)` |
| queries | `count(xs)`, `length(xs)`, `any?(pred, xs)`, `find_opt(pred, xs)` |
| ranges | `range(stop)`, `range(start, stop)`, `range(start, stop, step)` |
| aggregate note | `sum(xs)` expects plain numbers; filter or recover Option values first |

`nth` is `nth(index, xs)`.

## String Helpers

| Helper | Shape |
| --- | --- |
| checks | `is_empty(s)`, `contains(s, needle)`, `starts_with(s, prefix)`, `ends_with(s, suffix)` |
| transforms | `concat(a, b)`, `lower(s)`, `upper(s)`, `trim(s)`, `trim_start(s)`, `trim_end(s)` |
| split / join | `split(s, sep)`, `split_whitespace(s)`, `join(sep, xs)` |
| option-returning | `find(s, needle)`, `parse_int(text)`, `parse_int(text, base)` |

## Flow (Runtime Value Family)

| Helper | Shape |
| --- | --- |
| source bridge | `lines(source)` |
| experimental source bridge | `tick()`, `tick(count)` |
| split / fan-in | `tee(flow)`, `merge(flow1, flow2)`, `zip(flow1, flow2)` |
| option keep-only | `keep_some(flow)`, `keep_some(stage, flow)` |
| option routing | `keep_some_else(stage, dead_handler)`, `keep_some_else(stage, dead_handler, flow)` |
| rule stage | `rules(..fns)` |
| effects / sinks | `each(fn, flow)`, `collect(flow)`, `run(flow)` |

Flow values are lazy and single-use.
`head` / `take` stop upstream pulling promptly.
`collect` and `run` are explicit Value/Flow bridge boundaries.

## Modules And Interop

| Feature | Notes |
| --- | --- |
| module import | `import mod`, `import mod as alias` |
| slash access | `mod/name`, `map/name` |
| host allowlist | `python`, `python.json` |
| host examples | `python/len`, `python/str`, `python/json/loads`, `python/json/dumps` |

## Documentation And Metadata

| Helper | Shape |
| --- | --- |
| doc lookup | `doc("name")` |
| metadata lookup | `meta("name")` |
| note | last annotation wins for duplicate metadata keys |

### `@doc` Quick Reference

Keep `@doc` short and source-readable.
See `docs/style/doc-style.md` for the canonical style guide.

[case: core-min-annotation-doc]
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

## Output And Terminal Helpers

| Helper | Shape |
| --- | --- |
| sink output | `write(sink, value)`, `writeln(sink, value)`, `flush(sink)` |
| terminal control | `clear_screen()`, `move_cursor(x, y)` |
| grid rendering | `render_grid(grid)` |

## Web Helpers

Use `import web` and call helpers through module exports.

| Helper | Shape |
| --- | --- |
| host bridge | `web/serve_http(config, handler)` |
| routes | `web/get(path, handler)`, `web/post(path, handler)`, `web/route_request(routes)` |
| response maps | `web/response(status, headers, body)` |
| response helpers | `web/json(body)`, `web/text(body)`, `web/ok(body)`, `web/ok_text(text)`, `web/bad_request(message)`, `web/not_found()` |

Current request maps use `method`, `path`, `query`, `headers`, `body`, `raw_body`, and `client`.
Current response maps use `status`, `headers`, and `body`.

## CLI Entry Modes

| Mode | Command | Behavior |
| --- | --- | --- |
| file | `genia path/to/file.genia` | run source file |
| command | `genia -c 'source'` | run inline source |
| pipe | `genia -p 'stage_expr'` | wraps as `stdin |> lines |> <expr> |> run` |
| repl | `genia` | interactive REPL |

Dispatch and mode notes:

- file/command mode dispatch: `main(argv())` first, then `main()` fallback
- pipe mode bypasses `main`
- when no `-c`/`-p` mode is selected, the first non-mode argument must be a source file path (`--` stops option parsing for dash-prefixed literals)

## Minimal Valid Snippets

[case: core-min-unwrap-or]
```genia
unwrap_or("unknown", {user: {name: "Genia"}} |> get("user") |> get("name"))
```

[case: core-min-fields-nth-parse]
```genia
fields("a b c d 5 x") |> nth(5) |> flat_map_some(parse_int) |> unwrap_or(0)
```

[case: core-min-keep-some]
```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect
```

[case: core-min-keep-some-else]
```genia
["10", "oops", "20"] |> lines |> keep_some_else(parse_int, log) |> collect
```

[case: core-min-sum-after-keep-some]
```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect |> sum
```

[case: core-min-flow-tee-zip]
```genia
["a", "b"] |> lines |> tee |> zip |> collect
```

[case: core-min-flow-tick]
```genia
tick(4) |> scan((state, _) -> [state + 1, state + 1], 0) |> collect
```
