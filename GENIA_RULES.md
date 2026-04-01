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
- variable binding
- wildcard `_`
- tuple pattern
- list pattern with optional rest

Required constraints:

- list rest pattern (`..name` / `.._`) is valid only in final list-pattern position
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
- lambdas do not support docstrings
- docstring text is interpreted as Markdown for `help(...)` display with lightweight formatting only (no full Markdown engine)

## 9) Operator model

Implemented operators are limited to:

- unary: `-`, `!`
- binary: `+ - * / % < <= > >= == != && ||`
- pipeline: `|>`

Pipeline rewrite invariant:

- `x |> f` is equivalent to `f(x)`
- `x |> f(y)` is equivalent to `f(y, x)` (append source value as final arg)
- chaining is left-associative
- this is expression-level call rewriting only (no stream runtime semantics)

No additional member/index/flow operators should be introduced without explicitly updating state/rules docs and tests.

## 10) Ref + concurrency runtime guarantees

- refs are synchronized host objects
- process mailbox handling is FIFO per process
- one handler invocation at a time per process
- concurrency remains host-backed (threads), not language-scheduled

## 11) Host-backed persistent map bridge invariants

- persistent map support is runtime/builtin only (no syntax added)
- required builtins: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- map values are opaque runtime wrappers, not exposed host objects
- `map_put` / `map_remove` must return new map values (no mutation of prior values)
- unsupported map input types and unsupported key types must raise clear `TypeError`

## 12) Error behavior

- unmatched function/case dispatch should raise deterministic runtime errors
- invalid grammar forms should fail during parse with syntax errors
- type-invalid builtins (e.g., non-list spread) should raise clear `TypeError`
- value-invalid builtins should raise clear `ValueError` where appropriate (e.g., `rand_int(0)`, `sleep(-1)`)

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
