# Genia Pipeline: Flow vs Value

The one rule that makes Genia pipelines predictable:

> **Raw values stay values.  Flows stay flows.  Only explicit bridges cross the boundary.**

Seq is the semantic abstraction for ordered value production.
List is the eager reusable Seq-compatible value.
Flow is the lazy single-use Seq-compatible value.
Iterator is a host implementation detail.

Option behavior (`some` / `none`) composes with this rule but does not erase it:
pipelines auto-lift ordinary stages over `some(x)` and short-circuit on `none(...)`,
regardless of whether the pipeline carries values or flows.

Legend: 🟢 Value  🔵 Flow  🟣 Bridge  🔴 Sink

Validation: runnable rows include `[case: <id>]` markers and are executed by pytest. Examples are classified as **Valid** if directly tested, **Likely valid** if not directly tested, **Illustrative** if not runnable, or **Invalid** if contradicted by implementation.

---

## Teaching model

```text
Value world                          Flow world
─────────────                        ──────────
[1, 2, 3]                            stdin |> lines        ← source bridge
  |> map(f)        polymorphic         |> map(f)
  |> filter(p)     polymorphic         |> filter(p)
  |> take(n)       polymorphic         |> take(n)
  |> drop(n)       polymorphic         |> drop(n)
  |> sum           value-only          |> collect  ← bridge to value
                                       |> sum      (now value world)
                                       |> each(print) |> run  ← sink
```

Three bridge shapes exist and nothing else crosses the boundary:

| Direction | Bridge | What it does |
| --- | --- | --- |
| Value → Flow | `lines(source)`, `evolve(init, f)` | Create a lazy single-use flow |
| Flow → Value | `collect(flow)` | Materialize flow into a list |
| Flow → Effect | `run(flow)` | Consume flow to completion; `run(list)` also traverses and returns `nil` |

---

## Pipeline invariant contract

These invariants are enforced by the pipeline evaluator and locked by tests under `tests/cases/option/` and `tests/cases/flow/`. Only examples with `[case: <id>]` markers are **Valid**; others are **Likely valid** unless contradicted.

| # | Invariant | Key implication |
|---|-----------|-----------------|
| 1 | **Raw values stay raw.** Non-Option values pass through stages without gaining Option wrappers. | `5 \|> add1 \|> double` → `12`, never `some(12)` |
| 2 | **`some(x)` auto-lifts through ordinary stages.** Non-Option-aware stages receive `x`, return wrapped as `some(y)`. | `some(5) \|> add1` → `some(6)` |
| 3 | **`none(...)` short-circuits absolutely.** All remaining stages are skipped — including Option-aware stages like `unwrap_or`. | `none("x") \|> unwrap_or(0)` → `none("x")` |
| 4 | **`none(...)` metadata is preserved exactly.** Reason and context survive short-circuit unchanged. | `none("timeout", {retry: 3}) \|> f \|> g` keeps both fields |
| 5 | **Final result preserves Option structure.** The pipeline boundary does not strip or add wrappers. | `some(5) \|> add1` → `some(6)`, not `6` |
| 6 | **Flow vs Value is orthogonal to Option.** Option propagation works the same in both worlds. | Use `keep_some` for per-item Option filtering in flows |

Recovery pattern: wrap the pipeline, not a single stage.

```text
✗  value |> stages |> unwrap_or(default)     ← short-circuit skips unwrap_or
✓  unwrap_or(default, value |> stages)       ← recovery is outside the pipeline
```

---

## Explicit function classification

### 🟢 Value functions (list in, value out)

| Helper | Call shape | Notes |
| --- | --- | --- |
| `map` | `map(f, xs)` | Also works as flow stage; polymorphic |
| `filter` | `filter(pred, xs)` | Also works as flow stage; polymorphic |
| `sum` | `sum(xs)` | Expects plain numbers |
| `first` | `first(xs)` | Returns `some(x)` or `none(...)` |
| `last` | `last(xs)` | Returns `some(x)` or `none(...)` |
| `nth` | `nth(index, xs)` | Returns `some(x)` or `none(...)` |
| `take` | `take(n, xs)` | Also works as flow stage; polymorphic |
| `drop` | `drop(n, xs)` | Also works as flow stage; polymorphic |
| `reverse` | `reverse(xs)` | Reversed list |

### 🔵 Flow functions (flow in, flow out)

| Helper | Call shape | Notes |
| --- | --- | --- |
| `map` | `flow \|> map(f)` | Polymorphic with list version above |
| `filter` | `flow \|> filter(pred)` | Polymorphic with list version above |
| `take` | `flow \|> take(n)` | Polymorphic with list version above; limits flow and stops upstream promptly |
| `drop` | `flow \|> drop(n)` | Polymorphic with list version above; skips first n pulled items |
| `head` | `head(n, flow)` / `flow \|> head(n)` | Limits flow; stops upstream promptly |
| `keep_some` | `keep_some(flow)` or `keep_some(stage, flow)` | Unwraps `some(v)`, drops `none(...)` |
| `keep_some_else` | `keep_some_else(stage, handler, flow)` | Routes `some(v)` forward; `none(...)` to handler |
| `scan` | `scan(step, init, flow)` | Stateful `step(state, item) -> [next_state, output]` |
| `rules` | `refine(..steps)` (preferred), `rules(..fns)` (compatibility) | Stateful flow orchestration |
| `tee` | `tee(flow)` | Returns `[left_flow, right_flow]` |
| `merge` | `merge(f1, f2)` / `merge(pair)` | Concatenates two flows |
| `zip` | `zip(f1, f2)` / `zip(pair)` | Emits `[left, right]` items |

### 🟣 Bridge functions (cross the boundary)

| Helper | Direction | Notes |
| --- | --- | --- |
| `lines` | Value → Flow | Accepts stdin, list-of-strings, or existing flow |
| `evolve` | Value → Flow | Emits `init`, then `f(previous_value)` on later pulls |
| `each` | list or Flow → Flow | Returns a lazy effect stage; passes original items through when consumed |
| `collect` | list or Flow → list | Returns list data or materializes lazy flow into a list |
| `run` | list or Flow → nil | Traverses/consumes; returns `nil` |
| `reduce` | list or Flow → value | Folds items into accumulator; `none(...)` as initial accumulator is not short-circuited |
| `count` | list or Flow → int | Counts items; built on `reduce` |

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
| Rule-driven transform | — | 🔵 `flow \|> refine(..steps)` (preferred), `flow \|> rules(..fns)` (compatibility) | [case: pfv-transform-rules] |

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
| Reduce | 🟢 `reduce(f, acc, xs)` | 🟣 `flow \|> reduce(f, acc)` | [case: pfv-reduce] |
| Sum | 🟢 `sum(xs)` | 🟣 `flow \|> collect \|> sum` | [case: pfv-sum] |
| Count | 🟢 `count(xs)` | 🟣 `flow \|> count` | [case: pfv-count] |

## Positional access

| Goal | Value | Flow | [case] |
| --- | --- | --- | --- |
| First item | 🟢 `first(xs)` | 🟣 `flow \|> head(1) \|> collect \|> first` | [case: pfv-first] |
| Last item | 🟢 `last(xs)` | 🟣 `flow \|> collect \|> last` | [case: pfv-last] |
| Nth item | 🟢 `nth(index, xs)` | 🟣 `flow \|> collect \|> nth(index)` | [case: pfv-nth] |
| Take first n | 🟢 `take(n, xs)` | 🔵 `flow \|> take(n)` | [case: pfv-take-flow] |
| Drop first n | 🟢 `drop(n, xs)` | 🔵 `flow \|> drop(n)` | [case: pfv-drop-flow] |

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
| Side effect per item | 🟢 `xs \|> each(fn) \|> run` | 🔴 `flow \|> each(fn) \|> run` | [case: pfv-sink-each-run] |
| Print items | 🟢 `xs \|> each(print) \|> run` | 🔴 `flow \|> each(print) \|> run` | [case: pfv-sink-print] |
| Materialize | `xs \|> collect` returns list data | 🟣 `flow \|> collect` | [case: pfv-bridge-collect] |

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
| Column extraction + sum | 🟢 value-only with nested pipeline | 🟣 `stdin \|> lines \|> refine((r, _) -> split_whitespace(r) \|> nth(4) \|> parse_int \|> flat_map_some(step_emit)) \|> collect \|> sum` (preferred), `stdin \|> lines \|> rules((r, _) -> split_whitespace(r) \|> nth(4) \|> parse_int \|> flat_map_some(rule_emit)) \|> collect \|> sum` (compatibility) | [case: pfv-shape-column-sum] |
| Stream to output | 🟢 `xs \|> map(f) \|> map(print)` | 🔴 `stdin \|> lines \|> map(f) \|> each(print) \|> run` | [case: pfv-shape-stream-output] |

## CLI mode selection

| Goal | Mode | Why |
| --- | --- | --- |
| Stream stdin through flow stages | `-p 'stage_expr'` | `-p` injects `stdin \|> lines` and consumes the final Flow |
| Produce a final collected value | `-c 'source'` or file mode | You control full program shape and materialization |
| File program with `main(argv())` | file mode | Supports trailing args and runtime dispatch |

Pipe mode runs the stage expression over `stdin |> lines`, then consumes the final Flow automatically.
Do not include explicit `stdin` or `run` in `-p`.
For reducers like `sum` that require a list, use `collect` first or use `-c`. `reduce` and `count` accept Flow directly.

## Value-only pipeline example

<!-- [case: pfv-value-only-pipeline] -->
```genia
[3, 1, 4, 1, 5] |> filter((x) -> x > 2) |> map((x) -> x * 10) |> sum
```
Classification: **Valid** (directly tested)

## Flow-only pipeline example

<!-- [case: pfv-flow-only-pipeline] -->
```genia
["hello", "world"] |> lines |> map(upper) |> each(print) |> run
```
Classification: **Valid** (directly tested)

## Explicit bridge example

<!-- [case: pfv-explicit-bridge] -->
```genia
["3", "bad", "7"] |> lines |> keep_some(parse_int) |> collect |> sum
```
Classification: **Valid** (directly tested)

## Option + Flow interaction example

<!-- [case: pfv-option-flow-example] -->
```genia
["10", "oops", "20"] |> lines |> map(parse_int) |> keep_some |> collect |> sum
```
Classification: **Valid** (directly tested)

---

## Rules of thumb

1. **Start from the input.** Stdin or IO? Use `lines` to enter Flow world. Already a list? Stay in Value world.
2. **Stay in one world.** Chain flow stages or chain value stages. Use Seq-compatible sinks when you only need ordered traversal/materialization.
3. **Cross explicitly.** `collect(flow)` is the Flow → Value bridge. `lines` is the primary Value → Flow bridge.
4. **Option composes orthogonally.** Pipeline `some`/`none` lifting works the same in both worlds.
5. **Use `keep_some` for stream-level Option filtering.** It is flow-oriented. For single Options, use `map_some`, `flat_map_some`, or `unwrap_or`.
6. **`reduce` and `count` are Seq-compatible.** They accept both lists and Flow directly. `sum` expects a list; use `collect` first for Flow input.
7. **Direct calls don't lift.** Automatic `some(x)` unwrapping is pipeline-only. Direct `f(some(x))` short-circuits.

## Gotchas

- `nth` is `nth(index, xs)` in normal calls; `xs |> nth(index)` in pipeline style.
- `each(fn)` over a list or Flow does not execute effects until the returned Flow is consumed with `run` or `collect`.
- Flows are single-use; reusing a consumed flow raises a runtime error.
- `keep_some` is flow-oriented, not a list helper.
- Pipe mode runs the stage expression over `stdin |> lines` and consumes the final Flow automatically; do not include explicit `stdin` or `run`.
- `stdin` is a host input capability, not a Seq-compatible value. `stdin |> each(...)`, `stdin |> collect`, and `stdin |> run` all fail. Use `stdin |> lines` first to enter Flow world.
- `map`, `filter`, `take`, and `drop` are polymorphic: they work on both lists and flows, staying in whichever world they receive.
