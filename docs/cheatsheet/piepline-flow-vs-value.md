# Genia Pipeline: Flow vs Value Matrix

Dense implemented-only reference for choosing value pipelines vs flow pipelines.

Legend: 🟢 Value  🔵 Flow  🟣 Bridge  🔴 Sink

Validation: runnable rows include `[case: <id>]` in comments and are executed by pytest.

## Transforms

| Function description | Value function | Flow function | Comments |
| --- | --- | --- | --- |
| Transform each item | 🟢 `map(f, xs)` | 🔵 `flow \|> map(f)` | Same map stage semantics; flow stays lazy. [case: pfv-transform-map] |
| Transform then transform | 🟢 `xs \|> map(f) \|> map(g)` | 🔵 `flow \|> map(f) \|> map(g)` | Stage chaining applies left-to-right in both. [case: pfv-transform-chain] |
| Rule-driven transform | not applicable | 🔵 `flow \|> rules(..fns)` | `rules` is flow-oriented orchestration. [case: pfv-transform-rules] |

## Filters / selection

| Function description | Value function | Flow function | Comments |
| --- | --- | --- | --- |
| Keep matching items | 🟢 `filter(pred, xs)` | 🔵 `flow \|> filter(pred)` | Predicate filtering in either pipeline style. [case: pfv-filter-predicate] |
| Keep only successful Option items | manual list filtering | 🔵 `flow \|> keep_some` | `keep_some` is a flow helper. [case: pfv-filter-keep-some] |
| Apply Option stage and keep successes | 🟢 `map(stage, xs)` then manual filtering | 🔵 `flow \|> keep_some(stage)` | Equivalent to `keep_some_else(stage, (_) -> nil)`. [case: pfv-filter-keep-some-stage] |
| Route failed Option items | manual split logic | 🔵 `flow \|> keep_some_else(stage, dead_handler)` | `some(v)` continues as `v`; `none(...)` goes to dead handler. [case: pfv-filter-keep-some-else] |

## Reducers / aggregation

| Function description | Value function | Flow function | Comments |
| --- | --- | --- | --- |
| Reduce | 🟢 `reduce(f, acc, xs)` | 🟣 `flow \|> collect \|> reduce(f, acc)` | Flow reduction crosses boundary via `collect`. [case: pfv-reduce] |
| Sum | 🟢 `sum(xs)` | 🟣 `flow \|> collect \|> sum` | `sum` expects plain numbers after intentional filtering/recovery. [case: pfv-sum] |
| Count | 🟢 `count(xs)` | 🟣 `flow \|> collect \|> count` | Same count after collecting flow to list. [case: pfv-count] |

## Positional / indexing / slicing

| Function description | Value function | Flow function | Comments |
| --- | --- | --- | --- |
| First item | 🟢 `first(xs)` | 🟣 `flow \|> head(1) \|> collect \|> first` | Head can bound flow; `first` returns Option. [case: pfv-first] |
| Last item | 🟢 `last(xs)` | 🟣 `flow \|> collect \|> last` | Last requires full traversal. [case: pfv-last] |
| Nth item | 🟢 `nth(index, xs)` | 🟣 `flow \|> collect \|> nth(index)` | Canonical call shape is `nth(index, xs)`. [case: pfv-nth] |
| Take first n | 🟢 `take(n, xs)` | 🟣 `flow \|> head(n) \|> collect` | `head` is the flow-facing limiter. [case: pfv-take-head] |

## Option / maybe handling

| Function description | Value function | Flow function | Comments |
| --- | --- | --- | --- |
| Map inside Option | 🟢 `map_some(f, opt)` | 🔵 `flow \|> map(stage) \|> keep_some` | Value side is one Option; flow side is stream of Options. [case: pfv-option-map-some] |
| Flat-map Option | 🟢 `flat_map_some(f, opt)` | 🔵 `flow \|> keep_some(stage)` | `stage` should return Option per item. [case: pfv-option-flat-map-some] |
| Provide fallback | 🟢 `unwrap_or(default, opt)` | 🔵 `flow \|> map((x) -> unwrap_or(default, x \|> stage))` | Fallback is explicit per item. [case: pfv-option-unwrap-or] |
| Pipeline behavior on `none(...)` | 🟢 `none(...) \|> f` short-circuits | 🔵 use `keep_some` or `keep_some_else` | Pipelines preserve `some(...)`; no implicit unwrapping. [case: pfv-option-none-short-circuit] |

## Side effects / sinks

| Function description | Value function | Flow function | Comments |
| --- | --- | --- | --- |
| Side effect per item | 🟢 `map(fn, xs)` plus later consumption | 🔴 `flow \|> each(fn) \|> run` | `each` is pass-through; `run` consumes flow. [case: pfv-sink-each-run] |
| Print items | 🟢 `xs \|> map(print)` plus later consumption | 🔴 `flow \|> each(print) \|> run` | Common stream sink shape. [case: pfv-sink-print] |
| Materialize result | already value | 🟣 `flow \|> collect` | `collect` is the value bridge sink. [case: pfv-bridge-collect] |

## Bridges Flow <-> Value

| Function description | Value function | Flow function | Comments |
| --- | --- | --- | --- |
| Start flow from stdin | not applicable | 🔵 `stdin \|> lines` | Standard input source bridge. [case: pfv-bridge-stdin-lines] |
| Start flow from list | 🟢 `xs` | 🔵 `xs \|> lines` | `lines` accepts list-of-strings input. [case: pfv-bridge-list-lines] |
| Keep in flow world | not applicable | 🔴 `... \|> map/filter/rules/... \|> each(...) \|> run` | Streaming path to effect sink. [case: pfv-bridge-run] |
| Cross to value world | already value | 🟣 `flow \|> collect` | Explicit flow-to-list boundary. [case: pfv-bridge-collect-2] |

## Common pipeline shapes

| Pattern | Value | Flow | Comments |
| --- | --- | --- | --- |
| Parse and aggregate | 🟢 `rows \|> map(parse_int) \|> map((o) -> unwrap_or(0, o)) \|> sum` | 🟣 `rows \|> lines \|> keep_some(parse_int) \|> collect \|> sum` | Flow form naturally drops failed parses. [case: pfv-shape-parse-aggregate] |
| Column extraction and sum | 🟢 `rows \|> map((r) -> split_whitespace(r) \|> nth(4) \|> flat_map_some(parse_int)) \|> map((o) -> unwrap_or(0, o)) \|> sum` | 🟣 `stdin \|> lines \|> rules((r, _) -> split_whitespace(r) \|> nth(4) \|> flat_map_some(parse_int) \|> flat_map_some(rule_emit)) \|> collect \|> sum` | Mirrors current unix-style rules pattern. [case: pfv-shape-column-sum] |
| Stream to output | 🟢 `xs \|> map(f) \|> map(print)` plus consumption | 🔴 `stdin \|> lines \|> map(f) \|> each(print) \|> run` | Flow path is direct for CLI streaming. [case: pfv-shape-stream-output] |

## Rules of thumb

- Use flow when reading stdin, streaming, or applying effect sinks.
- Use value pipelines for in-memory list transforms and direct indexing helpers.
- Cross from flow to value only when needed, with `collect`.
- Treat `keep_some` and `keep_some_else` as flow-level Option routing tools.
- Remember pipeline `none(...)` short-circuits while `some(...)` is preserved.
- Treat `sum` as a plain-number reducer, not an Option-aware stage.
- Prefer explicit Option helpers (`map_some`, `flat_map_some`, `unwrap_or`) over implicit assumptions.

## Gotchas

- `nth` is `nth(index, xs)` in normal calls; `xs \|> nth(index)` is pipeline style.
- `each(fn)` does not execute anything until the flow is consumed (`run` or `collect`).
- Flows are single-use; reusing the same flow value raises a runtime flow-reuse error.
- `keep_some` is flow-oriented, not a list helper.
- Pipe mode already wraps input as `stdin \|> lines \|> <stage_expr> \|> run`; do not include explicit `stdin` or `run` there.
