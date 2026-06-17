# Issue #451 DOC SYNC handoff

## Branch report

- Starting branch: `feature/issue-451-r4-lifecycle-cleanup-failure-semantics`
- Working branch: `feature/issue-451-r4-lifecycle-cleanup-failure-semantics`
- Branch existed before this DOC SYNC phase.

## Input files read

Required repo truth and planning docs were read before editing:

- `AGENTS.md`
- `GENIA_STATE.md`
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/ai/LLM_CONTRACT.md`
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`

Required handoffs were read:

- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/00-preflight.md` existed but was empty.
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/01-contract.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/02-design.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/03-failing-tests.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/04-implementation.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/05-test-verification.md`

Implementation commit referenced by the verification handoff:

- `2442f5e83a6defa2b8f4c7f2819791f3feedd811`

Verification commit immediately before this phase:

- `fa84d2542162c455f7b42184dc8e5a06df4ab92c`

## Docs search summary

Required lifecycle search:

```sh
grep -R "lifecycle" -n GENIA_STATE.md GENIA_RULES.md GENIA_REPL_README.md README.md docs tests/doc | head -100
```

Result summary:

- Current implemented lifecycle plan truth is documented in `GENIA_STATE.md` section 9.3.
- Current lifecycle architecture status is documented in `docs/architecture/lifecycle.md`.
- README/REPL references found by the search are Flow/native-test/roadmap exclusions, not lifecycle plan validation contracts requiring correction.
- Existing doc guard coverage is in `tests/doc/test_lifecycle_architecture_doc.py` and `tests/doc/test_semantic_doc_sync.py`.

Required policy wording search:

```sh
grep -R "setup\|teardown\|cleanup\|finalize\|failure_policy\|result_policy" -n GENIA_STATE.md GENIA_RULES.md GENIA_REPL_README.md README.md docs tests/doc | head -100
```

Result summary:

- Existing `cleanup` mentions include Flow resource finalization, lifecycle vocabulary, and lifecycle non-goals.
- `failure_policy` and `result_policy` were not documented as current lifecycle plan validation before this phase.
- Existing native-test docs already state that setup/teardown lifecycle hooks are not implemented.

## Files changed

- `GENIA_STATE.md`
- `docs/architecture/lifecycle.md`
- `.genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/06-doc-sync.md`

No production/runtime files were changed.

## Docs update summary

`GENIA_STATE.md` section 9.3 now documents issue #451 root policy validation:

- optional root policy maps: `cleanup`, `failure_policy`, and `result_policy`
- policy maps are portable data validation/normalization only
- unsupported, unsafe, and nonportable policy values are rejected
- test count updated from 13 to 32 for `tests/unit/test_lifecycle_plan.py`
- explicit limitation added for no cleanup execution behavior

`docs/architecture/lifecycle.md` current implementation status now mirrors the source-of-truth boundary:

- lifecycle plan validation covers optional root policy maps
- unsafe examples such as unentered-scope cleanup, cleanup failures that overwrite or disappear, and nondeterministic failure reporting are rejected
- the implementation remains Python reference-host data validation only
- no prelude API, runner, cleanup execution, phase execution, action resolution, or annotation discovery was added

## Truth boundaries

This DOC SYNC phase documents only implemented and verified behavior from issue #451.

Still not implemented:

- lifecycle runner behavior
- lifecycle phase execution
- cleanup execution
- action resolution or action registry
- execution-mode lifecycle dispatch
- annotation-driven phase discovery such as `@setup` or `@teardown`
- native-test lifecycle hooks, setup/teardown, fixtures, filtering, or parallel execution
- module, server, actor, notebook, browser, or multi-host lifecycle runner behavior

README and REPL docs were intentionally not updated because the required searches did not show an existing lifecycle plan validation section there needing correction.

No native-test docs were updated because the docs wording did not change native-test lifecycle context.

## Commands run

```sh
git status --short --branch
git branch --show-current
sed -n '1,260p' docs/strategy/release-roadmap.md
grep -R "lifecycle" -n GENIA_STATE.md GENIA_RULES.md GENIA_REPL_README.md README.md docs tests/doc | head -100
grep -R "setup\|teardown\|cleanup\|finalize\|failure_policy\|result_policy" -n GENIA_STATE.md GENIA_RULES.md GENIA_REPL_README.md README.md docs tests/doc | head -100
sed -n '2350,2390p' GENIA_STATE.md
sed -n '1,220p' docs/architecture/lifecycle.md
sed -n '1,260p' tests/doc/test_lifecycle_architecture_doc.py
sed -n '1040,1085p' tests/doc/test_semantic_doc_sync.py
rg -n "cleanup|failure_policy|result_policy|unsafe|policy|13 tests|lifecycle plan" tests/unit/test_lifecycle_plan.py src/genia/lifecycle_plan.py
sed -n '1,260p' tests/unit/test_lifecycle_plan.py
sed -n '1,300p' src/genia/lifecycle_plan.py
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py -v
UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_lifecycle_architecture_doc.py tests/doc/test_semantic_doc_sync.py
git diff -- GENIA_STATE.md docs/architecture/lifecycle.md
git status --short --branch
git log --oneline -5
wc -c .genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/00-preflight.md .genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/01-contract.md .genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/02-design.md .genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/03-failing-tests.md .genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/04-implementation.md .genia/process/tmp/handoffs/issue-451-r4-lifecycle-cleanup-failure-semantics/05-test-verification.md
```

Validation results:

- `UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/unit/test_lifecycle_plan.py -v` -> `32 passed in 0.14s`
- `UV_CACHE_DIR=/tmp/uv-cache UV_TOOL_DIR=/tmp/uv-tools uv run pytest -q tests/doc/test_lifecycle_architecture_doc.py tests/doc/test_semantic_doc_sync.py` -> `92 passed in 0.43s`

Ruff was not run because this DOC SYNC phase did not change Python files.

Native-test neighbor tests were not run because this DOC SYNC phase did not touch native-test lifecycle wording.

## Issues and deviations

- `00-preflight.md` exists but is empty. Recorded here as directed; not treated as a blocker.
- No README/REPL update was made because the searches did not reveal existing lifecycle plan validation claims there.
- No runtime, parser, CLI, prelude, native-test, or Core IR changes were made.

## Next recommended phase

Proceed to the AUDIT phase for issue #451.
