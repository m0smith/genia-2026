# Issue #853 Audit — E21-1 Numeric Source Classification

Status: durable audit evidence for issue #853 (E21-1). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority.

## Acceptance criteria verification

| Criterion | Result |
|---|---|
| `1` classifies as Integer source | PASS — `classify_numeric_literal("1")` -> `kind="integer"`; `spec/parse/parse-r21-integer-source-classification.yaml` |
| `1.0`, `1.25`, `1e3`, `1E+3`, `1.25e-2` classify as Decimal source | PASS — unit tests `test_classify_decimal_*`; `spec/parse/parse-r21-decimal-*.yaml` |
| malformed exponents rejected deterministically | PASS — lexer raises `SyntaxError("Malformed exponent in numeric literal at <pos>")`; `spec/parse/parse-error-r21-malformed-exponent-*.yaml` |
| `.5` and `5.` are not accepted as R21 numeric literals | PASS — both raise `SyntaxError` (pre-existing bare-`.` punctuation gap); `spec/parse/parse-error-r21-leading-dot-rejected.yaml`, `parse-error-r21-trailing-dot-rejected.yaml` |
| `-1.25` remains unary minus applied to positive Decimal source | PASS — `test_parser_unary_negative_is_unary_minus_over_positive_decimal_literal` |
| Decimal classification/normalization never constructs a host binary float | PASS — `test_classify_never_calls_float` statically asserts no `float(...)` call anywhere in `src/genia/numeric_source.py` |
| existing Integer source behavior remains compatible | PASS — `Number.value` construction for Integer literals is byte-for-byte unchanged (`int(tok.text)`); huge-integer case exercised |
| failing parse/unit evidence authored before implementation | PASS — commit `b964425` (tests) precedes commit `47ce53e` (implementation) |

## Regression evidence

- `uv run python -m tools.spec_runner` -> `Summary: total=714 passed=714 failed=0 invalid=0` (703 baseline + 11 new R21 parse cases)
- `uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py -q` -> 1 passed (updated hardcoded total 703->714, passed 685->696, matching exactly the 11 new parse-category cases; no other count moved)
- `uv run pytest -n auto -q -m "not loopback"` -> 11 failed, 4345 passed. All 11 failures were independently reproduced against pre-R21 `main` (unstaged working tree with this ticket's changes stashed) with an identical failure set and identical assertion text: `test_host_template_structure.py::test_planned_host_readmes_reference_template[cpp]`, `test_r11_release_truth_sync_617.py`, `test_r12_release_truth_sync_650.py`, `test_r13_release_truth_sync_677.py` (x1), `test_r7_web_capability_sync.py` (x2), `test_roadmap_publishing_697.py`, `test_semantic_doc_sync.py::test_r3_native_test_roadmap_stays_separate_from_r4_lifecycle_generalization`, `test_native_test_runner.py` (x2, sandbox file-permission artifacts: `chmod` does not restrict read for the sandbox's effective user). None reference numeric literals, the lexer, the parser, or `Number`/`IrLiteral`. These are pre-existing baseline failures unrelated to E21-1 and are not repaired by this ticket (repairing unrelated pre-existing failures is outside E21-1's scope and risks the kind of scope creep #855's stop rule exists to prevent).
- `uv run pytest -n auto -q -m loopback` -> 26 passed, 0 failed.
- `uv run pytest tests/unit/test_r21_numeric_source_classification_853.py tests/spec/test_parse_shared_spec_runner.py -q` -> 30 + 15 passed.

## Scope boundary check

- No change to `lowering.py` or `ir.py`: `IrLiteral(node.value, ...)` construction for `Number` nodes is untouched; grep confirms zero references to the new `source_kind`/`digits`/`coefficient`/`exponent` fields outside `numeric_source.py`, `ast_nodes.py`, `parser.py`, and this ticket's own tests.
- No new Core IR node family; `docs/architecture/core-ir-portability.md`'s frozen node list is unmodified.
- No evaluator Decimal materialization, arithmetic, equality, map-key, rendering, formatting, or JSON change — verified by inspection of the diff (`git diff main...HEAD -- src/genia/evaluator.py src/genia/equality.py src/genia/values.py` is empty).
- No R22/R23 semantics introduced.

## Verdict

**PASS.** E21-1's full acceptance criteria are met with shared evidence, the
implementation strictly avoids host binary-float construction in the new
classification path, no Core IR node family or evaluator numeric semantics
changed, and the only regression-suite failures present are reproduced
identically on `main` before this branch's changes.

## Doc Distillation

Reviewed `GENIA_STATE.md` section 9.21 and the `GENIA_REPL_README.md`
literals bullet added by this ticket for conciseness against
`docs/process/run-change.md`'s Doc Distillation phase. Both additions are
already minimal (state the landed behavior and its explicit non-goals in
one place each, with no duplicated prose across the two files) — no further
trimming was needed. This process's own preflight/contract/design/audit
artifacts remain under `docs/analysis/` and `docs/design/` as durable
history, matching existing precedent (for example
`docs/analysis/issue-836-portable-cross-module-preflight.md`,
`docs/analysis/r20-release-truth-audit.md`).
