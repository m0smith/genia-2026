# === GENIA IMPLEMENTATION ===

CHANGE NAME:
issue #510 r5-native-test-boundary

CHANGE SLUG:
issue-510-r5-native-test-boundary

Issue: #510
Type: contract
Release classification: R5 - Native Test Expansion / Pytest Migration Wave 1
Branch: `contract/issue-510-r5-native-test-boundary`
Handoff directory: `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/`

`GENIA_STATE.md` is final authority.

This IMPLEMENTATION phase is docs/contract-only. It makes the approved failing doc guardrail pass and does not change runtime behavior, native-test behavior, parser behavior, IR behavior, CLI behavior, prelude behavior, host adapter behavior, spec runner behavior, shared specs, or native Genia tests.

---

## 0. BRANCH CHECK

- Must NOT be on `main`: confirmed - current branch is `contract/issue-510-r5-native-test-boundary`.
- Expected branch: `contract/issue-510-r5-native-test-boundary`.
- Branch matches pre-flight / contract / design / failing-tests handoffs.
- No merge, rebase, branch switch, or commit performed.

---

## 1. SUMMARY OF CHANGES

Files changed:

- `GENIA_STATE.md`
- `tests/doc/test_semantic_doc_sync.py` (carried from TEST phase; unchanged by this implementation except now satisfied by `GENIA_STATE.md`)

Section added:

- `GENIA_STATE.md` near the existing native-test sections, immediately after the current native-test support limitations and before `## 9.1) Native test kernel core`.
- Exact section heading: `### Native test / pytest / shared-spec placement boundary (Python reference host, Experimental)`.

What the section states:

- Native test support remains Experimental and backed by the Python reference host.
- Native tests complement pytest and shared semantic specs.
- Native tests do not replace pytest or shared semantic specs.
- Genia-native tests belong to Genia-facing source behavior such as Outcome helpers, validation helpers, Flow/Seq visible behavior, Sheet helpers, user-facing examples, and similar prelude/source-level behavior.
- Python pytest remains the home for parser, lexer, AST, Core IR, host/runtime internals, host adapter behavior, CLI harness internals, spec runner internals, Python-specific exception/normalization behavior, and native-test stack internals.
- Shared semantic specs remain authoritative for portable observable CLI/eval/flow/error/parse/IR behavior where covered.
- Unsupported native-test features remain unsupported: setup/teardown execution, setup/teardown, fixtures, parameterized tests, snapshots, property tests, parallelism, filtering, broad discovery, and multi-host execution.

---

## 2. SCOPE CONFIRMATION

No runtime/native-test behavior changed.

No edits were made to:

- parser, lexer, AST, Core IR, lowering, evaluator, runtime, prelude, or builtins
- CLI harness, native test kernel, native test CLI, or native test runner
- host adapter or spec runner internals
- shared spec YAML files
- native Genia test fixtures

No pytest tests were migrated. No native-test features were added.

---

## 3. VALIDATION

Command:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_semantic_doc_sync.py::test_native_test_placement_boundary_stays_explicit_in_state
```

Result:

```text
1 passed in 0.05s
```

Command:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_semantic_doc_sync.py
```

Result:

```text
86 passed in 0.34s
```

---

## 4. COMPLEXITY CHECK

[x] Minimal and direct
[ ] Broader than ideal but necessary
[ ] Too broad

The implementation is a single authoritative documentation subsection that satisfies the approved doc guardrail without touching behavior.

---

## 5. NOTES FOR LATER PHASES

- Ignored handoff files under `.genia/process/tmp/` may need `git add -f` later if the process requires committing them.
- Stop after IMPLEMENTATION. Do not proceed to DOC SYNC, AUDIT, or commit in this phase.
