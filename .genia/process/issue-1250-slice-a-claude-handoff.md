# Claude handoff: #1250 Slice A

Verdict: **GO for independent maintainability review; not GO for merge.**
Reviewer requested: Claude, independent of Codex implementation. No independent PASS is claimed.
Branch: `issue-1250-slice-a`. Base: `d85a56fa66d3369806ab9951b7572c79db98eba3` (approved design #1259). Contract #1255; issue #1250 stays open. #1251 and B–E are not completed by this slice.

## Exact commits

- Preflight: `58ce99e7d45e6216a197ceb11f568824fdae13cf`
- Initial RED: `b3ffef45b6d1d7c0e4e5a3c5f19de20d844cae04`
- Implementation: `13869b33836734e0e5da452e34515949fec13c86`
- Disclosed self-review: `e487c1473b318793d2c4657a42639064a125053d`
- Wire-compatibility RED: `3c96c6fa11ba82bab70b591113b038ac84e6da42`
- Wire-compatibility fix: `11d4b2d963dd3294ec18fe56f2a0e0acec9585c8`
- Documentation/MCP synchronization: `af12db38798677c260d5ac851386afb947771230`

## Scope and exclusions

Python lexer/parser/AST/IR/lowering/normalization/traversal/direct-IR validation and explicit transitional evaluator rejection only. Atomic closed groups retain per-clause annotations. Legacy ordinary IrFuncDef wire representation is preserved, including its existing optional-context omission; new pattern headers retain full context. R20 behavior is retained. No B–E binding enforcement, default-open dispatcher, linker or closed publication; no optional capability, known-host-gap, protocol or core_ir_version change.

No approved grammar deviation. One RED tuple fixture mistakenly used nested tuple atoms outside R20 grammar; corrected to the full argument tuple. A later wire-compatibility regression was independently reproduced by supplemental shared tests (1 failed, 1 passed), committed, then fixed. The exact new-carrier AST projection kind names remain unpinned; no new AST success snapshots were added.

## Verification evidence

- Initial RED: `uv run pytest -q tests/spec/test_model_b_slice_a.py tests/unit/test_model_b_slice_a.py`: 40 failed, 8 passed against unchanged production.
- Baseline: `uv run pytest -q tests/spec/test_r20_open_functions_shared_specs.py tests/unit/test_ir.py`: 86 passed.
- Final affected Slice A/IR/R20 annotations/diagnostics/cross-module suite: 107 passed.
- After wire fix: `uv run pytest -q tests/spec/test_model_b_slice_a.py tests/unit/test_ir_shared_spec_contract.py tests/unit/test_model_b_slice_a.py`: 68 passed.
- All cheatsheets: `uv run pytest -q tests/unit/test_cheatsheet_*.py`: 103 passed.
- Affected documentation/MCP suite: 632 passed, 35 skipped; its sole remaining failure scanned generated `site/search/search_index.json`. Relocating generated output outside the checkout and rerunning all STATE distillation gates: 9 passed. No source assertion was weakened.
- Full partitions were actually run, but **full regression PASS is not claimed**. Initial non-loopback: 6998 passed / 65 skipped / 4 failed. Later non-loopback: 6999 passed / 65 skipped / 12 failed while final doc/golden updates were still being completed. Doc/golden failures were corrected and affected suites rerun. Two xdist MCP output-limit failures passed in isolation. The remaining official-client assertion requires Linux `/proc`; on macOS the harness correctly reports `checked: false`. It remains a Linux CI verification requirement.
- Final loopback partition: 31 passed (24.18s).
- `uv run ruff check .`: PASS.
- `uv run python -m tools.code_documentation --base-ref origin/main --inventory /tmp/1250-final-code-docs.json`: 9563 records, 2804 legacy gaps, zero errors; resolved baseline entries removed, none added.
- MCP generator `--check`, generated function docs `--check`, and prelude documentation coverage/style: PASS.
- Strict MkDocs build: PASS; final generated output is outside source-scanning paths.
- Shared R16 final run: `uv run python -m tools.spec_runner`: **860 total / 860 passed / 0 failed / 0 invalid**. The original run was 858/858; the final run includes both added wire snapshots.

## C++ boundary

Final 29 case classifications: **2 PASS / 27 UNSUPPORTED**, none counted as parity. Unmodified source HEAD `87204407543f2b175c6b185bdc7e625edeb19251`; adapter `contract_revision` `9ab0d3a323c9add045d47db1f476aead96af1e77`. This is ancestor compatibility/gap evidence, not current pinned conformance. Exact cases are in `issue-1250-slice-a-cpp-evidence.md`; #1250 owns the bounded C++ parser/lowering follow-up. New syntax obligations were not hidden behind optional capabilities.

## Independent inspection priorities

1. Balanced parser lookahead vs calls; guarded/pattern arrows and grouped-case rejection; comments/annotations/submissions in closed grouping.
2. Direct-IR malformed groups, competing header channels, nested host-local nodes and annotation ownership; inspect validation depth, not just passing constructor tests.
3. Traversal of all new and R20 expression children; conservative optimizer call counting and publication boundaries.
4. Legacy wire compatibility vs new pattern context preservation.
5. Explicit evaluator/native-test/route-discovery rejection before effects; no accidental B–E implementation.
6. Maintained source documentation and the additional wire fix beyond the earlier self-review range.
7. C++ unsupported boundary and Linux CI results before any merge decision.

After independent maintainability PASS: resolve any findings, obtain independent truth audit, and confirm Linux CI. Do not self-merge, close #1250, or begin Slice B. Full #1251 integration remains separate.

## Files in the reviewed branch

- `.genia/process/issue-1250-slice-a-cpp-evidence.md`
- `.genia/process/issue-1250-slice-a-implementation.md`
- `.genia/process/issue-1250-slice-a-maintainability-self-review.md`
- `.genia/process/issue-1250-slice-a-preflight.md`
- `.genia/process/issue-1250-slice-a-red.md`
- `.github/code-documentation-baseline.json`
- `GENIA_REPL_README.md`
- `GENIA_RULES.md`
- `GENIA_STATE.md`
- `README.md`
- `apps/mcp/mcp.genia`
- `docs/architecture/core-ir-portability.md`
- `docs/book/03-functions.md`
- `docs/cheatsheet/core.md`
- `docs/cheatsheet/unix-power-mode.md`
- `docs/contract/semantic_facts.json`
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
- `hosts/python/ir_normalize.py`
- `spec/ir/model-b-a-annotated-immutable.yaml`
- `spec/ir/model-b-a-calls.yaml`
- `spec/ir/model-b-a-closed-grouped.yaml`
- `spec/ir/model-b-a-closed-run.yaml`
- `spec/ir/model-b-a-closed.yaml`
- `spec/ir/model-b-a-guard-identifier.yaml`
- `spec/ir/model-b-a-guard-pattern.yaml`
- `spec/ir/model-b-a-immutable.yaml`
- `spec/ir/model-b-a-legacy-rest.yaml`
- `spec/ir/model-b-a-legacy-some-context.yaml`
- `spec/ir/model-b-a-ordinary-independent.yaml`
- `spec/ir/model-b-a-pattern-list.yaml`
- `spec/ir/model-b-a-pattern-literal.yaml`
- `spec/ir/model-b-a-pattern-map.yaml`
- `spec/ir/model-b-a-pattern-some-context.yaml`
- `spec/ir/model-b-a-pattern-string-body.yaml`
- `spec/ir/model-b-a-pattern-tuple.yaml`
- `spec/ir/model-b-a-split.yaml`
- `spec/manifest.json`
- `spec/parse/model-b-a-guard-arrow.yaml`
- `spec/parse/model-b-a-guard-grouped.yaml`
- `spec/parse/model-b-a-index.yaml`
- `spec/parse/model-b-a-missing-body.yaml`
- `spec/parse/model-b-a-missing-init.yaml`
- `spec/parse/model-b-a-mixed-reverse.yaml`
- `spec/parse/model-b-a-mixed.yaml`
- `spec/parse/model-b-a-nested.yaml`
- `spec/parse/model-b-a-pattern-arrow.yaml`
- `spec/parse/model-b-a-pattern-grouped.yaml`
- `spec/parse/model-b-a-target.yaml`
- `src/genia/ast_nodes.py`
- `src/genia/evaluator.py`
- `src/genia/interpreter.py`
- `src/genia/ir.py`
- `src/genia/lexer.py`
- `src/genia/lowering.py`
- `src/genia/optimizer.py`
- `src/genia/parser.py`
- `src/genia/server_route_binding.py`
- `tests/data/mcp_language_profile.golden.json`
- `tests/spec/test_model_b_slice_a.py`
- `tests/unit/test_execution_process_core_ir_regression.py`
- `tests/unit/test_model_b_slice_a.py`
- `tests/unit/test_r28_mcp_language_profile.py`
- `tests/unit/test_r28_mcp_language_registry.py`
- `tools/code_documentation.py`
