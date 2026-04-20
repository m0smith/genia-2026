
# Shared Spec Runner

The shared spec runner loads spec cases, dispatches them to the Python host adapter, and compares normalized results.

**Python is the only implemented host today.**
The Python host adapter exposes a single `run_case(case: SpecCase) -> SpecResult` entrypoint, dispatching to category-specific execution modules for parse, ir, eval, cli, flow, and error. All results are normalized before comparison.

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

**How to run the spec suite:**

```bash
pytest tests/test_python_host_adapter.py
```

**How it works:**
- Cases are loaded from the shared spec suite (or local test definitions)
- Each case is dispatched to the adapter, which normalizes the result
- Results are compared against expected outputs
- Failures are reported with a full diff and error context

**Example failure output:**

```
FAILED tests/test_python_host_adapter.py::test_eval_case[case42] - AssertionError: Result mismatch
--- expected
+++ actual
@@ ...
  "result": 42,
  "stdout": "",
  "stderr": "",
  "exit_code": 0
  ...
```

**Normalization:**
All observable outputs (values, errors, IR, CLI, flow) are normalized to canonical, host-neutral forms. No Python-specific details are allowed in normalized outputs. Only the minimal portable Core IR node families are used in the contract. Error objects are normalized with required fields and strict category separation.

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
