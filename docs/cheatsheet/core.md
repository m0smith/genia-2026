# Note: Examples in this cheatsheet are validated by the Semantic Spec System where covered. Currently, only the eval category is active for executable shared spec files; other categories are scaffold-only. See GENIA_STATE.md for authoritative status.

# Genia Core Cheatsheet

Dense reference of currently implemented features.
If anything here disagrees with GENIA_STATE.md, GENIA_STATE.md wins.

Validation: runnable snippets include `[case: <id>]` markers and are executed by pytest. Examples are classified as **Valid** if directly tested, **Likely valid** if not directly tested, **Illustrative** if not runnable, or **Invalid** if contradicted by implementation.

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
| lifted result | non-Option `y` becomes `some(y)`; Option results are preserved as-is |
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

## Randomness

Python-host-only runtime helpers in the current reference host; not part of the shared portability contract.

| Helper | Shape |
| --- | --- |
| explicit seeded state | `rng(seed)` |
| convenience float | `rand()` |
| seeded float | `rand(rng_state)` |
| convenience int | `rand_int(n)` |
| seeded int | `rand_int(rng_state, n)` |
| delay | `sleep(ms)` |

Use `rng(seed)` plus the seeded overloads when you need reproducible tests or demos.
Use `rand()` / `rand_int(n)` when host-backed nondeterministic convenience is fine.

## Flow (Runtime Value Family)

| Helper | Shape |
| --- | --- |
| source bridge | `lines(source)` |
| experimental source bridge | `tick()`, `tick(count)` |
| split / fan-in | `tee(flow) -> [left_flow, right_flow]`, `merge(flow1, flow2)`, `merge(pair)`, `zip(flow1, flow2)`, `zip(pair)` |
| option keep-only | `keep_some(flow)`, `keep_some(stage, flow)` |
| option routing | `keep_some_else(stage, dead_handler)`, `keep_some_else(stage, dead_handler, flow)` |
| rule stage | `rules(..fns)` |
| effects / sinks | `each(fn, flow)`, `collect(flow)`, `run(flow)` |

Flow values are lazy and single-use.
`head` / `take` stop upstream pulling promptly.
`collect` and `run` are explicit Value/Flow bridge boundaries.
`map` and `filter` are polymorphic: they work on both lists and flows.

The one rule: raw values stay values, flows stay flows, only explicit bridges cross.
See `docs/cheatsheet/piepline-flow-vs-value.md` for the full classification matrix.

## Shell Stage

**Python-host-only pipeline stage** (not part of portable contract):

| Rule | Meaning |
| --- | --- |
| form | `value |> $(command)` executes `command` via the host shell |
| stdin materialization | strings → UTF-8; lists/flows → newline-joined display; numbers/bools → display |
| stdout | captured as UTF-8 string; one trailing newline is stripped |
| empty stdout | returns `none("empty-shell-output")` |
| limits | only valid inside a pipeline; not part of portable Core IR |

[case: core-shell-stage-upper]
```genia
"hello" |> $(tr a-z A-Z)
```
Classification: **Valid** (directly tested)

## Refs

Python-host-only runtime helpers in the current reference host; not part of the shared portability contract.

| Helper | Shape |
| --- | --- |
| create | `ref()`, `ref(initial)` |
| read / write | `ref_get(r)`, `ref_set(r, value)` |
| atomic update | `ref_update(r, fn)` |
| check | `ref_is_set(r)` |

`ref_get` and `ref_update` **block** until value is set. No timeout.

## Processes

Python-host-only runtime helpers in the current reference host; not part of the shared portability contract.

| Helper | Shape |
| --- | --- |
| create | `spawn(handler)` |
| send | `send(process, message)` |
| inspection | `process_alive?(process)`, `process_failed?(process)`, `process_error(process)` |

FIFO mailbox, one handler call at a time. Handler exceptions enter fail-stop state.

## Cells

Python-host-only runtime helpers in the current reference host; not part of the shared portability contract.

| Helper | Shape |
| --- | --- |
| create | `cell(initial)`, `cell_with_state(ref)` |
| update / read | `cell_send(cell, update_fn)`, `cell_get(cell)`, `cell_state(cell)` |
| lifecycle | `cell_stop(cell)`, `restart_cell(cell, new_state)` |
| inspection | `cell_status(cell)`, `cell_alive?(cell)`, `cell_failed?(cell)`, `cell_error(cell)` |

Cells are serialized mutable state backed by a worker thread.
`cell_send` enqueues an update function `(state) -> new_state`.
`cell_stop` drains queued updates then exits the worker.

## Actors

Python-host-only runtime helpers in the current reference host; not part of the shared portability contract.

| Helper | Shape |
| --- | --- |
| create | `actor(initial_state, handler)` |
| fire-and-forget | `actor_send(actor, msg)` |
| request-reply | `actor_call(actor, msg)` |
| lifecycle | `actor_stop(actor)`, `actor_restart(actor, new_state)` |
| inspection | `actor_state(actor)`, `actor_status(actor)`, `actor_alive?(actor)` |
| health | `actor_failed?(actor)`, `actor_error(actor)` |

Handler shape: `handler(state, msg, ctx) -> ["ok", new_state]`, `["reply", new_state, response]`, or `["stop", reason, new_state]`.
All three shapes work with both `actor_send` and `actor_call`.
`actor_call` with `["ok", new_state]` replies with `new_state`.
`actor_call` with `["reply", new_state, response]` replies with `response`.
`actor_call` with `["stop", ...]` replies with `none("actor-stopped")`.
If the handler throws during `actor_call`, the result is `none("actor-error")`.
Actors are a thin prelude layer over cells, not a BEAM-style actor system.
They are public Python-host behavior in this phase, not a shared cross-host contract surface.

<!-- [case: core-actor-call-reply] -->
```genia
handler(state, msg, _ctx) = ["reply", state + msg, state + msg]
a = actor(0, handler)
actor_call(a, 5)
```
Classification: **Valid** (directly tested)

<!-- [case: core-actor-call-ok] -->
```genia
handler(state, msg, _ctx) = ["ok", state + msg]
a = actor(0, handler)
actor_call(a, 3)
```
Classification: **Valid** (directly tested)

<!-- [case: core-actor-status] -->
```genia
handler(state, _msg, _ctx) = ["ok", state]
a = actor(0, handler)
actor_status(a)
```
Classification: **Valid** (directly tested)

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
| doc lookup | `doc("name")` → string or `none("missing-doc", {name: ...})` |
| metadata lookup | `meta("name")` → map or `none("missing-meta", {name: ...})` |
| note | `@doc` metadata takes priority over legacy inline docstrings; last annotation wins for duplicate metadata keys |

Supported built-in annotations are `@doc`, `@meta`, `@since`, `@deprecated`, and `@category`.

### `@doc` Quick Reference

Keep `@doc` short and source-readable.
See `docs/style/doc-style.md` for the canonical style guide.

[case: core-min-annotation-doc]
```genia
@doc "Adds one to x."
inc(x) -> x + 1
doc("inc")
```
Classification: **Valid** (directly tested)

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

Terminal demos can stay simple and deterministic with ordinary CLI flags plus `sleep`.
The ants terminal UI accepts `--seed`, `--ants`, `--steps`, `--delay`, `--size`, and `--mode pure|actor`; it is blocking and does not use `stdin_keys` for pause/step controls.

## Web Helpers

**LANGUAGE CONTRACT:** `import web` and these HTTP helpers are not part of the shared cross-host contract surface.
**PYTHON REFERENCE HOST:** use `import web` and call helpers through module exports. These helpers are Python reference host behavior (**Python-host-only**) in this phase.

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
| pipe | `genia -p 'stage_expr'` | wraps as `stdin |> lines |> <stage_expr> |> run` |
| repl | `genia` | interactive REPL |

Dispatch and mode notes:

- file/command mode dispatch: `main(argv())` first, then `main()` fallback
- runtime entrypoint order is `main/1` first, then `main/0`
- pipe mode bypasses `main`
- in pipe mode, stage helpers still receive a Flow; use `map(...)`, `filter(...)`, `each(...)`, `keep_some(...)`, or `keep_some_else(...)` for per-item work
- use `-c` or file mode for final value reducers such as `collect |> sum` or `collect |> count`
- when no `-c`/`-p` mode is selected, the first non-mode argument must be a source file path (`--` stops option parsing for dash-prefixed literals)

## Minimal Valid Snippets

[case: core-min-unwrap-or]
```genia
unwrap_or("unknown", {user: {name: "Genia"}} |> get("user") |> get("name"))
```
Classification: **Valid** (directly tested)

[case: core-min-fields-nth-parse]
```genia
fields("a b c d 5 x") |> nth(5) |> parse_int |> unwrap_or(0)
```
Classification: **Valid** (directly tested)

[case: core-min-keep-some]
```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect
```
Classification: **Valid** (directly tested)

[case: core-min-keep-some-else]
```genia
["10", "oops", "20"] |> lines |> keep_some_else(parse_int, log) |> collect
```
Classification: **Valid** (directly tested)

[case: core-min-sum-after-keep-some]
```genia
["10", "oops", "20"] |> lines |> keep_some(parse_int) |> collect |> sum
```
Classification: **Valid** (directly tested)

[case: core-min-flow-tee-zip]
```genia
["a", "b"] |> lines |> tee |> zip |> collect
```
Classification: **Valid** (directly tested)

[case: core-min-flow-tick]
```genia
tick(4) |> scan((state, _) -> [state + 1, state + 1], 0) |> collect
```
Classification: **Valid** (directly tested)

[case: core-min-seeded-rand-int]
```genia
pair_left(pair) = ([x, _]) -> x
pair_right(pair) = ([_, x]) -> x

r0 = rng(7)
s1 = rand_int(r0, 10)
r1 = pair_left(s1)
v1 = pair_right(s1)
s2 = rand_int(r1, 10)
[v1, pair_right(s2)]
```
Classification: **Valid** (directly tested)
