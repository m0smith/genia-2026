# Chapter 06: Recursion

Genia uses recursion as the primary looping model.

## Minimal example

```genia
sum(xs) =
  [] -> 0 |
  [x, ..rest] -> x + sum(rest)
```
Classification: **Valid** (directly tested)

## Edge case example

```genia
sum([]) -> 0
```
Classification: **Valid** (directly tested)

## Failure case example

```genia
sum(123)
```
Classification: **Valid** (directly tested)

Expected behavior:

- runtime match failure (input is not a list).

## Where recursion is used in stdlib/examples

- `reduce`, `any?`, `nth`, `take`, `drop`, and `range` in `src/genia/std/prelude/list.genia`
- main loop in `examples/tic-tac-toe.genia` (`play` / `playTurn`)
- simulation stepping/collection loops in `examples/ants.genia` (`step`, `step_ants_acc`, `collect_world_signatures`)

## Tail calls

Genia guarantees proper tail-call optimization for calls in tail position.

### Minimal tail-recursive example

```genia
sum_to(n, acc) =
  (n, acc) ? n == 0 -> acc |
  (n, acc) -> sum_to(n - 1, acc + n)
```
Classification: **Likely valid** (not directly tested)

This shape runs in constant stack space.

### Edge case example

Tail position also includes the final expression in a block and the final stage after pipeline lowering:

```genia
sum_pipe(acc, n) = {
  acc
  |> (
    n ? n == 0 -> acc |
    _ -> sum_pipe(acc + n, n - 1)
  )
}
```
Classification: **Likely valid** (not directly tested)

The final call to `sum_pipe(...)` is still in tail position.

### Failure case example

```genia
bad(n) =
  (n) ? n == 0 -> 0 |
  (n) -> 1 + bad(n - 1)
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- this recursive call is not in tail position
- it can still consume Python stack space and raise `RecursionError`

## Implementation status

### ✅ Implemented

- direct recursive functions
- recursion over list patterns
- proper tail-call optimization for calls in tail position
- self tail recursion
- mutual tail recursion

### ⚠️ Partial

- non-tail recursion still uses Python stack space
- specialized low-level loop rewrites remain targeted to a few narrow shapes such as `nth`

### ❌ Not implemented

- dedicated loop keywords beyond existing `repeat`

---

## Delayed recursion with promises

Promises let recursive definitions produce delayed ordinary values.

### Status

✅ Implemented

- delayed recursive pair tails with `delay(expr)`
- explicit forcing with `force(x)`
- memoized successful forcing

⚠️ Partial

- delayed recursion is explicit only
- there is no dedicated stream stdlib in this phase

❌ Not implemented

- automatic forcing
- lazy list literals

### Minimal example

```genia
ones() = cons(1, delay(ones()))
car(force(cdr(ones())))
```
Classification: **Likely valid** (not directly tested)

Expected result:

```genia
1
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
Classification: **Likely valid** (not directly tested)

Expected result:

```genia
21
```

The promise sees the same lexical rebinding model closures see.

### Failure case example

```genia
{
  p = delay(car(1))
  force(p)
}
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- forcing raises `TypeError`
- the promise remains unforced, so a later `force(p)` retries evaluation
