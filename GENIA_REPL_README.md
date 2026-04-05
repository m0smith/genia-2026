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

Pass raw CLI args into a program:

```bash
python3 -m genia.interpreter path/to/file.genia --pretty input.txt
```

Run a command string:

```bash
python3 -m genia.interpreter -c "[1,2,3] |> count"
```

Run a pipeline stage expression:

```bash
python3 -m genia.interpreter -p 'head(1) |> each(print)'
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

- parser keeps a surface AST and lowers it into a minimal Core IR before evaluation
- runtime value categories today:
  - core values: Number, String, Boolean, `nil`, `none` / `some(value)`, List, Map
  - function / module values: Function, Module
  - callable behaviors layered on values: functions/lambdas, callable maps, callable string projectors
  - runtime capability values: `stdout`, `stderr`, Flow (runtime Phase 1 is implemented), Ref, Process handle, Bytes wrapper, Zip entry wrapper
  - current maybe/absence behavior is split: legacy helpers such as `map_get`, `cli_option`, string `find`, `nth`, and `first` remain non-Option, while `get?`, `first_opt`, `last`, and `find_opt` return `none` / `some(value)`
  - Option pattern matching supports literal `none` and constructor pattern `some(pattern)`
  - new `?`-suffixed APIs are boolean-returning; `get?` remains the current compatibility exception
- literals: numbers, strings (single/double quotes + escapes, plus triple-quoted multiline strings), booleans, `nil`, `none`
- variables and top-level assignment (`name = expr`)
- unary/binary operators: `!`, unary `-`, `+ - * / %`, comparisons, equality, `&&`, `||`
- pipeline operator (phase 2): `|>` with call-rewrite semantics (`x |> f` → `f(x)`, `x |> f(y)` → `f(y, x)`, `x |> expr` → `expr(x)` when `expr` is valid in ordinary call-callee position)
  - example: `record |> "name"` behaves like `"name"(record)`
  - lowering/desugaring happens in the AST→Core IR pass
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
- map literals (`{name: "m"}`, `{"name": "m"}`, `{}`)
- module import forms: `import mod`, `import mod as alias`
  - imports are cached by module name; repeated imports/aliases reuse the same module value
- phase-1 slash named accessor: `mod/name`, `map/name` (bare identifier RHS only)
- callable data (phase 1 subset):
  - map lookup calls: `m(key)`, `m(key, default)`
  - string projector calls over maps: `"key"(m)`, `"key"(m, default)`
- function-call argument spread (`f(..xs)`)
- pattern matching:
  - tuple patterns
  - list patterns
  - map patterns (`{name}`, `{name: n}`, `{"name": n}`)
  - glob string patterns (`glob"..."`) with whole-string matching only
  - option constructor patterns (`some(pattern)`) and literal `none`
  - wildcard `_`
  - rest pattern `..rest` / `.._`
  - duplicate-binding equality semantics (`[x, x]`)
  - guards with `?`
- case expressions in function bodies and as final expression in a block
- conditionals expressed only through pattern matching in function definitions/case expressions
- function resolution with fixed arity + varargs precedence
- autoloaded stdlib functions keyed by `(name, arity)`
  - includes list transforms/helpers such as `reduce`, `map`, `filter`, `first_opt`, `last`, `find_opt`, and `range`
  - includes cell helpers `cell`, `cell_with_state`, `cell_send`, `cell_get`, `cell_state`, `cell_failed?`, `cell_error`, `restart_cell`, `cell_status`, `cell_alive?`
  - bundled prelude `.genia` sources are loaded from package resources rather than checkout-relative paths
  - prelude helper docs are Markdown docstrings and display through `help("name")`
- builtins:
  - I/O: `log`, `print`, `input`, `stdin`, `stdout`, `stderr`, `write`, `writeln`, `flush`, `help`
  - CLI: `argv`, `cli_parse`, `cli_flag?`, `cli_option`, `cli_option_or`
  - refs: `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`
  - concurrency: `spawn`, `send`, `process_alive?`
  - phase-1 persistent associative maps: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
  - phase-1 primitive option model: `none`, `some`, `get?`, `unwrap_or`, `is_some?`, `is_none?`
  - simulation primitives (phase 2): `rand`, `rand_int`, `sleep`
  - bytes/json/zip bridge builtins (phase 1):
    - `utf8_encode`, `utf8_decode`
    - `json_parse`, `json_pretty`
    - `zip_entries`, `zip_write`
    - `entry_name`, `entry_bytes`, `set_entry_bytes`, `update_entry_bytes`, `entry_json`
  - strings: `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`, `find`, `split`, `split_whitespace`, `join`, `trim`, `trim_start`, `trim_end`, `lower`, `upper`
  - constants: `pi`, `e`, `true`, `false`, `nil`
- flow runtime (phase 1):
  - `stdin |> lines` creates a lazy single-use flow
  - Flow is a runtime value family; pipeline syntax itself is unchanged call rewriting
  - binding `stdin` into a flow does not read all input up front
  - `stdin()` still returns cached full stdin lines for compatibility
  - transforms: `lines`, `map`, `filter`, `take`
  - stdlib aliases: `head(flow)`, `head(n, flow)`
  - sinks/materialization: `each`, `run`, `collect`
  - consuming the same flow twice raises `RuntimeError("Flow has already been consumed")`
  - `take`/`head` perform early upstream termination without over-reading one extra item (normal completion)
- Option/list notes:
  - `first(list)` remains the legacy non-empty extractor and raises a normal match failure on `[]`
  - `first_opt(list)`, `last(list)`, and `find_opt(predicate, list)` return `none` / `some(value)`
  - string `find(string, needle)` remains the legacy index-or-`nil` API
  - `some(nil)` is valid and distinct from `none`
- cell semantics (phase 1 fail-stop):
  - cells queue asynchronous updates and run them one at a time
  - failed updates preserve prior state, cache an error string, and mark the cell failed
  - failed cells reject future `cell_send` and `cell_get`
  - `cell_error(cell)` returns `none` or `some(error_string)`
  - `restart_cell(cell, new_state)` clears failure and discards queued pre-restart updates
  - nested `cell_send` calls made during an update are committed only if that update succeeds
- CLI pipe mode:
  - `-p` / `--pipe` wrap the provided stage expression as `stdin |> lines |> <expr> |> run`
  - pipe mode expects a single stage expression, not a full standalone program
  - explicit `stdin` and explicit `run` are rejected with a clear error
  - pipe mode bypasses the `main` convention
  - no `pipe(...)` helper function exists in this phase
- output routing:
  - `print(...)` writes to `stdout`
  - `log(...)` writes to `stderr`
  - `write(sink, value)` / `writeln(sink, value)` write display-formatted output
  - `flush(sink)` flushes a sink
  - broken pipe on `stdout` output in command/file execution is treated as normal downstream termination without a Python traceback
  - REPL results go to `stdout`; REPL and command/file diagnostics go to `stderr`

## REPL commands

- `:help`
- `:env`
- `:quit`
- `help(name)` to inspect named-function metadata (`name/shape`, source location, rendered docstring, undocumented fallback)

## Not implemented (current)

- regex patterns / extglob operators
- `$1` / `$2` / `ARGV`-style special CLI syntax
- general host interop / FFI
- general member access and indexing syntax
- a language-level scheduler (concurrency is host-thread based)
- full Flow runtime system beyond phase 1 (async scheduling, multi-port stages, richer cancellation/backpressure controls)

## Conditionals in Genia

- Genia does **not** use `if` or `switch`.
- All branching is expressed through pattern matching.
- There is no dedicated conditional keyword.

## CLI args model (list-first)

- `argv()` returns raw trailing command-line args as a plain list of strings.
- Positional-only CLI programs should pattern match directly on that list.
- `cli_parse(args)` returns `[opts, positionals]` where `opts` is a persistent map.
- `cli_parse(args, spec)` supports minimal map spec keys:
  - `flags`: list of names forced to boolean
  - `options`: list of names forced to consume values
  - `aliases`: map alias->canonical name
- This layer does **not** add shell tokenization, dotted access syntax, or `$` positional variables.

## Program entrypoint behavior

- In **file mode** and **`-c` command mode**, Genia applies a runtime `main` convention after top-level evaluation:
  1. If `main/1` exists, it runs `main(argv())`.
  2. Else if `main/0` exists, it runs `main()`.
  3. Else, no entrypoint call is made (existing behavior is preserved).
- In **pipe mode** (`-p` / `--pipe`), Genia runs the wrapped flow directly and does not apply the `main` convention.
- In **REPL mode**, no automatic `main` invocation is performed.
- `main` remains a normal function name (not syntax).

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
