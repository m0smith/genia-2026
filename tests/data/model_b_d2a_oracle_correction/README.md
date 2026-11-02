# D2a awareness oracle correction — test only (#1250)

Parent implementation candidate: 073ed63e885dffcb4393aa55acd9851ff618e1a3.
Original RED oracle: 74c6545359e6abd9d3118052b68875c90a64c8ed.
Design: #1311, cc262127c11071f0722f5487e6dcf75452382b75 §3.6.
This changes no production code, historical R20 spec or authority document.

## Independent source verification before correction

R20 contract `docs/design/r20-open-functions-contract.md` §5.2 explicitly says a
none argument reaches dispatch when a selected clause contains a none **or some**
pattern. A resulting pattern miss is a no-matching-case failure. Other shapes do
not affect awareness. D2 §3.6 preserves the existing OpenClauseRecord expression.
GENIA_RULES §8.5 and baseline callable.py none-awareness predicate agree; the Model
B contract introduces no contrary Option rule. Latest authority blobs match the
accepted baseline; no documentation semantic rewrite is needed.

On the pre-GREEN checkout 74c65453 (review-red2 worktree), historical R20 shared
wrappers and cross-module tests: **72 passed**. Direct source probe with existing
runtime `open f(some(v)) = v + 10`: `f(some(7))` returns 17;
`f(none("absent"))` raises OpenFunctionNoMatchingCaseError with exact message
`No matching case for function f/1 with arguments [none("absent")]`.
Historical specs include r20-option-some-pattern-in-stratum-dispatches,
r20-option-other-arity-clause-not-aware and cross-module contribution awareness.
The historical suite does not directly pin the some-pattern/none cross-product;
the explicit contract and direct pre-GREEN probe establish that observation.

## Changed expectations (same two test functions)

- Old: some-aware unary contribution is **not** none-aware. New: it is both
  some-aware and none-aware, preserving §5.2.
- Old: passing none to that view propagates identical none. New: assert the exact
  OpenFunctionNoMatchingCaseError; its selected some pattern admits none but cannot
  match it. Keep actual some invocation returning 17 and binary none handling 9.
- Preserve the original stratum-exclusion purpose with a separate view containing
  only unaware unary clauses plus the binary none pattern. Its unary call must
  propagate the identical none; binary invocation still returns 9. Simply removing
  the negative awareness assertion would have lost this coverage.

## Verification and discrimination

Python 3.12.14, pytest 9.1.1, existing uv environment; Linux host unchanged. Prefix
`UV_CACHE_DIR=/workspace/work/uv-cache uv run --no-sync pytest -q --maxfail=19`.
No dependency/source/runtime installation or monkeypatch persisted.

- `tests/unit/test_model_b_d2a_link_dispatch.py`: **17 passed** on candidate runtime.
- All three D2a link test modules: **58 passed** on candidate runtime. This is
  focused oracle validation, not full GREEN acceptance or later-gate approval.
- Revised two functions over original RED tree in isolated oracle-red-check
  worktree: **2 failed, 15 deselected**, missing target constructor seam. This is
  expected seam RED; downstream oracle discrimination is tested separately below.
- Historical selection on pre-GREEN tree:
  `tests/spec/test_r20_open_functions_shared_specs.py tests/unit/test_r20_open_functions_cross_module.py`
  **72 passed** (UV_PROJECT_ENVIRONMENT points to the existing repo .venv).

Mutation reproduction (the preserved oracle_mutant.py is a pytest plugin, not a
runtime patch): put its directory on PYTHONPATH alongside candidate src, set
ORACLE_MUTATION to false, true or leak, then run
`uv run --no-sync pytest -q --maxfail=19 --tb=short -p oracle_mutant tests/unit/test_model_b_d2a_link_dispatch.py -k 'option_awareness_uses_the_union or some_invocation_and_awareness'`.
Each intentionally incorrect predicate yielded **2 failed / 15 deselected**:
false incorrectly propagates all none, true incorrectly admits every stratum,
leak consults arity 2 for every view. Thus both corrected tests reject all three
incorrect implementations, including loss of cross-arity isolation. Exact logs
are retained here; failures are mutation evidence, not implementation failures.

No R20 behavior, D2b activation, merge or GREEN acceptance is authorized by this
correction. Submit its separate test-only SHA on #1250 for independent Codex review.
Claude Code reviews, full test partitions and other GREEN gates remain pending.
