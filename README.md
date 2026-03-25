# Genia starter cases

Drop `tests/test_cases.py` into your project and copy the files under `tests/cases/`.

Recommended layout:

```text
tests/
  test_cases.py
  cases/
    arithmetic_precedence.genia
    arithmetic_precedence.out
    ...
```

Run:

```bash
uv run pytest tests/test_cases.py -q
```

Starter cases included:
- arithmetic
- list literals
- recursive len
- duplicate bindings
- reduce/count
- reduce/sum
- lambda apply
- top-level assignment
- tuple patterns
- error cases
