# Genia — Current Language State (Main Branch)

This file describes what is **actually implemented now** in the Python runtime.

## 1) Execution model

- programs are expression sequences
- parser AST stays close to surface syntax, then lowers into a tiny Core IR before evaluation
- top-level assignment is supported (`name = expr`)
- blocks evaluate expressions in order and return the last value
- no statement/declaration split at runtime level
- CLI entry points support three execution modes:
  - file mode: `genia path/to/file.genia`
  - command mode: `genia -c "expr_or_program_source"`
  - REPL mode: `genia` (no file/command arguments)
- in file/command mode, trailing host CLI arguments are exposed to programs as `argv()` (list of strings)
  - command mode accepts both bare positionals (`a`) and option-like args (`--pretty`) as trailing args
- after file/command source evaluation, runtime entrypoint convention is:
  - if `main/1` exists, call `main(argv())`
  - else if `main/0` exists, call `main()`
  - else keep existing result behavior (no implicit call)

## 2) Implemented syntax and expression forms

- literals: number, string (single/double quoted + triple-quoted multiline), boolean, `nil`, `none`
- variables
- function calls
- unary operators: `-`, `!`
- binary operators: `+ - * / % < <= > >= == != && ||`
- pipeline operator: `|>`
- block expressions: `{ ... }`
- list literals: `[a, b, c]`
- map literals: `{ key: value }` with identifier/string keys (`name: 1` sugar for `"name": 1`)
- module import: `import mod`, `import mod as alias`
- list spread in literals: `[..xs]`, `[1, ..xs, 2]`
- call spread: `f(..xs)`
- lambdas: `(x) -> x + 1`
- varargs lambdas: `(..xs) -> xs`, `(a, ..rest) -> rest`

Pipeline (Phase 2) rewrite model:

- `x |> f` rewrites to `f(x)`
- `x |> f(y)` rewrites to `f(y, x)` (left value appended as the last argument)
- `x |> expr` rewrites to `expr(x)` when `expr` is valid in ordinary call-callee position
  - example: `record |> "name"` rewrites to `"name"(record)`
- left associative: `a |> f |> g` rewrites to `g(f(a))`
- rewrite is performed in the AST→Core IR lowering pass (not by runtime special-casing)
- no stream runtime semantics are added in this phase

## 3) Functions and dispatch

- named functions are first-class values
- multiple definitions by arity shape are allowed
- varargs named functions are supported (`f(a, ..rest) = ...`)
- named function definitions may include an optional leading docstring string literal after `=`
  - example:
    ```genia
    inc(x) = """
    # inc

    Increment by one.
    """ x + 1
    ```
  - docstrings are metadata, not runtime body expressions
  - for multi-clause named functions: zero docstrings = undocumented; one docstring total = valid; repeated identical docstrings = valid; conflicting docstrings raise a clear `TypeError`
- resolution behavior:
  - exact fixed arity beats varargs
  - if multiple varargs candidates match and neither is more specific, runtime raises `TypeError("Ambiguous function resolution")`
- slash named accessor (phase 1):
  - `lhs/name` uses narrow named access when RHS is a bare identifier
  - supported LHS runtime kinds: module values, map values
  - map missing key => `nil`
  - module missing export => clear error
  - this does not add general member/index access
- callable data (phase 1):
  - maps are callable lookup values:
    - `m(key)` returns stored value or `nil`
    - `m(key, default)` returns stored value when key exists, otherwise `default`
    - arity other than 1 or 2 raises `TypeError`
  - strings are callable map projectors:
    - `"key"(m)` returns `map_get(m, "key")` behavior (`value` or `nil`)
    - `"key"(m, default)` returns stored value when key exists, otherwise `default`
    - first argument must be map-like (runtime map value); non-map targets raise clear `TypeError`
    - arity other than 1 or 2 raises `TypeError`

## 4) Case expressions and pattern matching

Case arms support:

```genia
pattern -> result
pattern ? guard -> result
```

Implemented pattern types:

- literal patterns
- glob string patterns (`glob"..."`) for whole-string matching
- variable binding
- wildcard `_`
- tuple patterns
- list patterns
- map patterns (partial-by-default key matching)
- rest pattern `..name` / `.._` (list patterns only; final position only)
- duplicate binding semantics (same name must match equal value)
- multiline list pattern formatting is accepted (newlines inside `[...]` pattern shapes)

Map pattern semantics:

- key forms:
  - explicit: `{ name: n }`, `{ "name": n }`
  - shorthand binding: `{ name }` (identifier keys only; sugar for `{ name: name }`)
  - mixed forms are supported (`{ name, age: years }`)
- trailing commas are accepted (`{ name, age: years, }`)
- patterns are partial by default:
  - `{ name }` matches any map containing key `"name"`
  - multiple entries require all listed keys to be present
- missing keys fail the match
- duplicate binding names follow normal duplicate-binding equality semantics

Glob pattern semantics (Phase 1):

- valid in any pattern position accepted by function clauses / case arms
- matches only string values (non-string values fail to match)
- whole-string matching only (no substring mode)
- supported metacharacters:
  - `*` (zero or more chars)
  - `?` (exactly one char)
  - character classes: `[abc]`, `[a-z]`, `[!abc]`
- supported escaping inside glob text:
  - `\*`, `\?`, `\[`, `\]`, `\\`
- malformed character classes raise deterministic syntax errors

Case placement rules (enforced):

- allowed in function body
- allowed as final expression in block
- rejected in ordinary subexpressions / call args / non-final block positions

### Conditionals

- implemented via pattern matching in function definitions and case expressions
- no dedicated conditional keyword exists
- `decide` has been removed from the language

## 5) Builtins (runtime)

### Core I/O and utilities

- `log`, `print`, `input`, `stdin`, `help`
- `argv` (returns raw trailing CLI args as a list of strings)
- constants in global env: `pi`, `e`, `true`, `false`, `nil`

### CLI argument helpers (host-backed builtin layer)

- `cli_parse(args) -> [opts, positionals]`
- `cli_parse(args, spec) -> [opts, positionals]`
- `cli_flag?(opts, name) -> bool`
- `cli_option(opts, name) -> value_or_nil`
- `cli_option_or(opts, name, default) -> value`

Behavior:

- raw args are list-first data (`argv()`), intended for normal list pattern matching
- `cli_parse` returns a persistent map (`opts`) and remaining positional args list
- default parsing:
  - `--name` => boolean `true` unless followed by a non-option token (then `--name value`)
  - `--name=value` => string value
  - `-abc` => grouped short boolean flags
  - `-o value` => short option value when next token is non-option
  - `--` terminates option parsing
  - repeated keys are deterministic last-one-wins (`map_put` replacement semantics)
- `cli_parse(args, spec)` supports a minimal map-based spec:
  - `flags`: list of names forced to boolean behavior
  - `options`: list of names forced to value-taking behavior
  - `aliases`: map of alias name -> canonical name (string keys/values)
- grouped short options with spec raise clear `ValueError` for ambiguous mixes

### Program entrypoint convention (runtime, no syntax)

- `main` is a runtime convention, not parser syntax
- in file mode and `-c` command mode, `main/1` is preferred over `main/0`
- arity coercion is not performed by the entrypoint selector:
  - only exact `main/1` or exact `main/0` are auto-invoked
  - if neither exists, no entrypoint call is attempted

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
- module imports produce opaque module namespace values (`<module name>`)
- `map_new` returns an empty map
- `map_put` and `map_remove` are persistent (return a new map, do not mutate input map)
- `map_get` returns stored value or `nil` when key is missing
- `map_has?` returns `true`/`false`
- `map_count` returns entry count
- list keys are supported by stable structural key-freezing in runtime
- tuple keys are supported by the same runtime key-freezing strategy (runtime-level interop values)
- invalid map arguments and unsupported key types raise clear `TypeError`

### Primitive Option model (Phase 1, runtime-backed)

- option values:
  - `none` (distinct from `nil`)
  - `some(value)`
- option/query builtins:
  - `get?(key, target)`
  - `unwrap_or(default, opt)`
  - `is_some?(opt)`
  - `is_none?(opt)`

`get?` semantics:

- `get?(key, none) -> none`
- `get?(key, some(map)) -> get?(key, map)`
- `get?(key, map) -> some(value)` when key exists (including `value = nil`)
- `get?(key, map) -> none` when key is missing
- unsupported target types raise clear `TypeError`

Compatibility note:

- existing callable-data map/string-projector behavior is unchanged:
  - `m(key)`, `m(key, default)`
  - `"key"(m)`, `"key"(m, default)`

### String builtins

- `byte_length`, `is_empty`, `concat`
- `contains`, `starts_with`, `ends_with`, `find`
- `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`
- `lower`, `upper`

### Bytes / JSON / ZIP bridge builtins (Phase 1, host-backed)

- `utf8_decode(bytes) -> string`
- `utf8_encode(string) -> bytes`
- `json_parse(string) -> value`
- `json_pretty(value) -> string`
- `zip_entries(path) -> list of zip entries`
- `zip_write(entries, path) -> path` (also accepts `(path, entries)` for pipeline ergonomics)
- `entry_name(entry) -> string`
- `entry_bytes(entry) -> bytes`
- `set_entry_bytes(entry, new_bytes) -> entry`
- `update_entry_bytes(entry, f) -> entry`
- `entry_json(entry) -> bool`

Behavior:

- bytes are opaque runtime wrappers (`<bytes N>`)
- zip entries are opaque runtime wrappers (`<zip-entry ...>`) containing entry name + bytes payload
- `zip_entries` currently returns a strict list (Phase 1) and preserves entry order
- JSON objects from `json_parse` are represented as persistent runtime map values (`map_*` bridge type)
- `json_pretty` currently emits deterministic pretty JSON with 2-space indentation and sorted object keys
- this is a minimal host-backed bridge and is **not** the full flow system

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

- list: `list`, `first`, `rest`, `empty?`, `nil?`, `append`, `length`, `reverse`, `reduce`, `map`, `filter`, `count`, `any?`, `nth`, `take`, `drop`, `range`
- fn: `apply`, `compose`
- math: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk: `fields`, `awkify`, `awk_filter`, `awk_map`, `awk_count`
- agent: `agent`, `agent_send`, `agent_get`, `agent_state`, `agent_alive?`
- prelude public functions now carry Markdown docstrings intended for `help(...)` teaching output

## 7) Optimization behavior

Implemented optimizations:

- self tail-call elimination via trampoline for tail-position calls
- specialized nth-style list traversal rewrite to `IrListTraversalLoop` for a narrow recognized recursion shape

Core IR shape currently includes:

- program items: expression statement, assignment, named function definition
- expressions: literal, variable, call, unary, binary, lambda, block, list, map, spread, case
- patterns: wildcard, variable, literal, tuple, list, map, final rest
- function docstrings are carried as metadata on named-function definitions (not runtime expressions)

## 8) Debug/runtime tooling

- parser/IR nodes carry source spans (filename + line/column ranges)
- `run_debug_stdio(...)` exposes debugger protocol endpoints used by the VS Code extension
- `help(name)` displays named-function metadata when available:
  - function signature header (`name/shape`, shapes include `+` for varargs)
  - source location (`Defined at file:line`) when available
  - Markdown-aware docstring rendering (headings, bullet lists, inline code, fenced code blocks, paragraph spacing)
  - docstring normalization (trim outer blank lines, dedent indentation, optional triple-quote wrapper stripping, collapse excessive blank lines)
  - undocumented fallback message (`No documentation available.`)

## 9) Explicitly not implemented (current)

- general host interop / FFI layer
- general member access syntax
- index syntax
- generalized flow runtime semantics (lazy sequences, multi-output stages, backpressure, cancellation)
- full Flow system (stages/sinks/backpressure/multi-port pipelines)
- language-level scheduler/selective receive/timeouts (concurrency remains host-primitive based)

## 10) Example demos shipped in-repo

- `examples/tic-tac-toe.genia`: interactive text game example
- `examples/ants.genia`: first minimal ants-style stochastic grid simulation demo

`examples/ants.genia` intentionally uses only currently implemented features:

- host-backed map builtins for persistent world updates
- `rand_int` for random movement choice
- recursion for stepping
- `sleep` for blocking frame delay
- text rendering via `print`

It is intentionally minimal and single-ant first. It is **not** actor-based, does **not** add a scheduler, and does **not** introduce new language syntax.
