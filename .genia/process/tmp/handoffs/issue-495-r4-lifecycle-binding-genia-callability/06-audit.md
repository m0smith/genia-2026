# Audit — issue #495 r4-lifecycle-binding-genia-callability

CHANGE NAME: issue #495 r4-lifecycle-binding-genia-callability
ISSUE: #495
PHASE: AUDIT (assume wrong until proven correct)

Output file:

```text
.genia/process/tmp/handoffs/issue-495-r4-lifecycle-binding-genia-callability/06-audit.md
```

---

## 0. BRANCH

Starting branch: `feature/issue-495-r4-lifecycle-binding-genia-callability`
Working branch:  `feature/issue-495-r4-lifecycle-binding-genia-callability`

Branch matches exactly. No work on `main`. No merge. No rebase.

`git status --short` shows only the untracked tooling file `?? .claude/settings.local.json`
(ignored per instructions, not committed). No unrelated tracked changes.

`git diff --name-only main..HEAD`:

```text
.genia/process/tmp/handoffs/.../03-test.md
.genia/process/tmp/handoffs/.../04-implementation.md
.genia/process/tmp/handoffs/.../05-doc-sync.md
GENIA_STATE.md
src/genia/lifecycle_binding.py
tests/unit/test_lifecycle_binding.py
```

All tracked changes are in-scope for #495.

---

## 1. COMMITS REVIEWED

```text
3d5429a test(lifecycle): capture Genia callable participants issue #495
89c6ede fix(lifecycle): align callable participant validation issue #495
2fe22bd docs(lifecycle): sync callable participant docs issue #495
```

Note (informational, not a defect): the audit prompt referred to `2fe22bd` as
"docs(lifecycle): record doc sync decision issue #495". The actual message is
"docs(lifecycle): sync callable participant docs issue #495". This is correct: the
doc-sync prompt specified the "sync callable participant docs" message precisely when
a source-of-truth doc changes, and a source doc (GENIA_STATE.md) did change.

---

## 2. FILES REVIEWED

- `src/genia/lifecycle_binding.py` (diff + lines 160–197)
- `tests/unit/test_lifecycle_binding.py` (new tests in `3d5429a`)
- `src/genia/callable.py` (`GeniaFunctionGroup`, `GeniaFunction`, their `__call__`)
- `src/genia/test_kernel.py` (unchanged — not in diff)
- `GENIA_STATE.md` §9.5, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
  `docs/architecture/lifecycle.md`
- Handoffs `00`–`05`

---

## 3. SUMMARY VERDICT

**PASS** — ready to merge: **YES**

The change is a minimal, correct, internal hardening of lifecycle-binding
callable-participant recognition. Tests pin the intended contract and catch
regression to host-only `callable()` semantics. Docs remain accurate; the only doc
change is a correct test-count update.

---

## 4. CONTRACT ↔ IMPLEMENTATION FINDINGS

The decision point is `_participant_kind_matches` → `_is_lifecycle_callable_participant`:

```python
def _is_lifecycle_callable_participant(value: Any) -> bool:
    return isinstance(value, (GeniaFunctionGroup, GeniaFunction)) or callable(value)
```

- ✅ `participant_kind="callable"` no longer relies only on raw Python `callable()`;
  it first checks the Genia runtime callable types by `isinstance`.
- ✅ Accepts `GeniaFunctionGroup` (isinstance branch).
- ✅ Accepts `GeniaFunction` (isinstance branch).
- ✅ Plain Python callables remain accepted (`or callable(value)`).
- ✅ Ordinary non-callable values remain rejected (e.g. `int 1` → both checks False).
  The rejection diagnostic at `lifecycle_binding.py:102`
  (`for @<name> expected callable, ...`) is unchanged.
- ✅ Validation does not execute candidates — only `isinstance(...)` / `callable(...)`
  introspection; no call is made.
- ✅ Filtering (`_annotation_matches`), ordering (`_validate_ordering`/`_order_key`),
  duplicate diagnostics, and required-binding diagnostics are untouched by the diff.
- ✅ No native-test discovery integration added; `discover_lifecycle_participants`
  is not wired into the native-test path.
- ✅ No lifecycle runner / phase execution / setup / teardown added.
- ✅ No parser, lexer, Core IR, prelude, or public builtin change (diff touches only
  `lifecycle_binding.py` + tests + GENIA_STATE.md).
- ✅ Native-test CLI/kernel behavior unchanged (`test_kernel.py` not in diff;
  native-test test suites pass — see §7).

Observation: both `GeniaFunctionGroup` and `GeniaFunction` define `__call__`
(callable.py:235, 276), so real instances are already Python-callable. The change is
therefore type-intent hardening: the binding now decides on the Genia callable *type*
rather than the host `__call__` protocol, so a Genia callable representation that does
not expose `__call__` is still accepted. This is exactly what the design intended.

---

## 5. DESIGN ↔ IMPLEMENTATION FINDINGS

- ✅ Matches `04-implementation.md`: single import added, one internal helper added,
  the `"callable"` branch delegates to it; "smallest production change".
- ✅ Scope discipline held — no scope creep into runner/lifecycle/native-test surfaces
  as committed in `01-contract.md` / `02-design.md`.

---

## 6. TESTS ↔ CONTRACT FINDINGS

New tests (`3d5429a`):

- `test_callable_participant_kind_accepts_genia_function_group_semantics`: uses
  `NonCallableMock(spec=GeniaFunctionGroup)` and asserts `not callable(function_group)`
  AND `isinstance(..., GeniaFunctionGroup)`, then that the participant is bound with no
  diagnostics. This is the meaningful regression guard: it pins acceptance via type,
  not via `callable()`.
- `test_callable_participant_kind_accepts_genia_function_values`: builds a real
  `GeniaFunction` and asserts it binds with no diagnostics.

Red/green verification (run in the clean 3.10 venv; see §7 for environment):

- Current implementation: both tests PASS.
- Simulated pre-implementation (decision point forced back to raw `callable()`):
  the group-semantics test **FAILS** (assertion), the function test still passes
  (real `GeniaFunction` has `__call__`). This reproduces `04-implementation.md`'s
  observed pre-impl state ("1 failed, 16 passed") and proves the suite catches
  regression to host-only `callable()` semantics.

- ✅ Tests assert concrete behavior (participant names, value identity, empty
  diagnostics) — not implementation trivia.
- ✅ Existing lifecycle binding tests still cover ordering, filters, duplicate
  diagnostics, required bindings, and the non-callable rejection diagnostic (17 tests
  total, all pass).

---

## 7. VALIDATION ENVIRONMENT + COMMANDS/RESULTS

Environment acceptability decision: **ACCEPTABLE.**

`05-doc-sync.md` documented that `uv run pytest` could not execute because the repo
`.venv` points to a missing `python@3.12` and uv's standalone-interpreter download is
network-blocked. Confirmed again here — `uv run pytest` fails at cache/interpreter
initialization. Per `pyproject.toml`, `requires-python = ">=3.8"` and the only runtime
dependency is `PyYAML`, so running on system CPython 3.10.12 with `pytest` + `PyYAML`
and an editable install is a faithful equivalent. No version-specific behavior is
exercised by these tests. This is acceptable for audit; no fix required.

uv attempt (still blocked):

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_binding.py
# -> error: Failed to initialize cache / interpreter download blocked
```

Clean venv used (system CPython 3.10.12):

```bash
python3 -m venv /tmp/genvenv
/tmp/genvenv/bin/pip install pytest pyyaml
/tmp/genvenv/bin/pip install -e .
```

Results:

```bash
/tmp/genvenv/bin/python -m pytest -q tests/unit/test_lifecycle_binding.py
# -> 17 passed

/tmp/genvenv/bin/python -m pytest -q tests/unit/test_native_test_cli.py tests/unit/test_native_test_kernel.py
# -> 29 passed

/tmp/genvenv/bin/python -m pytest -q tests/doc/test_semantic_doc_sync.py
# -> 85 passed
```

Red/green check script (monkeypatching the decision point to raw `callable()`):

```text
CURRENT IMPL (89c6ede):              group-semantics PASS, function-values PASS
SIMULATED PRE-IMPL (raw callable()): group-semantics FAIL,  function-values PASS
```

---

## 8. DOCS ↔ BEHAVIOR FINDINGS

- ✅ `GENIA_STATE.md` §9.5 test count for `test_lifecycle_binding.py` correctly
  updated 15 → 17 (verified: parent of `3d5429a` = 15 `def test_`, HEAD = 17). The
  `2fe22bd` diff is exactly that one line.
- ✅ No doc implies public/user-facing lifecycle binding behavior (§9.5 keeps
  "Python reference host, Experimental", "No public Genia lifecycle annotation binding
  API was added").
- ✅ No doc implies setup/teardown is implemented (explicit limitations intact).
- ✅ No doc implies native-test discovery is integrated with lifecycle binding
  (§9.5: "Native test discovery remains owned by the existing native test CLI/test-mode
  layer; it was not refactored to use this helper").
- ✅ `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md` unchanged and accurate
  (no lifecycle-binding callable-participant claims).
- ✅ `docs/architecture/lifecycle.md` describes "callable participant validation"
  without restricting it to Python callables — remains accurate; not stale.

---

## 9. ISSUES FOUND

None of severity ≥ low affecting correctness, scope, or docs.

Informational only:
- Commit message of `2fe22bd` differs from the string in the audit prompt; the actual
  message is the doc-sync-prescribed one for a source-doc change. No action.

No code or doc fixes required.

---

## 10. FINAL VERDICT

PASS WITH NO ISSUES. Ready to merge: **YES**.

Stopping after the audit commit. Not proceeding to PR, cleanup, distillation, or merge.
