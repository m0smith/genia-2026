# R29 — Sheet Record Pipelines Contract

**Status: PROPOSED R29-C CONTRACT — NOT YET APPROVED; NOT IMPLEMENTED BY THIS DOCUMENT.** This is a candidate portable language contract for maintainer semantic approval and independent review. `GENIA_STATE.md` is the final authority for **currently implemented** behavior; do not treat the proposed `sheet_records/1` function as available until implemented, verified, merged, and documented there.

**Scope baseline:** [R29 umbrella #1328](https://github.com/m0smith/genia-2026/issues/1328), merged [pre-flight PR #1284](https://github.com/m0smith/genia-2026/pull/1284) and `docs/analysis/r29-sheet-record-pipelines-preflight.md` revision 4 (§§4–6, 9, 12–13), `docs/strategy/roadmap/r25-r29.md`, and `docs/strategy/killer-workflow.md`. This contract resolves pre-flight candidate decisions D1–D11 *as proposals*, not as implemented facts. Contract approval is a separate gate.

## 1. Purpose and single new boundary

R29 adds **one explicit, pure, eager Sheet-to-record conversion** for existing Outcome-aware validated-data-pipeline composition:

- **Proposed public name:** `sheet_records/1`. The ordinary call `sheet_records(sheet_value)` returns a Genia `List` of Genia `Map` records. It also supports ordinary alias, higher-order, and `|>` call behavior; there is no special syntax.
- **Input:** exactly one existing immutable Sheet value. Any other input is programmer misuse: a Sheet-style, pipeline-preserved `TypeError("sheet_records expected a Sheet")`. Other arity errors use existing function-call semantics.
- **Output:** exactly one new eagerly materialized List; each element is a new Map describing one row. The List contains no header, schema wrapper, synthetic row marker, or index field.
- **Purity and ownership:** conversion has no callbacks, filesystem/network access, stdout/stderr, mutation, Outcome evaluation, or hidden resources. It preserves the original Sheet and retains each exact column-name and cell value (including Outcome and protected-value carriers) without type conversion, coercion, unwrapping, copying of protected payloads, or declassification. It creates structural List/Map storage; it does not promise host-object identity for new containers.

This is deliberately the converse *data boundary* of existing `collect_sheet(records)`, not a new collection abstraction or general-purpose iterable conversion.

## 2. Ordering, shape, and exact-value semantics

For a well-formed Sheet with `r` rows and ordered column names `[c1, ..., ck]`:

1. The returned List has exactly `r` Maps in original Sheet row order.
2. Each Map has exactly `k` entries, with keys in original Sheet column order `c1, ..., ck` and values from that row's corresponding cells.
3. Keys are the exact Genia column-name values, not display text; no string/symbol normalization, numeric conversion, or reinterpretation of legal map-key equality is permitted. Existing Sheet legality and uniqueness rules are inherited without adding a second validation/error vocabulary.
4. Rows are structurally independent Maps. No field is added to supply a row index, metadata, implicit schema or validation status.
5. Cells that contain `some(...)`, `none(...)`, or `err(...)` remain **ordinary cell values**. The conversion never short-circuits, projects or aggregates them.

**Edge cases and limits:**

- A Sheet with **zero rows** converts to `[]` even when columns exist. This List cannot carry column schema, so `collect_sheet(sheet_records(s)) == s` is **not a general guarantee** for a zero-row Sheet with nonzero columns; callers must separately retain `columns(s)` if they need the schema.
- A Sheet with **zero columns and `r > 0` rows** converts to a List of `r` empty Maps. It preserves the row count; current `collect_sheet` behavior reconstructs that zero-column Sheet.
- A zero-row, zero-column Sheet converts to `[]`.
- For nonempty Sheets whose record Maps are preserved unchanged, `collect_sheet(sheet_records(s))` respects existing `collect_sheet` column/key identity, row count, and cell-value rules. It is not a promise about modified/heterogeneous records, additional map-key types not admitted by Sheet, or empty-row schema.
- Existing `sheet` construction rejects duplicate/illegal column keys. This conversion consumes only already-valid Sheet values; there is **no new duplicate-name resolution** and no new repair or normalization behavior.

## 3. Eagerness and existing composition

`sheet_records/1` materializes *every* record Map **before** returning. Its structural allocation scales with the number of rows and columns. Applying `take(n)` **after conversion** cannot reduce this allocation.

The resulting List is reusable and follows existing List operations; it is **not** a Flow, streaming source, or Seq-compatible Sheet adapter. A consumer may explicitly construct a single-use Flow from its List using existing application-owned composition (`evolve`, `take`, `map`, `nth`, `unwrap_or`). Downstream Flow pull/bounding/finalization semantics remain exactly as implemented. In particular, `lines` is **not** a List-of-Maps-to-Flow bridge: it requires a List of strings. No new List-to-Flow function is authorized.

Existing `map`, `filter`, `reduce`, `scan`, `validate_each`, `collect_validated`, `collect_sheet`, `where`, `select`, and `derive` retain their own contracts and input restrictions. R29 changes only the Sheet-to-List-of-Maps boundary. Existing schema-changing operations remain explicit; there is no column union, padding, implicit key coercion, or query/aggregation DSL.

## 4. Outcome and lifecycle separation

- Data-level Outcomes are governed only by existing `some/none/err`, `validate_each`, `validate_record`, and `collect_validated` behavior. To collect validated rows into a Sheet, consumers explicitly pass the existing `collect_validated(...).clean` list to `collect_sheet`; this operation adds no new validation shortcut.
- `lifecycle_repeat` may consume a separately constructed Flow of records. Its result remains a **lifecycle result envelope**, not the callback value. Consumers must check `status` and inspect `primary_failure`/`cleanup_failures` on lifecycle failure before reading `result`. An `err(...)` returned by an otherwise successful callback remains data-level Outcome inside the successful envelope; it is not a lifecycle failure.
- No new index API is introduced. Existing `lifecycle_repeat` element context is 1-based and existing `collect_validated` diagnostic `index` is 0-based. Neither changes here.
- `lifecycle_repeat` remains Python-host-specific; the R29 contract does **not** imply that a C++ runtime implements it.

## 5. Protected data and diagnostic boundary

This conversion transports existing protected cell values as opaque values, never exposes their payloads, and grants no declassification authority. Existing rejection/redaction rules for `print`, `display`, `debug_repr`, `json_encode`, `render_csv`, validation diagnostics and output sinks remain binding; no new sink or special diagnostic renderer is introduced. The existing rule that declassification authority cannot be stored in a Sheet is unchanged.

**Fail-closed release condition:** if a supported R29 path leaks protected data, that path is **blocked** until fixed with verifiable evidence or removed from the supported claim. Merely opening a defect issue, hiding output, or downgrading the feature's maturity does not make it acceptable.

## 6. Host portability, capability and MCP contract impact

**Portability classification:** portable observable language behavior, **Python-reference-host implementation only in R29**. The new function is an ordinary global arity-1 builtin, not a parser construct, Core IR node, new host transport, or C++ feature. Its initial maturity, once implemented, is **Experimental**, consistent with existing Sheets.

**Capability decision (D7):** the existing Sheet family and this boundary belong under proposed optional manifest capability **`sheet_values`**. Existing Sheet-only shared cases should be capability-gated alongside new Sheet-boundary cases; Python continues to claim support only as verified. C++ is not to claim `sheet_values` until implemented. The conformance gap must have a **real tracking issue**, host, affected cases and removal condition before any `spec/known_host_gaps.json` entry is committed. Reclassifying cases must not reduce Python's previously passing evidence or conceal C++'s unsupported status.

**Mixed R18 family decision (D10):** during the TEST/conformance-accounting phase, remove the duplicated Sheet equality pair from `r18-conformance-cross-family-summary` while retaining the other ten families, preserving their oracle, and relying on the dedicated R18 Sheet structural-equality and column-identity cases for Sheet claims. Update references to the aggregate and obtain **R18-owner independent review** before accepting that edit. Do not gate the whole mixed aggregate on `sheet_values`: this would hide unrelated equality evidence. Do not make that edit during this CONTRACT phase.

**MCP execution-policy decision (D11):** classify `sheet_records` explicitly as an **allowed pure binding** within the existing default-deny Python MCP worker policy, since it introduces no authority or I/O. Its classification must not weaken forbidden-source inspection, allow secret/config/declassification access, or add tools/resources/prompts. After verified implementation, the MCP language profile must accurately say that conversion is explicit and Sheets are not Seq-compatible, via `GENIA_STATE.md`, the guarded `mcp_language_profile` registry, and regenerated `apps/mcp/mcp.genia`. No MCP or implemented-truth file changes during contract drafting.

## 7. Pre-flight decision resolution (proposed, D1–D11)

| ID | Proposed disposition | Contract section |
|---|---|---|
| D1 | Ordered List of Maps with unchanged legal Sheet column keys and cell values | §2 |
| D2 | Eager List only; no lazy boundary or List→Flow builtin | §§1, 3 |
| D3 | Existing 1-based lifecycle and 0-based validation indexing; no new index | §4 |
| D4 | Outcome cells are data; existing validation and collection only | §§2, 4 |
| D5 | Protected diagnostic paths fail closed; no leakage waiver | §5 |
| D6 | Inherit Sheet name uniqueness and map-key legality; no new repairs | §2 |
| D7 | Optional `sheet_values`, issue-backed C++ gap; no false host claims | §6 |
| D8 | Seek any narrowly scoped #1251 exception **only at implementation gate**, after approved contract and committed RED | §9 |
| D9 | Choose `sheet_records/1` rather than generic `records/1`, to avoid Model B runtime-owned-name collisions with existing program bindings | §1 |
| D10 | Extract duplicate Sheet pair from R18 mixed aggregate without hiding ten other families; R18-owner review | §6 |
| D11 | Explicitly allow pure `sheet_records` in default-deny MCP worker, without new authorities | §6 |

Every row requires maintainer acceptance. A reviewer may propose a correction, but changing any semantic decision means revising this proposed contract before downstream work.

## 8. Scope compliance — cross-agent enforcement (process only)

**This section is phase governance, not additional language semantics.** It exists to ensure Claude, Codex, Copilot, ChatGPT and OpenClaw participants inherit exactly the same decisions.

**Immutable references for each authorized phase:** (a) merged pre-flight #1284 / revision 4; (b) issue #1328 and its newest *accepted* top-level phase handoff; (c) this contract at the **exact maintainer-approved commit SHA**, once approved; (d) the accepted design/RED evidence for phases that require them. Changes in later branches do not silently replace an accepted baseline.

**Authorized change envelope:** one `sheet_records/1` behavior; only the minimal registration/metadata, conformance-capability/issue-backed-gap accounting, protected/MCP policy, proving-case, documentation and release evidence necessary to deliver it. After approval the design must enumerate the actual allowed paths. Modifying an unlisted path requires a written necessity and explicit scope decision **before** editing it. Work that can be postponed goes to its existing follow-up or a tightly scoped future issue; do not consume R29 time on cleanup.

**Hard STOP / no implicit escalation:** parser, AST, Core IR, evaluator, Flow kernel, lifecycle runtime, Model B ownership/open/closed/immutable/module semantics, implicit Sheet→Seq behavior, another conversion or List→Flow builtin, C++ Sheet code, file/CSV/JSONL readers, joins/grouping/windowing, R30–R32 scope, or unrelated #1192 debt. A plausible improvement is **not** authorization. A needed exception returns to contract/pre-flight decisions for maintainer approval; no agent may self-waive it.

**Required Scope Compliance declaration in every phase/slice handoff and independent review:**

1. **Baseline:** issue #1328, pre-flight #1284, accepted contract SHA, prerequisite handoff URLs, and candidate commit/tree SHA; if contract is not yet approved, explicitly say `PROPOSED`.
2. **Authorized phase and changed files:** list exact paths and the approved contract clause or phase obligation that justifies each; report added files or interfaces separately.
3. **Invariant review:** explicitly state whether the new function remains the *only* semantic addition; identify any changes to existing Sheet/Flow/Outcome/lifecycle/Model B behavior, portable-host claims, or protected-value exposure.
4. **Exceptions and discoveries:** list every deviation, maintainer authorization link (if any), blocked finding, and deferred idea with its issue/owner; write `none` only after inspecting the actual diff.
5. **Evidence and verdict:** candidate SHA, relevant commands/results and host pins, independently inspecting reviewer, and `COMPLIANT`, `NONCOMPLIANT — STOP`, or `NOT YET REVIEWED`. Passing tests or the implementer's own claim does not substitute for independent inspection.

**Phase advancement:** R29-C ends only with independent contract review and maintainer semantic approval on #1328 or the contract PR. R29-G maps approved clauses to paths and remains design-only; R29-T commits observable RED before implementation and separately records current-behavior PASS; R29-I requires the §9 gate and exact RED SHA; post-GREEN maintainability, documentation and independent truth review verify scope against the **actual diff**. Every later agent re-reads accepted handoffs, not agent chat or memories. A missing handoff, missing authorization, changed semantics, test weakening, or unresolved blocking finding means **STOP**. The canonical ledger is the append-only **top-level comments on #1328**; supersede errors by linking a new comment.

CI and branch protection remain additional mechanical safeguards where configured; this clause **does not claim that an automated scope check already exists**.

## 9. Implementation gate and release completion are distinct

No R29 code implementation is authorized by approval of this contract alone. Implementation begins only if:

- **R29-C contract** and subsequent design have accepted handoffs;
- **R29-T RED** is committed, with exact SHA and honest Python/C++ conformance/host-gap evidence;
- either Model B #1250/#1251 foundation is fully signed off **or** the maintainer grants a **narrow exception on #1251 itself**, naming this approved contract and RED SHA; and
- the work remains inside §§1–8, including all hard STOP boundaries.

The #1251 exception cannot be inferred from pre-flight merge, contract approval, review comments, or an agent's assertion. The exception cannot waive protected-value safety, conformance truth, independent review, or subsequent #1251 integration. **R29 release completion**, if an exception was used, also requires #1251 signoff and a recorded post-integration R29/Model B interaction regression. Existing #1192 documentation debt, #1236, #1208, #1014 and broader C++ expansion remain deferred; they are not prerequisites to start R29-C/G/T.

---

**Approval ledger:** **PENDING** — independent reviewer and maintainer have not yet accepted the D1–D11 resolutions. Record the reviewer, accepted contract SHA and approval decision on [#1328](https://github.com/m0smith/genia-2026/issues/1328). Until then, this document stays **PROPOSED** and no design/TEST/implementation phase is automatically authorized.
