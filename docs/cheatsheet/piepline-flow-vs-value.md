# Genia Pipeline: Flow vs Value Matrix

A dense reference for choosing between Value and Flow pipelines.

Legend: 🟢 Value  🔵 Flow  🟣 Bridge  🔴 Sink

---

## 🔁 Transforms

| Function description | Value function                | Flow function                      | Comments                                                                    |
| -------------------- | ----------------------------- | ---------------------------------- | --------------------------------------------------------------------------- |
| Transform each item  | 🟢 `map(f, xs)`               | 🔵 `flow \|> map(f)`               | Same semantics. Flow version is lazy and processes items as pulled.         |
| Transform with index | 🟢 `enumerate(xs) \|> map(f)` | 🔵 `flow \|> enumerate \|> map(f)` | Index-aware transform. Flow preserves laziness.                             |
| Apply function chain | 🟢 `x \|> f \|> g`            | 🔵 `flow \|> map(f) \|> map(g)`    | Value pipelines operate on whole value; Flow pipelines operate per element. |

---

## 🔍 Filters / Selection

| Function description         | Value function                    | Flow function                              | Comments                                                       |
| ---------------------------- | --------------------------------- | ------------------------------------------ | -------------------------------------------------------------- |
| Keep matching items          | 🟢 `filter(pred, xs)`             | 🔵 `flow \|> filter(pred)`                 | Same logic; Flow version avoids materializing full collection. |
| Remove invalid Option values | 🟢 `keep_some(xs)`                | 🔵 `flow \|> keep_some`                    | Critical after parsing or lookups.                             |
| Conditional transform+filter | 🟢 `map(parse_int) \|> keep_some` | 🔵 `flow \|> map(parse_int) \|> keep_some` | Canonical “clean pipeline” pattern.                            |

---

## 📊 Reducers / Aggregation

| Function description | Value function          | Flow function                            | Comments                                                   |
| -------------------- | ----------------------- | ---------------------------------------- | ---------------------------------------------------------- |
| Reduce to value      | 🟢 `reduce(f, acc, xs)` | 🟣 `flow \|> collect \|> reduce(f, acc)` | Flow must be materialized unless streaming reducer exists. |
| Sum values           | 🟢 `sum(xs)`            | 🟣 `flow \|> collect \|> sum`            | Always `keep_some` first if Option possible.               |
| Count items          | 🟢 `count(xs)`          | 🟣 `flow \|> collect \|> count`          | Flow requires consumption.                                 |

---

## 📍 Positional / Indexing

| Function description | Value function  | Flow function                     | Comments                                  |
| -------------------- | --------------- | --------------------------------- | ----------------------------------------- |
| First item           | 🟢 `first(xs)`  | 🔵 `flow \|> head(1)`             | Flow version short-circuits early.        |
| Last item            | 🟢 `last(xs)`   | 🟣 `flow \|> collect \|> last`    | Requires full consumption.                |
| Nth item             | 🟢 `nth(xs, i)` | 🔵 `flow \|> drop(i) \|> head(1)` | Flow version avoids full materialization. |
| Skip items           | 🟢 `rest(xs)`   | 🔵 `flow \|> drop(n)`             | Flow form is more general.                |

---

## 🧩 Option / Maybe Handling

| Function description  | Value function        | Flow function                       | Comments                                                        |
| --------------------- | --------------------- | ----------------------------------- | --------------------------------------------------------------- |
| Map optional value    | 🟢 `map_some(f, opt)` | 🔵 `flow \|> map(f) \|> keep_some`  | Different levels: single Option vs stream of Options.           |
| Filter present values | 🟢 `keep_some(xs)`    | 🔵 `flow \|> keep_some`             | Removes `none(...)`.                                            |
| Short-circuit on none | 🟢 `none(...) \|> f`  | 🔵 handled per-item via `keep_some` | Value pipelines stop entirely; Flow pipelines skip per element. |

---

## 🔊 Side Effects / Sinks

| Function description | Value function       | Flow function                     | Comments                                  |
| -------------------- | -------------------- | --------------------------------- | ----------------------------------------- |
| Apply side effect    | 🟢 `map(print, xs)`  | 🔴 `flow \|> each(print) \|> run` | Flow requires terminal operation (`run`). |
| Debug pipeline       | 🟢 inline inspection | 🔴 `flow \|> each(print)`         | No execution until consumed.              |

---

## 🔄 Flow ↔ Value Bridges

| Function description | Value function     | Flow function                    | Comments                    |
| -------------------- | ------------------ | -------------------------------- | --------------------------- |
| Materialize stream   | 🟢 already value   | 🟣 `flow \|> collect`            | Main Flow → Value bridge.   |
| Start stream         | 🟢 not applicable  | 🔵 `stdin \|> lines`             | Native Flow source.         |
| Return to pipeline   | 🟢 `xs \|> map(f)` | 🟣 `flow \|> collect \|> map(f)` | Explicit boundary crossing. |

---

## 🔗 Common Pipeline Shapes

| Pattern                       | Value                                            | Flow                                                                                 | Comments              |
| ----------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------ | --------------------- |
| Clean → transform → aggregate | 🟢 `xs \|> map(parse_int) \|> keep_some \|> sum` | 🟣 `flow \|> map(parse_int) \|> keep_some \|> collect \|> sum`                       | Most common pattern.  |
| Transform → filter → output   | 🟢 `xs \|> map(f) \|> filter(p)`                 | 🔴 `flow \|> map(f) \|> filter(p) \|> each(print) \|> run`                           | CLI-style pipeline.   |
| Extract column → aggregate    | 🟢 `map(nth(_, i), xs) \|> sum`                  | 🔵 `flow \|> map(split) \|> map(nth(_, i)) \|> map(parse_int) \|> keep_some \|> sum` | AWK-style processing. |

---

## ⚠️ Rules of Thumb

* Stay in **Flow** for streaming, stdin, large data, and early termination.
* Stay in **Value** for in-memory operations and indexing.
* Use `collect` only when you intentionally cross into Value space.
* `none(...)` stops Value pipelines entirely.
* Flow pipelines handle absence **per element**, not globally.
* Flows are **lazy and single-use**.
* `each(...)` does nothing without `run`.

---

## 🚨 Gotchas

* `nth(xs, i)` requires **two arguments**
* `none(...)` will break aggregation unless filtered
* `stdin \|> lines` does nothing without a sink
* Flow pipelines must end with `run` or `collect`
* `some(...)` is not auto-unwrapped in pipelines

---

## 🚀 One-Liner

> Value = whole collection
> Flow = item-by-item stream
