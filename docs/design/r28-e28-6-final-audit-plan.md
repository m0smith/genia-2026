# R28 E28-6 — Final audit plan (pre-flight) and gate record

Status: **Pre-flight and gate record for E28-6 (final audit: section 10)** (issue #707, epic #700). `GENIA_STATE.md` is final
authority for implemented behavior. This document is the plan the final audit follows and, in section 7,
the recorded outcome. It is a release-evidence artifact: the release page `docs/releases/R28.md` distills
it. Findings are cited `[H##]` (ledger `docs/analysis/r28-host-dependency-inventory.md`), matrix rows as
`M:<id>` (`docs/mcp/conformance-matrix.md`), contract sections as `C§` (`docs/design/r28-genia-mcp-contract-threat-model.md`).

## 1. Verified starting state (`main` at `f1c04f6`)

E28-0 through E28-5 are merged (E28-3 PR #1073, E28-4 PR #1080, E28-5 PR #1081; issues #704, #705, #706
closed). Implemented on the Python reference host: native `apps/mcp/mcp.genia`, local stdio, the
checked-in repository-root `.mcp.json`, exactly `genia_capabilities` / `genia_parse` / `genia_run`, governed
disposable workers, cancellation, limits, authority restriction, protected-value handling, the official
TypeScript client acceptance harness (CI job), and the E28-5 matrix. #1078 (the 0.5 s spec-runner adapter
timeout) is open infrastructure work, labeled "not R28 scope"; it is unrelated and stays untouched here.

## 2. The release rule

R28 is **Complete** only when docs, tests, capability claims, examples, and `GENIA_STATE.md` agree **and**
contract section 12.2 is satisfied by an authentic VS Code + GitHub Copilot run (C§12: "R28 is not complete
until the native `mcp.genia` server is proven as a local development tool from a supported VS Code/GitHub
Copilot agent client"). Official-SDK runs, the Inspector, unit tests, documentation reading, or reasoning
that `.mcp.json` should work do not satisfy it. H36 (legacy `initialize`) was decided by the first such run (2026-10-05, failed at `initialize`; section 8).

## 3. Release gates

| Gate | Requirement | Status | Evidence / blocker |
|---|---|---|---|
| G1 | Exactly three tools, no resources/prompts/HTTP | PASS | M:D1–D6, `client::test_the_official_client_completes_the_acceptance_scenario`, Inspector run (section 5) |
| G2 | Authentic VS Code + Copilot run, evidence recorded (C§12.2, issue #707 hard gate) | **PASS** | Run 3 (owner, macOS, VS Code 1.138.0, Copilot Chat 0.66.0, revision `0ff058a2`) passed; runs 1 (failed at `initialize`) and 2 (failed at `genia_run`) preserved. `docs/mcp/acceptance/vscode-copilot-evidence.md`; items 1-8 mapped there; gate `tests/unit/test_r28_release_gate.py` |
| G3 | "At least one mainstream MCP host/client can connect over stdio" (E28-4 acceptance, #705) and the epic's "ordinary MCP client" criterion | **PASS** | authentic VS Code + GitHub Copilot run 3; also the official TypeScript client (all negotiation paths) and Inspector 2.9.0 |
| G4 | H36 disposition | **PASS (closed by run 2)** | contract A5 implemented natively; authentic VS Code negotiated `2025-11-25` and discovered the three tools (runs 2 and 3) |
| G5 | Runnable demo, no repository-internal knowledge | PASS | `docs/mcp/demo.md`, `examples/mcp/`, `tests/unit/test_r28_mcp_demo.py`, clean-clone run (section 5) |
| G6 | Packaging/publishing and executable entrypoint | PASS | Decision section 6: repository launcher plus `scripts/genia-mcp`; no new CLI contract, no registry/PyPI/npm claim |
| G7 | MCP reference, security/deployment limitations, host-portability statement | PASS | `docs/mcp/reference.md`, `docs/mcp/security-and-deployment.md`, `docs/mcp/host-portability.md` |
| G8 | Every non-closed ledger entry dispositioned | **PASS** | section 4 and section 10: H39, H45, H47, H48 and the accepted-limitation entries closed; follow-up candidates H05-H09, H15, H24, H26 stay open with a recorded disposition (parking lot, not ticketed) |
| G9 | Docs, state, roadmap tell the truth | **PASS** | R28 Complete in `GENIA_STATE.md` 9.49, the release page, the releases index, and the roadmaps; the gate test accepts a completion claim only when the latest run passes |
| G10 | Full regression, matrix, namespace granted and denied | **PASS** | `docs/releases/R28.md` verification table and section 10 (final audit results) |
| G11 | Skeptical audit | PASS with the recorded findings | section 7 |
| G12 | Agent-guidance update (`LLM_CONTRACT.md` prefers the MCP, C§12.3) | **PASS** | done after the acceptance evidence: `docs/ai/LLM_CONTRACT.md` and `.github/copilot-instructions.md` (`tools/validate_llm_instructions.py` clean) |
| G13 | Inventory of agent bypasses/fallbacks (C§12.3) | PASS (inventory), observations H42/H43 | section 7.3 |

Decision rule: any BLOCKER above means **NOT READY TO CLOSE**. There is no middle category. (As of section 10 no gate is a blocker.)

## 4. Ledger audit: every non-closed entry (22 at the release-candidate audit; final state in section 10)

Dispositions: *accepted R28 limitation*, *post-R28 follow-up candidate* (recorded in the ledger and
`docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and
the shape in `docs/process/08-roadmap-ticketing.md`), *held open by G2*. No entry is deleted, none is closed
merely because this is the last phase, and no release number is assigned. The full text of each
disposition is in the ledger; this is the table.

| Entry | Final disposition | Why |
|---|---|---|
| H01 native-owned protocol | **closed** (standing constraint satisfied) | `arch` tests guard it for the whole release; nothing left to implement |
| H04 hard deadline/kill/OS isolation | accepted R28 limitation | implemented behind the host boundary; OS layer is best effort and never claimed as a sandbox (M:A21, A22, T1–T4) |
| H05 no bootstrap for `execution.process` | follow-up candidate | host provisions the capability explicitly; evidence preserved for a general capability |
| H06 child stdin unavailable | follow-up candidate | supervisor owns stdin for its worker only |
| H07 argv cannot carry the source | follow-up candidate (evidence for H06) | solved by stdin pipe in the supervisor |
| H08 blocking call cannot be cancelled | follow-up candidate | solved by supervisor plus multiplexer; no Genia-level cancellation exists |
| H09 no bounded stdin reader | follow-up candidate | solved by the 8 MiB multiplexer back-pressure (limitation recorded) |
| H10 no build identity facility | accepted R28 limitation | launcher injects `git rev-parse HEAD`; a clone without `.git`/`git` fails closed (documented prerequisite) |
| H15 no Genia process exit status | follow-up candidate | one documented workaround in `mcp.genia` (`reject_start`) |
| H17 Genia source cannot reach the parser | accepted R28 limitation | one explicit host capability; no builtin added |
| H18 no code-point helpers | accepted R28 limitation | parse diagnostics are a character offset only (no line/column) |
| H20 capability provisioning needs a host bootstrap | accepted R28 limitation | `serve(revision, host)` is the explicit boundary |
| H24 no restricted-authority evaluation profile | follow-up candidate | default-deny classification with a drift test (M:A18) |
| H26 `execution.process` cannot launch the worker | follow-up candidate | the supervisor; generalizable with H05–H08 |
| H27 cancellation vs. single-threaded stdin loop | accepted R28 limitation | multiplexer plus native predicate; best effort above 8 MiB pending input (documented) |
| H28 shell stages bypass pruning | accepted R28 limitation | static policy plus runtime stub plus optional namespace, asserted at each layer (M:A10) |
| H29 no implicit `main` vs `-c` dispatch | accepted R28 limitation | contract wins; difference pinned (M:R9) |
| H30 rendering cannot be bounded incrementally | accepted R28 limitation | deadline, `RLIMIT_AS`, post-check (M:L8) |
| H32 debug renderer exposes host representations | accepted R28 limitation | no contract requirement violated (section 7.2); values are canonical debug text, not a portable serialization |
| H36 legacy-`initialize` clients | **closed (run 2)** | amendment A5 implemented; authentic VS Code negotiated, listed three tools, and parsed |
| H39 VS Code/Copilot acceptance | **closed (run 3 PASS)** | run 1 failed at `initialize`; run 2 failed at `genia_run` (H47); run 3 passed (G2/G3) |
| H47 governed worker does not run on macOS | **closed (run 3 PASS; full macOS suite 1141 passed)** | platform-aware limits, portable test backend; macOS has no address-space bound and no namespace (accepted) |
| H40 UTF-16 surrogate escapes | accepted R28 limitation | contract requires no preservation of non-scalar code units; fails closed; no new string semantics (section 7.2) |

New in this phase: H42 (no runtime diagnostic text for agents), H43 (the platform evidence is Linux only; macOS run 1 proved only discovery, launcher start, and stdio JSON-RPC transport). Both are accepted limitations (section 7.3). Added after run 1: H44 (gate schema; closed), H45 (post-`initialize` VS Code behavior inferred; open), H46 (run 1 revision not recorded; accepted).

## 5. Work completed in this phase

- **Demo:** `examples/mcp/validated_records.genia` and `validated_records_broken.genia` (existing Genia
  only), the public walkthrough `docs/mcp/demo.md`, and `tests/unit/test_r28_mcp_demo.py` (parse failure at
  a useful offset, repair, run, exact value/stdout/stderr, equality with direct evaluation, and a guard that
  the documented source equals the example files).
- **Entrypoint:** `scripts/genia-mcp` (start from any working directory); tests in `test_r28_mcp_entrypoint.py`.
- **Documentation:** reference, security and deployment, host portability, the demo, the VS Code/Copilot
  procedure and evidence template, the release page (Release Candidate at that time), ledger and roadmap
  updates (R28 In Progress at that time; R20 follow-up #1067 stays after R28 and before R29).
- **Gate test:** `tests/unit/test_r28_release_gate.py`: any document claiming R28 Complete while the
  VS Code/Copilot evidence record is not fully executed fails; so the owner's later evidence commit is the
  only change needed before the completion synchronization.
- **Inspector (official, v2.9.0, CLI mode):** executed here against `.mcp.json`. With the default
  (`legacy`) era it fails with `Method not found`; with `--protocol-era auto` it lists exactly the three
  tools and runs `genia_run`. This is *manually executed, not automated in CI*; the web UI and TUI were not
  executed. It is additional H36 evidence, not mainstream-host acceptance.
- **Clean clone:** the demo and entrypoint were run from a fresh `git clone` of the branch in a temporary
  directory (results in the release page).

## 6. Packaging and entrypoint decision

The existing surface is the `.mcp.json` command `uv run --no-project --no-python-downloads python
hosts/python/mcp_launch.py`. Options considered: (a) a console script or wheel entry; (b) a `genia mcp`
subcommand; (c) a launcher script; (d) registry metadata. (a)/(b) would package `hosts/` and `apps/` into the
wheel, replace the git-derived `contract_revision` (H10) with a different identity source, and add a public
CLI command, all contract-level changes outside E28-6. (d) would advertise a package that does not exist.
**Decision:** keep the repository checkout as the supported distribution; add `scripts/genia-mcp`, a POSIX
shell wrapper with no arguments that works from any directory (it only resolves the repository root and
starts the same launcher), so a client or Inspector configuration needs one absolute path instead of
knowledge of the module layout. `pyproject.toml`, the `genia` CLI, and the wheel are unchanged. No PyPI,
npm, registry, or container publication is claimed.

## 7. Outcome

### 7.1 Decision

**NOT READY TO CLOSE.** Blockers: G2 (the authentic VS Code + GitHub Copilot run, including the negotiation
path observed), G3 (mainstream-host acceptance for E28-4/epic), G4 (H36 decided by that evidence), and G12
(agent-guidance update that the contract permits only after the evidence). Exact owner action:
`docs/mcp/vscode-copilot-acceptance.md` (a short deterministic procedure) producing the filled record
`docs/mcp/acceptance/vscode-copilot-evidence.md`. Then, if the host negotiated the modern era, only the
completion synchronization remains (listed in the release page); if it sent legacy `initialize`, stop and
decide on the ledger's amendment proposal. (Superseded by section 8: the host did send `initialize`.)

### 7.2 Dispositions that needed an argument

- **H32:** C§2.5 says the value is "rendered by the existing canonical debug renderer; it is not claimed to be
  lossless JSON or a new Genia serialization", so host text in a callable's rendering contradicts no
  requirement. E28-5 proved a captured protected value is not rendered, and no deterministic comparison uses
  callable values. Accepted limitation; the docs state values are debug-rendered text, not a portable format.
- **H40:** C§2.4/A2 requires invalid Unicode to be rejected at the JSON-RPC boundary and says nothing
  requiring preservation of UTF-16 surrogate code units produced by string escapes. The path fails closed
  (`internal_error`, fixed message, no leak) or merges a valid pair into one scalar. This is a host
  string-representation limitation, not a contract violation; no Genia string semantics are changed. A
  language-level ticket would need its own pre-flight and owner approval; none is created.

### 7.3 Findings of this phase

- **H42:** `runtime_error` carries only a fixed message, and parse errors only a character offset, so an agent
  cannot learn *why* a program failed from MCP alone and falls back to direct Python/CLI evaluation (an
  agent bypass in the sense of C§12.3). By design (C§2.2, C§6 forbid raw diagnostics); the demo keeps its
  diagnostics inside the program's own value. Accepted limitation; a normalized diagnostic facility would
  be a follow-up candidate.
- **H43:** the checked evidence is Linux only (`/proc`-based lifecycle tests, `unshare`, a Linux CI host);
  macOS is unverified. Earlier text said "POSIX (Linux or macOS)". The docs now say Linux verified, macOS
  not verified, Windows unsupported.

## 8. Skeptical audit (assume the release claim is wrong)

| Question | Result |
|---|---|
| Can a fresh user run this? Does the command work from a clean checkout? | Yes: a fresh `git clone` of the branch started the launcher, answered `tools/list` through `scripts/genia-mcp` from another directory, and ran the demo end to end; the demo and entrypoint tests pass in the clone |
| Does the mainstream host connect? | **Unknown: never executed (G2).** SDK and Inspector connect only with `auto`; their default fails |
| Exactly three tools? | Yes (M:D1–D6; SDK; Inspector) |
| Can invalid code be parsed and repaired? Does the demo execute? Only implemented Genia? | Yes to all; `demo` tests; equality with direct evaluation; no denied name used |
| Are diagnostics useful? | The parse offset points at the defect line (tested); a failed run gives no text (H42, accepted) |
| Does any output cross framing? Can prohibited authority be reached? Protected leaks? | No (M:C-F, A1–A22, S1–S10) |
| Are we relying on the namespace while claiming otherwise? | No: capabilities never mention it; identical outcomes granted and denied |
| Limits in characters instead of UTF-8 bytes? | No (M:L1–L9, multibyte boundaries) |
| Workers or temp directories left behind? | Only the documented SIGKILL case (M:X9, Y1–Y10; SIGHUP defect fixed in E28-5) |
| Does client negotiation work without undocumented configuration? | **Yes since amendment A5**: the SDK default, `auto`, and a pin all connect, and authentic VS Code negotiates `2025-11-25` (H36 closed) |
| Python implementation called portable? | No: `portable_mcp_implementation: false`, the portability statement, no C++ claim |
| Claiming Inspector, VS Code, Copilot, Windows, C++, HTTP, resources, prompts without evidence? | No. Inspector is labeled manual CLI only; VS Code/Copilot rests on the recorded authentic run 3 (two fields labeled as protocol-level evidence); macOS verification is owner-run and labeled not in CI; Windows, C++, HTTP, resources, prompts are not claimed |
| Release doc ahead of `GENIA_STATE.md`? `GENIA_STATE.md` ahead of implementation? | No: every status says R28 is Complete only because run 3 passed; the gate test accepts a completion claim only when the latest run passes; STATE 9.49 describes only what exists |
| Roadmap truthful? Ledger dispositioned? #1078 separate? #1067 after R28 and before R29? | Yes (stale "E28-4/E28-5 in progress" statuses corrected; 24 dispositions; #1078 untouched; ordering asserted by `gate::test_the_r20_followup_stays_after_r28_and_before_r29`) |
| Machine-specific or secret configuration checked in? | No (`.mcp.json` unchanged; the evidence-record gate rejects secrets and personal paths) |

New findings: H42 and H43 (accepted limitations). No new defect required code changes in this phase.

## 8. Amendment A5 record (after authentic run 1, 2026-10-05)

Run 1 (VS Code 1.138.0, Copilot Chat 0.66.0, macOS) failed at `initialize`: `protocolVersion: "2025-11-25"`
answered `-32601`; tool discovery was never reached. Pre-flight: `docs/design/r28-e28-6-protocol-compat-preflight.md`
(GO). Contract amendment A5 (section 18) serves exactly `2026-07-28` and `2025-11-25`; implemented only in
`apps/mcp/mcp.genia` with one process-local state bit; no tool, resource, prompt, transport, authority, or
limit added; client capabilities grant nothing; no Python host change. Evidence: matrix section K and the
official client and Inspector runs on both paths. Gate: the release test now distinguishes not executed,
executed-failed, and executed-passed runs; the latest run governs; the allowed negotiation paths are derived
from the amended contract.

**Decision at that time: NOT READY TO CLOSE — awaiting post-amendment authentic VS Code/Copilot acceptance (run 2). (Superseded by section 10.)**
Unchanged blockers: G2, G3, G4 (verification), G12. New open item: H45 (VS Code behavior after `initialize`
is inferred). Owner procedure: `docs/mcp/vscode-copilot-acceptance.md`.

## 9. Run 2 and the macOS finding (after authentic run 2, 2026-10-05)

Run 2 on revision `66b50594` proved amendment A5 in authentic VS Code (H36 closed) and failed at `genia_run`:
the governed worker did not run on macOS, and the macOS test suite showed Linux-only test infrastructure (`/proc`).
Pre-flight `docs/design/r28-e28-6-macos-execution-preflight.md` (GO, conditional on the Mac probe confirming
`RLIMIT_AS`). Repair: platform-aware limits (four POSIX limits fail closed everywhere; `RLIMIT_AS` fails closed
except on Darwin), a portable process-inspection test backend, Linux-only namespace tests skipped elsewhere,
`tools/mcp_diagnostics/worker_probe.py`, and a development-only worker diagnostic. No contract change was needed.

**Decision at that time: NOT READY TO CLOSE — awaiting successful macOS governed-execution verification and authentic VS
Code/Copilot acceptance (run 3).** Open items: G2, G3, G12, H39, H47 (macOS verification), H45.

## 10. Final audit and completion decision (after authentic run 3)

**Evidence.** Authentic VS Code + GitHub Copilot run 3 (owner, macOS, VS Code 1.138.0, Copilot Chat 0.66.0, revision
`0ff058a28e488275f344ee24bbd12d072bd3e9cc`) **PASSED**: `initialize` negotiated `2025-11-25`; `Discovered 3 tools`;
`genia_capabilities` (exactly the three tools, profile `source-only-isolated-v1`, 5000 ms, all authority flags false);
broken demo through `genia_parse` -> `parse_error`, phase `parse`, offset 171; corrected demo -> `parsed` with AST;
corrected demo through Copilot Agent `genia_run` -> `ok`/`completed`, exit 0, stdout `"2\n"`, stderr
`"record_validation_failed\nrecord_validation_failed\n"`, rendered value with Ada, Edsger and two structured diagnostics, channels
separate; after the server stopped no `mcp_launch`/`mcp_host`/`mcp_worker` process remained. Recorded as `evidence run=3`.

**Contract 12.2 mapped against the evidence** (each item verified, not assumed; full mapping in the evidence file):

| 12.2 item | Satisfied by |
|---|---|
| 1 discover, start, supported negotiation | run 3 (`.mcp.json`; `initialize`, `2025-11-25` as reported by `genia_capabilities`) |
| 2 exactly three tools, no resources or prompts | run 3 `Discovered 3 tools`; server advertises `{tools: {}}`; resources/prompts `-32601` (matrix K5, K6). The VS Code UI views for resources/prompts were not separately reported, and the record says so |
| 3 `genia_capabilities` | run 3 |
| 4 `genia_parse` diagnostic and success | run 3 |
| 5 `genia_run` value, stdout, stderr separate | run 3 |
| 6 invalid -> `genia_parse` feedback -> corrected -> successful `genia_run` | run 3 (the recorded loop) |
| 7 stdout and stderr cannot corrupt framing | run 3 (the demo writes both) and matrix C rows |
| 8 no authority beyond the fixed profile | capabilities flags false; clean process list after stop; matrix A rows |

**Gate table (section 3) final state:** G1-G13 all PASS; no BLOCKER. H39, H45, H47, H48 closed; accepted-limitation entries closed
(H04, H10, H17, H18, H20, H27-H30, H32, H40, H42, H43, H46); post-R28 follow-up candidates H05-H09, H15, H24, H26 stay open (parking
lot, not ticketed). H36 closed by run 2.

**Test and audit results (PR branch; Linux unless stated):**

| Check | Result |
|---|---|
| Non-loopback regression (`-n auto -m "not loopback"`) | 6096 passed, 19 skipped (18 WIT/wasmtime unrelated; 1 gate test that applies only to a not-executed run), 0 failed |
| Loopback | 31 passed |
| R28/MCP suite, namespace simulated denied | 1159 passed, 1 skipped |
| Lifecycle/security/run/supervisor/compat suites on the `ps` backend (macOS code path, run on Linux) | 384 passed |
| Full R28/MCP suite on macOS (owner, `d0e4f2a4`) | 1141 passed, 18 skipped, 0 failed |
| Spec runner | 793/793 |
| Python/C++ host parity | Python 775/18, C++ 257/536, failure classes 0, gate `OK` |
| Official TypeScript client (default, `auto`, legacy, pin), Inspector 2.9.0 (default, `auto`) | all connect; three tools; `genia_run` 42 |
| ruff, `gen_function_docs --check`, `lint_doc`, `validate_llm_instructions`, `tests/doc` | clean |
| Release gate and mutation tests | pass; the latest run (3) is a passing run |

**Skeptical re-check of claims.** (a) Two run-3 fields (`resources_or_prompts_visible`, `workspace_trusted`) rest on protocol-level evidence and
the server starting, not a reported UI inspection; the evidence file states this. They do not change the acceptance items, which concern the
tool-discovery result. (b) The run-3 raw VS Code trace was not supplied; the record states that its entries are the owner's reported results.
(c) macOS verification is owner-run, not CI; the release page says so. (d) macOS has no address-space bound and no network namespace; no
document claims otherwise. (e) No Genia semantic, builtin, syntax, Core IR, MCP tool, resource, prompt, transport, or authority was added
by A5 or the macOS repair.

**Decision: READY TO CLOSE after PR #1082 merges.** R28 is Complete; PR #1082 is ready to merge (no failing check, no open blocker,
no unresolved finding). After the merge: close issue #707 and epic #700. #1078 and #1067 are untouched (#1067 stays after R28 and before R29).

