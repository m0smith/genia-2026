# Chapter 03: Functions

## The Smallest Example

```genia
inc(x) = x + 1
```
Classification: **Likely valid** (not directly tested)

Named functions are values and dispatch by name + arity shape.
Single-expression named functions may currently use either `=` or `->` bodies.
Docstrings still use the `=` form only.

Ordinary call syntax also supports a small callable-data subset:

- maps: `m(key)` / `m(key, default)`
- string projectors over maps: `"key"(m)` / `"key"(m, default)`
- in arity-2 forms, the second argument is used only when the key is missing
- string projector calls raise a clear `TypeError` when the first argument is not a map-like runtime map value

These callable lookup forms are still supported, but they are no longer the preferred teaching style for new code.

Prefer:

```genia
get("name", person)
```

over:

```genia
person("name")
"name"(person)
person/name
```

This means Genia's current callable story is behavior-based, not one flat nominal "callable type":

- functions and lambdas are ordinary callable values
- maps remain map values even when called for lookup
- strings remain string values even when used as map projectors

No other callable-data forms are implemented in this phase.

---

## Lexical Assignment

Assignment uses the existing `name = expr` surface syntax.

### Status

✅ Implemented

- top-level assignment
- lexical assignment inside blocks
- nearest-binding rebinding through lexical scope chains
- assignable function parameters
- closure-visible rebinding

⚠️ Partial

- assignment is limited to simple names
- lexical rebinding is most practical in blocks and block-bodied functions
- builtin/root names are not protected from rebinding inside the same root environment

❌ Missing

- destructuring assignment
- map/list/pair field assignment
- pair mutation (`set-car!`, `set-cdr!`)

### Minimal example

```genia
{
  x = 1
  x = 2
  x
}
```
Classification: **Likely valid** (not directly tested)

This evaluates to `2`.

### Edge case: closures see rebinding

```genia
make_counter() = {
  n = 0
  () -> {
    n = n + 1
    n
  }
}

c = make_counter()
[c(), c(), c()]
```
Classification: **Likely valid** (not directly tested)

This evaluates to `[1, 2, 3]`.

### Edge case: nested scopes update the nearest binding

```genia
{
  x = 1
  y = {
    x = 2
    x
  }
  [x, y]
}
```
Classification: **Likely valid** (not directly tested)

This evaluates to `[2, 2]`.

### Failure case

```genia
{
  (1 + 2) = 3
}
```
Classification: **Likely valid** (not directly tested)

This raises:

- `SyntaxError("Assignment target must be a simple name")`

---

## Prefix Annotations

Prefix annotations now attach runtime metadata to top-level bindings.
They remain simple runtime metadata in this phase: no macros, no compile-time transforms, and no syntax rewriting.

### Status

✅ Implemented

- `@name value` prefix annotation syntax
- stacked annotations before a top-level named function definition
- stacked annotations before a top-level assignment
- explicit AST nodes for annotations and annotated targets
- binding metadata attachment for `@doc`, `@meta`, `@since`, `@deprecated`, and `@category`
- `doc("name")` lookup for the current doc string; `@doc` metadata takes priority over legacy inline docstrings
- `meta("name")` introspection for current binding metadata; returns `none("missing-meta", {name: ...})` for undefined names
- `help("name")` display of selected metadata fields; prefers `@doc` metadata over legacy inline docstrings

⚠️ Partial

- supported targets are limited to top-level named functions and top-level assignments
- supported built-in annotations are limited to `@doc`, `@meta`, `@since`, `@deprecated`, and `@category`

❌ Missing

- annotation support on lambdas, imports, or arbitrary expressions
- macro-style annotation behavior
- compile-time transforms

### Minimal example

```genia
@doc "Adds one"
inc(x) -> x + 1
```
Classification: **Likely valid** (not directly tested)

```genia
unwrap_or("missing", meta("inc") |> get("doc"))
```

This evaluates to `"Adds one"`.

```genia
doc("inc")
```

This also evaluates to `"Adds one"`.

### Edge case: stacked annotations

```genia
@doc """
Adds one.
"""
@meta {category: "math"}
@since "0.4"
inc(x) -> x + 1
```
Classification: **Likely valid** (not directly tested)

### Edge case: assignment target

```genia
@meta {category: "math"}
x = 10
```
Classification: **Likely valid** (not directly tested)

```genia
unwrap_or("missing", meta("x") |> get("category"))
```

This evaluates to `"math"`.

### Edge case: rebinding preserves metadata unless new keys override it

```genia
@meta {category: "math", stable: true}
x = 1
x = 2
@meta {stable: false}
x = 3

[unwrap_or("missing", meta("x") |> get("category")), unwrap_or(true, meta("x") |> get("stable"))]
```
Classification: **Likely valid** (not directly tested)

This evaluates to `["math", false]`.

### Best practices

- use `@doc` for the main human-readable description
- use `@category`, `@since`, and `@deprecated` for short discovery-oriented metadata
- prefer `@meta { ... }` when you need multiple custom fields at once
- when duplicate keys appear, the last annotation wins
- keep deprecated messages actionable, for example `@deprecated "Use square2 instead."`

### Failure case

```genia
@doc {text: "bad"}
inc(x) -> x + 1
```
Classification: **Likely valid** (not directly tested)

This raises:

- `TypeError("@doc annotation expected a string, received map")`

Another failure case:

```genia
@doc "Adds one"
1 + 2
```

This raises:

- `SyntaxError("Prefix annotations must be followed by a top-level function definition or simple-name assignment, got ...")`

---

## Documenting Functions

`@doc` is the current annotation-based way to attach lightweight binding metadata for a documented function.
It exists so a public binding can carry a readable contract directly in source without turning into a wall of prose.
Unlike comments, `@doc` is structured metadata that can be surfaced through `help("name")` and `doc("name")`.

For the canonical formatting rules, see [the `@doc` style guide](../style/doc-style.md).
That guide is the single source of truth for formatting; this chapter just teaches the workflow.

### Minimal example

```genia
@doc "Adds one"
inc(x) -> x + 1
```
Classification: **Likely valid** (not directly tested)

The function binding metadata becomes:

```genia
{doc: "Adds one"}
```

You can retrieve the rendered source text directly with:

```genia
doc("inc")
```

Use `@doc` when the contract matters to a caller.
Skip it when the binding is trivial and the name already says enough.

### Edge case: combine `@doc` and `@meta`

```genia
@doc """
# square

Multiply a number by itself.
"""
@meta {category: "math", stable: true}
square(x) -> x * x

[
  unwrap_or("missing", meta("square") |> get("doc")),
  unwrap_or("missing", meta("square") |> get("category")),
  unwrap_or(false, meta("square") |> get("stable"))
]
```
Classification: **Likely valid** (not directly tested)

This evaluates to:

```genia
["# square\n\nMultiply a number by itself.\n", "math", true]
```

### Edge case: help output includes selected metadata

```genia
@doc "Adds one"
@category "math"
@since "0.4"
@deprecated "Use inc2 instead."
inc(x) -> x + 1

help("inc")
```
Classification: **Likely valid** (not directly tested)

Current help output includes:

- the function name/arity
- the doc text
- selected metadata lines such as `Category: math`, `Since: 0.4`, and `Deprecated: Use inc2 instead.`

### Markdown subset

`@doc` supports a small terminal-friendly Markdown subset:

- paragraphs
- blank lines
- `-` bullet lists
- inline code
- fenced code blocks
- simple headings such as `## Arguments` and `## Returns`

Avoid HTML, tables, images, and deeply nested formatting.
Keep the body readable in source.

### Failure case: `@meta` must produce a map

```genia
@meta "math"
square(x) -> x * x
```
Classification: **Likely valid** (not directly tested)

This raises:

- `TypeError("@meta annotation expected a map, received string")`

---


## Calling module exports (Phase 1 modules)

Module imports bind module values, and exports are accessed with narrow slash access.

```genia
import math
math/inc(2)
```

Notes:

- `import math` binds one module value named `math`.
- `import math as m` binds that same module value as `m`.
- repeated imports are cached by module name, so module files are evaluated once per root environment.
- export access uses `module/name` (bare identifier RHS only).
- module values are namespace-like and distinct from maps.
- the same module model is also used for the current Python host bridge:
  - `import python`
  - `import python.json as pyjson`
  - host exports still use slash access such as `python/open` and `pyjson/loads`

### Python host interop (Phase 1, allowlisted)

Genia now has a small Python-host-only host bridge.
This section describes the current Python reference host surface, not a shared cross-host contract.
To keep the language minimal, it reuses the existing `import` + `module/name` model instead of adding new member-access syntax.

Implemented host modules in this phase:

- `python`
- `python.json`

Implemented host exports:

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

### Minimal example

```genia
import python
"file.txt" |> python/open |> python/read
```
Classification: **Likely valid** (not directly tested)

### Edge case example

```genia
import python.json as pyjson
unwrap_or("fallback", "null" |> pyjson/loads)
```
Classification: **Likely valid** (not directly tested)

Result:

```genia
"fallback"
```

This works because Python `None` maps to Genia `none`, and the ordinary Option-aware pipeline rules apply after the boundary conversion.

Failure examples:

```genia
import no_such_module
```

- raises `FileNotFoundError("Module not found: no_such_module")`.

```genia
import math
math/missing
```

- raises `NameError` for the missing export.

```genia
import python.json as pyjson
"{" |> pyjson/loads
```

- raises `ValueError("python.json/loads invalid JSON: ...")`.

```genia
import python.os
```

- raises `PermissionError("Host module not allowed: python.os")`.

## Autoloaded Function Values

Bundled stdlib functions are not only callable by name.
They can also be used as function values in higher-order positions, and name lookup may autoload the defining prelude file before the lookup succeeds.
This now includes the public Option, String, Map, Ref, Process, sink, and Flow helper surfaces, which are exposed as thin prelude wrappers over host-backed runtime behavior.

### Minimal example

```genia
apply(inc, [41])
```
Classification: **Likely valid** (not directly tested)

This evaluates to `42`.

### Edge case example

```genia
result = 5 |> rule_emit
unwrap_or([], get("emit", result))
```
Classification: **Likely valid** (not directly tested)

This evaluates to `[5]`.

That works because `rule_emit` is looked up as a function value, autoloaded from the prelude, and then used as an ordinary pipeline stage.

### Failure case example

```genia
apply(missing, [1])
```
Classification: **Likely valid** (not directly tested)

This raises:

- `NameError("Undefined name: missing")`

Autoload only helps when a matching autoload registration exists.

## Function Docstrings (Implemented)

A named function may include a leading docstring string literal after `=`:

```genia
inc(x) = """
# inc

Increment a number by one.
""" x + 1
```

The string is metadata for the named function group, not a normal runtime expression.
Docstrings are rendered by `help(...)` as lightweight Markdown text.
Docstrings are allowed for **named functions only** (not lambdas).
After the docstring, the body can still be either a normal expression or a parenthesized multi-clause case body.

```genia
sign(n) = """
# sign
""" (
  0 -> 0 |
  _ -> 1
)
```

You can inspect it with:

```genia
help("inc")
```

`help("name")` also autoloads registered prelude helpers before rendering their docstrings.
For example, the public wrapper-backed helpers below are help-visible without being called first:

```genia
help()
help("get")
help("cli_parse")
help("lines")
help("parse_int")
help("map_put")
help("spawn")
help("eval")
help("write")
```

Current help model:

- `help()` gives a compact overview of the public prelude-backed stdlib families, with family names grouped from registered prelude autoloads.
- `help("name")` autoloads registered public helpers and shows their wrapper docstrings.
- `help("missing")` prints a short missing-name note.
- raw host-backed runtime names such as `print` or `stdout` intentionally do not grow a separate detailed docs registry in this phase; they show a small bridge note instead.

---

## `@doc` Style Guide

Formatting rules for `@doc` now live in one place:
[docs/style/doc-style.md](../style/doc-style.md)

Use that guide for:

- allowed Markdown
- required summary/section rules
- good vs bad examples
- when to document vs when to keep the source minimal

This chapter intentionally stays practical and points back to the style guide instead of redefining it.

---

## Pipeline Operator (Phase 2)

Genia now supports a minimal pipeline operator for left-to-right stage composition:

`left |> right`

Stage rules (implemented):

* pipelines lower into explicit Core IR as one source plus an ordered stage list
* `x |> f` calls `f(x)`
* `x |> f(y)` calls `f(y, x)` (the piped value is appended as the final argument)
* `x |> expr` calls `expr(x)` when `expr` is valid in ordinary call-callee position
  * this includes callable data such as string projectors over maps (`record |> "name"` behaves like `"name"(record)`)
* chaining is left-associative: `a |> f |> g` evaluates stages left to right
* newlines may appear immediately before or after `|>`:
  ```genia
  value
    |> f
    |> g
  ```
* this explicit pipeline lowering happens in the AST→Core IR pass

### Minimal example

```genia
record = { name: "Matthew" }
record |> "name"
```
Classification: **Likely valid** (not directly tested)

Result:

```genia
"Matthew"
```

### Edge case example

```genia
record = { user: { name: "Matthew" } }
record |> "user" |> "name"
```
Classification: **Likely valid** (not directly tested)

Result:

```genia
"Matthew"
```

Pipeline-friendly API design note:

- With current stage-call semantics (`x |> f(y)` => `f(y, x)`), functions that are commonly terminal pipeline steps often use destination/config args first.
- Example: `entries |> zip_write("out.zip")` calls `zip_write("out.zip", entries)` in this phase.

### Absence propagation is explicit, not unwrap magic

`|>` is now an explicit pipeline form, but it still does not create implicit Flow bridges.

Absence-aware evaluation in this phase follows these rules:

- if the current pipeline value is `none(...)`, later stages do not run and that same `none(...)` is returned
- if the current pipeline value is `some(x)` and the next stage is not explicitly Option-aware, the stage receives `x`
- when that lifted stage returns a non-Option value `y`, the pipeline wraps it back as `some(y)`
- when that lifted stage returns `some(...)` or `none(...)`, that Option result is preserved

Use `map_some` / `flat_map_some` when you need explicit wrap-vs-flat-map control regardless of stage detection.

### Minimal example

```genia
record = { profile: { name: "Genia" } }
unwrap_or("?", record |> get("profile") |> get("name"))
```
Classification: **Likely valid** (not directly tested)

Result:

```genia
"Genia"
```

### Edge case example

```genia
record = {}
result = record |> get("profile") |> get("name")
[absence_reason(result), unwrap_or({}, absence_context(result))/key]
```
Classification: **Likely valid** (not directly tested)

Result:

```genia
[some("missing-key"), "profile"]
```

The original structured absence survives the whole chain unchanged.

For debugging failure context, inspect full metadata directly:

```genia
result = {} |> get("profile") |> get("name")
absence_meta(result)
```

Result:

```genia
some({reason: "missing-key", context: {key: "profile"}})
```

Another useful chaining shape:

```genia
data = { users: [{ email: "a@example.com" }] }
unwrap_or("unknown", data |> get("users") |> then_first() |> then_get("email"))
```

Result:

```text
"a@example.com"
```

When a chain fails early, the rendered result keeps the structured absence visible:

```genia
{} |> get("profile") |> get("name")
```

Rendered result:

```text
none("missing-key", {key: "profile"})
```

### Failure case example

```genia
none("empty-list") |> parse_int
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

* renders as `none("empty-list")`
* later stages do not execute
* direct pipelines propagate structured absence automatically

Another important edge:

```genia
unwrap_or(0, fields("a b c d 5 x") |> nth(5) |> parse_int)
```

This works because `nth(5)` returns `some("5")`, and pipeline lifting feeds `"5"` into `parse_int` while preserving structured `none(...)` short-circuit behavior.

### Failure case example

```genia
1 |> 2
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

* runtime `TypeError` because `2` is not callable.

Another failure case:

```genia
"name"(42)
```

Expected behavior:

* runtime `TypeError` because string projectors require a map-like runtime map target.

---

## Implementation Status

### ✅ Implemented

* Named function definitions
* Arity-based + varargs dispatch
* Runtime `main` entrypoint convention in file/`-c` modes:
  * `main/1` is preferred and called as `main(argv())`
  * fallback to `main/0` when `main/1` is absent
  * trailing CLI args in `-c` mode are passed through to `argv()` (including bare positional values)
  * when no `-c`/`-p` mode is selected, the first non-mode argument must be a source file path (`--` can be used to pass dash-prefixed literal args/paths)
* Explicit pipe-mode CLI wrapper:
  * `genia -p '<stage_expr>'` / `genia --pipe '<stage_expr>'`
  * wraps as `stdin |> lines |> <stage_expr> |> run`
  * explicit unbound `stdin` and explicit unbound `run` are rejected
  * bypasses `main`
* Bundled stdlib/prelude `.genia` sources are loaded through package resources, so installed-tool execution does not depend on checkout-relative stdlib paths
* Pipeline operator `|>` with Option-aware stage semantics while preserving ordinary call shape
* Bare callable pipeline RHS forms that lower to ordinary call syntax (for example, string projector pipelines such as `record |> "name"`)
* Direct maybe-returning pipeline composition:
  * `get`
  * `then_first`
  * `then_nth`
  * `then_find`
  * `parse_int`
  * `unwrap_or`
* Explicit Option helpers still available for non-pipeline composition:
  * `then_get`
  * `then_first`
  * `then_nth`
  * `then_find`
  * `map_some`
  * `flat_map_some`
  * these still matter when the value in hand is already an explicit Option, or when higher-order wrap-vs-flat-map behavior is the point
* Named-function docstring metadata (`f(...) = "doc" ...`)
* `help(name)` output with:
  * signature header (`name/shape`)
  * source location when available
  * Markdown-aware docstring rendering (headings/lists/inline code/fenced code blocks)
  * undocumented fallback (`No documentation available.`)

### ⚠️ Partial

* Markdown rendering is intentionally minimal and terminal-first (no full Markdown engine, no syntax highlighting)
* Docstring parsing requires the docstring and body expression to be part of the same definition expression sequence (no dedicated block-doc syntax)
* Flow runtime behavior is still implemented separately in Phase 1; pipeline evaluation is Option-aware, but Flow bridges remain explicit
* public Flow helpers are help-visible through `src/genia/std/prelude/flow.genia`; the lazy Flow kernel stays host-backed while `rules` orchestration/defaulting mostly live in prelude
* explicit Option helpers remain secondary:
  * `then_get`, `then_first`, `then_nth`, and `then_find` are thin wrappers over canonical maybe-returning access/search helpers
  * `map_some` / `flat_map_some` remain useful for direct Option values and higher-order code
  * `unwrap_or`, `or_else`, and `or_else_with` recover/default by wrapping the final Option result
* `main` auto-invocation is only for file/`-c` execution modes (not REPL)

### ❌ Not implemented

* Lambda docstrings
* Separate docstring keywords or block syntax
* Dedicated CLI syntax (`$1`, `$2`, special argument keywords)
* Advanced Flow runtime features beyond Phase 1 (multi-output stages, async scheduling, richer backpressure/cancellation controls)
* `pipe(...)` helper function

---

## CLI Entrypoint with `main` (Runtime Convention)

`main` is just a normal function name with runtime convention behavior in file/`-c` execution.
No parser syntax is added.

### Minimal example

```genia
main(args) = length(args)
```
Classification: **Likely valid** (not directly tested)

When run with two trailing args, this returns `2`.

### Edge case example

```genia
main() = "ok"
```
Classification: **Likely valid** (not directly tested)

If `main/1` is absent, `main/0` is called automatically.

### Failure case example

```genia
main(args) = args
main() = "fallback"
```
Classification: **Likely valid** (not directly tested)

`main/1` has precedence, so this returns the argv list rather than `"fallback"`.

Pipe mode does not use this `main` convention. It runs the wrapped flow directly.
