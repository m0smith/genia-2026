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

This chapter focuses on the map bridge because it is the newest core data capability.

---

## Phase 1 map bridge (what it is)

Genia does **not** have map literals or map patterns yet.

Instead, Genia now exposes a minimal runtime/builtin bridge:

- `map_new()`
- `map_get(m, key)`
- `map_put(m, key, value)`
- `map_has?(m, key)`
- `map_remove(m, key)`
- `map_count(m)`

Implementation note: this is a **Phase 1 host-backed opaque map bridge**, not full native map syntax.

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

### ⚠️ Partial

- key support is intentionally minimal and runtime-defined (stable structural strategy for list/tuple-compatible keys and scalar keys)

### ❌ Not implemented

- map literals
- map pattern matching
- member/index syntax for maps
- general host interop / FFI

---

## Simulation primitives (Phase 2)

Genia includes minimal host-backed simulation builtins:

- `rand()`
- `rand_int(n)`
- `sleep(ms)`

These are builtins only. They do **not** add async runtime behavior, a scheduler, or new syntax.

### Random decision example

```genia
decide rand_int(2) {
  0 -> print("left")
  1 -> print("right")
}
```

Expected behavior:

- one branch is selected using random integer output in `[0, 2)`

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
