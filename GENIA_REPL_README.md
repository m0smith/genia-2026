# Genia Prototype REPL

This is a Python prototype REPL for the current Genia design.

## Run

```bash
python3 genia_repl.py
```

Or run a file:

```bash
python3 genia_repl.py sample.genia
```

## Supported in this prototype

- numbers, strings, booleans, nil
- arithmetic: `+ - * / %`
- comparison: `< <= > >= == !=`
- variables and function calls
- function definitions with `=`
- function definitions with `{}` block bodies
- case expressions in function bodies
- case expressions as the final expression in a block
- pattern matching against the full argument tuple
- single-parameter shorthand patterns
- guards with `?`
- `log(...)` builtin

## Examples

### Arithmetic

```genia
1 + 2 * 3
```

### Simple function

```genia
square(x) = x * x
square(5)
```

### Factorial

```genia
fact(n) =
  0 -> 1 |
  n -> n * fact(n - 1)
```

### Factorial with logging block

```genia
fact2(n) {
  log(n)
  0 -> 1 |
  n -> n * fact2(n - 1)
}
```

### Tuple-pattern matching

```genia
add(x, y) =
  (0, y) -> y |
  (x, 0) -> x |
  (x, y) -> x + y
```

## REPL commands

- `:help`
- `:env`
- `:quit`

## Not implemented yet

- lambdas
- lists/maps/destructuring beyond tuple parameter matching
- pipelines
- modules/imports
- member access / indexing
- full standard library

This is a prototype to validate the language model and syntax decisions, not a finished implementation.
