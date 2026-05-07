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
- Lambda parameter patterns also match the full argument tuple, but lambdas remain single-arm.

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
- lambda parameter position may use existing pattern forms; it must not introduce multi-arm lambda syntax
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

## 8.1.1) Prefix annotation parse invariant

- prefix annotation syntax is:
  - `@name value`
  - `@name "string"`
  - `@name """multiline string"""`
- annotation values are parsed as ordinary expressions in this phase
- one or more consecutive top-level prefix annotation lines attach to the next bindable top-level form only
- currently supported annotation targets are:
  - named function definitions
  - top-level simple-name assignments
- annotations not followed by one of those bindable forms must raise a parse error
- parser must not silently drop parsed annotations
- parsed annotations are represented explicitly in the AST as:
  - `Annotation(name, value)`
  - `AnnotatedNode(annotations, target)`
- annotation metadata behavior is currently implemented only for:
  - `@doc`
  - `@meta`
  - `@since`
  - `@deprecated`
  - `@category`
- no annotation introduces macros, compile-time transforms, or syntax rewriting in this phase

## 8.1.2) Prefix annotation runtime semantics

- annotations attach to the binding name, not to an anonymous raw value detached from that binding
- annotated targets still evaluate normally first; annotation metadata is attached after the binding is created or updated
- `@doc`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"doc"`
- `@meta`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a map
  - merges all map entries into the binding metadata
- `@since`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"since"`
- `@deprecated`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"deprecated"`
- `@category`:
  - evaluates its value expression after the target binding exists
  - the resulting value must be a string
  - stores metadata under key `"category"`
- multiple annotations merge from top to bottom
- last annotation wins for duplicate metadata keys
- rebinding without annotations preserves existing binding metadata
- rebinding with annotations merges new metadata over existing metadata for that binding
- `doc("name")` returns the current doc string for a bound name or `none("missing-doc", {name: ...})`
- `meta("name")` returns the current metadata map for a bound name
- unsupported annotations must fail clearly at runtime
- annotation metadata is ordinary runtime metadata only in this phase:
  - no macros
  - no compile-time transforms
  - no evaluator special forms beyond metadata attachment


## 8.2) Module import + module value invariants (phase 1)

- supported import forms are exactly:
  - `import mod`
  - `import mod as alias`
- imports bind only the module value in the current environment (no export splatting)
- module values are runtime namespace values distinct from maps
- module resolution is:
  - file-based for ordinary modules
  - allowlisted host-backed for the current Python host namespace (`python`, `python.json`)
- module loads are cached by module name (`loaded_modules`); duplicate imports/aliases must reuse the same module value instance
- top-level named assignments/functions from the module file are exported
- missing module files must raise a deterministic `FileNotFoundError("Module not found: <name>")`
- disallowed host module names must raise a deterministic `PermissionError("Host module not allowed: <name>")`
- module resolution order for user modules:
  - (1) requester-relative — `<requester-dir>/<mod>.genia` when the importing source has a known filesystem path
  - (2) BASE_DIR-relative — `<BASE_DIR>/<mod>.genia`
  - (3) packaged stdlib — bundled `std/prelude/<mod>.genia`
  - (4) raise `FileNotFoundError("Module not found: <mod>")`
- requester-relative resolution is skipped when the importing source filename is `<memory>` or `<command>`; when the filename is `<pipe>`, resolution proceeds from the current working directory
- import cycle detection must raise `RuntimeError("Module import cycle detected while loading <mod>")`; the cycling module must not be committed to the cache

## 8.2.1) Python host interop invariants (phase 1)

- Python host interop reuses the existing module system and narrow slash export access.
- There is no new member-access syntax for host interop in this phase.
- supported host modules are currently allowlisted:
  - `python`
  - `python.json`
- current Python root host exports are:
  - `open`
  - `read`
  - `write`
  - `close`
  - `read_text`
  - `write_text`
  - `len`
  - `str`
  - nested `json` submodule
- current `python.json` exports are:
  - `loads`
  - `dumps`
- host module exports participate in ordinary calls and pipelines through the existing callable model.
- boundary conversion rules in this phase are:
  - Genia string/number/bool -> Python scalar
  - Genia list -> Python list (recursive)
  - Genia map -> Python dict (recursive)
  - Genia `some(x)` -> converted host value for `x`
  - Genia `none(...)` -> Python `None`
  - Python `None` -> Genia `none("nil")`
  - Python list/tuple -> Genia list (recursive)
  - Python dict -> Genia map (recursive)
- host resource results that cannot be represented as plain Genia data may appear as opaque Python handle values.
- host exceptions must not be silently converted to success values.
  - ordinary host failures currently propagate as explicit Python-host errors
  - host `None` results are the only automatic none-mapping path in this phase
- current normalized bridge example:
  - `python.json/loads` raises `ValueError("python.json/loads invalid JSON: ...")` for invalid JSON text
- pipeline interaction at the bridge still uses ordinary pipeline semantics:
  - `some(x) |> python/len` passes `x` into the host export through ordinary host-boundary conversion
  - `none(...) |> python/len` skips the host export and preserves the same `none(...)`
  - Flow does not implicitly cross the bridge; passing a Flow to a host value export remains a type error unless an explicit Flow stage has already materialized ordinary values
- unrestricted host import, arbitrary attribute access, and arbitrary code execution are not part of this phase.

## 8.2.2) Autoload loading path invariants

- autoload loading is a separate loading path from user module imports
- autoloads are keyed by `(name, arity)` and triggered lazily on first name lookup miss in the root environment
- loaded exports bind directly into the root environment; no module value is created and no module cache entry is written
- autoload deduplication uses a separate file-key set, independent of the `loaded_modules` cache
- autoload cycle detection must raise `RuntimeError("Autoload cycle detected while loading <key>")`
- autoloads are stdlib-internal infrastructure; they are not accessible via slash access (`mod/name`) and are not part of the user-facing module system

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

## 8.3.1) Named function definition surface forms

- named function definitions currently accept:
  - `name(args) = expr`
  - `name(args) -> expr`
  - `name(args) { ... }`
- only the `=` form may carry named-function docstring metadata in this phase

## 8.4) Core IR portability invariants

- Core IR is the semantic portability boundary, while parser AST shape is host-local.
- The frozen minimal portable Core IR contract is documented in `docs/architecture/core-ir-portability.md`.
- AST->IR lowering output must stay inside the frozen portable `Ir*` node families.
- Host-local post-lowering optimized nodes (for example `IrListTraversalLoop`) are allowed only after host-local optimization passes and are not part of the minimal shared Core IR contract.
- Named slash access `lhs/name` lowers as `IrBinary(op=SLASH)`; hosts must not introduce a separate `IrSlashAccess` node.
- `none(reason, ctx)` lowers as `IrOptionNone`; the reason argument is wrapped in `IrQuote` (not evaluated) — bare `none` produces `reason=null`.
- `IrAssign` appears directly in `IrBlock.exprs`; it is not wrapped in `IrExprStmt`.

## 9) Operator model

Implemented operators are limited to:

- unary: `-`, `!`
- binary: `+ - * / % < <= > >= == != && ||`
- pipeline: `|>`
- slash named accessor form: `lhs/name` (RHS bare identifier only)

Pipeline invariant:

- `|>` is a dedicated pipeline evaluation form in this phase
- AST lowering keeps pipelines explicit in Core IR as one source plus an ordered stage list
  - pipelines are not lowered into nested ordinary call nodes
- ordinary call shape is preserved:
  - `x |> f` calls `f(x)`
  - `x |> f(y)` calls `f(y, x)` (append source value as final arg)
  - `x |> expr` calls `expr(x)` when `expr` is valid in ordinary call-callee position
  - example: `record |> "name"` behaves like `"name"(record)`
- chaining is left-associative
- newlines may appear immediately before `|>` and immediately after `|>` in ordinary expression parsing
- Option propagation is part of pipeline evaluation:
  - if a stage input is `none(...)`, the remaining stages do not execute and that same `none(...)` is returned
  - if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage receives `x`
- when that lifted stage returns a non-Option value `y`, the pipeline wraps it back as `some(y)`
- when that lifted stage returns `some(...)` or `none(...)`, that Option result is used as-is


## 10) Observable Spec Contract (Current Implemented Scope)

- Shared semantic-spec cases define observable behavior only for categories and scope implemented and recorded in `GENIA_STATE.md` (currently: `eval`, `ir`, `cli`, first-wave `flow`, initial `error`, and initial `parse` are active; focused core stdlib list/Flow coverage for `map`, `filter`, `first`, `last`, and `nth` is included in the eval and flow categories)
- Current shared eval and cli cases assert:
  - `stdout`
  - `stderr`
  - `exit_code`
- Current shared cli cases cover deterministic non-interactive file, command, and pipe modes; REPL is not covered by shared executable specs
- Current shared ir cases compare normalized portable Core IR
- Determinism in the current shared semantic-spec scope means:
  - eval and cli asserted outputs must match exactly after newline normalization
  - the runner must not trim or reinterpret meaningful whitespace
- Expanding shared semantic-spec coverage beyond that scope requires implementation plus `GENIA_STATE.md` updates first
- Flow remains explicit:
  - pipeline evaluation does not create implicit Value→Flow conversions
  - flow values still come from explicit bridge/stage functions such as `lines`, `evolve`, `collect`, and `run`
  - tail position propagates through the final pipeline stage


Slash accessor invariants (phase 1):

- `lhs/name` is narrow named access, not general member access
- only module values and map values are valid LHS kinds
- for maps: missing key returns `none("missing-key", {key: <name>})`
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
  - unary / binary / call forms -> tagged application pair chain `(app <operator> <arg1> ...)`
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
- the host-backed substrate in this phase remains intentionally small:
  - parser/lowering/quote representation
  - symbol/self-evaluating runtime shape detection
  - metacircular pattern-lowering support used by evaluator internals
- language-visible selectors, structural helpers, and branch/match glue over quoted forms should prefer prelude/Genia code.
- Current stabilized quoted tags are:
  - `(quote <expr>)`
  - `(quasiquote <expr>)`
  - `(app <operator> <operand1> <operand2> ...)`
  - `(assign <name-symbol> <value-expr>)`
  - `(lambda <params-structure> <body-expr>)`
  - `(block <expr1> <expr2> ...)`
  - `(match (clause <pattern> <result>) ...)`
  - `(match (clause <pattern> <guard> <result>) ...)`
- Current helper surface includes:
  - predicates: `self_evaluating?`, `symbol_expr?`, `tagged_list?`, `quoted_expr?`, `quasiquoted_expr?`, `assignment_expr?`, `lambda_expr?`, `application_expr?`, `block_expr?`, `match_expr?`
  - selectors: `text_of_quotation`, `assignment_name`, `assignment_value`, `lambda_params`, `lambda_body`, `operator`, `operands`, `block_expressions`
  - match selectors: `match_branches`, `branch_pattern`, `branch_has_guard?`, `branch_guard`, `branch_body`
- Selectors must raise clear `TypeError` when used on the wrong expression kind.
- Application expressions are represented explicitly as `(app ...)`.
- Ordinary quoted pair/list data remain plain pair/list data and must not be classified as applications.
- `operands(expr)` returns the operand tail of the tagged application as a pair-chain sequence.
- `match_branches(expr)` returns the branch tail of `(match ...)` as a pair-chain sequence.
- `branch_guard(branch)` raises a clear `TypeError` when the branch is not guarded.

## 9.2.3) Metacircular evaluation

- Genia provides a minimal phase-1 metacircular evaluator over quoted expressions.
- evaluator dispatch and helper glue are exposed through prelude in this phase, while host code keeps the metacircular environment/runtime substrate.
- Public evaluator/environment names are:
  - `empty_env`
  - `lookup`
  - `define`
  - `set`
  - `extend`
  - `eval`
  - `apply`
- `eval(expr, env)` currently supports only:
  - self-evaluating literals
  - symbol expressions
  - quoted expressions
  - assignment expressions
  - lambda expressions
  - match/case expressions
  - application expressions
  - block expressions
- `eval(expr, env)` must follow current lexical scoping rules through metacircular environments:
  - `define` binds in the current frame
  - `set` rebinds the nearest existing lexical name or creates in the current frame when missing
  - `extend` creates a child lexical environment
  - closures capture the defining environment
- metacircular compound procedures are represented as tagged pair data:
  - `(compound <params> <body> <env>)`
- metacircular matcher procedures are represented as tagged pair data:
  - `(matcher <match-expr> <env>)`
- `apply(proc, args)` must preserve current ordinary callable behavior and additionally apply metacircular compound procedures and metacircular matcher procedures.
- current limitations:
  - the evaluator is only defined for the supported expression families above
  - unsupported quoted forms must fail clearly instead of pretending broader evaluator coverage

## 9.3) Pairs

- pairs are immutable two-field runtime values created with `cons`
- `car` returns the head field
- `cdr` returns the tail field
- `pair?(x)` reports whether a value is a pair
- `null?(x)` reports whether a value is the normalized empty-pair terminator (`none("nil")`, including legacy `nil`)
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

## 9.6) Option / absence semantics

This section is the complete contract for how absence values behave in Genia.

### 9.6.1) The two Option forms

There are exactly two Option forms:

- `some(value)` — a present value
- `none(reason)` / `none(reason, context)` — a structured absence
  - bare `none` and legacy `nil` both normalize to `none("nil")`
  - `reason` is always a string
  - `context` is an optional map of metadata about the absence
  - metadata inspection helpers are:
    - `absence_reason(none(...))` -> `some(reason)`
    - `absence_context(none(...))` -> `some(context)` when present, otherwise `none("nil")`
    - `absence_meta(none(...))` -> `some({reason: ..., context: ...?})`

### 9.6.2) Option propagation in pipelines (invariants)

- if a stage input is `none(...)`, the stage does not execute and the same `none(...)` is returned
- if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage is invoked with `x`
- lifted stage results follow this rule:
  - non-Option result `y` becomes `some(y)`
  - Option results (`some(...)` / `none(...)`) are propagated unchanged
- if a stage produces a `none(...)` result, remaining stages do not execute
- structured none metadata (reason string + context map) passes through every skipped stage unchanged
### 9.6.3) Structured-none metadata invariant

Agents and implementations must preserve structured none metadata:

- `none("missing-key", { key: "user" }) |> f` → `none("missing-key", { key: "user" })` (not `none("missing-key")`)
- every stage skip must return the exact same `none(...)` value, not a new one

### 9.6.4) None-awareness: when a function receives none

- ordinary functions short-circuit on `none(...)` arguments (the call does not execute)
- a function explicitly handles absence when:
  - it is in `_NONE_AWARE_PUBLIC_FUNCTIONS`, or
  - at least one pattern arm matches `none(...)` or `none(reason, ctx)`, or
  - it is registered with `__genia_handles_none__ = True`
- handlers such as `some?`, `none?`, `unwrap_or`, `or_else`, `map_some`, `flat_map_some`, and all `then_*` helpers are explicitly none-aware

### 9.6.4.1) Explicit raw invocation: `apply_raw`

`apply_raw(f, args)` is a language-contract host primitive that calls `f` with the elements of list `args` as positional arguments without triggering the automatic `none(...)` short-circuit.

- `f` may be any Genia callable (named function, lambda, builtin)
- `args` must be a Genia list; a non-list second argument raises `TypeError`
- none values in `args` are delivered to `f` unchanged — the body executes
- exceptions raised inside `f` propagate through `apply_raw` unchanged
- the return value of `f` is returned as-is; no coercion or wrapping is applied
- `apply_raw` itself is subject to ordinary none-propagation: `apply_raw(f, none("x"))` short-circuits before `apply_raw` runs because `none("x")` is a direct argument to `apply_raw`
- use case: implementing higher-order functions (`reduce`, `map`, `filter`) that must deliver `none(...)` list elements to their callback

### 9.6.6) Debugging structured absence

Use structured none metadata directly instead of exceptions.

Examples:

- parse failure with reason-only metadata:
  - `none("parse_error")`
  - `absence_meta(none("parse_error"))` -> `some({reason: "parse_error"})`
- missing key with context metadata:
  - `none("missing_key", { key: "user" })`
  - `absence_meta(none("missing_key", { key: "user" }))` -> `some({reason: "missing_key", context: {key: "user"}})`
- pipeline propagation keeps metadata unchanged:
  - `none("index_out_of_bounds", { index: 9, length: 2 }) |> parse_int`
  - result is the same `none("index_out_of_bounds", { index: 9, length: 2 })`

### 9.6.5) Applying functions to Option-wrapped values

In direct calls, `some(x)` is still a normal value and is passed explicitly.
In pipelines, ordinary stages lift over `some(x)` automatically unless they are explicitly Option-aware.
Use explicit helpers when you want exact wrap/flat-map control regardless of stage detection:

| Goal | Helper |
|---|---|
| Apply plain `f` to inner value | `map_some(f, opt)` |
| Chain an Option-returning `f` | `flat_map_some(f, opt)` |
| Get a key from a map-or-Option | `then_get(key, target)` |
| Get first element of a list-or-Option | `then_first(target)` |
| Get nth element of a list-or-Option | `then_nth(index, target)` |
| Find substring in a string-or-Option | `then_find(needle, target)` |
| Recover with a default at pipeline end | `unwrap_or(default, opt)` |
| Recover with a fallback value | `or_else(opt, fallback)` |
| Recover with a lazy thunk | `or_else_with(opt, thunk)` |

Canonical pipeline patterns:

```
some("42") |> parse_int
```

Result: `some(42)` (stage receives `"42"`, result is already Option so it is preserved).

```
some(4) |> ((x) -> x + 1)
```

Result: `some(5)` (lifted stage result wraps back into `some(...)`).

```
some(4) |> unwrap_or(0)
```

Result: `4` (explicitly Option-aware stage receives the Option directly).

### 9.6.6) Some-lifting safety invariant

Automatic lifting applies only to pipeline stages that are not explicitly Option-aware.
Stages that explicitly handle Option values keep receiving Option values unchanged.
This protects helper-based and pattern-based Option handling from silent semantic drift.

## 10) Ref + concurrency runtime guarantees

- refs are synchronized host objects
- public ref helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/ref.genia`
- public process helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/process.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying ref/process behavior remains host-backed in this phase; wrappering does not change semantics
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
- public map helper names are exposed through `src/genia/std/prelude/map.genia`
- those helper names are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying persistent map runtime remains host-backed in this phase; helper exposure does not change semantics
- required builtins: `map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`
- map values are opaque runtime wrappers, not exposed host objects
- `map_put` / `map_remove` must return new map values (no mutation of prior values)
- unsupported map input types and unsupported key types must raise clear `TypeError`
- `pairs(xs, ys)` is a public stdlib helper whose observable contract is independent of the persistent map runtime:
  - it accepts two list values
  - it returns a list of two-element list values `[x, y]`
  - it preserves input order
  - it stops at the shorter input
  - it returns `[]` when either input list is empty
  - first-argument non-list values must raise `TypeError("pairs expected a list as first argument, received <type>")`
  - second-argument non-list values must raise `TypeError("pairs expected a list as second argument, received <type>")`
  - it must not return host tuples, Pair values, Flow values, padded rows, or Option wrappers

## 11.1) Callable-data invariants (phase 1)

- ordinary call syntax may target map values and string values in these exact forms only:
  - `m(key)` / `m(key, default)` where `m` is a map value
  - `"key"(m)` / `"key"(m, default)` where first arg is a map value
- map-call and string-projector-call arity is restricted to 1 or 2; other arities raise clear `TypeError`
- missing map keys return `none("missing-key", {key: key})` unless an explicit default is provided in arity-2 form
- string projector with non-map target raises clear `TypeError`
- this does not add parser syntax, call operators, or user-defined callable-data protocols

## 11.2) Option invariants (phase 3 canonical access)

- primitive option values are:
  - `none`
  - `none(reason)`
  - `none(reason, context)`
  - `some(value)`
- public option helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/option.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying option behavior remains host-backed in this phase; wrappering does not change semantics
- all `none...` forms belong to one absence family; reason/context are metadata, not a separate result kind
- `none` is shorthand for `none("nil")`
- legacy surface `nil` also evaluates to `none("nil")`; it is not a separate runtime absence value
- `reason` must be a string
- `context` must be a map when present
- key presence, not value truthiness, determines `some(...)` vs `none...`
  - key mapped to legacy `nil` still returns `some(none("nil"))`
- `get(key, target)` is the canonical maybe-aware lookup helper in this phase
- `get?(key, target)` is defined exactly as:
  - `get?(key, none) -> none`
  - `get?(key, none(reason)) -> none(reason)`
  - `get?(key, none(reason, context)) -> none(reason, context)`
  - `get?(key, some(map)) -> get?(key, map)`
  - `get?(key, map) -> some(value)` when key exists
  - `get?(key, map) -> none("missing-key", { key: key })` when key is missing
- `get(key, target)` has the same runtime behavior as `get?(key, target)`
- canonical list access helpers:
  - `first(list) -> some(value)` or `none("empty-list")`
  - `last(list) -> some(value)` or `none("empty-list")`
  - `nth(index, list) -> some(value)` or `none("index-out-of-bounds", { index: i, length: n })`
- canonical string search helper:
  - `find(string, needle) -> some(index)` or `none("not-found", { needle: needle })`
- canonical integer parsing helper:
  - `parse_int(string) -> some(int)` or `none("parse-error", context)`
  - `parse_int(string, base) -> some(int)` or `none("parse-error", context)`
- `find_opt(predicate, list)` is the canonical maybe-aware predicate-search helper for lists in this phase
- ordinary function calls propagate structured absence directly:
  - if any evaluated argument is `none(...)`, the call returns that same `none(...)`
  - the callee body is not evaluated unless the callee explicitly handles absence
- pattern matching supports:
  - literal `none`
  - structured none patterns `none(reason)` and `none(reason, context)`
  - constructor destructuring for `some(...)` with exactly one inner pattern
- in `none(reason)` and `none(reason, context)` patterns, the reason position matches the reason value directly; the context position uses normal pattern matching rules
- `unwrap_or(default, opt)` accepts option values only
- `is_some?(opt)` / `some?(opt)` and `is_none?(opt)` / `none?(opt)` report option shape
- `or_else(opt, fallback)` returns the wrapped value for `some(value)` and the fallback for any `none...` form
- `or_else_with(opt, thunk)` returns the wrapped value for `some(value)` and calls `thunk()` only for `none...`
- `absence_reason(opt)` returns `some(reason)` for any `none...` value
  - because plain `none` normalizes to `none("nil")`, `absence_reason(none)` returns `some("nil")`
- `absence_context(opt)` returns `some(context)` only when context metadata is present
- `some?` / `none?` and `is_some?` / `is_none?` have the same runtime truth values; the shorter `some?` / `none?` names are preferred in docs/examples
- `map_some(f, opt)`:
  - returns `some(f(value))` for `some(value)`
  - returns the original `none...` unchanged for any absence value
- `flat_map_some(f, opt)`:
  - returns `f(value)` for `some(value)`
  - requires `f(value)` to be an Option value
  - returns the original `none...` unchanged for any absence value
- direct pipelines propagate `none(...)` automatically and lift ordinary stages over `some(...)`
- those helpers remain distinct for explicit wrap/flat-map control, higher-order use, and non-pipeline composition
- `then_get(key, target)` is a thin maybe-aware chaining helper over `get`
- `then_first(target)` is a thin maybe-aware chaining helper over `first`
- `then_nth(index, target)` is a thin maybe-aware chaining helper over `nth`
- `then_find(needle, target)` is a thin maybe-aware chaining helper over string `find`
- propagation helpers preserve the original structured `none(...)` unchanged unless they are explicit recovery/defaulting helpers
- expected absence remains data, not an exception
- runtime failures are not silently converted into `none(...)`
- new `?`-suffixed APIs must be boolean-returning
- maybe-returning APIs should prefer Option values and should not use `?`
- compatibility aliases retained in this phase:
  - `get?` for `get`
  - `first_opt` for `first`
  - `nth_opt` for `nth`
- compatibility aliases are expected to preserve the same outward behavior as their canonical target
- migration status labels used in docs:
  - `canonical`: preferred public API for new code
  - `compatibility alias`: thin wrapper/alias kept for migration stability
  - `compatibility surface`: behavior still supported but is no longer the preferred teaching path when a clearer helper exists
- book/readme/repl examples should prefer canonical maybe-aware access and direct absence-aware pipelines over helper-heavy chaining and compatibility lookup surfaces
- `get?` remains the current compatibility exception to that naming rule; `get` is preferred for new maybe-aware code
- pipeline behavior is now Option-aware directly
- canonical safe-chaining is therefore direct:
  - `record |> get("user") |> get("address") |> get("zip")`
  - `data |> get("items") |> then_nth(0) |> then_get("name")`
  - the first structured `none(...)` is preserved unchanged until an explicit recovery/defaulting helper wraps the final pipeline result
- explicit helpers such as `map_some`, `flat_map_some`, and `then_*` remain useful for direct Option values, higher-order code, and non-pipeline composition
- compatibility lookup surfaces now also return structured `none(...)` for missing results
- developer-facing presentation is separate from semantics:
  - REPL/debug output should preserve structured absence syntax and context metadata visibly
  - clearer rendering does not change evaluation behavior, matching rules, or error behavior

## 11.3) String builtin invariants

- public string helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/string.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying string behavior remains host-backed in this phase; wrappering does not change semantics
- `find(string, needle)` returns:
  - `some(index)` when the substring exists
- `none("not-found", { needle: needle })` when the substring is missing
- `parse_int(string)` returns `some(int)` or `none("parse-error", context)`
- `parse_int(string, base)` does the same with explicit base in `2..36`
- `parse_int` ignores surrounding whitespace and supports leading `+` / `-`
- invalid integer text must return `none("parse-error", context)`
- non-string input must raise clear `TypeError`
- invalid base type must raise clear `TypeError`
- out-of-range base must raise clear `ValueError`

## 12) Error behavior

- unmatched function/case dispatch should raise deterministic runtime errors
- invalid grammar forms should fail during parse with syntax errors
- type-invalid builtins (e.g., non-list spread) should raise clear `TypeError`
- value-invalid builtins should raise clear `ValueError` where appropriate (e.g., `rand_int(0)`, `sleep(-1)`, invalid parse bases)

## 13) Simulation primitive builtins

- supported public randomness surface:
  - `rng(seed)`
  - `rand()`
  - `rand(rng_state)`
  - `rand_int(n)`
  - `rand_int(rng_state, n)`
- `sleep(ms)` remains a host-backed blocking builtin
- `rng(seed)` requires a non-negative integer seed and returns an explicit RNG state value
- `rand()` returns a host-RNG float in `[0, 1)` for convenience use
- `rand(rng_state)` returns `[next_rng_state, float]` deterministically from the explicit RNG state
- `rand_int(n)` requires a positive integer `n`, returns an integer in `[0, n)` for convenience use
- `rand_int(rng_state, n)` requires a valid RNG state and positive integer `n`, returns `[next_rng_state, int]` with the integer in `[0, n)`
- explicit seeded randomness is state-threaded and deterministic; the same seed must yield the same sequence
- the current Python host uses a simple fixed 32-bit LCG for the explicit seeded RNG
- these are intentionally small runtime primitives only: no scheduler, no async/await, no event loop, no new syntax

## 14) Bytes / JSON / ZIP bridge invariants (host-backed only)

- bytes are runtime wrapper values (not string/list aliases)
- zip entries are runtime wrapper values with name + bytes payload
- required builtins:
  - `utf8_decode`, `utf8_encode`
  - internal JSON bridge primitives: `_json_parse`, `_json_stringify`
  - `zip_entries`, `zip_write`
  - `entry_name`, `entry_bytes`, `set_entry_bytes`, `update_entry_bytes`, `entry_json`
- public JSON helpers are prelude-backed wrappers in `src/genia/std/prelude/json.genia`:
  - `json_parse(string)`
  - `json_stringify(value)`
  - `json_pretty(value)` compatibility alias for `json_stringify(value)`
- `zip_entries(path)` returns an eager list in this phase (not lazy flow semantics)
- `zip_write` preserves the order of entries it receives
- `json_parse` returns runtime map values for JSON objects
- JSON parse/stringify failures return structured `none(...)` values:
  - parse failures: `none("json-parse-error", context)`
  - stringify failures: `none("json-stringify-error", context)`
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
- public CLI helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/cli.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying host support is intentionally narrow in this phase:
  - raw `argv()`
  - spec normalization/validation
  - token character decomposition
  - deterministic CLI-specific error raising
- CLI parsing remains runtime/library behavior, not parser syntax
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

- pipeline operator semantics are Option-aware, but Flow remains explicit and runtime-level
- `stdin` may be used as a source value in pipelines; `input()` remains interactive-only
- public flow helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/flow.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- the host Flow kernel remains intentionally small in this phase:
  - lazy pull-based consumption
  - single-use enforcement
  - source-bound stdin/runtime integration
  - sink/materialization boundaries
- language-visible `rules` orchestration, defaulting, and most contract validation now live in prelude/Genia code
- the host rules kernel consumes normalized rule output from prelude and must not provide user-visible rule-result defaults itself
- phase-1 flow builtins:
  - sources/transforms: `lines`, `evolve(init, f)`, `map`, `filter`, `take`, `rules`
  - stdlib aliases over `take`: `head(flow)`, `head(n, flow)`
  - sinks/materialization: `each`, `run`, `collect`
- flows are single-use:
  - first consumption succeeds
  - second consumption must raise `RuntimeError("Flow has already been consumed")`
- `take(n, flow)` must stop upstream pulling immediately after producing `n` items
- `evolve(init, f)` must emit `init` first and then call `f(previous_value)` only when downstream pulls later items
- `stdin |> lines` must remain lazy; binding the source must not force a full stdin read up front
- reaching EOF or a `take`/`head` limit is normal completion (not an error)

## 19.1) Seq compatibility invariants

- Seq is a semantic compatibility category for ordered value production, not a public runtime value, type constructor, syntax form, helper, or Core IR node.
- In this phase, only lists and Flow are Seq-compatible public values.
- Lists are eager and reusable.
- Flow is lazy, pull-based, source-bound, and single-use.
- Iterators and generators are host implementation details, not portable Genia values.
- Python reference-host internal lifecycle helpers for Seq-compatible sources must not create a public Seq surface.
- Seq compatibility does not change pipeline call shape.
- Seq compatibility does not change Option-aware pipeline behavior.
- No implicit list-to-Flow conversion is introduced.
- No implicit Flow-to-list conversion is introduced.
- Matching a Flow as a list requires explicit materialization first.
- `_seq_transform(initial_state, step, source)` is a kernel primitive over Seq-compatible public sources:
  - `source` must be a list or Flow
  - list sources return lists; Flow sources return Flows
  - `step` is called as `step(state, item)`
  - `step` must return a map with optional `state`, `emit`, and `halt`
  - omitted `state` keeps the current state; omitted `emit` defaults to `[]`; omitted `halt` defaults to `false`
  - `emit` must be a list and emits zero, one, or many values in order
  - `halt: true` emits the current result and stops the whole transform without pulling later source items
  - invalid result shape, invalid `emit`, and invalid `halt` raise runtime errors prefixed with `invalid-seq-transform-result:`
- `_seq_transform` must not introduce syntax, a Core IR node, a public Seq value/type/helper, implicit list-to-Flow conversion, or implicit Flow-to-list conversion.

## `rules(..fns)`

`rules(..fns)` is a Flow-stage function that applies rule functions to each incoming flow item.

It is a library/runtime abstraction, not special syntax.

### Rule shape

Each rule must be a function with the shape:

```genia
(record, ctx) -> none(...) | some(result)
```

Plain `none` is also valid and means the same no-effect result as `none(reason)` / `none(reason, context)`.

Where `result` is a map that may contain:

* `emit`: a list of values to emit to the output flow
* `record`: a replacement current record for subsequent rules on the same input item
* `ctx`: a replacement running context carried to later rules and later input items
* `halt`: when true, stop evaluating remaining rules for the current input item

### Defaults

If a matching rule returns `some(result)` and a field is missing:

* `emit` defaults to `[]`
* `record` defaults to the current record unchanged
* `ctx` defaults to the current ctx unchanged
* `halt` defaults to `false`

### Evaluation semantics

The running `ctx` starts as `{}` before the first input item.

For each input item:

1. Initialize `record` to the current input item
2. Reuse the current running `ctx`
3. Evaluate rules from left to right
4. If a rule returns `none(...)` (including plain `none`), it has no effect
5. If a rule returns `some(result)`:

   * append `result.emit` to the output stream
   * replace `record` if `result.record` is present
   * replace `ctx` if `result.ctx` is present
   * stop evaluating later rules for this item if `result.halt` is true
6. After the last applicable rule, continue to the next input item using the final `ctx`

### Output semantics

A single input item may produce:

* zero output values
* one output value
* many output values

`rules(..fns)` may therefore filter, transform, expand, or suppress items.

### Identity case

`rules()` with zero rules acts as an identity flow stage.

### Errors

It is a runtime error if:

* a rule does not return `none(...)` or `some(...)`
* a matching rule returns `some(result)` where `result` is not a map-like structure
* `emit` is present but is not a list
* `halt` is present but is not a boolean

Rule-contract violations raise runtime errors prefixed with `invalid-rules-result:` so tooling can detect them reliably.

### Notes

* `rules(..fns)` works on any incoming flow, not only `stdin`
* `rules(..fns)` does not change the semantics of `|>`
* `record` is the current item being transformed
* `ctx` is persistent rule-processing state across items
* in this phase, the host runtime keeps the lazy Flow kernel while `src/genia/std/prelude/flow.genia` handles most user-visible rule semantics
* the host rules kernel expects normalized prelude output with `emit` and `ctx` already present

## `keep_some_else(stage, dead_handler[, flow])`

`keep_some_else(...)` is an explicit Flow-stage helper for Option-returning stages.

It is a library/runtime abstraction, not special syntax.

### Evaluation semantics

For each incoming flow item `x`:

1. Evaluate `stage(x)`
2. If the result is `some(v)`:
   * emit `v` on the main output flow
3. If the result is `none(...)`:
   * emit nothing on the main output flow for that item
   * call `dead_handler(x)` with the original input item
4. If the result is not an Option:
   * raise a clear user-facing error

### Notes

* this helper is explicit local dead-letter routing
* it does not change the semantics of `|>`
* ordinary pipelines still preserve `none(...)` short-circuit and metadata
* `dead_handler` is a handler call, not a second live flow output in this phase
* `none`, `none(reason)`, and `none(reason, meta)` are all treated as dead-letter results

## 20) Output sink invariants (host-backed phase 1)

- `display` and `debug_repr` are the first concrete public entry points of the planned Representation System (#166)
- these names must be treated as Representation System surface area, not standalone utility helpers
- `display(value)` and `debug_repr(value)` return strings and must not write to `stdout` or `stderr`
- output operations remain separate:
  - `print(...)` writes to `stdout`
  - `log(...)` writes to `stderr`
  - `write(sink, value)` and `writeln(sink, value)` write to explicit sinks
- #185 must not define the full Representation System
- #166 owns the broader representation model, naming boundaries beyond `display` / `debug_repr`, extension points, user-defined representations, registry/strategy behavior, and cross-host handling of opaque runtime values
- #185 must not introduce alternate public representation terminology such as `render`, `view`, or `repr`
- if #166 later changes the canonical names, #185 behavior must migrate through the alias-safe rename sequence: introduce alias, migrate usage incrementally, update tests, then remove the old name later

- `stdout` and `stderr` are runtime capability values, not parser syntax
- public sink helper names are exposed through thin prelude wrappers in `src/genia/std/prelude/io.genia`
- those wrappers are the canonical user-facing API surface for `help(...)` and higher-order use
- underlying sink behavior remains host-backed in this phase; wrappering does not change semantics
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
- pipe mode wraps the provided source exactly as `stdin |> lines |> <stage_expr> |> run`
- the provided source must be a single stage expression
- explicit `stdin` and explicit `run` in pipe mode are rejected with a clear error
- pipe mode diagnostics should stay Genia-facing rather than exposing internal IR/runtime node names
- if a user gives a value helper or reducer where a Flow stage is expected, the error should point toward Flow stages such as `map(...)`, `filter(...)`, `each(...)`, `keep_some(...)`, or toward `-c` / file mode for final value reducers such as `sum` / `count`
- ordinary `-c` command mode remains unchanged and evaluates exactly what the user wrote
- pipe mode bypasses the `main` convention; file mode and `-c` mode keep existing `main/1` then `main/0` behavior
- pipeline operator semantics are unchanged; this does not add a new operator or runtime meaning for `|>`
