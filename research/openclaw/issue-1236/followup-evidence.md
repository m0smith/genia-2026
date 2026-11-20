# #1236 follow-up: callable, Flow, diagnostics and host-parity evidence

**Status:** SOURCE-ONLY RESEARCH; NO LANGUAGE CONTRACT OR IMPLEMENTATION APPROVED.

- Issue: https://github.com/m0smith/genia-2026/issues/1236
- Branch: `research/openclaw-1236-isolated-20261120` (isolated from main and R29).
- Evidence is pinned to `7475646d44fee58bc98294ba78e22727eaab63f1`.
- This document is an *independent manual source inventory* supporting the v0.9 OpenClaw `followup-case.json`; **it is not the output of a live OpenClaw follow-up run**.
- No Genia executable/spec tests were run as part of this source inventory. Existing test *definitions* are cited without implying current passing results.

## Verified implemented behavior (limited to pinned excerpts)

1. **Value-application pipeline.** `GENIA_STATE.md` pipeline Phase 2 says `x |> f` calls `f(x)` and `x |> f(y)` calls `f(y, x)`. It specifies `IrPipeline` as source plus ordered stages, and says pipelines are not nested calls. No evidence here establishes `f |> g` as a callable-composition operator. Callables can themselves be values; changing `|>` based solely on the input's callable type risks breaking existing data application.
2. **Callable dispatcher.** `src/genia/callable.py:1730+` contains `invoke_callable`, dispatching ordinary Genia callable values. This establishes an existing invocation mechanism; it does **not** establish that an ordinary `compose(...)` can be implemented with no IR change, nor that a new IR form is necessary.
3. **Pipeline errors.** `src/genia/evaluator.py:1106–1150` computes `stage_index + 1` in the error wrapper and invokes that wrapper around each sequential stage. Therefore “no stage indexing exists” is **false**. Mapping nested/composed stages to accurate spans/indexes remains a design question.
4. **Outcome propagation.** `GENIA_STATE.md` pipeline Phase 2 explicitly specifies `some` lifting and `none`/`err` short-circuit semantics. `src/genia/evaluator.py:1135+` implements early return for `none` and `err`. Composition must preserve this; no new Outcome type is authorized.
5. **Flow lifetime.** `GENIA_STATE.md` states Flow is lazy, pull-based, source-bound, and single-use. `src/genia/values.py:966+` rejects a second consume for a single-use GeniaSeq; `GeniaFlow.consume` delegates to the Seq. The existing `tests/unit/test_flow_phase1.py:87+` defines a single-use regression, and `:407+` defines an early-close propagation regression. Their presence establishes intended coverage, not that they executed during this investigation.
6. **Terminals and boundedness.** The existing `spec/flow/flow-map-filter-chain.yaml` defines a Flow pipeline ending in `collect`; `GENIA_STATE.md` describes `collect`/`run`/`reduce` terminals. Hence a new terminal primitive is **not proven necessary** for ordinary-callable composition. Whether materialization, terminal-then-stage rejection, or demand are preserved in a proposed composition helper remains untested.
7. **Host support.** `GENIA_STATE.md:120–135` reports a **bounded** C++ Flow phase 1 floor with known unsupported features, including pipelines inside call arguments. This makes a composition API's C++ parity and host-gap disposition an **open portability gate**, not a demonstrated capability.

## Proposed alternatives — decision matrix (not implemented)

| Contract question | A: ordinary `compose(...)` callable | B: new explicit composition syntax |
|---|---|---|
| Existing `|>` meaning | Could preserve it by leaving `|>` as data application; needs executable compatibility cases | Must prove parsing is unambiguous and cannot reinterpret existing `|>` data applications |
| Core IR | Investigate reuse of ordinary calls, callable values, and pipelines **before** considering new nodes | Likely needs parser/lowering decision and portable IR representation audit; not approved |
| Definition is inert | Require no Flow pulls/effects while constructing composed callable | Same requirement |
| Repeated invocations | Require fresh input per call; reject reusing consumed Flow | Same requirement |
| Intermediate transformations | Define stage sequence, parameter binding and callable-as-data behavior | Same requirement plus syntax precedence |
| Terminal behavior | Reuse existing `collect`/`sum` where type-compatible; reject invalid terminal-to-transform transitions | Same requirement; no implied new terminal |
| Outcome | Preserve `some` lift, `none`/`err` identity and early return | Same requirement |
| Diagnostics | Preserve current 1-based stage indices; decide mapping nested/composed stage spans | Same requirement plus new syntax span accounting |
| Flow cleanup | Demonstrate bounded pull, early close, cancellation and single-use protection | Same requirement |
| C++ host | Need explicit capability/parity matrix; document/track unsupported cases | Same; likely higher parser/IR surface |
| Confidence | **Candidate only** | **Candidate only** |

## Specific missing evidence / required negative cases

- Callable-as-data collision: callable value passed to `|>` must not silently become a composition declaration.
- Definition-time effects: no source iterator consumption, network/file effects or callable invocation during construction.
- Fresh Flow input versus reusing the same consumed Flow; early-close and exception cleanup.
- Terminal followed by a Flow-only transform, and List-vs-Flow `sum`/`collect` compatibility.
- `some/none/err` through multiple composed stages; side-effects after short-circuit forbidden.
- Source spans and 1-based diagnostics for failing inner composed stage.
- Python/C++ shared eval/IR/flow/error cases or explicit issue-backed C++ gap; verify actual support rather than infer it from the Python reference host.

## Read-only OpenClaw follow-up

Run the pinned `followup-case.json` with external OpenClaw controller v0.9, as documented in `followup-runbook.md`. The controller's `PASS` only checks its bounded evidence/provenance contract; semantic claims require an independent skeptical assessment. The reviewer may be run later if actual disputed claims warrant its cost.

**Decision:** Enough source evidence to explain the principal compatibility risks and to reject the earlier model's unsupported “new IR node/terminal required” assumptions. **Not enough evidence to select alternative A or B, approve a contract, or start implementation.**

The four root authoritative docs (`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`) remain unchanged. Any later CODEX implementation prompt must require them to stay synchronized with verified implemented truth under `AGENTS.md` and the separately authorized change gates.
