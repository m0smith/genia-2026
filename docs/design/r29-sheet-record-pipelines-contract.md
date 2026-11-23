# R29 — Sheet Record Pipelines Contract

**Status: PROPOSED R29-C CONTRACT — NOT YET APPROVED; NOT IMPLEMENTED BY THIS DOCUMENT.** This is a candidate portable language contract for maintainer semantic approval and independent review. `GENIA_STATE.md` is the final authority for **currently implemented** behavior; do not treat the proposed `sheet_records/1` function as available until implemented, verified, merged, and documented there.

**Scope baseline:** [R29 umbrella #1328](https://github.com/m0smith/genia-2026/issues/1328), merged [pre-flight PR #1284](https://github.com/m0smith/genia-2026/pull/1284) and `docs/analysis/r29-sheet-record-pipelines-preflight.md` revision 4 (§§4–6, 9, 12–13), `docs/strategy/roadmap/r25-r29.md`, and `docs/strategy/killer-workflow.md`. This contract resolves pre-flight candidate decisions D1–D11 *as proposals*, not as implemented facts. Contract approval is a separate gate.

## 1. Purpose and single new boundary

R29 adds **one explicit, pure, eager Sheet-to-record conversion** for existing Outcome-aware validated-data-pipeline composition:

- **Proposed public name:** `sheet_records/1`. The ordinary call `sheet_records(sheet_value)` returns a Genia `List` of Genia `Map` records. It also supports ordinary alias, higher-order, and `|>` call behavior, and visibility through existing module rules; there is no special syntax. The ordinary builtin registration must expose discoverable `help`/`doc`/`meta` metadata with maintained `@doc`/`@category` and generated reference entries, without altering module export or linking semantics. **Model B reservation is an accepted compatibility cost:** as an entry-scope runtime-owned builtin name, `sheet_records =: expr` is rejected under existing immutable-binding rules; nested/module-local binding and ordinary parameter shadowing retain their existing rules. The TEST phase must explicitly pin these behaviors; this contract does not alter Model B.
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

Existing `map`, `filter`, `reduce`, `scan`, `validate_each`, `collect_validated`, `collect_sheet`, `where`, `select`, and `derive` retain their own contracts and input restrictions. In particular, existing `keep_some_else` raises on an `err` item; R29 does **not** change that limitation (separately owned by #1014/#1236). R29 changes only the Sheet-to-List-of-Maps boundary. Existing schema-changing operations remain explicit; there is no column union, padding, implicit key coercion, or query/aggregation DSL.

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

**Capability decision (D7):** the existing Sheet family and this boundary belong under proposed optional manifest capability **`sheet_values`**. Add `sheet_values` to the existing `optional_capabilities` manifest and apply `requires: [sheet_values]` to the **19 Sheet-only existing shared cases** and new Sheet boundary cases in R29-T, without relabeling the mixed-family R18 aggregate as Sheet-only. **Python's protocol adapter automatically reports a new non-partial, non-vocabulary manifest capability as `supported`; this is not conditional on passing tests.** The TEST phase must verify the entire previously passing Python Sheet set still passes, with before/after Python totals and pass counts unchanged for the retro-gated baseline (apart from deliberately added new tests); the capability declaration must never be presented as proof by itself. C++ is not to claim `sheet_values` until implemented. The conformance gap must have a **real tracking issue**, host, affected cases and removal condition before any `spec/known_host_gaps.json` entry is committed. Existing C++ adapter-reported unsupported Sheet cases should become truthfully capability-excluded, with no suppressed regression or unsupported outcome. Reclassification must not conceal C++'s unsupported status.

**Mixed R18 family decision (D10):** during R29-T conformance accounting, remove the Sheet equality pair at positions 16–17 from `spec/eval/r18-conformance-cross-family-summary.yaml` **only after moving its unique same-cell, same-shape renamed-column negative check** (`sheet([["c", [1]]]) == sheet([["d", [1]]])` must be `false`) into `spec/eval/r18-conformance-sheet-structural-equality.yaml` in that same TEST change. The dedicated R18 Sheet structural-equality and column-identity cases must then preserve all Sheet evidence, including this currently unique near-miss. Preserve the mixed aggregate's other ten equality families and their original oracle; update its expected vector from 22 to 20 entries, the `families:` note and the case description, plus `docs/host-interop/HOST_PORTING_GUIDE.md` (current line 168), `docs/releases/R18.md` (current line 139) and `tests/spec/test_r18_conformance_protocol_evidence_795.py` (current line 63) to reflect the preserved split without overstating coverage. **R18 ownership:** the repository maintainer (`m0smith`, owner of the release decision for R18 issue #789 / E18-5 #795), or an explicitly designated independent R18 equality/conformance reviewer recorded on #1328, must review this edit before it is accepted. Do not gate the whole mixed aggregate on `sheet_values`: this would hide unrelated equality evidence. **No spec, test, or reference edit is authorized in this CONTRACT phase.**

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
| D9 | Choose `sheet_records/1` rather than generic `records/1` to avoid existing user-binding collisions; explicitly accept new entry-scope runtime-owned-name reservation (`sheet_records =: …` rejected) | §1 |
| D10 | Move the unique renamed-column near-miss into dedicated Sheet evidence **before** extracting mixed aggregate's Sheet pair; preserve other ten families, update named references and obtain R18-maintainer/designee review | §6 |
| D11 | Explicitly allow pure `sheet_records` in default-deny MCP worker, without new authorities | §6 |

Every row requires maintainer acceptance. A reviewer may propose a correction, but changing any semantic decision means revising this proposed contract before downstream work.

## 8. Scope compliance — cross-agent enforcement (process only)

**This section is phase governance, not additional language semantics.** It exists to ensure Claude, Codex, Copilot, ChatGPT and OpenClaw participants inherit exactly the same decisions.

**Immutable references for each authorized phase:** (a) merged pre-flight #1284 / revision 4; (b) issue #1328 and its newest *accepted* top-level phase handoff; (c) this contract at the **exact maintainer-approved commit SHA**, once approved; (d) the accepted design/RED evidence for phases that require them. **Approval is valid only for the exact reviewed contract commit recorded on #1328, not for this file's later HEAD contents.** Later commits **on this same branch** may add approved phase artifacts without changing the accepted contract baseline; if any later commit edits this contract, changes its `PROPOSED`/approval wording, or resolves a semantic clause differently, the prior approval for the changed contract is void until the new exact SHA receives independent re-review and renewed maintainer acceptance **on #1328**. A branch rename, PR update, or agent report never implicitly replaces the accepted SHA.

**One-living-PR history preservation:** use existing draft PR #1329 on branch `issue-1328-r29-sheet-record-contract` through R29-C/G/T/I/M/X/A/Z (and R29-R where required). Each authorized phase uses a separate auditable commit and an append-only verified handoff on issue #1328. **Do not squash or rebase away** separate contract, design, failing RED, GREEN, documentation or audit commits; when merging, use a method that retains original phase commits and their SHAs (for example a merge commit, **not** GitHub squash-merge or rebase-merge). If an unavoidable rewrite changes commit SHAs, STOP: repin evidence, redo affected reviews/approvals and re-record the accepted history on #1328 before advancing. No second per-phase PR is expected; a necessary `genia-cpp` cross-repository evidence change remains separate.

**Authorized change envelope:** one `sheet_records/1` behavior; only the minimal registration/metadata, conformance-capability/issue-backed-gap accounting, protected/MCP policy, proving-case, documentation and release evidence necessary to deliver it. After approval the design must enumerate the actual allowed paths. Modifying an unlisted path requires a written necessity and explicit scope decision **before** editing it. Work that can be postponed goes to its existing follow-up or a tightly scoped future issue; do not consume R29 time on cleanup.

**Hard STOP / no implicit escalation:** parser, AST, Core IR, evaluator, Flow kernel, lifecycle runtime, Model B ownership/open/closed/immutable/module semantics, implicit Sheet→Seq behavior, another conversion or List→Flow builtin, C++ Sheet code, file/CSV/JSONL readers, joins/grouping/windowing, R30–R32 scope, or unrelated #1192 debt. A plausible improvement is **not** authorization. A needed exception returns to contract/pre-flight decisions for maintainer approval; no agent may self-waive it.

**Required Scope Compliance declaration in every phase/slice handoff and independent review:**

1. **Baseline:** issue #1328, pre-flight #1284, accepted contract SHA, prerequisite handoff URLs, and candidate commit/tree SHA; if contract is not yet approved, explicitly say `PROPOSED`.
2. **Authorized phase and changed files:** list exact paths and the approved contract clause or phase obligation that justifies each; report added files or interfaces separately.
3. **Invariant review:** explicitly state whether the new function remains the *only* semantic addition; identify any changes to existing Sheet/Flow/Outcome/lifecycle/Model B behavior, portable-host claims, or protected-value exposure.
4. **Exceptions and discoveries:** list every deviation, maintainer authorization link (if any), blocked finding, and deferred idea with its issue/owner; write `none` only after inspecting the actual diff.
5. **Evidence and verdict:** candidate SHA, relevant commands/results and host pins, independently inspecting reviewer, and `COMPLIANT`, `NONCOMPLIANT — STOP`, or `NOT YET REVIEWED`. Passing tests or the implementer's own claim does not substitute for independent inspection.

**Phase advancement:** R29-C ends only with independent contract review and maintainer semantic approval **recorded as a top-level comment on #1328, referencing the exact contract commit SHA and the reviewer handoff**; PR comments can request review but are not an alternate approval venue. R29-G maps approved clauses to paths and remains design-only; R29-T commits observable RED before implementation and separately records current-behavior PASS; R29-I requires the §9 gate and exact RED SHA; post-GREEN maintainability, documentation and independent truth review verify scope against the **actual diff**. Every later agent re-reads accepted handoffs, not agent chat or memories. A missing handoff, missing authorization, changed semantics, test weakening, or unresolved blocking finding means **STOP**. The canonical ledger is the append-only **top-level comments on #1328**; supersede errors by linking a new comment.

CI and branch protection remain additional mechanical safeguards where configured; this clause **does not claim that an automated scope check already exists**.

## 9. Implementation gate and release completion are distinct

No R29 code implementation is authorized by approval of this contract alone. Implementation begins only if:

- **R29-C contract** and subsequent design have accepted handoffs;
- **R29-T RED** is committed, with exact SHA and honest Python/C++ conformance/host-gap evidence;
- either Model B #1250/#1251 foundation is fully signed off **or** the maintainer grants a **narrow exception on #1251 itself**, naming this approved contract and RED SHA; and
- the work remains inside §§1–8, including all hard STOP boundaries.

The #1251 exception cannot be inferred from pre-flight merge, contract approval, review comments, or an agent's assertion. The exception cannot waive protected-value safety, conformance truth, independent review, or subsequent #1251 integration. **R29 release completion**, if an exception was used, also requires #1251 signoff and an **R29-R post-integration run of T1 + T2 + T3 plus the full Python regression** (either `uv run pytest -n auto -q` or both required loopback and non-loopback partitions), recording **candidate SHA, commands, observed results, host/evidence pins and any failures** on the #1328 handoff and linked release audit. R29-R must explicitly cover new-boundary behavior, existing composition, Model B name/module interactions, and no regressions before marking the release complete. Code additions in R29 must also meet the existing maintained-code documentation ratchet; that obligation does not authorize unrelated #1192 cleanup. Existing #1192 documentation debt, #1236, #1208, #1014 and broader C++ expansion remain deferred; they are not prerequisites to start R29-C/G/T.

---

**Approval ledger:** **PENDING** — independent reviewer and maintainer have not yet accepted the D1–D11 resolutions. Record the reviewer, accepted contract SHA and approval decision on [#1328](https://github.com/m0smith/genia-2026/issues/1328). Until then, this document stays **PROPOSED** and no design/TEST/implementation phase is automatically authorized.
