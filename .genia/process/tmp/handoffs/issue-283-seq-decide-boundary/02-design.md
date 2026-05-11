# === GENIA DESIGN ===

CHANGE NAME: issue #283 seq-decide-boundary
CHANGE SLUG: issue-283-seq-decide-boundary
ISSUE: #283 — Seq: Decide stdin compatibility boundary

Handoff directory:
`.genia/process/tmp/handoffs/issue-283-seq-decide-boundary/`

Output file:
`.genia/process/tmp/handoffs/issue-283-seq-decide-boundary/02-design.md`

---

## 0. BRANCH CHECK

Expected branch:
`feature/issue-283-seq-decide-boundary`

Status:
- Design written for the expected feature branch.
- Do not apply this design on `main` directly.

---

## 1. PURPOSE

Translate the approved contract into repo work.

The contract affirms the bridge-only stdin boundary:
- `stdin` is a host-backed input capability.
- `stdin` is not directly Seq-compatible.
- `stdin` enters Flow through `lines(stdin)`.
- Pipe mode keeps injecting `stdin |> lines` internally.

This design organizes the smallest work needed to prove and document that boundary.

---

## 2. SCOPE LOCK

Contract includes:
- Lock public Seq-compatible values to list and Flow for this phase.
- Keep raw `stdin` outside direct Seq compatibility.
- Require `stdin |> lines` for stdin-to-Flow adaptation.
- Keep pipe-mode behavior unchanged.
- Ensure direct raw stdin terminal calls fail with Genia-facing diagnostics.
- Correct docs/roadmap wording that implies direct stdin Seq compatibility.

Contract excludes:
- No raw stdin direct Seq compatibility.
- No public Seq type/helper/syntax.
- No parser changes.
- No Core IR changes.
- No async streams or scheduler semantics.
- No Python generator exposure.
- No broad pipe-mode redesign.
- No `lines` redesign.

Do not expand scope.

---

## 3. ARCHITECTURE

### 3.1 Boundary model

Keep the current three-layer shape:

```text
Host input capability: stdin
        |
        | explicit bridge
        v
Flow: stdin |> lines
        |
        | Seq-compatible terminal/helpers
        v
collect / each / run
```

Direct terminal use of `stdin` remains invalid:

```text
stdin |> collect      invalid
stdin |> run          invalid
stdin |> each(print)  invalid source to each
```

### 3.2 Integration points

Contract-level integration points:
- `GENIA_STATE.md`: final behavior statement.
- `GENIA_REPL_README.md` / `README.md`: CLI and user-facing examples.
- `docs/cheatsheet/piepline-flow-vs-value.md`: main teaching surface for Flow vs Value.
- `spec/flow/README.md`: clarify Flow specs cover Flow side only, and stdin enters through `lines`.

Runtime integration points, only if tests fail:
- `src/genia/builtins.py`: Seq-compatible terminal source validation and diagnostic wording.
- `src/genia/std/prelude/flow.genia`: public helper wrappers if diagnostics are enforced there.
- `src/genia/interpreter.py`: pipe-mode only if current rejection/auto-wrap behavior differs from contract.
- `hosts/python/adapter.py` or related host adapter files only if shared spec normalization is affected.

### 3.3 Data flow

Command/file mode with stdin:
```text
stdin capability -> lines(stdin) -> Flow -> map/filter/each/collect/run
```

Pipe mode:
```text
host stdin -> internal stdin capability -> internal lines(stdin) -> user stage expression -> final Flow -> automatic run
```

Invalid direct path:
```text
stdin capability -> each/collect/run -> Seq-compatible source error
```

---

## 4. FILE PLAN

New files:
- None expected for implementation.
- Potential new shared spec YAML files only in Test phase if coverage is added.

Modified files expected in Docs phase:
- `GENIA_STATE.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/cheatsheet/piepline-flow-vs-value.md`
- `spec/flow/README.md`

Modified files conditional:
- `docs/cheatsheet/core.md` if it contains stdin/Seq wording that over-promises.
- `docs/cheatsheet/unix-power-mode.md` if it contains stdin/Seq wording that over-promises.
- Relevant `docs/book/*` files if they describe Flow/Seq/stdin boundary.
- `docs/contract/semantic_facts.json` only if this boundary is already protected there or should become protected.
- `tests/test_semantic_doc_sync.py` only if semantic facts are updated.

Test files likely in Test phase:
- `tests/unit/test_flow_phase1.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_seq_prelude_migration_258.py` or a new focused unit test file for #283.
- `spec/eval/*` if direct stdin rejection is protected as shared eval behavior.
- `spec/cli/*` if pipe-mode behavior needs an added shared case.
- `spec/error/*` only if exact stderr is intentionally protected.
- Cheatsheet sidecar JSON under `tests/data/` if cheatsheet runnable examples change.

Implementation files only if tests prove mismatch:
- `src/genia/builtins.py`
- `src/genia/std/prelude/flow.genia`
- `src/genia/interpreter.py`
- `hosts/python/*` adapter/normalization files if shared specs need it.

Removed files:
- None.

---

## 5. DATA / INTERFACE DESIGN

No new data shapes.

No new public interfaces.

Existing interface boundaries:

### `stdin`
- Remains host-backed input capability.
- Not directly Seq-compatible.

### `lines(source)`
- Explicit bridge.
- Accepts current source categories, including `stdin`.
- Produces Flow.

### `each(f, source)`
- Source must be list or Flow.
- Raw `stdin` must be rejected.

### `collect(source)`
- Source must be list or Flow.
- Raw `stdin` must be rejected.

### `run(source)`
- Source must be list or Flow.
- Raw `stdin` must be rejected.

### Pipe mode
- Continues to wrap host stdin as `stdin |> lines`.
- Continues to reject explicit unbound `stdin` and `run` in pipe-mode stage expressions.

Diagnostic interface:
- Existing diagnostics may be reused if they clearly state list or Flow accepted.
- If current diagnostics are unclear, update them to include stdin bridge guidance.

Preferred diagnostic fact:
```text
expected a Seq-compatible value (list or Flow); received stdin. Use stdin |> lines to adapt stdin into a Flow.
```

Do not depend on exact punctuation until Test phase chooses exact assertions.

---

## 6. CONTROL / ERROR FLOW

### 6.1 Valid command/file mode path

1. Evaluate `stdin` as host input capability.
2. Apply `lines` as explicit bridge.
3. Produce Flow.
4. Flow stages operate normally.
5. `collect` or `run` consumes the Flow.

### 6.2 Invalid command/file mode path

1. Evaluate `stdin` as host input capability.
2. Pass raw `stdin` to `each`, `collect`, or `run`.
3. Seq-compatible source validation rejects it.
4. Error propagates through normal runtime/eval error handling.
5. Error remains Genia-facing.

### 6.3 Pipe mode path

1. CLI receives `-p 'stage_expr'`.
2. Runtime constructs internal `stdin |> lines` source Flow.
3. User stage expression is applied to that Flow.
4. Final value must be Flow.
5. Runtime consumes final Flow automatically.

No pipe-mode redesign.

### 6.4 Error boundaries

Enforce correctness at the source-validation boundary of `each`, `collect`, and `run`.
Do not enforce this in parser or Core IR.
Do not add special-case syntax checks.

---

## 7. TEST PLAN INPUT

Invariants to test:
- `stdin |> lines |> collect` succeeds.
- `stdin |> lines |> each(print) |> run` succeeds.
- `stdin |> collect` fails.
- `stdin |> run` fails.
- `stdin |> each(print) |> run` fails.
- Error mentions Seq-compatible accepted values, preferably list or Flow.
- Error for raw stdin mentions `stdin |> lines` or otherwise clearly teaches explicit bridging.
- Pipe mode remains valid for `genia -p 'each(print)'`.
- Pipe mode still rejects explicit `stdin` and explicit `run` stage usage.

Suggested unit tests:
- Add focused tests to `tests/unit/test_flow_phase1.py` or a new `tests/unit/test_seq_stdin_boundary_283.py`.
- Use `make_global_env(stdin_data)` and `run_source` for command/file-like eval tests.
- Use CLI helper tests in `tests/unit/test_cli.py` for pipe-mode behavior.

Suggested shared specs:
- Add `spec/eval/seq-stdin-lines-collect.yaml` if not already covered.
- Add `spec/eval/seq-stdin-direct-collect-error.yaml` only if exact error surface is intended as shared contract.
- Add or confirm `spec/cli/*` case for `-p 'each(print)'` and explicit `stdin`/`run` rejection.

Regression risks:
- Accidentally accepting raw `stdin` through a generic internal `GeniaSeq` adapter.
- Accidentally changing pipe mode from implicit source injection to direct stdin passing.
- Over-tight exact stderr assertions becoming brittle if diagnostics include stage context.
- Docs saying “stdin is Seq-compatible” when the contract says only list/Flow are direct public values.

Recommended validation commands after Test/Implementation/Docs:
```bash
uv run pytest -q tests/unit/test_flow_phase1.py tests/unit/test_cli.py tests/unit/test_seq_prelude_migration_258.py
uv run pytest -q tests/unit/test_flow_shared_spec_runner.py
uv run python -m tools.spec_runner
uv run pytest -q tests/test_cheatsheet_*.py
```

Run only the relevant subset first; run broader validation before audit/merge.

---

## 8. DOC IMPACT

Required docs updates:

### `GENIA_STATE.md`
- Ensure the Seq section explicitly says:
  - direct Seq-compatible public values are list and Flow.
  - `stdin` is not directly Seq-compatible.
  - `stdin` enters Flow through `lines(stdin)`.
  - pipe mode injects `stdin |> lines`.

### `GENIA_REPL_README.md`
- Ensure examples use `stdin |> lines` in command/file mode.
- Ensure pipe-mode explanation says users do not write explicit `stdin` or `run` in `-p`.
- Avoid any wording that raw `stdin` can go directly to `each`, `collect`, or `run`.

### `README.md`
- Same CLI/Flow wording cleanup as needed.
- Keep language concise and implemented-only.

### `docs/cheatsheet/piepline-flow-vs-value.md`
- This is likely the main documentation target.
- Keep the rule: raw values stay values, flows stay flows, only explicit bridges cross boundary.
- Clarify that `stdin` is a host input capability adapted by `lines`, not a direct Seq-compatible value.
- If runnable examples change, update sidecar JSON and run cheatsheet validation.

### `spec/flow/README.md`
- Clarify Flow specs cover Flow side of Seq contract.
- Clarify stdin enters through `lines` in Flow specs.

Conditional docs:
- `docs/cheatsheet/core.md`
- `docs/cheatsheet/unix-power-mode.md`
- relevant `docs/book/*` files
- `docs/contract/semantic_facts.json` if this boundary should become a protected semantic fact

---

## 9. COMPLEXITY CHECK

[x] Minimal
[ ] Necessary
[ ] Over-engineered

Explanation:
- The design affirms current semantics rather than adding a feature.
- Runtime changes should be unnecessary unless existing diagnostics are unclear or tests reveal accidental direct stdin acceptance.
- Most work should be tests and docs to lock the boundary.

---

## 10. FINAL CHECK

- Matches contract exactly: YES.
- Adds no new behavior: YES.
- No host-specific assumptions beyond Python reference-host validation locations: YES.
- Ready for Test phase: YES.
- Ready for Implementation phase: CONDITIONAL — only if failing tests reveal mismatch or diagnostics need improvement.
- Can ticket close immediately after Contract/Design: NO, unless you intentionally accept decision-only closure without repo truth-locking. Recommended path is Test + Docs + Audit.

Recommended next phases:
1. Test: add failing/protective tests for bridge-only stdin boundary.
2. Implementation: skip if tests already pass and diagnostics are acceptable; otherwise make minimal diagnostic/runtime correction.
3. Docs: sync canonical docs to the contract.
4. Audit: verify ticket can close.
