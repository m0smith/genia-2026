# D2a implementation attempt 1 — BLOCKED (#1250)

Parent accepted RED: `74c6545359e6abd9d3118052b68875c90a64c8ed`.
Accepted design baseline: `cc262127c11071f0722f5487e6dcf75452382b75` (#1311).
This is a draft implementation, not accepted GREEN or implemented-language truth.
No RED oracle, public evaluator branch, shared spec or historical R20 oracle changed.

## Semantic STOP

Design `docs/design/pre-r29-model-b-d2-linking-design.md` §3.6 says ordinary records
use existing `_record_handles_none/some`, while OpenClauseRecord keeps its current
expression and union-over-stratum is unchanged. Existing
`_callable_explicitly_handles_none` explicitly includes
`pattern_explicitly_handles_some(record.pattern)` for open clauses. Existing
ordinary `_record_handles_none` does so too.

Accepted RED `test_model_b_d2a_link_dispatch.py:106` instead requires a view with
`f(some(v))` to be some-aware **and not none-aware**. Lines 199–200 likewise require
an absent argument to propagate despite a selected some-aware clause. Preserving
the design and existing expression makes these tests fail: awareness is true and
calling the second fixture with none reaches dispatch, then raises
OpenFunctionNoMatchingCaseError.

No implementation choice can satisfy that combination without changing an accepted
semantic oracle or the design's unchanged awareness requirement. Implementing an
ordinary-view-only exception would also be an unapproved design delta. No such
exception or test change was made. Per AGENTS final rule and implementation prompt,
production changes stopped when the contradiction was established. Resolve the
accepted design/RED discrepancy explicitly; independently review any revised test
SHA before implementation resumes.

## Current draft

Adds exact completion lookup; detached frozen ordinary bases; canonical pure
cross-unit key/shape validation and normalized diagnostic classes; captured unit
clause lists; shared-engine identifier-header/TailCall branch; ordinary-record
awareness delegation; checked one-lock publication; inert exact-G contribution
stores and private completed-module storage. Public IrOpenContribution/IrOpenUse
branches are unchanged. No D2b, E, R29, C++ parity or issue closure.

## Retained execution

Environment unchanged from RED evidence: Linux 6.18.57 x86_64, Python 3.12.14,
pytest 9.1.1; existing uv environment, no dependency install, uv.lock absent.
`UV_CACHE_DIR=/workspace/work/uv-cache uv run --no-sync` was used for every pytest
command below. The existing pytest pythonpath selects candidate src.

1. `pytest -q --maxfail=19 --tb=short tests/unit/test_model_b_d2a_link_core.py`
   — **29 passed**, `green-core-1.log`.
2. `pytest -q --maxfail=19 --tb=short tests/unit/test_model_b_d2a_link_dispatch.py tests/unit/test_model_b_d2a_link_publish.py`
   — **2 failed, 27 passed**, `green-dispatch-publish-1.log`.
3. After correcting a misplaced awareness-helper edit (without changing semantics
   or tests), `pytest -q --maxfail=19 --tb=short tests/unit/test_model_b_d2a_link_core.py tests/unit/test_model_b_d2a_link_dispatch.py tests/unit/test_model_b_d2a_link_publish.py`
   — **2 failed, 56 passed**, `green-focused-2.log`; the two failures above remain.
4. Unaffected preservation checks after the semantic STOP:
   `pytest -q --maxfail=19 --tb=short tests/unit/test_model_b_d1_completion.py tests/unit/test_model_b_d1_preparation_failures.py tests/unit/test_model_b_slice_c_identity.py tests/unit/test_model_b_slice_c_ownership.py tests/unit/test_model_b_slice_c_keys.py tests/unit/test_r20_open_functions_cross_module.py tests/unit/test_r20_open_functions_annotations.py tests/unit/test_r20_open_functions_diagnostics.py tests/unit/test_host_binding_classification_p1_e.py tests/spec/test_model_b_d1_preservation.py tests/spec/test_r20_open_functions_shared_specs.py`
   — **223 passed**, `green-preservation.log`.

No run exceeded the mandatory failure threshold. Do not sum overlapping selections.
Full non-loopback and loopback partitions and later documentation/acceptance gates
were not run after the semantic STOP; they remain mandatory before GREEN can be
accepted. No test interface adaptation was made. All authority documents retain
current wording; no claim of private machinery acceptance is added before GREEN.

## Other blockers

Independent **Claude Code** maintainability and semantic reviews are required by
this task. `command -v claude` found no executable; exhaustive active-tool metadata
search found no Claude Code tool/connector. No Codex agent was presented as Claude.
Those reviews cannot be completed in this environment and have not been claimed.

Executor git network access remains broken (earlier retained proxy failure), so
publication uses the connected GitHub tools, with remote tree SHA matched to local
staged tree and fast-forward lease on the existing branch. Keep the PR draft.
Next action: maintainer resolves awareness design/oracle conflict, obtains any
necessary revised RED review, and supplies Claude Code review access. Resume
implementation and all required gates only once that semantic STOP is resolved.
