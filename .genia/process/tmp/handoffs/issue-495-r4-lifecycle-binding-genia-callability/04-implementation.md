# Implementation — issue #495 r4-lifecycle-binding-genia-callability

CHANGE NAME: issue #495 r4-lifecycle-binding-genia-callability
CHANGE SLUG: issue-495-r4-lifecycle-binding-genia-callability

Handoff directory:

```text
.genia/process/tmp/handoffs/issue-495-r4-lifecycle-binding-genia-callability/
```

Output file:

```text
.genia/process/tmp/handoffs/issue-495-r4-lifecycle-binding-genia-callability/04-implementation.md
```

---

## 0. BRANCH

Starting branch:

```text
feature/issue-495-r4-lifecycle-binding-genia-callability
```

Working branch:

```text
feature/issue-495-r4-lifecycle-binding-genia-callability
```

Branch check passed before edits. Work was not done on `main`.

---

## 1. FAILING-TEST ANCHOR

Referenced failing-test commit:

```text
3d5429a
```

Anchor verification:

```bash
git show --stat --oneline 3d5429a
```

Observed summary:

```text
3d5429a test(lifecycle): capture Genia callable participants issue #495
2 files changed, 170 insertions(+)
```

Focused pre-implementation check:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_binding.py -v
```

Observed starting result:

```text
1 failed, 16 passed
```

Observed failing test:

```text
tests/unit/test_lifecycle_binding.py::test_callable_participant_kind_accepts_genia_function_group_semantics
```

The failure was the intended Genia callable-participant red state: a `GeniaFunctionGroup`-shaped value that is not raw Python-callable was rejected by lifecycle binding.

---

## 2. FILES CHANGED

```text
src/genia/lifecycle_binding.py
.genia/process/tmp/handoffs/issue-495-r4-lifecycle-binding-genia-callability/04-implementation.md
```

No tests were modified in this implementation phase.

---

## 3. IMPLEMENTATION SUMMARY

Implemented the smallest production change in `src/genia/lifecycle_binding.py`:

* imported `GeniaFunction` and `GeniaFunctionGroup` from `genia.callable`
* added internal helper `_is_lifecycle_callable_participant(value) -> bool`
* delegated the existing `participant_kind == "callable"` branch to that helper

The helper accepts:

* `GeniaFunctionGroup`
* `GeniaFunction`
* plain Python callables for existing internal compatibility

All non-`"callable"` participant kinds preserve the previous behavior.

Callable validation does not execute candidate values. It only performs `isinstance(...)` checks and the existing Python `callable(...)` compatibility check.

Native-test behavior was not changed. No native-test discovery integration was added.

---

## 4. DOCUMENTATION DECISION

No source-of-truth docs were changed.

Reason:

* This is internal lifecycle binding hardening only.
* No public lifecycle behavior was introduced.
* No parser, lexer, Core IR, prelude, builtin, CLI, native-test, or user-visible lifecycle behavior changed.

---

## 5. VALIDATION

Focused lifecycle binding validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_binding.py -v
```

Observed result:

```text
17 passed
```

Nearby native-test validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_native_test_cli.py tests/unit/test_native_test_kernel.py -v
```

Observed result:

```text
29 passed
```

Optional nearby lifecycle validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py tests/unit/test_lifecycle_binding.py -v
```

Observed result:

```text
52 passed
```

---

## 6. IMPLEMENTATION COMMIT

Implementation commit SHA:

```text
See `git show --oneline HEAD` after commit creation.
```

Note: the final commit SHA cannot be embedded literally inside the same committed file without changing that commit's SHA. The final implementation commit SHA is reported by `git show --oneline HEAD` after the commit is created.

Commit message:

```text
fix(lifecycle): align callable participant validation issue #495
```

---

## 7. REMAINING FOLLOW-UPS

None for this implementation phase.

Do not proceed to doc-sync, audit, PR, or cleanup from this phase.
