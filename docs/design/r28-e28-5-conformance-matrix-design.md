# R28 E28-5 — MCP conformance and parity test matrix: Pre-flight and design

Status: **Pre-flight and design for E28-5** (issue #706, epic #700). `GENIA_STATE.md` remains final
authority (E28-1: 9.41, E28-2: 9.42, E28-3: 9.43, E28-4: 9.44). Governing contract:
`docs/design/r28-genia-mcp-contract-threat-model.md` (sections 2, 4, 5, 6, 7.1, 11, 12 and
Clarifications A1–A4). Findings are cited as `[H##]` from
`docs/analysis/r28-host-dependency-inventory.md`. The durable result of this phase is
`docs/mcp/conformance-matrix.md`.

E28-5 is a **conformance and evidence phase**. It adds tests, one matrix document, and ledger/status
updates. It adds no Genia syntax, builtin, Core IR node, MCP tool, resource, prompt, transport, or
host behavior, and it does not amend the contract. E28-6 (#707) still owns the demo and the final
release audit; E28-5 only leaves it an auditable matrix.

## 1. Reconciliation (what was checked)

| Source | Finding |
|---|---|
| #706 acceptance | "The matrix demonstrates that MCP is an adapter boundary, not a second Genia semantics path, and catches accidental leakage or capability widening." Coverage list: discovery, schema stability, parse, run, deterministic envelopes, timeout/cancel/size, redaction, prohibited authority, stdio end to end, **HTTP parity only "if HTTP ships in R28"**, direct-host/MCP parity. |
| Contract | Closed envelope (2.2), exact three tools (2.1), source-only run with command-source semantics and no `main` dispatch (2.5), limits in UTF-8 bytes (5), protected values never cross (6), `initialize` is an unknown method (7.1). |
| Implemented E28-1..E28-4 | As recorded in STATE 9.41–9.44; baseline on `main` `6aa646b`: all existing R28 tests pass (one local skip: the official client when Node/`npm ci` is absent). |
| Existing evidence | Strong unit coverage per ticket (`tests/unit/test_r28_mcp_*.py`). Gaps are cross-cutting: no single inspectable matrix, no namespace-denied sweep over the security matrix, few exact boundary cases (multibyte, one-below), no sentinel sweep over every response path, no multi-class failure-envelope shape check, thin cancellation/timeout edges, one official-client scenario. |
| E28-6 (#707) | Demo, publishing docs, release page, final truth audit and disposition of every non-closed ledger entry. Not started here. |
| #1078 | Separate infrastructure issue (load-sensitive 0.5 s spec-runner adapter timeout); not touched. |

HTTP did **not** ship in R28 v1 (contract 7, 9.3), so the HTTP-parity coverage item is
NOT APPLICABLE (deferred), recorded in the matrix and not implemented or tested as a feature.

## 2. Decisions

| # | Decision |
|---|---|
| M1 | One durable, checked-in matrix: `docs/mcp/conformance-matrix.md`. Every row has an ID, a classification, the authority, direct and MCP behavior, the expected relationship, the evidence test(s), host limitations, and a status. |
| M2 | A documentation test (`tests/unit/test_r28_mcp_conformance_matrix.py`) fails when a matrix row cites a test that does not exist, so the matrix cannot silently rot, and when a statused row has no evidence. |
| M3 | New tests extend the existing launcher/official-client harnesses (`tests/fixtures/r28_mcp_helpers.py`, `tools/mcp_acceptance/`); no second harness. |
| M4 | The parity oracle is **command-source evaluation** (`run_source(..., filename="<command>")` in a fresh default-or-equivalent global environment, value through `format_debug`, program output captured separately), not the CLI `-c` mode, because `-c` dispatches `main` and prints a text stream [H29]. A second oracle (`genia -c`) is used only for sources that define no `main`. Differences are classified, never normalized away silently. |
| M5 | Namespace honesty is tested by running the same corpus with the host's real namespace behavior **and** with `unshare` simulated as denied, and by an environment switch (`GENIA_R28_TEST_DENY_NAMESPACE=1`) that makes the whole R28 suite run in denied mode. |
| M6 | No production change unless a genuine E28-5 defect is found; any such fix goes through the normal gate and is recorded in the ledger. |

## 3. Matrix dimensions and classification

Every dimension is classified exactly once as one of: **P** MCP protocol conformance · **A**
adapter/direct-host parity · **S** security/authority boundary · **D** deterministic behavior ·
**R** resource/lifecycle behavior · **H** host-specific implementation evidence · **L** documented
limitation.

| ID | Dimension | Class | Notes |
|---|---|---|---|
| D1–D6 | Discovery: exact tool names, order, descriptor key set, exact descriptions, exact input schemas, no extra input properties, no resources/prompts, no fourth tool, no host-only tool leakage | P | Descriptions are not normative in the contract; they are pinned as drift detectors and the matrix says so |
| D7 | `genia_capabilities` matches the implemented profile, claims no OS mechanism, identical with a real and a denied namespace | P / H | The OS layer is intentionally absent from the capability response (A1, E28-3 section 5) |
| D8 | `initialize` is Method-not-found (stateless 2026-07-28) | L | H36; not a defect and not widened here |
| P1–P12 | `genia_parse`: valid, invalid, empty, several error offsets, UTF-8, Unicode identifiers, invalid Unicode at the JSON-RPC boundary, byte limit, large exact integers, AST equals the existing normalized surface, determinism, no authority | A (parse parity), P (framing), D | Unicode identifiers are **not supported by the parser today**: parity of the *failure* is tested; recorded as L, not as a defect |
| R1–R8 | `genia_run` success: literals, arithmetic, collections, functions, Outcomes, Flow/pipelines, Unicode strings, exact numerics, determinism | A | Compared to command-source evaluation (M4) |
| R9 | `main` is not dispatched | A (intentional difference) / L | Contract 2.5 vs STATE `-c` [H29] |
| C1–C9 | Value / stdout / stderr / exit code separation, JSON and JSON-RPC-looking and method-name output, newline-heavy and Unicode output | P / A | Program output is data, never framing |
| F1–F8 | Closed failure envelope for every contracted class (`parse_error`, `policy_denied`, `runtime_error`, `timeout`, `cancelled`, `result_limit`, `input_limit`, `internal_error`), fixed messages, no partial data, no host text | P / D | `internal_error` is induced through a substitute worker (supervisor seam), not by weakening production code |
| L1–L9 | Limits at one below / exact / one above for source, stdout, stderr, value, diagnostic, aggregate, in UTF-8 **bytes**; no unbounded accumulation before enforcement | R / P | Multibyte cases distinguish bytes from characters |
| A1–A22 | Authority denial per authority, split by layer: **static policy** (raw AST), **unavailable binding** (pruned environment), **runtime stub** (process/socket/import), **host/OS defense in depth** (rlimits, optional namespace) | S | The layers are different claims and are recorded separately |
| S1–S10 | Protected values never cross the boundary, sentinel over the whole response, every path | S | MCP provisions no provider, so a carrier can only be reached by host injection: worker-level injection plus source-echo checks on every failure class |
| X1–X10 | Cancellation matrix | R | Readiness barriers and bounded observable polling, never fixed sleeps |
| T1–T8 | Timeout matrix | R / D | The 5,000 ms deadline is not altered |
| Y1–Y12 | Lifecycle and leak matrix | R / H | A SIGKILLed host may leave an empty private temp directory (documented L) |
| N1–N4 | Namespace available / denied | H | Namespace is defense in depth, not the security contract |
| O1–O12 | Official TypeScript client end to end | P | Credential-free, CI-safe, `auto` negotiation |
| V1 | Direct-host versus MCP parity corpus | A | Section 5 |
| Z1 | H32 renderer exposes host representations | L | Evidence only; no renderer redesign |
| Z2 | H36 legacy `initialize` clients | L | Investigation and recommendation only |
| Z3 | H39 VS Code/Copilot run | L | Honest status; not claimed |
| Z4 | Streamable HTTP | NOT APPLICABLE | Deferred; no listener, no HTTP tests |
| Z5 | C++ MCP | NOT APPLICABLE | No C++ implementation or parity claim |

## 4. Matrix status vocabulary

`PASS` (automated evidence exists and passes) · `KNOWN LIMITATION` (documented behavior that is
intentionally not parity or not supported; evidence pins the limitation so it cannot silently
change) · `NOT APPLICABLE` (the contract defers or excludes it). A difference that the contract
mandates (policy restriction, no `main` dispatch, closed envelope instead of raw text) is never
labeled a parity failure.

## 5. Direct-host/MCP parity design

For each corpus program the matrix records: source, direct mode, direct expectation, MCP
expectation, whether exact equality is required, intentional differences.

- **Direct mode:** command-source evaluation, in-process, with captured stdout/stderr streams and
  the canonical debug renderer (`format_debug`); the same call the worker makes, minus the restricted
  environment. Because it runs the *default* global environment, equality shows the restricted
  environment does not change results of ordinary programs. Where the corpus depends on a binding
  that the profile prunes, the case is a **policy restriction**, listed separately.
- **Equality required:** rendered value, stdout and stderr byte-for-byte, for the whole corpus.
- **Intentional differences:** envelope instead of raw text; no `main` dispatch; denied authorities;
  addresses and Python class names in the debug rendering of callable values [H32] (excluded from
  exact equality and pinned as L).
- **Not compared:** transport envelopes against raw CLI text.

## 6. H36 investigation plan

Evidence, not implementation: run the pinned official client with the three negotiation modes
(`legacy`, `auto`, pinned `2026-07-28`) against the launcher and record the result; inspect the
SDK's documented configuration surface; assess what supporting `initialize` would add (state,
version negotiation, capability negotiation, `notifications/initialized`, session identity versus
the contract's stateless model). Output: recommendation for E28-6. If evidence shows a contract
amendment is necessary before release, E28-5 stops and reports the proposed amendment instead of
implementing it.

## 7. H39 plan

Attempt only what the environment can honestly do. No VS Code or Copilot is available in the cloud
container, so H39 stays open; the manual procedure is made exact and the evidence record E28-6 must
obtain is specified.

## 8. Out of scope

HTTP, resources, prompts, additional tools, C++ MCP, new Genia semantics, renderer changes,
legacy-handshake support, #1078, the demo, packaging/publishing, and the final audit (E28-6).
