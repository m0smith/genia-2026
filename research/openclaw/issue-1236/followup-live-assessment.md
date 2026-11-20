# #1236 — second OpenClaw live run: skeptical assessment

**Status: RESEARCH INCOMPLETE — NO CONTRACT OR IMPLEMENTATION AUTHORIZATION.**
**Isolation:** `research/openclaw-1236-isolated-20261120`, pinned evidence SHA `7475646d44fee58bc98294ba78e22727eaab63f1`.
**Observed on Benjamin:** November 20, 2026, `issue-1236-callable-flow-parity-evidence`; v0.9 controller `FAIL`; researcher 121.473 s; total 124.056 s; 5,817 prompt tokens; zero tool calls; reviewer NOT_RUN.
**Deterministic failure:** researcher did not cite required source path `src/genia/callable.py`. Although the controller retrieved and pinned `invoke_callable`, the answer did not address that file. Do not relabel as a passed run.
**Evidence:** user-supplied live transcript, locally in `/tmp/genia-openclaw-controller/runs/issue-1236-followup/report.md` on Benjamin. This assessment is a separate skeptical human-assisted source inspection; it does not claim the entire generated report was stored in GitHub.

## What the model got right

- `GENIA_STATE.md` specifies ordinary data application for `x |> f` and `x |> f(y)`; this does not define reusable callable composition.
- `src/genia/evaluator.py:1106–1120` includes `stage_index + 1` in pipeline error reporting.
- `src/genia/values.py:994–1019` delegates `GeniaFlow.consume()` to its single-use `GeniaSeq`; Flow reuse is a material risk for a proposed `compose(...)`.
- C++ has documented unsupported cases, including pipelines inside call arguments; portable composition needs a supported-host matrix.

## Material errors / unsupported conclusions

1. **C++ support contradicted by authority.** Model says Flow phase 1 and `map`/`filter`/`collect`/`reduce` are Python-only and that C++ has no Flow composition support. `GENIA_STATE.md:120–135` explicitly says C++ supports a bounded Flow phase 1 including those stages and terminals. Its limitations are specific, not complete absence of Flow.
2. **Pipeline application ≠ reusable callable.** `x |> f(y) |> g(z)` establishes a sequential evaluated expression (given compatible values and calls), not construction of a reusable function `compose(f,g)`. No inert definition, fresh-input repeat invocation, closure capture, or callable-as-data collision tests were supplied.
3. **Incorrect confidence on new Core IR.** The original claim that explicit `compose` requires a new node was unfounded. The follow-up swung too far: it now claims ordinary call syntax proves no new node is required. That architectural choice is not resolved by the excerpts; compare ordinary callable implementation against syntax/IR alternatives under #1236 contract gates.
4. **Flow lifecycle overclaims.** Single-use applies to a particular source-bound Flow's consumption, not necessarily each intermediate pipeline stage or arbitrary callable results. `GeniaFlow.consume()` does not prove that “no intermediate state” exists or that reusable composition must store previously evaluated results. A reusable callable would normally invoke its stage logic anew on fresh input.
5. **Test source ≠ execution evidence.** `tests/unit/test_flow_phase1.py` contains single-use and early-close tests, but this run did not execute them. Their presence is evidence of intended checks, not observed passing behavior in this investigation.
6. **Precision of porting claims.** The model describes the Flow spec as “explicit stage composition”; it is an existing pipeline's application stages, not an approved first-class composition operator. It also calls Flow entirely Python-only, conflicting with the state document.
7. **Incomplete evidence boundary.** The model omitted the required `src/genia/callable.py` citation; review of dispatch implementation and negative cases remains open. It also did not inspect the actual C++ codebase in this run.

## Remaining decisions

- Decide whether an inert ordinary `compose(...)` can preserve existing `|>` semantics without parser/IR changes; do not assume yes or no.
- Specify closure/callable capture, independent invocation, and correct use of fresh Flow sources.
- Reuse existing Outcome and terminal semantics unless approved evidence identifies a necessary extension.
- Verify stages and diagnostics for nested composition, early-close propagation, error spans, terminal-then-transform and incompatible callable-as-data cases.
- Build explicit shared parse/IR/eval/flow/error cases, a C++ parity or issue-backed gap disposition, and independent contract approval **before** implementation.

**Decision:** The v0.9 controller correctly failed on a missing evidence citation. The generated analysis is not trustworthy enough for contract choice. The existing independent source inventory `followup-evidence.md` is the grounded baseline; update only this isolated research branch. Do not touch `main`, R29/#1328, or source-of-truth root docs.

Any future CODEX implementation prompt must read latest `AGENTS.md`, respect the approval gates, and update `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, and `README.md` only to reflect verified implemented behavior.
