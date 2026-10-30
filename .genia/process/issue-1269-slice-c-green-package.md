# #1269 / #1250 — Model B Slice C GREEN implementation package

Process evidence and plan only. **Not implemented-truth documentation.** No production, test, spec, manifest or C++ file is changed by this package, and nothing here authorizes GREEN, G1, a C++ fix or a merge.

## 0. Authority and state

- RED authority: Codex PASS [6374055115](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6374055115) at **`9a7808be18352da7acd41e4b0975851dab9f39ad`** (PR #1270 head; verified unchanged when this package was written). Test-content SHA `904ff907…` (the head adds only the evidence note). Frozen: 137 shared YAML + 12 fixtures, harness `tests/spec/test_model_b_slice_c_red.py`, nine host-local modules, C0 tests, staging (`spec/manifest.json`, `_VOCABULARY_ONLY_CAPABILITIES`, known-gap entry).
- Measured RED baseline (author) / independently reproduced (Codex): in-process `1038 / 956 / 82`; external Python `938 pass / 100 unsupported` (not GREEN); exact-18 parity fails `100 == 18`; focused set `230 failed / 221 passed`; pinned C++ `44456baea06b4bb7bdf727e39939dd7150261ee6` `270 / 9 / 759`.
- Host pin: `.github/workflows/host-parity.yml` → genia-cpp `44456ba…` (= `main`); adapter-declared contract revision is an ancestor (compat only). CI: `ci.yml` "Fast tests" runs `pytest -m "not slow and not loopback" -n auto --maxfail=1` plus a loopback partition; the parity test is `slow`/`full_conformance`.
- Exclusions that stay out of Slice C: Slice D (cross-module extension/linking), Slice E (closed `=:` functions), lifecycle #1271/#1272, G1 selector (until decided), R7-D3 (host-local follow-up).
- No new contract contradiction was found in preparing this package.

## 1. G1 decision package (R7-D9)

### 1.1 What is already settled (authority)
`preflight §2.5.1` records maintainer directive [6326404613](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6326404613) and the integration gate [6327837022](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6327837022). Those settle, as **boundary rules 1–8** (not new language design):
1. selection convention unchanged (`main/1` with `argv()`, else `main/0`, else source result); 2. **no pattern-based discovery**, no guard evaluated to choose an entry; 3. a pattern-bearing `main` (including wildcard headers) is not auto-selected; 4. **no new diagnostic**; 5. **no representative record**; 6. pipe/REPL/test/serve unchanged; 7. explicit calls use ordinary dispatch.
The frozen RED suite already encodes the *pure* cases: five legacy guards (`main-legacy-main1-preferred`, `-main0-fallback`, `-rest-main-selected`, `-no-qualifying`, `-command-mode`), `main-repl-never-selects`, and nine gated cases (`pattern-not-selected`, `pattern-guard-not-evaluated`, `wildcard-not-selected`, `multi-pattern-group-not-selected`, `pattern-command-mode`, `explicit-call-dispatches`, `explicit-call-miss`, `test-mode-unchanged`, `repl-pattern-never-selects`).

### 1.2 What is implemented today (verified by running the Python CLI)
| Program (file mode, argv `--x`) | Result today |
|---|---|
| `main(args)` + `main()` (legacy) | `top` / `main1` / `11` — `main/1` preferred |
| `main(a)` + `main(a, ..r)` (fixed + rest, same minimum) | `Error: Duplicate function definition: main/1` (cannot be constructed) |
| legacy `main(args)` + pattern `main(["--x"])` | `Error: model-b-not-implemented: …` (cannot be constructed) |
`_resolve_program_result` (`src/genia/interpreter.py:513`) reads `group.get(1)` then `group.get(0)`, called only from the `command` and `file` branches. **Mixed groups become constructible only at GREEN**, so GREEN must define the selector's behavior for them or violate rule 5.

### 1.3 What is not settled — the reserved six
Mixed-group behavior: `…-g1-mixed-main0-plus-pattern`, `…-mixed-main1-plus-pattern`, `…-main1-plus-pattern-arity1-legacy-first`, `…-pattern-first`, `…-fixed-plus-rest-same-minimum`, `…-legacy-rest-plus-pattern-arity1`. Rules 1–8 do not say whether a *legacy* record inside a mixed group is still selected, or whether declaration order matters.

### 1.4 Alternatives (SC-MAIN-3, argv `["--x"]`)
Program: `print("top")` / `main(args) = { print("legacy"); 1 }` / `main(["--x"]) = { print("pattern"); 2 }` / `42`.
| Option | Rule | Output for this program (and for the reordered program) |
|---|---|---|
| **A — whole-group (recommended; G1 as recorded)** | auto-run `main` only if the *entire* group is legacy identifier-header records with no two sharing a required-arity key; else silent source-result fallback | `top` / `42` in **both** orders; nothing selected |
| B — legacy-index | select the legacy record at arity key 1/0 even in a mixed group | `top` / `legacy` / `1`; for the pattern-first order the rule must say whether the "arity-1 record" is the pattern record (violates 2/5) or the later legacy one (needs a new ordering rule) |
| C — reject at construction | mixed `main` fails to declare | new diagnostic → violates rule 4; also changes explicit-call programs |
| D — leave unspecified | GREEN picks whatever the code does | invites a representative-record pick (rule 5) and an unreviewed oracle |

Other shapes under A: `main()` + pattern(arity 1) → `top` / `42`; `main(a)` + `main(a, ..r)` → `top` / `42` (no representative); legacy rest `main(a, ..r)` + pattern arity-1 → `top` / `42`. Pure legacy groups keep M1–M5 unchanged (A only *adds* the whole-group eligibility test).

### 1.5 Does deferral weaken the 137-case GREEN acceptance?
No: all 137 pass independently of mixed groups. But deferral leaves GREEN behavior for constructible mixed groups unreviewed. Recommendation:
- **Decision needed (one sentence):** approve Option A as the Slice C entry-selector invariant and authorize the six reserved cases as a reviewed TEST-only amendment **before** GREEN starts (so GREEN stays test-first).
- Cost if approved: shared cases 137 → 143, `requires: [default_open_functions]` (C++ `unsupported`); known-gap `affected_tests` 82 → 88; GREEN targets 1044 in-process, Python external 1026 pass + 18 unsupported. Smaller alternative if the maintainer will not add tests: approve A as a constraint and cover it host-locally only (HL-9b) — accepted but weaker portable evidence; the 137 are unaffected.
- #1271/#1272 keep ownership of any future `main` behavior.

## 2. Python GREEN work packages (dependency order)

Existing architecture is kept: `GeniaFunctionGroup` (`callable.py:238`) gains ordered records; dispatch reuses the R20 unit dispatcher (`_dispatch_open`, `OpenClauseRecord`); `GeniaFunction` stays the header/body record; `eval_with_tco`/`TailCall` unchanged. Every batch ends with the listed RED families passing, the 55 guards and 901 original specs green, and ruff/doc checks clean. Batches are separate commits that cite the RED SHA.

| # | Batch | Components | RED families turned green | Depends | Acceptance | Risk |
|---|---|---|---|---|---|---|
| B0 | Test-boundary amendments (TEST-only, reviewed first) | amend A1–A4 tests per §3; optional six G1 cases | none (preserves intent) | decisions §7 | Codex PASS on the amendment diff | semantic drift if rewritten loosely |
| B1 | Pure typed structural key | `callable._open_dispatch_key`/`_structural_key` (+ shared helper) | `test_model_b_slice_c_keys.py` (22); shared `key-*` as reached | none | all 34 key tests pass; explicit-open R20 specs unchanged except approved deltas `key-r20-delta-*` | R20 duplicate behavior changes for `true`/`1`, `1`/`1.0` (approved); lambda scope walker correctness |
| B2 | Ordered clause records + owner/provenance on the group | `GeniaFunctionGroup` (records list, arity index kept as index), `Env.define_function` (ownership via provenance, not `callable()`), `environment.py` lock | `records` (11), `ownership` direct-`define_function` and state tests, `disp-*` index consistency | B1 | legacy `.functions` consumers (route/HTTP/`@test`/lifecycle/help) unchanged for legacy groups; arity index consistent; duplicate rejected before publication | many readers of `.functions`; keep a derived index |
| B3 | Executable pattern/guard headers + dispatch adapter | evaluator `IrPatternFuncDef` branch (non-closed only), header-frame + guard scope, unified shape stratum (D1) incl. P5 ambiguity, case-miss identity | `pat-*`, `open-*`, `disp-*`, `hdr-*`, `d8-*`, `opt-*`, `stage-*` | B1, B2 | shared families pass in-process; closed `=:` still `model-b-not-implemented`; P7/P8/P20 text unchanged | Outcome awareness (`_callable_explicitly_handles_none`) must inspect the selected stratum; TCO |
| B4 | Ownership and alias rejection | `define_function`/evaluator: `function-declaration-not-owner` (local, imported), path/span-free messages, annotation not evaluated on rejection | `own-*`, `ownership` host tests | B2, B3 | exact approved strings; state after rejection | module-identity rendering; imported-alias detection |
| B5 | Metadata, annotations, consumers | three channels, annotation publication order, `help`, special consumers predicates (route/HTTP/`@test` exact single record) | `meta-*`, `ann-*`, `consumers` host tests | B2, B3 | consumers table (accept/reject) exact; help summary unchanged | route/`@test` must reject pattern/fixed+rest groups; lifecycle must accept |
| B6 | Optimizer retention + A4 | `optimizer.py`, `interpreter.py` optimize boundary | `optimizer_retention` (7), `d8-optimizer-equivalence`, `optim-*` | B3 | §3 | A4 semantics; hot-path performance |
| B7 | REPL / CLI / `main` | entry selector (Option A if approved), mode equivalence, REPL persistence (Python already treats `;` submissions as complete) | `mode-*`, `main-*`, `repl_main` host tests | B3, B4 | all 15 `main` cases + six G1 if authorized | entry selector must not use a lossy index |
| B8 | Races/reentrancy | lock discipline during annotation/guard callbacks | `optimizer_ir` race tests | B2–B5 | bounded joins, no deadlock | lock ordering |
| B9 | Capability transition + phase guards | remove `default_open_functions` from `_VOCABULARY_ONLY_CAPABILITIES`; C0 `GREEN_CAPABILITY_MAP`; flip only `*_legacy_outcome_today` companions and the listed phase-guard tests (package §6.4) | C0, capability evidence, `identity` companions | B1–B8 pass | GA-1…GA-23 | accidental weakening — each flip is a reviewed hunk |
| B10 | Documentation and MCP profile | §6 | doc/semantic tests | B9 verified | doc suites green | claiming unverified behavior |

Order rationale: key (B1) and records (B2) are leaves; B3 needs both; B4/B5/B6/B7 are independent after B3 and can be separate commits; B9 only when everything passes.

## 3. A1–A4 migration rules (preserve test intent)
- **A1 records/owner identity:** keep the observable boundary (dispatch order, group identity, alias liveness, arity index, duplicate provenance, rejection state). Once B2 names the record and owner fields, add exact-field assertions *in addition*; never remove the behavioral tests. Ownership is `(module identity, defining name)` provenance on the group, not `callable(value)`.
- **A2 pure-key signatures:** the key walker may change signature or move; migrate the 34 `keys` tests by replacing only the entry-point calls. The semantic table (Boolean/Integer/float tags, payload structure independent of mapping order, scope-aware alpha-normalization, quote as data, active `unquote` by depth, rest binders, rejection of unsupported/malformed input with no `repr`/rendering/evaluation) is invariant. Rejection tests keep "some Exception, no host rendering".
- **A3 retention location:** retention may move to the unoptimized declaration record. The `optimizer_retention` helper `_clauses` then reads that record; the assertions (all original arms in order, equal keys/ordinals/guards/provenance, derivation not from the optimized node alone) are unchanged. A *safe decline* of the rewrite is allowed **only** with an explicit amendment to the "rewrite participation" controls (`test_nil_empty_arm_reaches_the_nth_style_rewrite_today` would become a decline assertion), reviewed by Codex.
- **A4 on/off divergence (obligation, not a harmless bug):** with the optimizer on, `pick(0, 7)` returns `none("nil")` where the unoptimized program raises `No matching case for function pick/2 with arguments [0, 7]`, and `pick("a", [1])` returns `none("nil")` where the unoptimized program returns `none("type-error", …)`. Results, errors, effects, ordering and terminal grouped-miss must agree.
  **Recommendation:** make the rewrite *retention-aware and domain-exact*: keep the original `IrCase` structure on the declaration record (A3), and have `eval_list_traversal_loop` take the fast path only when its domain assumption holds (list-typed second argument and numeric first argument); otherwise fall back to the retained case evaluation. This preserves performance for the intended inputs, removes the divergence without changing semantics, and satisfies retention in one mechanism. Safe decline (never rewrite) is the fallback if the fast path cannot be proven exact; it needs the A3 amendment.

## 4. C++ remediation in parallel (genia-cpp #53–#57, no production change here)
- **Accountable owner proposal:** `m0smith` (maintainer/integration owner) is the *proposed* accountable owner for each issue; **assignment is not confirmed** and no GitHub assignee has been set. Please confirm per issue.
- **Verification against the approved RED suite:** reproductions and acceptance criteria were re-checked: nine C++ FAIL ids (D1 `hdr-grouped-body-captures-header`; D2 `own-explicit-open-alias-unchanged`, `d8-r20-flattening-unchanged`; D3 `meta-inline-doc-body-runs`; D4 `key-legacy-dup-id`, `d8-legacy-identical-header-dup`; D5 `open-persistent-arities`, `open-repl-alias-sees-later-arity`, `main-repl-never-selects`) match the independently reproduced `270 / 9 / 759`. Gap-bypassed informational failures (`meta-channel-inline-doc`, `meta-inline-doc-shared-via-alias`, `meta-conflicting-inline-doc-before-install`, REPL `ann-*`) share the D3/D5 causes. If the six G1 cases are authorized they are `unsupported` on C++.
- **Work packages (each: failing C++ test first; distinct RED/fix commits; run the pinned adapter against the exact shared YAML; no gap entry, capability change, sleep or expected-output change):**
  | Pkg | Issue | Area | Independent? |
  |---|---|---|---|
  | W1 | #53 D1 | parser/lowering: grouped arms see header params | yes |
  | W2 | #55 D3 | parser: inline docstring `f(x) = "d" body` | yes (touches the same function-definition parser as W1: sequence or rebase) |
  | W3 | #56 D4 | evaluator/environment: reject duplicate ordinary definitions with `Duplicate function definition: f/N` before later statements | yes; shares function-group storage with W4 |
  | W4 | #54 D2 | R20: ordinary declaration over an open interface/alias; flattened-arm duplicate | after or alongside W3 (same declaration path) |
  | W5 | #57 D5 | REPL: complete `;` submissions evaluated, final scalar echoed | yes |
  Parallelism: W1+W2 (parser), W3+W4 (evaluation), W5 (REPL) are three independent lanes; W1↔W2 and W3↔W4 serialize within a lane. Each package ends with a pinned-host rerun showing its ids PASS and no new FAIL.
- **Final acceptance (merge requirement, not a GREEN prerequisite):** `fail = protocol_error = crash = timeout = invalid = 0` on the exact final shared YAML at the workflow-pinned host (updated deliberately in `host-parity.yml` and the C++ README), per-id ledger (GA-22), `host_parity_gate` OK. `known_host_gaps.json` may list only the optional `default_open_functions` capability (unsupported cases); it must never waive the nine FAILs, and `unsupported` is never PASS.

## 5. GREEN acceptance matrix
Python GREEN prerequisites vs. final merge requirements are separated. Counts assume the 137-case suite; add +6 where noted if G1 is authorized (143 → in-process 1044, external 1026 pass + 18 unsupported).
| Acceptance | Required outcome | Command / evidence |
|---|---|---|
| Shared conformance (in-process) | 1038 pass / 0 fail / 0 invalid (G1: 1044) | `uv run python -m tools.spec_runner` |
| Frozen 137 | 137 pass; ids/requires/oracles equal §R6.D | harness `uv run pytest tests/spec/test_model_b_slice_c_red.py`; `git diff 9a7808be..HEAD -- spec/**/model-b-c-* tests/spec` empty or listed amendments (GA-15) |
| Python external adapter | 1020 pass / 18 unsupported / 0 other (G1: 1026) | `uv run python -m tools.spec_runner --host "<venv python> -m hosts.python.protocol_adapter" --host-jobs 2 --host-timeout 120 --evidence …`; evidence shows `default_open_functions: supported` and `unsupported == 18` (GA-10) |
| Per-id real adapter PASS | every id `kind == "pass"` | `execute_spec_via_host` loop (GA-4/GA-16), replaces the RED no-invocation witness |
| Exact-18 parity | passes **unchanged** | `uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py` (≈8 min; `git diff` of that file empty) |
| Host-local future tests | 148 now-failing pass (after reviewed A1–A4 migrations); the `*_legacy_outcome_today` companions and listed phase guards flipped deliberately | `uv run pytest tests/unit/test_model_b_slice_c_*.py` |
| Capability advertisement | `default_open_functions` `supported` only after verified behavior; override removed in the same change | C0 tests with `GREEN_CAPABILITY_MAP`; GA-2/3/19 |
| Optimizer correctness | no on/off divergence (A4), retention (A3) | `optimizer_retention` + `optimizer_ir` suites; `test_model_b_optimizer_regression.py` |
| Regression | fast selection green; loopback partition green | `pytest -n auto -q -m "not slow and not loopback"` and `-m loopback` |
| Docs / MCP | reflect implemented behavior only | `tests/doc`, `gen_mcp_language_profile --check`, `validate_llm_instructions`, strict MkDocs to a scratchpad dir |
| **Final merge only:** C++ | zero failure classes at the final pin | pinned adapter run + `host_parity_gate`; genia-cpp #53–#57 closed or evidenced |
| **Final merge only:** CI | final-head required CI incl. py3.14 matrix, Node jobs | workflow results |
Never counted as passing: `unsupported`, a skip, an xfail, an early `--maxfail` stop.

## 6. Documentation synchronization (only after verified GREEN)
| File | Sections to change | Evidence |
|---|---|---|
| `GENIA_STATE.md` | "Model B declarations" §716–744 (partial → ordinary default-open execution and pattern/guard headers; keep closed `=:` and linking unimplemented); §3625–3626 summary; function/dispatch sections for D1 (P5 ambiguity note), typed keys, ownership/`function-declaration-not-owner`; `main` entry caveat (pattern-bearing `main` not auto-selected, per G1 decision); anchors preserved | shared specs + host-local tests |
| `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md` | the identical "Model B declarations: partial support" block; REPL group growth / failed-declaration behavior / `;` complete submissions; `main` caveat | same |
| `docs/contract/semantic_facts.json` + `apps/mcp/mcp.genia` + `tests/data/mcp_language_profile.golden.json` | `clauses` idiom (line ≈255) and the `model-b-not-implemented` fragment (≈448); regenerate with `tools/gen_mcp_language_profile.py`; run its `--check`, `test_state_anchors_and_registry_sync.py`, `test_semantic_doc_sync.py` | profile tests |
| Host docs | `docs/host-interop/HOST_CAPABILITY_MATRIX.md` (row for `default_open_functions`: Python supported, C++ unsupported/#1269; ≈93) + `display_to_key` in `tests/doc/test_portability_contract_sync.py`; `capabilities.md`, `HOST_PORTING_GUIDE.md`, `docs/architecture/core-ir-portability.md` (≈219), `executable-semantic-conformance.md` | doc tests |
| Other | `docs/ai/LLM_CONTRACT.md` ("literal first parameter needs `open`" sentence), `docs/book/03-functions.md`, cheatsheets (with `[case:]` sidecars), `docs/design/pre-r29-*` status lines, roadmap/release records and #1250/#1269 issue status; maintained-code docs for new bindings | `tests/test_cheatsheet_*`, doc style, code-documentation checker |
Checklist rule: each statement cites the passing test id; no sentence describes Slice D/E or lifecycle behavior as implemented.

## 7. Decisions that genuinely require maintainer approval
1. **R7-D9 / G1** — approve Option A and whether the six cases become shared (recommended) or host-local only (§1.5).
2. **Separate GREEN authorization** (explicit SHA `9a7808be…`, scope Python B0–B10, exclusions §0).
3. **A4 disposition** — retention-aware, domain-exact fast path (recommended) vs. safe decline; either needs a reviewed B0 amendment.
4. **Owner confirmation** for genia-cpp #53–#57 (proposed: `m0smith`).
5. R7-D3 remains a separate host-local authority follow-up (no action in Slice C).

## 8. Copy-ready GREEN implementation prompt
> **GENIA Slice C GREEN (Python).** Repo `m0smith/genia-2026`, issue #1269, PR #1270, branch `claude/nice-brahmagupta-1e17ws`. Preconditions you must verify first: separate GREEN authorization comment exists naming RED SHA `9a7808be18352da7acd41e4b0975851dab9f39ad`; G1 decision recorded; B0 amendments (if any) reviewed. Read `AGENTS.md`, then `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/process/run-change.md`, `docs/ai/LLM_CONTRACT.md`, the Model B contract/design, `.genia/process/issue-1269-slice-c-green-package.md` and Codex's RED PASS. Implement batches B1→B10 from the package in order, one commit each citing the RED SHA, using the existing architecture (`GeniaFunctionGroup`, `OpenClauseRecord`, `_dispatch_open`, `eval_with_tco`). Treat the 137 YAML, fixtures, harness, comparator and runner as frozen; migrate A1–A4 tests only by reviewed amendment. No skips, xfails, comparator or oracle edits, capability masking, C++ changes, Slice D/E or lifecycle work. Remove `default_open_functions` from `_VOCABULARY_ONLY_CAPABILITIES` only in the commit where per-id real-adapter PASS holds. Validate per the package §5 (in-process 1038/1038, external 1020+18, unchanged exact-18 parity, host-local suites, fast + loopback partitions, docs, MCP profile check, strict MkDocs to a scratchpad dir, ruff). Then update STATE/RULES/REPL README/README/semantic facts/MCP profile/host and roadmap docs to *demonstrated* behavior only (package §6). Post a handoff with commands, counts and a coverage map; request independent Codex review; do not merge.
