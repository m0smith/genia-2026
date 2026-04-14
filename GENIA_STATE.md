# Genia — Current Language State (Main Branch)

This file describes what is **actually implemented now** in the Python runtime.

## 0) Multi-host status

Implemented today:

- Python is the current implemented reference host.
- The working Python implementation still lives in:
  - `src/genia/`
  - `tests/`
  - `src/genia/std/prelude/`
- Multi-host documentation/spec scaffolding now exists in:
  - `docs/host-interop/`
  - `docs/architecture/core-ir-portability.md`
  - `spec/`
  - `tools/spec_runner/README.md`
  - `hosts/`

Scaffolded or planned, not implemented as hosts:

- `hosts/python/` is currently a documentation placeholder for the intended future monorepo layout; it is not the live source location of the Python host today.
- Node.js host
- Java host
- Rust host
- Go host
- C++ host
- generic shared spec runner implementation

Clarifications:

- The new multi-host artifacts are documentation/manifest/layout scaffolding in this phase.
- They do not add a second implemented host yet.
- The shared spec runner contract and capability matrix are scaffolded now, but no generic multi-host runner implementation exists yet.

## 0.1) Browser playground status

Implemented today:

- browser playground architecture and runtime-adapter documentation scaffolding exists under:
  - `docs/browser/README.md`
  - `docs/browser/PLAYGROUND_ARCHITECTURE.md`
  - `docs/browser/RUNTIME_ADAPTER_CONTRACT.md`
- app scaffold documentation exists under:
  - `apps/playground/README.md`

Planned, not implemented yet:

- V1 browser playground app that runs Genia via a backend service using the current Python reference host
- browser-native runtime backend for the playground using either:
  - a JavaScript host, or
  - a Rust/WASM host

Clarifications:

- no browser playground application runtime is implemented in this repository yet
- browser work in this phase is architecture/contract scaffolding only
- browser execution remains a host-capability adaptation concern and does not define a new Genia dialect

## 0.2) Repository documentation publishing workflow

Implemented today:

- repository docs are staged into a temporary MkDocs input tree by `tools/stage_docs_for_mkdocs.py`
- the published docs site uses MkDocs with the Material theme
- published sections include:
  - `README.md` as the homepage
  - `GENIA_STATE.md`
  - `GENIA_RULES.md`
  - `GENIA_REPL_README.md`
  - `docs/book/*`
  - `docs/sicp/*` chapter content
  - `docs/cheatsheet/*`
  - public-facing host interop docs under `docs/host-interop/`
- GitHub Actions docs workflow behavior is:
  - on pull requests: stage, validate, and build docs without deployment
  - on pushes to `main`: stage, validate, build, and deploy to GitHub Pages
- docs validation in this phase includes:
  - strict MkDocs builds
  - semantic doc sync tests for protected cross-doc semantic facts
    - the protected facts surface is intentionally small and lives in `docs/contract/semantic_facts.json`
    - validation covers both public docs and LLM-instruction surfaces
  - cheatsheet validation tests
  - SICP runnable-block validation tests
  - lightweight book chapter status-marker validation

Clarifications:

- the staging tree is a build artifact only; source-of-truth docs remain in their existing repository locations
- the docs workflow is repository tooling, not part of the Genia language/runtime semantics

## 0.3) `@doc` linter (`tools/lint_doc.py`)

Implemented today:

- deterministic linter for `@doc` content strings
- located at `tools/lint_doc.py`; tests at `tests/test_lint_doc.py`
- accepts a raw `@doc` text string via the `lint_doc()` API or CLI
- returns structured `LintFinding` values with `rule_id`, `severity`, `message`, and optional `line`
- CLI modes:
  - inline: `python tools/lint_doc.py "doc string"`
  - file: `python tools/lint_doc.py --file path.genia`
  - directory scan: `python tools/lint_doc.py --scan-dir dir/`
  - all modes support `--json` for machine-readable output
- file/scan modes extract binding names and include them in output
- `--scan-dir` prints a summary (files scanned, doc count, error/warning counts) to stderr

Implemented lint rules (phase 1):

| Rule | ID | Severity | Description |
|---|---|---|---|
| Summary required | DOC001 | error | Every `@doc` must have a non-empty first line |
| Summary shape | DOC002 | warning | Summary should end with `.`/`!`/`?` and avoid boilerplate prefixes |
| Allowed sections | DOC003 | error | Only `## Arguments`, `## Returns`, `## Errors`, `## Notes`, `## Examples` |
| No HTML | DOC004 | error | Raw HTML tags forbidden outside fences |
| No tables | DOC005 | error | Pipe-table markdown forbidden outside fences |
| Behavior mention | DOC006 | warning | `none(`, `flow`, `lazy` should appear in prose, not only in fences |
| Fence sanity | DOC007 | error | Fences must be balanced; `## Examples` fences allow only `genia`, `text`, or empty lang |

Not implemented yet:

- semantic NLP scoring or readability metrics
- public/private marker enforcement (no such marker exists in the language yet)
- cross-reference validation between `@doc` content and function signatures

## 0.4) `@doc` style synchronization tests (`tests/test_doc_style_sync.py`)

Implemented today:

- style guide structure test: validates `docs/style/doc-style.md` has required sections, good/bad examples, and well-formed genia fences
- cheatsheet sync test: validates `docs/cheatsheet/core.md` and `docs/cheatsheet/quick-reference.md` have `@doc Quick Reference` sections with case markers linking back to the style guide
- book sync test: validates `docs/book/03-functions.md` has a `Documenting Functions` section whose allowed headers and Markdown subset are consistent with the style guide
- linter-style guide alignment test: validates that the linter's `ALLOWED_SECTION_HEADERS`, `DISCOURAGED_PREFIXES`, and disallowed Markdown match the style guide
- prelude doc lint sweep: scans all `src/genia/std/prelude/*.genia` files for `@doc` strings and runs the linter over them (currently zero `@doc` strings exist in prelude)

Not implemented yet:

- CI-gate enforcement (tests exist but are not yet wired into a required CI check)
- runnable example execution within the style guide itself (cheatsheet sidecar tests cover runnable examples separately)

Clarifications:

- these are repository tooling tests, not part of the Genia language/runtime semantics
- the linter is repository tooling, not part of the Genia language/runtime semantics
- rules are intentionally conservative and deterministic

## 1) Execution model

- programs are expression sequences
- parser AST stays close to surface syntax, then lowers into a tiny Core IR before evaluation
- Core IR is the current portability boundary
  - lowering keeps pipelines explicit as ordered stage sequences rather than nested calls
  - lowering keeps Option constructors explicit as `IrOptionSome(...)` / `IrOptionNone(...)`
  - the minimal Core IR contract is explicitly frozen in `docs/architecture/core-ir-portability.md`
  - lowered portable IR is validated before host-local optimization in the Python reference host
- the current Python host may apply small post-lowering optimization rewrites such as `IrListTraversalLoop`
  - those optimized nodes are Python-host implementation details, not the minimal shared Core IR contract
- assignment is supported at top level and in lexical scopes (`name = expr`)
- blocks evaluate expressions in order and return the last value
- no statement/declaration split at runtime level
- CLI entry points support three execution modes:
  - file mode: `genia path/to/file.genia`
  - command mode: `genia -c "expr_or_program_source"`
  - pipe mode: `genia -p "stage_expr"` / `genia --pipe "stage_expr"`
  - REPL mode: `genia` (no file/command arguments)
- when no `-c`/`-p` mode is selected, the first non-mode argument must be a source file path (option-like tokens are treated as malformed mode/arg combinations unless passed after `--`)
- in file/command/pipe mode, trailing host CLI arguments are exposed to programs as `argv()` (list of strings)
  - command mode accepts both bare positionals (`a`) and option-like args (`--pretty`) as trailing args
- pipe mode wraps the provided stage expression as `stdin |> lines |> <stage_expr> |> run`
  - pipe mode expects a single stage expression, not a full standalone program
  - explicit unbound `stdin` and explicit unbound `run` are rejected in pipe mode with a clear error
  - per-item functions used as bare stages (e.g. `parse_int`) are diagnosed with targeted suggestions (`map(parse_int)` or `keep_some(parse_int)`)
  - reducers used as bare stages (e.g. `sum`) are diagnosed with `collect |> sum` or `-c/--command` guidance
  - non-flow final results (e.g. from `collect`) are reported with `-c/--command` guidance
  - broken pipe on stdout exits cleanly with no traceback or stderr noise
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
- Pair
- None / Some (`none`, `some(value)`)
  - `none` is shorthand for `none("nil")`
  - legacy surface `nil` also normalizes to `none("nil")`
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
  - current Python host interop reuses this same module value model:
    - `import python`
    - `import python.json as pyjson`

### Callable values / callable behaviors

- Function values are callable in the ordinary way
- Map values also have callable lookup behavior
  - `m(key)` -> stored value or `none("missing-key", {key: key})`
  - `m(key, default)` -> stored value when key exists, otherwise `default`
- String values can act as callable map projectors
  - `"key"(m)` -> map lookup behavior (`value` or `none("missing-key", {key: key})`)
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
- Ref
  - refs are synchronized host-backed runtime cells
  - `ref_get` / `ref_update` may block until a value is present
- Process
  - `spawn` returns a host-backed process handle value
- Bytes
  - `utf8_encode` and ZIP helpers produce opaque bytes wrapper values
- ZipEntry
  - `zip_entries` returns opaque zip entry wrapper values
- HTTP serving
  - `import web` exposes module exports such as `web/serve_http(config, handler)` for the host-backed blocking HTTP capability
  - requests and responses are represented as ordinary Genia maps at the language boundary
- Python host handles
  - `python/open` returns opaque Python file-handle values (`<python file>`)
  - these are capability-style values intended only for passing back to allowlisted Python host exports

### Current consistency notes

- Maybe/absence behavior is now unified around one explicit family:
  - present value: `some(value)`
  - absence value: `none(reason, meta?)`
  - plain `none` and legacy `nil` both normalize to `none("nil")`
  - compatibility aliases remain where naming migration was staged (`get?`, `first_opt`, `nth_opt`)
  - canonical maybe-aware access/search APIs use structured absence directly (`get`, `first`, `last`, `nth`, string `find`, `find_opt`, `parse_int`)
  - compatibility surfaces such as `map_get`, slash access, callable map/string lookup, and `cli_option` now also return structured `none(...)` on missing results
- structured `none(...)` metadata is still absence metadata, not a separate control-flow family.
- absence metadata is inspectable through:
  - `absence_reason(none(...))` -> `some(reason)`
  - `absence_context(none(...))` -> `some(context)` when present, otherwise `none("nil")`
  - `absence_meta(none(...))` -> `some({reason: ..., context: ...?})`
- `some(pattern)` and `none(...)` patterns are implemented for Option values in pattern matching.
- ordinary function calls short-circuit on `none(...)` arguments unless the callee explicitly handles absence.
- pipelines short-circuit on `none(...)` and automatically lift ordinary stages over `some(...)`.
  - non-Option stage results are wrapped back into `some(...)`
  - Option stage results (`some(...)` / `none(...)`) are preserved as-is
  - explicitly Option-aware stages (for example `unwrap_or`, `map_some`, `flat_map_some`, and `then_*`) still receive Option values directly
- pipeline debugging helpers are implemented as prelude-level identity stages:
  - `inspect(value)` logs and returns `value` unchanged
  - `trace(label, value)` logs `label` plus `value` and returns `value` unchanged
  - `tap(fn, value)` runs `fn(value)` for side effects and returns `value` unchanged
  - these helpers do not force Flow materialization by themselves; they preserve explicit/lazy Flow boundaries unless user-provided side-effect callbacks consume a Flow value
- public Map/Ref/Process/IO helper names are also prelude-backed wrappers over host-backed runtime primitives, so `help("name")` and higher-order use follow the user-facing stdlib surface rather than raw host bindings.
- public Web helper names `serve_http`, `get`, `post`, `route_request`, `response`, `json`, `text`, `ok`, `ok_text`, `bad_request`, and `not_found` are also thin prelude wrappers in this phase; the underlying HTTP transport integration remains host-backed
- public Flow helper names `lines`, `tick` (experimental), `tee`, `merge`, `zip`, `scan`, `keep_some`, `keep_some_else`, `rules`, `each`, `collect`, and `run` are also thin prelude wrappers in this phase; the underlying Flow behavior remains host-backed
- limited Python host interop is implemented in this phase:
  - it uses the existing module/import model rather than new syntax
  - supported host modules are currently allowlisted: `python`, `python.json`
  - unsupported host module names fail clearly instead of falling through to arbitrary host import
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
- The current model is implemented and tested as one integrated design in this phase:
  - Core IR carries explicit pipeline and Option nodes
  - pipeline evaluation owns automatic Option propagation
  - Flow remains an explicit runtime value family rather than an implicit pipeline mode
  - host interop is a narrow capability bridge layered onto the same call/pipeline semantics
- This is still not a full static type/protocol system; the coherence is semantic rather than nominal.

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
  - dotted host module names are supported through ordinary identifiers (for example `import python.json as pyjson`)
- list spread in literals: `[..xs]`, `[1, ..xs, 2]`
- call spread: `f(..xs)`
- lambdas: `(x) -> x + 1`
- varargs lambdas: `(..xs) -> xs`, `(a, ..rest) -> rest`
- prefix annotations are now a usable binding-metadata surface: `@name value`
  - one or more consecutive annotations attach to the next top-level function definition or simple-name assignment
  - parsed annotations produce explicit AST nodes (`Annotation`, `AnnotatedNode`)
  - metadata attachment to bindings is implemented for `@doc`, `@meta`, `@since`, `@deprecated`, and `@category`
  - no macro behavior or compile-time transform behavior is implemented

Pipeline (Phase 2) evaluation model:

- `|>` is a dedicated pipeline stage form in Core IR/runtime in this phase
- Core IR shape is explicit:
  - `x |> f |> g` lowers to one pipeline node with a source plus ordered stages
  - pipelines are not represented as nested call nodes
- ordinary call shape is preserved:
  - `x |> f` calls `f(x)`
  - `x |> f(y)` calls `f(y, x)` (left value appended as the last argument)
  - `x |> expr` calls `expr(x)` when `expr` is valid in ordinary call-callee position
  - example: `record |> "name"` behaves like `"name"(record)`
- left associative: `a |> f |> g`
- newline-separated pipeline formatting is accepted:
  - `x`
    `|> f`
    `|> g`
  - `x |> `
    `f |> g`
- automatic Option propagation is part of pipeline evaluation:
  - if a stage input is `none(...)`, the remaining stages do not execute and the same `none(...)` is returned
  - if a stage input is `some(x)` and the stage is not explicitly Option-aware, the stage receives `x`
  - when a lifted stage returns non-Option `y`, the pipeline continues with `some(y)`
  - when a lifted stage returns `some(...)` or `none(...)`, that Option result is preserved
  - if a stage result is `none(...)`, the remaining stages do not execute and the same `none(...)` is returned
- pipeline failure diagnostics now include:
  - 1-based stage index
  - stage rendering when available
  - stage source span when available
  - pipeline mode classification (`Value mode`, `Flow mode`, or `Explicit bridge mode`)
  - received runtime type names
- pipeline-visible function modes are interpreted as:
  - Value -> Value
  - Flow -> Flow
  - explicit Value <-> Flow bridge
- recovery/defaulting wraps the whole pipeline result rather than living as a later pipeline stage:
  - `unwrap_or("unknown", record |> get("user") |> get("name"))`
  - `unwrap_or(0, fields(row) |> nth(5) |> parse_int)`
- Flow remains explicit:
  - Flow values still come only from explicit bridge/stage functions such as `lines`
  - Value↔Flow conversion is not implicit

## 4) Functions and dispatch

- named functions are first-class values
- multiple definitions by arity shape are allowed
- varargs named functions are supported (`f(a, ..rest) = ...`)
- named functions may use either `=` or `->` for single-expression bodies, or `{ ... }` for block bodies
- bindings may carry metadata maps discoverable through `meta("name")`
- doc lookup is available through `doc("name")`
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
- prefix annotations now attach metadata to bindings in this phase
  - supported built-in annotations are:
    - `@doc "text"` -> stores `{"doc": "text"}`
    - `@meta { ... }` -> merges map entries into binding metadata
    - `@since "0.4"` -> stores `{"since": "0.4"}`
    - `@deprecated "message"` -> stores `{"deprecated": "message"}`
    - `@category "name"` -> stores `{"category": "name"}`
  - annotation metadata attaches to the binding name for top-level functions and top-level assignments
  - unannotated rebinding preserves existing metadata on that binding
  - annotated rebinding merges new metadata over existing metadata, with the last annotation winning for duplicate keys
  - `doc("name")` returns the current doc string or `none("missing-doc", {name: ...})`
  - `help("name")` uses annotation doc text when no legacy function docstring is present and also shows selected metadata fields such as category/since/deprecated
  - no macros, compile-time transforms, or annotation-driven evaluator rewrites are implemented
- resolution behavior:
  - exact fixed arity beats varargs
  - if multiple varargs candidates match and neither is more specific, runtime raises `TypeError("Ambiguous function resolution")`
- slash named accessor (phase 1):
  - `lhs/name` uses narrow named access when RHS is a bare identifier
  - supported LHS runtime kinds: module values, map values
  - map missing key => `none("missing-key", {key: "name"})`
  - module missing export => clear error
  - non-identifier RHS (for example `lhs/(1 + 2)`) raises a clear `TypeError`
  - this does not add general member/index access

## 4.1) Python host interop layer (implemented, allowlisted)

- Genia currently exposes a minimal Python-only host interop layer through the existing module system.
- supported host imports in this phase:
  - `import python`
  - `import python.json`
  - `import python.json as alias`
- current allowlisted exports:
  - `python/open`
  - `python/read`
  - `python/write`
  - `python/close`
  - `python/read_text`
  - `python/write_text`
  - `python/len`
  - `python/str`
  - `python/json/loads`
  - `python/json/dumps`
- host exports participate in ordinary calls and pipeline stages without special pipeline rules.
- boundary conversion rules:
  - Genia string/number/bool -> Python scalar
  - Genia list -> Python list recursively
  - Genia map -> Python dict recursively
  - Genia `some(x)` -> converted host value for `x`
  - Genia `none(...)` -> Python `None`
  - Python `None` -> Genia `none("nil")`
  - Python list/tuple -> Genia list recursively
  - Python dict -> Genia map recursively
- host file objects cross the boundary only as opaque Python handle values.
- current safety limits:
  - no arbitrary host import
  - no general member access syntax
  - no unrestricted Python eval/exec surface
  - disallowed host modules raise `PermissionError("Host module not allowed: <name>")`
- current error behavior:
  - host exceptions remain explicit errors unless the host result is actually `None`
  - `None` maps to Genia `none("nil")` and therefore participates in ordinary call/pipeline absence propagation
  - invalid JSON through `python.json/loads` raises `ValueError("python.json/loads invalid JSON: ...")`
- callable data (phase 1):
  - maps are callable lookup values:
    - `m(key)` returns stored value or `none("missing-key", {key: key})`
    - `m(key, default)` returns stored value when key exists, otherwise `default`
    - arity other than 1 or 2 raises `TypeError`
  - strings are callable map projectors:
    - `"key"(m)` returns `map_get(m, "key")` behavior (`value` or `none("missing-key", {key: key})`)
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
  - `null?(x)` reports whether a value is the normalized empty-pair terminator (`none("nil")`, including legacy `nil`)
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

- Genia now ships a minimal metacircular expression helper layer in `src/genia/std/prelude/syntax.genia`
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

- Genia now ships a minimal metacircular evaluator layer in `src/genia/std/prelude/eval.genia`
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
  - `apply` (extended in `src/genia/std/prelude/fn.genia` to handle metacircular compound procedures as well as ordinary callables)
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

- direct runtime names: `log`, `print`, `input`, `stdin`, `stdin_keys`, `stdout`, `stderr`, `help`
- public sink helpers are thin prelude wrappers in `src/genia/std/prelude/io.genia`:
  - `write`
  - `writeln`
  - `flush`
  - `clear_screen`
  - `move_cursor`
  - `render_grid`
- public web helpers are thin prelude wrappers in `src/genia/std/prelude/web.genia`:
  - `serve_http`
  - `get`
  - `post`
  - `route_request`
  - `response`
  - `json`
  - `text`
  - `ok`
  - `ok_text`
  - `bad_request`
  - `not_found`
- `argv` (returns raw trailing CLI args as a list of strings)
- constants in global env: `pi`, `e`, `true`, `false`, legacy alias `nil`
- pair builtins: `cons`, `car`, `cdr`, `pair?`, `null?`

Output sink semantics:

- `write`, `writeln`, and `flush` are the canonical public sink helper names and carry Markdown docstrings for `help(...)`
- the underlying sink behavior remains host-backed and unchanged in this phase
- `write(sink, value)` writes display-formatted output without a trailing newline and returns `value`
- `writeln(sink, value)` writes display-formatted output with a trailing newline and returns `value`
- `flush(sink)` flushes the sink and returns `none("nil")`
- `clear_screen()` writes ANSI clear/home control codes to `stdout`, flushes, and returns `none("nil")`
- `move_cursor(x, y)` writes an ANSI cursor-position control code to `stdout` and returns `none("nil")`
  - `x` is terminal column, `y` is terminal row
  - both coordinates must be positive integers
- `render_grid(grid)` writes a text grid to `stdout` and returns `grid`
  - `grid` must be a list
  - each row must be either a string or a list of displayable values
- `web/serve_http(config, handler)` runs a synchronous blocking HTTP server and returns `{host, port, handled_requests}` after the server stops
  - `config.host` defaults to `"127.0.0.1"`
  - `config.port` defaults to `8000`
  - optional `config.max_requests` stops the server after a fixed number of handled requests
  - request maps currently include:
    - `method`
    - `path`
    - `query` (string-keyed map; repeated query keys keep the last value)
    - `headers` (lowercased string-keyed map)
    - `body` (parsed JSON when content type starts with `application/json`, otherwise decoded text)
    - `raw_body` (decoded text body)
    - `client` (`{host, port}`)
  - response maps currently use:
    - `status` (integer)
    - `headers` (string-keyed map)
    - `body` (string, bytes, or `none`)
  - invalid handler return values or response-shape errors produce a `500 internal server error` response in this phase
- `print(...)` writes to `stdout`
- `log(...)` writes to `stderr`
- `input()` remains interactive-only and does not consume the flow/stdin source path
- broken pipe on `stdout` output is treated as normal downstream termination in CLI/file/command execution (no Python traceback)
- flow-driven stdout writes use the same quiet broken-pipe path, so Unix pipelines can stop downstream early without noisy Python tracebacks
- broken pipe on `stderr` is handled best-effort and does not trigger recursive noisy failures
- on Windows console streams, `clear_screen` and `move_cursor` try to enable virtual terminal processing before writing ANSI control codes

### Flow runtime (Phase 1)

- `stdin` is a lazy source value when used in pipelines (`stdin |> lines`)
  - `stdin |> lines` reads incrementally from the underlying source
  - `stdin()` still materializes and caches the full remaining input as a list for compatibility
- `stdin_keys` is a lazy real-time keypress Flow source (`stdin_keys |> ...`)
  - emits one keypress item at a time without waiting for newline in interactive terminal mode
  - remains single-use like other Flow values
  - in non-interactive stdin contexts, falls back to character-by-character input reads
  - existing `stdin |> lines` behavior is unchanged
- public flow helpers are thin prelude wrappers in `src/genia/std/prelude/flow.genia`:
  - `lines`
  - `tick` (experimental)
  - `tee`
  - `merge`
  - `zip`
  - `scan`
  - `keep_some_else`
  - `rules`
  - `each`
  - `collect`
  - `run`
  - `rules` orchestration, defaulting, and contract validation now primarily live in prelude/Genia code
- flow transforms:
  - `lines(flow_or_source)`
  - `tick()` (unbounded integer tick flow starting at `0`)
  - `tick(count)` (bounded integer tick flow from `0` to `count - 1`)
  - `tee(flow)`
  - `merge(flow1, flow2)` and `merge(pair)` where `pair` comes from `tee(flow)`
  - `zip(flow1, flow2)` and `zip(pair)` where `pair` comes from `tee(flow)`
  - `scan(step, initial_state, flow)` / `flow |> scan(step, initial_state)`
  - `keep_some_else(stage, dead_handler, flow)` / `flow |> keep_some_else(stage, dead_handler)`
  - `map(f, flow)` / `filter(pred, flow)` when second arg is a flow
  - `take(n, flow)` when second arg is a flow
  - `rules(..fns, flow)` / `flow |> rules(..fns)` as a stateful rule-driven transform
  - `head(flow)` and `head(n, flow)` via stdlib aliases over `take`
- flow sinks/materialization:
  - `each(f, flow)` (tap-style stage)
  - `collect(flow)` (materialize to list)
  - `run(flow)` (consume to completion)
- stdlib rule helpers (autoloaded from `src/genia/std/prelude/fn.genia`):
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
- `tee` keeps one shared upstream flow and only buffers as needed when branch consumption rates diverge
- `merge` preserves input ordering (`flow1` items, then `flow2` items)
- `zip` emits lockstep `[left, right]` pairs and stops when either input flow is exhausted
- `take` performs early termination (stops upstream pulling as soon as limit is reached, without over-pulling one extra item)
- `tick` provides deterministic discrete step progression for simulation-style pipelines while preserving the same explicit/lazy/single-use Flow contract
- short-circuiting flow consumers such as `take`, `head`, and downstream broken-pipe termination stop generator-backed upstream work promptly
- `scan` is a per-flow stateful transform where `step(state, item)` must return `[next_state, output]`
- `scan` keeps state internal to the operator while emitting one output item per input item
- invalid flow-source misuse fails with clear Genia-facing runtime errors instead of leaked Python iterator errors
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
  - rule orchestration, defaulting of omitted fields, and most contract checking are implemented in `src/genia/std/prelude/flow.genia` in this phase
- `keep_some_else` semantics:
  - it is an explicit Flow-stage helper for Option-returning per-item stages
  - for each input item `x`, it evaluates `stage(x)`
  - `stage(x)` receives the original raw input item, not `some(x)`
  - `some(v)` emits `v` on the main output flow
  - `none(...)` emits nothing on the main flow for that item and calls `dead_handler(x)` with the original input item
  - if `stage(x)` does not return `some(...)` or `none(...)`, it raises a clear user-facing error
  - this helper is local dead-letter routing only; it does not change global `|>` semantics or create a second live output flow
- `keep_some` semantics:
  - `keep_some(flow)` expects upstream Option items
  - `keep_some(stage, flow)` applies an Option-returning stage per item
  - `some(v)` is unwrapped to `v` inside this helper
  - `none(...)` is dropped inside this helper
- explicit CLI pipe mode is implemented:
  - `genia -p "<stage_expr>"` / `genia --pipe "<stage_expr>"`
  - wraps as `stdin |> lines |> <stage_expr> |> run`
  - no `pipe(...)` helper function exists in this phase
  - pipe mode expects one stage expression, not a full program
  - explicit `stdin` is rejected because pipe mode provides it automatically
  - explicit `run` is rejected because pipe mode runs the final flow automatically
  - if the stage expression does not produce a flow for the automatic final `run`, pipe mode reports a clear user-facing error
  - if a pipe-mode stage helper receives the whole Flow when it expected per-item values, pipe mode reports clear guidance to use Flow stages such as `map(...)`, `filter(...)`, `each(...)`, `keep_some(...)`, or to switch to `-c` / `--command` for reducers such as `sum`
  - common `some(...)` pipeline mismatches in pipe mode keep the original type error but use Genia-facing stage rendering (for example `some(1)`) instead of leaking internal IR node names

### CLI argument helpers (prelude-backed over raw argv + tiny host validation primitives)

- `cli_parse(args) -> [opts, positionals]`
- `cli_parse(args, spec) -> [opts, positionals]`
- `cli_flag?(opts, name) -> bool`
- `cli_option(opts, name) -> value | none("missing-key", {key: name})`
- `cli_option_or(opts, name, default) -> value`

Behavior:

- `argv()` remains the raw host-backed CLI primitive and returns list-first data intended for normal pattern matching
- public CLI helper names are thin prelude wrappers in `src/genia/std/prelude/cli.genia`
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

- public ref helpers are thin prelude wrappers in `src/genia/std/prelude/ref.genia`
  - `ref([initial])`
  - `ref_get(ref)`
  - `ref_set(ref, value)`
  - `ref_is_set(ref)`
  - `ref_update(ref, updater)`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying ref behavior remains host-backed and unchanged in this phase

Behavior: refs are synchronized host objects; `ref_get` / `ref_update` block until value is set when created via `ref()`.

### Host-backed concurrency

- public process helpers are thin prelude wrappers in `src/genia/std/prelude/process.genia`
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

### Actor helpers (Phase 1, prelude-backed over cells)

- public prelude helpers in `src/genia/std/prelude/actor.genia`:
  - `actor(initial_state, handler)`
  - `actor_send(actor, msg)`
  - `actor_call(actor, msg)`
  - `actor_alive?(actor)`
- host-backed helpers:
  - `_actor_validate_effect` validates the handler effect shape for fire-and-forget sends
  - `_actor_call_update` handles handler invocation, effect validation, reply delivery, and error recovery for synchronous calls

Behavior:

- `actor(initial_state, handler)` creates an actor backed by a cell
  - the handler shape is `handler(state, msg, ctx) -> effect`
  - the actor is represented as a map with internal `_cell` and `_handler` keys
- supported effect shapes:
  - `["ok", new_state]` — update state only
  - `["reply", new_state, response]` — update state and deliver a response value
- `actor_send(actor, msg)` enqueues the message for asynchronous processing
  - the handler is called with `(current_state, msg, {})` inside a cell update
  - the handler may return either `["ok", new_state]` or `["reply", new_state, response]`
  - for `actor_send`, any response value from a `["reply", ...]` effect is discarded
  - messages are processed one at a time in FIFO order
- `actor_call(actor, msg)` sends a message and blocks until the handler replies
  - a one-shot ref is created and passed in `ctx` as `reply_to`
  - the handler is called with `(current_state, msg, {reply_to: <ref>})`
  - for `["reply", new_state, response]`: the caller receives `response`
  - for `["ok", new_state]`: the caller receives `new_state` as the reply
  - if the handler throws, the caller receives `none("actor-error")` and the actor enters failed state
  - the same handler works correctly with both `actor_send` and `actor_call`
- `actor_alive?(actor)` reports whether the backing cell worker thread is alive
- failure semantics are inherited from the backing cell:
  - handler exceptions or invalid effect shapes mark the actor as failed
  - subsequent `actor_send` raises `RuntimeError` after failure
  - `actor_call` on a failing handler returns `none("actor-error")` instead of blocking
  - failed state is preserved until the backing cell is restarted (no public restart API for actors in this phase)
- actors are a thin convenience layer; internal cell state is accessible through the actor map for advanced use in this phase

Not implemented yet:

- `actor_stop` (graceful shutdown)
- supervision / links / monitors
- actor-specific syntax

### Host-backed persistent associative maps (Phase 1 bridge)

- public map helpers are thin prelude wrappers in `src/genia/std/prelude/map.genia`
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
- `map_get` returns stored value or `none("missing-key", {key: key})` when key is missing
- `map_has?` returns `true`/`false`
- `map_count` returns entry count
- list keys are supported by stable structural key-freezing in runtime
- tuple keys are supported by the same runtime key-freezing strategy (runtime-level interop values)
- invalid map arguments and unsupported key types raise clear `TypeError`

### Primitive Option model (Phase 3 canonical access surface on runtime-backed values)

- option values:
  - `none`
  - `none(reason)`
  - `none(reason, context)`
  - `some(value)`
- public option helpers are thin prelude wrappers in `src/genia/std/prelude/option.genia`
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
  - `parse_int(string)`
  - `parse_int(string, base)`

Absence semantics:

- `some(value)` means present.
- `none`, `none(reason)`, and `none(reason, context)` are one absence family.
- `none` is shorthand for `none("nil")`.
- legacy surface `nil` also evaluates to `none("nil")`; there is no separate runtime nil value.
- `reason` must be a string.
- `context` / metadata must be a map when present.
- reason/context metadata does not create a new success/failure category.
- absence is not the same as a runtime error.
- helpers treat all `none...` forms as absence.
- `parse_int` uses `none("parse-error", context)` for invalid integer text instead of raising for ordinary parse failure
- ordinary function calls short-circuit on `none(...)` arguments unless the callee explicitly handles absence
- a present key whose stored value is legacy `nil` now appears as `some(none("nil"))`

`get?` semantics:

- `get(key, target)` is the canonical maybe-aware lookup helper in this phase
- `get?(key, target)` remains as a compatibility alias with the same runtime behavior
- `get?(key, none) -> none`
- `get?(key, none(reason)) -> none(reason)`
- `get?(key, none(reason, context)) -> none(reason, context)`
- `get?(key, some(map)) -> get?(key, map)`
- `get?(key, map) -> some(value)` when key exists (including `value = none("nil")`)
- `get?(key, map) -> none("missing-key", { key: key })` when key is missing
- unsupported target types raise clear `TypeError`

Maybe-flow helper semantics:

- they remain useful for:
  - explicit Option values outside pipeline position
  - higher-order composition
  - places where wrap-vs-flat-map behavior is the actual intent
  - pipeline stages that need the inner value of `some(...)`
- `map_some(f, some(x)) -> some(f(x))`
- `map_some(f, none(...)) -> none(...)` unchanged
- `map_some(f, some(x))` calls `f(x)` with the inner raw value only at that explicit helper boundary
- `flat_map_some(f, some(x)) -> f(x)` and requires `f(x)` to be an Option value
- `flat_map_some(f, none(...)) -> none(...)` unchanged
- `flat_map_some(f, some(x))` calls `f(x)` with the inner raw value only at that explicit helper boundary
- `then_get(key, target)` is a thin maybe-aware chaining helper:
  - `then_get(key, map) -> get(key, map)`
  - `then_get(key, some(map)) -> get(key, map)`
  - `then_get(key, none(...)) -> none(...)` unchanged
- `then_first(target)` is a thin maybe-aware chaining helper over raw list / `some(list)` / `none(...)`
- `then_nth(index, target)` is a thin maybe-aware chaining helper over raw list / `some(list)` / `none(...)`
- `then_find(needle, target)` is a thin maybe-aware chaining helper over raw string / `some(string)` / `none(...)`
- `or_else_with(opt, thunk)` is recovery/defaulting:
  - returns wrapped value for `some(value)`
  - calls `thunk()` only for `none...`
- `or_else(opt, fallback)` and `or_else_with(opt, thunk)` are direct recovery helpers over explicit Option values
- these helpers preserve structured absence reason/context during propagation unless they are explicitly recovery/defaulting helpers

Developer-facing rendering and introspection:

- REPL result display and debug-oriented formatting preserve structured absence syntax directly:
  - `none("nil")`
  - `none("empty-list")`
  - `none("index-out-of-bounds", {index: 8, length: 2})`
  - `none("missing-key", {key: "name"})`
  - `some(3)`
  - `some(none("nil"))`
- structured absence context is rendered structurally in debug/display output; it is no longer collapsed to `<map N>` in these tooling-facing paths
- `some?` / `none?` are the short predicate names; `is_some?` / `is_none?` remain supported aliases with the same runtime behavior
- `absence_reason(opt)` and `absence_context(opt)` are the canonical inspection helpers for structured absence metadata
- because plain `none` normalizes to `none("nil")`, `absence_reason(none)` returns `some("nil")`
- `absence_context(none)` returns `none("nil")`
- public evaluator result boundaries normalize raw host `None` to `none("nil")`, including empty top-level program results returned through `run_source(...)`
- both `none` and legacy `nil` render as `none("nil")`

Pipeline note:

- pipelines are now Option-aware directly
- canonical safe-chaining style is now:
  - `record |> get("user") |> get("address") |> get("zip")`
  - `data |> get("items") |> then_nth(0) |> then_get("name")`
  - `data |> get("users") |> then_first() |> then_get("email")`
- canonical recovery wraps the pipeline result:
  - `unwrap_or("unknown", record |> get("user") |> get("name"))`
  - `unwrap_or(0, fields(row) |> nth(5) |> parse_int)`
- pipelines now lift ordinary stages over `some(...)`; use `map_some` / `flat_map_some` when you need explicit wrap-vs-flat-map control
- reducers remain explicit:
  - `sum(xs)` expects a plain list of numbers
  - `sum` rejects raw Option items with a clear error instead of relying on accidental arithmetic with `some(...)` / `none(...)`
  - flow/value parse pipelines should therefore use `keep_some(...)`, `keep_some_else(...)`, or per-item `unwrap_or(...)` before `collect |> sum`
- explicit helpers such as `map_some`, `flat_map_some`, and `then_*` remain available for direct Option values and higher-order/non-pipeline composition

Structured absence currently used in canonical access/search helpers:

- `first([]) -> none("empty-list")`
- `last([]) -> none("empty-list")`
- `find(string, needle) -> none("not-found", { needle: needle })` when missing
- `find_opt(pred, xs) -> none("no-match")` when no element matches
- `nth(i, xs) -> none("index-out-of-bounds", { index: i, length: n })` when out of range
- `map_get(map, key) -> none("missing-key", {key: key})` when key is missing
- `cli_option(opts, name) -> none("missing-key", {key: name})` when the option is absent

Absence migration status:

| API | Status | Present result | Missing result | Notes |
| --- | --- | --- | --- | --- |
| `get` | canonical | `some(value)` | `none("missing-key", { key: key })` | preferred map lookup |
| `get?` | compatibility alias | `some(value)` | `none("missing-key", { key: key })` | retained naming exception |
| `first` | canonical | `some(value)` | `none("empty-list")` | list head access |
| `first_opt` | compatibility alias | `some(value)` | `none("empty-list")` | alias for `first` |
| `last` | canonical | `some(value)` | `none("empty-list")` | list tail access |
| `nth` | canonical | `some(value)` | `none("index-out-of-bounds", { ... })` | zero-based list indexing |
| `nth_opt` | compatibility alias | `some(value)` | `none("index-out-of-bounds", { ... })` | alias for `nth` |
| `find` | canonical string search | `some(index)` | `none("not-found", { needle: needle })` | string search only |
| `find_opt` | canonical predicate-search helper | `some(value)` | `none("no-match")` | list predicate search |
| `map_get` | compatibility surface | raw value | `none("missing-key", { key: key })` | use `get` in new code |
| callable map lookup `m(key)` | compatibility surface | raw value | `none("missing-key", { key: key })` | use `get` in new code |
| string projector lookup `"key"(m)` | compatibility surface | raw value | `none("missing-key", { key: key })` | use `get` in new code |
| map slash access `m/name` | compatibility surface | raw value | `none("missing-key", { key: key })` | keep for compatibility; prefer `get("name", m)` |
| `cli_option` | canonical CLI lookup | raw value | `none("missing-key", { key: name })` | use `cli_option_or` for defaults |

Compatibility note:

- legacy `nil` surface syntax remains accepted, but it normalizes immediately to `none("nil")`
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
  - direct Option-aware pipelines such as `record |> get("user") |> get("name")`
  - explicit chaining helpers such as `then_first`, `then_nth`, and `flat_map_some(...)` when the next stage expects the inner value of `some(...)`
  - outer recovery with `unwrap_or(...)` / `or_else(...)`
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
- public string helpers are thin prelude wrappers in `src/genia/std/prelude/string.genia`
  - these wrappers are the canonical user-facing API surface and carry Markdown docstrings for `help(...)`
  - the underlying runtime behavior remains host-backed and unchanged in this phase

`parse_int` behavior:

- `parse_int(string)` returns `some(int)` or `none("parse-error", context)`
- `parse_int(string, base)` does the same with explicit base `2..36`
- surrounding whitespace is ignored
- leading `+` / `-` is supported
- invalid integer text returns structured absence
- non-string input raises clear `TypeError`
- invalid base type raises clear `TypeError`
- out-of-range base raises clear `ValueError`
- non-string input raises clear `TypeError`
- invalid base type raises clear `TypeError`
- out-of-range base raises clear `ValueError`

### Bytes / JSON / ZIP bridge builtins (Phase 1, host-backed)

- `utf8_decode(bytes) -> string`
- `utf8_encode(string) -> bytes`
- internal JSON bridge primitives: `_json_parse(string) -> value|none`, `_json_stringify(value) -> string|none`
- public JSON helpers from `src/genia/std/prelude/json.genia`:
  - `json_parse(string) -> value | none("json-parse-error", context)`
  - `json_stringify(value) -> string | none("json-stringify-error", context)`
  - `json_pretty(value) -> string | none(...)` (compatibility alias)
- internal file/zip bridge primitives: `_read_file(path)`, `_write_file(path, text)`, `_zip_read(path)`, `_zip_write(path, items)`
- public file/zip helpers from `src/genia/std/prelude/file.genia`:
  - `read_file(path) -> string | none(...)`
  - `write_file(path, string) -> path | none(...)`
  - `zip_read(path) -> flow | none(...)`
  - `zip_write(path, flow_or_list) -> path | none(...)`
  - `zip_write(path)` stage form returns a pipeline stage `(items) -> zip_write(path, items)`
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
- `json_stringify`/`json_pretty` emit deterministic pretty JSON with 2-space indentation and sorted object keys
- JSON parse/stringify failures return structured `none(...)` metadata rather than raising parse/stringify exceptions
- `zip_read` is lazy and returns Flow items shaped as `[filename, bytes]`
- `zip_write` consumes a Flow (or list) of `[filename, bytes|string]` items
- file/zip parse/write/read failures return structured `none(...)` metadata for the new prelude API surface
- this is a minimal host-backed bridge and is **not** the full flow system

### Simulation primitives (Phase 2)

- public prelude-backed randomness helpers:
  - `rng(seed)`
  - `rand()`
  - `rand(rng_state)`
  - `rand_int(n)`
  - `rand_int(rng_state, n)`
- `sleep(ms)`

Behavior:

- `rng(seed)` returns an opaque explicit RNG value; seed must be a non-negative integer
- `rand()` returns a float in `[0, 1)` using host RNG convenience randomness
- `rand(rng_state)` returns `[next_rng_state, float]` using a deterministic explicit RNG sequence
- `rand_int(n)` returns an integer in `[0, n)` using host RNG convenience randomness
- `rand_int(rng_state, n)` returns `[next_rng_state, int]` using the same deterministic explicit RNG sequence; the integer is always in `[0, n)`
- the explicit seeded RNG uses a simple 32-bit LCG so the same seed yields the same sequence on the current Python host
- `rand_int(...)` raises clear `TypeError` for non-integer `n` and `ValueError` for `n <= 0` in both convenience and seeded forms
- `sleep(ms)` blocks current execution for `ms` milliseconds; raises clear `TypeError` for non-numeric values and `ValueError` for negative values

## 7) Autoloaded stdlib

Autoload is keyed by `(name, arity)` and currently registers functions from bundled stdlib sources:

- `src/genia/std/prelude/list.genia`
- `src/genia/std/prelude/fn.genia`
- `src/genia/std/prelude/map.genia`
- `src/genia/std/prelude/ref.genia`
- `src/genia/std/prelude/process.genia`
- `src/genia/std/prelude/io.genia`
- `src/genia/std/prelude/random.genia`
- `src/genia/std/prelude/option.genia`
- `src/genia/std/prelude/string.genia`
- `src/genia/std/prelude/json.genia`
- `src/genia/std/prelude/file.genia`
- `src/genia/std/prelude/math.genia`
- `src/genia/std/prelude/awk.genia`
- `src/genia/std/prelude/cell.genia`
- `src/genia/std/prelude/actor.genia`

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
- io: `write`, `writeln`, `flush`, `clear_screen`, `move_cursor`, `render_grid`
- randomness: `rng`, `rand`, `rand_int`
- flow: `lines`, `tee`, `merge`, `zip`, `scan`, `rules`, `each`, `collect`, `run`
- option: `some`, `none?`, `some?`, `get`, `get?`, `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`, `or_else`, `or_else_with`, `unwrap_or`, `absence_reason`, `absence_context`, `is_some?`, `is_none?`
- string: `byte_length`, `is_empty`, `concat`, `contains`, `starts_with`, `ends_with`, `find`, `split`, `split_whitespace`, `join`, `trim`, `trim_start`, `trim_end`, `lower`, `upper`, `parse_int`
- syntax: `self_evaluating?`, `symbol_expr?`, `tagged_list?`, `quoted_expr?`, `quasiquoted_expr?`, `assignment_expr?`, `lambda_expr?`, `application_expr?`, `block_expr?`, `match_expr?`, `text_of_quotation`, `assignment_name`, `assignment_value`, `lambda_params`, `lambda_body`, `operator`, `operands`, `block_expressions`, `match_branches`, `branch_pattern`, `branch_has_guard?`, `branch_guard`, `branch_body`
- metacircular evaluator: `empty_env`, `lookup`, `define`, `set`, `extend`, `eval`
- math: `inc`, `dec`, `mod`, `abs`, `min`, `max`, `sum`
- awk: `fields`, `awkify`, `awk_filter`, `awk_map`, `awk_count`
- cell: `cell`, `cell_with_state`, `cell_send`, `cell_get`, `cell_state`, `cell_failed?`, `cell_error`, `restart_cell`, `cell_status`, `cell_alive?`
- actor: `actor`, `actor_send`, `actor_call`, `actor_alive?`
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
- expressions: literal, explicit Option some/none, variable, call, pipeline, unary, binary, lambda, block, list, map, spread, case
- patterns: wildcard, variable, literal, tuple, list, map, final rest
- function docstrings are carried as metadata on named-function definitions (not runtime expressions)
- Python may add specialized optimized execution nodes after lowering for narrow cases such as `IrListTraversalLoop`
  - these optimized nodes are not the minimal Core IR portability contract

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

- general unrestricted host interop / FFI layer
- general member access syntax
- index syntax
- generalized flow runtime semantics beyond the current phase (async scheduling, advanced backpressure/cancellation, configurable multi-port stages)
- full Flow system (stages/sinks/backpressure/multi-port pipelines)
- language-level scheduler/selective receive/timeouts (concurrency remains host-primitive based)

## 11) Example demos shipped in-repo

- `examples/tic-tac-toe.genia`: interactive text game example
- `examples/ants.genia`: pure deterministic ants colony simulation demo with optional CLI seed for reproducible runs
- `examples/ants_terminal.genia`: terminal-rendered wrapper over the same colony simulation with CLI-configurable ant count and optional CLI seed

`examples/ants.genia` intentionally uses only currently implemented features:

- ordinary persistent maps/lists for explicit world, cell, and ant state
- explicit seeded randomness via `rng(seed)` plus `rand_int(rng_state, n)` for reproducible weighted movement choice
- world-owned RNG threading through `step(world) -> world2`
- recursive stepping over ants and simulation ticks
- `sleep` for blocking frame delay
- text rendering via `print`

Implemented colony behavior in this phase:

- nest/home region tracking
- food pickup with decremented food quantity
- return-to-nest delivery with delivered-food counting
- pheromone deposit on return paths
- pheromone evaporation each tick
- direction-aware candidate moves with weighted seeded choice

It is intentionally pure and explicit. It is **not** actor-based, does **not** add a scheduler, and does **not** introduce hidden mutable runtime state or new language syntax.

`examples/ants_terminal.genia` intentionally stays within the same current runtime surface:

- imports and renders the same pure colony simulation helpers from `examples/ants.genia`
- sequential multi-ant stepping with the same nest/food/pheromone/weighted-movement semantics as the tested ants helpers
- terminal rendering via `clear_screen()`, `move_cursor(x, y)`, and `render_grid(grid)`
- CLI configuration via `main(argv())` plus `cli_parse`
- explicit seeded randomness via `rng(seed)` plus `rand_int(rng_state, n)` for reproducible setup and movement

It is still a blocking terminal demo. It does **not** use `stdin_keys`, does **not** introduce a real-time event loop, and does **not** add new language/runtime features.
