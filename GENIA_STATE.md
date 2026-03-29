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

### String builtins

- `byte_length`, `is_empty`, `concat`
- `contains`, `starts_with`, `ends_with`, `find`
- `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`
- `lower`, `upper`

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
- module/import syntax
- member access syntax
- index syntax
- general pipeline operator syntax
- language-level scheduler/selective receive/timeouts (concurrency remains host-primitive based)
