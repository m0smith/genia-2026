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

## Implementation status

### ✅ Implemented

- stable quoted tags for application, assignment, lambda, block, and match/case
- syntax predicates for the current evaluator-facing expression families
- syntax selectors for quotation, assignment, lambda, application, and block forms
- clear selector failures on wrong expression kinds

### ⚠️ Partial

- `operands(...)` and `block_expressions(...)` return raw pair-chain tails, not normalized ordinary lists

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
  lambda_expr?(quote((x) -> x + 1)),
  operator(quote(f(1, 2))),
  operands(quote(f(1, 2))),
  application_expr?(quote([f, 1, 2]))
]
```

Expected result:

```genia
[true, f, (1 2), false]
```

This shows the current selector contract:

- `operator(...)` returns the quoted operator value
- `operands(...)` returns the raw quoted operand tail as a pair chain
- quoted source application is represented explicitly as `(app f 1 2)`

## Failure case example

```genia
operator(quote([f, 1, 2]))
```

Expected behavior:

- raises `TypeError("operator expected an application expression")`

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
