# Chapter 13: Metacircular Expression Helpers

This chapter prepares Genia for later evaluator/compiler examples.

The key idea is simple:

- programs are ordinary data
- the helper layer inspects the same quoted data produced by `quote(expr)` and `quasiquote(expr)`
- Genia does not introduce a second user-visible AST object family for this phase

## Current helper surface

Predicates:

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

Selectors:

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

## Implementation status

### ✅ Implemented

- stable quoted tags for application, assignment, lambda, block, and match/case
- syntax predicates for the current evaluator-facing expression families
- syntax selectors for quotation, assignment, lambda, application, block, and match-branch forms
- clear selector failures on wrong expression kinds

### ⚠️ Partial

- `operands(...)`, `block_expressions(...)`, and `match_branches(...)` return raw pair-chain tails, not normalized ordinary lists

### ❌ Not implemented

- a separate canonical evaluator language

## Minimal example

```genia
[
  assignment_expr?(quote(x = 10)),
  assignment_name(quote(x = 10)),
  assignment_value(quote(x = 10))
]
```

Expected result:

```genia
[true, x, 10]
```

## Edge case example

```genia
[
  branch_pattern(car(match_branches(quote(0 -> 1 | x ? x > 0 -> x)))),
  branch_has_guard?(car(match_branches(quote(0 -> 1 | x ? x > 0 -> x)))),
  branch_has_guard?(car(cdr(match_branches(quote(0 -> 1 | x ? x > 0 -> x))))),
  branch_guard(car(cdr(match_branches(quote(0 -> 1 | x ? x > 0 -> x)))))
]
```

Expected result:

```genia
[0, false, true, (app > x 0)]
```

This shows the current selector contract:

- `branch_pattern(...)` returns the quoted branch pattern
- `branch_has_guard?(...)` distinguishes guarded vs unguarded branches
- `branch_guard(...)` returns the quoted guard expression for guarded branches
- quoted match/case is represented explicitly as `(match (clause ...) ...)`

## Failure case example

```genia
branch_guard(car(match_branches(quote(_ -> 1))))
```

Expected behavior:

- raises `TypeError("branch_guard expected a guarded match branch")`

## Representation notes

Current stabilized quoted forms include:

- application: `(app <operator> <operand1> <operand2> ...)`
- assignment: `(assign <name-symbol> <value-expr>)`
- lambda: `(lambda <params-structure> <body-expr>)`
- block: `(block <expr1> <expr2> ...)`
- match/case:
  - `(match (clause <pattern> <result>) ...)`
  - `(match (clause <pattern> <guard> <result>) ...)`

This layer is intentionally narrow.

It exists to make later evaluator code readable while keeping ordinary quoted data as ordinary data.

The phase-1 evaluator now builds directly on these helpers in Chapter 14.
