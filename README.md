# Genia

Genia is a small, functional-first, expression-oriented language prototype.

This repository currently provides:

- a parser + evaluator (`src/genia/interpreter.py`)
- a tiny Core IR + AST→IR lowering pass used before evaluation
- a REPL and file runner (`python3 -m genia.interpreter`)
- host-backed concurrency primitives with public prelude-backed process helpers (`spawn`, `send`, `process_alive?`)
- host-backed refs with public prelude-backed helpers (`ref`, `ref_get`, `ref_set`, `ref_update`)
- raw host-backed `argv()` plus prelude-backed CLI parsing helpers (`cli_parse`, `cli_flag?`, `cli_option`, `cli_option_or`)
- simulation primitives (`rand`, `rand_int`, `sleep`)
- autoloaded prelude libraries (flow helpers, lists, map/ref/process/io helpers, option/string helpers, math helpers, awk helpers, fn helpers, evaluator helpers, cells)
  - bundled `.genia` prelude sources are loaded from package resources, so installed `genia` tools can use the same stdlib as repo execution
  - autoloaded function names can also be referenced as higher-order function values, not only called directly
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

- Core values: Number, Symbol, String, Boolean, `nil`, Pair, `none` / `none(reason)` / `none(reason, context)` / `some(value)`, List, Map
- Function / module values: Function, Module
- Callable behaviors:
  - functions/lambdas are callable values
  - maps are callable lookup values
  - strings can act as callable map projectors
- Runtime capability values:
  - `stdout`
  - `stderr`
  - MetaEnv
  - Flow (runtime Phase 1 is implemented)
  - Ref
  - Process handle
  - Bytes wrapper
  - Zip entry wrapper

Current consistency note:

- maybe/absence behavior is not fully unified yet
- map lookup via `map_get`, callable map/string lookup, and slash map access are retained but docs-deprecated legacy non-Option paths; `cli_option` remains a legacy-retained non-Option CLI helper
- canonical access/search APIs now use the absence family `none` / `none(reason)` / `none(reason, context)` and `some(value)`:
  - `get`
  - `first`
  - `last`
  - `nth`
  - string `find`
  - list predicate-search helper `find_opt`
- compatibility aliases retained:
  - `get?`
  - `first_opt`
  - `nth_opt`
- preferred modern absence style in new code:
  - `get`, `first`, `last`, `nth`, string `find`, `find_opt`
- maybe-flow helpers such as `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, and `then_find` preserve structured absence unchanged
- public Option, String, Map, Ref, Process, and sink helper names are now prelude-backed wrappers over host-backed runtime primitives, so they participate in `help("name")` doc output without changing runtime behavior
- public Flow helper names `lines`, `rules`, `each`, `collect`, and `run` are also prelude-backed wrappers over the host Flow runtime
- `help()` now points users toward the public prelude-backed stdlib surface, while raw host-backed runtime names remain intentionally generic
- REPL/debug output now renders structured absence with visible context metadata, for example `none(missing_key, {key: "name"})`
- `some(pattern)`, `none(reason)`, and `none(reason, context)` are supported in pattern matching for Option values
- new `?`-suffixed APIs are boolean-returning; `get?` remains the current compatibility exception and `get` is the preferred maybe-aware lookup name
- Flow, MetaEnv, Ref, and Process handles are runtime values, but they are not plain data in the same sense as numbers/lists/maps

### Programs as Data

Genia has a minimal `quote(expr)` special form for syntax-as-data.

```genia
quote(x)
quote([a, b, c])
quote(1 + 2)
```

- `quote(x)` returns a symbol distinct from the string `"x"`
- `quote([a, b, c])` returns a pair chain of symbols ending in `nil`
- `quote(1 + 2)` returns `(app + 1 2)`, not `3`
- quoted source applications use `(app operator operand1 operand2 ...)`
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
- `delay(expr)` creates a delayed promise value; `force(x)` forces promises and returns non-promises unchanged
- `quasiquote(expr)` constructs quoted data with selective evaluation via `unquote(...)`
  - `unquote_splicing(...)` is supported in quasiquoted list contexts
- quoted/quasiquoted data can now be inspected with the syntax helper prelude
  - `self_evaluating?`, `symbol_expr?`, `quoted_expr?`, `assignment_expr?`, `lambda_expr?`, `application_expr?`, `block_expr?`, `match_expr?`
  - selectors include `text_of_quotation`, `assignment_name`, `assignment_value`, `lambda_params`, `lambda_body`, `operator`, `operands`, `block_expressions`, `match_branches`, `branch_pattern`, `branch_has_guard?`, `branch_guard`, `branch_body`
- Genia also now includes a minimal phase-1 metacircular evaluator over quoted expressions
  - environment helpers: `empty_env`, `lookup`, `define`, `set`, `extend`
  - evaluator entry: `eval(expr, env)`
  - `apply(proc, args)` still applies ordinary callables and now also applies metacircular compound procedures and metacircular matcher procedures
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
- `name = expr` also works as lexical assignment in blocks
  - it rebinds the nearest existing lexical name when present
  - otherwise it defines a name in the current scope
  - function parameters are assignable
  - assignment is limited to simple names in this phase
- calls in tail position are guaranteed to run in constant stack space
- promises are separate from Flow
  - promises are memoized delayed ordinary values
  - Flow remains the single-use pipeline/runtime stream model
- stdlib streams are implemented on top of pairs + promises
  - `stream_cons`, `stream_head`, `stream_tail`, `stream_map`, `stream_take`, `stream_filter`
  - streams are pure delayed data and remain separate from Flow

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
- map slash access is still supported for compatibility, but new code should prefer canonical maybe-aware lookup:

```genia
get("name", person)
```

### Pipeline operator (Phase 1)

```genia
[1, 2, 3] |> map(inc)
```

- `x |> f` rewrites to `f(x)`
- `x |> f(y)` rewrites to `f(y, x)` (append piped value as final argument)
- left-associative chaining is supported (`a |> f |> g`)
- multiline formatting around `|>` is supported:
  ```genia
  value
    |> f
    |> g
  ```
- rewrite occurs during AST→Core IR lowering (not as a special runtime node)
- this rewrite is unchanged even when working with Flow values; streaming behavior is runtime-level, not parser-level

### Flow runtime (Phase 1)

```genia
stdin |> lines |> take(2) |> each(print) |> run
```

- `stdin |> lines` creates a lazy, pull-based, single-use Flow
- Flow is a runtime value produced/consumed by flow builtins; it is not a separate syntax category
- public flow helpers from `std/prelude/flow.genia`: `lines`, `rules`, `each`, `collect`, `run`
- reusable pipeline stages are ordinary functions of shape `(flow) -> flow`
- `rules(..fns)` is a stateful rule-driven stage over any incoming Flow:
  - each rule runs as `(record, ctx)`
  - `ctx` starts as `{}` and persists across items
  - `rules()` is the identity stage
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
- public helpers from `std/prelude/io.genia`: `write`, `writeln`, `flush`
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

- public helpers from `std/prelude/process.genia`: `spawn`, `send`, `process_alive?`
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

- direct runtime names: `log`, `print`, `input`, `stdin`, `stdout`, `stderr`, `help`
- public flow helpers from `std/prelude/flow.genia`: `lines`, `rules`, `each`, `collect`, `run`
- public sink helpers from `std/prelude/io.genia`: `write`, `writeln`, `flush`
- special form: `quote(expr)`
- pair builtins: `cons`, `car`, `cdr`, `pair?`, `null?`
- `help(name)` prints named-function/prelude metadata when available (`name/shape`, source if available, rendered docstring, or undocumented fallback)
- `help()` prints a compact overview of the public prelude-backed stdlib families and canonical helpers
- `help("name")` can autoload registered prelude helpers before rendering their docstrings
- `help("name")` for raw host-backed names prints a generic bridge note rather than a separate host-specific doc registry
- stdlib prelude helpers include Markdown docstrings for learn-by-inspection via `help("name")`
- constants: `pi`, `e`, `true`, `false`, `nil`
- option runtime + public helpers:
  - `none` remains a runtime literal/value
  - public helpers from `std/prelude/option.genia`: `some`, `get`, `get?`, `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`, `unwrap_or`, `is_some?`, `is_none?`, `some?`, `none?`, `or_else`, `or_else_with`, `absence_reason`, `absence_context`
- canonical maybe-returning list/search helpers: `first`, `last`, `nth`, `find` (string search), `find_opt` (predicate search)
- compatibility aliases: `first_opt`, `nth_opt`
- flow runtime (Phase 1): `lines`, flow-aware `map`/`filter`, `take`, `rules`, `each`, `collect`, `run`, plus prelude `head` aliases and rule helper constructors `rule_skip`, `rule_emit`, `rule_emit_many`, `rule_set`, `rule_ctx`, `rule_halt`, `rule_step`

### CLI args / options (runtime layer)

- `argv()` is the raw host-backed CLI primitive and exposes trailing CLI args as a plain list of strings
- public CLI helpers now live in `std/prelude/cli.genia`
- `cli_parse(args)` and `cli_parse(args, spec)` return `[opts_map, positionals]`
- `cli_flag?(opts, name)`, `cli_option(opts, name)`, `cli_option_or(opts, name, default)` help read options cleanly
- host-side CLI support is intentionally small: raw `argv()`, spec normalization/validation, token character decomposition, and deterministic CLI-specific error raising
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

- public helpers from `std/prelude/ref.genia`: `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`

### Strings

- public helpers from `std/prelude/string.genia`: `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`
- `find`, `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`, `lower`, `upper`
- `parse_int`
- these remain thin wrappers over the same host-backed string runtime behavior

Examples:

```genia
parse_int("42")
parse_int("ff", 16)
```

- base 10 by default
- explicit base supported in `2..36`
- surrounding whitespace is ignored
- invalid text raises `ValueError`

### Concurrency

- public helpers from `std/prelude/process.genia`: `spawn`, `send`, `process_alive?`

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

- public helpers from `std/prelude/map.genia`: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- implemented as an opaque host-backed runtime wrapper (no map syntax added)
- persistent semantics from Genia perspective (`map_put`/`map_remove` return new map values)

## Autoloaded stdlib highlights

- list helpers: `list`, `first`, `rest`, `append`, `length`, `reverse`, `reduce`, `map`, `filter`, `nth`, `take`, `drop`, `range`, ...
- canonical maybe-returning list/search helpers: `first`, `last`, `nth`, `find` (string search), `find_opt` (predicate search)
- compatibility aliases: `first_opt`, `nth_opt`
- fn helpers: `apply`, `compose`
- map helpers: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- ref helpers: `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`
- process helpers: `spawn`, `send`, `process_alive?`
- sink helpers: `write`, `writeln`, `flush`
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
