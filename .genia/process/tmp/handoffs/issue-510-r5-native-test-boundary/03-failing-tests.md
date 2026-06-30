# === GENIA FAILING TESTS ===

CHANGE NAME:
issue #510 r5-native-test-boundary

CHANGE SLUG:
issue-510-r5-native-test-boundary

Issue: #510
Type: contract
Release classification: R5 — Native Test Expansion / Pytest Migration Wave 1
Branch: `contract/issue-510-r5-native-test-boundary`
Handoff directory: `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/`

`GENIA_STATE.md` is final authority.

This TEST phase adds a doc/semantic guardrail only. It does not change runtime behavior, add native Genia tests, migrate pytest tests, edit shared specs, or implement the documentation sync.

---

## 0. BRANCH CHECK

- Must NOT be on `main`: confirmed — current branch is `contract/issue-510-r5-native-test-boundary`.
- Expected branch: `contract/issue-510-r5-native-test-boundary`.
- Branch matches pre-flight / contract / design handoffs.
- No merge, rebase, or branch switch performed.

---

## 1. TEST PLAN

Files updated:

- `tests/doc/test_semantic_doc_sync.py`

Behavior group tested:

- `GENIA_STATE.md` must gain and preserve an explicit R5 native-test / pytest / shared-spec placement boundary before DOCS sync is considered complete.

Contract invariants covered:

- Native tests complement pytest and shared semantic specs.
- Native tests do not replace pytest or shared semantic specs.
- Native-test placement is for Genia-facing behavior.
- Python pytest remains the placement for parser, Core IR, host adapter, CLI harness, spec runner, and other host/internal surfaces.
- Shared semantic specs remain authoritative for covered portable observable behavior.
- Native-test support remains Experimental and Python reference-host framed.
- The boundary must not claim support for setup/teardown, fixtures, parameterized tests, snapshots, property tests, parallelism, filtering, broad discovery, or multi-host execution.

Why a guardrail is appropriate:

- The contract/design introduce a protected documentation boundary rather than executable behavior.
- Existing `GENIA_STATE.md` has native-test layer and non-goal wording, but it does not yet contain the specific R5 placement boundary promised by the contract: native tests vs Python pytest vs shared semantic specs, including "complement, not replace."
- The smallest useful guardrail is one doc-sync test against `GENIA_STATE.md`.

---

## 2. REQUIRED COVERAGE

Happy path:

- The future DOCS phase can satisfy the test by adding a concise `GENIA_STATE.md` section titled `Native test / pytest / shared-spec placement boundary` with the required contract wording.

Edge / boundary cases:

- The test checks all three placements: native tests, Python pytest, and shared semantic specs.
- The test checks maturity/host framing: Experimental and Python reference host.
- The test checks unsupported feature boundaries in the same section so future wording cannot silently imply current support.

Failure cases:

- Missing placement-boundary section fails.
- Missing "complement / do not replace" wording fails.
- Missing pytest/internal or shared-spec authority wording fails.
- Missing unsupported-feature non-support wording fails.

Nearby regression risk:

- Existing native-test implementation-boundary docs could be mistaken for the new R5 placement boundary. This test requires the R5 boundary explicitly so DOCS sync cannot pass with only the older implementation-layer text.

---

## 3. EXECUTION

Command run:

```bash
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_semantic_doc_sync.py::test_native_test_placement_boundary_stays_explicit_in_state
```

Result:

- Failed as expected: `1 failed in 0.20s`.

---

## 4. FAILURE EVIDENCE

Failing test:

- `tests/doc/test_semantic_doc_sync.py::test_native_test_placement_boundary_stays_explicit_in_state`

Failure summary:

```text
AssertionError: GENIA_STATE.md must document the R5 native-test / pytest / shared-spec placement boundary
assert -1 != -1
```

Classification:

- Expected failure, correct per contract/design.

Why it fails:

- `GENIA_STATE.md` does not yet contain the marker text `Native test / pytest / shared-spec placement boundary`.
- That is the intended red signal for the later DOCS phase to add the authoritative boundary without changing runtime behavior.

---

## 5. AMBIGUITIES / BLOCKERS

None.

Stop after TEST. Do not implement docs sync in this phase.
