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
- variable binding
- wildcard `_`
- tuple pattern
- list pattern with optional rest

Required constraints:

- list rest pattern (`..name` / `.._`) is valid only in final list-pattern position
- duplicate names in a pattern require equality at match time

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
- the docstring is metadata, not a runtime expression
- lambdas do not support docstrings
- docstring text is interpreted as Markdown for `help(...)` display with lightweight formatting only (no full Markdown engine)

## 9) Operator model

Implemented operators are limited to:

- unary: `-`, `!`
- binary: `+ - * / % < <= > >= == != && ||`

No implicit pipeline/member/index operators should be introduced without explicitly updating state/rules docs and tests.

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
## 14) Documentation + tests as contract

When changing syntax/semantics/runtime behavior, update together:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md` for user-visible behavior
- corresponding tests under `tests/`

## 15) Conditional model invariant

- Genia has no conditional keyword (`if` or `switch`)
- branching is expressed only through pattern matching
