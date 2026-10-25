# R29 — Sheet Record Pipelines: pre-flight

Status: **Pre-flight record (PROPOSED, NON-AUTHORITATIVE).** Documentation only. It defines no
language behavior; every function name, shape, and decision below is a *candidate* for the contract
phase. `GENIA_STATE.md` remains final authority for implemented behavior. No runtime, test, spec,
manifest, or implemented-truth document is changed by this pre-flight.

Process: `AGENTS.md` (R26+ Change Pre-Flight Gate), `docs/process/run-change.md`,
`.github/ISSUE_TEMPLATE/genia-change-preflight.md`, `docs/process/extensions/portability-analysis.md`.
Evidence snapshot: `main` at `79c073b` (2026-10-25). Planning home: `docs/strategy/roadmap/r25-r29.md`
("Release R29", *Planned, not active*). No dedicated R29 planning issue exists (searched issue titles and
bodies for "R29" and "Sheet Record Pipelines": only closed 2026-05 killer-workflow issues
#377/#383/#390/#395/#398/#404 matched); see §13 for the recommended issue handling.

---

## 1. Executive decision

**CONDITIONAL GO** for the contract, design, and TEST phases.
**NO-GO** for the R29 implementation phase until the gate in §11 is satisfied.

Reasons:

1. R29 is **small and mostly compositional**. The repository already has an explicit List→Sheet
   boundary (`collect_sheet`), a Sheet→pair-list boundary (`rows`), lazy Flow, `scan`/`reduce`, R14
   `lifecycle_repeat` with `element`/`index` context, Outcome validation (`validate_each`,
   `collect_validated`) and protected-value transport. The one genuinely missing piece is an explicit
   **Sheet→record(map) boundary**. The smallest coherent R29 is one new boundary function plus proving
   evidence, not a new execution engine.
2. The roadmap gate (`#1249 → #1250 → #1251`) is **not yet satisfied** (§3): the #1249 contract is
   merged and approved, #1250 has merged Slices A and B but Slice C is still in RED/pre-flight and
   Slices D/E have not started, and #1251 (integration, audit, signoff) has had no activity.
   `sequence.md` says language-facing R29 implementation must not start until that gate is satisfied
   or a maintainer-approved scoped exception is recorded on #1251.
3. Several contract decisions (§6) must be made before any test is written, notably the record shape
   and key mapping, row-index base, and C++ capability accounting for the entire Sheet family, which
   today has **no capability and no known-host-gap entry** (§8).

This is not an approval of any candidate behavior.

---

## 2. Current implementation baseline (verified)

Sources: `GENIA_STATE.md` lines 587–625 and 1603–1690 (Sheet), 1688–1860 (Flow), 3217–3310 (R14),
2360–2510 (Outcome/validation), 377–398 (protected values); code at `src/genia/sheet.py` and
`src/genia/builtins.py`. All of the following is **Experimental** and **Python-reference-host only**.

| Capability | Implemented today | Evidence |
|---|---|---|
| Sheet value | Immutable, columnar, named columns, deterministic column order, aligned rows. "Not a lazy value, not a Seq-compatible source." | STATE §"Sheet values (Experimental)" |
| Sheet helpers | `sheet`, `shape`, `columns`, `select`, `where`, `derive`, `rows`, `row_get`, `collect_sheet`, `render_csv` | STATE 1603–1690; `builtins.py:6132-6145` |
| List/Flow → Sheet | `collect_sheet(records)`: finite list or Flow of maps with identical key sets; first record fixes column order; raw (string) keys; no union/pad/coerce | STATE 1635–1647 |
| Sheet → data | `rows(sheet)` = **List of `[name, value]` pair-lists** (not maps); `columns(sheet)` = names | STATE 1615 |
| Sheet → Seq/Flow | **Rejected.** `map`, `scan`, `each`, `reduce`, `lifecycle_repeat` over a Sheet raise the Seq-compatibility `TypeError` | Probes below; `builtins.py:2518` |
| Flow | Lazy, pull-based, single-use; `take` has no over-pull; closeable sources finalized on exhaustion/early close/error | STATE 1688–1860 |
| `scan`/`reduce` | `scan(step, init, source)` (`step(state,item) -> [next_state, output]`, list→list, Flow→Flow); `reduce(f, acc, xs)` mandatory accumulator | STATE 1753, 502 |
| Lifecycle | `lifecycle_repeat(peers, source, element_work)`; fresh scope per element; reserved `quote(element)` and `quote(index)` (**1-based**) context; List eager, Flow lazy | STATE 3248–3254 |
| Record proving case | E14-11 (#695): `record`/`nr`/`nf`-*style values derived by application code from string rows; no AWK syntax | `examples/r14_repeated_record_lifecycle_proving_case.genia` |
| Outcome / validation | `some/none/err`; `validate_record`, `validate_each`, `collect_validated` (`index` **0-based**), `keep_some`; Outcome stored in Sheet cells as inert data | STATE 2360–2510, 611 |
| Protected values | Transported exactly through containers, pipelines, Flow, Sheet cells; rejected by sinks (`json_encode`, Sheet CSV, output) | STATE 377–398 |
| Existing list-only AWK helpers | `fields(row)`, `awkify(fn, xs)` (1-based line numbers) in `src/genia/std/prelude/awk.genia` — legacy, not Sheet-aware | file |
| Core IR | Frozen 32 node + 12 pattern families (`spec/manifest.json` `core_ir_contract`); Sheet is runtime-only, no IR node | manifest; STATE 3221 |

**Probes run during this pre-flight (read-only, scratchpad only):**

- `sheet([[quote(a),[1,2]]]) |> map(inc)` → `pipeline stage 1 failed in Value mode at map(inc): stage received GeniaSheet; map expected a Seq-compatible value (list or Flow); received GeniaSheet.`
- `lifecycle_repeat([], <sheet>, (sc)->1)` → `lifecycle_repeat expected a Seq-compatible value (list or Flow); received GeniaSheet.`

Neither rejection currently has a dedicated shared-spec or unit test (the neighboring
`collect_sheet("not-a-seq")` error case does); the claim rests on STATE text, the guard code
(`_seq_compatible_error`), and the probes above.

**Focused existing checks run** (all from `/home/user/genia-2026`):

| Command | Result |
|---|---|
| `uv run pytest -q tests/unit/test_sheet.py tests/unit/test_sheet_native_tests.py tests/spec/test_sheet_shared_specs_335.py tests/doc/test_sheet_truth_sync.py tests/spec/test_r18_surface_reconciliation_shared_specs_794.py` | 65 passed |
| `uv run pytest tests/doc -q -n auto` (run after writing this document) | 397 passed, 35 skipped |
| `uv run pytest -q tests/unit/test_lifecycle_repeat.py tests/unit/test_r14_repeated_record_lifecycle_proving_case_695.py tests/unit/test_flow_phase1.py tests/unit/test_validate_each.py tests/unit/test_sheet.py tests/unit/test_protected_sinks.py` | 165 passed |

These are partial evidence for the named areas only. No full regression, no C++ host build, and no
shared-spec-runner (R16) parity run was executed for this pre-flight.

---

## 3. Verified dependency / status table

Statuses were read from GitHub on 2026-10-25, not inferred from roadmap text.

| Item | Current status (verified) | Evidence | Blocks | Action required |
|---|---|---|---|---|
| [#1067](https://github.com/m0smith/genia-2026/issues/1067) Unified Function Model | **Closed (completed)** 2026-10-14, via PR #1231. F2/P2 landed via #1247. | issue; `sequence.md` "R20 unified-function follow-up" | Nothing | None. |
| [#1229](https://github.com/m0smith/genia-2026/issues/1229) F2/P2 closeout | **Closed** 2026-10-16 (PR #1248). | issue | Nothing | None. |
| [#1230](https://github.com/m0smith/genia-2026/issues/1230) / [PR #1254](https://github.com/m0smith/genia-2026/pull/1254) module-fallback gate | **Closed; PR merged** 2026-10-16T16:55:36Z. Fallback, strict switch, and `module_fallback.py` removed. Residual write-through of entry-declared runtime-owned names remains, tracked by #1257. | PR #1254 body; #1230 | Nothing (hard gate satisfied by removal). | None for R29. Note that absence of third-party reliance was never established (stated in the PR). |
| [#1249](https://github.com/m0smith/genia-2026/issues/1249) default-open / immutable-binding pre-flight + contract | **Issue still OPEN**, no comments. The contract it requested is **merged and maintainer-approved**: [PR #1255](https://github.com/m0smith/genia-2026/pull/1255) merged 2026-10-16T20:28:24Z; `docs/design/pre-r29-default-open-and-immutable-binding-contract-DRAFT.md` header reads "MAINTAINER-APPROVED SEMANTIC CONTRACT (2026-10-16) — NOT IMPLEMENTED" (the filename keeps DRAFT). The portable design is `…-design.md` ("CONDITIONAL GO ONLY"). | PR #1255; the two docs | Pre-flight: no. Contract approval of R29: no. Implementation: **the contract decision is made, but the issue's acceptance boxes are unchecked and the issue is not closed.** | Maintainer to tick/close #1249 or record that PR #1255 satisfies it. I did not close it. |
| [#1250](https://github.com/m0smith/genia-2026/issues/1250) implementation + tests | **OPEN**, 1 sub-issue. Slice A merged (PR #1260). Slice B (#1261) merged (PR #1262, merge `6d50a36`): `=:` immutable bindings executing in Python. **Slice C ([#1269](https://github.com/m0smith/genia-2026/issues/1269)) — default-open ordinary functions — is not merged**: draft [PR #1270](https://github.com/m0smith/genia-2026/pull/1270) (24 commits, 184 files, "TEST-only RED") with open decisions D1–D7 awaiting an independent GO. **Slices D (cross-module linking) and E (closed `f(...)=:`) have no issue or work.** C++ gap `immutable_bindings` recorded (#1261). | issue comments 2026-10-19/21; #1269; PR #1270; `spec/known_host_gaps.json` | Pre-flight: no. Contract: no. **Implementation: yes** (per `sequence.md`). | Do not interfere. Gate resolution is §11. |
| [#1251](https://github.com/m0smith/genia-2026/issues/1251) integration, audit, release-gate signoff | **OPEN, untouched** (no comments, no children). Its own acceptance allows "resolved dependency **or explicit maintainer-approved scoped exception**". | issue | **R29 language-facing implementation (explicit in `sequence.md`)**; release completion | Needs either the full A–E → signoff path or a recorded scoped exception (§11). |
| [#1192](https://github.com/m0smith/genia-2026/issues/1192) data-pipeline documentation debt | **OPEN**, work-package tracker, no comments, no children; policy delivered under #1101 (PR #1104). | issue; `sequence.md` debt table | Nothing; not an R29 dependency | Select one slice (§10); record at pre-flight and audit. |
| [#1101](https://github.com/m0smith/genia-2026/issues/1101) code-documentation standard | **OPEN** (reopened); CI ratchet delivered; MCP remediation and later slices unchecked. | issue | Nothing (legacy backlog explicitly non-blocking) | New/changed R29 bindings must meet the ratchet in their own change. |
| [#1236](https://github.com/m0smith/genia-2026/issues/1236) named pipeline composition | **OPEN**, contract gate only, non-blocking for R29. Coordinates with #1014 (Outcome bind) and #1208 (count). | issue; `sequence.md` | Nothing | R29 must not depend on or implement it (§4, N10). |
| [#1257](https://github.com/m0smith/genia-2026/issues/1257) runtime-owned-name write-through | Tracking only; separate P3 decision. | `sequence.md` | Nothing for R29 pre-flight | Carry as a risk (§7, R-8). |

### Discrepancies found

- **D-A. Roadmap text lags reality.** `sequence.md` and `release-roadmap.md` present
  `#1249 → #1250 → #1251` as a single pending gate. Actual state: the #1249 *contract* is approved and
  merged, #1250 is partly delivered (A, B merged; C in RED; D, E unstarted), #1251 untouched, and the
  #1249 issue itself is still open. The roadmap does not mention slices. Recommend a documentation-only
  roadmap refresh after maintainer review (not done here: roadmap edits belong with the approval).
- **D-B. No R29 planning issue.** Roadmap detail exists, but no issue; §13 recommends one umbrella issue
  after approval, not a batch.
- **D-C. Issue-number reuse.** Main commit `0e63dc1` ("feat(host): add empty vocabulary-only capability
  override…, issue #1269") references #1269 although #1269 is Model B Slice C and the surrounding
  lifecycle work is #1271. Traceability nit only; no action in R29.
- **D-D. Sheet family has no capability or gap record** (§8). The roadmap does not mention this.
- **D-E. Index base mismatch** between `lifecycle_repeat` `index` (1-based) and
  `collect_validated` `index` (0-based) (§6, D3).
- **D-F. The "Sheets are not Seq-compatible" claim is not directly tested** for `map`/`each`/`scan`/
  `reduce`/`lifecycle_repeat` (§9).

---

## 4. Proposed semantic boundaries

Capability-by-capability analysis. "Compose" = achievable with existing, unchanged mechanisms.
"Candidate" = would need a new public interface or runtime behavior and requires a contract decision.

### C1. Explicit Sheet-to-record conversion boundary — **the one new surface**

- *Already implemented:* `rows(sheet)` (pair-lists), `columns`, `row_get`; reverse path `collect_sheet`.
- *Compose today:* a user can convert pair-lists to maps by hand (`rows` + map-building), but the
  result depends on the user's key choices and there is no Sheet-aware contract.
- *Genuinely new:* one explicit boundary that returns **records as maps** in row order. **Candidate**
  (name not approved; `records` does not collide with an existing prelude/builtin name per a grep of
  `src/genia`): `records(sheet) -> List<Map>` — eager, total, no I/O, mirrors `rows`.
  A Flow is obtained by the existing explicit bridge (e.g. `lines(list)`, as in
  `examples/r14_repeated_record_lifecycle_proving_case.genia:115`). **No** Sheet-as-Seq compatibility.
- *Why eager List first:* a Sheet is already fully materialized and immutable, so laziness buys no
  extra demand semantics; bounded consumption and finalization come from the existing Flow bridge.
  Recommend deferring a dedicated lazy Sheet→Flow source unless the proving case demonstrates need.
- *Host:* Python only (§8). *Risk:* naming; key mapping (D1).
- *Acceptance:* `records(s) |> collect_sheet` round-trips (see D1 for key-type caveat); passing a
  non-Sheet fails with a marked `TypeError`; `map(f, s)` still fails.

### C2. Deterministic row and column ordering — **already implemented; needs evidence only**

Column order is construction order; row order is index order (`rows`, `render_csv`). Candidate:
`records` must emit rows in row order with map entries in Sheet column order. No new semantics.
*Gap:* ordering of map entries is observable only where Map ordering is portable (R17 ordered maps) —
confirm in contract. *Risk:* low.

### C3. Per-record processing context — **compose; one decision**

`lifecycle_repeat` already supplies `element` and `index`. Genia deliberately avoids `NR`/`NF`
syntax; E14-11 shows these are derived by application code. *Compose:* row number = `index`.
*Decision (D3):* 1-based vs 0-based consistency across `lifecycle_repeat`, `collect_validated`, and any
`records`-adjacent diagnostic. **Recommend:** do not add a second index API; document the existing bases
and let diagnostics use the base of the primitive that produced them. *Not new:* column index is not an
access path (STATE 2207–2220).

### C4. Flow demand, bounded consumption, finalization — **compose**

Already specified and tested (`take`, no over-pull, finalization on early close, E14-11 bounded case).
R29 adds only a proof that a Flow built from `records(sheet)` obeys the same rules (no new mechanism).

### C5. R14 repeated lifecycle scopes — **compose**

`lifecycle_repeat(peers, lines(records(s)), work)`. No change to `lifecycle_runtime.py`. *Hard
constraint:* the Python-only status of lifecycle (no C++ lifecycle scopes) caps cross-host evidence of
this item at Python (§8).

### C6. Ordinary `scan` / `reduce` for state — **compose**

Already specified. `scan` must not gain row-global semantics (non-goal N2). *Evidence gap:* no
Sheet-sourced `scan`/`reduce` example; C++ lacks list-form `scan` (STATE 134), so shared specs for
this item must use Flow-form `scan` or be `requires:`-gated.

### C7. Schema-preserving vs schema-changing — **classification, probably no new API**

Existing: `where`, `select` (reorder/project), and `derive` (append) over Sheets; `collect_sheet`
(strict, first-record schema) as the explicit schema-*defining* destination. **Recommend** that R29
only *classify* these in the contract (preserving: `where`; narrowing: `select`; extending:
`derive`; defining: `collect_sheet`) and add **no** union/padding/coercion variant. A heterogeneous
`collect_sheet` variant is **not** to be added unless the proving case proves a need, and then it is
deferred to R30/R31 shape work (N6, N7).

### C8. Existing `some` / `none` / `err` semantics — **compose**

Records flow through `validate_record`/`validate_each`/`collect_validated`; `collect_validated` is the
single Outcome-aggregating step, and `collect_sheet` receives its `clean` list (STATE 2465). Outcome
cells in a Sheet stay inert data. *Open (D4):* `keep_some_else` raises on `err` and `scan` has no Outcome
handling — R29 must not paper over this; Outcome `bind` is #1014, a separate gate.

### C9. Protected-value handling and non-leakage — **new evidence, no new mechanism**

Transport is already exact. Not yet tested at this boundary: protected cell identity through
`records`; `render_csv`/`json_encode` rejection after a round trip; Outcome diagnostic `context` not
echoing a protected field (note `validate_field` copies the raw `actual` into invalid-field context —
STATE 2387 — so redaction currently depends on display-time substitution); protected value as a column
name (map-key rule, STATE 391). These are R29 proof obligations, not new behavior (D5).

### C10. Shared `eval` / `flow` / `error` conformance evidence — **new evidence; host accounting required**

Existing Sheet shared specs live only under `spec/eval` and `spec/error`; `spec/flow` has none.
See §8–§9.

### Non-goals preserved (verbatim from the roadmap, none promoted)

N1 AWK `$0`/`$1`/`NR`/`NF` syntax · N2 mutable row globals · N3 implicit Sheet→Seq compatibility ·
N4 dataframe/query DSLs · N5 joins, grouping, windowing · N6 automatic coercion · N7 second Outcome,
Template, or validation model · N8 AWK execution mode · N9 anything in R30 (shape/rank, scalar lifting,
whole-column derivation) or R31 (grouping, ordering, joins) or R32 (provider sources/sinks, Sheet↔store)
· N10 named pipeline composition (#1236) and Outcome `bind` (#1014), `count` ergonomics (#1208) ·
N11 file/CSV/JSONL *readers into Sheets* (not in the roadmap's R29 scope; `parse_csv_row` is single-row
only) — flagged as an adjacent killer-workflow gap for the maintainer, **not** proposed for R29.

---

## 5. Architecture and compatibility analysis

**Smallest coherent R29:** one pure builtin in `src/genia/sheet.py`, registered next to the other Sheet
helpers in `src/genia/builtins.py` (host-registered `GeniaFunctionGroup`, not autoloaded — same pattern
as `rows`/`collect_sheet`), plus docs and evidence. **No** parser, AST, Core IR, evaluator, lifecycle,
or Flow-runtime change. A prelude (Genia-source) implementation is possible but **not recommended**: the
Model B default-open work (#1250) is changing how prelude/ordinary functions are defined and exported,
and a host builtin is independent of it.

- *Row materialization / column identity:* `GeniaSheet` is tuple-backed; names may be any legal map-key
  value. Map keys and Sheet names share the legal family and R18 equality (STATE 2207–2220), so a name→key
  mapping is total **except** for the `collect_sheet`/`sheet()` key-type asymmetry (strings vs symbols),
  which is decision D1.
- *Flow and cleanup:* nothing new — a list is never finalized (STATE 1792–1801); the Flow comes from the
  explicit bridge.
- *Validation pipelines:* `validate_each(records, validator) |> collect_validated |> clean |> collect_sheet`
  composes today after manual pair→map conversion; `records` removes only that conversion.
- *Core IR / portability:* none (§8).
- *Modules / function declaration:* R29 code must avoid constructs whose meaning the in-flight Model B
  work may change (open-by-default ordinary exports, noncontiguous or overlapping varargs clauses,
  alias-append). Proving-case Genia code should use plain single-clause or clearly distinct-arity
  functions and no `=:`. See §7 R-2.
- *Protected values:* transported unchanged; the only new obligations are tests (C9).
- *Host support/gaps:* Sheet: Python only. Lifecycle, protected values: Python only. Flow: Python + C++
  phase 1 subset. See §8.

---

## 6. Open architectural decisions and recommendations

None of these is approved language semantics.

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Record **shape and key mapping** of `records(sheet)` | (a) map keyed by the Sheet column name unchanged (symbols stay symbols); (b) coerce to strings to match `collect_sheet`; (c) support both via a parameter | **(a)**: no coercion (N6). Document that `collect_sheet` produces string keys from map literals while `sheet()` uses symbols, and that the round trip preserves key identity (symbol keys round-trip because `collect_sheet` uses raw keys). Verify this round trip in the contract with a worked example. |
| D2 | **Eager List vs lazy Flow** source | List only; Flow only; both | **List only**, Flow via the existing explicit bridge. Revisit only on evidence. |
| D3 | **Row-index base** | document as-is; add 0/1 helper; unify | **Document as-is**; no new index API; the proving case uses `lifecycle_repeat`'s 1-based `index`. |
| D4 | **Outcome items in the record stream** (`err` through `keep_some_else`/`scan`) | add handling; leave | **Leave**; use `validate_each` + `collect_validated`; log the `keep_some_else` `err` raise as a known limitation, owned by #1014/#1236, not R29. |
| D5 | **Protected-value redaction in diagnostics** | change `validate_field` context; test only | **Test only**; if the audit finds a leak, open a separate defect, don't widen R29. |
| D6 | **Duplicate/odd column names** | n/a | Not reachable: Sheet construction already rejects duplicates and non-map-key names. Contract states the invariant; no new error path expected. |
| D7 | **Sheet capability accounting** (see §8) | new `sheet_values` capability + issue-backed C++ gap; or declare existing Sheet specs ungated | **Add capability + gap before any new Sheet shared spec lands** (process-correct, and fixes D-D). |
| D8 | **Where the scope-exception question is decided** | wait for #1251; scoped exception | **Ask for a scoped exception limited to the builtin-only R29 surface** (§11), with a post-#1251 re-run of R29 evidence. |
| D9 | **Name** of the boundary function | `records`, `sheet_records`, `row_maps` | `records` is short and consistent with `rows`/`columns`; the contract phase must also check docs/lint category and the `@category` convention. Not decided here. |

---

## 7. PORTABILITY ANALYSIS (section 3a; seven required fields)

- **Portability zone:** *Portable language contract, Python-reference-host implementation.* Sheet is a
  language-contract value (`GENIA_STATE.md` marks "LANGUAGE CONTRACT" and "PYTHON REFERENCE HOST"
  separately); the R29 boundary function is a candidate portable observation (row-ordered records from a
  Sheet). Lifecycle (`lifecycle_repeat`) and protected values are portable *in contract* but Python-only
  *in implementation*, so R29's lifecycle and protected-value evidence is Python-host-only.
- **Core IR impact:** `none`. No `Ir*` node family changes; Sheet and builtins are runtime-only, and R14
  and the Flow helpers added no IR (STATE 1732, 3221). The wire format and `spec/manifest.json`
  `core_ir_contract` are unchanged.
- **Capability categories affected:** `flow_phase_1` (only as a consumer of an existing Flow);
  a **new capability name for Sheet values is proposed (D7)** because `spec/manifest.json` has none
  and Sheet is a genuinely independent host surface. `cli_pipe_mode` unaffected. No effect on
  `refs`, `cell_primitives`, `process_primitives`, `json_*`, `bytes_utf8`, `repl`.
- **Shared spec impact:** New R16 cases would be added under `spec/eval` (boundary, ordering, immutability,
  protected-cell identity), `spec/error` (non-Sheet input, Sheet-not-Seq rejection for `map`/`scan`/
  `reduce`/`lifecycle_repeat`), and `spec/flow` (bounded/finalized consumption of a Flow built from the
  boundary), all under a new `requires: sheet_values` gate (plus `flow_phase_1` where applicable).
  Cases are written in the TEST phase only; none are added now. Lifecycle composition cannot be a
  shared case until a host supports lifecycle; it stays a Python native/unit/CLI test.
  Executable semantic conformance obligation (`docs/architecture/executable-semantic-conformance.md`):
  (1) authority = STATE Sheet section after contract; (2) shared evidence = the cases above; (3)
  applicability via the existing capability vocabulary plus the D7 addition; (4) host claim impact =
  C++ stays "unsupported" for Sheet with an issue-backed gap; (5) implemented-truth docs to sync after
  verification = STATE, RULES, REPL README, README, book, cheatsheets.
- **Python reference host impact:** one new function in `src/genia/sheet.py` + registration in
  `builtins.py`; `@doc`/`@category` coverage and `tools/gen_function_docs.py` regeneration if it lands as
  a documented public function; maintained-code documentation ratchet applies to new bindings.
- **Host adapter impact:** none. No new host capability, transport, or adapter; the MCP launch path and
  `genia_run` profile are unchanged. (CLI/pipe-mode adapters unaffected.)
- **Future host impact:** C++ (`m0smith/genia-cpp`): no Sheet implementation exists (`sheet` and
  `collect_sheet` appear only in `src/genia2026_known_globals.hpp` as known-but-unimplemented). R29
  must record an **issue-backed temporary host gap** (`spec/known_host_gaps.json`: issue, reason, host,
  affected tests, removal condition) before merge; this also covers the existing, currently unrecorded
  Sheet family. Porting Sheet to C++ is **out of R29 scope** (it would need Sheet, Map key identity,
  lifecycle for item C5, and protected values). No other hosts are invented.

**MCP language-knowledge impact:** *Potentially affected after implementation, not now.* A new public
Sheet→record function and a documented "records are explicit, Sheets are not Seq" idiom are the kind of
knowledge `genia_language_profile` projects (the A9/A10 `pipelines`/`outcomes`/`flow` idioms already
exist). This pre-flight changes no STATE, registry, or MCP source. The implementation/docs phase must
update the `mcp_language_profile` registry in `docs/contract/semantic_facts.json`, regenerate
`apps/mcp/mcp.genia` with `tools/gen_mcp_language_profile.py`, and pass `--check`.

**Feature maturity:** Experimental (the Sheet family is Experimental throughout).

---

## 8. Host and conformance observations

- `spec/manifest.json`: `optional_capabilities` includes `flow_phase_1`, `cli_pipe_mode`, etc.; no
  Sheet, lifecycle, or protected-value capability.
- `spec/known_host_gaps.json` has 18 entries; none for Sheet, lifecycle (outside the HTTP gaps'
  reasons), or protected values.
- Existing Sheet shared specs (`spec/eval/collect-sheet-core.yaml`, `row-get-core.yaml`,
  `r18-surface-sheet-column-identity.yaml`, …, and `spec/error/error-collect-sheet-*`) therefore exist
  without a capability gate. I did not run the C++ host or R16 runner and cannot say from this
  environment how C++ classifies them; the contract phase must determine this before relying on it
  (D7). This is flagged as an open verification item, not asserted as a defect.

---

## 9. Risk register and mitigations

| ID | Risk | Likelihood / impact | Mitigation |
|---|---|---|---|
| R-1 | R29 starts before the Model B gate is satisfied, violating `sequence.md` | Med / High | §11 condition 1; contract/design/TEST only until resolved. |
| R-2 | Model B Slice C/D/E change default-open export or clause semantics under R29 Genia code (e.g. D1 varargs ambiguity, D5 alias-append in PR #1270) | Med / Med | Host-builtin implementation; proving code uses no `=:`, no overlapping varargs, no alias declarations; re-run R29 evidence after #1251. |
| R-3 | **Scope creep** into R30/R31 (columns-as-values, grouping) or into readers (CSV/JSONL → Sheet) | High / High | Non-goal list (§4) is part of the contract acceptance; each PR checks it. |
| R-4 | Silent Seq-compatibility creep (Sheet accepted by `map`/`each`) | Low / High | Add negative shared specs (D-F); contract states explicit-only. |
| R-5 | Key identity drift (symbols vs strings) breaking round-trip | Med / Med | D1 with worked round-trip example, tested. |
| R-6 | Overclaiming portability (C++ lacks Sheet, lifecycle, protected values) | High / Med | D7 capability + issue-backed gap; docs label every claim "Python reference host". |
| R-7 | Protected-value leakage via diagnostics (context copies raw `actual`) | Low / High | C9 tests; separate defect issue if found. |
| R-8 | Runtime-owned-name write-through (#1257) lets an entry program shadow `records`/`rows`-like builtins seen by modules | Low / Med | Documented residual risk; no R29 reliance. |
| R-9 | Documentation drift (STATE, semantic facts, MCP profile, cheatsheets, doc-sync tests) | Med / Med | §10 sync list; run `tests/doc`, cheatsheet and MCP profile checks. |
| R-10 | Large, high-conflict PRs (`builtins.py`, `GENIA_STATE.md`) | Med / Med | Small PRs; docs-slice and boundary kept separate (§11 decomposition). |

---

## 10. Documentation and technical debt disposition

**Authoritative documents impacted when behavior lands (not now):** `GENIA_STATE.md` (Sheet builtins
section, Sheet values limitations, new pipeline-idiom paragraph), `GENIA_RULES.md`,
`GENIA_REPL_README.md`, `README.md`, `docs/book/` Sheet chapter, `docs/cheatsheet/*` (with `[case:]`
markers and sidecar JSON), `docs/design/composability-matrix.md` (if the family derivation changes),
`docs/contract/semantic_facts.json` + `tests/doc/test_semantic_doc_sync.py` guards, the
`mcp_language_profile` registry and generated `apps/mcp/mcp.genia`, `docs/reference/**` generated
pages, `docs/strategy/roadmap/r25-r29.md` status, `docs/releases/R29.md`. None is edited by this
pre-flight; this document labels all new names as candidates.

**Selected #1192 slice (one narrow, coherent slice):**
`tests/native/sheet_helper_behavior.genia` — 9 baseline identities in
`.github/code-documentation-baseline.json`:

- `…::module::<module>`
- `…::binding::collect_sheet_builds_sheet_from_homogeneous_records`
- `…::binding::empty_sheet_has_zero_shape_columns_and_rows`
- `…::binding::render_csv_produces_deterministic_escaped_report_text`
- `…::binding::row_get_returns_named_cell_directly_and_inside_where_derive`
- `…::binding::sheet_derive_appends_outcome_cells_and_preserves_original`
- `…::binding::sheet_select_reorders_columns_and_preserves_original`
- `…::binding::sheet_shape_columns_and_rows_are_deterministic`
- `…::binding::sheet_where_filters_rows_and_preserves_original`

Rationale: it is the Sheet native test file R29 will extend, it is a single file, and it is docs-only.
Sequencing: land this **before** the R29 TEST phase so test additions do not conflict. Count of the
baseline at this snapshot: 2,798 total gaps (freshly computed from the checked-in JSON; not copied from
older comments). Acceptance (from #1192): exact identities removed, no baseline growth or weakened
checks, behavior unchanged, focused ratchet/lint tests pass. Owner: maintainer-assigned implementer under
#1192; PR evidence recorded on #1192 at pre-flight approval and at the R29 audit.

**Carry-forward, owned:** the remaining Flow/Seq/prelude identities in the #1192 package (e.g.
`src/genia/std/prelude/flow.genia` 19, `list.genia` 8, `awk.genia` 4, `tests/native/r3_validation_helpers.genia`
26, and others) stay open under #1192 with their baseline entries; the R29 audit names the next slice
(candidate: `src/genia/std/prelude/awk.genia`, 4 identities). Unrelated legacy debt does not block R29.

---

## 11. Proposed release decomposition and conditions to begin implementation

Phases are separate, per `AGENTS.md` prompt discipline; each stops for review. **No implementation
tickets are created by this pre-flight.**

```text
R29-D0 docs slice (#1192)  ──────────────┐   (independent, parallel, before R29-T)
                                          │
R29-C  contract  ──► R29-G  design ──► R29-T  failing tests ──► R29-I  implementation
   (D1–D9 decided)      │                       │ (shared specs + Python tests)        │
                        │                       └── needs: D7 capability + C++ gap     ▼
                        └─(optional)                                  R29-P  proving case
                                                                          │
                                                                          ▼
                                                  R29-X docs sync ─► R29-A audit ─► R29-Z distillation
```

| Item | Purpose / boundary | Depends on | Contract decisions | Failing tests (TEST phase) | Implementation scope | Docs | Acceptance | Non-goals | Complexity / risk |
|---|---|---|---|---|---|---|---|---|---|
| **R29-D0** | #1192 docs-only slice (§10) | none | none | none (existing ratchet) | docs metadata in one native-test file | none | 9 identities removed, no baseline growth | any behavior change | XS / low |
| **R29-C** | Contract: boundary, key mapping, ordering, index doc, Outcome/protected rules, host accounting | this pre-flight approved | D1–D9 | none (contract defines no tests) | none | `docs/design/r29-sheet-record-pipelines-contract.md` marked PROPOSED | every candidate decision has an approved/rejected outcome | everything in N1–N11 | S / med (naming, D7) |
| **R29-G** | Design: function placement, registration, doc generation, capability/gap record | R29-C | none new | none | none | `docs/design/…-design.md` | maps each contract clause to a file and a test | | XS / low |
| **R29-T** | Failing tests committed first | R29-G; D7 capability decided | none | **Shared:** `spec/eval` (records order, immutability, empty sheet, round-trip, protected-cell identity); `spec/error` (non-Sheet; `map/each/scan/reduce/lifecycle_repeat` over Sheet still rejected); `spec/flow` (bounded + finalized Flow from boundary). **Python:** protected sinks after round trip, diagnostic non-leak, ordering/index docs, 1-vs-0 base pin. | none | manifest capability + `known_host_gaps.json` entry (with issue) | tests fail for the right reason, recorded SHA | | S / med (shared-runner accounting) |
| **R29-I** | Minimal implementation of the boundary | R29-T; **gate §11 cond. 1** | none | makes R29-T pass | `sheet.py` + `builtins.py` registration; `@doc`/`@category` | generated reference only | all R29-T green; no unrelated regression | any Flow/lifecycle/parser change | S / med |
| **R29-P** | Proving case: Sheet → `records` → `lines` → `lifecycle_repeat` (per-record context) → `scan`/`reduce` state → `validate_each` → `collect_validated` → `collect_sheet` → `render_csv` | R29-I | none | CLI shared spec + native test; protected non-leakage; bounded termination cleanup | **zero runtime change expected** | example + cheatsheet case | one validated pipeline end to end, diagnostics visible, exact stdout/stderr | AWK syntax; new helpers | S / low–med |
| **R29-X** | Docs sync (STATE, RULES, REPL README, README, book, cheatsheets, semantic facts, MCP profile, release notes) | R29-I, R29-P | none | doc-sync and cheatsheet tests | none | listed in §10 | docs describe only verified behavior | | M / **high drift** — keep PR small |
| **R29-A** | Independent skeptical audit | R29-X | none | none | repair PRs only for findings | | truth audit PASS; #1192 slice evidence recorded; next debt slice named | | S / low |
| **R29-Z** | Distillation | R29-A | none | none | none | | | | XS |

**Parallelism after contract approval:** R29-D0 (anytime); R29-G and the C++ gap/capability record
preparation in parallel; within TEST, the shared-spec set and the Python-only test set can be split across
two PRs if they touch different files; R29-X can start per surface (cheatsheets / semantic facts / MCP
profile) once R29-P is merged. Avoid concurrent edits to `GENIA_STATE.md` and `builtins.py`.

### Conditions to begin implementation (R29-I)

1. **Model B gate:** either (a) #1250 Slices C–E and #1251 signoff are complete, or (b) the maintainer
   records on #1251 an **explicit scoped exception** limited to the builtin-only R29 surface, with a
   commitment to re-run R29 evidence after #1251. (Neither exists today.)
2. R29-C contract decisions D1–D9 approved by the maintainer.
3. R29-T failing tests committed (SHA recorded) including the D7 capability and issue-backed C++ gap.
4. The #1192 slice (R29-D0) merged or explicitly deferred with an owner.
5. Contract, design and tests contain no R30/R31/R32 behavior, and the non-goal list is unchanged.

Conditions 2–5 do not block the contract/design/TEST phases; only condition 1 gates implementation.

---

## 12. Acceptance criteria and testing strategy (summary)

- Observable, shared-spec-first: ordering, immutability, empty Sheet, round-trip key identity, negative
  Seq rejection, bounded/finalized Flow from the boundary, error text for non-Sheet input (stable
  diagnostics, no Python class names).
- Python-only (declared in module docstrings): lifecycle composition, protected-value non-leakage through
  sinks, adapter/MCP profile checks.
- Native Genia test for user-facing behavior alongside the shared specs.
- Honest coverage claims: no "complete coverage"/"fully aligned" phrasing; C++ marked unsupported.
- Regression: focused suites above plus `uv run pytest -n auto -q -m "not loopback"` and
  `-m loopback`; `tools/gen_function_docs.py --check`, `tools/lint_doc.py --require-coverage`,
  `tests/doc`, cheatsheet tests, `tools/gen_mcp_language_profile.py --check`.

---

## 13. Recommended next action

**Maintainer review of this pre-flight.** The single action that most efficiently advances R29 is for
the maintainer to answer one question on #1251: *may R29 proceed to implementation under a scoped,
builtin-only exception, or must it wait for #1250 Slices C–E?* The answer determines whether R29-C
(contract) can run in parallel with Model B (recommended) or must queue behind it. Pending that, the
risk-free parallel work is R29-D0 (documentation slice).

Per `AGENTS.md`, work stops here: no contract, TEST, or implementation phase begins, and no
prerequisite issue is closed or modified by this document.

### Issue handling

No R29 umbrella issue exists, so none is duplicated. After approval, recommend creating **one**
R29 umbrella issue linking this document and #1249/#1250/#1251/#1192/#1236, with child issues created per
phase on demand rather than as a batch.

### Appendix — evidence links

- Roadmap: `docs/strategy/roadmap/r25-r29.md`, `sequence.md`, `release-roadmap.md`, `killer-workflow.md`
- Contract/design: `docs/design/pre-r29-default-open-and-immutable-binding-contract-DRAFT.md`, `…-design.md`
- PRs: [#1254](https://github.com/m0smith/genia-2026/pull/1254), [#1255](https://github.com/m0smith/genia-2026/pull/1255),
  [#1262](https://github.com/m0smith/genia-2026/pull/1262), [#1270](https://github.com/m0smith/genia-2026/pull/1270)
- Issues: #1067, #1101, #1192, #1229, #1230, #1236, #1249, #1250, #1251, #1257, #1261, #1269
- Code: `src/genia/sheet.py`, `src/genia/builtins.py:2518,3145,6132-6145`,
  `src/genia/lifecycle_runtime.py`, `src/genia/std/prelude/awk.genia`
- Tests/spec: `tests/unit/test_sheet.py`, `tests/spec/test_sheet_shared_specs_335.py`,
  `tests/unit/test_r14_repeated_record_lifecycle_proving_case_695.py`, `spec/eval/collect-sheet-core.yaml`,
  `spec/manifest.json`, `spec/known_host_gaps.json`
