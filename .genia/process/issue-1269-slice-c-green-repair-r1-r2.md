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
- `pytest tests/unit tests/doc -n auto`: 7263 passed, 60 skipped, 2 failed. One failure was `test_state_is_within_the_ratified_size_bounds`, caused by a first draft of my own `GENIA_STATE.md` edit (43010 > 43000 words); I reverted that edit and `tests/doc` is now 397 passed / 35 skipped. The other was `tests/unit/test_r28_mcp_stdio_lifecycle.py::...[SIGINT]` in this author environment. CORRECTION (Codex review 5669388186): Codex reproduced a baseline MCP discovery-cleanup failure, not a proven baseline SIGINT failure; this author run did not establish a baseline for the SIGINT test. R28 stays a separate investigation.
- Shared in-process: `total=1044 passed=1044 failed=0 invalid=0`.
- Python external adapter: `total=1044 passed=1026 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0` (exact-18 count unchanged). CORRECTION: the exact-18 pytest (`tests/spec/test_python_protocol_adapter_parity_762.py`) is under `tests/spec`, not in the `tests/unit tests/doc` selection, and was not run in that earlier pass.
- Ruff 0.15.18: all checks passed. `mkdocs build --strict`: built.
- Not re-run separately: host-local Model B tests are inside `tests/unit`; no separate "fast partition" command was identified.

## Documentation
`GENIA_RULES.md` §8.5.1: duplicate-key bullet now covers immutable declarations in guard blocks; the optimizer bullet no longer claims general equivalence and states the admission shape and the evidence's scope. `GENIA_STATE.md` was not changed (word-count gate at its limit); the 69 code-documentation CI errors, C++ conformance (`genia-cpp` #53-#57) and R28 stay as final-merge gates and are out of scope here.

---

# Second repair round (Codex review 5669388186)

Starting commit: `4b4737ff14dd2b42ae53b9b943a8c35988ffe8ef`. RED output: `issue-1269-r1ab-r2a-red-output.txt` (16 failed / 30 passed before the change).

## New defects and RED reproductions
- **R1-A recursive-pattern constraints.** `(n, [1, ..rest])`, repeated binders `(n, [n, ..rest])`, nested-list heads and `(h, ..h)` were admitted; optimized `8` vs unoptimized grouped-case miss.
- **R1-B callee resolution.** Rebinding (`alias = pick; pick = (n, xs) -> 99`): optimized `8` vs `99`. Rest binder named `pick` and a parameter named `pick`: optimized `8` vs TypeError. A earlier pattern clause `pick(1, [_, .._]) = 55` in the same group: optimized `9` vs `55`.
- **R2-A annotation scope.** Direct IR `IrBlock([IrImmutableBind(local, IrVar("x"), annotations=[IrAnnotation("meta", IrMap([("v", IrVar(ref))]))]), IrLiteral(True)])`: alpha-equivalent annotated locals produced different keys; bound-vs-free references produced equal keys; install of the alpha-equivalent clause was accepted.

## Minimal changes
- `optimizer.py`: recursive arm must have wildcard/fresh-binder head, pairwise-distinct counter/head/rest binders, and `fn.name` must not equal any of them or a parameter.
- `evaluator.py`: `_traversal_recursion_is_stable` - the fast path runs only if `fn_name` resolves (ordinary lookup, no autoload) to a `GeniaFunctionGroup` whose only fixed arity-2 record owns this loop body; otherwise the retained ordered case runs (exact errors/effects). One check at entry suffices because the recognized arms run no user code between steps.
- `structural_key.py`: immutable-declaration annotations are keyed after the binder enters scope.

## Tests
- `test_model_b_slice_c_optimizer_equivalence.py`: now 31 tests (R1-A: 7 constrained shapes + 3 unconstrained controls; R1-B: rebinding, rest/param shadowing, group dispatch; non-vacuity: stable canonical program never reaches `eval_case_expr`, rebinding does).
- `test_model_b_slice_c_block_scope_keys.py`: annotation alpha-equivalence, bound-vs-free, sequential, shadowing/restoration, direct-IR duplicate installation (same group object and records preserved after rejection), annotation-effect witness. The purity test now traps the real `Evaluator` methods, so the witness is connected to the operation under test; the "group unchanged" check now inspects the rejected group.
- Optimizer, retention (15 A4 controls), Slice A, keys and optimizer-IR suites: 291 passed together with the new tests.

## Documentation
`GENIA_RULES.md` §8.5.1 optimizer and duplicate-key bullets rewritten to the proven restrictions; `GENIA_STATE.md` line 2937 replaced (shorter) with Codex's suggested wording. No other root, semantic-facts, MCP-profile, host or roadmap statement changed; no word-count waiver.

## Limitations
Optimizer equivalence is evidenced by the on/off comparisons above, not proven in general. Separate final-integration gates unchanged: code-documentation CI (72 errors), C++ conformance (9 failures, `genia-cpp` #53-#57), final-head CI/host parity, R28 investigation, #1251, Slice D/E and R29.

## Second-round validation (commands actually run)
| Check | Command | Result |
|---|---|---|
| New + repaired tests | `uv run pytest tests/unit/test_model_b_slice_c_optimizer_equivalence.py tests/unit/test_model_b_slice_c_block_scope_keys.py` | 48 passed (31 + 17) |
| Optimizer/retention/Slice A/keys/optimizer-IR | `pytest` on `test_optimizer`, `..._optimizer_retention`, `test_model_b_optimizer_regression`, `test_model_b_slice_a`, `..._keys`, `..._optimizer_ir` plus the two new files | 291 passed (before the harness-injection test fix below) |
| Unit + doc | `uv run pytest tests/unit tests/doc -q -n auto` | 7288 passed, 60 skipped, 2 failed: `test_host_binding_classification_p1_e` (my new test used `env.set`; fixed by defining the callback through `run_source`, re-run 35 passed with the block-scope file) and the R28 `[SIGINT]` lifecycle test (not investigated; see correction above) |
| Doc tests after final edits | `uv run pytest tests/doc -q -n auto` | 397 passed, 35 skipped |
| Shared in-process | `python -m tools.spec_runner` | exit 0, `total=1044 passed=1044 failed=0 invalid=0` |
| Python external adapter | `python -m tools.spec_runner --host "python -m hosts.python.protocol_adapter" --host-jobs 2 --host-timeout 120` | exit 0, `1026 passed, 18 unsupported, 0 other` |
| Exact-18 parity pytest | `uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py` | exit 0, 1 passed (521 s) |
| Ruff 0.15.18 / strict MkDocs | `uv run ruff check .` / `uv run python -m mkdocs build --strict` | exit 0 / exit 0 |
Not run: the full unit+doc selection was not re-run after the test-only harness fix; the rest of `tests/spec` and any whole-repository slow partition were not run in this round.

---

# Third repair round: numeric optimizer correctness (Codex checkpoint 6452663432)

Starting commit: `f601b42ea745b39a3de970c45301be83da3d930f`. RED output: `issue-1269-n1n2-red-output.txt` (9 failed / 33 passed against `f601b42e`).

## Violated numeric contract and RED reproductions
- **N1 Float64.** `pick(float64(1), [7, 8])`: unoptimized `none("type-error", {source: "-", left: "float", right: "int"})` (ordinary `-` rejects mixed exact/Float64 operands), optimized `8`. The loop used Python `n - 1`. Also `float64(2)` and `float64(-1)` counters.
- **N2 Decimal decrement.** `n - 1.0` was recognized as the decrement because `numeric_literal_runtime_value(Decimal 1.0) == 1`. With the private 8-bit resource seam and `pick(-255, [7, 8])`: unoptimized `numeric-resource-limit`, optimized `none("nil")`. The same divergence reproduced at the unchanged production bound with a counter of `-(2**14000)` (the control runs in well under a second).

## Minimal changes
- `optimizer.py::_is_integer_literal_one`: accepts only an Integer-kind literal payload (or a bare Python `int` 1); Decimal `1.0`, floats and Booleans are no longer a recognized decrement, so such functions keep their ordered clauses.
- `evaluator.py::eval_list_traversal_loop`: the fast path requires `type(n_value) is int`. Float64, Decimal, Rational and Boolean counters run the retained case. For Python ints, `n - 1` is exactly what ordinary evaluation computes and has no resource check, so the whole traversal (not only the start) is equivalent. The unreachable `isinstance(n_value, (int, float))` re-check inside the loop is left as is.

## Tests (`test_model_b_slice_c_optimizer_equivalence.py`, now 73 tests)
N1 and N2 regressions (seam at 8 bits and the production-bound control), decimal-decrement non-admission, an 18-call by 2-limit numeric audit (integers, negatives, zero, floats, Float64, Boolean, rational, large power, empty list) comparing optimizer on/off, and a non-vacuity test that an Integer counter still never reaches `eval_case_expr`. Previously repaired R1/R2 files, A4 retention, Slice A, keys, optimizer-IR and `test_r22_misuse_resource_limits_894`: 353 passed together.

## Documentation
`GENIA_RULES.md` §8.5.1: Integer-literal decrement, and Integer-only fast path with the retained case for other numeric counters. `GENIA_STATE.md`, README, REPL README, semantic facts, MCP profile, host docs and roadmap: reviewed, no statement contradicted (none mention the numeric gate), so unchanged.

## Third-round validation (commands actually run, final tree)
| Check | Command | Result |
|---|---|---|
| Optimizer/R1/R2/retention/keys/R22 limits | `pytest` on the equivalence, block-scope, optimizer, retention, optimizer-regression, Slice A, keys, optimizer-IR and `test_r22_misuse_resource_limits_894` files | 353 passed |
| Unit + doc | `uv run pytest tests/unit tests/doc -q -n auto` | exit 1: 7331 passed, 60 skipped, 1 failed: R28 `test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGINT]` (separate R28 gate, not investigated; Codex established only a baseline discovery-cleanup failure) |
| Shared in-process | `python -m tools.spec_runner` | exit 0, 1044 passed, 0 failed |
| External adapter | `python -m tools.spec_runner --host "python -m hosts.python.protocol_adapter" --host-jobs 2 --host-timeout 120` | exit 0, 1026 passed, 18 unsupported, 0 other |
| Exact-18 parity pytest (separate) | `uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py` | exit 0, 1 passed (624 s) |
| Docs / lint | `uv run pytest tests/doc -n auto`; `uv run ruff check .` (0.15.18); `uv run python -m mkdocs build --strict` | 397 passed, 35 skipped; all passed; exit 0 (an earlier mkdocs run launched while the test chain was running exited 1 and was not investigated; the rerun on an idle machine exited 0) |
Not run: the rest of `tests/spec` and any whole-repository slow partition. Remaining separate gates are unchanged: code-documentation CI, C++ #53-#57, final-head CI/host parity, R28, #1251, Slice D/E, R29.
