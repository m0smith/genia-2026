# Genia Prototype REPL

This document describes the **actual current behavior** of the Python prototype in `src/genia/interpreter.py`.

## Run

Run the REPL:

```bash
python3 -m genia.interpreter
```

Run a program file:

```bash
python3 -m genia.interpreter path/to/file.genia
```

Run a command string:

```bash
python3 -m genia.interpreter -c "[1,2,3] |> count"
```

Run the ants demo:

```bash
python3 -m genia.interpreter examples/ants.genia
```

Run in stdio debug-adapter mode:

```bash
python3 -m genia.interpreter --debug-stdio path/to/file.genia
```

## Implemented today

- literals: numbers, strings (single/double quotes + escapes, plus triple-quoted multiline strings), booleans, `nil`
- variables and top-level assignment (`name = expr`)
- unary/binary operators: `!`, unary `-`, `+ - * / %`, comparisons, equality, `&&`, `||`
- pipeline operator (phase 1): `|>` with call-rewrite semantics (`x |> f` → `f(x)`, `x |> f(y)` → `f(y, x)`)
- function definitions with expression body, block body, or case body
- optional named-function docstring metadata:
  - `f(x) = """ ... """ x + 1` (multi-line Markdown docstring literal)
  - docstring is attached to function metadata (not evaluated as runtime expression)
  - lambdas do not support docstrings
  - `help(name)` renders docstrings as lightweight Markdown text (headings, lists, inline code, fenced code blocks)
  - help output normalizes docstring indentation/blank lines and strips optional outer triple-quote wrappers in docstring text
  - official docstring style/templates live in `docs/book/03-functions.md`
- lambda expressions, including varargs lambdas with `..rest`
- list literals with spread (`[..xs]`, `[1, ..xs, 2]`)
- function-call argument spread (`f(..xs)`)
- pattern matching:
  - tuple patterns
  - list patterns
  - wildcard `_`
  - rest pattern `..rest` / `.._`
  - duplicate-binding equality semantics (`[x, x]`)
  - guards with `?`
- case expressions in function bodies and as final expression in a block
- conditionals expressed only through pattern matching in function definitions/case expressions
- function resolution with fixed arity + varargs precedence
- autoloaded stdlib functions keyed by `(name, arity)`
  - includes list transforms/helpers such as `reduce`, `map`, `filter`, and `range`
  - prelude helper docs are Markdown docstrings and display through `help("name")`
- builtins:
  - I/O: `log`, `print`, `input`, `stdin`, `help`
  - refs: `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`
  - concurrency: `spawn`, `send`, `process_alive?`
  - phase-1 persistent associative maps: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
  - simulation primitives (phase 2): `rand`, `rand_int`, `sleep`
  - bytes/json/zip bridge builtins (phase 1):
    - `utf8_encode`, `utf8_decode`
    - `json_parse`, `json_pretty`
    - `zip_entries`, `zip_write`
    - `entry_name`, `entry_bytes`, `set_entry_bytes`, `update_entry_bytes`, `entry_json`
  - strings: `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`, `find`, `split`, `split_whitespace`, `join`, `trim`, `trim_start`, `trim_end`, `lower`, `upper`
  - constants: `pi`, `e`, `true`, `false`, `nil`

## REPL commands

- `:help`
- `:env`
- `:quit`
- `help(name)` to inspect named-function metadata (`name/shape`, source location, rendered docstring, undocumented fallback)

## Not implemented (current)

- map/dict literals and map patterns
- general host interop / FFI
- module/import system
- member access and indexing syntax
- a language-level scheduler (concurrency is host-thread based)
- generalized flow semantics (lazy sequences, multi-output stages, backpressure, cancellation)
- full Flow runtime system (stages/sinks/backpressure/cancellation/multi-port stages)

## Conditionals in Genia

- Genia does **not** use `if` or `switch`.
- All branching is expressed through pattern matching.
- There is no dedicated conditional keyword.

## Simulation primitive semantics

- `rand()` returns a host-RNG float in `[0, 1)`.
- `rand_int(n)` returns an integer in `[0, n)` and raises:
  - `TypeError` when `n` is not an integer
  - `ValueError` when `n <= 0`
- `sleep(ms)` blocks execution for `ms` milliseconds and raises:
  - `TypeError` when `ms` is not numeric
  - `ValueError` when `ms < 0`

These are blocking builtins only; they do not introduce scheduler/async runtime behavior.

## Bytes / JSON / ZIP bridge semantics

- `utf8_encode(string)` returns an opaque bytes wrapper value.
- `utf8_decode(bytes)` decodes UTF-8 and raises `ValueError` for invalid byte sequences.
- `json_parse(string)` parses JSON and raises `ValueError` for invalid JSON text.
  - JSON objects become runtime map values (same family used by `map_new`/`map_put`).
- `json_pretty(value)` renders deterministic pretty JSON (`indent=2`, sorted keys).
- `zip_entries(path)` returns an eager list of zip entry wrapper values in archive order.
- `zip_write(entries, path)` writes entries in order and returns `path`.
  - It also accepts `(path, entries)` to stay pipeline-friendly with current `|>` rewrite behavior.

## Demo note: ants simulation example

- `examples/ants.genia` is the first in-repo stochastic grid simulation demo.
- It is text-only, single-ant, recursive, and finite-step.
- It uses builtins only (`map_*`, `rand_int`, `sleep`, `print`) with no new syntax.
- It is not actor-based and does not provide a scheduler/event loop abstraction.
