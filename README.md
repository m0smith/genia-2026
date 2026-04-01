# Genia

Genia is a small, functional-first, expression-oriented language prototype.

This repository currently provides:

- a parser + evaluator (`src/genia/interpreter.py`)
- a REPL and file runner (`python3 -m genia.interpreter`)
- host-backed concurrency primitives (`spawn`, `send`, `process_alive?`)
- refs (`ref`, `ref_get`, `ref_set`, `ref_update`)
- list-first CLI args + parsing helpers (`argv`, `cli_parse`, `cli_flag?`, `cli_option`, `cli_option_or`)
- simulation primitives (`rand`, `rand_int`, `sleep`)
- autoloaded prelude libraries (lists, math helpers, awk helpers, fn helpers, agents)
- debug-stdio adapter support for editor integration
- runnable demos under `examples/` (including `tic-tac-toe.genia` and `ants.genia`)

## Quick start

```bash
python3 -m genia.interpreter
```

Run a program:

```bash
python3 -m genia.interpreter path/to/program.genia
```

Pass raw trailing CLI args into the running program:

```bash
python3 -m genia.interpreter path/to/program.genia --pretty input.txt
```

Run inline source from the command line:

```bash
genia -c "[1,2,3] |> count"
```

Run the ants demo:

```bash
python3 -m genia.interpreter examples/ants.genia
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
- Host-backed bytes wrapper
- Host-backed zip entry wrapper

### Functions and lambdas

```genia
square(x) = x * x
inc = (x) -> x + 1
list = (..xs) -> xs
```

- functions are dispatched by name + arity shape (fixed arity preferred over varargs)
- varargs supported in named functions and lambdas via `..rest`
- named functions may include optional docstring metadata:
  - example:
    ```genia
    inc(x) = """
    # inc

    Increment by one.
    """ x + 1
    ```
  - `help(name)` renders docstrings with lightweight Markdown-aware formatting
  - official style guide + templates: `docs/book/03-functions.md` ("Official Docstring Style Guide")
- closures are supported

### Pattern matching

```genia
head(xs) =
  [x, .._] -> x
```

Supported pattern forms:

- literals (`0`, `"ok"`, `true`, `nil`)
- glob string patterns (`glob"..."`) for whole-string string matching
- variable bindings
- wildcard `_`
- tuple patterns (`(a, b)`)
- list patterns (`[x, ..rest]`)
- guards (`pattern ? condition -> result`)
- duplicate bindings (`[x, x]` only matches equal values)

### Conditionals in Genia

- Genia does **not** use `if` or `switch`
- all conditional logic is expressed with function-based pattern matching
- pattern matching is the only branching mechanism

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

### Pipeline operator (Phase 1)

```genia
[1, 2, 3] |> map(inc)
```

- `x |> f` rewrites to `f(x)`
- `x |> f(y)` rewrites to `f(y, x)` (append piped value as final argument)
- left-associative chaining is supported (`a |> f |> g`)
- this is expression-level composition only (not full flow runtime semantics)

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
- `help(name)` prints named function metadata (`name/shape`, source if available, rendered docstring, or undocumented fallback)
- stdlib prelude helpers include Markdown docstrings for learn-by-inspection via `help("name")`
- constants: `pi`, `e`, `true`, `false`, `nil`

### CLI args / options (runtime layer)

- `argv()` exposes raw trailing CLI args as a plain list of strings
- `cli_parse(args)` and `cli_parse(args, spec)` return `[opts_map, positionals]`
- `cli_flag?(opts, name)`, `cli_option(opts, name)`, `cli_option_or(opts, name, default)` help read options cleanly
- no `$1`/`$2` syntax is added; positional arguments are list-pattern friendly

## CLI Programs (`main` Entrypoint Convention)

In file mode (`genia path/to/program.genia`) and command mode (`genia -c "..."`), Genia checks for `main` after top-level evaluation:

1. `main/1` → called as `main(argv())`
2. else `main/0` → called as `main()`
3. else → no implicit entrypoint call

`main` is a runtime convention, not syntax.

Example (`main/1` + list pattern matching):

```genia
main(args) =
  [] -> print("usage") |
  ["hello", name] -> print("Hello " + name) |
  _ -> print("unknown command")
```

Example (`main/0`):

```genia
main() = print("Hello world")
```

### Refs

- `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`

### Strings

- `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`
- `find`, `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`, `lower`, `upper`

### Concurrency

- `spawn`, `send`, `process_alive?`

### Simulation primitives (Phase 2)

- `rand()` returns a float in `[0, 1)`
- `rand_int(n)` returns an integer in `[0, n)` for positive integer `n`
- `sleep(ms)` blocks for `ms` milliseconds
- intentionally simple: no scheduler, no async/await, no event loop

### Bytes / JSON / ZIP bridge builtins (Phase 1)

- `utf8_encode(string) -> bytes`
- `utf8_decode(bytes) -> string`
- `json_parse(string) -> value` (objects become runtime map values)
- `json_pretty(value) -> string`
- `zip_entries(path) -> list of zip entries`
- `zip_write(entries, path) -> path` (also accepts `(path, entries)` for pipeline style)
- `entry_name(entry)`, `entry_bytes(entry)`, `set_entry_bytes(entry, bytes)`, `update_entry_bytes(entry, f)`, `entry_json(entry)`

This is a minimal host-backed bridge for pipeline-first archive transforms; it is **not** the full Flow runtime system.

Example archive rewrite pipeline (list-based in this phase):

```genia
rewrite_entry(entry) =
  entry ? entry_json(entry) ->
    update_entry_bytes(entry, compose(utf8_encode, json_pretty, json_parse, utf8_decode)) |
  _ -> entry

rewrite_zip(in_path, out_path) =
  zip_entries(in_path)
    |> map(rewrite_entry)
    |> zip_write(out_path)
```

### Phase 1 persistent associative maps

- `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- implemented as an opaque host-backed runtime wrapper (no map syntax added)
- persistent semantics from Genia perspective (`map_put`/`map_remove` return new map values)

## Autoloaded stdlib highlights

- list helpers: `list`, `first`, `rest`, `append`, `length`, `reverse`, `reduce`, `map`, `filter`, `nth`, `take`, `drop`, `range`, ...
- fn helpers: `apply`, `compose`
- math helpers: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk-ish helpers: `awkify`, `awk_filter`, `awk_map`, `awk_count`, `fields`
- agents: `agent`, `agent_send`, `agent_get`, `agent_state`, `agent_alive?`

## Not implemented yet

- map literals/patterns
- general host interop / FFI
- module/import syntax
- member access / indexing syntax
- generalized flow semantics (lazy sequences, multi-output stages, backpressure, cancellation)
- full Flow system (stages/sinks/backpressure/multi-port pipelines)
- language-level scheduler/event loop for simulations

For stricter implementation details and invariants, see:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
