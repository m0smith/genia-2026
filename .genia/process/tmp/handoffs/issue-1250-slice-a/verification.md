# Slice A closeout verification evidence

Independent review source and dispositions: `maintainability-closeout.md`.
Independent audit request: `truth-audit-handoff.md`. These are implementer
verification records, not an independent truth-audit verdict.

## Environment and scope

Local Linux, Python 3.12.14, existing repository development environment.
Commands below have the exact prefix
`UV_CACHE_DIR=/workspace/.cache/uv uv run --no-sync` (abbreviated `uv` in tables).
A normal `uv run` first failed because its default home cache was read-only;
using the workspace cache reached a build dependency fetch blocked by the
network-isolated command. `--no-sync` uses the already-present pytest, xdist,
PyYAML, ruff, MkDocs and documentation-tool dependencies, not system pytest.
CI independently syncs dependencies and uses Python 3.14. No test assertion,
skip marker, timeout or documentation-size limit was weakened.

Initial git fetch failed in network isolation. The GitHub connector patch was
reconstructed and its exact tree hash verified against the PR head
`d66581ecc8d88124cb2a059666c60e9619572ad8`. A subsequent fetch with network
permission recovered the real history before any branch update. Only actual
correction commits descending from `45a1def2` were pushed; no reconstruction
commit is in the branch history.

Production/spec changes finish at `41455262`; test-method documentation at
`c02e969c`; final root-doc correction at `08a92c01`. `src` and `spec` tree hashes
are identical at `c02e969c` and `08a92c01`, recorded in the closeout. Some long
runs began before documentation condensation; their failed old-doc snapshots
are retained and distinguished below.

## Focused evidence

The historical parser/optimizer substitutions used exact baseline
`d85a56fa66d3369806ab9951b7572c79db98eba3` (local `origin/main`), with current
files restored immediately afterward.


| Command / observation | Result |
| --- | --- |
| `uv pytest -q tests/spec/test_model_b_slice_a.py` before N1 fix | 4 failed / 32 passed. |
| Same four `-k legacy-dotted` cases with `origin/main` parser, restored afterward | 4 passed / 32 deselected; historical behavior characterized directly. |
| `uv pytest -q tests/spec/test_model_b_slice_a.py tests/unit/test_model_b_slice_a.py` after N1 | 63 passed. |
| Direct-discovery regression `-k direct_server_discovery` before N2 | 18 failed / 27 deselected. |
| Slice A internals plus route/config/CORS suites after N2 | 98 passed. |
| Five N3 tests with `origin/main` optimizer, restored afterward | 4 failed / 1 passed. |
| N3 tests plus existing optimizer/TCO suite | 26 passed. |
| Both new shared list/map eval cases through existing load/execute/compare APIs | No comparison failures. |
| Final focused suite below | **258 passed** (139.61s). |

Final focused command:

```
uv pytest -q tests/spec/test_model_b_slice_a.py tests/unit/test_model_b_slice_a.py tests/unit/test_model_b_optimizer_regression.py tests/unit/test_ir.py tests/unit/test_ir_shared_spec_contract.py tests/spec/test_r20_open_functions_shared_specs.py tests/unit/test_optimizer.py tests/unit/test_tco.py tests/unit/test_server_route_binding.py tests/unit/test_server_config_binding.py tests/unit/test_server_cors_binding.py
```

## Documentation and tooling

- Initial docs/profile batch: **611 passed / 35 skipped / 1 failed** (390.41s).
  Failure: STATE word count 43069 exceeded the existing 43000 budget. This
  snapshot predates condensation and is not a docs PASS.
- Condensation initially removed one literal registry evidence fragment. Its
  two anchor checks failed (242 pass / 34 skip); the exact existing fragment
  was restored. Neither the registry nor its tests were weakened.
- Final STATE semantic/anchor/distillation gates: **244 passed / 34 skipped**
  (10.61s), STATE 42995 words under the unchanged limit.
- Final `uv pytest -n auto -q tests/doc tests/unit/test_doc_style_sync.py tests/unit/test_cheatsheet_*.py`:
  **518 passed / 35 skipped** (81.39s). The earlier batch's additional MCP
  profile/registry tests passed; no generated profile/golden change was needed.
- `uv python tools/gen_mcp_language_profile.py --check`: PASS.
- `uv python tools/gen_function_docs.py --check`: PASS, up to date.
- `uv python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage`:
  24 files / 286 doc strings / 0 errors / 0 warnings.
- `uv python -m tools.code_documentation --base-ref origin/main --inventory work/code-doc-inventory.json`:
  9571 records / 2804 legacy gaps / 1 classified exclusion / 0 errors. The
  first run identified two missing docstrings on new test-spy methods; fixed
  directly, without adding baseline debt.
- `uv ruff check .`: PASS. `git diff --check`: PASS.
- Initial strict MkDocs build at `c02e969c`: PASS. A concurrent final attempt
  overlapped documentation tests resetting `.tmp/mkdocs-docs`, producing a
  missing staged-file error. This was a local staging race, not hidden as a
  passing build. Rerun after docs tests completed: **PASS**, strict build in
  88.26s, generated output `/tmp/genia-1250-site-final` outside source scans.

## C++

See the exact 38-case ledger in
`.genia/process/issue-1250-slice-a-cpp-evidence.md`: **5 PASS / 33 UNSUPPORTED**,
no failure-class outcomes. Existing R16 APIs, 10-second request timeout; no C++
source or claim changed. The binary's ancestor pin and uncertified source-build
provenance preclude current pinned conformance. Optional host-parity success
cannot waive required syntax gaps.

## Shared R16

`uv python -m tools.spec_runner` completed: **total=869 passed=869 failed=0
invalid=0**. This is the whole in-process reference suite (not an external-host
pin claim), including all original cases, seven N1 characterization/restriction
cases and two N3 eval twins. The source/spec trees stayed identical through
`08a92c01`; later edits are process evidence only.

## Loopback partition

Every command selects the complete loopback partition, not a subset. Networking
permission was enabled for permitted runs; failures were not converted to skips.

- Initial isolated `uv pytest -n auto -q -m loopback`: **29 failed / 2 passed**,
  socket permission unavailable. This is not a passing regression partition.
- Permitted same command under concurrent verification: **1 failed / 30 passed**
  (37.75s), upstream-failure proving-case connection timeout. That single test
  passed in isolation (1.44s); an isolated pass is not a partition PASS.
- Permitted `--dist loadgroup` attempt: **1 failed / 30 passed** (36.96s), ants
  HTTP demo startup/request failure. No timeout or assertion changed.
- Final permitted serial selection `uv pytest -n0 -q -m loopback`:
  **31 passed / 7111 deselected** (16.61s). The deselected tests belong to the
  other partition, not skipped loopback cases. Running serially avoids xdist
  port/startup contention while retaining the entire partition.

## CI status pinned to source/truth-doc head

All six workflows at `08a92c010ccef8b95fd67022622d41356bd1a749` completed
**successfully**:

| Workflow | Run |
| --- | --- |
| CI | https://github.com/m0smith/genia-2026/actions/runs/39271785994 |
| Docs | https://github.com/m0smith/genia-2026/actions/runs/39271786326 |
| Code documentation | https://github.com/m0smith/genia-2026/actions/runs/39271786292 |
| Validate LLM instructions | https://github.com/m0smith/genia-2026/actions/runs/39271785511 |
| Host parity gate | https://github.com/m0smith/genia-2026/actions/runs/39271785728 |
| Docker development environment | https://github.com/m0smith/genia-2026/actions/runs/39271786119 |

The main CI fast-test job (Python 3.14) independently reports **6958 passed /
63 skipped** for `not slow and not loopback` (530.38s), **31 passed** for the
non-slow loopback partition (8.32s), and **869/869** shared R16. Its official
MCP SDK acceptance, cheatsheet, generated-doc/coverage and extension jobs also
passed. This CI selection excludes slow tests; it is not an assertion that a
local all-tests partition passed.

Earlier `c02e969c` CI stopped after the STATE word-budget failure (417 pass /
34 skip / 1 fail); later steps in that failed fast-test job were skipped, not
counted as successful. It is superseded by the green `08a92c01` source head.
The old `45a1def2` workflows were also all green, but are historical evidence,
not coverage of the corrections.

The final handoff commit changes process evidence only. Any newly queued CI
for that artifact-only head is distinct from the completed source-head runs
above; pending is never reported as PASS.

## Completed local non-loopback partition and bounded triage

`uv pytest -n auto -q -m "not loopback"` completed, without early stopping:
**22 failed / 7026 passed / 63 skipped** (2005.04s; 33m25s). This is a completed
failed full partition, never reported as PASS. It began before final doc
condensation: its STATE module retained 43069 words. That one failure was fixed
and its final 244-test semantic/anchor/distillation rerun passed.

The other 21 failures are MCP host tests. One raw traceback explicitly reports
read-only `/home/agent/.cache/uv`; the client fixture intentionally retains only
HOME/LOGNAME/PATH/SHELL/TERM/USER, so the outer UV_CACHE_DIR does not reach its uv
launcher. Another test's local socket-creation probe gets sandbox PermissionError.
Most remaining failures close stdout before the launch-ready frame. No MCP
launcher, client allowlist, test timeout or assertion was changed to address this.

Bounded rerun of exactly those 21 MCP node IDs, `uv run --no-sync pytest -n0 -q`:
**20 passed / 1 failed** (93.76s), with networking permission and a task-only PATH
wrapper that execs the real uv binary with `--cache-dir /workspace/.cache/uv`
and forwards every caller argument. HOME was not reassigned; the wrapper and
rerun helper remain scratch files, not repository changes. This is explicit
test-host cache configuration, not an unmodified-environment/full-suite PASS.

Remaining local case:
`tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_discover_probe_launch_followed_by_a_session_launch_leaves_nothing_behind`.
Its original 60-second cleanup wait reports "a launch left processes behind".
The same unmodified case is explicitly PASSED in the green `08a92c01` Linux CI
fast-test job. The local discrepancy remains an audit input, not a reason to
weaken process-identity/reaping assertions or claim a full local regression PASS.
Integration owner m0smith retains this verification risk under #1250 / existing
R28-H37 two-launch evidence, until it is explained/resolved in the applicable
host environment with the original assertion intact.

Exact failed nodes from the completed full partition:

- `tests/doc/test_state_distillation_gates.py::test_state_is_within_the_ratified_size_bounds`
- `tests/unit/test_r28_mcp_conformance_lifecycle.py::test_sighup_to_the_client_launched_process_stops_the_chain_and_cleans_up`
- `tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_discover_probe_launch_followed_by_a_session_launch_leaves_nothing_behind`
- `tests/unit/test_r28_mcp_entrypoint.py::test_the_entrypoint_works_from_any_working_directory`
- `tests/unit/test_r28_mcp_run_worker.py::test_runtime_stubs_deny_process_creation_and_sockets_and_are_restored`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_the_configured_command_discovers_exactly_the_three_tools_and_nothing_else`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_the_native_application_is_the_server_not_a_python_implementation`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_stdout_carries_only_json_rpc_frames_and_stderr_is_silent`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_hostile_program_output_cannot_corrupt_protocol_framing`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_invalid_source_is_diagnosed_by_parse_then_repaired_then_run`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_a_program_sees_no_argv_stdin_or_inherited_state`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_no_process_in_the_chain_holds_a_listening_socket`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_the_configured_server_denies_every_prohibited_authority_without_effect`
- `tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_client_that_closes_both_streams_mid_run_leaves_no_survivors`
- `tests/unit/test_r28_mcp_stdio_lifecycle.py::test_closing_stdin_mid_run_lets_the_run_finish_then_exits`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_each_launch_is_independent_and_stateless`
- `tests/unit/test_r28_mcp_stdio_lifecycle.py::test_cancellation_still_reaps_the_worker_through_the_wrapper_chain`
- `tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGTERM]`
- `tests/unit/test_r28_mcp_stdio_launch.py::test_a_client_can_launch_twice_in_a_row_and_get_the_same_answers`
- `tests/unit/test_r28_mcp_stdio_lifecycle.py::test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up[SIGINT]`
- `tests/unit/test_r28_mcp_stdio_lifecycle.py::test_closing_stdin_while_idle_exits_cleanly_and_leaves_nothing`
- `tests/unit/test_r28_mcp_stdio_lifecycle.py::test_sigterm_to_the_host_reaps_the_worker_and_removes_its_directory`

A read-only diagnostic invocation of that unchanged two-launch test function
also failed its original cleanup assertion. Captured identities after the
60-second wait: one process was gone; the other had the same start token,
state **Z (zombie)** and parent **PID 1**, whose program is `tail` in this
managed environment. No running-versus-zombie distinction was used to turn the
assertion into PASS: the fixture deliberately counts unreaped zombies as reap
failures. This narrows the local risk to a concrete orphan-reaping discrepancy;
it does not self-certify a fix or erase the failing result. The diagnostic
script/log and the cache-only wrapper are included in the downloadable evidence
packet, not committed as production/test changes.

## Handoff readiness

**Ready for independent behavioral/documentation truth audit with the explicit
validation limitations above; not a truth-audit PASS or merge approval.**
All N1–N3 corrections and N4–N9 ownership/reporting dispositions are concrete;
focused/shared/doc/tool checks pass, the loopback partition passes serially,
and all six frozen-source-head CI workflows pass. The completed local
non-loopback partition does not pass, and the remaining local MCP reap assertion
is still a recorded risk despite the passing CI case. C++ remains unsupported
for the listed cases and not current-pinned by the local binary.

No independent audit was performed, no PR merge or issue closure was made, and
no Slice B execution work began. Later artifact-only CI must be reported at its
own status, not inherited as PASS from `08a92c01`.
