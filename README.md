# Genia

Genia is a small, functional-first, expression-oriented language prototype.

This repository currently provides:

- a parser + evaluator (`src/genia/interpreter.py`)
- a tiny Core IR + AST→IR lowering pass used before evaluation
- a REPL and file runner (`python3 -m genia.interpreter`)
- host-backed concurrency primitives (`spawn`, `send`, `process_alive?`)
- refs (`ref`, `ref_get`, `ref_set`, `ref_update`)
- list-first CLI args + parsing helpers (`argv`, `cli_parse`, `cli_flag?`, `cli_option`, `cli_option_or`)
- simulation primitives (`rand`, `rand_int`, `sleep`)
- autoloaded prelude libraries (lists, math helpers, awk helpers, fn helpers, cells)
  - bundled `.genia` prelude sources are loaded from package resources, so installed `genia` tools can use the same stdlib as repo execution
- debug-stdio adapter support for editor integration
- runnable demos under `examples/` (including `tic-tac-toe.genia` and `ants.genia`)
- proper tail-call optimization for calls in tail position

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

Run a pipeline stage expression:

```bash
printf 'a\nb\n' | genia -p 'head(1) |> each(print)'
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

### Runtime value categories

- Core values: Number, Symbol, String, Boolean, `nil`, Pair, `none` / `some(value)`, List, Map
- Function / module values: Function, Module
- Callable behaviors:
  - functions/lambdas are callable values
  - maps are callable lookup values
  - strings can act as callable map projectors
- Runtime capability values:
  - `stdout`
  - `stderr`
  - Flow (runtime Phase 1 is implemented)
  - Ref
  - Process handle
  - Bytes wrapper
  - Zip entry wrapper

Current consistency note:

- maybe/absence behavior is not fully unified yet
- map lookup, callable map/string lookup, slash map access, `cli_option`, string `find`, `nth`, and legacy `first` still use non-Option behavior
- `get?`, `first_opt`, `last`, and `find_opt` return `none` / `some(value)`
- `some(pattern)` is supported in pattern matching for Option values
- new `?`-suffixed APIs are boolean-returning; `get?` remains the current compatibility exception
- Flow and Ref are runtime values, but they are not plain data in the same sense as numbers/lists/maps

### Programs as Data

Genia has a minimal `quote(expr)` special form for syntax-as-data.

```genia
quote(x)
quote([a, b, c])
quote(1 + 2)
```

- `quote(x)` returns a symbol distinct from the string `"x"`
- `quote([a, b, c])` returns a pair chain of symbols ending in `nil`
- `quote(1 + 2)` returns `(+ 1 2)`, not `3`
- there is no `'x` shorthand in this phase

### Pairs and Lists

Genia also has immutable pairs for SICP-style data.

```genia
cons(1, 2)
cons(1, cons(2, nil))
```

- `car` and `cdr` access pair fields
- `pair?(x)` checks for pairs
- `null?(x)` checks for `nil`
- pair-built lists end in `nil`
- ordinary list literals remain separate list values in this phase

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
- calls in tail position are guaranteed to run in constant stack space

### Pattern matching

```genia
head(xs) =
  [x, .._] -> x
```

Supported pattern forms:

- literals (`0`, `"ok"`, `true`, `nil`)
- option patterns (`none`, `some(pattern)`)
- glob string patterns (`glob"..."`) for whole-string string matching
- variable bindings
- wildcard `_`
- tuple patterns (`(a, b)`)
- list patterns (`[x, ..rest]`)
- map patterns (`{name}`, `{name: n}`, `{"name": n}`; partial by default)
- map pattern shorthand is identifier-only (`{"name"}` shorthand is invalid; use `{"name": n}`)
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

### Map literals

```genia
person = { name: "Matthew", age: 42 }
point = { "x": 10, "y": 20 }
empty = {}
```

- identifier keys in literals are sugar for string keys
- trailing commas are supported
- duplicate keys are deterministic last-one-wins


### Modules (Phase 1)

```genia
import math
import math as m

[math/pi, m/inc(2)]
```

- `import mod` binds a module value to `mod`
- `import mod as alias` binds the same module value to `alias`
- module imports are cached by module name (`loaded_modules`) so duplicate imports are not re-evaluated
- module exports are accessed with narrow slash access (`mod/name`)
- modules are immutable runtime namespace values (distinct from maps)

### Named slash access (`/`)

```genia
person = { name: "Matthew", age: 42 }
[person/name, person/age, person/middle]
```

- map named access returns the value when present
- missing map keys return `nil`
- module named access returns exported bindings
- missing module exports raise a clear error
- `/` access is narrow: only `lhs/name` (bare identifier RHS), not general member/index access

### Pipeline operator (Phase 1)

```genia
[1, 2, 3] |> map(inc)
```

- `x |> f` rewrites to `f(x)`
- `x |> f(y)` rewrites to `f(y, x)` (append piped value as final argument)
- left-associative chaining is supported (`a |> f |> g`)
- rewrite occurs during AST→Core IR lowering (not as a special runtime node)
- this rewrite is unchanged even when working with Flow values; streaming behavior is runtime-level, not parser-level

### Flow runtime (Phase 1)

```genia
stdin |> lines |> take(2) |> each(print) |> run
```

- `stdin |> lines` creates a lazy, pull-based, single-use Flow
- Flow is a runtime value produced/consumed by flow builtins; it is not a separate syntax category
- reusable pipeline stages are ordinary functions of shape `(flow) -> flow`
- `take` stops upstream pulling as soon as the limit is satisfied
- `collect(flow)` materializes reusable data, while `run(flow)` drives effects to completion
- `stdin()` remains separate and returns a cached list of full stdin lines for non-stream use
- `-p` / `--pipe` wrap a stage expression as `stdin |> lines |> <expr> |> run` for ergonomic Unix pipeline use
- `-p` expects a stage expression only; omit explicit `stdin` and `run`
- no `pipe(...)` helper function exists in this phase

### Output sinks (Phase 1)

```genia
write(stdout, "a")
writeln(stderr, "oops")
flush(stdout)
```

- `stdout` and `stderr` are first-class host-backed sink values
- `write(sink, value)` writes display-formatted output with no newline
- `writeln(sink, value)` writes display-formatted output with a trailing newline
- `flush(sink)` flushes a sink and returns `nil`
- `print(...)` writes to `stdout`, and `log(...)` writes to `stderr`
- `input()` remains independent of `stdin`
- broken pipe on `stdout` output in Unix pipelines is treated as normal downstream termination

### Concurrency and cells

```genia
counter = cell(0)
cell_send(counter, (n) -> n + 1)
cell_get(counter)
```

- `spawn(handler)` creates a host-thread worker with FIFO mailbox
- `send(process, message)` enqueues messages
- `process_alive?(process)` reports worker liveness
- prelude provides `cell`, `cell_with_state`, `cell_send`, `cell_get`, `cell_state`, `cell_failed?`, `cell_error`, `restart_cell`, `cell_status`, `cell_alive?`
- cells are fail-stop:
  - failed updates preserve last successful state
  - failed cells cache an error string and reject future `cell_send` / `cell_get`
  - `restart_cell(cell, new_state)` clears failure and discards queued pre-restart updates in this phase

## Builtins

### Core

- `log`, `print`, `input`, `stdin`, `stdout`, `stderr`, `write`, `writeln`, `flush`, `help`
- special form: `quote(expr)`
- pair builtins: `cons`, `car`, `cdr`, `pair?`, `null?`
- `help(name)` prints named function metadata (`name/shape`, source if available, rendered docstring, or undocumented fallback)
- stdlib prelude helpers include Markdown docstrings for learn-by-inspection via `help("name")`
- constants: `pi`, `e`, `true`, `false`, `nil`
- option builtins: `none`, `some`, `get?`, `unwrap_or`, `is_some?`, `is_none?`
- option-returning list helpers: `first_opt`, `last`, `find_opt`
- flow runtime (Phase 1): `lines`, flow-aware `map`/`filter`, `take`, `each`, `collect`, `run`, plus prelude `head` aliases over `take`

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

Pipe mode (`genia -p "..."` / `genia --pipe "..."`) is separate:

1. it wraps the provided stage expression as `stdin |> lines |> <expr> |> run`
2. it does not apply the `main` convention
3. it rejects explicit `stdin` and explicit `run` inside the provided stage expression

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
- Option-returning list helpers: `first_opt`, `last`, `find_opt`
- fn helpers: `apply`, `compose`
- math helpers: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk-ish helpers: `awkify`, `awk_filter`, `awk_map`, `awk_count`, `fields`
- cells: `cell`, `cell_with_state`, `cell_send`, `cell_get`, `cell_state`, `cell_failed?`, `cell_error`, `restart_cell`, `cell_status`, `cell_alive?`

## Not implemented yet

- quote sugar (`'x`)
- quasiquote / unquote
- macros
- general host interop / FFI
- general member access / indexing syntax
- full flow system beyond Phase 1 (async scheduling, multi-port stages, richer cancellation/backpressure controls)
- full Flow system (stages/sinks/backpressure/multi-port pipelines)
- language-level scheduler/event loop for simulations

For stricter implementation details and invariants, see:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
