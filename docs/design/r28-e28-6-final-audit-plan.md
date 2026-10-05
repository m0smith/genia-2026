# R28 E28-6 — Final audit plan (pre-flight) and gate record

Status: **Pre-flight and gate record for E28-6** (issue #707, epic #700). `GENIA_STATE.md` is final
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
that `.mcp.json` should work do not satisfy it. H36 (legacy `initialize`) is decided by that run.

## 3. Release gates

| Gate | Requirement | Status | Evidence / blocker |
|---|---|---|---|
| G1 | Exactly three tools, no resources/prompts/HTTP | PASS | M:D1–D6, `client::test_the_official_client_completes_the_acceptance_scenario`, Inspector run (section 5) |
| G2 | Authentic VS Code + Copilot run, evidence recorded (C§12.2, issue #707 hard gate) | **BLOCKER** | No VS Code binary, GUI, Copilot authentication, or reachable marketplace in the audit environment (re-verified). Evidence record `docs/mcp/acceptance/vscode-copilot-evidence.md` is a structured template, status `NOT EXECUTED` |
| G3 | "At least one mainstream MCP host/client can connect over stdio" (E28-4 acceptance, #705) and the epic's "ordinary MCP client" criterion | **BLOCKER** | #705 closed on official-SDK evidence only; same missing run as G2. SDK default and Inspector default fail (H36); `auto`/pin work |
| G4 | H36 disposition | **BLOCKER (decided by G2)** | Held open: no legacy `initialize` support is added; if the VS Code/Copilot run sends `initialize` and cannot connect, stop and use the amendment proposal (ledger H36) |
| G5 | Runnable demo, no repository-internal knowledge | PASS | `docs/mcp/demo.md`, `examples/mcp/`, `tests/unit/test_r28_mcp_demo.py`, clean-clone run (section 5) |
| G6 | Packaging/publishing and executable entrypoint | PASS | Decision section 6: repository launcher plus `scripts/genia-mcp`; no new CLI contract, no registry/PyPI/npm claim |
| G7 | MCP reference, security/deployment limitations, host-portability statement | PASS | `docs/mcp/reference.md`, `docs/mcp/security-and-deployment.md`, `docs/mcp/host-portability.md` |
| G8 | Every non-closed ledger entry dispositioned | PASS (with H36, H39 held open by G2) | section 4 |
| G9 | Docs, state, roadmap tell the truth | PASS for the release-candidate state | R28 stays In Progress everywhere; `tests/unit/test_r28_release_gate.py` fails any "Complete" claim while G2 is unmet |
| G10 | Full regression, matrix, namespace granted and denied | PASS | section 7 |
| G11 | Skeptical audit | PASS with the recorded findings | section 7 |
| G12 | Agent-guidance update (`LLM_CONTRACT.md` prefers the MCP, C§12.3) | **DEFERRED by rule** | contract: only after the acceptance evidence exists; not changed |
| G13 | Inventory of agent bypasses/fallbacks (C§12.3) | PASS (inventory), observations H42/H43 | section 7.3 |

Decision rule: any BLOCKER above means **NOT READY TO CLOSE**. There is no middle category.

## 4. Ledger audit: every non-closed entry (22)

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
| H36 legacy-`initialize` clients | **held open (decided by G2)** | the contract mandates the stateless protocol; evidence so far: SDK default and Inspector default fail, `auto`/pin work; no code is added |
| H39 no VS Code/Copilot run | **held open: release blocker** | G2/G3 |
| H40 UTF-16 surrogate escapes | accepted R28 limitation | contract requires no preservation of non-scalar code units; fails closed; no new string semantics (section 7.2) |

New in this phase: H42 (no runtime diagnostic text for agents), H43 (macOS and Linux distributions beyond
the CI host are unverified). Both are accepted limitations (section 7.3).

## 5. Work completed in this phase

- **Demo:** `examples/mcp/validated_records.genia` and `validated_records_broken.genia` (existing Genia
  only), the public walkthrough `docs/mcp/demo.md`, and `tests/unit/test_r28_mcp_demo.py` (parse failure at
  a useful offset, repair, run, exact value/stdout/stderr, equality with direct evaluation, and a guard that
  the documented source equals the example files).
- **Entrypoint:** `scripts/genia-mcp` (start from any working directory); tests in `test_r28_mcp_entrypoint.py`.
- **Documentation:** reference, security and deployment, host portability, the demo, the VS Code/Copilot
  procedure and evidence template, the release page (Release Candidate, not Complete), ledger and roadmap
  updates (R28 In Progress; R20 follow-up #1067 stays after R28 and before R29).
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
decide on the ledger's amendment proposal.

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
