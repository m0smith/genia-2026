# #1269 / #1250 — Model B Slice C TEST-only RED evidence

Process evidence only (not implemented-truth documentation). Authorization: [PR #1270 comment 6367339301](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6367339301) at planning SHA `a3bdc306bf6b4242027ad55be4ca7f5f89bfacb2`; decisions [6366547321](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6366547321).
Per-case data: `issue-1269-slice-c-red-per-case.json`. RED commits: `a60a5dfc` (cases, harness, staging), `38a94e84` (host-local tests), `5e408dd3` (gap links); this note's own commit is the review head.

> **Revision 2 (RED corrections after Codex REVISE [6369869513](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6369869513)).** Prior RED SHA `f5aa07d5a34b4255d69ea6051ed0a4eb794f0f8b`. Only host-local tests changed; the 137 shared YAML, 12 fixtures, harness, manifest, gap entry, adapter override and C0 tests are byte-identical to `f5aa07d5`. The *Revision 2* sections at the end supersede the host-local counts and the "Blocked / not written" paragraph below.

## Inventory (all measured)
- 137 shared cases materialized mechanically from test plan §R6.D (74 eval, 37 error, 26 cli; 12 sibling `.genia` inputs). Re-parsing the YAML through the loader and comparing source, modules, argv, requires and expected streams against §R6.D: **0 differences**. 55 guards, 82 `default_open_functions` future cases (P5 and the six D5 rows included, Option B). Repeated-header-binder case and six G1 ids not created.
- Host-local (superseded by Revision 2 below): 212 items in the first RED commit; blocked items are now implemented.

## Staging
Manifest `optional_capabilities` + `default_open_functions` (36 names); `_VOCABULARY_ONLY_CAPABILITIES = {default_open_functions}`; Python advertises it `unsupported`; known-gap entry (cpp, #1269, 82 ids, links to genia-cpp#53–#57). C0 tests: `PRE_C0_CAPABILITY_MAP` kept; `RED_CAPABILITY_MAP`/`PHASE_OVERRIDE`/`_stage` union helper added; 12 C0 tests pass. No change under `src/`, `tools/spec_runner/`, root docs, semantic facts or MCP profile since the authorized SHA.

## Results (Python 3.12.3, this container; HEAD `5e408dd3` content)
| Check | Command | Result |
|---|---|---|
| Direct harness | `uv run pytest tests/spec/test_model_b_slice_c_red.py -n auto -m "not slow and not loopback"` | 143 items: **82 failed, 61 passed**, 0 skipped/xfailed; failed set == the 82 future ids exactly |
| In-process runner | `uv run python -m tools.spec_runner` | `total=1038 passed=956 failed=82 invalid=0` (exit 1); every actual stdout/stderr/exit equals the plan's baseline column |
| External Python | `... --host "<venv python> -m hosts.python.protocol_adapter"` | `total=1038 passed=938 failed=0 unsupported=100`, exit **0** — not GREEN; the 100 = 82 gated + 18 pre-existing |
| Unchanged parity assertion | `uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py` | **FAILED** `assert 100 == 18` (expected RED), 472 s |
| Fast-CI selection | `uv run pytest -q -m "not slow and not loopback" -n 4` | 7177 passed, 60 skipped (all pre-existing environmental, none in Slice C files), 192 failed = 82 harness + 109 host-local + 1 artifact (below). Without `--maxfail` so all 82 are attempted |
| Loader | harness | zero invalid specs; exact 137-id equality both directions |
| Docs | `uv run pytest tests/doc -n 2` | 397 passed, 35 skipped (= baseline) |
| MCP profile / LLM | `tools/gen_mcp_language_profile.py --check`; `tools/validate_llm_instructions.py` | pass |
| MkDocs | `uv run mkdocs build --strict` | built, no warnings. The generated untracked `site/` made `test_state_distillation_gates` fail once; removed, passes (not a regression) |
| Lint/whitespace | `uv run ruff check .`; `git diff --check` | clean |
| C0 + capability + gate unit tests | focused set | pass |
Not run: loopback partition, py3.14 CI matrix, VS Code/Node jobs, `gen_function_docs`/doc-lint (no prelude or docs changed), full slow suite beyond the parity test.

## C++ (pinned `genia-cpp@44456ba…` = workflow pin = `main`, rebuilt natively with g++ 13.3, read-only; not the CI binary; adapter contract revision `6402e668…` is an ancestor)
Exact RED YAML, normal gate: `total=1038 passed=270 failed=9 unsupported=759` (matches the projection). The 9 FAILs are all ungated guards: CPP-D1 `hdr-grouped-body-captures-header` (genia-cpp#53); CPP-D2 `own-explicit-open-alias-unchanged`, `d8-r20-flattening-unchanged` (#54); CPP-D3 `meta-inline-doc-body-runs` (#55); CPP-D4 `key-legacy-dup-id`, `d8-legacy-identical-header-dup` (#56); CPP-D5 `open-persistent-arities`, `open-repl-alias-sees-later-arity`, `main-repl-never-selects` (#57). Host parity gate: `default_open_functions` = KNOWN_GAP, overall FAIL because of fail=9 (intended; must reach 0 before merge). Gate-bypassed informational run: 5 further gated cases would also fail (D3/D5 causes). All 82 future cases are `unsupported` on C++.

## Remaining before GREEN
Independent Codex RED review; separate GREEN authorization; R7-D9 (G1) decision; naming of internal group/key APIs for the blocked host-local items; R7-D3 follow-up; assignment of CPP-D1–D5 and zero C++ failures on the final YAML; at GREEN: remove the override, flip only the `*_legacy_outcome_today` companions and the phase-guard tests listed in package §6.4, then synchronize root docs, semantic facts, MCP profile, host/roadmap docs to verified behavior.

## Revision 2 — host-local corrections (measured)

### Host-local coverage matrix (HL-1…HL-24)
| HL | Subject | Module (tests/unit/test_model_b_slice_c_*.py) | RED status |
|---|---|---|---|
| 1 | ordered records / index / provenance | `records` (+ legacy index in `optimizer_ir`) | 11 behavioral tests fail (`model-b-not-implemented` stops construction); 4 oracle self-checks and the legacy-table baseline pass |
| 2 | pure dispatch-key boundary (`_open_dispatch_key`/`_structural_key`) | `keys` | 22 of 34 fail on real invariant violations; 12 pass (already-correct behavior) |
| 3 | writer races, reentrancy, lock | `optimizer_ir` | pattern-declaration cases fail; legacy lock case passes |
| 4, 5 | consumer table, effective help, autoload twin | `consumers` | legacy rows pass; pattern/fixed+rest rows fail |
| 6, 21, 22, 23 | failure identity, legacy wording, lambda/builtin, migration companions | `identity` | `*_today` pass; new-outcome tests fail |
| 7 | source ↔ direct-IR ↔ optimized twins vs YAML oracle | `optimizer_ir` | 63 future ids fail, 42 guards pass |
| 8 | optimizer participation, on/off equivalence, arm retention | `optimizer_retention` | 7 of 18 fail (retention ×3, out-of-domain divergence ×2, D8 terminal miss ×2); controls pass |
| 9, 12, 15, 19, 20, 24 | REPL/main/file-label structure | `repl_main` | `*_today` pass; pattern rows fail |
| 10, 11, 14, 16, 17, 18 | ownership, diagnostic safety, post-failure state | `ownership` | 11 fail, 10 pass |
| 13 | capability evidence | `capability_evidence` | 3 pass (staging only) |
Totals (measured): 278 host-local items in 9 modules + helper: **148 fail, 130 pass**; with the 143-item harness and 12 C0 tests: 433 items, **230 fail, 203 pass**, 0 skipped/xfailed.

### Corrections (Codex findings)
1. **HL-8** — new `optimizer_retention` module. Programs use `nil`; each test proves the rewrite ran (`IrCase` → `IrListTraversalLoop`) and a `0` control proves the shared witnesses are declined (`optimize_program` returns the same node). Retention is asserted at the program boundary (every original `IrCaseClause` reachable in order; arm key/ordinal/guard/span records equal): the optimized declaration reaches 2 of 3 arms (recursive arm absent) → RED. Later-declaration, legacy-duplicate and arm-not-checked observations added. The previous test that expected `"special"` behind an all-bind header contradicted D8 (earlier header wins, grouped miss is terminal) and was replaced. **New finding (pre-existing, not introduced here):** with the optimizer on, `pick(0, 7)` returns `none("nil")` and `pick("a", [1])` returns `none("nil")`, where the unoptimized program raises the case-miss error / returns `none("type-error", …)`; the approved on/off-equivalence requirement is violated → RED tests added; production unchanged.
2. **HL-2** — new `keys` module through the existing `genia.callable._open_dispatch_key`/`_structural_key`. Real violations observed: `true`/`1`/`1.0` collapse into one dictionary key; numeric payload dicts are keyed by `repr` (insertion-order dependent); lambda parameters are not alpha-normalized and an inner binder shadowing an outer one yields a wrong slot; active `unquote` (depth 1 and doubly-nested depth 2) is not normalized; unsupported objects (custom class, set, bytes, plain object) are accepted through `repr` — `__repr__` is actually called; malformed patterns (non-pattern node, `items=None`, raw ints/strings, `None`) are silently accepted as fixed arity 0. Already-correct behavior is pinned (`*_today`). Rejection tests require only that some Exception is raised.
3. **HL-1** — new `records` module (no invented field names). Observable boundary: dispatch results over all 6 orderings of three distinct-key same-arity clauses interleaved with an unrelated declaration (reference model), group identity/alias liveness, arity index as index, construction-time duplicate with exact first/duplicate provenance, state after rejection. Four self-checks show the oracle rejects arity-keyed (first/last wins), sorted and reversed stores; one baseline test shows the legacy table cannot hold two clauses of one arity (flipped deliberately at GREEN).
4. **Help order** — the old assertion was non-discriminating. Help prints only a shape summary (`h/1, 2, 3+`), so the claim is narrowed to "every declared shape named, deterministic, no host objects" with a discrimination self-check; declaration order is asserted at the record boundary (item 3).

### Proposed test-boundary amendments (no test written; for maintainer/Codex confirmation)
- A1 (HL-1 representation): once GREEN names the ordered-record and owner/defining-name fields, add exact-field assertions; until then behavior above is the approved boundary.
- A2 (HL-2): if GREEN replaces `_open_dispatch_key`/`_structural_key` with a different internal signature, the semantic assertions in `keys` migrate with it (no weakening).
- A3 (HL-8): retention is asserted as "reachable in the optimized program"; if GREEN stores arms on a declaration record outside the program IR, the reachability helper moves to that record.
- A4: decide whether the pre-existing optimizer on/off divergence is fixed in Slice C GREEN or the rewrite is declined for out-of-domain arguments; the RED tests accept either.

### Outstanding-decision register
| Item | Status |
|---|---|
| R7-D3 lambda/builtin authority | open, host-local only |
| R7-D9 / G1 six `main` cases | separate pre-GREEN decision |
| R7-D8 CPP-D1–D5 owner | issues genia-cpp#53–#57 name "C++ host implementer with m0smith integration"; no assignee set. **m0smith must confirm the named accountable owner** (not set by this work) |
| A1–A4 above | proposed |
| Zero C++ failure classes | final-merge requirement (currently fail=9) |

### Revision 2 validation (Python 3.12.3; uv; this container; single runs, no recoveries)
| Check | Command | Result |
|---|---|---|
| Shared inventory | harness + loader; YAML/fixtures/harness/manifest/gaps/adapter/C0 vs `f5aa07d5` | `git diff f5aa07d5 -- spec src tools hosts docs root-docs tests/spec C0-test` empty; 137 ids, 55/82, zero invalid |
| In-process | `uv run python -m tools.spec_runner` | `total=1038 passed=956 failed=82 invalid=0`, exit 1 |
| External Python | `--host "<venv python> -m hosts.python.protocol_adapter" --host-jobs 2 --host-timeout 120` | `passed=938 failed=0 unsupported=100 timeout=0`, exit **0 — not GREEN** (clean single run; the earlier 4-job/short-timeout timeouts did not recur) |
| Exact-18 parity | `uv run pytest tests/spec/test_python_protocol_adapter_parity_762.py` | unchanged file FAILED `assert 100 == 18` (431 s) |
| Pinned C++ `44456ba` | `--host /home/user/genia-cpp/build/genia-adapter` | `270 / 9 fail / 759 unsupported` (unchanged; same 9 ids) |
| Fast CI selection | `uv run pytest -q -m "not slow and not loopback" -n 4 -rfEs` | 7204 passed, 60 skipped (pre-existing, none in Slice C), 231 failed: 82 harness + 148 host-local + 1 hygiene failure (below) |
| Hygiene gate | `tests/unit/test_host_binding_classification_p1_e.py` | the new `keys` test used `Env.set` as a harness injection → gate failed; fixed to `set_host(..., visibility="entry-only")`; gate passes (not weakened) |
| Focused regressions | C0, capability, parity-gate, R20 shared, function-resolution, optimizer, Slice A/B | 243 passed |
| Docs / MCP / LLM / lint | `tests/doc -n 2`; `gen_mcp_language_profile --check`; `validate_llm_instructions`; `ruff check .`; `git diff --check` | 397 passed/35 skipped; pass; pass; pass; clean |
| MkDocs | `mkdocs build --strict --site-dir <scratchpad>/site_out` | built, no warnings; no in-tree `site/` created |
Final host-local totals: 278 items, 148 fail, 130 pass. Not run: loopback partition, py3.14 matrix, Node/VS Code jobs, Genia MCP client acceptance (the Genia MCP server was unavailable in this session; repo scripts were used instead).
