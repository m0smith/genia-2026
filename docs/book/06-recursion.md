# Chapter 06: Recursion

Genia uses recursion as the primary looping model.

## Minimal example

```genia
sum(xs) =
  [] -> 0 |
  [x, ..rest] -> x + sum(rest)
```

## Edge case example

```genia
sum([]) -> 0
```

## Failure case example

```genia
sum(123)
```

Expected behavior:

- runtime match failure (input is not a list).

## Where recursion is used in stdlib/examples

- `reduce`, `any?`, `nth`, `take`, `drop`, and `range` in `std/prelude/list.genia`
- main loop in `examples/tic-tac-toe.genia` (`play` / `playTurn`)
- simulation stepping loop in `examples/ants.genia` (`run`)

## Implementation status

### ✅ Implemented

- direct recursive functions
- recursion over list patterns
- tail-call elimination for self tail recursion in recognized tail positions

### ⚠️ Partial

- optimization is targeted; not every recursive shape is rewritten to a low-level loop

### ❌ Not implemented

- dedicated loop keywords beyond existing `repeat`
