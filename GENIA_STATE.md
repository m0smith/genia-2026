# Genia — Current Language State (Main Branch)

This file describes what is **actually implemented now** in the Python runtime.

## 1) Execution model

- programs are expression sequences
- parser AST stays close to surface syntax, then lowers into a tiny Core IR before evaluation
- assignment is supported at top level and in lexical scopes (`name = expr`)
- blocks evaluate expressions in order and return the last value
- no statement/declaration split at runtime level
- CLI entry points support three execution modes:
  - file mode: `genia path/to/file.genia`
  - command mode: `genia -c "expr_or_program_source"`
  - pipe mode: `genia -p "stage_expr"` / `genia --pipe "stage_expr"`
  - REPL mode: `genia` (no file/command arguments)
- in file/command/pipe mode, trailing host CLI arguments are exposed to programs as `argv()` (list of strings)
  - command mode accepts both bare positionals (`a`) and option-like args (`--pretty`) as trailing args
- pipe mode wraps the provided stage expression as `stdin |> lines |> <expr> |> run`
  - pipe mode expects a single stage expression, not a full standalone program
  - explicit `stdin` and explicit `run` are rejected in pipe mode with a clear error
- after file/command source evaluation, runtime entrypoint convention is:
  - if `main/1` exists, call `main(argv())`
  - else if `main/0` exists, call `main()`
  - else keep existing result behavior (no implicit call)
  - pipe mode bypasses the `main` convention and runs the wrapped flow directly

## 2) Implemented runtime value categories

This is the current runtime value model in `main`. It is intentionally descriptive, not a new static type system.

### Core values

- Number
- Promise
- Symbol
- String
- Boolean
- Nil (`nil`)
- Pair
- None / Some (`none`, `some(value)`)
- List
- Map
  - map literals and `map_*` builtins produce the same runtime map value family
  - map values are persistent and opaque at runtime (`<map N>`)

### Function / module values

- Function
  - named functions are first-class values
  - lambdas evaluate to ordinary callable runtime values
- Module
  - `import mod` / `import mod as alias` bind module namespace values
  - module values are distinct from maps and are accessed with narrow slash access (`mod/name`)

### Callable values / callable behaviors

- Function values are callable in the ordinary way
- Map values also have callable lookup behavior
  - `m(key)` -> stored value or `nil`
  - `m(key, default)` -> stored value when key exists, otherwise `default`
- String values can act as callable map projectors
  - `"key"(m)` -> map lookup behavior (`value` or `nil`)
  - `"key"(m, default)` -> stored value when key exists, otherwise `default`
- This callable layer is behavior-based, not a single unified nominal type
  - maps stay maps even when callable
  - strings stay strings even when used as projectors

### Runtime capability values

- Stdout / Stderr
  - `stdout` and `stderr` are first-class host-backed output sink values
  - they are opaque runtime capability values (`<stdout>`, `<stderr>`)
- MetaEnv
  - `empty_env()` returns a host-backed metacircular environment value (`<meta-env>`)
  - metacircular environments support lexical lookup/definition/rebinding for the phase-1 evaluator layer
- Flow
  - Flow is a real runtime value family (`<flow ...>`)
  - Flow runtime (Phase 1) is implemented
  - flows are lazy, pull-based, source-bound, and single-use
  - `|>` itself is still only call rewriting
- Ref
  - refs are synchronized host-backed runtime cells
  - `ref_get` / `ref_update` may block until a value is present
- Process
  - `spawn` returns a host-backed process handle value
- Bytes
  - `utf8_encode` and ZIP helpers produce opaque bytes wrapper values
- ZipEntry
  - `zip_entries` returns opaque zip entry wrapper values

### Current consistency notes

- Maybe/absence behavior is currently split across two models:
  - canonical APIs use the structured absence family `none` / `none(reason)` / `none(reason, context)` and `some(value)`
  - compatibility aliases remain where migration was staged (`get?`, `first_opt`, `nth_opt`)
  - some older `nil`-returning access paths are intentionally retained but now treated as docs-deprecated or legacy-retained migration surfaces (`map_get`, map slash access, callable map/string lookup, `cli_option`)
  - canonical maybe-aware access/search APIs use the absence family `none` / `none(reason)` / `none(reason, context)` and `some(value)` (`get`, `first`, `last`, `nth`, string `find`)
  - list predicate search remains helper-shaped as `find_opt`
- `nil` and `none` therefore overlap in purpose today, but they are different runtime values with different APIs/patterns.
- structured `none(...)` metadata is still absence metadata, not a separate control-flow family.
- `some(pattern)` and `none(...)` patterns are implemented for Option values in pattern matching.
- maybe flow is now available through helper functions such as `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, and `then_find`; the public helper names are prelude-backed wrappers over host-backed runtime primitives, and pipeline syntax itself remains ordinary AST→Core IR call rewriting.
- public Map/Ref/Process/IO helper names are also prelude-backed wrappers over host-backed runtime primitives, so `help("name")` and higher-order use follow the user-facing stdlib surface rather than raw host bindings.
- public Flow helper names `lines`, `rules`, `each`, `collect`, and `run` are also thin prelude wrappers in this phase; the underlying Flow behavior remains host-backed
- `help()` now serves as a small public-surface overview that points users toward autoloaded prelude families and canonical helpers such as `get`, `map_put`, `ref_update`, `spawn`, `write`, `parse_int`, `match_branches`, and `eval`
- naming discipline for current APIs:
  - new `?`-suffixed APIs are boolean-returning
  - maybe-returning APIs should use Option values without `?`
  - `get?` remains as the current compatibility exception
- Callable behavior currently crosses nominal value boundaries:
  - functions are callable as functions
  - maps are callable as lookup values
  - strings are callable as map projectors
- Flow, stdout/stderr, MetaEnv, Ref, and Process handles are runtime capability values, not plain data in quite the same sense as numbers, lists, or maps.
- lexical assignment currently does not protect builtin/root names from rebinding inside the same root environment; that is real current behavior.
- The current model is implemented and tested, but it is still piecemeal rather than a single fully unified type/protocol system.

## 3) Implemented syntax and expression forms

- literals: number, string (single/double quoted + triple-quoted multiline), boolean, `nil`, `none`
- quote special form: `quote(expr)`
- quasiquote special form: `quasiquote(expr)`
- delay special form: `delay(expr)`
- variables
- function calls
- unary operators: `-`, `!`
- binary operators: `+ - * / % < <= > >= == != && ||`
- pipeline operator: `|>`
- block expressions: `{ ... }`
- list literals: `[a, b, c]`
- map literals: `{ key: value }` with identifier/string keys (`name: 1` sugar for `"name": 1`)
- module import: `import mod`, `import mod as alias`
  - imports are cached by module name in `loaded_modules` (repeat imports/aliases reuse the same module instance)
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
- newline-separated pipeline formatting is accepted:
  - `x`
    `|> f`
    `|> g`
  - `x |> `
    `f |> g`
- rewrite is performed in the AST→Core IR lowering pass (not by runtime special-casing)
- no stream runtime semantics are added in this phase

## 4) Functions and dispatch

- named functions are first-class values
- multiple definitions by arity shape are allowed
- varargs named functions are supported (`f(a, ..rest) = ...`)
- lexical assignment uses the same `name = expr` surface syntax
  - if `name` already exists in the reachable lexical environment chain, assignment updates the nearest existing binding
  - otherwise assignment creates `name` in the current scope
  - blocks create lexical scopes
  - function parameters are ordinary assignable lexical bindings
  - closures capture lexical environments, so rebinding is visible across calls to the same closure
  - assignment is limited to simple names in this phase
  - invalid targets such as `(a + b) = 3` raise `SyntaxError("Assignment target must be a simple name")`
  - module evaluation uses its own module environment, so module top-level assignment does not rebind names in the importing root environment
- named function definitions may include an optional leading docstring string literal after `=`
  - example:
    ```genia
    inc(x) = """
    # inc

    Increment by one.
    """ x + 1
    ```
  - docstrings are metadata, not runtime body expressions
  - function bodies may still use the ordinary parenthesized case-expression style after a docstring
    - example:
      ```genia
      sign(n) = """
      # sign
      """ (
        0 -> 0 |
        _ -> 1
      )
      ```
  - for multi-clause named functions: zero docstrings = undocumented; one docstring total = valid; repeated identical docstrings = valid; conflicting docstrings raise a clear `TypeError`
- resolution behavior:
  - exact fixed arity beats varargs
  - if multiple varargs candidates match and neither is more specific, runtime raises `TypeError("Ambiguous function resolution")`
- slash named accessor (phase 1):
  - `lhs/name` uses narrow named access when RHS is a bare identifier
  - supported LHS runtime kinds: module values, map values
  - map missing key => `nil`
  - module missing export => clear error
  - non-identifier RHS (for example `lhs/(1 + 2)`) raises a clear `TypeError`
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

## 4.1) Symbols and quote

- Symbol is a real runtime value family
  - symbols are distinct from strings
  - symbols print as bare names (`x`, not `"x"`)
  - symbols compare by value/name
  - symbols are valid stable map keys
- `quote(expr)` is implemented as a special form
  - it does not evaluate `expr`
  - it converts syntax to runtime data
- current quote conversion rules:
  - identifier -> symbol
  - number / string / boolean / `nil` / `none` -> corresponding literal runtime value
  - list literal -> pair chain ending in `nil`
  - map literal -> runtime map with quoted keys and values
  - unary / binary / call forms -> tagged application pair chain `(app <operator> <arg1> ...)`
  - quoted identifier map keys become symbols; quoted string map keys stay strings
- there is no quote sugar (`'x`) in this phase
- `quasiquote(expr)` is implemented as a special form
  - it constructs the same runtime data shapes as `quote(expr)`
  - `unquote(expr)` evaluates `expr` and inserts the result at the nearest active quasiquote depth
  - nested `quasiquote(...)` forms are depth-sensitive; inner `unquote(...)` applies only to the nearest surrounding quasiquote
  - `unquote_splicing(expr)` is implemented only for quasiquoted list literal contexts
  - current `unquote_splicing` input families are:
    - ordinary list values
    - `nil`
    - nil-terminated pair chains
  - `unquote(...)` and `unquote_splicing(...)` outside quasiquote raise clear runtime errors
  - `quasiquote(unquote_splicing(...))` is invalid because splicing requires a quasiquoted list context
 - current quoted representation also supports these evaluator-facing tagged forms:
   - assignment -> `(assign <name-symbol> <value-expr>)`
   - lambda -> `(lambda <params-structure> <body-expr>)`
   - block -> `(block <expr1> <expr2> ...)`
   - match/case -> `(match (clause <pattern> <result>) ...)` or `(match (clause <pattern> <guard> <result>) ...)`
   - application -> `(app <operator> <operand1> <operand2> ...)`
 - ordinary quoted list/pair data remain plain pair/list data and are distinct from tagged quoted applications

## 4.2) Pairs

- Pair is a real immutable runtime value family
  - `cons(x, y)` creates a pair
  - `car(pair)` returns the head field
  - `cdr(pair)` returns the tail field
  - `pair?(x)` reports whether a value is a pair
  - `null?(x)` reports whether a value is exactly `nil`
- pair equality is structural
- SICP-style lists can be represented as pair chains ending in `nil`
- ordinary list literals remain separate List values in this phase

## 4.3) Promises

- Promise is a real runtime value family
  - `delay(expr)` is a special form that does not evaluate `expr` immediately
  - `delay(expr)` captures the lexical environment in the same way closures do
  - `force(value)` forces promise values and returns non-promise values unchanged
  - forcing is memoized after the first successful evaluation
  - if forcing raises, the promise remains unforced and a later `force(...)` retries evaluation
  - promises are ordinary delayed values and are separate from Flow
  - promises are reusable and memoized; flows are source-bound, single-use, and pipeline-oriented

## 4.4) Streams (stdlib)

- Streams are implemented as a stdlib/prelude layer, not as a runtime value family
  - a stream node is `cons(head, delay(tail_expr))`
  - in prelude practice, stream construction is exposed as `stream_cons(head, tail_fn)`
  - the tail is forced explicitly with `stream_tail(s)` / `force(cdr(s))`
- current public stream helpers are:
  - `stream_cons(head, tail_fn)`
  - `stream_head(s)`
  - `stream_tail(s)`
  - `stream_map(f, s)`
  - `stream_take(n, s)`
  - `stream_filter(pred, s)`
- `stream_take` materializes the requested prefix as an ordinary list
- streams are distinct from Flow:
  - streams are pure data built from Pair + Promise
  - Flow is the runtime pipeline/IO model and remains separate

## 4.5) Programs-as-data helper layer (stdlib)

- Genia now ships a minimal metacircular expression helper layer in `std/prelude/syntax.genia`
- these helpers operate on the same quoted/quasiquoted data representation produced by `quote(expr)` and `quasiquote(expr)`
- the host-backed substrate in this phase is intentionally small:
  - parser/lowering/quote/quasiquote runtime representation
  - symbol/self-evaluating runtime shape detection
  - metacircular pattern-lowering support used by the evaluator
- most user-facing quoted-form predicates, selectors, and branch/match structural helpers now live in prelude/Genia code
- current public helpers are:
  - predicates:
    - `self_evaluating?`
    - `symbol_expr?`
    - `tagged_list?`
    - `quoted_expr?`
    - `quasiquoted_expr?`
    - `assignment_expr?`
    - `lambda_expr?`
    - `application_expr?`
    - `block_expr?`
    - `match_expr?`
  - selectors:
    - `text_of_quotation`
    - `assignment_name`
    - `assignment_value`
    - `lambda_params`
    - `lambda_body`
    - `operator`
    - `operands`
    - `block_expressions`
  - match selectors:
    - `match_branches`
    - `branch_pattern`
    - `branch_has_guard?`
    - `branch_guard`
    - `branch_body`
- current supported expression families in the helper layer are:
  - self-evaluating literals
  - symbol/variable expressions
  - quote / quasiquote forms
  - assignments
  - lambdas
  - applications
  - blocks
  - match/case expressions
- quoted source applications are now represented and detected with the stable `(app ...)` tag
- `operands(expr)` returns the operand tail of `(app ...)` as a pair-chain sequence of operand expressions
- `match_branches(expr)` returns the branch tail of `(match ...)` as a pair-chain sequence of quoted branches
- `branch_guard(branch)` raises a clear `TypeError` when used on an unguarded branch

## 4.6) Metacircular evaluator (stdlib)

- Genia now ships a minimal metacircular evaluator layer in `std/prelude/eval.genia`
- the host-backed substrate in this phase remains:
  - metacircular environment values and lexical mutation support
  - metacircular pattern lowering/matching support
  - ordinary evaluator/runtime substrate and `apply` fallback machinery
- evaluator dispatch and most user-facing semantic glue live in prelude/Genia code
- current public evaluator/environment names are:
  - `empty_env`
  - `lookup`
  - `define`
  - `set`
  - `extend`
  - `eval`
  - `apply` (extended in `std/prelude/fn.genia` to handle metacircular compound procedures as well as ordinary callables)
- `eval(expr, env)` currently supports these quoted expression families:
  - self-evaluating literals
  - symbol/variable expressions
  - quoted expressions
  - assignments
  - lambdas
  - match/case expressions
  - applications
  - blocks
- metacircular environments follow current lexical scoping rules:
  - `define` binds in the current frame
  - `set` rebinds the nearest existing lexical name or defines in the current frame when missing
  - `extend` creates a child lexical environment for lambda application
  - closures capture the defining metacircular environment
- metacircular compound procedures are represented as tagged pair data:
  - `(compound <params> <body> <env>)`
- metacircular matcher procedures are represented as tagged pair data:
  - `(matcher <match-expr> <env>)`
- current evaluator limitations:
  - `eval` is only defined for the supported expression families above
  - unsupported quoted forms raise a clear runtime error instead of silently expanding evaluator coverage

## 5) Case expressions and pattern matching

Case arms support:

```genia
pattern -> result
pattern ? guard -> result
```

Implemented pattern types:

- literal patterns
- glob string patterns (`glob"..."`) for whole-string matching
- option constructor patterns (`some(pattern)`)
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

## 6) Builtins (runtime)

### Core I/O and utilities

- direct runtime names: `log`, `print`, `input`, `stdin`, `stdout`, `stderr`, `help`
- public sink helpers are thin prelude wrappers in `std/prelude/io.genia`:
  - `write`
  - `writeln`
  - `flush`
- `argv` (returns raw trailing CLI args as a list of strings)
- constants in global env: `pi`, `e`, `true`, `false`, `nil`
- pair builtins: `cons`, `car`, `cdr`, `pair?`, `null?`

Output sink semantics:

- `write`, `writeln`, and `flush` are the canonical public sink helper names and carry Markdown docstrings for `help(...)`
- the underlying sink behavior remains host-backed and unchanged in this phase
- `write(sink, value)` writes display-formatted output without a trailing newline and returns `value`
- `writeln(sink, value)` writes display-formatted output with a trailing newline and returns `value`
- `flush(sink)` flushes the sink and returns `nil`
- `print(...)` writes to `stdout`
- `log(...)` writes to `stderr`
- `input()` remains interactive-only and does not consume the flow/stdin source path
- broken pipe on `stdout` output is treated as normal downstream termination in CLI/file/command execution (no Python traceback)
- broken pipe on `stderr` is handled best-effort and does not trigger recursive noisy failures

### Flow runtime (Phase 1)

- `stdin` is a lazy source value when used in pipelines (`stdin |> lines`)
  - `stdin |> lines` reads incrementally from the underlying source
  - `stdin()` still materializes and caches the full remaining input as a list for compatibility
- public flow helpers are thin prelude wrappers in `std/prelude/flow.genia`:
  - `lines`
  - `rules`
  - `each`
  - `collect`
  - `run`
  - `rules` orchestration, defaulting, and contract validation now primarily live in prelude/Genia code
- flow transforms:
  - `lines(flow_or_source)`
  - `map(f, flow)` / `filter(pred, flow)` when second arg is a flow
  - `take(n, flow)` when second arg is a flow
  - `rules(..fns, flow)` / `flow |> rules(..fns)` as a stateful rule-driven transform
  - `head(flow)` and `head(n, flow)` via stdlib aliases over `take`
- flow sinks/materialization:
  - `each(f, flow)` (tap-style stage)
  - `collect(flow)` (materialize to list)
  - `run(flow)` (consume to completion)
- stdlib rule helpers (autoloaded from `std/prelude/fn.genia`):
  - `rule_skip()`
  - `rule_emit(x)`
  - `rule_emit_many(xs)`
  - `rule_set(record)`
  - `rule_ctx(ctx)`
  - `rule_halt()`
  - `rule_step(record, ctx, out)`

Flow semantics:

- lazy, pull-based, source-bound, single-use
- consuming a flow twice raises `RuntimeError("Flow has already been consumed")`
- `take` performs early termination (stops upstream pulling as soon as limit is reached, without over-pulling one extra item)
- host-backed Flow kernel remains intentionally small in this phase:
  - flow value creation and single-consumption enforcement
  - lazy pull-based iteration over upstream sources
  - source-bound stdin integration
  - sink/materialization boundaries such as `each`, `collect`, and `run`
- `rules` semantics:
  - each rule is called as `(record, ctx)`
  - running `ctx` starts as `{}` for the first input item and persists across later items
  - `none`, `none(reason)`, and `none(reason, context)` mean no effect
  - `some(result)` expects a map result with optional fields:
    - `emit` (default `[]`)
    - `record` (default current record unchanged)
    - `ctx` (default current ctx unchanged)
    - `halt` (default `false`)
  - emitted values become downstream flow items in rule order
  - `halt: true` stops later rules for the current input item only
  - `rules()` is the identity stage
  - contract violations raise `RuntimeError` messages prefixed with `invalid-rules-result:`
  - rule orchestration, defaulting of omitted fields, and most contract checking are implemented in `std/prelude/flow.genia` in this phase
- explicit CLI pipe mode is implemented:
  - `genia -p "<stage_expr>"` / `genia --pipe "<stage_expr>"`
  - wraps as `stdin |> lines |> <stage_expr> |> run`
  - no `pipe(...)` helper function exists in this phase

### CLI argument helpers (prelude-backed over raw argv + tiny host validation primitives)

- `cli_parse(args) -> [opts, positionals]`
- `cli_parse(args, spec) -> [opts, positionals]`
- `cli_flag?(opts, name) -> bool`
- `cli_option(opts, name) -> value_or_nil`
- `cli_option_or(opts, name, default) -> value`

Behavior:

- `argv()` remains the raw host-backed CLI primitive and returns list-first data intended for normal pattern matching
- public CLI helper names are thin prelude wrappers in `std/prelude/cli.genia`
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
- host-side CLI support is intentionally small in this phase:
  - raw `argv()`
  - spec normalization/validation
  - token-to-char decomposition
  - deterministic CLI-specific error raising
- the actual option-parsing walk now lives in prelude/Genia code

### Program entrypoint convention (runtime, no syntax)

- `main` is a runtime convention, not parser syntax
- in file mode and `-c` command mode, `main/1` is preferred over `main/0`
- arity coercion is not performed by the entrypoint selector:
  - only exact `main/1` or exact `main/0` are auto-invoked
  - if neither exists, no entrypoint call is attempted

### Refs

- public ref helpers are thin prelude wrappers in `std/prelude/ref.genia`
  - `ref([initial])`
  - `ref_get(ref)`
  - `ref_set(ref, value)`
  - `ref_is_set(ref)`
  - `ref_update(ref, updater)`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying ref behavior remains host-backed and unchanged in this phase

Behavior: refs are synchronized host objects; `ref_get` / `ref_update` block until value is set when created via `ref()`.

### Host-backed concurrency

- public process helpers are thin prelude wrappers in `std/prelude/process.genia`
  - `spawn(handler)`
  - `send(process, message)`
  - `process_alive?(process)`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying process behavior remains host-backed and unchanged in this phase

Behavior:

- each process has FIFO mailbox
- one handler invocation at a time per process
- implemented with host threads

### Cell helpers (Phase 1, runtime-backed fail-stop)

- public prelude helpers:
  - `cell(initial)`
  - `cell_with_state(state_ref)`
  - `cell_send(cell, update_fn)`
  - `cell_get(cell)`
  - `cell_state(cell)`
  - `cell_failed?(cell)`
  - `cell_error(cell)`
  - `restart_cell(cell, new_state)`
  - `cell_status(cell)`
  - `cell_alive?(cell)`

Behavior:

- cells process queued updates asynchronously and serialize them one at a time
- successful updates replace cell state in order
- failed updates do not change state
- on update failure:
  - the cell caches an error string
  - `cell_status(cell)` becomes `"failed"`
  - `cell_failed?(cell)` becomes `true`
  - `cell_error(cell)` returns `some(error_string)`
  - later queued updates are discarded
  - future `cell_send` and `cell_get` raise `RuntimeError`
- `cell_state(cell)` is an alias for `cell_get(cell)`
- `restart_cell(cell, new_state)`:
  - replaces state with `new_state`
  - clears cached failure/error
  - marks the cell ready again
  - discards queued pre-restart updates in this phase
- nested `cell_send` calls made during an update are staged and are committed only if that update succeeds

### Host-backed persistent associative maps (Phase 1 bridge)

- public map helpers are thin prelude wrappers in `std/prelude/map.genia`
  - `map_new()`
  - `map_get(map, key)`
  - `map_put(map, key, value)`
  - `map_has?(map, key)`
  - `map_remove(map, key)`
  - `map_count(map)`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying map behavior remains host-backed and unchanged in this phase

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

### Primitive Option model (Phase 3 canonical access surface on runtime-backed values)

- option values:
  - `none` (distinct from `nil`)
  - `none(reason)`
  - `none(reason, context)`
  - `some(value)`
- public option helpers are thin prelude wrappers in `std/prelude/option.genia`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying runtime behavior remains host-backed and unchanged in this phase
  - `none` remains a runtime literal/value, not a prelude wrapper
- option/query helpers:
  - `get(key, target)`
  - `get?(key, target)`
  - `unwrap_or(default, opt)`
  - `is_some?(opt)` / `some?(opt)`
  - `is_none?(opt)` / `none?(opt)`
  - `or_else(opt, fallback)`
  - `or_else_with(opt, thunk)`
  - `absence_reason(opt)`
  - `absence_context(opt)`
- maybe-flow helpers:
  - `map_some(f, opt)`
  - `flat_map_some(f, opt)`
  - `then_get(key, target)`
  - `then_first(target)`
  - `then_nth(index, target)`
  - `then_find(needle, target)`
- option-returning stdlib helpers:
  - `first(list)`
  - `first_opt(list)` (compatibility alias)
  - `last(list)`
  - `find(string, needle)`
  - `find_opt(predicate, list)`
  - `nth(index, list)`
  - `nth_opt(index, list)` (compatibility alias)

Absence semantics:

- `some(value)` means present.
- `none`, `none(reason)`, and `none(reason, context)` are one absence family.
- reason/context metadata does not create a new success/failure category.
- absence is not the same as a runtime error.
- helpers treat all `none...` forms as absence.

`get?` semantics:

- `get(key, target)` is the canonical maybe-aware lookup helper in this phase
- `get?(key, target)` remains as a compatibility alias with the same runtime behavior
- `get?(key, none) -> none`
- `get?(key, none(reason)) -> none(reason)`
- `get?(key, none(reason, context)) -> none(reason, context)`
- `get?(key, some(map)) -> get?(key, map)`
- `get?(key, map) -> some(value)` when key exists (including `value = nil`)
- `get?(key, map) -> none(missing_key, { key: key })` when key is missing
- unsupported target types raise clear `TypeError`

Maybe-flow helper semantics:

- `map_some(f, some(x)) -> some(f(x))`
- `map_some(f, none(...)) -> none(...)` unchanged
- `flat_map_some(f, some(x)) -> f(x)` and requires `f(x)` to be an Option value
- `flat_map_some(f, none(...)) -> none(...)` unchanged
- `then_get(key, target)` is a thin maybe-aware chaining helper:
  - `then_get(key, some(map)) -> get(key, map)`
  - `then_get(key, none(...)) -> none(...)` unchanged
- `then_first(target)` is a thin maybe-aware chaining helper over `first`
- `then_nth(index, target)` is a thin maybe-aware chaining helper over `nth`
- `then_find(needle, target)` is a thin maybe-aware chaining helper over string `find`
- `or_else_with(opt, thunk)` is recovery/defaulting:
  - returns wrapped value for `some(value)`
  - calls `thunk()` only for `none...`
- `or_else(opt, fallback)` and `or_else_with(opt, thunk)` accept both direct style and pipeline-friendly style in this phase:
  - `or_else(some(3), 0) -> 3`
  - `some(3) |> or_else(0) -> 3`
  - `or_else_with(none(empty_list), () -> 0) -> 0`
  - `none(empty_list) |> or_else_with(() -> 0) -> 0`
- these helpers preserve structured absence reason/context during propagation unless they are explicitly recovery/defaulting helpers

Developer-facing rendering and introspection:

- REPL result display and debug-oriented formatting preserve structured absence syntax directly:
  - `none`
  - `none(empty_list)`
  - `none(index_out_of_bounds, {index: 8, length: 2})`
  - `none(missing_key, {key: "name"})`
  - `some(3)`
  - `some(nil)`
- structured absence context is rendered structurally in debug/display output; it is no longer collapsed to `<map N>` in these tooling-facing paths
- `some?` / `none?` are the short predicate names; `is_some?` / `is_none?` remain supported aliases with the same runtime behavior
- `absence_reason(opt)` and `absence_context(opt)` are the canonical inspection helpers for structured absence metadata
- `nil` and `none` remain visibly distinct in tooling output:
  - `nil`
  - `none`
  - `some(nil)`

Pipeline note:

- pipeline semantics themselves are unchanged
- absence flow in pipelines comes from helper behavior such as `record |> get("a") |> then_get("b") |> then_get("c")`, not from a magical pipeline runtime
- safe-chaining helpers preserve the first structured `none(...)` unchanged:
  - `record |> get("user") |> then_get("address") |> then_get("zip")`
  - `data |> get("items") |> then_nth(0) |> then_get("name")`
  - `data |> get("users") |> then_first() |> then_get("email") |> or_else("unknown")`

Structured absence currently used in canonical access/search helpers:

- `first([]) -> none(empty_list)`
- `last([]) -> none(empty_list)`
- `find(string, needle) -> none(not_found, { needle: needle })` when missing
- `find_opt(pred, xs) -> none(no_match)` when no element matches
- `nth(i, xs) -> none(index_out_of_bounds, { index: i, length: n })` when out of range

Absence migration status:

| API | Status | Present result | Missing result | Notes |
| --- | --- | --- | --- | --- |
| `get` | canonical | `some(value)` | `none(missing_key, { key: key })` | preferred map lookup |
| `get?` | compatibility alias | `some(value)` | `none(missing_key, { key: key })` | retained naming exception |
| `first` | canonical | `some(value)` | `none(empty_list)` | list head access |
| `first_opt` | compatibility alias | `some(value)` | `none(empty_list)` | alias for `first` |
| `last` | canonical | `some(value)` | `none(empty_list)` | list tail access |
| `nth` | canonical | `some(value)` | `none(index_out_of_bounds, { ... })` | zero-based list indexing |
| `nth_opt` | compatibility alias | `some(value)` | `none(index_out_of_bounds, { ... })` | alias for `nth` |
| `find` | canonical string search | `some(index)` | `none(not_found, { needle: needle })` | string search only |
| `find_opt` | canonical predicate-search helper | `some(value)` | `none(no_match)` | list predicate search |
| `map_get` | deprecated-in-docs | raw value | `nil` | use `get` in new code |
| callable map lookup `m(key)` | deprecated-in-docs | raw value | `nil` | use `get` in new code |
| string projector lookup `"key"(m)` | deprecated-in-docs | raw value | `nil` | use `get` in new code |
| map slash access `m/name` | deprecated-in-docs | raw value | `nil` | keep for compatibility; prefer `get("name", m)` |
| `cli_option` | legacy retained | raw value | `nil` | no canonical maybe-aware CLI option helper yet |

Compatibility note:

- `nil` remains a normal runtime value; the migration is about missing-result APIs, not removing `nil`
- existing callable-data map/string-projector behavior is unchanged:
  - `m(key)`, `m(key, default)`
  - `"key"(m)`, `"key"(m, default)`
- compatibility aliases retained in this phase:
  - `get?` for `get`
  - `first_opt` for `first`
  - `nth_opt` for `nth`
- docs and new examples should prefer canonical APIs:
  - `get`
  - `first`
  - `last`
  - `nth`
  - string `find`
  - `find_opt`
  - helper-driven chaining with `then_get`, `then_first`, `then_nth`, `then_find`, and `or_else` where composition helps
- new naming rule in current docs/runtime surface:
  - new `?`-suffixed APIs are boolean-returning
  - maybe-returning APIs should use Option values without `?`
  - `get?` remains the existing compatibility exception; `get` is the canonical maybe-aware name in this phase

Pattern matching note:

- `none` matches as a literal pattern
- `none(reason)` matches structured absence by reason
- `none(reason, context)` matches structured absence by reason and context
- `some(pattern)` destructures option values in function clauses and case arms
- `some(...)` pattern form requires exactly one inner pattern
- in `none(reason)` and `none(reason, context)` patterns, the reason slot matches the quoted/literal reason value

### String helpers

- `byte_length`, `is_empty`, `concat`
- `contains`, `starts_with`, `ends_with`, `find`
- `split`, `split_whitespace`, `join`
- `trim`, `trim_start`, `trim_end`
- `lower`, `upper`, `parse_int`
- public string helpers are thin prelude wrappers in `std/prelude/string.genia`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying runtime behavior remains host-backed and unchanged in this phase

`parse_int` behavior:

- `parse_int(string)` parses base-10 integers
- `parse_int(string, base)` parses using explicit base `2..36`
- surrounding whitespace is ignored
- leading `+` / `-` is supported
- invalid text raises clear `ValueError`
- non-string input raises clear `TypeError`
- invalid base type raises clear `TypeError`
- out-of-range base raises clear `ValueError`

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

## 7) Autoloaded stdlib

Autoload is keyed by `(name, arity)` and currently registers functions from bundled stdlib sources:

- `std/prelude/list.genia`
- `std/prelude/fn.genia`
- `std/prelude/map.genia`
- `std/prelude/ref.genia`
- `std/prelude/process.genia`
- `std/prelude/io.genia`
- `std/prelude/option.genia`
- `std/prelude/string.genia`
- `std/prelude/math.genia`
- `std/prelude/awk.genia`
- `std/prelude/cell.genia`

Loading behavior:

- bundled stdlib `.genia` files are loaded via package resources
- this works in both local repo execution and installed-package/tool execution
- custom absolute filesystem autoload paths still work
- file-relative module imports still resolve from the requesting source file's directory first
- autoload can be triggered both by calls and by plain name lookup for function values
  - this means autoloaded functions can be passed to higher-order helpers such as `apply`, `compose`, `map_some`, and `flat_map_some`
  - `help("name")` also triggers autoload for registered public helpers before reporting an undefined name

Notable autoloaded functions include:

- list: `list`, `first`, `rest`, `empty?`, `nil?`, `append`, `length`, `reverse`, `reduce`, `map`, `filter`, `count`, `any?`, `nth`, `take`, `drop`, `range`
- canonical list/search helpers: `first`, `last`, `nth`, string `find`, `find_opt`
- compatibility aliases: `first_opt`, `nth_opt`
- fn: `apply`, `compose`
- cli: `cli_parse`, `cli_flag?`, `cli_option`, `cli_option_or`
- map: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- ref: `ref`, `ref_get`, `ref_set`, `ref_is_set`, `ref_update`
- process: `spawn`, `send`, `process_alive?`
- io: `write`, `writeln`, `flush`
- flow: `lines`, `rules`, `each`, `collect`, `run`
- option: `some`, `none?`, `some?`, `get`, `get?`, `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`, `or_else`, `or_else_with`, `unwrap_or`, `absence_reason`, `absence_context`, `is_some?`, `is_none?`
- string: `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`, `find`, `split`, `split_whitespace`, `join`, `trim`, `trim_start`, `trim_end`, `lower`, `upper`, `parse_int`
- syntax: `self_evaluating?`, `symbol_expr?`, `tagged_list?`, `quoted_expr?`, `quasiquoted_expr?`, `assignment_expr?`, `lambda_expr?`, `application_expr?`, `block_expr?`, `match_expr?`, `text_of_quotation`, `assignment_name`, `assignment_value`, `lambda_params`, `lambda_body`, `operator`, `operands`, `block_expressions`, `match_branches`, `branch_pattern`, `branch_has_guard?`, `branch_guard`, `branch_body`
- metacircular evaluator: `empty_env`, `lookup`, `define`, `set`, `extend`, `eval`
- math: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk: `fields`, `awkify`, `awk_filter`, `awk_map`, `awk_count`
- cell: `cell`, `cell_with_state`, `cell_send`, `cell_get`, `cell_state`, `cell_failed?`, `cell_error`, `restart_cell`, `cell_status`, `cell_alive?`
- prelude public functions now carry Markdown docstrings intended for `help(...)` teaching output

## 8) Tail calls and optimization behavior

Implemented tail-call/runtime behavior:

- proper tail-call optimization is implemented via trampoline evaluation
- function calls in tail position execute in constant stack space
- self tail recursion is implemented
- mutual tail recursion is implemented
- tail position currently includes:
  - the direct result of a function body
  - the selected branch result of a case expression
  - the final expression in a block
  - the final pipeline stage after `|>` lowering

Other implemented optimizations:

- specialized nth-style list traversal rewrite to `IrListTraversalLoop` for a narrow recognized recursion shape

Core IR shape currently includes:

- program items: expression statement, assignment, named function definition
- expressions: literal, variable, call, unary, binary, lambda, block, list, map, spread, case
- patterns: wildcard, variable, literal, tuple, list, map, final rest
- function docstrings are carried as metadata on named-function definitions (not runtime expressions)

## 9) Debug/runtime tooling

- parser/IR nodes carry source spans (filename + line/column ranges)
- `run_debug_stdio(...)` exposes debugger protocol endpoints used by the VS Code extension
- `help(name)` displays named-function metadata when available:
  - function signature header (`name/shape`, shapes include `+` for varargs)
  - source location (`Defined at file:line`) when available
  - Markdown-aware docstring rendering (headings, bullet lists, inline code, fenced code blocks, paragraph spacing)
  - docstring normalization (trim outer blank lines, dedent indentation, optional triple-quote wrapper stripping, collapse excessive blank lines)
  - undocumented fallback message (`No documentation available.`)
- `help()` with no arguments prints a small overview centered on the public prelude-backed stdlib surface and calls out the intentionally small host bridge
  - the overview keeps only a small host-written scaffold; representative public family samples are derived from registered prelude autoloads
- `help("name")` for a string that resolves to a non-Genia host-backed runtime name prints a generic bridge note instead of maintaining a separate raw-host documentation registry

## 10) Explicitly not implemented (current)

- general host interop / FFI layer
- general member access syntax
- index syntax
- generalized flow runtime semantics beyond the current phase (async scheduling, advanced backpressure/cancellation, configurable multi-port stages)
- full Flow system (stages/sinks/backpressure/multi-port pipelines)
- language-level scheduler/selective receive/timeouts (concurrency remains host-primitive based)

## 11) Example demos shipped in-repo

- `examples/tic-tac-toe.genia`: interactive text game example
- `examples/ants.genia`: first minimal ants-style stochastic grid simulation demo

`examples/ants.genia` intentionally uses only currently implemented features:

- public prelude-backed map helpers over the host-backed map runtime for persistent world updates
- `rand_int` for random movement choice
- recursion for stepping
- `sleep` for blocking frame delay
- text rendering via `print`

It is intentionally minimal and single-ant first. It is **not** actor-based, does **not** add a scheduler, and does **not** introduce new language syntax.
