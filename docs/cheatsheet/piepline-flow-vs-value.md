# Genia Pipeline: Flow vs Value

The one rule that makes Genia pipelines predictable:

> **Raw values stay values.  Flows stay flows.  Only explicit bridges cross the boundary.**

Option behavior (`some` / `none`) composes with this rule but does not erase it:
pipelines auto-lift ordinary stages over `some(x)` and short-circuit on `none(...)`,
regardless of whether the pipeline carries values or flows.

Legend: 🟢 Value  🔵 Flow  🟣 Bridge  🔴 Sink

Validation: runnable rows include `[case: <id>]` markers and are executed by pytest.

---

## Teaching model

```text
Value world                          Flow world
─────────────                        ──────────
[1, 2, 3]                            stdin |> lines        ← source bridge
  |> map(f)        polymorphic         |> map(f)
  |> filter(p)     polymorphic         |> filter(p)
  |> sum           value-only          |> collect  ← bridge to value
                                       |> sum      (now value world)
                                       |> each(print) |> run  ← sink
```

Three bridge shapes exist and nothing else crosses the boundary:

| Direction | Bridge | What it does |
| --- | --- | --- |
| Value → Flow | `lines(source)`, `tick()`, `tick(count)` | Create a lazy single-use flow |
| Flow → Value | `collect(flow)` | Materialize flow into a list |
| Flow → Effect | `run(flow)` | Consume flow for side effects only |

---

## Explicit function classification

### 🟢 Value functions (list in, value out)

| Helper | Call shape | Notes |
| --- | --- | --- |
| `map` | `map(f, xs)` | Also works as flow stage; polymorphic |
| `filter` | `filter(pred, xs)` | Also works as flow stage; polymorphic |
| `reduce` | `reduce(f, acc, xs)` | Value-only reducer |
| `sum` | `sum(xs)` | Expects plain numbers |
| `count` | `count(xs)` | List length |
| `first` | `first(xs)` | Returns `some(x)` or `none(...)` |
| `last` | `last(xs)` | Returns `some(x)` or `none(...)` |
| `nth` | `nth(index, xs)` | Returns `some(x)` or `none(...)` |
| `take` | `take(n, xs)` | First n items as list |
| `drop` | `drop(n, xs)` | Skip first n items |
| `reverse` | `reverse(xs)` | Reversed list |

### 🔵 Flow functions (flow in, flow out)

| Helper | Call shape | Notes |
| --- | --- | --- |
| `map` | `flow \|> map(f)` | Polymorphic with list version above |
| `filter` | `flow \|> filter(pred)` | Polymorphic with list version above |
| `head` | `head(n, flow)` / `flow \|> head(n)` | Limits flow; stops upstream promptly |
| `keep_some` | `keep_some(flow)` or `keep_some(stage, flow)` | Unwraps `some(v)`, drops `none(...)` |
| `keep_some_else` | `keep_some_else(stage, handler, flow)` | Routes `some(v)` forward; `none(...)` to handler |
| `scan` | `scan(step, init, flow)` | Stateful `step(state, item) -> [next_state, output]` |
| `rules` | `rules(..fns)` | Stateful flow orchestration |
| `each` | `each(fn, flow)` | Side effects; passes items through |
| `tee` | `tee(flow)` | Splits one flow into two |
| `merge` | `merge(f1, f2)` | Concatenates two flows |
| `zip` | `zip(f1, f2)` | Pairs items from two flows |

### 🟣 Bridge functions (cross the boundary)

| Helper | Direction | Notes |
| --- | --- | --- |
| `lines` | Value → Flow | Accepts stdin, list-of-strings, or existing flow |
| `tick` | (source) → Flow | `tick()` unbounded, `tick(count)` bounded |
| `collect` | Flow → Value | Materializes lazy flow into a list |
| `run` | Flow → Effect | Consumes flow; returns `nil` |

### Debug helpers (mode-transparent)

| Helper | Behavior |
| --- | --- |
| `inspect(value)` | Logs value, returns unchanged |
| `trace(label, value)` | Logs label + value, returns unchanged |
| `tap(fn, value)` | Runs `fn(value)` for side effects, returns unchanged |

---

## Transforms

| Goal | Value | Flow | [case] |
| --- | --- | --- | --- |
| Transform each item | 🟢 `map(f, xs)` | 🔵 `flow \|> map(f)` | [case: pfv-transform-map] |
| Chain transforms | 🟢 `xs \|> map(f) \|> map(g)` | 🔵 `flow \|> map(f) \|> map(g)` | [case: pfv-transform-chain] |
| Rule-driven transform | — | 🔵 `flow \|> rules(..fns)` | [case: pfv-transform-rules] |

## Filters / selection

| Goal | Value | Flow | [case] |
| --- | --- | --- | --- |
| Keep matching items | 🟢 `filter(pred, xs)` | 🔵 `flow \|> filter(pred)` | [case: pfv-filter-predicate] |
| Keep successful Options | manual list filtering | 🔵 `flow \|> keep_some` | [case: pfv-filter-keep-some] |
| Apply + keep successful | `map(stage, xs)` then filter | 🔵 `flow \|> keep_some(stage)` | [case: pfv-filter-keep-some-stage] |
| Route failed Options | manual split logic | 🔵 `flow \|> keep_some_else(stage, handler)` | [case: pfv-filter-keep-some-else] |

## Reducers / aggregation

| Goal | Value | Flow | [case] |
| --- | --- | --- | --- |
| Reduce | 🟢 `reduce(f, acc, xs)` | 🟣 `flow \|> collect \|> reduce(f, acc)` | [case: pfv-reduce] |
| Sum | 🟢 `sum(xs)` | 🟣 `flow \|> collect \|> sum` | [case: pfv-sum] |
| Count | 🟢 `count(xs)` | 🟣 `flow \|> collect \|> count` | [case: pfv-count] |

## Positional access

| Goal | Value | Flow | [case] |
| --- | --- | --- | --- |
| First item | 🟢 `first(xs)` | 🟣 `flow \|> head(1) \|> collect \|> first` | [case: pfv-first] |
| Last item | 🟢 `last(xs)` | 🟣 `flow \|> collect \|> last` | [case: pfv-last] |
| Nth item | 🟢 `nth(index, xs)` | 🟣 `flow \|> collect \|> nth(index)` | [case: pfv-nth] |
| Take first n | 🟢 `take(n, xs)` | 🟣 `flow \|> head(n) \|> collect` | [case: pfv-take-head] |

## Option handling in both worlds

| Goal | Value | Flow | [case] |
| --- | --- | --- | --- |
| Map inside Option | 🟢 `map_some(f, opt)` | 🔵 `flow \|> map(stage) \|> keep_some` | [case: pfv-option-map-some] |
| Flat-map Option | 🟢 `flat_map_some(f, opt)` | 🔵 `flow \|> keep_some(stage)` | [case: pfv-option-flat-map-some] |
| Provide fallback | 🟢 `unwrap_or(default, opt)` | 🔵 `flow \|> map((x) -> unwrap_or(default, x \|> stage))` | [case: pfv-option-unwrap-or] |
| `none` short-circuits pipeline | 🟢 `none(...) \|> f` returns `none(...)` unchanged | 🔵 use `keep_some` / `keep_some_else` on flow items | [case: pfv-option-none-short-circuit] |
| Option + Flow interaction | 🟢 `some(x) \|> f` auto-unwraps x for f | 🔵 flow items are plain values; use `map(parse_int) \|> keep_some` for stream-level Option routing | [case: pfv-option-flow-interaction] |

## Side effects / sinks

| Goal | Value | Flow | [case] |
| --- | --- | --- | --- |
| Side effect per item | 🟢 `map(fn, xs)` | 🔴 `flow \|> each(fn) \|> run` | [case: pfv-sink-each-run] |
| Print items | 🟢 `xs \|> map(print)` | 🔴 `flow \|> each(print) \|> run` | [case: pfv-sink-print] |
| Materialize | already value | 🟣 `flow \|> collect` | [case: pfv-bridge-collect] |

## Bridges

| Goal | Shape | [case] |
| --- | --- | --- |
| Start flow from stdin | 🟣 `stdin \|> lines` | [case: pfv-bridge-stdin-lines] |
| Start flow from list | 🟣 `xs \|> lines` | [case: pfv-bridge-list-lines] |
| Stream through to effects | 🔴 `... \|> map/filter/... \|> each(...) \|> run` | [case: pfv-bridge-run] |
| Cross to value world | 🟣 `flow \|> collect` | [case: pfv-bridge-collect-2] |

## Common pipeline shapes

| Pattern | Value | Flow | [case] |
| --- | --- | --- | --- |
| Parse and aggregate | 🟢 `rows \|> map(parse_int) \|> map((o) -> unwrap_or(0, o)) \|> sum` | 🟣 `rows \|> lines \|> keep_some(parse_int) \|> collect \|> sum` | [case: pfv-shape-parse-aggregate] [case: pfv-shape-parse-aggregate-value] |
| Column extraction + sum | 🟢 value-only with nested pipeline | 🟣 `stdin \|> lines \|> rules((r, _) -> split_whitespace(r) \|> nth(4) \|> parse_int \|> flat_map_some(rule_emit)) \|> collect \|> sum` | [case: pfv-shape-column-sum] |
| Stream to output | 🟢 `xs \|> map(f) \|> map(print)` | 🔴 `stdin \|> lines \|> map(f) \|> each(print) \|> run` | [case: pfv-shape-stream-output] |

## CLI mode selection

| Goal | Mode | Why |
| --- | --- | --- |
| Stream stdin through flow stages | `-p 'stage_expr'` | `-p` injects `stdin \|> lines` and final `run` |
| Produce a final collected value | `-c 'source'` or file mode | You control full program shape and materialization |
| File program with `main(argv())` | file mode | Supports trailing args and runtime dispatch |

Pipe mode wraps as `stdin |> lines |> <stage_expr> |> run`.
Do not include explicit `stdin` or `run` in `-p`.
For reducers like `sum` or `count`, use `-c`.

## Value-only pipeline example

<!-- [case: pfv-value-only-pipeline] -->
```genia
[3, 1, 4, 1, 5] |> filter((x) -> x > 2) |> map((x) -> x * 10) |> sum
```

## Flow-only pipeline example

<!-- [case: pfv-flow-only-pipeline] -->
```genia
["hello", "world"] |> lines |> map(upper) |> each(print) |> run
```

## Explicit bridge example

<!-- [case: pfv-explicit-bridge] -->
```genia
["3", "bad", "7"] |> lines |> keep_some(parse_int) |> collect |> sum
```

## Option + Flow interaction example

<!-- [case: pfv-option-flow-example] -->
```genia
["10", "oops", "20"] |> lines |> map(parse_int) |> keep_some |> collect |> sum
```

---

## Rules of thumb

1. **Start from the input.** Stdin or IO? Use `lines` to enter Flow world. Already a list? Stay in Value world.
2. **Stay in one world.** Chain flow stages or chain value stages. Don't mix without an explicit bridge.
3. **Cross explicitly.** `collect` is the only Flow → Value bridge. `lines` is the primary Value → Flow bridge.
4. **Option composes orthogonally.** Pipeline `some`/`none` lifting works the same in both worlds.
5. **Use `keep_some` for stream-level Option filtering.** It is flow-oriented. For single Options, use `map_some`, `flat_map_some`, or `unwrap_or`.
6. **Reducers need values.** `sum`, `count`, `reduce` expect lists, not flows. Use `collect` first.
7. **Direct calls don't lift.** Automatic `some(x)` unwrapping is pipeline-only. Direct `f(some(x))` short-circuits.

## Gotchas

- `nth` is `nth(index, xs)` in normal calls; `xs |> nth(index)` in pipeline style.
- `each(fn)` does not execute until the flow is consumed with `run` or `collect`.
- Flows are single-use; reusing a consumed flow raises a runtime error.
- `keep_some` is flow-oriented, not a list helper.
- Pipe mode already wraps as `stdin |> lines |> <stage_expr> |> run`; do not include explicit `stdin` or `run`.
- `map` and `filter` are polymorphic: they work on both lists and flows, staying in whichever world they receive.
