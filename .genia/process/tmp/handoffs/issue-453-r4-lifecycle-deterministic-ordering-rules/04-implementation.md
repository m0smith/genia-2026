# IMPLEMENTATION handoff: issue #453 r4-lifecycle-deterministic-ordering-rules

CHANGE NAME: issue #453 r4-lifecycle-deterministic-ordering-rules
CHANGE SLUG: issue-453-r4-lifecycle-deterministic-ordering-rules
ISSUE: #453
BRANCH: feature/issue-453-r4-lifecycle-deterministic-ordering-rules
PHASE: IMPLEMENTATION only

---

## Branch

- Starting branch: `feature/issue-453-r4-lifecycle-deterministic-ordering-rules`
- Working branch: `feature/issue-453-r4-lifecycle-deterministic-ordering-rules`
- Branch already existed: yes
- Worked directly on `main`: no
- Failing test commit SHA: `8a2eecb`

---

## Files changed

- `src/genia/lifecycle_binding.py`
- `.genia/process/tmp/handoffs/issue-453-r4-lifecycle-deterministic-ordering-rules/04-implementation.md`

No tests were modified in this phase.

No project docs outside this handoff were modified.

---

## Implementation summary

Implemented the smallest production change needed to satisfy the TEST phase:

- `LifecycleAnnotationBinding.ordering` now defaults to `source_order` when omitted.
- The internal binding defaults now match the existing helper defaults used by tests: `required=False`, `participant_kind="callable"`, and `failure_policy="diagnostic"`.
- Ordering validation is centralized in `_validate_ordering(...)`.
- Non-string ordering values now fail with a deterministic diagnostic:

```text
invalid lifecycle annotation binding at binding.ordering: expected ordering identifier, got <runtime-type>
```

- Unsupported string ordering values continue to fail with:

```text
invalid lifecycle annotation binding at binding.ordering: unsupported ordering <value>
```

- Ordering values are validated without calling or coercing callable values.
- Participant ordering behavior and order keys remain unchanged.

No lifecycle execution, setup/teardown behavior, lifecycle runner, action registry, parser, IR, prelude, CLI, or execution-mode behavior was added or changed.

---

## stable_name_order mismatch resolution

The TEST prompt listed only:

- `source_order`
- `reverse_source_order`

However, the approved preflight, contract, design, `GENIA_STATE.md`, `docs/architecture/lifecycle.md`, and existing tests also include `stable_name_order` as an accepted first-pass ordering label.

Because `GENIA_STATE.md` is final authority and the handoff/source-of-truth chain preserves `stable_name_order`, this implementation kept `stable_name_order` accepted and did not remove or reject it.

---

## Commands run

Focused validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_binding.py
```

Observed result:

```text
15 passed in 0.11s
```

Nearby regression validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py tests/doc/test_lifecycle_architecture_doc.py
```

Observed result:

```text
39 passed in 0.18s
```

Additional nearby lifecycle/doc validation:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_scope.py tests/doc/test_semantic_doc_sync.py
```

Observed result:

```text
94 passed in 0.52s
```

---

## Confirmation

- Docs outside this handoff modified: no
- Tests modified in this phase: no
- Parser behavior changed: no
- Lexer behavior changed: no
- Core IR behavior changed: no
- Prelude behavior changed: no
- CLI behavior changed: no
- Execution-mode behavior changed: no
- Lifecycle execution added: no
- setup/teardown behavior added: no
- Lifecycle runner added or invoked: no
- Action registry added: no
- Priority/dependency/before/after ordering added: no

---

## Remaining ambiguity or follow-up

The only remaining ambiguity is the prompt wording that named two ordering rules while the source-of-truth chain names three. This implementation resolved that by preserving `stable_name_order`; a later docs-sync or audit phase can update wording only if the authoritative contract intentionally changes.

Do not proceed to docs sync or audit from this handoff without an explicit prompt.
