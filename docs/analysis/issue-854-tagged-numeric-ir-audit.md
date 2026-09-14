# Issue #854 Audit — E21-2 Tagged Portable Numeric IrLiteral Payloads

Status: durable audit evidence for issue #854 (E21-2). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority.

## Acceptance criteria verification

| Criterion | Result |
|---|---|
| Integer and Decimal source lower through `IrLiteral` with canonical tagged string payloads | PASS — `test_lowering_integer_literal`, `test_lowering_decimal_dotted_literal`, `spec/ir/r21-integer-literal-tagged-payload.yaml`, `spec/ir/r21-decimal-dotted-literal-tagged-payload.yaml` |
| huge Integer payloads preserve exact digits | PASS — `test_lowering_huge_integer_literal_exact_digits`; `spec/ir/r21-huge-integer-literal-tagged-payload.yaml` |
| equivalent Decimal spellings normalize to identical payloads while retaining Decimal kind | PASS — `test_lowering_equivalent_decimal_spellings_identical_payload`; `spec/ir/r21-decimal-equivalent-spellings-identical-payload.yaml` |
| unary negative numeric source lowers as unary minus around the positive tagged literal | PASS — `test_lowering_unary_negative_wraps_positive_tagged_literal`; `spec/ir/r21-unary-negative-decimal-tagged-payload.yaml` |
| slash/division lowering is unchanged | PASS — `test_lowering_slash_remains_ordinary_binary`; `spec/ir/r21-slash-remains-ordinary-binary.yaml` |
| no host-native binary float appears in portable numeric payloads | PASS — `test_lowering_no_host_native_float_in_payload`; every payload field is a `str` |
| no new numeric Core IR node family is introduced | PASS — `IrLiteral` reused unchanged; `docs/architecture/core-ir-portability.md`'s frozen node list is unmodified (only the invariants prose gained a documenting bullet) |
| Python in-process and R16 subprocess IR evidence agree for applicable cases | PASS — `tests/spec/test_python_protocol_adapter_parity_762.py` (updated totals 714→721, 696→703, exactly the 7 new ir-category cases) |

## Scope boundary check

- `src/genia/equality.py` and `src/genia/values.py`: zero diff against `main` (`git diff main...HEAD -- src/genia/equality.py src/genia/values.py` empty). No R22 equality/map-key semantics touched.
- `src/genia/evaluator.py`: 8 lines added, 1 changed — exactly the two `IrLiteral` value unwrap sites plus the import, matching the documented compatibility shim. No other evaluator behavior touched.
- No new numeric runtime kind, arithmetic operator, conversion function, or rendering/formatting/JSON behavior anywhere in the diff.
- `IrPatLiteral` (case-pattern numeric literals) is unchanged by design — grep confirms `lowering.py`'s `lower_pattern` still constructs `IrPatLiteral(pattern.value)` with the plain AST `Number.value`, not the tagged payload.
- `numeric_literal_runtime_value` is the only function in `numeric_source.py` that calls `float()`, verified by `test_only_runtime_value_shim_calls_float_in_module`; `classify_numeric_literal` and its private helpers remain float()-free, verified by the (scope-corrected) `test_classify_never_calls_float` from #853.

## Regression evidence

- `uv run python -m tools.spec_runner` → `Summary: total=721 passed=721 failed=0 invalid=0` (714 baseline-after-#853 + 7 new R21 ir cases)
- `uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py -q` → 1 passed
- `uv run pytest -n auto -q -m "not loopback"` → 4370 passed, 10 failed; all 10 are the identical pre-existing baseline failures already tracked in issue #859 (confirmed unchanged in count and identity from the #853 audit — no new failures introduced by this ticket's evaluator/optimizer/lowering changes or the 13-fixture migration)
- `uv run pytest -n auto -q -m loopback` → 26 passed, 0 failed
- `uv run pytest tests/unit/test_r21_tagged_numeric_ir_854.py tests/unit/test_r21_numeric_source_classification_853.py tests/unit/test_ir.py tests/unit/test_ir_shared_spec_contract.py tests/unit/test_optimizer.py -q` → all passed

## Verdict

**PASS.** E21-2's full acceptance criteria are met with shared in-process and
subprocess-protocol evidence, the tagged payload never contains a host
binary float, no Core IR node family was added, `IrPatLiteral` was
correctly left out of scope, and the evaluator compatibility shim is
verified to reconstruct exactly the same value the evaluator produced
before this ticket — no R22 runtime semantics were introduced.

## Doc Distillation

Reviewed `GENIA_STATE.md` section 9.22 and the
`docs/architecture/core-ir-portability.md` lowering-invariants bullet added
by this ticket for conciseness. Both are scoped to stating the landed
payload shape, the unaffected sign/slash lowering, the compatibility-shim
boundary, and explicit non-goals — no duplication across the two files and
no further trimming needed. Process artifacts (preflight/contract/design)
remain under `docs/analysis/` and `docs/design/` as durable history,
matching #853's precedent.
