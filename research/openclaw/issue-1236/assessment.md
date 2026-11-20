# Issue #1236 — OpenClaw v0.9 research run and independent assessment

**Status:** READ-ONLY RESEARCH COMPLETE; **DESIGN/CONTRACT NOT ACCEPTED**.
**Isolation:** branch `research/openclaw-1236-isolated-20261120`; no implementation, shared spec, runtime, source-of-truth doc, or R29 changes.
**Research issue:** https://github.com/m0smith/genia-2026/issues/1236
**Pinned evidence SHA:** `7475646d44fee58bc98294ba78e22727eaab63f1`
**Live execution:** Benjamin / OpenClaw v0.9 / `case.json` (user-provided transcript, November 20, 2026).
**Result:** controller `PASS`, researcher 106.914 s, total 109.249 s, prompt tokens 5,457, bridge calls 0; reviewer `NOT_RUN`.
**Important:** v0.9 PASS checks bounded source/provenance requirements; it is not semantic acceptance, independent review, or test execution of Genia. The terminal report remains in the local controller at `runs/issue-1236-research/report.md`; this note records its substantive conclusions and assessment, not a claim that the generated report has been copied to GitHub.

## Source-supported observations

- `src/genia/evaluator.py:1135–1150`: `eval_pipeline` evaluates `node.source` first, applies `node.stages` in order, propagates `none`/`err` by returning early, and wraps stage exceptions via `_wrap_pipeline_stage_error(exc, index, stage, stage_value)`.
- `src/genia/evaluator.py:1185–1208`: call-form and bare-name stages invoke the resolved callable with the preceding value (plus any explicit arguments), through option-lifting logic. This supports data-application, not a documented callable-composition interpretation of `|>`.
- `spec/ir/pipeline-explicit.yaml:1–20`: `IrPipeline` has a `source` and an ordered `stages` list.
- `spec/eval/pipeline-map-sum.yaml`: expected output of `[1,2,3] |> map((x)->x+1) |> sum` is `9\n`.
- `spec/flow/flow-map-filter-chain.yaml`: Flow example ends in `collect` and has specified output. This is a source-level spec definition; no spec-runner execution was performed by OpenClaw in this spike.
- `docs/design/pipeline-semantics.md`: Core IR is the portability boundary; this design note is subordinate to `GENIA_STATE.md`.

## Corrections required to the model's answer

1. **Unproven IR change.** The model asserted an explicit ordinary-callable `compose(...)` would require a new `compose` IR node. That does **not** follow from the retrieved evidence. Issue #1236 specifically requires deciding whether existing ordinary calls/pipelines suffice before considering a new portable representation. Mark as `UNKNOWN/PROPOSAL`.
2. **Unproven terminal primitive.** The model asserted a new terminal stage would be needed. Existing `collect` and `sum` appear in pinned specs. The contract needs to establish terminal semantics and materialization boundaries, not presume a new primitive.
3. **Incorrect error-indexing claim.** The model claimed current code lacks stage error indexing. `eval_pipeline` already enumerates stages and calls `_wrap_pipeline_stage_error(exc, index, stage, stage_value)`; any gap must be specified as a *composed-stage* mapping problem rather than absence of current indexing.
4. **Outcome speculation.** The model suggested composition could require a new Outcome structure. Neither the excerpts nor issue authorize that. Any proposal must preserve current `some/none/err` behavior; no new Outcome semantics are assumed.
5. **Overstated unknowns and citation accuracy.** The model said there was no evidence for error indexing and beyond-early-return behavior despite relevant evaluator source. It also referenced `src/eval/pipeline-map-sum.yaml` instead of `spec/eval/pipeline-map-sum.yaml` and misstated nearby line numbers in the design note.
6. **Scope completeness.** This case included only five files and nine checked lines; it did not review the full function-valued callable API, Flow cleanup/cancellation, complete Outcome behavior, C++ parity, or executable compatibility/negative cases. Those remain to investigate before pre-flight decisions.

## Decision and safe next actions

- **Accept** this as a successful external evidence-injection workflow smoke test and a *partial* implementation inventory.
- **Do not accept** it as the #1236 pre-flight, contract, design, RED evidence, semantic approval, or implementation authorization.
- For a subsequent *bounded* evidence pass, first inspect `GENIA_STATE.md` pipeline and Flow anchors; `src/genia/evaluator.py` stage-error handling and invocation; `src/genia/callable.py`; stage helpers/prelude; Flow lifecycle/terminal tests; relevant specs; and C++ host-gap evidence. Use an explicit evaluation matrix contrasting ordinary `compose(...)` with syntax, including callable-as-data and single-use Flow negative cases.
- A reviewer should challenge individual model claims against pinned source, not request runtime logs for a source-tracing task. Keep reviewer advisory.
- Any future contract or CODEX implementation prompt must follow `AGENTS.md` phases and keep `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, and `README.md` accurate **only when implemented truth changes**. Do not amend those files in this research spike.

**Stop:** No issue change, PR, merge, or changes to R29/#1328 are authorized by this record.
