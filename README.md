# Genia

Genia is a small, functional-first, expression-oriented language prototype.

This repository currently provides:

- a parser + evaluator (`src/genia/interpreter.py`)
- a REPL and file runner (`python3 -m genia.interpreter`)
- host-backed concurrency primitives (`spawn`, `send`, `process_alive?`)
- refs (`ref`, `ref_get`, `ref_set`, `ref_update`)
- autoloaded prelude libraries (lists, math helpers, awk helpers, fn helpers, agents)
- debug-stdio adapter support for editor integration

## Quick start

```bash
python3 -m genia.interpreter
```

Run a program:

```bash
python3 -m genia.interpreter path/to/program.genia
```

Run tests:

```bash
pytest -q
```

## Language snapshot (implemented)

### Core values

- Number
- String (UTF-8 safe helpers available through builtins)
- Boolean (`true`, `false`)
- Nil (`nil`)
- List
- Function
- Host-backed reference (`ref`)
- Host-backed process handle (`spawn`)
- Host-backed persistent associative map (`map_new`, `map_put`, ...)

### Functions and lambdas

```genia
square(x) = x * x
inc = (x) -> x + 1
list = (..xs) -> xs
```

- functions are dispatched by name + arity shape (fixed arity preferred over varargs)
- varargs supported in named functions and lambdas via `..rest`
- closures are supported

### Pattern matching

```genia
head(xs) =
  [x, .._] -> x
```

Supported pattern forms:

- literals (`0`, `"ok"`, `true`, `nil`)
- variable bindings
- wildcard `_`
- tuple patterns (`(a, b)`)
- list patterns (`[x, ..rest]`)
- guards (`pattern ? condition -> result`)
- duplicate bindings (`[x, x]` only matches equal values)

### Case placement rules

Case expressions are valid only:

- as a function body
- as the final expression in a block

### Lists and spread

```genia
[1, ..[2, 3], 4]
add(..[20, 22])
```

- list literal spread is implemented
- function call argument spread is implemented

### Concurrency and agents

```genia
counter = agent(0)
agent_send(counter, (n) -> n + 1)
agent_get(counter)
```

- `spawn(handler)` creates a host-thread worker with FIFO mailbox
- `send(process, message)` enqueues messages
- `process_alive?(process)` reports worker liveness
- prelude provides `agent`, `agent_send`, `agent_get`, `agent_state`, `agent_alive?`

## Builtins

### Core

- `log`, `print`, `input`, `stdin`, `help`
- constants: `pi`, `e`, `true`, `false`, `nil`

### Refs

- `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`

### Strings

- `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`
- `find`, `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`, `lower`, `upper`

### Concurrency

- `spawn`, `send`, `process_alive?`

### Phase 1 persistent associative maps

- `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- implemented as an opaque host-backed runtime wrapper (no map syntax added)
- persistent semantics from Genia perspective (`map_put`/`map_remove` return new map values)

## Autoloaded stdlib highlights

- list helpers: `list`, `first`, `rest`, `append`, `length`, `reverse`, `nth`, `take`, `drop`, ...
- fn helpers: `apply`, `compose`
- math helpers: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk-ish helpers: `awkify`, `awk_filter`, `awk_map`, `awk_count`, `fields`
- agents: `agent`, `agent_send`, `agent_get`, `agent_state`, `agent_alive?`

## Not implemented yet

- map literals/patterns
- general host interop / FFI
- module/import syntax
- member access / indexing syntax
- general pipeline operator syntax

For stricter implementation details and invariants, see:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
