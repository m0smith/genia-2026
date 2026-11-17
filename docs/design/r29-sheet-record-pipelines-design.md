# R29 — Sheet Record Pipelines: implementation design

**Status: PROPOSED R29-G DESIGN — NOT IMPLEMENTED; independent review pending.** This design operationalizes the **maintainer-accepted R29-C contract at exact commit `575f09d5424b75a29791fb55177d41515a042dd1`**, as recorded on [#1328](https://github.com/m0smith/genia-2026/issues/1328#issuecomment-6961850153), after [Claude's independent PASS](https://github.com/m0smith/genia-2026/issues/1328#issuecomment-6961799141). The contract remains an unimplemented planning artifact; `GENIA_STATE.md` is the current-behavior authority. A subsequent change to the contract invalidates this design baseline pending fresh contract acceptance. This file defines no new Genia semantics.

**PR shape:** add this design as a separate `design(r29)` commit to the **existing draft PR #1329** on `issue-1328-r29-sheet-record-contract`. Keep separate contract, RED test, GREEN implementation and docs/audit commits; never erase the original RED commit history by squash/rebase-merge. Use #1328 top-level comments for accepted handoffs and review at exact SHAs.

## 1. Smallest implementation and API mapping

The single additional exported Genia callable is **`sheet_records/1`**. It is a pure eager `Sheet -> List<Map>`; no Flow or Seq adaptation of Sheet occurs. It must retain raw Sheet column keys (Genia map-key identity and insertion order), existing cell references including protected carriers and Outcomes, original row order and immutability. For zero-row Sheets return `[]`, with accepted zero-row column-schema loss; for `r` rows and zero columns return `r` distinct empty Maps. Reject a non-Sheet value with marked `TypeError("sheet_records expected a Sheet")`. Do not add any index field, new key normalization, schema wrapper, extra builtin, callback, or resource.

| Planned path / phase | Minimal change and exact rationale |
|---|---|
| `src/genia/sheet.py` — GREEN | One pure `sheet_records` helper using existing `_ensure_sheet`, `GeniaSheet.columns`/`row_count` and the existing `GeniaMap` construction/conventions. Preserve canonical key identity and per-row order; avoid route through rendering/CSV, `rows` pair-lists, or Flow. Do not change existing Sheet helpers. |
| `src/genia/builtins.py` — GREEN | Import and register exactly one `GeniaFunctionGroup` arity-1 global `sheet_records` with existing `runtime-public` handling, matching `rows`, `collect_sheet` and `render_csv`; no changes to evaluator, name ownership, module linker, or parser. |
| `src/genia/host_builtin_docs.py` — GREEN/docs | One public Experimental Sheets entry, with truthful summary, correct signature and generated metadata (`help`/`doc`/`meta`, `@doc`/`@category`); follow existing metadata ratchet. |
| `hosts/python/mcp_worker_profile.py` — GREEN | Add the pure name **`sheet_records` to `ALLOWED_BINDINGS`**; preserve the default-deny classification, authority blacklist, AST deny logic and MCP transport contract. Do not add to denied/privileged source classes. |
| `tests/data/p1_host_binding_inventory.json` — GREEN | Add exactly `"sheet_records": "runtime-public"` under `bindings` when the builtin is registered. The exact-inventory invariant in `tests/unit/test_host_binding_classification_p1_e.py` (the `set(env.values)` and `host_binding_visibility` equality checks) would otherwise fail. Keep all other binding, internal and autoload classifications unchanged. |
| `docs/contract/semantic_facts.json`, `apps/mcp/mcp.genia` — DOCS, after GREEN | Add the smallest Sheet/explicit-record-boundary language-profile fact/idiom grounded in newly verified STATE anchor, regenerate via `tools/gen_mcp_language_profile.py`. Do not change MCP tool count, resources, prompts or schema. |

A design/implementation review must verify which `GeniaMap` constructor/interface preserves insertion order and legal composite keys **before** the helper is coded. If existing Map APIs cannot satisfy the approved key-identity contract, **STOP** and return to contract review; do not introduce a new Map type, alter equality or use Python `dict` key semantics to force a pass.

Normal callable alias, higher-order, pipeline and module use are inherited from existing builtin registration. Test the explicit entry-scope `sheet_records =: 5` immutable-name rejection and ordinary shadowing behavior; do not alter Model B.

## 2. Conformance accounting: one truthful capability

**Capability name: `sheet_values`** (approved D7). Use **the existing** `spec/manifest.json` `optional_capabilities`, `requires:` field, `spec/known_host_gaps.json`, the R16 runner, and existing capability matrix/parity gate. No new runner, registry or conformance taxonomy.

**R29-T0 sequence** — first create and verify a **real GitHub issue** for the C++ Sheet capability gap, with host `cpp`, affected case family, reason and removal condition; then:
- add `sheet_values` to manifest optional capabilities;
- add `requires: [sheet_values]` to exactly the **19 pre-existing Sheet-only cases** listed below (this count excludes new R29-T1 cases);
- record the `cpp` gap and case list in `spec/known_host_gaps.json`, linked to the actual gap issue; its `affected_tests` must include **all 19 retro-gated cases plus every newly introduced Sheet-boundary shared case**, including `spec/flow` cases;
- record Python before/after count and identity of passing cases, and C++ adapter-reported versus capability-excluded unsupported classification; Python automatically self-reports manifest capabilities as supported, so **tests**, not a claim, are the evidence;
- run existing host-parity, spec-adapter and manifest/capability checks; treat new or missing support as findings, never skips or artificial passes.

Existing **10 Sheet-only eval cases**:
`spec/eval/collect-sheet-core.yaml`,
`spec/eval/render-csv-core.yaml`,
`spec/eval/row-get-core.yaml`,
`spec/eval/sheet-derive-core.yaml`,
`spec/eval/sheet-empty-core.yaml`,
`spec/eval/sheet-select-immutable.yaml`,
`spec/eval/sheet-shape-columns-rows.yaml`,
`spec/eval/sheet-where-core.yaml`,
`spec/eval/r18-surface-sheet-column-identity.yaml`,
`spec/eval/r18-conformance-sheet-structural-equality.yaml`.

Existing **9 Sheet-only error cases**:
`spec/error/error-collect-sheet-missing-column.yaml`,
`spec/error/error-collect-sheet-not-seq.yaml`,
`spec/error/error-render-csv-not-sheet.yaml`,
`spec/error/error-render-csv-unsupported-cell.yaml`,
`spec/error/error-row-get-missing-column.yaml`,
`spec/error/error-row-get-not-row.yaml`,
`spec/error/error-sheet-derive-duplicate-column.yaml`,
`spec/error/error-sheet-select-missing-column.yaml`,
`spec/error/error-sheet-unequal-column-lengths.yaml`.

**R18 mixed-family case:** `spec/eval/r18-conformance-cross-family-summary.yaml` is **not** a Sheet-only case. Before removing its Sheet equality pair at vector positions 16–17, move its unique same-cells renamed-column inequality (`"c"` versus `"d"`, expected `false`) into `r18-conformance-sheet-structural-equality.yaml` in the **same TEST change**. Confirm the remaining ten families retain all observations and update expected vector 22→20, description/`families` note, `docs/host-interop/HOST_PORTING_GUIDE.md`, `docs/releases/R18.md`, and `tests/spec/test_r18_conformance_protocol_evidence_795.py`. Require review by maintainer (`m0smith`, R18 #789/#795) or delegated independent R18 equality reviewer on #1328. Do not mark the mixed case `requires: [sheet_values]` or delete the whole case.

**New R29-T1 shared-case applicability:** Every new `spec/eval/*`, `spec/error/*`, or `spec/flow/*` case that calls `sheet_records` or otherwise depends on the new Sheet boundary MUST carry `requires: [sheet_values]` **from its first TEST commit**. Any such Flow case must additionally carry `requires: [flow_phase_1, sheet_values]` (the manifest's existing Flow capability and the new Sheet capability). Verify each YAML's `requires` with the existing spec loader, and include the complete new-case paths in the `known_host_gaps.json` `affected_tests` list. This is in addition to, not part of, the 19 pre-existing cases; it prevents ungated C++ failures without claiming C++ Sheet support. The R18 mixed-family aggregate remains ungated by `sheet_values`.

**Cross-repo follow-up:** `genia-cpp` lacks Sheet; after truthful T0 accounting, a separate repository PR may re-pin its contract/evidence. It must not implement Sheet in C++ during R29. The issue-backed known gap is not waived; no fictitious parity claim.

## 3. R29-T test placement and RED/PASS distinction

R29-T is an independently authorized **TEST phase**; no test/spec edits in this DESIGN phase. A separate committed test SHA must be observed **RED before GREEN**, and the implementation phase must cite that exact SHA. Preserve the failed output and the passing existing-composition cases separately; a previously passing test must never be called an expected RED.

| Category | Test locations / assertions |
|---|---|
| **T1, expected RED** | New shared `spec/eval/*` cases for row and key order/type identity, immutability, alias/higher-order/pipe, zero-row/zero-column, conditional round trip, distinct row Maps, Outcome as cell data. New `spec/error/*` for non-Sheet and arity misuse. Shared `spec/flow/*` for separately application-constructed Flow and bounded downstream consumption; **do not** misrepresent `sheet_records` as lazy. **All new Sheet-boundary cases require `[sheet_values]` from creation; new Flow cases require `[flow_phase_1, sheet_values]`.** Include each in the C++ known-gap affected-test inventory. |
| **T1 host-specific, expected RED** | Focused Python `tests/unit/` and/or `tests/native/` cases for protected carrier exact transport, sink and diagnostic non-leakage, MCP worker default-deny allowance, public docs/metadata, runtime-owned-name reservation, module visibility and existing function semantics; locate existing adjacent suites before adding files. In `tests/unit/test_host_binding_classification_p1_e.py` (or a focused adjacent test), assert that `sheet_records` is present in `make_global_env([])` with `runtime-public` visibility **and** is listed as `runtime-public` in `tests/data/p1_host_binding_inventory.json`: both new assertions are expected RED before GREEN registration/inventory update. Preserve the pre-existing exact-inventory test and its original PASS baseline. |
| **T1 proving-case, expected RED** | Add one executable Genia proving case in the existing examples/spec/native-test convention: Sheet → `sheet_records` → ordinary filter/map/validation with Outcome diagnostics → explicit `collect_sheet` and/or report. Keep any optional R14 `lifecycle_repeat` envelope exercise in **Python-host-specific** `tests/native` or `tests/unit`, not shared specs; do not treat envelopes as callback values. Provide an observed runnable expected result; no new reader, DSL, kernel, or Flow bridge. |
| **T2, expected PASS without `sheet_records`** | Shared/native/Python guards that Sheets remain non-Seq to `map`, `each`, `scan`, `reduce`, `lifecycle_repeat`; existing List→Flow application composition works on empty/nonempty/bounded/single-use; lifecycle success/failure envelopes; hand-conversion Round Trips G1–G6; protected sinks/diagnostics. Failure here is an actual finding, **not** RED evidence. |
| **T3, after #1251** | At post-integration gate, rerun T1+T2 and Model B name-resolution, `=:` reservation, module visibility, aliases and open-by-default interaction. Also run complete Python regression with SHA, commands, results and host pins. |

**Evidence must be executable where possible:** shared portable observable semantics reside in `spec/`; Python-only lifecycle/protection/security wiring tests clearly identify their host limitation. Do not claim cross-host proof from Python-only tests. The pre-flight's earlier scratch probes are not committed RED.

## 4. Implementation safety and independent review

**R29-I is prohibited until:** (a) maintainer-accepted contract SHA and accepted R29-G design; (b) T0 host gap and T1 committed/observed RED SHA; (c) #1251 signoff **or** an explicit narrowly scoped maintainer exception actually **posted on #1251**, naming contract and RED; (d) no new semantics or out-of-scope dependencies. The current #1251 issue being open is **not** such an exception.

GREEN should be strictly limited to the **five runtime/registration/policy/inventory paths in §1** (`sheet.py`, `builtins.py`, `host_builtin_docs.py`, `mcp_worker_profile.py`, `p1_host_binding_inventory.json`) and minimum first-class metadata. Verify that the existing `GeniaMap` import/constructor path in `sheet.py` does not introduce a circular import before coding; STOP if the approved semantics cannot be implemented with existing interfaces. The pure helper must never decrypt/print protected values, allocate lazy futures, coerce names/values, introduce a second conversion function, or add Flow/Model B rules. An inability to fulfill the contract using the existing Map/API is a **STOP**, not a mandate to rewrite the runtime.

Use `docs/process/code-maintainability-review.md` independently on the actual implementation diff before docs for the full high-risk lifecycle. Then update only applicable implemented-truth surfaces after passing behavior: `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, docs/book, cheatsheets/tests, host capability registry/matrix, generated function references, `docs/contract/semantic_facts.json` MCP registry and generated MCP file, `docs/strategy/roadmap/r25-r29.md` status, and release page. Run generated-doc checks, code-doc ratchet and `uv run pytest` coverage as required. Include the existing `tests/doc/test_sheet_truth_sync.py` in documentation truth checks and update `.github/code-documentation-baseline.json` only as required by the existing maintained-code documentation ratchet. Extend the existing S-series cases in `tests/unit/test_r28_mcp_conformance_security.py` (verify its actual path before editing) for the new pure binding rather than creating a competing security test suite. Independent truth/scope audit then distillation, with full parity and release acceptance when applicable. If a maintainer explicitly authorizes a bounded RED→GREEN→docs slice under `AGENTS.md`, combine its *end-of-slice* independent maintainability/truth review only as that policy permits; do not collapse evidence or skip a release audit.

No separate R29 phase PRs. Only a genuinely different repository (`genia-cpp`) needs its own PR.

## 5. Scope Compliance — design phase and future handoffs

**Locked:** merged #1284 pre-flight, #1328 accepted decisions and handoffs, contract **`575f09d5424b75a29791fb55177d41515a042dd1`**, this design at its eventual reviewed/accepted SHA. No new language semantics beyond `sheet_records/1`.

| Clause / obligation | Proposed paths | Scope restriction |
|---|---|---|
| Contract §§1–2, D1/D6/D9 | `src/genia/sheet.py`, `src/genia/builtins.py`, `src/genia/host_builtin_docs.py`, `tests/data/p1_host_binding_inventory.json`, `tests/unit/test_host_binding_classification_p1_e.py` | one pure function + registration/docs and its exact runtime-public inventory; new failing visibility/inventory assertions in RED, inventory update in GREEN |
| Contract §3 | Shared `spec/flow` with `requires: [flow_phase_1, sheet_values]`, bounded native tests | no Flow kernel or builtin; new shared Sheet-boundary cases gated from creation |
| Contract §4 | `spec/eval`, `tests/native` or `tests/unit` | no new Outcome/lifecycle semantics |
| Contract §5 | host-specific security tests | no leakage, sink or declassification changes |
| Contract §6 D7/D10 | manifest, **19 existing** Sheet-only specs, **all new** Sheet-boundary `spec/eval`, `spec/error`, `spec/flow` cases, mixed R18 case + named references, C++ gap registry/affected-test inventory, host matrix | all new cases require `sheet_values` (Flow also `flow_phase_1`); truthful applicability; no hidden families, no C++ implementation |
| Contract §6 D11 | Python MCP profile (GREEN), semantic-facts/MCP generator outputs (DOCS) | preserve default-deny and adapter contract |
| Contract §§8–9 | #1328 handoffs, #1329 commits and release/audit evidence | no implicit approvals or merge |

**Hard STOP:** unexpected required files outside the justified map; parser/AST/Core IR/evaluator; Map equality semantics; Flow kernel; lifecycle runtime; Model B ownership/immutability/module linker; implicit Sheet→Seq; a second List→Flow builtin; CSV/JSONL readers, joins/grouping, R30–R32, C++ Sheet implementation, or unrelated #1192 cleanup. Such a discovery goes back to maintainer/contract approval, not a spontaneous implementation extension.

**Design-phase compliance record:** proposed changed path is only `docs/design/r29-sheet-record-pipelines-design.md`; no tests, code, manifest, generated files or current-behavior docs modified. Evidence at design commit SHA on #1328 must include actual changed files and any exceptions. A second independent agent must inspect the design's file/contract mapping and approve or require revisions. **R29-T remains blocked until design review and accepted handoff.**

---

**R29-G approval ledger:** PENDING independent design review and an accepted, exact-SHA handoff on #1328. This design does **not** authorize writing tests, running RED, beginning GREEN, granting #1251 exception, changing the contract, or merging PR #1329.
