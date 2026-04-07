# Chapter 01: Core Data

## What data exists in Genia today?

Genia's current runtime value model is broader than just "plain data".

### Core values

- numbers
- promises
- symbols
- strings
- booleans (`true`, `false`)
- `nil`
- pairs
- Option values: `none`, `none(reason)`, `none(reason, context)`, `some(value)`
- lists
- maps
  - map literals and `map_*` builtins produce the same runtime map value family

### Function / module values

- functions
- modules (`import mod`)
  - current Python host bridge also reuses module values (`import python`, `import python.json`)

### Callable behaviors layered on values

- functions are callable values
- maps are callable lookup values
- strings can be used as callable map projectors
- maps and strings do not become separate callable types when used this way

### Runtime capability values

- `stdout`
- `stderr`
- MetaEnv (`empty_env()`)
- Flow (runtime Phase 1 is implemented)
- refs (`ref`)
- process handles (`spawn`)
- **phase-1 host-backed bytes wrappers** (`utf8_encode`, `utf8_decode`)
- **phase-1 host-backed zip entry wrappers** (`zip_entries`, `entry_*`, `zip_write`)
- **phase-1 Python host handles** returned by `python/open` (`<python file>`)

## Current absence semantics

- `nil` and `none` coexist today; they are distinct runtime values
- canonical missing-result APIs return structured absence:
  - `get`
  - `first`
  - `last`
  - `nth`
  - string `find`
  - `find_opt`
- compatibility aliases remain:
  - `get?`
  - `first_opt`
  - `nth_opt`
- docs-deprecated legacy access paths still return `nil` for missing values:
  - `map_get`
  - map slash access (`map/name`)
  - callable map lookup (`m(key)`)
  - callable string projector lookup (`"key"(m)`)
- `cli_option` remains legacy-retained and still returns `value_or_nil`
- `some(nil)` is possible and means the key exists with value `nil`
- `none`, `none(reason)`, and `none(reason, context)` all mean absence; reason/context are metadata
- Option pattern matching supports literal `none`, structured `none(...)`, and constructor pattern `some(pattern)`
- the public Map helper names are thin prelude wrappers in `std/prelude/map.genia`, backed by the same host runtime behavior
- the public Ref helper names are thin prelude wrappers in `std/prelude/ref.genia`, backed by the same host runtime behavior
- the public output sink helper names are thin prelude wrappers in `std/prelude/io.genia`, backed by the same host runtime behavior
- the public Option helper surface is exposed through `std/prelude/option.genia`, and canonical `some(...)` / `none(...)` constructor forms lower explicitly in Core IR
- the public String helper names are thin prelude wrappers in `std/prelude/string.genia`, backed by the same host runtime behavior
- the public Flow helper names `lines`, `rules`, `each`, `collect`, and `run` are thin prelude wrappers in `std/prelude/flow.genia`, backed by the same host runtime behavior
- `help()` now points users toward these public prelude-backed helper families; the family samples come from registered autoload metadata, while raw host bridge names remain intentionally generic in help output

Naming rule today:

- new `?`-suffixed APIs are boolean-returning
- maybe-returning APIs should use Option values without `?`
- `get?` remains the current compatibility exception
- `get` is the preferred maybe-aware lookup name in this phase
- `first_opt` and `nth_opt` remain compatibility aliases for canonical `first` and `nth`
- docs and new examples should prefer canonical APIs over docs-deprecated `nil`-returning lookup forms

Current consistency note:

- missing values are not represented by one fully unified model today
- promises are real runtime values but are separate from Flow
- Flow, output sinks, MetaEnv values, and refs are real runtime values, but they are not plain data in the same sense as numbers, lists, or maps

This chapter focuses on the currently implemented data-facing runtime values and bridges, starting with maps and the current Option model.

### Absence migration matrix

| API / form | Status | Present result | Missing result | Preferred in new code? |
| --- | --- | --- | --- | --- |
| `get` | Canonical | `some(value)` | `none(missing_key, { key: key })` | Yes |
| `get?` | Compatibility alias | `some(value)` | `none(missing_key, { key: key })` | No |
| `first` | Canonical | `some(value)` | `none(empty_list)` | Yes |
| `first_opt` | Compatibility alias | `some(value)` | `none(empty_list)` | No |
| `last` | Canonical | `some(value)` | `none(empty_list)` | Yes |
| `nth` | Canonical | `some(value)` | `none(index_out_of_bounds, { ... })` | Yes |
| `nth_opt` | Compatibility alias | `some(value)` | `none(index_out_of_bounds, { ... })` | No |
| `find` | Canonical string search | `some(index)` | `none(not_found, { needle: needle })` | Yes |
| `find_opt` | Canonical predicate-search helper | `some(value)` | `none(no_match)` | Yes |
| `map_get` | Deprecated-in-docs | raw value | `nil` | No |
| `m(key)` | Deprecated-in-docs | raw value | `nil` | No |
| `"key"(m)` | Deprecated-in-docs | raw value | `nil` | No |
| `m/name` | Deprecated-in-docs | raw value | `nil` | No |
| `cli_option` | Legacy retained | raw value | `nil` | Usually no |

---

## Programs as data (phase 1)

Genia has:

- `quote(expr)` for syntax-as-data
- `quasiquote(expr)` for syntax-as-data with selective evaluation

Both produce the same runtime data representation.

- identifier -> symbol
- number / string / boolean / `nil` / `none` -> literal runtime value
- list literal -> pair chain ending in `nil`
- map literal -> map of quoted keys and quoted values
- unary / binary / call forms -> tagged application pair chain `(app <operator> <arg1> ...)`
- assignment -> `(assign <name-symbol> <value-expr>)`
- lambda -> `(lambda <params-structure> <body-expr>)`
- block -> `(block <expr1> <expr2> ...)`
- match/case -> `(match (clause <pattern> <result>) ...)` or `(match (clause <pattern> <guard> <result>) ...)`

### Minimal example

```genia
quote([a, b, c])
```

Expected result:

```genia
(a b c)
```

### Edge case example

```genia
q = quote({a: 1, "b": c})
[map_get(q, quote(a)), map_get(q, "b")]
```

Expected result:

```genia
[1, c]
```

This shows the current quoted-map key rule:

- identifier keys become symbol keys
- string keys stay strings

Quasiquote example:

```genia
x = 10
quasiquote([a, unquote(x), c])
```

Expected result:

```genia
(a 10 c)
```

Nested quasiquote example:

```genia
x = 7
quasiquote([a, quasiquote([b, unquote(x)]), c])
```

Expected result:

```genia
(a (quasiquote (b (unquote x))) c)
```

This shows the current depth rule:

- `unquote(...)` only applies to the nearest surrounding quasiquote

Splicing example:

```genia
xs = [1, 2]
quasiquote([a, unquote_splicing(xs), b])
```

Expected result:

```genia
(a 1 2 b)
```

### Failure case example

```genia
quote(a, b)
```

Expected behavior:

- syntax error because `quote(...)` expects exactly one argument
- `unquote(1)` outside quasiquote raises a clear runtime error
- `quasiquote(unquote_splicing(xs))` raises a clear runtime error because splicing is only valid in quasiquoted list context

### Implementation status

### ✅ Implemented

- first-class symbol runtime values
- `quote(expr)` special form
- `quasiquote(expr)` special form
- `unquote(expr)`
- `unquote_splicing(expr)` in quasiquoted list literal contexts
- symbol values distinct from strings
- recursive quoting for lists and maps
- tagged quoted source applications:
  - `quote(1 + 2)` -> `(app + 1 2)`
  - `quote(f(1, 2))` -> `(app f 1 2)`
- depth-sensitive nested quasiquote handling

### ⚠️ Partial

- `unquote_splicing(expr)` is intentionally narrow:
  - list context only
  - accepts ordinary lists, `nil`, and nil-terminated pair chains

### ❌ Not implemented

- `'x` quote sugar
- reader shorthand for quasiquote / unquote / unquote-splicing
- macros

---

## Metacircular expression helpers (phase 1)

Genia now includes a small stdlib helper layer for inspecting quoted expressions.

These helpers live in `std/prelude/syntax.genia` and reuse the existing `quote(expr)` / `quasiquote(expr)` data model.

### Minimal example

```genia
assignment_name(quote(x = 10))
assignment_value(quote(x = 10))
```

Expected result:

```genia
x
10
```

### Edge case example

```genia
[
  branch_has_guard?(car(match_branches(quote(0 -> 1 | x ? x > 0 -> x)))),
  branch_has_guard?(car(cdr(match_branches(quote(0 -> 1 | x ? x > 0 -> x))))),
  branch_guard(car(cdr(match_branches(quote(0 -> 1 | x ? x > 0 -> x))))) == quote(x > 0)
]
```

Expected result:

```genia
[false, true, true]
```

Current note:

- quoted source applications use the stable tag form `(app <operator> <operand1> ...)`
- `operands(...)` returns the operand tail as a pair chain
- `match_branches(...)` returns the branch tail of `(match ...)` as a pair chain
- this helper layer stays close to the existing quoted representation instead of inventing a second AST type family

### Failure case example

```genia
assignment_name(quote(42))
```

Expected behavior:

- raises `TypeError("assignment_name expected an assignment expression")`

### Implementation status

### ✅ Implemented

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
  - `match_branches`
  - `branch_pattern`
  - `branch_has_guard?`
  - `branch_guard`
  - `branch_body`

### ⚠️ Partial

- `operands(...)`, `block_expressions(...)`, and `match_branches(...)` return pair-chain sequences instead of normalized ordinary lists

### ❌ Not implemented

- a separate canonical evaluator language

---

## Metacircular evaluation (phase 1)

Genia now includes a minimal metacircular evaluator built on the quoted-data model.

Current split:

- parser/quote/quasiquote substrate and metacircular environments remain host-backed
- public syntax selectors and most helper glue over quoted data live in prelude

Public names:

- `empty_env`
- `lookup`
- `define`
- `set`
- `extend`
- `eval`
- `apply`

### Minimal example

```genia
eval(quote(42), empty_env())
```

Expected result:

```genia
42
```

### Edge case example

```genia
expr = quote({
  make_adder = (n) -> (x) -> x + n
  add5 = make_adder(5)
  add5(10)
})
eval(expr, empty_env())
```

Expected result:

```genia
15
```

### Failure case example

```genia
apply(eval(quote(0 -> 1), empty_env()), [9])
```

Expected behavior:

- raises a clear runtime error because no quoted match branch matched the argument list

### Implementation status

### ✅ Implemented

- environment helpers:
  - `empty_env`
  - `lookup`
  - `define`
  - `set`
  - `extend`
- metacircular `eval(expr, env)` for:
  - self-evaluating literals
  - symbols
  - quoted expressions
  - assignments
  - lambdas
  - match/case expressions
  - applications
  - blocks
- `apply(proc, args)` for:
  - ordinary callable values
  - metacircular compound procedures represented as `(compound <params> <body> <env>)`
  - metacircular matcher procedures represented as `(matcher <match-expr> <env>)`

### ⚠️ Partial

- `operands(...)` and `block_expressions(...)` still expose pair-chain sequences rather than normalized ordinary lists

### ❌ Not implemented

- a full metacircular evaluator for every current surface form

---

## Pairs (phase 1)

Genia has immutable pairs for SICP-style structural data.

- `cons(x, y)`
- `car(pair)`
- `cdr(pair)`
- `pair?(x)`
- `null?(x)`

### Minimal example

```genia
car(cons(1, 2))
```

Expected result:

```genia
1
```

### Edge case example

```genia
xs = cons(1, cons(2, cons(3, nil)))
[car(xs), car(cdr(xs)), null?(cdr(cdr(cdr(xs))))]
```

Expected result:

```genia
[1, 2, true]
```

### Failure case example

```genia
car(1)
```

Expected behavior:

- raises `TypeError` because `car` expects a pair

### Implementation status

### ✅ Implemented

- immutable pair runtime values
- `cons`, `car`, `cdr`, `pair?`, `null?`
- structural pair equality
- quoted lists as pair chains

### ⚠️ Partial

- ordinary list literals remain separate list values in this phase

### ❌ Not implemented

- mutable pairs
- list literals lowering to pairs

---

## Promises (phase 1)

Genia has explicit delayed values through `delay(expr)` and `force(x)`.

Promises are not Flow values.

- promises delay ordinary expression evaluation
- successful forcing is memoized
- forcing is explicit
- non-promise values pass through `force(...)` unchanged

### Minimal example

```genia
force(delay(1 + 2))
```

Expected result:

```genia
3
```

### Edge case example

```genia
{
  x = 10
  p = delay(x + 1)
  x = 20
  force(p)
}
```

Expected result:

```genia
21
```

This shows the current lexical-capture rule:

- promises capture the same lexical environment model that closures capture
- rebinding before the first force is visible when the promise is forced

### Failure case example

```genia
{
  p = delay(car(1))
  force(p)
}
```

Expected behavior:

- forcing raises `TypeError`
- the promise remains unforced, so a later `force(p)` retries instead of returning a cached failure

### Implementation status

### ✅ Implemented

- `delay(expr)` special form
- `force(x)` builtin
- memoized forcing after successful evaluation
- non-promise passthrough in `force`
- lexical environment capture for delayed expressions

### ⚠️ Partial

- promises are explicit only; Genia does not auto-force
- promises are separate from Flow and do not provide stream helpers by themselves

### ❌ Not implemented

- quasiquote-driven lazy syntax
- automatic forcing
- promise-specific pattern matching

---

## Output sinks (phase 1)

Genia has minimal host-backed output sink values for Unix-style IO.
The public `write`, `writeln`, and `flush` names are defined in `std/prelude/io.genia` as thin documented wrappers over the host-backed sink bridge.

- `stdout`
- `stderr`
- `write(sink, value)`
- `writeln(sink, value)`
- `flush(sink)`

`print(...)` writes to `stdout`.

`log(...)` writes to `stderr`.

### Minimal example

```genia
write(stdout, "a")
writeln(stdout, "b")
```

Expected behavior:

- writes `ab` followed by a newline to standard output

### Edge case example

```genia
flush(stdout)
flush(stderr)
```

Expected behavior:

- both calls succeed
- each returns `nil`

### Failure case example

```genia
write(42, "x")
```

Expected behavior:

- raises `TypeError` because `write` expects a sink as its first argument

### Implementation status

### ✅ Implemented

- first-class `stdout` and `stderr` runtime sink values
- public `write`, `writeln`, and `flush` wrappers in `std/prelude/io.genia`
- `write(sink, value)` and `writeln(sink, value)`
- `flush(sink)`
- `print(...)` routed to `stdout`
- `log(...)` routed to `stderr`
- quiet broken-pipe handling on `stdout` in CLI/file/command execution

### ⚠️ Partial

- broken-pipe handling is intentionally narrow and host-backed in this phase

### ❌ Not implemented

- generalized port APIs
- configurable user-defined sink protocols

---

## String parsing

Genia includes a small explicit integer parser.
The public `parse_int` name is defined in `std/prelude/string.genia` as a thin documented wrapper over the host-backed parser:

- `parse_int(string)`
- `parse_int(string, base)`

### Minimal example

```genia
parse_int("42")
```

Expected result:

```genia
some(42)
```

### Edge case example

```genia
[parse_int("  -17  "), parse_int("ff", 16), parse_int("101010", 2)]
```

Expected result:

```genia
[some(-17), some(255), some(42)]
```

### Failure case example

```genia
parse_int("12x")
```

Expected behavior:

- returns `none(parse_failed, context)` because the string is not a valid base-10 integer

Additional current rules:

- surrounding whitespace is ignored
- leading `+` / `-` is supported
- explicit base must be in `2..36`
- non-string input raises `TypeError`

### Implementation status

### ✅ Implemented

- `parse_int(string)` and `parse_int(string, base)`
- public `parse_int` wrapper in `std/prelude/string.genia`
- `help("parse_int")` visibility through the wrapper docstring
- parse failures return structured absence instead of raising for ordinary invalid text

### ⚠️ Partial

- integer parsing only; there is no broader numeric parsing family in this phase

### ❌ Not implemented

- built-in float parsing helpers
- Option-returning parse helpers

---

## Phase 1 map bridge (what it is)

Genia now has minimal map literals and map patterns, and the public map helper names are thin prelude wrappers over a minimal host-backed runtime bridge:

- `map_new()`
- `map_get(m, key)`
- `map_put(m, key, value)`
- `map_has?(m, key)`
- `map_remove(m, key)`
- `map_count(m)`

These public helper names live in `std/prelude/map.genia` as thin documented wrappers over the same host-backed map runtime support.

Implementation note: map values remain the same **Phase 1 host-backed opaque map runtime value** under both builtin and literal syntax.

Literal forms implemented:

- `{}` (empty map)
- `{ name: "Matthew" }` (identifier key sugar for string key)
- `{ "name": "Matthew" }` (explicit string key)
- trailing commas are accepted
- duplicate keys are deterministic last-one-wins

---

## Minimal example

```genia
world0 = map_new()
world1 = map_put(world0, [10, 12], "food")
world2 = map_put(world1, [11, 12], "ant")
print(map_get(world2, [10, 12]))
```

Expected behavior:

- prints `food`
- `world0` is still empty
- `world1` and `world2` are new values

---

## Edge case example

```genia
m0 = map_new()
m1 = map_put(m0, [1, 2], "a")
m2 = map_put(m1, [1, 2], "b")
[map_count(m1), map_count(m2), map_get(m1, [1, 2]), map_get(m2, [1, 2])]
```

Expected result:

```genia
[1, 1, "a", "b"]
```

This shows persistent update semantics with key replacement.

---

## Failure case example

```genia
map_put(1, "k", 10)
```

Expected behavior:

- raises `TypeError` with a clear message because first argument must be a map value.

Another failure case:

```genia
map_put(map_new(), ref(1), 10)
```

Expected behavior:

- raises `TypeError` because this phase supports only stable key types.

---

## Implementation status

### ✅ Implemented

- opaque runtime map value wrapper
- public map helper surface in `std/prelude/map.genia`
- map helpers (`map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`)
- persistent behavior for `map_put` and `map_remove`
- missing-key lookup returns `nil`
- callable map lookup:
  - `m(key)` => value or `nil`
  - `m(key, default)` => stored value when key exists, else `default`
- callable string projectors for maps:
  - `"key"(m)` => value or `nil`
  - `"key"(m, default)` => stored value when key exists, else `default`

### ⚠️ Partial

- key support is intentionally minimal and runtime-defined (stable structural strategy for list/tuple-compatible keys and scalar keys)

### ❌ Not implemented

- member/index syntax for maps
- callable data beyond maps and string projectors (no list-call, no string indexing, no callable protocol)
- general unrestricted host interop / FFI

---


## Narrow named slash access on maps (phase 1)

Map values support static named access with `/` when the right-hand side is a bare identifier.

### Minimal example

```genia
person = { name: "Matthew", age: 42 }
person/name
```

Expected result:

```genia
"Matthew"
```

### Edge case example

```genia
person = { name: "Matthew" }
person/middle
```

Expected result:

```genia
nil
```

### Failure case example

```genia
{name: "Matthew"}/"name"
```

Expected behavior:

- raises `TypeError` because slash named access requires a bare identifier RHS (`lhs/name`).

### Implementation status

### ✅ Implemented

- map named access via `map/name`
- missing map key via slash returns `nil`
- callable map (`m("name")`) and string projector (`"name"(m)`) behavior remains unchanged

### ⚠️ Partial

- slash access is intentionally narrow in this phase (no expressions on RHS, no chaining semantics beyond repeated valid accesses)

### ❌ Not implemented

- general member access
- index syntax
- quoted/dynamic RHS slash access forms

---

## Callable data (phase 1, map-centric)

Only two non-function callable-data forms are implemented in this phase.

### Minimal example

```genia
person = { name: "Matthew", age: 42 }
[person("name"), "age"(person)]
```

Expected result:

```genia
["Matthew", 42]
```

### Edge case example

```genia
person = { name: "Matthew" }
[person("missing"), person("missing", "?"), "missing"(person, "?")]
```

Expected result:

```genia
[nil, "?", "?"]
```

Pipeline cross-reference (same callable semantics, explicit pipeline stages):

```genia
person = { name: "Matthew" }
person |> "name"
```

Expected result:

```genia
"Matthew"
```

This works because the pipeline stage still calls the string projector with the piped value as its final argument (`person |> "name"` behaves like `"name"(person)`), not because pipeline has separate lookup semantics.

### Failure case example

```genia
"name"(42)
```

Expected behavior:

- raises `TypeError` because string projector targets must be map-like runtime map values.

Another failure case:

```genia
{}()
```

Expected behavior:

- raises `TypeError` because callable maps support only arity 1 or 2.

### Implementation status

### ✅ Implemented

- map callable lookup by key (`m(key)`) and key-with-default (`m(key, default)`)
- string key projector lookup against maps (`"key"(m)` and `"key"(m, default)`)
- maps stay map values when called; strings stay string values when used as projectors
- missing-key result is `nil` (or provided default in arity-2 forms); existing keys mapped to `nil` still return `nil`

### ⚠️ Partial

- callable-data support is intentionally narrow to canonical map lookup and string projection only

### ❌ Not implemented

- any other callable-data behavior (lists, nested path lookup, mutation-by-call, user-defined callable protocols)

---

## Bytes / JSON / ZIP bridge (phase 1)

Genia now includes a minimal host-backed bridge for byte-safe JSON rewriting inside zip archives.

Flat pipeline-friendly API (no member/dot syntax):

- `utf8_encode(string) -> bytes`
- `utf8_decode(bytes) -> string`
- `json_parse(string) -> value`
- `json_pretty(value) -> string`
- `zip_entries(path) -> list of zip entries`
- `zip_write(entries, path) -> path`
- `entry_name(entry)`, `entry_bytes(entry)`, `set_entry_bytes(entry, bytes)`, `update_entry_bytes(entry, f)`, `entry_json(entry)`

### Minimal example

```genia
format_json_bytes(bytes) =
  compose(utf8_encode, json_pretty, json_parse, utf8_decode)(bytes)
```

### Edge case example

```genia
rewrite_entry(entry) =
  entry ? entry_json(entry) -> update_entry_bytes(entry, format_json_bytes) |
  _ -> entry
```

Expected behavior:

- `entry_json(entry)` true: bytes are reformatted JSON
- `entry_json(entry)` false: bytes are unchanged

### Failure case examples

```genia
utf8_decode("not-bytes")
```

Expected behavior:

- raises `TypeError` (`utf8_decode expected bytes`)

And:

```genia
json_parse("{\"x\":")
```

Expected behavior:

- raises `ValueError` with parse location details

### Implementation status

### ✅ Implemented

- opaque bytes runtime wrapper values
- opaque zip entry runtime wrapper values
- UTF-8 encode/decode builtins
- JSON parse/pretty builtins
- zip read/write builtins with preserved entry order
- JSON objects mapped to runtime map values

### ⚠️ Partial

- `zip_entries` is eager list-based in this phase (not lazy sequences)
- `zip_write` supports both `(entries, path)` and `(path, entries)` to stay compatible with current pipeline stage-call shape

### ❌ Not implemented

- advanced Flow runtime features beyond Phase 1 (multi-port stages, richer cancellation/backpressure controls)
- stream-native zip processing or lazy archive sequences

---

## Simulation primitives (Phase 2)

Genia includes minimal host-backed simulation builtins:

- `rand()`
- `rand_int(n)`
- `sleep(ms)`

These are builtins only. They do **not** add async runtime behavior, a scheduler, or new syntax.

### Random branching example

```genia
pick_direction(n) =
  0 -> print("left") |
  1 -> print("right")

pick_direction(rand_int(2))
```

Expected behavior:

- one pattern branch is selected using random integer output in `[0, 2)`

### Simple loop with sleep

```genia
step(n) =
  n ? n <= 0 -> "done" |
  _ -> {
    print(rand())
    sleep(5)
    step(n - 1)
  }
```

Expected behavior:

- prints a random float each step
- blocks briefly each iteration
- remains single-threaded from language perspective

### Edge case example

```genia
rand_int(1)
```

Expected behavior:

- always returns `0`

### Failure case examples

```genia
rand_int(0)
```

Expected behavior:

- raises `ValueError` (`n` must be `> 0`)

And:

```genia
sleep("10")
```

Expected behavior:

- raises `TypeError` (`ms` must be numeric)

### Implementation status

### ✅ Implemented

- `rand()` returns float in `[0, 1)`
- `rand_int(n)` validates integer and positive bound, returns integer in `[0, n)`
- `sleep(ms)` validates non-negative numeric argument and blocks for milliseconds

### ⚠️ Partial

- randomness is host-RNG quality, not seed-controlled by language-level API
- sleep granularity depends on host scheduler/timer resolution

### ❌ Not implemented

- scheduler/event loop primitives
- async/await syntax
- deterministic RNG seeding controls

---

## First simulation demo: ants (minimal, text mode)

Genia now ships a first working ants-style demo at:

- `examples/ants.genia`

This demo is intentionally minimal and uses only currently implemented builtins and syntax:

- host-backed persistent maps for world state (`map_new`, `map_get`, `map_put`, `map_has?`)
- random direction selection (`rand_int(4)`)
- recursive stepping (finite number of steps)
- blocking frame pacing (`sleep(ms)`)
- plain text rendering (`print`)

### Minimal example (from the demo)

```genia
cell_get(world, pos) =
  (world, pos) ? map_has?(world, pos) -> map_get(world, pos) |
  (_, _) -> "empty"

step_cell(world, ant_pos, target, target_cell) =
  (world, ant_pos, target, "ant") -> [world, ant_pos, "blocked"] |
  (world, ant_pos, target, "food") -> [move_ant(world, ant_pos, target), target, "ate_food"] |
  (world, ant_pos, target, _) -> [move_ant(world, ant_pos, target), target, "moved"]
```

This shows the central simulation shape:

- world is a persistent map keyed by `[x, y]`
- missing cell defaults to `"empty"`
- each step returns `[next_world, next_ant_pos, event]`

### Edge case example

```genia
wrap(n, size) =
  (n, size) ? n < 0 -> size - 1 |
  (n, size) ? n >= size -> 0 |
  (n, _) -> n
```

Expected behavior (demo grid wrapping):

- `wrap(-1, 8)` -> `7`
- `wrap(8, 8)` -> `0`

### Failure / limitation notes

- The demo is text-mode only (no graphics).
- The first version is single-ant only.
- Simulation timing is blocking (`sleep`) and host-dependent.
- Native map syntax is available for authoring state (`{}`, `{ key: value }`, map patterns like `{name}`).
- There is still no scheduler/event loop or language-level simulation framework.

### Implementation status for the ants demo

### ✅ Implemented

- runnable finite-step simulation in `examples/ants.genia`
- random movement + wrapped grid movement
- persistent map-based world updates
- default-empty cell lookup via helper function
- recursive step loop with `sleep` timing

### ⚠️ Partial

- only one ant entity is modeled
- randomness is non-deterministic host RNG (no seed API)
- rendering is plain ASCII grid text

### ❌ Not implemented

- actor/scheduler-based simulation runtime
- native language abstractions for cells, ticks, or worlds
- native map syntax for simulation state authoring

---

## Primitive Option values (phase 1)

Genia now has a minimal Option model that is separate from `nil`.

This is the current explicit presence/absence model, but it does not replace all legacy `nil`-for-missing behavior.

- `none`
- `none(reason)`
- `none(reason, context)`
- `some(value)`

And minimal helpers:

- `get(key, target)`
- `get?(key, target)`
- `map_some(f, opt)`
- `flat_map_some(f, opt)`
- `then_get(key, target)`
- `then_first(target)`
- `then_nth(index, target)`
- `then_find(needle, target)`
- `unwrap_or(default, opt)`
- `is_some?(opt)`
- `is_none?(opt)`
- `some?(opt)`
- `none?(opt)`
- `or_else(opt, fallback)`
- `or_else_with(opt, thunk)`
- `absence_reason(opt)`
- `absence_context(opt)`

These public helper names live in `std/prelude/option.genia` as thin documented wrappers over the same host-backed Option runtime support.
`none` remains a runtime value/literal rather than a prelude wrapper.

Canonical access/search helpers implemented today:

- `first(list)`
- `first_opt(list)` (compatibility alias)
- `last(list)`
- `find(string, needle)`
- `find_opt(predicate, list)`
- `nth(index, list)`
- `nth_opt(index, list)` (compatibility alias)

### Minimal example

```genia
person = { profile: { name: "Genia" } }
unwrap_or("unknown", person |> get("profile") |> get("name"))
```

Expected result:

```genia
"Genia"
```

### Edge case example

```genia
[
  get("a", {a:nil}),
  first([nil]),
  find_opt((x) -> x == nil, [1, nil, 2]),
  absence_reason(last([])),
  find("abc", "b"),
]
```

Expected behavior:

- first result is `some(nil)` (key exists)
- second result is `some(nil)` (first list item is present and is `nil`)
- third result is `some(nil)` (matching item is present and is `nil`)
- fourth result is `some(empty_list)` (absence metadata is inspectable without changing absence into success)
- fifth result is `some(1)` (string search is also maybe-returning now)

### Tooling example

```genia
[
  get("name", {}),
  none(index_out_of_bounds, { index: 8, length: 2 }),
  some(nil),
]
```

Expected rendered result:

```text
[none(missing_key, {key: "name"}), none(index_out_of_bounds, {index: 8, length: 2}), some(nil)]
```

This is still ordinary data. The tooling/rendering is just making the data easier to inspect.

### Failure case example

```genia
absence_reason(42)
```

Expected behavior:

- runtime failure because `absence_reason` expects an Option value

### Implementation status

### ✅ Implemented

- primitive option values: `none`, `none(reason)`, `none(reason, context)`, `some(value)`
- `none` is distinct from `nil`
- pattern matching on Option values:
  - literal `none`
  - structured `none(reason)` / `none(reason, context)`
  - constructor pattern `some(pattern)`
- canonical maybe-aware lookup via `get(key, target)` with key-presence distinction (`some(nil)` vs `none...`)
- `get?(key, target)` remains as a compatibility alias
- explicit Option helpers for non-pipeline and higher-order use: `map_some`, `flat_map_some`, `then_get`, `then_first`, `then_nth`, `then_find`
- helper builtins: `some?`, `none?`, `or_else`, `or_else_with`, `absence_reason`, `absence_context`
- public Option helper surface is help-visible through prelude/autoload metadata, so helpers such as `some`, `get`, `map_some`, and `or_else` are visible through `help("name")`
- canonical list/search helpers: `first`, `last`, `nth`, string `find`, `find_opt`
- compatibility aliases: `first_opt`, `nth_opt`
- `unwrap_or(default, opt)` for defaulting on `none`
- `some?` / `none?` short predicates
- `is_some?` / `is_none?` supported aliases
- pipeline-friendly lookup (`record |> get("name")`)
- callable-data compatibility remains unchanged (`m(key)`, `m(key, default)`, `"key"(m)`, `"key"(m, default)` still return legacy `nil`/default semantics for missing keys)
- `cli_option` also remains in the legacy `value_or_nil` family
- naming rule for current APIs:
  - new `?`-suffixed APIs are boolean-returning
  - maybe-returning APIs use Option values without `?`
  - `get?` remains the existing compatibility exception
  - `get` is the preferred maybe-aware lookup name for new code
- structured absence metadata:
  - `first([]) -> none(empty_list)`
  - `last([]) -> none(empty_list)`
  - `find("abc", "x") -> none(not_found, { needle: "x" })`
  - `find_opt(pred, xs)` can return `none(no_match)`
  - `nth(i, xs)` can return `none(index_out_of_bounds, { index: i, length: n })`
- Option-aware pipelines:
  - `record |> get("user") |> get("name")`
  - `data |> get("items") |> nth(0) |> get("name")`
  - `fields(row) |> nth(5) |> parse_int`
  - recover by wrapping the whole pipeline result with `unwrap_or(...)` or `or_else(...)`
- explicit helpers remain useful outside pipelines:
  - `map_some` and `flat_map_some` preserve structured absence unchanged
  - `then_get`, `then_first`, `then_nth`, and `then_find` are thin explicit helpers for direct Option values
- developer-facing inspection:
  - REPL/debug output preserves structured absence syntax and context visibly
  - `absence_reason` / `absence_context` are the canonical metadata-inspection helpers
  - `some?` / `none?` are the preferred predicate names in docs/examples

### ⚠️ Partial

- `some(pattern)` supports exactly one inner pattern (multi-item constructor patterns are rejected)
- lookup consistency is still partial: `get`, `get?`, `first`, `first_opt`, `last`, `nth`, `nth_opt`, string `find`, and `find_opt` use Option values, while callable maps/string projectors, `map_get`, slash map access, and `cli_option` still use legacy `nil`/match-failure behavior

### ❌ Not implemented

- multi-argument option constructor pattern forms (e.g., `some(a, b)`)
