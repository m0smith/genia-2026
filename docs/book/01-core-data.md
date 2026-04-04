# Chapter 01: Core Data

## What data exists in Genia today?

Genia currently supports these runtime value families:

- numbers
- strings
- booleans (`true`, `false`)
- `nil`
- lists
- functions
- refs (`ref`)
- process handles (`spawn`)
- **phase-1 host-backed persistent associative maps** (`map_new`, `map_put`, ...)
- **phase-1 host-backed bytes wrappers** (`utf8_encode`, `utf8_decode`)
- **phase-1 host-backed zip entry wrappers** (`zip_entries`, `entry_*`, `zip_write`)

This chapter covers the current Phase-1 host-backed core-data bridges (maps, bytes, and zip entries), starting with maps.

---

## Phase 1 map bridge (what it is)

Genia now has minimal map literals and map patterns, and still exposes the runtime/builtin bridge APIs directly.

Instead, Genia now exposes a minimal runtime/builtin bridge:

- `map_new()`
- `map_get(m, key)`
- `map_put(m, key, value)`
- `map_has?(m, key)`
- `map_remove(m, key)`
- `map_count(m)`

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
- map builtins (`map_new`, `map_get`, `map_put`, `map_has?`, `map_remove`, `map_count`)
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
- general host interop / FFI

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

Only two callable-data forms are implemented in this phase.

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

Pipeline cross-reference (same callable semantics, pipeline lowering only):

```genia
person = { name: "Matthew" }
person |> "name"
```

Expected result:

```genia
"Matthew"
```

This works because pipeline lowers to ordinary call form (`person |> "name"` -> `"name"(person)`), not because pipeline has separate lookup semantics.

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
- `zip_write` supports both `(entries, path)` and `(path, entries)` to stay compatible with current pipeline rewrite shape

### ❌ Not implemented

- full Flow runtime (stages, backpressure, cancellation, multi-port stages)
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
- native language abstractions for agents, ticks, or worlds
- native map syntax for simulation state authoring

---

## Primitive Option values (phase 1)

Genia now has a minimal Option model that is separate from `nil`.

- `none`
- `some(value)`

And minimal helpers:

- `get?(key, target)`
- `unwrap_or(default, opt)`
- `is_some?(opt)`
- `is_none?(opt)`

### Minimal example

```genia
person = { name: "Genia" }
person |> get?("name") |> unwrap_or("unknown")
```

Expected result:

```genia
"Genia"
```

### Edge case example

```genia
[get?("a", {a:nil}), get?("b", {a:nil})]
```

Expected behavior:

- first result is `some(nil)` (key exists)
- second result is `none` (key missing)

### Failure case example

```genia
get?("name", 42)
```

Expected behavior:

- raises `TypeError` (`get?` supports map targets, `some(map)`, and `none`)

### Implementation status

### ✅ Implemented

- primitive option values: `none`, `some(value)`
- `get?` lookup semantics with key-presence distinction (`some(nil)` vs `none`)
- `unwrap_or(default, opt)` for defaulting on `none`
- `is_some?` / `is_none?` predicates
- pipeline-friendly lookup (`record |> get?("name")`)
- callable-data compatibility remains unchanged (`m(key)`, `m(key, default)`, `"key"(m)`, `"key"(m, default)` still return legacy `nil`/default semantics for missing keys)

### ⚠️ Partial

- `some(pattern)` supports exactly one inner pattern (multi-item constructor patterns are rejected)

### ❌ Not implemented

- multi-argument option constructor pattern forms (e.g., `some(a, b)`)
