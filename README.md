# Additional Genia test cases

Copy these files into your repo under:

tests/cases/

These cases focus on:
- parser edge cases
- call vs definition ambiguity
- lambda calls and closures
- block-bodied functions
- rest-pattern behavior
- duplicate binding correctness
- top-level assignment
- higher-order reduce usage
- representative error cases

Run with:

```bash
uv run pytest tests/test_cases.py -q
```
