# R29 — Sheet Record Pipelines: pre-flight (revision 3)

Status: **Pre-flight record (PROPOSED, NON-AUTHORITATIVE).** Documentation only. It defines no
language behavior; every function name, shape, and decision below is a *candidate* for the contract
phase. `GENIA_STATE.md` remains final authority for implemented behavior. This revision changes no
runtime, test, spec, manifest, or implemented-truth document (`GENIA_STATE.md`, `GENIA_RULES.md`,
`GENIA_REPL_README.md`, `README.md` are untouched).

Revisions 2 and 3 resolve the independent review verdict **REVISE** on draft PR #1284. Revision 3
independently re-executed every probe and count behind revision 2 (nothing was carried over unrun) and
tightened four statements that the re-execution showed to be imprecise or self-contradictory; see §0.
The evidence behind each correction is in §4 and §9 and was produced by commands run against `main` at
`79c073b` (scripts in Appendix B, commands and outputs in Appendix A).

Process: `AGENTS.md` (R26+ Change Pre-Flight Gate), `docs/process/run-change.md`,
`.github/ISSUE_TEMPLATE/genia-change-preflight.md`, `docs/process/extensions/portability-analysis.md`.
There is no dedicated R29 planning issue (searches for "R29" and "Sheet Record Pipelines" found only
closed 2026-05 killer-workflow issues); see §15.

**Evidence labels used throughout.**

| Label | Meaning |
|---|---|
| **[I]** | Implemented behavior, backed by `GENIA_STATE.md` (Python reference host unless stated). |
| **[T]** | Behavior covered by an existing committed test or shared spec. |
| **[V]** | Verified by a read-only probe run for this pre-flight; **not** committed as a test. |
| **[P]** | Proposed or candidate; not implemented, not approved. |
| **[U]** | Unverified. |

---

## 0. Review resolution (revisions 2 and 3)

| # | Blocking finding | Resolution | Where |
|---|---|---|---|
| 1 | `lines(records(sheet))` is invalid: `lines` accepts only a List of strings. | Every occurrence removed. Verified that `lines([{n: 1}])` fails (`lines expected a list of strings`). Replaced by an application-owned indexed composition built from `evolve`, `take`, `map`, `nth`, `unwrap_or`; verified on empty and nonempty lists, under `take`, and for single-use. No builtin added. Eager allocation, lazy downstream, bounded demand, single-use, finalization and the `lifecycle_repeat` envelope are now separated. | §4, §5 C4/C5 |
| 2 | Round-trip claim overstated. | Universal claim removed. Replaced by conditional guarantees G1–G7, with measured results for zero-row, zero-column, name identity, ordering, and protected cells. Zero-row schema loss is accepted as a limitation of the record boundary; no schema wrapper is proposed. | §4.3 |
| 3 | Capability/conformance accounting incomplete. | Reproduced the reviewer's counts (Python 20 pass, C++ 20 unsupported, all `requires` empty). Defined baseline-applicable vs capability-excluded vs adapter-reported unsupported, using the runner's actual code. Gave a concrete migration plan (which cases are retro-gated, which new cases are gated, claims, the issue-backed gap, and a decision for the mixed-family case). Manifest and specs are **not** changed here. | §9 |
| 4 | Phase sequence deviates from `run-change.md`. | Decomposition rebuilt against the 20 numbered steps, including the Code Quality & Maintainability Review after implementation and before docs. Proving-case tests are specified in the TEST phase; new-failing and already-passing tests are separated. The #1251 exception is stated to gate implementation only. | §12 |

**Revision 3 re-verification and corrections.** Every program in §4 and Appendix B was re-run with the
current interpreter, and the 20 Sheet cases were re-run on a freshly built `genia-cpp@44456ba` and on the
Python protocol adapter (results unchanged: Python 20 pass, C++ 20 unsupported; no other shared case uses a
Sheet helper). The re-execution changed the document in these places only:

1. **Self-contradiction removed (T2, §10.1).** Revision 2 said the Sheet-is-not-a-Seq guards "must already
   pass" while §2 correctly says no dedicated test exists today. They are *new tests written in the TEST
   phase that pass against current code*; only tests that need `records/1` are expected to fail first.
2. **Protected-value result completed (§4.5).** The invalid-field branch (the branch that actually copies the
   raw `actual`) was probed; `print` of the result is *rejected* (`protected-value: print`), `display` and
   `debug_repr` render `<protected>`, `json_encode` is rejected, and the sentinel occurred 0 times.
3. **Phase wording (§12)** now carries run-change step 13's "fresh verdict, do not proceed on FAIL" and step
   14's handoff commit verbatim in intent.
4. **D9** gains the observation that `records` is also used as a *parameter* name in three shipped examples
   (harmless, shown for completeness) and that rebinding `rows` with `=` works while `rows =: 5` is rejected.

The scripts are now reproduced in full in Appendix B so a reviewer can run them without reconstructing them
from prose.

---

## 1. Executive decision

**CONDITIONAL GO** for the contract, design, and TEST phases (R29-C, R29-G, R29-T).
**NO-GO** for implementation (R29-I) until §13 condition 1 is met.

The scoped exception to #1251 discussed in the first revision is **recommended for consideration, not
approved, and not yet ready to approve.** It gates implementation only; contract, design and TEST work
need no exception. Reasons it should not be approved yet:

1. The contract decisions it would cover (D1–D11) are unmade, including the name of the boundary
   function. Evidence in §6 D9 shows a generic name has a concrete Model B cost.
2. Model B Slice C ([#1269](https://github.com/m0smith/genia-2026/issues/1269) / draft
   [PR #1270](https://github.com/m0smith/genia-2026/pull/1270)) still has open decisions D1–D7 and
   Slices D and E are unstarted; the interaction surface (reserved names, aliases, module visibility,
   metadata) is therefore not final.
3. The conformance-accounting plan (§9) needs a maintainer decision and an issue-backed C++ gap before it
   can be committed; that gap's tracking issue does not exist yet.
4. There is no RED evidence. An exception is easiest to bound once the contract and failing tests exist,
   so request it at the implementation gate with the contract and RED SHA in hand.
5. The maintainer has not recorded any exception; this document does not record or imply one.

Minimal architecture is unchanged: one candidate **pure, eager `records(sheet) -> List<Map>` builtin**
plus executable composition evidence. The name `records/1` is a working placeholder (D9).

---

## 2. Current implementation baseline

Sources: `GENIA_STATE.md` lines 587–625 and 1603–1690 (Sheet), 1688–1860 (Flow), 3217–3310 (R14),
2360–2510 (Outcome/validation), 377–398 (protected values); code at `src/genia/sheet.py` and
`src/genia/builtins.py`. Everything below is **Experimental** and **Python-reference-host only** unless
stated.

| Capability | Status | Evidence |
|---|---|---|
| Sheet value: immutable, columnar, named columns, deterministic order; "not lazy, not a Seq-compatible source" | [I] | STATE 587–625 |
| Helpers: `sheet`, `shape`, `columns`, `select`, `where`, `derive`, `rows`, `row_get`, `collect_sheet`, `render_csv` | [I][T] | STATE 1603–1690; `tests/unit/test_sheet.py` |
| `rows(sheet)` = List of `[name, value]` pair-lists (not maps) | [I][T] | STATE 1615 |
| `collect_sheet(records)`: finite List/Flow of maps, identical key sets, first record fixes column order, raw keys, no coercion | [I][T] | STATE 1635–1647 |
| Sheet rejected by Seq operations (`map`, `scan`, `each`, `reduce`, `lifecycle_repeat`) | [I][V] (no dedicated test; guard `builtins.py:2518`) | probes, appendix A1 |
| Flow lazy, pull-based, single-use; `take` no over-pull; finalization of closeable sources | [I][T] | STATE 1688–1860; `tests/unit/test_flow_phase1.py` |
| `scan(step, init, source)`, `reduce(f, acc, xs)` | [I][T] | STATE 1753, 502 |
| `lifecycle_repeat(peers, source, work)`; per-element `element`/`index` (**1-based**); List eager, Flow lazy | [I][T] | STATE 3248–3254; `tests/unit/test_lifecycle_repeat.py` |
| `lines(list)` requires a List of strings | [I][V] | appendix A2 |
| E14-11 record-oriented proving case over **string** rows | [I][T] | `examples/r14_repeated_record_lifecycle_proving_case.genia` |
| Validation: `validate_record`, `validate_each`, `collect_validated` (`index` **0-based**) | [I][T] | STATE 2360–2510 |
| Protected values transported exactly; rejected by sinks | [I][T] | STATE 377–398; `tests/unit/test_protected_sinks.py` |
| Core IR: no node for Sheet; builtins are runtime-only | [I] | `spec/manifest.json` `core_ir_contract`; STATE 1732, 3221 |

**Focused existing checks** (from `/home/user/genia-2026`; partial evidence only, no full regression):

| Command | Result |
|---|---|
| `uv run pytest -q tests/unit/test_sheet.py tests/unit/test_sheet_native_tests.py tests/spec/test_sheet_shared_specs_335.py tests/doc/test_sheet_truth_sync.py tests/spec/test_r18_surface_reconciliation_shared_specs_794.py` | 65 passed |
| `uv run pytest -q tests/unit/test_lifecycle_repeat.py tests/unit/test_r14_repeated_record_lifecycle_proving_case_695.py tests/unit/test_flow_phase1.py tests/unit/test_validate_each.py tests/unit/test_sheet.py tests/unit/test_protected_sinks.py` | 165 passed |

Results for this revision's own checks are in §14.

---

## 3. Verified dependency / status table

Statuses were read from GitHub (2026-10-25), not inferred from roadmap text. Unchanged from revision 1
except where noted.

| Item | Current status | Evidence | Blocks | Action |
|---|---|---|---|---|
| [#1067](https://github.com/m0smith/genia-2026/issues/1067) | Closed (completed) 2026-10-14. | issue | Nothing | None. |
| [#1229](https://github.com/m0smith/genia-2026/issues/1229) | Closed 2026-10-16. | issue | Nothing | None. |
| [#1230](https://github.com/m0smith/genia-2026/issues/1230) / [PR #1254](https://github.com/m0smith/genia-2026/pull/1254) | Closed / merged 2026-10-16T16:55:36Z; fallback removed. Write-through residue tracked by #1257. | PR body | Nothing | None. Third-party reliance remains unknown (stated in the PR). |
| [#1249](https://github.com/m0smith/genia-2026/issues/1249) | **Issue open**, no comments. Contract merged and maintainer-approved ([PR #1255](https://github.com/m0smith/genia-2026/pull/1255), 2026-10-16T20:28:24Z); doc header "MAINTAINER-APPROVED SEMANTIC CONTRACT … NOT IMPLEMENTED". | PR #1255; `docs/design/pre-r29-default-open-and-immutable-binding-contract-DRAFT.md` | Pre-flight/contract/design/TEST: no. Implementation: only through the #1250/#1251 gate. | Maintainer to tick/close #1249 or note that #1255 satisfies it. Not closed here. |
| [#1250](https://github.com/m0smith/genia-2026/issues/1250) | **Open.** Slice A merged (PR #1260); Slice B (#1261) merged (PR #1262, `6d50a36`); **Slice C ([#1269](https://github.com/m0smith/genia-2026/issues/1269)) is only a draft RED PR [#1270](https://github.com/m0smith/genia-2026/pull/1270)** with open decisions D1–D7; Slices D and E unstarted. | issue/PR | Implementation (per `sequence.md`) | Do not interfere. |
| [#1251](https://github.com/m0smith/genia-2026/issues/1251) | **Open, untouched.** Its acceptance allows a "maintainer-approved scoped exception". | issue | R29 language-facing implementation; release completion | See §1, §13. No exception exists. |
| [#1192](https://github.com/m0smith/genia-2026/issues/1192) / [#1101](https://github.com/m0smith/genia-2026/issues/1101) | Open trackers; legacy backlog explicitly non-blocking. | issues | Nothing | §11 slice. |
| [#1236](https://github.com/m0smith/genia-2026/issues/1236) | Open; non-blocking. | issue | Nothing | R29 must not implement it. |
| [#1257](https://github.com/m0smith/genia-2026/issues/1257) | Tracking only. | `sequence.md` | Nothing | Risk R-8. |

**Discrepancies recorded:** (A) roadmap text lags (gate described as one pending item; actual state is
contract merged, A and B merged, C in RED, D/E unstarted, #1251 untouched, #1249 still open);
(B) no R29 umbrella issue; (C) main commit `0e63dc1` cites "#1269" for lifecycle-adapter work that
belongs to #1271 (traceability only); (D) Sheet has no capability record (§9); (E) index base mismatch
(§7 D3); (F) "Sheets are not Seq-compatible" has no dedicated test for `map`/`each`/`scan`/`reduce`/
`lifecycle_repeat` (§10 T2).

---

## 4. Executable composition evidence

All programs below were run with `uv run genia <file>` on `main@79c073b`. They are **[V]** probes held in
scratch space, **not** committed tests. The boundary function `records/1` does not exist, so the
Sheet→record step uses a hand conversion `as_records` that is a stand-in for the candidate (it demonstrates
downstream composition only; it is not evidence that `records/1` behaves the same way).

### 4.1 Replacement for the invalid bridge: List of records → Flow

```genia
to_flow(xs) = evolve(0, inc) |> take(length(xs)) |> map((i) -> unwrap_or(nil, nth(i, xs)))
```

The reviewer's equivalent form, verified to give identical results, is
`collect(map((i) -> unwrap_or(nil, nth(i, xs)), take(length(xs), evolve(0, inc))))`.

| Check | Result [V] |
|---|---|
| Nonempty `[{n: 1}, {n: 2}, {n: 3}]`, both forms | `[{n: 1}, {n: 2}, {n: 3}]` |
| Empty `[]`, both forms | `[]` |
| Bounded demand: stage with a counter, `to_flow(xs) \|> take(2) \|> collect` over 3 records | `[{n: 1}, {n: 2}]`; the per-element stage ran exactly **2** times (no over-pull) |
| Single-use: collect the same Flow value twice | `Error: Flow has already been consumed` |
| Invalid original idea `collect(lines([{n: 1}]))` | `Error: lines expected a list of strings` |
| `collect(as_seq([{n: 1}]))` | `[{n: 1}]` — `as_seq(list)` returns the List unchanged (STATE 548); it is **not** a Flow bridge |

No existing function converts a List of Maps to a Flow directly; the composition above uses existing
semantics only and no new builtin is proposed for it. If the proving case finds it too awkward, that is
evidence for a *separate* decision (e.g. alongside #1236/#1208), not for widening R29. The per-pull cost
of `nth` was **not measured** and no performance claim is made [U].

### 4.2 What each term means (and does not mean)

- **Eager allocation:** `records(sheet)` would materialize the complete List before any pipeline stage
  runs. Memory is proportional to row count. A Sheet is already fully materialized and immutable [I], so
  eagerness adds no new laziness loss but doubles row storage for the call's lifetime.
- **Lazy downstream processing:** begins only after `to_flow`; stages after it pull one element at a time.
  It does not make the allocation lazy.
- **Bounded demand / no over-pull:** observed above (2 pulls for `take(2)`), and for `lifecycle_repeat`
  below. Existing guarantee [I][T]; R29 adds a proof, not a mechanism.
- **Single-use:** the Flow from `to_flow` is single-use; the underlying List is reusable. Build a new Flow
  per consumer.
- **Finalization:** the Flow is List-backed, so there is no closeable resource; Lists are never finalized
  (STATE 1792–1801). The observable early-termination guarantee comes from `lifecycle_repeat` element
  scopes, shown next. Resource-backed finalization is out of scope for R29.

### 4.3 Lifecycle: envelope versus callback value [V]

`lifecycle_repeat([audit_peer], to_flow(recs), work) |> take(2) |> collect` over 4 records returned two
**envelopes**, not the callback's values:

- envelope keys: `status, state, scope, phase, peer, result, primary_failure, cleanup_failures`;
- `status` is `ok` for both; `result` is `some(<callback value>)` (first: `some({id: 1})`);
- extracting callback values requires `unwrap_or(nil, r.result)` → `[{id: 1}, {id: 2}]`;
- peer log, in order: `enter 1, exit 1, enter 2, exit 2` — only two element scopes were ever entered, and
  each was fully unwound before the next pull.

Consequences for the proving case: the pipeline must filter on `status == quote(ok)` and unwrap `result`
before `validate_each`/`collect_validated`/`collect_sheet`; a raising callback yields a non-`ok` status with
`result = none("lifecycle-no-result")` (STATE 3240–3241), which is data, not an exception.

### 4.4 Round-trip: precise, conditional guarantees

Statement revised from "`collect_sheet(records(s))` reconstructs `s`". Measured with the hand conversion
(`rows(s)` → pair-lists → maps → `collect_sheet`):

| ID | Case | Result [V] | Guarantee |
|---|---|---|---|
| G1 | Nonempty, ≥1 column, symbol names (`name`, `age`) | `back == s` is `true`; columns and rows equal | Holds under G4/G6 conditions |
| G2 | **Zero-row Sheet with columns** (`sheet([[a, []], [b, []]])`, shape `[[rows,0],[columns,2]]`) | records `[]`; `collect_sheet([])` has shape `[[rows,0],[columns,0]]` | **Schema is lost.** Accepted limitation; columns must be obtained from `columns(s)` separately. No schema wrapper proposed. |
| G3 | **Nonzero rows, zero columns** (`select([], s)`: 2 rows, 0 columns) | records `[{}, {}]`; `collect_sheet` gives `[[rows,2],[columns,0]]`, `== original` is `true` | Row count survives because each row is an empty Map; depends on `collect_sheet` accepting empty maps (verified) |
| G4 | Exact column-name identity and order, names of kinds Integer `1`, Boolean `true`, String `"1"`, List `[1, 2]`, Symbol `sym`, Decimal `1.5` | `columns(back) == columns(s)` and `back == s` are `true` | Holds for these kinds; other legal map-key kinds must be added in the TEST phase. Names must be in the map-key family (nil/Outcome/Map names cannot exist: `sheet` rejects them) |
| G5 | Cells and protected values (a protected leaf from `config_provider`→`secret_get`) | `rows(back) == rows(s)` is `true`; `display` shows `<protected>`; `json_encode` → `err("protected-value", …)`; `render_csv` → `Error: protected-value: render-csv cell at row 0, column 0`; no sentinel in output | Exact transport per STATE 393; cell values are not copied or coerced. Only `==`/render/sink behavior was verified; carrier identity at the Python-object level is a TEST-phase obligation [U] |
| G6 | Key-type asymmetry | A Sheet with **symbol** columns round-trips to symbol keys. `collect_sheet([{name: "Ann"}])` produces **string** column `"name"`, so `== sheet([[quote(name), ["Ann"]]])` is `false` | A round trip preserves whatever key type the Sheet had; it does not normalize string and symbol names |
| G7 | Duplicate or illegal names | Unreachable: `sheet` rejects duplicates and non-map-key names | No new error path |

These are guarantees *of the candidate contract to be decided in R29-C*; none is implemented behavior for
a Sheet→record function today.

### 4.5 Protected-value diagnostics [V]

The probe (Appendix B, `protected.genia`) puts a protected leaf (built with `config_provider` →
`secret_get`; sentinel `SENTINEL_R29_XYZ`) in a record and runs the **invalid-field** branch of
`validate_field` inside `validate_each`, because that branch copies the raw `actual` into the diagnostic
context (STATE 2387, 2395). It then pushes the result through `collect_validated`:

| Surface | Result [V] | Sentinel occurrences |
|---|---|---|
| `display(result)` / `display(collect_validated(result))` | renders `actual: <protected>` | 0 |
| `debug_repr(result)` | renders `actual: <protected>` | 0 |
| `json_encode(result)` / `json_encode(collect_validated(result))` | `err("protected-value", {operation: "json-encode"})` | 0 |
| `print(result)` / `print(collect_validated(result))` / `print(token)` | `Error: protected-value: print` (rejected, nothing written) | 0 |
| `render_csv(sheet_with_protected_cell)` | `Error: protected-value: render-csv cell at row 0, column 1` | 0 |
| `rows(collect_sheet(records)) == rows(s)` for the protected-cell Sheet | `true` (exact transport) | n/a |

No leakage was found in these paths. This is not a committed test; the TEST phase must commit it (§10). A
`validate_each` run whose records hold protected values is therefore *not* printable with `print`; the
proving case must render diagnostics through `display`/`debug_repr` or avoid printing the raw result.
If a leak is found in an R29-supported path it must be **fixed before that path is accepted**; recording an
issue is insufficient.

---

## 5. Semantic boundaries (capability analysis)

"Compose" = existing, unchanged mechanisms. "Candidate" = would need a new public interface or behavior and
a contract decision. None of this is approved.

| ID | Capability | Already implemented | Compose without new semantics | Genuinely new | Principal risk |
|---|---|---|---|---|---|
| C1 | Explicit Sheet→record boundary | `rows` (pairs), `collect_sheet` (reverse) | Hand conversion (user code) | **[P]** `records(sheet) -> List<Map>`: pure, eager, total, no I/O | Name (D9); key mapping (D1) |
| C2 | Deterministic row/column order | [I] `rows`, `render_csv` | — | Evidence only: Map entry order follows column order | Low |
| C3 | Per-record context | `lifecycle_repeat` `element`/`index` | `index` as row number (1-based) | Decision D3 only; no index API | Base mismatch with `collect_validated` (0-based) |
| C4 | Flow demand, bounded consumption, finalization | [I][T] | `to_flow` (§4.1) | Proof only | Eager allocation is not hidden (§4.2) |
| C5 | R14 repeated scopes | [I][T] | `lifecycle_repeat(peers, to_flow(records), work)`; unwrap envelope | Proof only | Python-only (no C++ lifecycle) |
| C6 | `scan`/`reduce` state | [I][T] | Yes | Evidence only | C++ lacks list-form `scan` (STATE 134) |
| C7 | Schema-preserving vs changing | `where`, `select`, `derive`, `collect_sheet` | Yes | Classification in the contract only; no union/pad variant | R30/R31 creep |
| C8 | `some`/`none`/`err` | [I] | `validate_each` → `collect_validated` → `collect_sheet(clean)` | None | `keep_some_else` raises on `err` (#1014/#1236, not R29) |
| C9 | Protected-value non-leakage | [I][T] transport and sinks | Yes | Tests at the new boundary | Diagnostic context copies raw `actual` (§4.5) |
| C10 | Shared eval/flow/error evidence | partial | — | New cases; accounting in §9 | Capability accounting |

**Non-goals preserved:** AWK `$0`/`$1`/`NR`/`NF` syntax; mutable row globals; implicit Sheet→Seq
compatibility; dataframe/query DSLs; joins/grouping/windowing; automatic coercion; a second Outcome,
Template, or validation model; AWK execution mode. Not promoted from R30 (shape/rank, scalar lifting,
whole-column derivation), R31 (grouping, ordering, joins), or R32 (provider sources/sinks). Not
implemented by R29: named pipeline composition (#1236), Outcome `bind` (#1014), `count` ergonomics
(#1208), file/CSV/JSONL readers into Sheets.

---

## 6. Open architectural decisions and recommendations

None is approved.

| ID | Decision | Recommendation |
|---|---|---|
| D1 | Record shape and key mapping | Map keyed by the Sheet column name unchanged; no coercion; conditional guarantees G1–G7 stated in the contract. |
| D2 | Eager List vs lazy Flow | **Eager List only.** A Flow is obtained by the application-owned composition in §4.1. |
| D3 | Row-index base | Document existing bases (1-based `lifecycle_repeat`, 0-based `collect_validated`); add no index API. |
| D4 | Outcome items in the record stream | Leave as is; use `validate_each` + `collect_validated`; record `keep_some_else` limitation (owned elsewhere). |
| D5 | Protected diagnostics | Test; if an R29-supported path leaks, fix before acceptance. |
| D6 | Duplicate/illegal names | Contract states the invariant (G7); no new error path. |
| D7 | Sheet capability accounting | Introduce a Sheet capability with an issue-backed C++ gap, via the migration in §9. Needs maintainer approval. |
| D8 | When the #1251 exception is requested | At the implementation gate, with contract and RED SHA; scope in §13. |
| D9 | Name of the boundary function | **Not decided.** `records` is the working placeholder. Evidence against a bare generic name: two repository programs bind `records` (`examples/mcp/validated_records.genia:28`, `examples/mcp/validated_records_broken.genia:23`); today rebinding a builtin name with `=` works, but `rows =: 5` is already rejected (`Cannot declare immutable binding rows: name is reserved by the runtime`, **[V]**), so a builtin named `records` would make `records =: …` an error in Model B code. A namespaced name consistent with `collect_sheet`/`render_csv` (e.g. `sheet_records`) avoids this; the contract must weigh it. Verified [V]: `rows = 5` works (plain rebinding of a builtin name), `f(rows) = rows` works (parameter shadowing), `rows =: 5` is rejected; `records` is additionally a parameter name in `examples/r10_*`, `r12_*`, `r13_*` (harmless: parameters shadow). |
| D10 | Mixed-family conformance case | See §9.5. |
| D11 | MCP worker allowlist classification of the new name | See §10 (needed so the default-deny profile does not silently remove it). |

---

## 7. PORTABILITY ANALYSIS (section 3a; seven required fields)

- **Portability zone:** *Portable language contract, Python-reference-host implementation.* The Sheet
  contract is a language contract (STATE separates "LANGUAGE CONTRACT" from "PYTHON REFERENCE HOST");
  the candidate boundary is a portable observation (row-ordered Maps from a Sheet). Lifecycle and
  protected values are portable in contract but Python-only in implementation, so those proofs are
  Python-host-only evidence.
- **Core IR impact:** `none`. No `Ir*` node family changes; Sheet and builtins are runtime-only.
- **Capability categories affected:** a new Sheet capability is proposed (name TBD in R29-C; working name
  `sheet_values`; §9); `flow_phase_1` is consumed only as an existing capability. No effect on
  `cli_pipe_mode`, `refs`, `cell_primitives`, `process_primitives`, `json_*`, `bytes_utf8`, `repl`.
- **Shared spec impact:** Phase-gated plan in §9 and §10: retro-gating of existing Sheet cases, new
  eval/error/flow cases for the boundary, a decision on the mixed-family case; lifecycle and protected-value
  proofs stay host-specific. Executable-conformance obligation
  (`docs/architecture/executable-semantic-conformance.md`): (1) authority = STATE Sheet section after
  contract; (2) shared evidence = §9/§10 cases; (3) applicability via the existing `spec/manifest.json`
  vocabulary plus the D7 addition; (4) host claim impact = C++ declares nothing, issue-backed gap;
  (5) implemented-truth docs to sync after verification = STATE, RULES, REPL README, README, book,
  cheatsheets, generated reference, MCP registry.
- **Python reference host impact:** one function in `src/genia/sheet.py`; registration in `builtins.py`;
  public-doc entry in `src/genia/host_builtin_docs.py`; MCP worker allowlist classification in
  `hosts/python/mcp_worker_profile.py`; `@doc`/`@category` and `tools/gen_function_docs.py` outputs; the
  maintained-code documentation ratchet applies to new bindings.
- **Host adapter impact:** Python protocol adapter claims every manifest capability `supported` by
  construction (`hosts/python/protocol_adapter.py::_python_claimed_capabilities`), so adding a manifest
  capability needs no adapter edit; the MCP worker profile (a host policy file) does need an edit (D11).
  No new transport or adapter.
- **Future host impact:** C++ (`m0smith/genia-cpp`) has no Sheet implementation (`sheet`/`collect_sheet`
  appear only in `src/genia2026_known_globals.hpp`). R29 does not implement Sheet in C++. C++ stays
  `unsupported` with an issue-backed gap (§9); a separate genia-cpp change re-pins evidence. No other
  hosts are invented.

**MCP language-knowledge impact:** *Affected after implementation, not now.* A new public Sheet function and
the "records are explicit; Sheets are not Seq" idiom are knowledge `genia_language_profile` projects. This
pre-flight changes no STATE, registry, or MCP source. The implementation/docs phases must update the
`mcp_language_profile` registry in `docs/contract/semantic_facts.json`, regenerate `apps/mcp/mcp.genia` with
`tools/gen_mcp_language_profile.py`, and pass `--check`. Execution-policy consistency is in §10 (the MCP
worker cannot create protected values: `config_provider`/`secret_get` are denied there).

**Feature maturity:** Experimental.

---

## 8. Risk register and mitigations

| ID | Risk | Mitigation |
|---|---|---|
| R-1 | Implementation starts before the Model B gate | §13 condition 1; exception is explicit, bounded, maintainer-recorded. |
| R-2 | Slice C/D/E change function definition/export semantics under R29 code | Host builtin; proving code uses no `=:`, no overlapping varargs, no alias declarations; **post-#1251 Model B/R29 interaction regression** (§10 T3). |
| R-3 | Scope creep into R30/R31, readers, or new bridge builtins | Non-goals are contract acceptance criteria; each PR is checked. |
| R-4 | Implicit Seq compatibility creep | Negative tests (§10 T2) made explicit regression guards. |
| R-5 | Key identity drift (symbol vs string) | G1–G7 and TEST cases. |
| R-6 | Portability overclaim | §9 accounting; every claim labeled Python reference host. |
| R-7 | Protected-value leakage | §4.5 probes become TEST cases; leakage in a supported path blocks acceptance. |
| R-8 | #1257 runtime-owned-name write-through lets an entry program shadow a builtin seen by modules/prelude | Documented residual; D9 name choice reduces exposure; no R29 reliance. |
| R-9 | Documentation and generated-artifact drift | §10 documentation/generated checks. |
| R-10 | Large high-conflict PRs (`builtins.py`, `GENIA_STATE.md`) | Small PRs; accounting, boundary, and docs separated (§12). |
| R-11 | Eager allocation doubles row storage; `nth`-based bridge cost unmeasured | State in contract; no performance claim; measure only if a TEST-phase benchmark is approved. |
| R-12 | Retro-gating 19 existing specs changes evidence counts and could hide a regression | §9.4 migration with before/after counts and an unchanged Python pass set. |
| R-13 | MCP default-deny profile silently drops the new name | D11; classification test must fail first. |

---

## 9. Capability and conformance accounting

### 9.1 What was measured

The 20 Sheet-related shared cases are: `spec/eval/{collect-sheet-core, render-csv-core, row-get-core,
sheet-derive-core, sheet-empty-core, sheet-select-immutable, sheet-shape-columns-rows, sheet-where-core,
r18-surface-sheet-column-identity, r18-conformance-sheet-structural-equality,
r18-conformance-cross-family-summary}` and `spec/error/{error-collect-sheet-missing-column,
error-collect-sheet-not-seq, error-render-csv-not-sheet, error-render-csv-unsupported-cell,
error-row-get-missing-column, error-row-get-not-row, error-sheet-derive-duplicate-column,
error-sheet-select-missing-column, error-sheet-unequal-column-lengths}`. Every one has an empty
`requires`. Run through the subprocess protocol (scratch script, not committed):

| Host | Result [V] | Per-case reason |
|---|---|---|
| Python (`python -m hosts.python.protocol_adapter`) | **20 pass** | — |
| C++ (`genia-cpp` `44456ba`, built with `cmake`, Release, out-of-tree) | **20 unsupported** | The same generic adapter message for all 20: "genia-cpp implements only the E24-2..E24-7 vertical slice …"; it names no Sheet capability |

This reproduces the independent review.

### 9.2 Three different "unsupported" meanings

Per `tools/spec_runner/capabilities.py`, `runner.py`, and `host_parity_gate.py`:

| Class | Rule | Applies to Sheet today |
|---|---|---|
| **Baseline-applicable** | A case with empty `requires` "belongs to the base required-capability set every conforming host implements by definition and is always applicable". The runner invokes the adapter. | **All 20** Sheet cases |
| **Adapter-reported unsupported** | The adapter itself answers `unsupported` for a baseline case. The runner counts it in `unsupported` but nothing links it to a capability or a gap entry. | **All 20 on C++** (reason is generic, not Sheet-specific) |
| **Capability-excluded** | A case with `requires` whose capabilities the host does not declare exactly `supported` is reported `unsupported` **without invoking the adapter**, with a reason naming the capability. | **None** — no Sheet capability exists |

The parity gate compares only `optional_capabilities` (undeclared = unsupported) against
`spec/known_host_gaps.json`; per-case adapter-reported unsupported outcomes are invisible to it. Therefore
the Sheet family is today an *undocumented, baseline-claimed* gap. This is the accounting defect the
review identified.

### 9.3 Why a new capability alone changes nothing

Adding a capability name to `spec/manifest.json` does not alter any existing case: the 20 cases stay
`requires`-empty, still baseline-applicable, still adapter-reported unsupported on C++. Only a
`requires: [<capability>]` line reclassifies a case. Adding the name *without* a matching
`spec/known_host_gaps.json` entry would make the parity gate report `UNDOCUMENTED_GAP` for C++
(`cpp_status` undeclared → unsupported, no gap). The two edits therefore have to land together, and the gap
entry requires a real tracking-issue reference. Precedent for retro-gating: R26-2 retro-gated every
previously-ungated JSON/Bytes case with the matching `requires:` tag
(`docs/state-record/hosts-and-conformance.md`, B008).

### 9.4 Concrete migration plan (future work; **not performed in this revision**)

| Step | Work | Phase | Edits |
|---|---|---|---|
| M1 | Decide capability name and scope; decide D10 | R29-C contract | none |
| M2 | Create the issue-backed C++ gap tracking issue | immediately before R29-T0 | (issue creation requires approval) |
| M3 | Add the capability to `optional_capabilities` | R29-T0 | `spec/manifest.json` |
| M4 | Add `requires: [<capability>]` to **19** existing Sheet cases (all except the mixed-family case, pending D10) | R29-T0 | 19 YAML files |
| M5 | Add the C++ gap entry: `capability`, `reason`, `tracking_issue`, `affected_host: cpp`, `affected_tests` (the 19 retro-gated and the new R29 cases), `removal_condition` | R29-T0 | `spec/known_host_gaps.json` |
| M6 | New R29 boundary cases carry `requires: [<capability>]` from creation | R29-T1 | new YAML under `spec/eval`, `spec/error`, `spec/flow` |
| M7 | Python claim: automatic (adapter claims every manifest capability `supported`); verify Python pass set is unchanged and the in-process runner still passes | R29-T0 | none (verification only); update `docs/host-interop/HOST_CAPABILITY_MATRIX.md` |
| M8 | C++: no implementation; declares nothing (undeclared = unsupported); re-pin `evidence.json` and contract revision in `genia-cpp` as a separate repository change. Retro-gated cases move from adapter-reported to capability-excluded with a truthful reason; the `unsupported` total is expected to stay 20 + the new gated cases, but the exact counts must be recomputed, not predicted | after R29-T0 merges | `m0smith/genia-cpp` (separate PR) |
| M9 | Remove the gap only when C++ declares the capability `supported` and the gate reports `PARITY_OK` | future (out of R29) | — |

Before/after check for M4–M8: Python total and pass counts must not decrease; the full set of formerly
passing Sheet cases must still pass; `tests/unit/test_host_parity_gate.py` and
`tests/spec/test_python_protocol_adapter_parity_762.py` must pass.

### 9.5 The mixed-family case (D10)

`spec/eval/r18-conformance-cross-family-summary.yaml` asserts 11 equality families in one expected
vector, including Sheet (indices 16–17), and also exercises `ref` (`refs`), `utf8_encode` (`bytes_utf8`),
`represent`, and a protected carrier via `config_provider`/`secret_get` (no capability name exists for
representations or protected carriers). It is documented as the implementer's first-run check
(`docs/host-interop/HOST_PORTING_GUIDE.md:168`, `docs/releases/R18.md:139`) and listed in
`tests/spec/test_r18_conformance_protocol_evidence_795.py:63`.

- Gating it **only** on the Sheet capability would be wrong in both directions: it would attribute an
  unsupported result to Sheet that is equally caused by other families, and a host missing only Sheet
  would lose the other ten families' evidence.
- Leaving it ungated keeps a *baseline* case asserting an *optional* capability's family.

Options for R29-C: (1) **recommended** — move the Sheet pair out of the aggregate (the dedicated
`r18-conformance-sheet-structural-equality` and `r18-surface-sheet-column-identity` cases already cover
Sheet equality and identity), regenerate the expected vector, and update the three references above; this
touches a protected R18 summary and needs R18-owner review; (2) gate it on every involved capability —
not completable because representations and protected carriers have no capability; (3) leave it ungated
as a recorded exception. Whatever is chosen, **no case may hide unrelated families under a Sheet-only
requirement.** The decision, its text, and the spec edit belong to R29-C/R29-T0, not this pre-flight.

### 9.6 Host-specific evidence (cannot use the shared protocol)

Lifecycle composition (`lifecycle_repeat`, Python-only), injected/real protected-value proofs, MCP worker
policy, and generated documentation checks stay in Python unit/native/CLI tests whose module docstrings
say they are host-specific (`AGENTS.md` portable-behavior test placement). The C++ host has no lifecycle or
protected values, so no shared case may require them.

---

## 10. Acceptance criteria and future verification

### 10.1 TEST-phase categories

| Category | Must fail before `records/1` exists? | Content |
|---|---|---|
| **T0 conformance accounting** | n/a (infrastructure) | M3–M5, M7; counts unchanged for Python |
| **T1 new boundary tests** | **Yes** | Shared eval: row order, column order, immutability, empty Sheet, zero-row and zero-column behavior (G2/G3), round trip G1/G4/G6, protected-cell passthrough; shared error: non-Sheet input; shared flow: bounded/no-over-pull consumption of a Flow built by `to_flow` from `records`; Python: protected sinks/diagnostics after the boundary, `records` callable via alias/higher-order/pipeline/module visibility, metadata/`help`, runtime-reserved-name behavior; MCP allowlist classification; **end-to-end proving-case spec** (CLI/native) written in this phase |
| **T2 existing composition regression** | **No — written in the TEST phase but expected to pass against the current tree (they need no `records/1`); the TEST commit records them passing. A T2 test that fails at that commit is a defect in the test or a finding about current behavior, never an "expected failure".** | Sheet rejected by `map`/`each`/`scan`/`reduce`/`lifecycle_repeat` (no dedicated test exists today; this closes discrepancy F); `to_flow` empty/nonempty/bounded/single-use; lifecycle envelope extraction including a raising callback; hand-conversion round trips (G1–G6); protected diagnostics/sink behavior via hand conversion |
| **T3 post-#1251 interaction** | Runs after the Model B gate closes | Re-run T1+T2 plus a Model B/R29 regression: name resolution of `records/1` when entry code defines or aliases it, `=:` collision behavior, module visibility, and open-by-default effects |

### 10.2 Items the future work must verify (each maps to a test or audit step)

- Source and Core IR: ordinary call, alias (`r = records`), higher-order use (`map(records, [s])`), pipeline
  use (`s |> records`), unchanged parse/Core IR (no new node).
- Module visibility, metadata (`help`, `doc`, `meta`), `@doc`/`@category`, and runtime-reserved names
  (D9 evidence in §6).
- MCP execution policy: `hosts/python/mcp_worker_profile.py` is default-deny; a name in neither the allowed
  nor denied set is removed and its classification test fails, so the new name must be classified
  deliberately (D11); `genia_language_profile` registry and generated `apps/mcp/mcp.genia` consistent.
- Protected-value non-leakage in diagnostics, `display`, `debug_repr`, `json_encode`, `render_csv`, and
  output sinks; a leak in an R29-supported path is fixed before acceptance.
- Lifecycle envelope extraction (§4.3), including a raising callback.
- Zero-row and zero-column behavior (G2, G3).
- Python/C++ shared-spec selection and parity evidence (§9), including `host_parity_gate`.
- Full Python regression: `uv run pytest -n auto -q -m "not loopback"` and `uv run pytest -n auto -q -m
  loopback`.
- Documentation and generated artifacts: `tests/doc`, cheatsheet tests, `tools/gen_function_docs.py --check`,
  `tools/lint_doc.py --require-coverage`, `tools/gen_mcp_language_profile.py --check`, code-documentation
  ratchet.
- Post-#1251 Model B/R29 interaction regression (T3).

---

## 11. Documentation and technical-debt disposition

**Authoritative documents** (`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`) are
**not edited** by this pre-flight; they are updated only for verified implemented behavior (R29-X), with
`docs/book/`, cheatsheets (with `[case:]` markers), `docs/design/composability-matrix.md` if its family
derivation changes, `docs/contract/semantic_facts.json`, the MCP registry, generated reference pages, and
`docs/strategy/roadmap/r25-r29.md` status. This document labels all new names as candidates.

**Selected #1192 slice (unchanged, non-blocking):** `tests/native/sheet_helper_behavior.genia` — nine
baseline identities in `.github/code-documentation-baseline.json` (the module and eight bindings:
`collect_sheet_builds_sheet_from_homogeneous_records`, `empty_sheet_has_zero_shape_columns_and_rows`,
`render_csv_produces_deterministic_escaped_report_text`,
`row_get_returns_named_cell_directly_and_inside_where_derive`,
`sheet_derive_appends_outcome_cells_and_preserves_original`,
`sheet_select_reorders_columns_and_preserves_original`, `sheet_shape_columns_and_rows_are_deterministic`,
`sheet_where_filters_rows_and_preserves_original`). Baseline total at this snapshot: 2,798 gaps (freshly
counted). Land before R29-T so test additions do not conflict. Carry-forward, owned by #1192: remaining
Flow/Seq/prelude identities (e.g. `flow.genia` 19, `list.genia` 8, `awk.genia` 4,
`tests/native/r3_validation_helpers.genia` 26); the R29 audit names the next slice.

---

## 12. Release decomposition (aligned to `docs/process/run-change.md`)

Each `run-change.md` step is its own stopping point; phases are never combined.

| Step (run-change) | R29 item | Notes |
|---|---|---|
| 1–3 Branch, pre-flight, commit | This document (PR #1284) | Docs-only; draft |
| — (parallel, independent) | **R29-D0** #1192 slice (§11) | XS, docs metadata only |
| 4–5 Contract, commit | **R29-C** | Decide D1–D11 and the §9.5 option; produce `docs/design/r29-…-contract.md` marked PROPOSED→approved. **No tests.** |
| 6–7 Design, commit | **R29-G** | Map clauses to files; registration; capability accounting plan (M1–M9); MCP classification plan |
| 8–9 Failing tests, commit | **R29-T0** then **R29-T1** (+ **T2** recorded passing) | T0: manifest, retro-gating, gap entry (needs approved tracking issue). T1: new failing boundary tests **and the proving-case end-to-end spec**, SHA recorded. T2: existing-composition guards, recorded as already passing |
| 10–11 Implementation, commit | **R29-I** | **Gate: §13 condition 1.** Only `records/1` + registration/doc/metadata/allowlist; references the failing-test SHA |
| 12 **Code Quality & Maintainability Review** (`code-maintainability-review.md`; inspects the implementation diff and affected call sites, records reviewer, evidence, findings, verdict, follow-ups) | **R29-M** | Required, after implementation (step 11) and before docs (step 15); reviewer other than the implementer preferred |
| 13 Resolve blocking findings, fresh verdict | **R29-M** | Focused fix commits only; **a FAIL verdict blocks docs** |
| 14 Commit review handoff/evidence | **R29-M** | Per existing handoff conventions |
| 15–16 Docs prompt, commit | **R29-X** | Per-surface PRs (STATE; cheatsheets; semantic facts + MCP registry; generated reference) may run in parallel once R29-M passes |
| 17–18 Audit, commit | **R29-A** | Independent truth audit; records #1192 slice evidence, next owned slice |
| 19–20 Distillation, commit | **R29-Z** | |
| after #1251 | **R29-R** | Re-run T1+T2+T3. Release completion needs #1251 sign-off; the R29 audit cannot close the release before it |

Do not merge until the audit passes. The proving case itself needs **no separate runtime phase**: its
tests are specified in R29-T1, exercised by R29-I, and its example/docs ship in R29-X. No implementation
issues are created now (the branch rule `issue-<number>-<short-name>` is a further reason to create one
umbrella issue only after this pre-flight is approved).

**Parallelism after contract and tests are approved:** R29-D0 any time; R29-G with the genia-cpp evidence
re-pin preparation; T0 and T1 in two PRs if they touch disjoint files; docs-sync surfaces after R29-M.
Avoid concurrent edits to `GENIA_STATE.md` and `builtins.py`.

---

## 13. Conditions to begin implementation and exception scope

**Conditions for R29-I (all required):**

1. Model B gate: either #1250 Slices C–E and #1251 sign-off are complete, **or** the maintainer records an
   explicit scoped exception on #1251 (none exists; this document does not approve one).
2. R29-C contract approved (D1–D11 resolved).
3. R29-T0/T1 committed with the failing-test SHA, including the approved capability and issue-backed gap.
4. R29-D0 merged or deferred with an owner.
5. No R30/R31/R32 behavior in contract, design, or tests.

Conditions 2–5 do not block contract/design/TEST. **The exception gates implementation, not contract,
design, or TEST.**

**Scope the exception could cover (recommendation only):** one pure, eager Sheet-to-record builtin;
registration, documentation and metadata (including the MCP allowlist entry); tests and conformance
accounting; the executable record-pipeline proving case; the required maintainability review and audit;
and the post-#1251 regression (R29-R).

**It must exclude:** parser, AST, or Core IR changes; the evaluator; the Flow kernel; the lifecycle
runtime; Model B default-open or module-linking behavior; implicit Sheet-to-Seq conversion; Outcome
semantics; R30/R31 operations; a C++ Sheet implementation; and any new List→Flow bridge builtin.

---

## 14. Verification performed for this revision

Run from `/home/user/genia-2026` on the revision-3 tree (documentation-only change; `origin/main` is
still `79c073b`, so the source tree is byte-identical to the one revision 2 tested).

| Command | Result (re-executed for revision 3) |
|---|---|
| Appendix B scripts B1–B5, extracted from this file and run with `uv run genia` | Outputs as recorded in §4 |
| Sheet-case protocol runs, Python adapter and a freshly built `genia-cpp@44456ba` adapter (Appendix B6) | Python 20 pass; C++ 20 unsupported; all 20 `requires` empty; no other shared case uses a Sheet helper |
| `uv run pytest tests/doc -q -n 4` | 397 passed, 35 skipped |
| Sheet suite (§2, first command) | 65 passed |
| Lifecycle/Flow/validation/protected-sinks suite (§2, second command) | 165 passed |
| `uv run pytest -q tests/unit/test_host_parity_gate.py tests/spec/test_r18_conformance_protocol_evidence_795.py` | 31 passed |
| `uv run pytest -n auto -q -m "not loopback"` | 7104 passed, 60 skipped (9 min 9 s) |
| `uv run pytest -n auto -q -m loopback` | 31 passed |
| `git diff --stat origin/main` | Only `docs/analysis/r29-sheet-record-pipelines-preflight.md` |

Not run: `host_parity_gate` against fresh Python and C++ evidence documents; the `genia-cpp` test suite;
generated-reference and MCP-profile `--check` tools (no public function or registry changed). The
`(not loopback)` + `loopback` pair is the repository's full regression partition for socket-restricted
environments.

---

## 15. Recommended next action and issue handling

**Next action:** maintainer review of this revision, then authorization of **R29-C (contract)** only. The
#1251 exception question moves to the implementation gate (§1, D8). The risk-free parallel item is R29-D0.

No R29 umbrella issue exists; none is created here. After approval, create **one** umbrella issue linking
this document and #1249/#1250/#1251/#1192/#1236, and create child issues per phase on demand (including the
C++ gap tracking issue required by §9.4 M2).

Per `AGENTS.md`, work stops here: no contract, TEST, or implementation phase begins, no prerequisite issue
is modified, and no exception is recorded.

---

## Appendix A — Reproduction (scratch programs; not committed)

Run from `/home/user/genia-2026` with `uv run genia <file>` (or `-c`). Programs:

- **A1 (Sheet rejected by Seq operations):** `sheet([[quote(a),[1,2]]]) |> map(inc)` → `pipeline stage 1 failed in
  Value mode at map(inc): stage received GeniaSheet; map expected a Seq-compatible value (list or Flow);
  received GeniaSheet.`; `lifecycle_repeat([], <sheet>, (sc)->1)` → `lifecycle_repeat expected a
  Seq-compatible value (list or Flow); received GeniaSheet.`
- **A2 (bridge):** `to_flow` as in §4.1; `reviewer_form`, `[]`, bounded `take(2)` with a counter, single-use
  second `collect`, `collect(lines([{n: 1}]))`, `collect(as_seq([{n: 1}]))` — results in §4.1.
- **A3 (hand conversion):** `pairs_to_map(row) = reduce((m, kv) -> map_put(m, unwrap_or(nil, nth(0, kv)),
  unwrap_or(nil, nth(1, kv))), map_new(), row)` and `as_records(s) = rows(s) |> map(pairs_to_map)`; used for
  G1–G7.
- **A4 (lifecycle envelope):** `lifecycle_repeat([audit_peer], to_flow(recs), work) |> take(2) |> collect` with
  a peer that logs `enter`/`exit` and `lifecycle_context(scope, quote(index))` — results in §4.3.
- **A5 (protected):** a protected leaf made in pure Genia with
  `config_provider([{kind: quote(values), values: {K: "…"}}]) |> unwrap_or(none)` then
  `secret_get(provider, "K", quote(demo)) |> unwrap_or(none)`; checks in G5 and §4.5.
- **A6 (conformance):** scratch script using `tools.spec_runner.host_executor.execute_spec_via_host` over the
  20 files listed in §9.1, with the Python adapter command above and the C++ adapter built out-of-tree from
  `m0smith/genia-cpp` at `44456ba` (`cmake -S . -B <scratch>/cppbuild -DCMAKE_BUILD_TYPE=Release`).
- **A7 (reserved name):** `rows =: 5` → `Error: Cannot declare immutable binding rows: name is reserved by
  the runtime`; `records =: [1]` currently succeeds (no `records` builtin exists).

Other evidence: PR [#1254](https://github.com/m0smith/genia-2026/pull/1254),
[#1255](https://github.com/m0smith/genia-2026/pull/1255),
[#1262](https://github.com/m0smith/genia-2026/pull/1262),
[#1270](https://github.com/m0smith/genia-2026/pull/1270); issues #1067, #1101, #1192, #1229, #1230, #1236,
#1249, #1250, #1251, #1257, #1261, #1269; code `src/genia/sheet.py`, `src/genia/builtins.py:2518,3145`,
`src/genia/host_builtin_docs.py`, `hosts/python/mcp_worker_profile.py`,
`hosts/python/protocol_adapter.py`, `tools/spec_runner/{capabilities,runner,host_parity_gate}.py`;
specs `spec/manifest.json`, `spec/known_host_gaps.json`.

---

## Appendix B — Scripts re-executed for revision 3 (scratch; not committed)

Run each with `uv run genia <file>` from the repository root on `main@79c073b`. Outputs are in the
sections cited. In file mode the CLI echoes the program's final value, so when the last statement is a
`print(...)` its output appears once as display text and once as the echoed value (for example the final
`[[error, none("lifecycle-no-result")]]` line of B3 prints twice). `as_records` is a stand-in for the candidate `records/1` (hand conversion), so these programs
prove only the composition around it.

**B1 — List of records to Flow (§4.1), including empty, single-use, bounded demand** (expected output:
`[{n: 1}, {n: 2}, {n: 3}]`, `[]`, the same two again, then `Error: Flow has already been consumed`):

```genia
to_flow(xs) = evolve(0, inc) |> take(length(xs)) |> map((i) -> unwrap_or(nil, nth(i, xs)))
rev(xs) = collect(map((i) -> unwrap_or(nil, nth(i, xs)), take(length(xs), evolve(0, inc))))
three = [{n: 1}, {n: 2}, {n: 3}]
print(collect(to_flow(three)))
print(collect(to_flow([])))
print(rev(three))
print(rev([]))
f = to_flow(three)
print(collect(f))
print(collect(f))
```

**B2 — Bounded demand and the invalid bridge (§4.1)** (expected: `[{id: 1}, {id: 2}]`, `2`, then
`Error: lines expected a list of strings`):

```genia
to_flow(xs) = evolve(0, inc) |> take(length(xs)) |> map((i) -> unwrap_or(nil, nth(i, xs)))
recs = [{id: 1}, {id: 2}, {id: 3}, {id: 4}]
c = ref(0)
tick(r) = { ref_update(c, inc); r }
print(to_flow(recs) |> map(tick) |> take(2) |> collect)
print(ref_get(c))
print(collect(lines([{n: 1}])))
```

**B3 — Lifecycle envelope versus callback value (§4.3)** (expected: `[ok, ok]`, `[{id: 1}, {id: 2}]`, an
envelope `some({status: ok, state: completed, scope: element, phase: exit, peer: none("lifecycle-no-peer"),
result: some({id: 1}), primary_failure: none("lifecycle-no-failure"), cleanup_failures: []})`, log
`[[enter, 1], [exit, 1], [enter, 2], [exit, 2]]`, and `[[error, none("lifecycle-no-result")]]` for the raising
callback):

```genia
to_flow(xs) = evolve(0, inc) |> take(length(xs)) |> map((i) -> unwrap_or(nil, nth(i, xs)))
recs = [{id: 1}, {id: 2}, {id: 3}, {id: 4}]
log = ref([])
add(e) = ref_update(log, (l) -> [..l, e])
peer = {
  name: quote(audit),
  enter: (scope) -> { add(["enter", lifecycle_context(scope, quote(index)) |> unwrap_or(none)]); some(nil) },
  exit: (scope, summary) -> { add(["exit", lifecycle_context(scope, quote(index)) |> unwrap_or(none)]); some(nil) }
}
work(scope) = lifecycle_context(scope, quote(element)) |> unwrap_or(none)
out = lifecycle_repeat([peer], to_flow(recs), work) |> take(2) |> collect
print(map((r) -> r.status, out))
print(map((r) -> unwrap_or(nil, r.result), out))
print(out |> first)
print(ref_get(log))
bad(scope) = 1 / 0
out2 = lifecycle_repeat([peer], to_flow(recs), bad) |> take(1) |> collect
print(map((r) -> [r.status, r.result], out2))
```

**B4 — Round-trip cases G1–G6 (§4.4)** (expected: `[true, true, [[rows, 2], [columns, 2]]]`; zero-row
`[[[rows, 0], [columns, 2]], [], [[rows, 0], [columns, 0]], false]`; zero-column
`[[[rows, 2], [columns, 0]], [{}, {}], [[rows, 2], [columns, 0]], true]`; mixed key kinds
`[true, true, ...]`; string-versus-symbol `false`, `["name"]`):

```genia
pairs_to_map(row) = reduce((m, kv) -> map_put(m, unwrap_or(nil, nth(0, kv)), unwrap_or(nil, nth(1, kv))), map_new(), row)
as_records(s) = rows(s) |> map(pairs_to_map)
s1 = sheet([[quote(name), ["Ann", "Bo"]], [quote(age), [3, 4]]])
r1 = as_records(s1)
print(r1)
b1 = collect_sheet(r1)
print([b1 == s1, columns(b1) == columns(s1), shape(b1)])
z = sheet([[quote(a), []], [quote(b), []]])
print([shape(z), as_records(z), shape(collect_sheet(as_records(z))), collect_sheet(as_records(z)) == z])
zc = select([], s1)
print([shape(zc), as_records(zc), shape(collect_sheet(as_records(zc))), collect_sheet(as_records(zc)) == zc])
k = sheet([[1, ["a"]], [true, ["b"]], ["1", ["c"]], [[1, 2], ["d"]], [quote(sym), ["e"]], [1.5, ["f"]]])
kb = collect_sheet(as_records(k))
print([kb == k, columns(kb) == columns(k), columns(k)])
print(collect_sheet([{name: "Ann"}]) == sheet([[quote(name), ["Ann"]]]))
print(columns(collect_sheet([{name: "Ann"}])))
```

**B5 — Protected values (§4.4 G5, §4.5)** — `protected.genia` (the last line is replaced in turn by each
surface listed in the §4.5 table; the sentinel count in the combined output was 0 every time):

```genia
provider = config_provider([{kind: quote(values), values: {K: "SENTINEL_R29_XYZ"}}]) |> unwrap_or(none)
tok = secret_get(provider, "K", quote(demo)) |> unwrap_or(none)
r = validate_each([{n: tok}], (rec) -> validate_field("n", (v) -> false, "number", rec))
cv = collect_validated(r)
display(r)
```

Cell-level transport and `render_csv`:

```genia
pairs_to_map(row) = reduce((m, kv) -> map_put(m, unwrap_or(nil, nth(0, kv)), unwrap_or(nil, nth(1, kv))), map_new(), row)
as_records(s) = rows(s) |> map(pairs_to_map)
provider = config_provider([{kind: quote(values), values: {K: "SENTINEL_R29_XYZ"}}]) |> unwrap_or(none)
tok = secret_get(provider, "K", quote(demo)) |> unwrap_or(none)
s = sheet([[quote(who), ["a"]], [quote(secret), [tok]]])
b = collect_sheet(as_records(s))
print([rows(b) == rows(s), b == s])
print(display(tok))
print(json_encode(rows(b)))
print(render_csv(b))
```

**B6 — Conformance runner** — scratch script `cases.py`: loads the 20 specs named in §9.1 with
`tools.spec_runner.loader.discover_specs`, scans all other specs for `sheet(`, `collect_sheet`, `render_csv`
and `row_get` (none found), and runs each through `tools.spec_runner.host_executor.execute_spec_via_host`
with either `python -m hosts.python.protocol_adapter` (claims from `_python_claimed_capabilities()`) or the
`genia-adapter` binary built by `cmake -S . -B <scratch>/cppbuild -DCMAKE_BUILD_TYPE=Release` at
`genia-cpp@44456baea06b4bb7bdf727e39939dd7150261ee6`. Result: Python `Counter({'pass': 20})`, C++
`Counter({'unsupported': 20})`, every `requires` empty.
