# Chapter 14: Building an Evaluator

This chapter is the first small proof that Genia can evaluate Genia expressions as ordinary data.

The evaluator works over quoted expressions, not raw source text.

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

Expected result:

```genia
15
```

## Failure case example

```genia
eval(quote(0 -> 1 | _ -> 2), empty_env())
```

Expected behavior:

- raises a clear runtime error because quoted match/case forms are not executable through phase-1 metacircular `eval`

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
  - application expressions
  - block expressions
- `apply(proc, args)` for:
  - ordinary callable values
  - metacircular compound procedures represented as `(compound <params> <body> <env>)`

### ⚠️ Partial

- the evaluator operates only on the supported quoted expression families above
- quoted match/case forms are inspectable but not executable yet
- raw quoted pair/list data can still share the same raw shape as quoted applications
- the evaluator relies on a host-backed metacircular environment capability instead of a pure-Genia environment implementation

### ❌ Not implemented

- metacircular evaluation for every current Genia surface form
- metacircular execution of quoted match/case expressions
- macro expansion or compiler/analyzer passes

## Notes

- `define` binds in the current metacircular environment frame
- `set` follows current lexical rebinding rules: nearest existing binding first, otherwise current frame
- `extend` creates a child lexical environment and is used by metacircular `apply`
- closures capture the defining metacircular environment
- `apply` preserves its old ordinary-callable behavior and now also handles metacircular compound procedures
