# R28 Host-Dependency and Genia-Gap Inventory (living ledger)

Status: **Living release-wide R28 findings ledger; not a language contract.**
`GENIA_STATE.md` remains final authority for implemented Genia behavior. Nothing
in this file makes a capability, host API, or language feature current or
approved. It is the bounded host-dependency inventory required by E28-0 contract
§3.1 and §10 (`docs/design/r28-genia-mcp-contract-threat-model.md`) and is the
input the final R28 audit dispositions.

## 1. Purpose and the three layers

| Layer | Artifact | Question answered |
|---|---|---|
| 1. Ledger (primary record) | this file | what we found and what we are doing about it |
| 2. Discovery evidence | phase design docs, e.g. `docs/design/r28-e28-1-native-mcp-skeleton-design.md` | how each finding was discovered (probes, outputs) |
| 3. Issues | GitHub issues, only after promotion | approved work, via issue → pre-flight → roadmap |

Conversation discoveries become repository knowledge here; repository knowledge
becomes evidence; only evidence-backed entries become roadmap work.

## 2. Mandatory process rules

1. **Required input.** Every R28 phase (design, failing tests, implementation,
   documentation, audit) for E28-1 through E28-6 MUST read this file first and
   MUST update it when the phase discovers, resolves, reclassifies, or promotes a
   host dependency or Genia capability gap. A phase report must state which entries
   it added or changed (or that it changed none).
2. **No ticket from discovery alone.** Do not create language-feature issues merely
   because a gap is discovered. Preserve the evidence here. Promote an entry only
   via finding → evidence → issue → pre-flight → roadmap, at the final R28 audit
   or earlier only if the gap actually blocks R28. Promotion requires general
   usefulness beyond MCP (E28-0 §10); MCP implementation details do not become
   Genia features automatically.
3. **No release numbers.** Dispositions never assign a release number; roadmap
   placement is the normal roadmap process's job.
4. **Final audit.** The final R28 audit (currently E28-6/#707) MUST disposition
   every entry whose status is not `closed`, and publish the resulting table.
5. **Honesty.** Entries cite evidence actually observed. An unverified claim is
   marked `unverified`. Temporary host code is listed with the exact code that
   could later disappear.
6. **Lifecycle note.** This is a release-evidence artifact. Per the repository's
   "no process artifact in docs/ after merge" rule, the final audit distills the
   dispositioned table into the R28 release page (`docs/releases/`) and records
   whether this working ledger is retained or removed.

## 3. Entry format

Fields: **ID**, **finding / capability needed**, **evidence**, **class**
(A intrinsic host · B current Genia capability gap · C native Genia
responsibility · N not a gap / process), **current workaround**, **affected
hosts**, **general usefulness beyond MCP**, **removable code**, **disposition**,
**status** (`open` · `closed` · `promoted`), **promotion link** (issue /
pre-flight, when promoted), **raised in**.

## 4. Entries

### Native responsibilities and architecture decisions

**R28-H01 — Native Genia can own decode / validate / dispatch / result composition**
- Class: **C**. Status: `open` (standing constraint).
- Evidence: E28-1 native proof (stdin → `lines` → `json_decode` → `Json(...)`
  facet pattern → map-pattern dispatch → value construction → `json_encode` → stdout)
  ran on the Python reference host; design §4.
- Workaround: none needed. Hosts: Python verified; C++ not claimed.
- General usefulness: n/a (constraint, not a feature). Removable code: none.
- Disposition: architectural constraint; prevent regression to Python. Guarded by
  `tests/unit/test_r28_mcp_architecture.py` (AST literal scan, differential
  host-supplies-only-revision run, no-authority run).
- Raised in: E28-0/E28-1.

**R28-H02 — MCP SDK unnecessary**
- Class: **N (architecture finding)**. Status: `closed` (decision recorded).
- Evidence: H01 shows protocol/value handling is native-capable; an SDK would own
  dispatch/validation.
- Disposition: do not adopt. Reopen only if later evidence shows a native-incapable
  protocol requirement; it would then need an inventory entry (E28-0 §7).
  Guarded by the no-SDK import/dependency test.
- Raised in: E28-1.

**R28-H03 — JSON output is pretty, but native single-line framing works**
- Class: **N (not a gap)**. Status: `closed`.
- Evidence: `json_encode` always emits indented, key-sorted JSON (STATE ~3252);
  `split(t, "\n") |> map(trim) |> join("")` yields valid single-line JSON because
  literal newlines in encoded output are structural only (verified). Byte-compact
  JSON is not required by the verified stdio transport.
- Workaround: the native transformation itself. Removable code: none.
- Disposition: close; no feature needed. Byte-minimized JSON is not part of the gap
  backlog unless later evidence shows general usefulness beyond MCP. Framing is
  proven by the E28-1 framing tests (one line per frame, escapes, round trip).
- Raised in: E28-1 (corrected by approval feedback).

### Intrinsic host capabilities

**R28-H04 — Hard deadline, kill/reap, OS-level isolation, byte enforcement**
- Class: **A**. Status: `open`.
- Evidence: `execution.process` (STATE §9.40; `src/genia/process_transport.py`)
  already provides monotonic deadline, SIGKILL + reap, and incremental 1 MiB
  per-channel limits. OS-level filesystem/network/process denial is not provided by
  Genia and inherently needs OS authority.
- Workaround: reuse unchanged (E28-3). Hosts: Python; C++ would need its own.
- General usefulness: already general. Removable code: none.
- Disposition: keep behind the narrow host boundary; OS-level restrictions remain
  an E28-3 design question.
- Raised in: E28-0/E28-1.

### Current Genia capability gaps (class B)

**R28-H05 — No Genia-side bootstrap for an `execution.process` capability**
- Class: **B**. Status: `open`.
- Evidence: STATE §9.40 "Explicit limitations": only privileged host code can call
  `create_process_capability`; no file/command/pipe/import mode provisions one.
  `mcp.genia` therefore cannot obtain a worker-launch capability without host
  injection.
- Workaround (E28-3 candidate): host provisions one bound capability at launch.
- Hosts: Python (C++ has no `execution.process`). Usefulness beyond MCP: high
  (every consumer of `execution.process`, e.g. conformance tooling).
- Removable code: the host-side injection glue, once a general bootstrap exists.
- Disposition: preserve evidence; evaluate a general capability at the audit, or
  earlier if E28-3 is blocked. Not yet an issue.
- Raised in: E28-1 reconnaissance.

**R28-H06 — Child process stdin unavailable**
- Class: **B**. Status: `open`.
- Evidence: STATE §9.40: child stdin is immediate EOF; `process_transport.py`
  uses `stdin=DEVNULL`.
- Workaround: pass data by argv (see H07), or host-side worker entry.
- Usefulness beyond MCP: high (any process consumer needing input).
- Removable code: any stdin-substitute glue added in E28-3.
- Disposition: strong candidate for a later general process improvement; preserve
  evidence; promote only via the normal process.
- Raised in: E28-1 reconnaissance.

**R28-H07 — argv cannot carry the full allowed MCP source size**
- Class: **B** (consequence of H06). Status: `open`.
- Evidence: Linux caps a single argv element at 128 KiB (`MAX_ARG_STRLEN`); the
  contract source limit is 262,144 bytes. `execution.process` has argv only.
- Workaround: none proposed; needs design in E28-3 (evidence supporting H06).
- Usefulness beyond MCP: follows H06. Removable code: none yet.
- Disposition: evidence for H06; do not treat as an independent feature.
- Raised in: E28-1 reconnaissance.

**R28-H08 — Blocking process call cannot be cancelled**
- Class: **B**. Status: `open`.
- Evidence: `execution.process` is one synchronous call; STATE §9.40 lists no
  signals, general cancellation, or process handles. MCP stdio cancellation is a
  `notifications/cancelled` message arriving on the same stdin the server would be
  reading (verified, `patterns/cancellation.mdx`). The contract (§5) requires
  cancellation to terminate and reap the worker.
- Workaround: none chosen. Options (host supervisor vs. cancellable abstraction)
  belong to E28-3/E28-4 design.
- Usefulness beyond MCP: moderate to high (supervision, timeouts, servers).
- Disposition: evaluate a cancellable process abstraction; preserve evidence.
- Raised in: E28-1 reconnaissance.

**R28-H09 — No bounded stdin / line reader**
- Class: **B**. Status: `open`.
- Evidence: `stdin |> lines` materializes each full line before any size check, so
  a per-request byte bound cannot be enforced incrementally in Genia (contract §5
  asks for incremental enforcement). Also unverified: whether `lines` treats
  U+2028/U+2029 as separators (MCP frames on `\n` only) — **verified in E28-1**:
  `lines` splits only on `\n` (raw U+2028, `\r`, and NUL stay inside the line), and
  invalid UTF-8 input reaches Genia as a line that `json_decode` rejects, so the
  server answers `-32700` and continues.
- Workaround: none in E28-1.
- Usefulness beyond MCP: high (safe streaming of untrusted input).
- Disposition: evaluate as a general safe-streaming capability; preserve evidence.
- Raised in: E28-1 reconnaissance.

**R28-H10 — No build / revision identity facility**
- Class: **A/B (needs refinement)**. Status: `open`.
- Evidence: Genia has no builtin exposing build identity; the contract requires
  `contract_revision` as a 40-hex value that is not request-selected and carries no
  dirty-workspace description.
- Workaround (E28-1): host/launcher `hosts/python/mcp_launch.py` supplies it as the
  single argv datum; `mcp.genia` validates it and constructs the result.
- Hosts: Python launcher; a C++ host would need an equivalent launcher.
- Usefulness beyond MCP: to be assessed (version/identity reporting).
- Removable code: `resolve_contract_revision` / launcher glue if a general facility
  is adopted.
- E28-1 implementation: `hosts/python/mcp_launch.py` resolves `git rev-parse HEAD`
  (module-relative, `GIT_*` ignored, workspace state never described), validates
  40 lowercase hex, and passes it as the single argv datum; `mcp.genia` validates it
  again natively and constructs every result that contains it.
  Its environment allowlist (`PATH`, `LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`,
  `PYTHONIOENCODING`, `PYTHONUTF8`, `LANG`, `LC_ALL`, `SYSTEMROOT`, plus the computed
  `PYTHONPATH`) carries only what the host runtime needs to start; the loader paths
  were added after CI showed a shared-library Python 3.14 could not start without them.
- Disposition: R28 injects build identity; assess at the audit whether Genia needs a
  general facility. A is the current classification for the injection boundary; B is
  the open question.
- Raised in: E28-1 (approval feedback).

### Observations (knowledge, not gaps)

**R28-H11 — `json_decode` representation facet**
- Class: **N (documented behavior)**. Status: `closed`.
- Evidence: decode returns `some(represent("json", root), ctx)`; bare map patterns
  do not match until a `pattern Json(v) = representation_match("json", v)` arm is
  used (verified).
- Disposition: behavior is documented and sufficient; recorded in the E28-1 design
  so `mcp.genia` authors use it. No feature.
- Raised in: E28-1.

**R28-H12 — Flow pipelines are lazy and need a terminal `run`**
- Class: **N (documented behavior)**. Status: `closed`.
- Evidence: `map`/`each` over `stdin |> lines` produced `<flow each ready>` until
  `|> run` was added (verified). Also: `writeln` requires a sink; top-level function
  parameters are identifiers, so dispatch uses arm bodies. Further E28-1
  implementation observations (all verified while writing `mcp.genia`): arms over a
  multi-parameter function match the argument tuple, so they need tuple patterns
  (`(a, b) -> …`, catch-all `(_, _)`); a binary operator cannot start a line and a
  clause body cannot start on the line after `->`.
- Disposition: behavior is documented; no feature.
- Raised in: E28-1.


**R28-H15 — No Genia-level process exit status**
- Class: **B**. Status: `open`.
- Evidence: a Genia program cannot choose its exit code: `main` returning `7`,
  `err(...)`, or `none(...)` all exit 0, and no `exit`/`halt`/`error` builtin exists
  (probed; `exit` in STATE is the lifecycle peer callback). E28-1 needs a nonzero
  exit when the launch datum is rejected (contract §2.3).
- Workaround (temporary, in `mcp.genia` `reject_start`): write one fixed stderr
  diagnostic, then fail through a deliberate undefined-name runtime error, which
  exits 1 with nothing on stdout. The rejected datum is never echoed.
- Hosts: Python verified; C++ not assessed. Usefulness beyond MCP: high (any CLI
  program or pipeline stage reporting failure).
- Removable code: the `reject_start` undefined-name trigger.
- Disposition: preserve evidence; evaluate a general process-exit facility at the
  audit. Not yet an issue.
- Raised in: E28-1 implementation.

**R28-H16 — `none(...)` call short-circuit (documented) and eager `&&`/`||` (undocumented)**
- Class: **N (language behavior, observed)**. Status: `closed` (captured outside R28).
- Evidence: (a) `nil` is `none("nil")`; an ordinary function called with a `none(...)`
  argument is not run unless its arms handle `none`, so validity predicates return
  `none(...)` instead of `false` (`is_object(nil)` → `none("nil")`). This **is
  documented**: `GENIA_STATE.md` ("ordinary function calls short-circuit on
  `none(...)` arguments unless the callee explicitly handles absence", section on
  Outcomes). Part (a) is closed as documented behavior.
  (b) `&&` and `||` evaluate both operands (`false && boom("s")` raised
  from `boom`). `GENIA_RULES.md` lists the operators but neither it nor
  `GENIA_STATE.md` states their evaluation order. `mcp.genia` therefore uses total
  accessors (`norm`, `field`, `present`) and guard arms instead of `&&` for
  safety checks.
- Workaround: the total accessors in `mcp.genia`. Hosts: Python observed.
- Disposition: (b) is captured outside R28 as the parking-lot follow-up candidate
  "Selective Non-Strict Evaluation / Call-by-Need" (`docs/strategy/roadmap/parking-lot.md`,
  merged via PR #1059), which uses `false && rhs` / `true || rhs` as its first proving
  case and requires its own pre-flight. R28 changes and documents nothing about
  `&&`/`||`; this entry is evidence for that candidate. Its workaround in
  `mcp.genia` (total accessors) remains until such a feature lands; it is removable
  only after that.
- Raised in: E28-1 implementation; refined in E28-1 documentation.


**R28-H17 — Genia source cannot reach the parser**
- Class: **A**. Status: `open`.
- Evidence: no Genia-visible `parse`/`read` facility exists (probed builtins and
  prelude; metacircular `eval` works on quoted values). E28-0 §1 forbids R28 from
  adding a builtin or prelude function. The approved parse surface is
  `hosts/python/parse_adapter.parse_and_normalize`.
- Workaround (E28-2 design): one host capability returning JSON text, provisioned
  as an explicit argument to `serve(revision, host)`; no ambient binding.
- Hosts: Python; a C++ host would provide the same capability over its parser.
- Usefulness beyond MCP: a Genia-level "parse to normalized data" facility could
  serve tooling, but nothing here proposes one.
- Disposition: keep behind the narrow boundary; audit decides whether a general
  facility is worth a proposal.
- Raised in: E28-2 design.

**R28-H18 — No code-point length or substring helpers**
- Class: **B**. Status: `open`.
- Evidence: `length("héllo")` and `substring`/`slice`/`chars` are unavailable;
  `byte_length` exists. Contract §2.4 names a character `maxLength` guard, and
  parse diagnostics would ideally give line/column.
- Workaround: the byte limit check subsumes the character guard (more than
  262,144 chars implies more than 262,144 bytes); diagnostics report a character
  offset only.
- Usefulness beyond MCP: high (text processing in general).
- Disposition: preserve evidence for the audit.
- Raised in: E28-2 design.

**R28-H19 — Contract §2.4 invalid-Unicode wording vs strict JSON decoding**
- Class: **N (contract wording)**. Status: `closed` (resolved by Clarification A2).
- Evidence: contract §2.4 required `genia_parse` to return `input_limit` for invalid
  Unicode input. On the live E28-1 server, a request containing a lone surrogate
  escape (`"\ud800"`) is rejected by strict `json_decode`
  (`invalid_json_unicode`) and answered with JSON-RPC `-32700` before any tool is
  dispatched, so that `input_limit` case cannot exist.
- Disposition: resolved by contract **Clarification A2** (contract §2.4, §7.1, §15).
  Malformed JSON, including invalid Unicode, is `-32700` at the protocol boundary
  and invokes no tool; `genia_parse` `input_limit` applies only to a well-formed
  decoded `source` over 262,144 UTF-8 bytes. Strict JSON decoding is unchanged.
  Raised by the E28-2 design (commit `33e77a2`, which also records H17, H18,
  H20, H21); it blocked E28-2 failing tests until A2.
- Raised in: E28-2 design. Resolved in: E28-0 Clarification A2 (issue #703).

**R28-H20 — Capability provisioning needs an in-process host bootstrap**
- Class: **A** (relates to H05). Status: `open`.
- Evidence: CLI file mode passes only strings to `main(args)`; a host-built
  capability can reach `mcp.genia` only if the host loads the program in-process and
  calls a Genia function with it, as `hosts/python/exec_ollama_chat.py` already does.
- Workaround (E28-2 design): the launcher loads `mcp.genia` and calls
  `serve(revision, {parse: capability})`; CLI mode calls `serve(revision, {})` and
  advertises only `genia_capabilities`.
- Removable code: the bootstrap, if a general Genia capability-provisioning
  mechanism lands (see H05).
- Disposition: keep as the explicit provisioning boundary for R28; the audit
  decides together with H05 whether a general mechanism is worth a proposal.
- Raised in: E28-2 design.

**R28-H21 — Stale #703 wording ("official MCP client contract tests")**
- Class: **N (process/documentation drift)**. Status: `closed`.
- Evidence: #703 predates the native-Genia architecture (same drift as H13).
- Disposition: corrected — #703 body rewritten to the native-Genia scope and the
  raw JSON-RPC stdio harness (no SDK).
- Raised in: E28-2 design.



**R28-H22 — Parse AST integers beyond the strict JSON safe-integer range cannot cross the native boundary**
- Class: **B** (also a contract conflict: §2.4 requires `ast` "unchanged"). Status: `open` — **blocks E28-2 acceptance**.
- Evidence: `parse_and_normalize("123456789012345678901234567890")` returns
  `{"kind": "Literal", "value": 123456789012345678901234567890}` (R21 exact Integer
  source, shared spec `spec/parse/parse-r21-huge-integer-source-classification.yaml`).
  Genia's strict `json_decode`/`json_encode` accept only integers in
  `[-9007199254740991, 9007199254740991]` (STATE R9/R23: "no arbitrary-precision
  JSON-number transport"). Through the E28-2 implementation, an AST containing such a
  literal makes the native decode reject the host reply, so `genia_parse` returns the
  fixed `internal_error` envelope instead of the unchanged AST. Verified: sources whose
  integer literal is 9007199254740991 or smaller (and all float/decimal literals tried)
  match the host AST exactly; `9007199254740992` and larger do not. No wrong AST is
  ever returned.
- Failing boundary (isolated probes, not inferred): parser normalization
  (`parse_and_normalize`) and host serialization (`mcp_parse_capability.parse_source`,
  `json.dumps`) both preserve `9007199254740992` and `123456789012345678901234567890`
  exactly. The first rejection is the native decode of the capability reply:
  `json_decode(...)` at `apps/mcp/mcp.genia` `parse_result` reaches
  `_strict_json_int` (`src/genia/builtins.py`, `parse_int` hook), which returns
  `err(json_number_out_of_range, {cause: integer_out_of_range})`; `parse_reply` maps that
  to `internal_error`. A second, independent rejection waits behind it: native result
  construction uses `json_encode`, whose `_strict_json_from_runtime` rejects the same
  range (`json_encode({a: 9007199254740992})` -> `err(json_number_out_of_range, ...)`,
  while `9007199254740991` encodes). Genia runtime integers themselves are unrestricted
  (`9007199254740992 + 1` evaluates to `9007199254740993`). So the limit is the R9
  portable JSON data boundary, applied at two native calls, not a parser, capability,
  or JSON-RPC limitation.
- Distinction (do not conflate): Genia language/AST integer semantics are unrestricted;
  the R9 +/-(2^53-1) range governs only Genia's documented portable JSON data boundary
  (`json_decode`/`json_encode`); JSON as an external wire encoding has no such limit
  (consumers differ: Python clients read exact integers, IEEE-754 clients such as
  JavaScript would round). The current failure is fail-closed (never a wrong AST) but
  violates "unchanged normalized AST".
- Why no narrow fix exists inside the approved design: a lossless path needs either
  (B) a Genia JSON facility that is not R9 (new language/runtime semantics; excluded
  by R9/R23 and by contract §1), (C) opaque splicing of host-encoded AST text into the
  native frame (changes the approved native/host split of design §3.1/§3.3: the host
  would own AST encoding and native code would no longer decode/validate/size the AST),
  or (A) not returning `ast` for such sources (weakens AST parity). Each is a design
  or contract decision; no implementation was attempted.
- Workaround: none shipped. The shared-spec parity test for the huge-integer case
  stays red until a decision is made (it was not weakened).
- Options (human decision): (A) narrow contract clarification stating that an AST with
  an integer outside the strict JSON safe range is reported with a distinct fixed
  diagnostic rather than as `ast`, and adjust that one parity expectation; (B) a general
  Genia facility for exact large-integer JSON transport, which R23 explicitly excluded
  and R28 must not add; (C) host-side raw splicing of AST text into frames, rejected
  because it bypasses native validation and encoding.
- Hosts: Python; any host sharing the strict JSON boundary has the same limit.
- Usefulness beyond MCP: moderate (exact-integer interchange); promotion only through
  the normal process.
- Disposition: **STOPPED at the decision gate** -- awaiting a design/contract decision
  (options above, plus whether lossless wire integers are required for IEEE-754
  clients). The earlier recommendation of A is withdrawn pending that decision because
  A weakens AST parity. No code, test, or STATE change was made for H22.
- Raised in: E28-2 implementation.

### Process / documentation drift

**R28-H13 — Stale #702 wording (Python package, mandatory SDK, resources)**
- Class: **N (process/documentation drift)**. Status: `closed`.
- Evidence: original #702 body contradicted E28-0 §1.1, §2.1, §7.
- Disposition: corrected — #702 rewritten to native-Genia scope.
- Raised in: E28-1.

**R28-H14 — E28-0 wording vs. intermediate surface and verified MCP 2026-07-28**
- Class: **N (contract wording)**. Status: `closed`.
- Evidence: verified `2026-07-28` spec/schema showed E28-0 lacked: intermediate vs.
  final tool surface (C1), verified error codes and `resultType`/`isError` (C2),
  mandatory `server/discover` and `ttlMs`/`cacheScope` (C3), the reporting meaning of
  `execution_profile` before execution exists (C4), and `serverInfo.version` (D2).
  Discovery detail: E28-1 design §7 and §9.
- Disposition: resolved by narrow E28-0 **Clarification A1** (contract §2.1–§2.3,
  §7.1, §11, §12.2, §14); no architecture or authority change. The E28-1 failing
  tests already encode the clarified contract.
- Raised in: E28-1. Resolved in: E28-0 Clarification A1 (issue #702).

## 5. Phase update log

| Phase | Entries added / changed |
|---|---|
| E28-0 (contract) | provisional A-class candidates named in §3.1 (folded into H01–H10) |
| E28-1 design + failing tests | H01–H14 seeded; H03, H11, H12 closed on evidence |
| E28-0 Clarification A1 | H14 closed (contract clarified; no new entries) |
| E28-1 implementation | H09 (`lines`/UTF-8 verified), H10 (launcher implemented), H12 (syntax observations) updated; H15, H16 added |
| E28-1 documentation | H16 refined and closed (a: documented in STATE; b: captured as parking-lot follow-up via PR #1059); `GENIA_STATE.md` section 9.41 added |
| E28-2 design | H17, H18, H19 (blocking contract item), H20, H21 added |
| E28-0 Clarification A2 | H19 recorded and closed (invalid Unicode is `-32700` at the JSON-RPC boundary; `input_limit` is byte size only) |
| E28-2 implementation | H22 added (huge-integer AST literals vs strict JSON range; blocks acceptance); H17, H20 realized as designed |
| E28-2 | _not started — must read and update this ledger_ |
| E28-3 | _not started — expected to update H04–H09_ |
| E28-4 – E28-5 | _not started_ |
| E28-6 final audit | _must disposition every non-closed entry_ |
