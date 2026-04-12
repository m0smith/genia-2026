# Chapter 03: Functions

## The Smallest Example

```genia
inc(x) = x + 1
```

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

This evaluates to `[2, 2]`.

### Failure case

```genia
{
  (1 + 2) = 3
}
```

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
- `doc("name")` lookup for the current doc string
- `meta("name")` introspection for current binding metadata
- `help("name")` display of selected metadata fields

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

### Edge case: assignment target

```genia
@meta {category: "math"}
x = 10
```

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

### Minimal example

```genia
@doc "Adds one"
inc(x) -> x + 1
```

The function binding metadata becomes:

```genia
{doc: "Adds one"}
```

You can retrieve the rendered source text directly with:

```genia
doc("inc")
```

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

Current help output includes:

- the function name/arity
- the doc text
- selected metadata lines such as `Category: math`, `Since: 0.4`, and `Deprecated: Use inc2 instead.`

### Failure case: `@meta` must produce a map

```genia
@meta "math"
square(x) -> x * x
```

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

Genia now has a small Python-only host bridge.
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

### Edge case example

```genia
import python.json as pyjson
unwrap_or("fallback", "null" |> pyjson/loads)
```

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

This evaluates to `42`.

### Edge case example

```genia
result = 5 |> rule_emit
unwrap_or([], get("emit", result))
```

This evaluates to `[5]`.

That works because `rule_emit` is looked up as a function value, autoloaded from the prelude, and then used as an ordinary pipeline stage.

### Failure case example

```genia
apply(missing, [1])
```

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

- `help()` gives a compact overview of the public prelude-backed stdlib families, with representative family samples derived from registered autoload metadata.
- `help("name")` autoloads registered public helpers and shows their wrapper docstrings.
- raw host-backed runtime names such as `print` or `stdout` intentionally do not grow a separate detailed docs registry in this phase; they show a small bridge note instead.

---

## Official Docstring Style Guide

Use this guide for new or updated public named functions.

### What a docstring is in Genia

* A string literal placed immediately after `=` in a named function definition.
* Attached as metadata for `help(...)`.
* Not evaluated as part of the function body expression.

### Where docstrings are allowed

* ✅ Named functions
* ❌ Lambdas

### Markdown support (implemented subset)

`help(...)` currently preserves and normalizes lightweight Markdown structure:

* Headings (`#`, `##`)
* Bullet lists (`-` or `*`)
* Inline code (`` `like_this` ``)
* Fenced code blocks (```genia ... ```)
* Paragraph spacing (extra blank lines are collapsed)

This is terminal-first formatting, not a full Markdown rendering engine.

### Canonical multi-clause rule

For a single named function group (same name across clauses):

* no docstrings → undocumented function
* one total docstring across clauses → documented function
* repeated identical docstrings across clauses → valid
* conflicting docstrings across clauses → runtime `TypeError`

### How `help` displays docstrings

`help("name")` prints:

1. function signature header (`name/shape`)
2. source location (`Defined at file:line`) when available
3. rendered docstring, or `No documentation available.`

`help()` without arguments prints a surface overview that points users toward the canonical public prelude helpers.

---

## Official Templates

### Minimal template

```text
"""
One-line summary.
"""
```

### Standard template

```text
"""
# function-name

One-line summary.

Optional short description.

## Params

* `param`: description

## Returns

* description

## Examples

```genia
example() -> result
```

## Edge cases

* description

## Failure

* description
"""
```

Use these templates as the **content** of the string literal docstring.

---

## Usage Guidelines

### When to use minimal vs standard

* Use **minimal** for tiny helpers with obvious behavior.
* Use **standard** for most public stdlib-style functions.

### Keep docstrings concise

* Lead with one clear summary sentence.
* Add sections only when they improve understanding.

### Avoid redundant documentation

Avoid repeating things that are obvious from the function name/signature.

### Include examples for public functions

Most public functions should have at least one realistic example.

### Include edge/failure sections when behavior is non-trivial

Add `## Edge cases` and `## Failure` when:

* behavior depends on special inputs, or
* runtime errors are expected for invalid input.

### Avoid overdocumentation

If a section adds no new information, omit it.

---

## Real Examples (Valid Genia Syntax)

### 1) Simple function

```genia
inc(x) = "\"\"\"\n# inc\n\nIncrement `x` by one.\n\n## Params\n\n* `x`: number\n\n## Returns\n\n* number\n\n## Examples\n\n```genia\ninc(4) -> 5\n```\n\"\"\"" x + 1
```

### 2) Recursive function

```genia
fact(n) = "\"\"\"\n# fact\n\nCompute factorial recursively.\n\n## Params\n\n* `n`: non-negative integer\n\n## Returns\n\n* factorial of `n`\n\n## Examples\n\n```genia\nfact(5) -> 120\n```\n\n## Edge cases\n\n* `fact(0)` returns `1`\n\n## Failure\n\n* this version does not include an explicit negative-input guard\n\"\"\"" (
  0 -> 1 |
  n -> n * fact(n - 1)
)
```

### 3) Pattern-matching multi-clause function

All clauses must use the same canonical docstring text (or only one clause provides it):

```genia
sign(0) = "\"\"\"\n# sign\n\nClassify a number by sign.\n\"\"\"" 0
sign(n) = "\"\"\"\n# sign\n\nClassify a number by sign.\n\"\"\"" (
  n > 0 -> 1 |
  _ -> -1
)
```

### 4) Stdlib-style helper

```genia
sum(xs) = "\"\"\"\n# sum\n\nAdd all numbers in `xs`.\n\n## Params\n\n* `xs`: list of numbers\n\n## Returns\n\n* total as number\n\n## Examples\n\n```genia\nsum([1, 2, 3]) -> 6\nsum([]) -> 0\n```\n\"\"\"" (
  [] -> 0 |
  [x, ..rest] -> x + sum(rest)
)
```

---

## `help` Output Examples

### Documented function

Given:

```genia
inc(x) = "\"\"\"\n# inc\n\nIncrement `x` by one.\n\"\"\"" x + 1
help("inc")
```

Typical output:

```text
inc/1
Defined at demo.genia:1

# inc

Increment `x` by one.
```

### Undocumented function

Given:

```genia
plain(x) = x
help("plain")
```

Typical output:

```text
plain/1
Defined at demo.genia:1

No documentation available.
```

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

Result:

```genia
"Matthew"
```

### Edge case example

```genia
record = { user: { name: "Matthew" } }
record |> "user" |> "name"
```

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

When run with two trailing args, this returns `2`.

### Edge case example

```genia
main() = "ok"
```

If `main/1` is absent, `main/0` is called automatically.

### Failure case example

```genia
main(args) = args
main() = "fallback"
```

`main/1` has precedence, so this returns the argv list rather than `"fallback"`.

Pipe mode does not use this `main` convention. It runs the wrapped flow directly.
