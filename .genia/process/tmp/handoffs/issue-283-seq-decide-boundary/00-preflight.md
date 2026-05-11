# === GENIA PRE-FLIGHT ===

CHANGE NAME: issue #283 seq-decide-boundary
CHANGE SLUG: issue-283-seq-decide-boundary
ISSUE: #283 — Seq: Decide stdin compatibility boundary

Handoff directory:
`.genia/process/tmp/handoffs/issue-283-seq-decide-boundary/`

Output file:
`.genia/process/tmp/handoffs/issue-283-seq-decide-boundary/00-preflight.md`

---

## 0. BRANCH

Branch required: YES
Branch type: feature
Branch slug: issue-283-seq-decide-boundary
Expected branch: `feature/issue-283-seq-decide-boundary`
Base branch: `main`

Observed in this execution context:
- Local checkout was not available in the execution container.
- Remote branch search initially found no branch named `feature/issue-283-seq-decide-boundary`.
- Remote branch `feature/issue-283-seq-decide-boundary` was created from `main` commit `b594302cde47bf8988b1894b1083492e0725fe09` so the handoff artifact could be written.

Rules:
- No work on `main`.
- Branch must exist before contract.
- One branch per change.

Status:
- Safe to proceed to Contract on `feature/issue-283-seq-decide-boundary`.
- Do not proceed to Design/Test/Implementation until Contract chooses the stdin boundary.

---

## 1. SCOPE LOCK

Includes:
- Decide whether raw `stdin` should become a Seq-compatible public source.
- If raw `stdin` becomes Seq-compatible, define the portable contract, diagnostics, tests, docs, and pipe-mode interaction required for that behavior.
- If raw `stdin` remains outside direct Seq compatibility, affirm the current explicit bridge model and update roadmap/docs so `stdin` enters Seq/Flow through explicit bridge functions such as `lines(...)`.
- Preserve the distinction between public language contract and Python reference-host mechanics.
- Clarify how this decision affects `each`, `collect`, `run`, `lines`, pipe mode, and related diagnostics.
- Identify docs/spec/test surfaces affected by #253 over-promising broader Seq source compatibility.

Excludes:
- No async streams.
- No scheduler semantics.
- No selective receive.
- No Python generator exposure.
- No public Seq runtime type/helper/syntax/Core IR node unless a separate approved contract introduces it.
- No broad pipe-mode redesign.
- No implicit conversion of arbitrary values to Seq.
- No changes to `lines`, pipe mode, or Flow terminals unless explicitly contracted in the next phase.
- No implementation work in this phase.
- No tests or docs edits outside this pre-flight artifact in this phase.

Clarification:
- In this issue title, “Decide” means make a decision about the boundary. This pre-flight found no reason to treat this as a change to Genia case/conditional syntax.

---

## 2. SOURCE OF TRUTH

Authoritative:
- `GENIA_STATE.md` — final authority.
- `GENIA_RULES.md`.
- `GENIA_REPL_README.md`.
- `README.md`.
- `AGENTS.md`.
- GitHub issue #283.

Process:
- `docs/process/00-preflight.md`.
- `docs/process/llm-system-prompt.md`.
- `docs/process/extensions/portability-analysis.md`.

Additional relevant:
- `spec/flow/README.md`.
- `spec/flow/*`.
- `spec/eval/*` list/Seq-compatible terminal cases.
- `spec/cli/*` pipe-mode cases.
- `spec/error/*` if diagnostics change.
- `docs/cheatsheet/piepline-flow-vs-value.md`.
- `docs/cheatsheet/core.md`.
- `docs/cheatsheet/unix-power-mode.md`.
- Relevant book docs under `docs/book/*` if Flow/Seq/CLI examples are touched.
- `src/genia/builtins.py` and Flow/Seq runtime substrate.
- `src/genia/std/prelude/flow.genia` and related prelude helpers.
- `src/genia/interpreter.py` / CLI path if pipe-mode behavior changes.
- `hosts/python/` adapter files if shared spec execution or normalized diagnostics change.
- `tests/unit/test_flow_phase1.py`.
- `tests/unit/test_seq_transform_256.py`.
- `tests/unit/test_seq_prelude_migration_258.py`.
- `tests/unit/test_cli.py`.
- `tests/unit/test_flow_shared_spec_runner.py`.
- Relevant cheatsheet sidecar tests if examples change.

Notes:
- `GENIA_STATE.md` currently says Seq is semantic terminology, not a public runtime value/type/helper/syntax/Core IR node.
- `GENIA_STATE.md` currently says implemented Seq-compatible public values are lists and Flow.
- `GENIA_STATE.md` currently says explicit bridges such as `lines` and Flow-side `collect` / `run` define Value<->Flow crossings.
- `docs/cheatsheet/piepline-flow-vs-value.md` states the teaching rule: raw values stay values, flows stay flows, and only explicit bridges cross the boundary.
- Issue #283 exists because #253 roadmap language may overstate the intended source set by implying users should not care whether a source is list, range, Flow, stdin, evolve, or future host-backed stream.

---

## 3. FEATURE MATURITY

Stage:
- [ ] Experimental
- [x] Partial
- [ ] Stable

Doc wording:
- Seq remains semantic terminology, not a public runtime value/type/helper/syntax/Core IR node.
- Current implemented Seq-compatible public values are list and Flow.
- Direct raw `stdin` Seq compatibility is not currently documented as implemented behavior.
- If the contract chooses explicit bridge only, docs should say `stdin` enters ordered Flow processing through `lines(stdin)` and through pipe-mode's implicit `stdin |> lines` wrapper.
- If the contract chooses raw `stdin` Seq compatibility, it must be labeled as a deliberate expansion of the implemented Seq-compatible public source set and must be backed by tests/specs/docs.

Current maturity assessment:
- The existing list/Flow Seq-compatible behavior is Partial.
- The raw `stdin` compatibility decision is unresolved and should not be described as implemented.

---

## 3a. PORTABILITY ANALYSIS

Portability zone:
- Language contract / Flow-Seq boundary / CLI pipe-mode interaction.
- Potentially Python reference-host runtime and host adapter if behavior changes.

Core IR impact:
- Expected impact: none.
- This should not introduce a new `Ir*` node family.
- Existing pipeline lowering as explicit ordered-stage IR should remain unchanged unless the Contract discovers a specific bug.

Capability categories affected:
- `flow`: Seq-compatible source/terminal behavior, Flow bridge boundaries, `lines`, `each`, `collect`, `run`.
- `cli`: pipe mode, because pipe mode injects `stdin |> lines` and consumes the resulting Flow automatically.
- `eval`: command-mode behavior for direct expressions such as `stdin |> each(print) |> run` or `stdin |> collect` if raw `stdin` behavior changes.
- `error`: diagnostics if direct raw `stdin` remains rejected or becomes accepted in some contexts.
- `parse`: none expected.
- `ir`: none expected.

Shared spec impact:
- If behavior changes, add or update shared specs for affected observable behavior:
  - `spec/flow/*` for Flow/Seq behavior.
  - `spec/eval/*` for direct command-source eval cases involving raw `stdin` if accepted/rejected at eval surface.
  - `spec/cli/*` if pipe-mode diagnostics or accepted shapes change.
  - `spec/error/*` for exact diagnostics if new/changed errors become protected.
- If behavior does not change, add or update tests/docs to explicitly protect and explain the current bridge-only boundary.

Python reference host impact:
- If raw `stdin` becomes Seq-compatible, Python must define how stdin capability values are consumed directly by `each`, `collect`, `run`, and possibly `_seq_transform` internals without leaking Python iterator/generator mechanics.
- If raw `stdin` remains bridge-only, Python behavior should mostly remain unchanged; implementation changes may be limited to tests/diagnostics/docs.

Host adapter impact:
- If raw `stdin` becomes part of the portable contract, future adapters must model it consistently.
- If bridge-only is affirmed, adapters only need to preserve existing `lines(stdin)` / pipe-mode behavior.

Future host impact:
- Raw `stdin` compatibility would widen the future-host contract by making host input capability values directly Seq-compatible.
- Bridge-only keeps future hosts simpler: stdin remains an input capability adapted into Flow through `lines`, while list/Flow remain the public Seq-compatible values.

Portability risk:
- Medium if bridge-only is affirmed and documented.
- High if raw `stdin` compatibility is added, because it blurs host capability values and public Seq-compatible values unless the contract is very narrow.

---

## 4. CONTRACT vs IMPLEMENTATION

Portable contract today:
- Seq is a semantic compatibility category for ordered value production.
- Seq is not a public runtime value, type constructor, syntax form, helper, or Core IR node.
- Implemented Seq-compatible public values are lists and Flow.
- Lists are eager and reusable.
- Flow is lazy, pull-based, source-bound, and single-use.
- Iterators/generators are host implementation details.
- `each`, `collect`, and `run` accept list or Flow as Seq-compatible public values.
- `lines` and Flow-side `collect` / `run` define explicit Value<->Flow crossings.
- Pipe mode injects `stdin |> lines` and expects the stage expression to produce a Flow.

Python implementation today:
- Python is the only implemented host and the reference host.
- Python uses host-backed runtime Flow mechanics and internal Seq helper/kernel mechanics.
- `_seq_transform(initial_state, step, source)` is an internal kernel primitive and not an ordinary public Genia name.
- `tests/unit/test_seq_transform_256.py` covers internal `_seq_transform` behavior for list and Flow sources.
- `tests/unit/test_seq_prelude_migration_258.py` protects internal sequence kernels from being exposed as public helpers while preserving public list/Flow helpers.

Not implemented / unresolved:
- Raw `stdin` as direct Seq-compatible public source.
- Any public `Seq` type/helper/syntax.
- Direct host iterator/generator exposure.
- Async/multi-port stream semantics.
- Broad pipe-mode redesign.

Decision needed in Contract:
- Outcome A: raw `stdin` becomes a narrow Seq-compatible public source, with exact lifecycle, consumption, diagnostics, and pipe-mode rules.
- Outcome B: current bridge-only model is affirmed, and docs/roadmap are corrected to say `stdin` enters Seq/Flow through `lines(...)`.

Pre-flight recommendation:
- Prefer Outcome B unless the Contract can show a compelling clarity win for raw `stdin` that does not blur explicit Value/Flow crossings or future-host portability.

---

## 5. TEST STRATEGY

Core invariants:
- Seq remains semantic terminology, not a public runtime type/helper/syntax/Core IR node.
- Public Seq-compatible values are exactly those specified by the contract.
- If bridge-only is affirmed, `stdin` is not accepted directly by `each`, `collect`, or `run`; users must use `stdin |> lines` or pipe mode.
- If raw `stdin` is added, direct behavior must be exact, deterministic, and consistent across `each`, `collect`, and `run`.
- Pipe mode must remain internally consistent with whichever boundary is chosen.
- Errors must stay Genia-facing and not leak Python iterator/generator details.

Expected behavior to test if bridge-only is affirmed:
- `stdin |> lines |> each(print) |> run` works in command/file mode.
- `stdin |> lines |> collect` materializes input lines.
- `stdin |> each(print) |> run` fails with a clear Seq-compatible / bridge guidance diagnostic.
- `stdin |> collect` fails with a clear bridge guidance diagnostic.
- `stdin |> run` fails with a clear bridge guidance diagnostic.
- Pipe mode remains unchanged: `genia -p 'each(print)'` works because pipe mode injects `stdin |> lines`.
- Pipe mode still rejects explicit unbound `stdin` and explicit unbound `run` per current contract.

Expected behavior to test if raw `stdin` becomes Seq-compatible:
- `stdin |> each(print) |> run` works and consumes stdin in order.
- `stdin |> collect` returns the ordered input lines or a precisely defined raw-unit representation.
- `stdin |> run` behavior is specified and tested.
- Reuse/consumption lifecycle is specified: reusable vs single-use must not be ambiguous.
- `lines(stdin)` behavior remains compatible or is explicitly adjusted.
- Pipe mode's implicit `stdin |> lines` wrapper does not double-adapt or conflict with raw stdin compatibility.

Failure cases:
- Non-list/non-Flow/non-approved sources passed to `each`, `collect`, or `run` fail clearly.
- If `stdin` remains bridge-only, direct `stdin` terminal calls must fail with diagnostics that teach `lines(stdin)`.
- If raw `stdin` is accepted, consuming it twice must have exact, tested lifecycle semantics.
- Invalid pipe-mode final values remain diagnosed clearly.

Test approach:
- Contract phase must choose bridge-only or raw-stdin-compatible before tests are written.
- Test phase should add failing tests first.
- Likely targeted runs:
  - `uv run pytest -q tests/unit/test_flow_phase1.py tests/unit/test_cli.py tests/unit/test_flow_shared_spec_runner.py`
  - `uv run pytest -q tests/unit/test_seq_transform_256.py tests/unit/test_seq_prelude_migration_258.py`
  - `uv run python -m tools.spec_runner`
- If docs/cheatsheets change, run relevant cheatsheet validation:
  - `uv run pytest -q tests/test_cheatsheet_*.py`
- If book docs change, run relevant book/doc sync tests if available.

Validation performed in this pre-flight:
- No tests were run. Pre-flight only.

---

## 6. EXAMPLES

Minimal examples for bridge-only outcome:

Valid bridge shape:
```genia
stdin |> lines |> each(print) |> run
```

Invalid direct raw stdin shape, if bridge-only is affirmed:
```genia
stdin |> each(print) |> run
```
Expected direction: clear diagnostic pointing to `stdin |> lines |> each(print) |> run`.

Pipe-mode shape that should remain valid:
```bash
printf 'a\nb\n' | genia -p 'each(print)'
```
Reason: pipe mode injects `stdin |> lines` and consumes the final Flow automatically.

Minimal examples for raw-stdin-compatible outcome:

Direct stdin traversal:
```genia
stdin |> each(print) |> run
```

Direct stdin materialization:
```genia
stdin |> collect
```

These examples must not be documented as valid unless Contract explicitly chooses and Implementation proves raw `stdin` compatibility.

Real example:
```bash
printf '10\noops\n20\n' | genia -c 'stdin |> lines |> keep_some(parse_int) |> collect |> sum'
```

This should remain valid under either outcome unless the Contract explicitly changes `lines` behavior, which is out of scope by default.

---

## 7. COMPLEXITY CHECK

- [ ] Adding complexity
- [x] Revealing structure

Justification:
- The issue is primarily about making an existing boundary explicit.
- Current docs already distinguish values, Flow, explicit bridges, and Seq-compatible terminal behavior.
- The change should reduce ambiguity introduced by the broader #253 roadmap language.
- Adding raw `stdin` compatibility would add complexity; affirming bridge-only would mostly reveal and document existing structure.

Complexity warning:
- Treating raw `stdin` as directly Seq-compatible risks turning host capabilities into implicit ordered sources, which could blur the current explicit Value/Flow crossing model.

---

## 8. CROSS-FILE IMPACT

Files likely to change if bridge-only is affirmed:
- `GENIA_STATE.md` — clarify stdin bridge-only boundary if current wording is insufficient.
- `GENIA_RULES.md` — only if an invariant needs to be added around explicit bridges / stdin not direct Seq.
- `README.md` — keep quickstart/CLI/Seq language truthful.
- `GENIA_REPL_README.md` — clarify command/pipe examples if needed.
- `docs/cheatsheet/piepline-flow-vs-value.md` — likely primary docs correction point.
- `docs/cheatsheet/unix-power-mode.md` and/or `docs/cheatsheet/core.md` if stdin examples imply broader compatibility.
- `spec/flow/README.md` and possibly `spec/flow/*`.
- `spec/eval/*` and/or `spec/error/*` for direct stdin rejection/diagnostics if protected.
- `spec/cli/*` if pipe-mode wording or diagnostics are protected.
- Tests under `tests/unit/` around flow/cli/seq terminal behavior.

Files likely to change if raw `stdin` compatibility is added:
- Everything above, plus implementation areas:
  - `src/genia/builtins.py`.
  - `src/genia/std/prelude/flow.genia`.
  - `src/genia/interpreter.py` / CLI pipe-mode path if interaction changes.
  - `hosts/python/*` adapter/normalization if shared specs require it.

Risk of drift:
- [ ] Low
- [x] Medium for bridge-only clarification.
- [x] High if raw `stdin` compatibility is added.

Drift notes:
- `docs/cheatsheet/piepline-flow-vs-value.md` currently says `lines(source)` accepts stdin, list-of-strings, or existing flow, while terminal helpers accept list or Flow.
- #253 roadmap language may need correction if it implies stdin itself is already a direct Seq-compatible public value.
- Pipe-mode docs must stay consistent with command/file-mode docs.

---

## 9. DOC DISTILLATION CHECK

Creates process artifacts?
- [x] YES → this pre-flight handoff is a process artifact.
- [ ] NO

Adds docs/design or docs/architecture files?
- [ ] YES → classify KEEP / EXTRACT / DELETE
- [x] NO

Doc drift risk:
- [ ] Low
- [x] Medium
- [ ] High

Distillation notes:
- This handoff is not canonical documentation.
- If the contract affirms bridge-only behavior, durable wording should be distilled into the canonical docs listed above.
- If the contract adds raw `stdin` compatibility, docs must distinguish portable contract from Python implementation and avoid implying a public Seq runtime value/helper.

---

## 10. PHILOSOPHY CHECK

- preserves minimalism? YES, if this clarifies the existing boundary; MAYBE if raw `stdin` compatibility is added.
- avoids hidden behavior? YES for bridge-only; RISK for raw `stdin` compatibility unless lifecycle/adaptation is explicit.
- keeps semantics out of host? YES if the contract stays centered on language-visible `lines`/Flow behavior; RISK if Python stdin mechanics leak into public Seq semantics.
- aligns with pattern-matching-first? YES; this does not introduce competing control-flow syntax.

Notes:
- The strongest Genia-aligned default is explicit bridges: `stdin |> lines` makes the host input boundary visible.
- Raw `stdin` direct compatibility may be ergonomic, but it must earn its keep by reducing ambiguity rather than creating implicit conversion magic.
- Do not use this issue to add public Seq syntax, helpers, or new Core IR concepts.

---

## 11. PROMPT PLAN

Pipeline:
- Preflight — this artifact.
- Contract — choose raw `stdin` compatibility vs bridge-only; define exact behavior and diagnostics.
- Design — map the chosen contract to implementation/docs/tests/specs.
- Test — write failing tests first for the chosen contract.
- Implementation — make only the approved tests pass.
- Docs — sync only implemented/tested behavior.
- Audit — verify truth, scope, tests, docs, and drift risks.
- Distillation — extract durable truths from handoffs into canonical docs if needed, then keep handoffs non-canonical.

Recommended next prompt:
- Contract for issue #283.
- The Contract must explicitly choose one of:
  1. raw `stdin` direct Seq compatibility, or
  2. bridge-only `stdin |> lines` model.
- The Contract must not design or implement.

---

## OPEN QUESTIONS / AMBIGUITIES

1. Should raw `stdin` be accepted directly by `each`, `collect`, and `run`, or should it remain an opaque host input capability requiring `lines(stdin)`?
2. If raw `stdin` is accepted, what exactly are its item units: lines, bytes, characters, or host-defined records?
3. If raw `stdin` is accepted, is it single-use, reusable, or tied to the same cached behavior as `stdin()` compatibility?
4. If raw `stdin` is accepted, does `lines(stdin)` remain the canonical bridge or become redundant? If redundant, how is that not a second equivalent way to express the same concept?
5. If bridge-only is affirmed, what exact diagnostic should users see for `stdin |> collect`, `stdin |> run`, and `stdin |> each(print) |> run`?
6. Which #253 roadmap/docs text currently over-promises broader source compatibility and must be corrected?
7. Should direct raw `stdin` rejection be protected in shared `eval`/`error` specs, or is unit coverage sufficient?
8. Should pipe-mode explicit unbound `stdin` / `run` rejection remain unchanged under both outcomes? Pre-flight recommendation: yes, unless Contract explicitly says otherwise.

---

## FINAL GO / NO-GO

Ready to proceed?
- YES, to Contract only.
- NO, to Design/Test/Implementation until the Contract selects the stdin boundary.

Missing before Contract:
- Nothing blocking Contract.

Missing before Design/Test/Implementation:
- Explicit contract decision: raw `stdin` direct Seq-compatible source vs bridge-only `stdin |> lines` model.
- Exact diagnostics for rejected or accepted direct raw `stdin` terminal calls.
- Exact docs/spec/test impact list for the chosen outcome.
