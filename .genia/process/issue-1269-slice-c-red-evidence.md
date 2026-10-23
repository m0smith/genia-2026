# #1269 / #1250 — Model B Slice C TEST-only RED evidence

Process evidence only (not implemented-truth documentation). Authorization: [PR #1270 comment 6367339301](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6367339301) at planning SHA `a3bdc306bf6b4242027ad55be4ca7f5f89bfacb2`; decisions [6366547321](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6366547321).
Per-case data: `issue-1269-slice-c-red-per-case.json`. RED commits: `a60a5dfc` (cases, harness, staging), `38a94e84` (host-local tests), `5e408dd3` (gap links); this note's own commit is the review head.

## Inventory (all measured)
- 137 shared cases materialized mechanically from test plan §R6.D (74 eval, 37 error, 26 cli; 12 sibling `.genia` inputs). Re-parsing the YAML through the loader and comparing source, modules, argv, requires and expected streams against §R6.D: **0 differences**. 55 guards, 82 `default_open_functions` future cases (P5 and the six D5 rows included, Option B). Repeated-header-binder case and six G1 ids not created.
- Host-local: 212 pytest items in 6 files (`tests/unit/test_model_b_slice_c_{identity,consumers,ownership,repl_main,optimizer_ir,capability_evidence}.py`, helper `model_b_slice_c_support.py`): 103 pass (pin current behavior, `*_today`/guards/twins), 109 fail (approved Slice C behavior, genuine). HL-1 (legacy index only), HL-3, HL-4, HL-5, HL-6, HL-7, HL-8 (on/off equivalence), HL-9–HL-24 covered as scoped in each module docstring.
- **Blocked / not written:** ordered-record API and owner token (HL-1), pure key walker (HL-2), arm-key retention (`optim-keys-retained`, `d8-arms-retained-not-checked`, HL-8 part). No approved internal API name exists; writing them would invent an interface. Needs the GREEN design to name those internals. No skip/xfail placeholders were added. R7-D3 lambda/builtin targets are pinned as current Python behavior only.

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
