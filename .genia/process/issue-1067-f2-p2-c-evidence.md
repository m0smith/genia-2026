# F2/P2-C evidence — environment topology (issue #1067, tracker #1229)

Python-host implementation of contract §16.1/§16.6 and A3. Stacked on the P2-B red-test branch
(`issue-1067-f2-p2-b-red-tests`, PR #1235). **Not releasable alone**: P2-D (consumers, reflection,
`empty_env`) and P2-E (module fallback, strict switch) are not delivered; the branch must not be merged
to `main` before them. #1067, #1220, #1221, #1229, #1230 and #1238 stay open.

## Provenance

- Approval: [D1–D6 with A1–A3](https://github.com/m0smith/genia-2026/issues/1067#issuecomment-6171848719).
- Red-test SHA (all cites): `163f5160f6486cb56fc78211edd0afc261a13c18`; P2-B head `24cbe008`.
- Implementation commits on `claude/tender-dijkstra-vk788s`: `976bb2a5` (topology), `8e405889` (class-level defaults, sink readers, seams,
  supplemental tests, instrument repairs, baseline shrink), `b0c50c9d` (review documentation), `159c9889` (documentation sync); a final
  documentation commit adds this record and the STATE interim-state wording.
- MCP language-knowledge impact: none (host-internal Python; no language fact, `semantic_facts.json` or profile change;
  `tools/gen_mcp_language_profile.py --check` passes).

## What P2-C delivers

`Env.create_entry_scope()` (once per runtime, only on R; E is a child of R with parent rebinding), registered-entry accessors,
runtime-owned routing (`is_runtime_owned`, static prelude manifest from autoload-target files captured before pruning,
write-through for runtime-owned names, rejection of pruned names), registered-entry `set_host*`/`register_host_autoload` rules, the single
construction helper `make_program_env(..., prepare=)`, and migration of the 13 program sites. Class-level immutable defaults keep ordinary
frames cheap (best-of-7, ns/`Env(parent)`: P1 586–620, instance attributes 668, class defaults 624–634; single noisy machine, not a benchmark claim).

## The 75 P2-C obligations

All 75 pass (`P2-C still-red 0 / green 75` against the per-test table). Two of them needed documented, independently reviewed instrument repairs
to `tests/unit/test_f2_p2_b_hosts.py::test_B8_B_all_13_program_construction_paths_register_entry`; both repaired cases fail on the P1 tree with
`program still evaluated in shared R=E` and pass now:

| Case | Original defect (test, not implementation) | Repair (assertion unchanged) |
|---|---|---|
| `[serve]` | instruments `run_source`; serve evaluates via `Evaluator.eval_program`, so `seen` stayed empty | also wrap `Evaluator.eval_program` |
| `[pipe]` | source `it` is not a valid pipe stage (exit 1 on any topology) | source `map((line) -> line)` |
| all | trusted prelude autoload (`internal_access=True`) runs in R by design and was recorded as a program Env | do not record `internal_access` evaluations |

Beyond the 75: 54 D/E-assigned cases already pass (e.g. strict module reads: modules cannot see E) and `tests/unit/test_f2_p2_c_topology.py` adds 8.

## Remaining expected reds (50 P2-B cases; zero P2-C)

37 P2-D (reflection, `eval` base, REPL `:env`, debugger, discovery, #1220 catalogue, #1221 wrong-accessor matrix), 13 P2-E (fallback/strict/events).

## Regression evidence (initial failures preserved)

| Run | Result |
|---|---|
| Baseline P2-B reds on `24cbe008` | 179 failed (as intended) |
| First full non-loopback after topology + migration (`976bb2a5`, P2-B suites excluded) | **36 failed**, 6666 passed, 60 skipped, 469.7s. Groups: 10 MCP protected-worker fixture (entry-only carrier injected during pruning, which §16.6.1 forbids), 5 native/serve seam (patched `make_global_env`; sinks read from E), 4 host-binding placement, 3 R20 spec + 1 parity (reflection), 4 debugger globals, 3 REPL `:env`, 1 test-mode doc, 2 P2-A, 3 other; plus 1 load-sensitive lifecycle SIGINT test that passed on rerun |
| Rerun of those 36 files after fixes | 16 failed, 395 passed (3 new P2-A sink flips, rest P2-D/E) |
| Final non-loopback (`159c9889`, P2-B suites included) | **63 failed**, 6826 passed, 60 skipped, 431.9s = 50 P2-B reds + 13 existing tests below |
| Final loopback | 31 passed |
| Shared specs (`tools.spec_runner`) | 819/822 (was 822/822): 3 R20 reflection specs, P2-D |
| ruff, maintained-code documentation (0 errors, baseline 2840→2827), function-reference/prelude-doc/MCP-profile checks, `tests/doc` | pass (`tests/doc`: 395 passed, 35 skipped) |

No retry cleared any failure silently. Not run: Node/VS Code, official-SDK job, C++.

## Classification of the 13 remaining existing-test failures (all approved behavior awaiting a later slice)

| Tests | Cause | Contract | Green-making action |
|---|---|---|---|
| `test_r20_open_functions_shared_specs` ×3, `test_python_protocol_adapter_parity_762` (count 819 vs 822) | `doc`/`meta`/`help` of entry names read R | §16.2 | P2-D scope-bound reflection (also turns parity green) |
| `test_interpreter_test_mode::…doc_metadata…` | same, inside native test | §16.2 | P2-D |
| `test_debug_stdio` ×4 | debugger globals are the unit scope (E/M/R) | §16.6.1, D3 | P2-D debugger globals; update the four shared-root expectations |
| `test_repl_env_characterization` ×2, P2-A REPL ×1 | `:env` lists E only | §16.1.4, §8 | P2-D `:env` (E + `entry_declared_runtime_owned`); update expectations |
| P2-A `test_native_discovery_…` | module reads entry-only fixture | §11 | P2-E fallback |

Deviation recorded (audit F-3): the sink readers (`_emit_error`, `_write_stdout`, `_write_stderr`) now read the runtime-owned sink — the only consumer touched,
because E-resident reads would otherwise silently route captured output to the process streams. This flipped three P2-A cases scheduled for P2-D (rewritten
in place, commented); three P2-B B10 sink cases turned green early. Seam edits (patching `make_program_env`), P1-E placement updates and the MCP fixture change
(carrier installed on the env returned by `genia.make_program_env`, call style pinned) preserve each original property.

## Interim-state warning (audit F-1)

On `make_program_env` host paths until P2-D/E land: `doc`/`meta`/`help` of entry names fail, REPL `:env` and debugger globals changed, and modules reading entry
globals raise `NameError` without the warning fallback. STATE §9 states this; do not merge to `main` before P2-D/E.

## Reviews

- Maintainability: **PASS WITH NON-BLOCKING FINDINGS** (`.genia/process/issue-1067-f2-p2-c-maintainability-review.md`); N1–N3 tracked in #1238.
- Independent truth audit (read-only): **PASS WITH FINDINGS**, no blocking defect. F-1 settled by STATE wording and this section; F-2 by the #1238 link; F-3 recorded;
  F-4 confirmed here (the spec runner and final run show the 3 R20 specs and the parity case failing, all reflection).

## #1226 dogfooding observation (optional pilot; not a gate)

Supporting computation: a Python helper that parses the P2-B evidence Markdown table, runs pytest and compares failures to the slice column (re-run several times).
Classification: **D** (host tooling remains preferable) for the helper as a whole — it shells out to pytest and reads repository files, authority the restricted
`genia_run` worker does not have (the full host's `execution.process` was not exercised: **E** for that part). One fragment was tried: the table filter
("rows whose last cell is `P2-C`, return ids") in `genia_run` on a **three-row sample** with one non-row line. After four failed/incorrect attempts
(argument order of `starts_with`, `first` returning an Option, no regex) the fifth returned `["| `a::t1`", "| `a::t3`"]` — the right rows, but with a leading `| `
the Python helper does not keep. This is **B** for that fragment (works, needs library knowledge, no regex), and says nothing about equivalence for the
179-row table, its multi-pipe test ids, or the pytest orchestration. Cost: five `genia_run` calls, review cost unmeasured. No gap ticket; duplicates nothing in R39.
