# Issue #1269 Slice C GREEN repair R1/R2 (PR #1270)

Starting review SHA: `7cccd2722e7e529fc766022e13ed6d225a5b82f1` (branch `claude/lucid-allen-4t9idb` was reset to it; it held no unmerged commits).

## R1 optimizer divergence
- New tests: `tests/unit/test_model_b_slice_c_optimizer_equivalence.py` (counterexamples A, B, C compared optimizer-off vs on; admission checks; canonical shape still rewritten for 4 calls).
- RED against the reviewed implementation: 9 failed / 4 passed (`issue-1269-r1-red-output.txt`). A optimized `8` vs unoptimized `effect`+`99`; B `7` vs `none("nil")`; C `none("nil")` vs `No matching case for function pick/2 ...`.
- Change (`src/genia/optimizer.py`, +11 lines): rewrite admitted only when `case.clauses` is exactly `[empty, zero, recur]` in that order and the empty arm's counter pattern is a wildcard/binder. Evaluator unchanged; non-admitted programs run their original ordered clauses.
- GREEN: 13 new tests pass; `test_optimizer`, `..._optimizer_retention` (15 literal A4 controls and retention), `test_model_b_optimizer_regression`, `test_model_b_slice_a` pass (107 total).

## R2 guard-local alpha-normalization
- New tests: `tests/unit/test_model_b_slice_c_block_scope_keys.py` (renamed locals, lambda guard blocks, sequential locals, initializer-before-binder, shadowing, free references, scope restoration after block, no initializer execution, direct `IrImmutableBind` block, Codex end-to-end reproducer).
- RED: 8 failed / 1 passed before the change (`issue-1269-r2-red-output.txt`).
- Change (`src/genia/structural_key.py::_block_key`): `IrImmutableBind` initializers keyed in the visible scope, then the binder gets a fresh ordinal; scope is block-local. Pure; nothing evaluated.
- GREEN: 10 tests pass; the reproducer now fails with `open-function-duplicate-clause` and the first clause is unchanged (`f(1)` = 1 with only the first clause).

## Regression results (after both fixes)
- `pytest tests/unit tests/doc -n auto`: 7263 passed, 60 skipped, 2 failed. One failure was `test_state_is_within_the_ratified_size_bounds`, caused by a first draft of my own `GENIA_STATE.md` edit (43010 > 43000 words); I reverted that edit and `tests/doc` is now 397 passed / 35 skipped. The other is the known R28 `test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGINT]` failure Codex also saw on baseline; unchanged and not addressed here.
- Shared in-process: `total=1044 passed=1044 failed=0 invalid=0`.
- Python external adapter: `total=1044 passed=1026 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0` (exact-18 unchanged; the exact-18 parity test was inside the unit run).
- Ruff 0.15.18: all checks passed. `mkdocs build --strict`: built.
- Not re-run separately: host-local Model B tests are inside `tests/unit`; no separate "fast partition" command was identified.

## Documentation
`GENIA_RULES.md` §8.5.1: duplicate-key bullet now covers immutable declarations in guard blocks; the optimizer bullet no longer claims general equivalence and states the admission shape and the evidence's scope. `GENIA_STATE.md` was not changed (word-count gate at its limit); the 69 code-documentation CI errors, C++ conformance (`genia-cpp` #53-#57) and R28 stay as final-merge gates and are out of scope here.
