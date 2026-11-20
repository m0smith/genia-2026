# #1334 integrated Model B verification — evidence (Claude, evidence collector)

Pinned subject: genia-2026 `main` = `5ed34effa430b07e95f536902373dbb9207c9007`, tree
`34ce7444a5d7081ad6db73493d97b0ace5f18029` (identical tree to reviewed PR #1336 head `ddccffa1…`).
Host: genia-cpp `main` `fef41e58dcd3b80aaedcac98c92943fcfbfd1945` (tree `f647b244…`), the merge of the
`1f33886606fc94dadab679ed56182a15ca503a4b` the repository workflows pin. Environment: Linux x86_64 VM, 4 CPUs,
CPython 3.12.3, uv 0.11.32; `uv.lock` is gitignored and was solved live on 2026-11-20 (sha256 in `logs/env.txt`).
Checkout was unshallowed (`git fetch --unshallow`) to match CI `fetch-depth: 0`; the first C++ spec run failed
`UNRESOLVABLE host-declared contract_revision` on the shallow clone and was re-run (recorded here, not hidden).

All commands ran from a clean worktree at the pinned SHA (`git status --porcelain` empty before and after).
No source, test, spec, timeout or doc file was modified. Evidence only lives under `.genia/process/issue-1334/`.

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest -n auto -q -p no:cacheprovider tests/unit/test_model_b_*.py` | 1097 passed, 0 failed |
| 2 | `uv run pytest -n auto -q -p no:cacheprovider -m "not loopback" --junitxml=…` (AGENTS.md partition 1) | **8390 passed, 61 skipped, 0 failed** (605.6 s) |
| 3 | `uv run pytest -n auto -q -p no:cacheprovider -m loopback --junitxml=…` (partition 2) | **32 passed, 0 failed** |
| 4 | `uv run python -m tools.spec_runner` (default, in-process) | total=1146 passed=1146 failed=0 invalid=0 |
| 5 | `uv run python -m tools.spec_runner --host-jobs 4 --host "python -m hosts.python.protocol_adapter" --evidence python-evidence.json` (strict external-protocol path) | total=1146 passed=1128 unsupported=18 failed/protocol_error/crash/timeout/invalid=0 |
| 6 | `tests/spec/test_python_protocol_adapter_parity_762.py` (`full_conformance`, ran inside #2) | passed (558.8 s) |
| 7 | cpp: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j4`; `ctest --test-dir build` | build exit 0; 7/7 CTest targets passed |
| 8 | `uv run python -m tools.spec_runner --host <cpp>/build/genia-adapter --evidence cpp-evidence.json` | total=1146 passed=295 **unsupported=851** failed/protocol_error/crash/timeout/invalid=0 |
| 9 | `uv run python -m tools.spec_runner.host_parity_gate --python-evidence … --cpp-evidence … --known-gaps spec/known_host_gaps.json` | exit 0; `closed_functions`, `default_open_functions`, `immutable_bindings`, `multi_file_eval` = KNOWN_GAP |
| 10 | `gen_mcp_language_profile.py --check`, `gen_function_docs.py --check`, `lint_doc.py --require-coverage`, `validate_llm_instructions.py`, `ruff check .`, `python -m tools.code_documentation --base-ref 7475646d…` | all exit 0 (code docs: 10545 records, 0 errors) |

"Strict" in the ticket is interpreted as the external E16-1 protocol conformance path (#5, #8) plus the
`full_conformance` proof (#6); the repository defines no separate `--strict` conformance flag.

SIGINT: `tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGINT]`
**passed** (1.07 s) in run #2. No recurrence of the excepted 60 s timeout at this SHA. The earlier exception
(#1250 comment 7051550231 / 7052161758) was not relied upon.

Skips in #2 (61, not PASS, reported separately): 34 "non-text evidence is verified by the unit tests", 18 WIT
component/wasmtime unavailable, 7 Node harness deps not installed (`npm ci` not run), 1 distilled-baseline, 1 "executed".
Hosted CI counts 64 skips (it has Node); the 7 Node-dependent checks were NOT executed locally.

Hosted evidence at the exact merge SHA (read from GitHub): CI [44829347636], Host parity gate [44829347594], Docs
[44829347775], Code documentation [44829347561], Validate LLM instructions [44829347552] all `success`.
Docker development environment does not trigger on push to main; its latest run [44825627267] is at tree-identical `ddccffa1` (success).
