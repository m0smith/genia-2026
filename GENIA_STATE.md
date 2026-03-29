# Genia — Current Language State (Main Branch)

This file describes what is **actually implemented now** in the Python runtime.

## 1) Execution model

- programs are expression sequences
- top-level assignment is supported (`name = expr`)
- blocks evaluate expressions in order and return the last value
- no statement/declaration split at runtime level

## 2) Implemented syntax and expression forms

- literals: number, string, boolean, `nil`
- variables
- function calls
- unary operators: `-`, `!`
- binary operators: `+ - * / % < <= > >= == != && ||`
- block expressions: `{ ... }`
- list literals: `[a, b, c]`
- list spread in literals: `[..xs]`, `[1, ..xs, 2]`
- call spread: `f(..xs)`
- lambdas: `(x) -> x + 1`
- varargs lambdas: `(..xs) -> xs`, `(a, ..rest) -> rest`

## 3) Functions and dispatch

- named functions are first-class values
- multiple definitions by arity shape are allowed
- varargs named functions are supported (`f(a, ..rest) = ...`)
- resolution behavior:
  - exact fixed arity beats varargs
  - if multiple varargs candidates match and neither is more specific, runtime raises `TypeError("Ambiguous function resolution")`

## 4) Case expressions and pattern matching

Case arms support:

```genia
pattern -> result
pattern ? guard -> result
```

Implemented pattern types:

- literal patterns
- variable binding
- wildcard `_`
- tuple patterns
- list patterns
- rest pattern `..name` / `.._` (list patterns only; final position only)
- duplicate binding semantics (same name must match equal value)

Case placement rules (enforced):

- allowed in function body
- allowed as final expression in block
- rejected in ordinary subexpressions / call args / non-final block positions

## 5) Builtins (runtime)

### Core I/O and utilities

- `log`, `print`, `input`, `stdin`, `help`
- constants in global env: `pi`, `e`, `true`, `false`, `nil`

### Refs

- `ref([initial])`
- `ref_get(ref)`
- `ref_set(ref, value)`
- `ref_is_set(ref)`
- `ref_update(ref, updater)`

Behavior: refs are synchronized host objects; `ref_get` / `ref_update` block until value is set when created via `ref()`.

### Host-backed concurrency

- `spawn(handler)`
- `send(process, message)`
- `process_alive?(process)`

Behavior:

- each process has FIFO mailbox
- one handler invocation at a time per process
- implemented with host threads

### Host-backed persistent associative maps (Phase 1 bridge)

- `map_new()`
- `map_get(map, key)`
- `map_put(map, key, value)`
- `map_has?(map, key)`
- `map_remove(map, key)`
- `map_count(map)`

Behavior:

- map values are opaque runtime values (`<map N>`) and do not expose host methods
- `map_new` returns an empty map
- `map_put` and `map_remove` are persistent (return a new map, do not mutate input map)
- `map_get` returns stored value or `nil` when key is missing
- `map_has?` returns `true`/`false`
- `map_count` returns entry count
- list keys are supported by stable structural key-freezing in runtime
- tuple keys are supported by the same runtime key-freezing strategy (runtime-level interop values)
- invalid map arguments and unsupported key types raise clear `TypeError`

### String builtins

- `byte_length`, `is_empty`, `concat`
- `contains`, `starts_with`, `ends_with`, `find`
- `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`
- `lower`, `upper`

### Simulation primitives (Phase 2, host-backed builtins)

- `rand()`
- `rand_int(n)`
- `sleep(ms)`

Behavior:

- `rand()` returns a float in `[0, 1)` using host RNG
- `rand_int(n)` returns an integer in `[0, n)`; raises clear `TypeError` for non-integer `n` and `ValueError` for `n <= 0`
- `sleep(ms)` blocks current execution for `ms` milliseconds; raises clear `TypeError` for non-numeric values and `ValueError` for negative values

## 6) Autoloaded stdlib

Autoload is keyed by `(name, arity)` and currently registers functions from:

- `std/prelude/list.genia`
- `std/prelude/fn.genia`
- `std/prelude/math.genia`
- `std/prelude/awk.genia`
- `std/prelude/agent.genia`

Notable autoloaded functions include:

- list: `list`, `first`, `rest`, `empty?`, `nil?`, `append`, `length`, `reverse`, `reduce`, `count`, `any?`, `nth`, `take`, `drop`
- fn: `apply`, `compose`
- math: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk: `awkify`, `awk_filter`, `awk_map`, `awk_count`, `fields`
- agent: `agent`, `agent_send`, `agent_get`, `agent_state`, `agent_alive?`

## 7) Optimization behavior

Implemented optimizations:

- self tail-call elimination via trampoline for tail-position calls
- specialized nth-style list traversal rewrite to `IrListTraversalLoop` for a narrow recognized recursion shape

## 8) Debug/runtime tooling

- parser/IR nodes carry source spans (filename + line/column ranges)
- `run_debug_stdio(...)` exposes debugger protocol endpoints used by the VS Code extension

## 9) Explicitly not implemented (current)

- map literals / map patterns
- general host interop / FFI layer
- module/import syntax
- member access syntax
- index syntax
- general pipeline operator syntax
- language-level scheduler/selective receive/timeouts (concurrency remains host-primitive based)
