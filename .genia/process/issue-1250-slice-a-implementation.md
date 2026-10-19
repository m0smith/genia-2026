# Slice A implementation evidence

RED prerequisite: b3ffef4. Base: d85a56fa66d3369806ab9951b7572c79db98eba3.

Implemented: longest-match declaration token; explicit AST/portable immutable, pattern and atomic closed-group records; parser grouping/mixing errors; stable legacy IrFuncDef normalization; recursive R20/new-node traversal; direct-IR structure validation; transitional evaluator rejection before child effects; conservative optimizer traversal; documentation discovery of pattern declarations. Native discovery evaluates and explicitly rejects new declarations; direct route discovery also rejects rather than omitting declarations.

Excluded: B–E execution, binding policy, default-open dispatcher, linking and closed publication. No optional capability, known-gap, protocol-version or Core IR version changes.

Validation:

- Final Slice A/IR/R20 annotation/diagnostic/cross-module tests: 107 passed (1.04s).
- Earlier focused IR/inventory/native discovery/code-documentation suite: 139 passed before six supplemental hardening tests; final affected tests above pass.
- Existing R20 shared/IR baseline: 86 passed before production changes.
- `uv run python -m tools.spec_runner`: 858 passed, 0 failed, 0 invalid before final direct-IR-only hardening; source conformance unchanged.
- `uv run pytest -n auto -q -m "not loopback"`: 6998 passed, 65 skipped, 4 failed. One is pending portable-IR documentation sync. Two MCP output-limit tests passed on isolated rerun. The remaining official-client disconnect assertion requires Linux `/proc`; macOS reports `checked: false`. No skip or assertion was changed. This partition ran while later hardening was still in progress; final verification remains required.
- `uv run pytest -n auto -q -m loopback`: 31 passed.
- `uv run ruff check .`: PASS.
- `uv run python -m tools.code_documentation --base-ref origin/main --inventory /tmp/1250-code-docs-verified.json`: 9563 records, 2805 legacy gaps, 0 errors. Only 14 resolved baseline entries removed; none added.
- `git diff --check`: PASS.

Test correction: the initial tuple fixture incorrectly assumed nested tuple atoms, which R20 does not accept. Replaced with a full argument tuple (`f("key",x) = x`), preserving the approved grammar. Supplemental annotation fixtures use the existing required `@test "description"` form.

C++ unchanged: source HEAD 87204407543f2b175c6b185bdc7e625edeb19251; adapter contract_revision 9ab0d3a323c9add045d47db1f476aead96af1e77. RED cases: 2 PASS (bare calls, noncontiguous ordinary declarations), 25 UNSUPPORTED. Exact case records are in the RED artifact. This ancestor-pinned binary is compatibility/gap evidence, not current pinned conformance. #1250 owns the C++ parser/lowering follow-up.
