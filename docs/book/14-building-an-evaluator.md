# Chapter 14: Building an Evaluator

This chapter is the first small proof that Genia can evaluate Genia expressions as ordinary data.

The evaluator works over quoted expressions, not raw source text.

Implementation split in this phase:

- parser/lowering, ordinary evaluator substrate, and metacircular environment capabilities remain host-backed
- evaluator dispatch and most user-facing semantic glue live in `src/genia/std/prelude/eval.genia`

Public phase-1 names:

- `empty_env`
- `lookup`
- `define`
- `set`
- `extend`
- `eval`
- `apply`

## Minimal example

```genia
eval(quote(42), empty_env())
```
Classification: **Likely valid** (not directly tested)

Expected result:

```genia
42
```

## Lambda / apply example

```genia
env = empty_env()
f = eval(quote((x) -> x + 1), env)
apply(f, [10])
```
Classification: **Likely valid** (not directly tested)

Expected result:

```genia
11
```

## Closure example

```genia
expr = quote({
  make_adder = (n) -> (x) -> x + n
  add5 = make_adder(5)
  add5(10)
})
eval(expr, empty_env())
```
Classification: **Likely valid** (not directly tested)

Expected result:

```genia
15
```

## Edge case example

```genia
matcher = eval(quote(x ? x > 0 -> x | _ -> 0), empty_env())
[apply(matcher, [5]), apply(matcher, [-1])]
```
Classification: **Likely valid** (not directly tested)

Expected result:

```genia
[5, 0]
```

## Failure case example

```genia
apply(eval(quote(0 -> 1), empty_env()), [9])
```
Classification: **Likely valid** (not directly tested)

Expected behavior:

- raises a clear runtime error because no quoted match branch matched the argument list

## Implementation status

### ✅ Implemented

- host-backed metacircular environment values via `empty_env()`
- environment operations:
  - `lookup`
  - `define`
  - `set`
  - `extend`
- `eval(expr, env)` for:
  - self-evaluating literals
  - symbol expressions
  - quoted expressions
  - assignment expressions
  - lambda expressions
  - match/case expressions
  - application expressions
  - block expressions
- `apply(proc, args)` for:
  - ordinary callable values
  - metacircular compound procedures represented as `(compound <params> <body> <env>)`
  - metacircular matcher procedures represented as `(matcher <match-expr> <env>)`

### ⚠️ Partial

- the evaluator operates only on the supported quoted expression families above
- the evaluator relies on a host-backed metacircular environment capability instead of a pure-Genia environment implementation
- `operands(...)` and `block_expressions(...)` still return pair-chain sequences rather than normalized ordinary lists
- unsupported quoted forms still fail with a clear runtime error instead of expanding evaluator coverage

### ❌ Not implemented

- metacircular evaluation for every current Genia surface form
- macro expansion or compiler/analyzer passes

## Notes

- quoted source applications reach the evaluator as `(app <operator> <operand1> ...)`
- `define` binds in the current metacircular environment frame
- `set` follows current lexical rebinding rules: nearest existing binding first, otherwise current frame
- `extend` creates a child lexical environment and is used by metacircular `apply`
- closures capture the defining metacircular environment
- `apply` preserves its old ordinary-callable behavior and now also handles metacircular compound procedures
