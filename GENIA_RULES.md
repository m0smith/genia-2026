# Genia — Compiler & Language Invariants (Current)

These are implementation invariants that contributors should preserve.

## 1) Expression vs case grammar separation

- Case syntax (`->`, `?`, `|`) is not a normal infix-expression system.
- Parser must only parse case arms in explicit case contexts.

## 2) Case placement (hard constraint)

Case expressions are valid only:

- as full function bodies
- as the final expression in a block

Parser must reject case syntax in subexpressions, call arguments, list elements, and non-final block positions.

## 3) One case expression per block

- A block may include zero or more ordinary expressions.
- If a case expression appears, it must be the final expression.

## 4) Full tuple match model

Pattern matching always targets the full argument tuple.

- `f(x)` still matches a one-item tuple target.
- Multi-arg functions are tuple-pattern sugar, not a separate mechanism.

## 5) Arrow disambiguation by parse context

`->` means:

- lambda arrow in expression parsing
- case arm mapping in case parsing

Do not resolve this via precedence hacks.

## 6) Pattern validity rules

Supported patterns:

- literal
- glob string pattern (`glob"..."`)
- option constructor pattern (`some(pattern)`)
- variable binding
- wildcard `_`
- tuple pattern
- list pattern with optional rest
- map pattern (string-keyed entries; partial-by-default)

Required constraints:

- list rest pattern (`..name` / `.._`) is valid only in final list-pattern position
- map pattern shorthand is valid only for identifier keys (`{name}`), not string keys (`{"name"}` requires `:`)
- parser ignores newlines between list-pattern delimiters and items
- duplicate names in a pattern require equality at match time
- glob patterns match only string values and must match the entire string
- glob pattern syntax supports only:
  - `*`, `?`, `[abc]`, `[a-z]`, `[!abc]`
  - escapes: `\*`, `\?`, `\[`, `\]`, `\\`
- malformed glob classes must raise deterministic syntax errors

## 7) Spread semantics

- list literal spread requires list value at runtime
- call argument spread requires list value at runtime
- spreading non-list values must raise `TypeError`

## 8) Function resolution invariants

- fixed-arity match is preferred over varargs match
- varargs ambiguity must raise `TypeError("Ambiguous function resolution")`
- named-function groups may carry one canonical docstring:
  - no docstrings => undocumented
  - one docstring total => valid
  - repeated identical docstrings => valid
  - conflicting docstrings => clear `TypeError`

## 8.1) Named function docstring parse invariant

- parser may treat a string literal as function docstring metadata only for named function definitions after `=`
- supported docstring string literals include ordinary quoted strings and triple-quoted multiline strings
- the docstring is metadata, not a runtime expression
- after docstring metadata, the function body may be either a normal expression or the same parenthesized case-expression form accepted for ordinary function bodies
- lambdas do not support docstrings
- docstring text is interpreted as Markdown for `help(...)` display with lightweight formatting only (no full Markdown engine)


## 8.2) Module import + module value invariants (phase 1)

- supported import forms are exactly:
  - `import mod`
  - `import mod as alias`
- imports bind only the module value in the current environment (no export splatting)
- module values are runtime namespace values distinct from maps
- module resolution is file-based only in this phase
- module loads are cached by module name (`loaded_modules`); duplicate imports/aliases must reuse the same module value instance
- top-level named assignments/functions from the module file are exported
- missing module files must raise a deterministic `FileNotFoundError("Module not found: <name>")`

## 8.3) Assignment invariants

- `name = expr` defines or rebinds a lexical name.
- If `name` already exists in the reachable lexical environment chain, assignment updates the nearest existing binding.
- Otherwise assignment creates `name` in the current scope.
- Function parameters are ordinary assignable lexical bindings.
- Closures observe rebinding through captured lexical environments.
- Assignment is limited to simple names in this phase.
- Invalid targets such as `(a + b) = 3` must raise `SyntaxError("Assignment target must be a simple name")`.
- Module evaluation keeps its own module environment boundary, so module top-level assignment must not rebind names in the importing root environment.
- Builtin/root names are not protected from rebinding inside the same root environment in the current implementation.

## 9) Operator model

Implemented operators are limited to:

- unary: `-`, `!`
- binary: `+ - * / % < <= > >= == != && ||`
- pipeline: `|>`
- slash named accessor form: `lhs/name` (RHS bare identifier only)

Pipeline rewrite invariant:

- `x |> f` is equivalent to `f(x)`
- `x |> f(y)` is equivalent to `f(y, x)` (append source value as final arg)
- `x |> expr` is equivalent to `expr(x)` when `expr` is valid in ordinary call-callee position
  - example: `record |> "name"` is equivalent to `"name"(record)`
- chaining is left-associative
- newlines may appear immediately before `|>` and immediately after `|>` in ordinary expression parsing
- rewrite happens in lowering from parsed AST to Core IR; runtime does not treat pipeline as a separate IR/runtime primitive
- this is expression-level call rewriting only (no stream runtime semantics)
- tail position propagates through the final pipeline stage because the lowered call expression inherits the surrounding tail position


Slash accessor invariants (phase 1):

- `lhs/name` is narrow named access, not general member access
- only module values and map values are valid LHS kinds
- for maps: missing key returns `nil`
- for modules: missing export raises a clear error
- non-identifier RHS forms are invalid for named access
- arithmetic division `/` remains available and unchanged for ordinary arithmetic contexts

No additional member/index/flow operators should be introduced without explicitly updating state/rules docs and tests.

## 9.1) Tail-call guarantee

- Genia guarantees proper tail-call optimization for function calls in tail position.
- A tail-position call must execute in constant stack space.
- Current runtime implementation uses an explicit trampoline in the evaluator rather than relying on Python recursion.
- Tail position currently includes:
  - the direct result of a function body
  - the result expression of a selected case arm
  - the final expression in a block
  - the final pipeline stage after `|>` lowering
- Non-tail calls are unchanged and may still consume Python stack space.

## 9.2) Symbols and quote

- symbols are runtime values distinct from strings
- `quote(expr)` is a special form, not an ordinary function call
- `quote(expr)` must not evaluate `expr`
- `quote(expr)` currently converts syntax to data with these core rules:
  - identifier -> symbol
  - number / string / boolean / `nil` / `none` -> corresponding literal runtime value
  - list literal -> pair chain ending in `nil`
  - map literal -> map of quoted keys and quoted values
  - unary / binary / call forms -> pair chain headed by a symbol
- quoted identifier map keys remain symbols; quoted string map keys remain strings
- symbol values print as bare names and are stable map keys
- there is no `'x` quote sugar in this phase

## 9.2.1) Quasiquotation

- `quasiquote(expr)` is a special form that constructs the same runtime data shapes as `quote(expr)`.
- `quasiquote(expr)` must not eagerly evaluate ordinary subexpressions.
- `unquote(expr)` evaluates `expr` and inserts the result at the nearest active quasiquote depth.
- Nested quasiquote depth is significant:
  - nested `quasiquote(...)` increases depth
  - `unquote(...)` only activates at the nearest surrounding quasiquote
- `unquote_splicing(expr)` is implemented only in quasiquoted list literal contexts.
- `unquote_splicing(expr)` currently accepts:
  - ordinary list values
  - `nil`
  - nil-terminated pair chains
- invalid splice values must raise clear `TypeError`
- `unquote(...)` and `unquote_splicing(...)` outside quasiquote must raise clear runtime errors
- `quasiquote(unquote_splicing(...))` is invalid because splicing requires a quasiquoted list context

## 9.2.2) Programs-as-data helpers

- Genia provides a small stdlib helper layer for inspecting quoted expressions.
- These helpers operate on the same runtime data representation produced by `quote(expr)` and `quasiquote(expr)`.
- Current stabilized quoted tags are:
  - `(quote <expr>)`
  - `(quasiquote <expr>)`
  - `(assign <name-symbol> <value-expr>)`
  - `(lambda <params-structure> <body-expr>)`
  - `(block <expr1> <expr2> ...)`
  - `(match (clause <pattern> <result>) ...)`
  - `(match (clause <pattern> <guard> <result>) ...)`
- Current helper surface includes:
  - predicates: `self_evaluating?`, `symbol_expr?`, `tagged_list?`, `quoted_expr?`, `quasiquoted_expr?`, `assignment_expr?`, `lambda_expr?`, `application_expr?`, `block_expr?`, `match_expr?`
  - selectors: `text_of_quotation`, `assignment_name`, `assignment_value`, `lambda_params`, `lambda_body`, `operator`, `operands`, `block_expressions`
- Selectors must raise clear `TypeError` when used on the wrong expression kind.
- Current representation limitation:
  - ordinary quoted pair/list data and application expressions can share the same raw pair shape
  - the helper layer therefore documents application detection as a best-fit rule over the current quoted representation rather than a full surface-syntax classifier

## 9.3) Pairs

- pairs are immutable two-field runtime values created with `cons`
- `car` returns the head field
- `cdr` returns the tail field
- `pair?(x)` reports whether a value is a pair
- `null?(x)` reports whether a value is exactly `nil`
- pair equality is structural
- lists built from pairs are chains of pairs ending in `nil`
- ordinary list literals remain list values in this phase; they do not lower to pairs

## 9.4) Promises

- `delay(expr)` is a special form, not an ordinary function call.
- `delay(expr)` must not evaluate `expr` eagerly.
- `delay(expr)` creates a promise value that captures the current lexical environment in the same way closures do.
- `force(value)` forces a promise once and memoizes the successful result.
- `force(value)` returns non-promise values unchanged.
- If promise forcing raises, the promise remains unforced and later `force(...)` calls retry evaluation.
- Promises are ordinary delayed values and are separate from Flow.
- Promise forcing is explicit only; no automatic forcing is introduced in this phase.

## 9.5) Streams

- Streams are a stdlib abstraction, not a runtime value family.
- A stream node is built from Pair + Promise:
  - `cons(head, delay(tail_expr))`
  - prelude construction is exposed as `stream_cons(head, tail_fn)`
- Stream tails are forced explicitly with `stream_tail(s)` / `force(cdr(s))`.
- Current public stream helpers are `stream_cons`, `stream_head`, `stream_tail`, `stream_map`, `stream_take`, and `stream_filter`.
- `stream_take(n, s)` materializes the first `n` items as an ordinary list.
- Streams remain distinct from Flow:
  - streams are pure delayed data
  - Flow is the runtime pipeline/IO model

## 10) Ref + concurrency runtime guarantees

- refs are synchronized host objects
- process mailbox handling is FIFO per process
- one handler invocation at a time per process
- concurrency remains host-backed (threads), not language-scheduled
- cell helpers are runtime-backed in this phase and expose these public names:
  - `cell(initial)` / `cell_with_state(ref_value)`
  - `cell_send(cell, update)`
  - `cell_get(cell)` / `cell_state(cell)`
  - `cell_failed?(cell)` / `cell_error(cell)`
  - `restart_cell(cell, new_state)`
  - `cell_status(cell)` / `cell_alive?(cell)`
- cell invariants:
  - updates are asynchronous and serialized one at a time
  - last successful state is preserved
  - failed updates must not change state
  - failed updates mark the cell failed and cache an error string
  - failed cells reject future `cell_send` and `cell_get` with `RuntimeError`
  - queued updates after a failure are discarded
  - `restart_cell` clears failure, installs new state, and discards queued pre-restart updates in this phase
  - nested `cell_send` calls issued during an update are staged and are committed only if that update succeeds

## 11) Host-backed persistent map invariants

- persistent map runtime is shared by both map builtins and map literal/pattern syntax
- required builtins: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- map values are opaque runtime wrappers, not exposed host objects
- `map_put` / `map_remove` must return new map values (no mutation of prior values)
- unsupported map input types and unsupported key types must raise clear `TypeError`

## 11.1) Callable-data invariants (phase 1)

- ordinary call syntax may target map values and string values in these exact forms only:
  - `m(key)` / `m(key, default)` where `m` is a map value
  - `"key"(m)` / `"key"(m, default)` where first arg is a map value
- map-call and string-projector-call arity is restricted to 1 or 2; other arities raise clear `TypeError`
- missing map keys return `nil` unless an explicit default is provided in arity-2 form
- string projector with non-map target raises clear `TypeError`
- this does not add parser syntax, call operators, or user-defined callable-data protocols

## 11.2) Option invariants (phase 1)

- primitive option values are `none` and `some(value)` (where `none` is distinct from `nil`)
- `get?(key, target)` is defined exactly as:
  - `get?(key, none) -> none`
  - `get?(key, some(map)) -> get?(key, map)`
  - `get?(key, map) -> some(value)` when key exists
  - `get?(key, map) -> none` when key is missing
- key presence, not value truthiness, determines `some(...)` vs `none`
  - key mapped to `nil` still returns `some(nil)`
- `nil` and `none` remain distinct runtime values
- `some(nil)` is valid and distinct from `none`
- pattern matching supports constructor destructuring for `some(...)` with exactly one inner pattern
- `unwrap_or(default, opt)` accepts option values only
- `is_some?(opt)` and `is_none?(opt)` report option shape
- new `?`-suffixed APIs must be boolean-returning
- maybe-returning APIs should prefer Option values and should not use `?`
- `get?` remains the current compatibility exception to that naming rule
- current Option-returning list helpers are `first_opt`, `last`, and `find_opt`
- pipeline behavior is unchanged and relies on existing rewrite rules (`record |> get?("name")` rewrites to `get?("name", record)`)

## 11.3) String builtin invariants

- `parse_int(string)` parses base-10 integers from strings
- `parse_int(string, base)` parses with explicit base in `2..36`
- `parse_int` ignores surrounding whitespace and supports leading `+` / `-`
- invalid integer text must raise clear `ValueError`
- non-string input must raise clear `TypeError`
- invalid base type must raise clear `TypeError`
- out-of-range base must raise clear `ValueError`

## 12) Error behavior

- unmatched function/case dispatch should raise deterministic runtime errors
- invalid grammar forms should fail during parse with syntax errors
- type-invalid builtins (e.g., non-list spread) should raise clear `TypeError`
- value-invalid builtins should raise clear `ValueError` where appropriate (e.g., `rand_int(0)`, `sleep(-1)`, `parse_int("12x")`)

## 13) Simulation primitive builtins (host-backed only)

- supported builtins: `rand`, `rand_int`, `sleep`
- `rand()` returns a float in `[0, 1)`
- `rand_int(n)` requires a positive integer `n`, returns integer in `[0, n)`
- `sleep(ms)` requires a non-negative number and blocks current execution for `ms` milliseconds
- these are simple runtime builtins only: no scheduler, no async/await, no event loop, no new syntax

## 14) Bytes / JSON / ZIP bridge invariants (host-backed only)

- bytes are runtime wrapper values (not string/list aliases)
- zip entries are runtime wrapper values with name + bytes payload
- required builtins:
  - `utf8_decode`, `utf8_encode`
  - `json_parse`, `json_pretty`
  - `zip_entries`, `zip_write`
  - `entry_name`, `entry_bytes`, `set_entry_bytes`, `update_entry_bytes`, `entry_json`
- `zip_entries(path)` returns an eager list in this phase (not lazy flow semantics)
- `zip_write` preserves the order of entries it receives
- `json_parse` returns runtime map values for JSON objects
- this bridge does not introduce a generalized Flow system

## 15) Documentation + tests as contract

When changing syntax/semantics/runtime behavior, update together:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md` for user-visible behavior
- corresponding tests under `tests/`

## 16) Conditional model invariant

- Genia has no conditional keyword (`if` or `switch`)
- branching is expressed only through pattern matching

## 17) CLI args + parsing invariants (runtime-only, list-first)

- raw process args are exposed via `argv()` as a list of strings (no `$1`/`$2` syntax)
- CLI parsing is runtime builtin behavior (`cli_parse`, `cli_flag?`, `cli_option`, `cli_option_or`), not parser syntax
- `cli_parse` returns `[opts_map, positionals_list]` where `opts_map` is persistent (`map_put` semantics, last write wins)
- `cli_parse(args, spec)` accepts minimal map spec keys only:
  - `flags` (list of strings)
  - `options` (list of strings)
  - `aliases` (map of string->string)
- invalid CLI arg/spec/value types raise clear deterministic `TypeError`; ambiguous grouped short-option-with-value specs raise deterministic `ValueError`

## 18) Program entrypoint invariant (runtime convention only)

- `main` is not a keyword and introduces no parser syntax
- automatic entrypoint execution applies only in file mode and `-c` command mode
- entrypoint resolution order is exact arity:
  - prefer exact `main/1` and call it with `argv()`
  - else use exact `main/0`
  - else do nothing
- no partial matching/coercion is performed by the entrypoint selector

## 19) Flow runtime invariants (phase 1)

- pipeline operator semantics are unchanged (AST→Core IR call rewrite only)
- flow behavior is runtime-level and value-based, with no parser/operator additions
- `stdin` may be used as a source value in pipelines; `input()` remains interactive-only
- phase-1 flow builtins:
  - sources/transforms: `lines`, `map`, `filter`, `take`
  - stdlib aliases over `take`: `head(flow)`, `head(n, flow)`
  - sinks/materialization: `each`, `run`, `collect`
- flows are single-use:
  - first consumption succeeds
  - second consumption must raise `RuntimeError("Flow has already been consumed")`
- `take(n, flow)` must stop upstream pulling immediately after producing `n` items
- `stdin |> lines` must remain lazy; binding the source must not force a full stdin read up front
- reaching EOF or a `take`/`head` limit is normal completion (not an error)

## 20) Output sink invariants (host-backed phase 1)

- `stdout` and `stderr` are runtime capability values, not parser syntax
- required output builtins:
  - `write(sink, value)`
  - `writeln(sink, value)`
  - `flush(sink)`
- `print(...)` writes to `stdout`
- `log(...)` writes to `stderr`
- `input()` remains independent from `stdin` / Flow source behavior
- broken pipe on `stdout` output in CLI/file/command execution is normal downstream termination and must not surface as a Python traceback
- broken pipe on `stderr` should be handled best-effort without recursive noisy failures

## 21) Pipe command mode invariants (runtime-only)

- `-p` / `--pipe` are CLI-only runtime flags, not parser syntax
- pipe mode wraps the provided source exactly as `stdin |> lines |> <expr> |> run`
- the provided source must be a single stage expression
- explicit `stdin` and explicit `run` in pipe mode are rejected with a clear error
- ordinary `-c` command mode remains unchanged and evaluates exactly what the user wrote
- pipe mode bypasses the `main` convention; file mode and `-c` mode keep existing `main/1` then `main/0` behavior
- pipeline operator semantics are unchanged; this does not add a new operator or runtime meaning for `|>`
