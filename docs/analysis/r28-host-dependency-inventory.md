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
- Class: **C**. Status: `closed` (standing constraint satisfied for the whole release).
- Evidence: E28-1 native proof (stdin → `lines` → `json_decode` → `Json(...)`
  facet pattern → map-pattern dispatch → value construction → `json_encode` → stdout)
  ran on the Python reference host; design §4.
- Workaround: none needed. Hosts: Python verified; C++ not claimed.
- General usefulness: n/a (constraint, not a feature). Removable code: none.
- Disposition: architectural constraint; prevent regression to Python. Guarded by
  `tests/unit/test_r28_mcp_architecture.py` (AST literal scan, differential
  host-supplies-only-revision run, no-authority run).
- Raised in: E28-0/E28-1.
- E28-6 final disposition: **Closed.** The constraint held for all of R28: the MCP application is native Genia and host modules contain no MCP literals (`tests/unit/test_r28_mcp_architecture.py`; `docs/mcp/host-portability.md`). It is evidence, not a deliverable, and can be reopened only by a regression.

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
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. Evidence: M:T1–T8, M:X1–X10, M:A21–A22; the OS layer is best effort and never claimed as a sandbox.

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
- E28-6 final disposition: Post-R28 follow-up candidate: a general facility beyond MCP (recorded here and in `docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and the shape in `docs/process/08-roadmap-ticketing.md`; no release number assigned). R28 ships the narrow host workaround named above. Status stays `open` until the completion synchronization. Evidence: the supervisor works with an explicitly provisioned capability (M:Y1–Y8).

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
- E28-6 final disposition: Post-R28 follow-up candidate: a general facility beyond MCP (recorded here and in `docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and the shape in `docs/process/08-roadmap-ticketing.md`; no release number assigned). R28 ships the narrow host workaround named above. Status stays `open` until the completion synchronization. Evidence: the supervisor owns its worker's stdin (M:L1).

**R28-H07 — argv cannot carry the full allowed MCP source size**
- Class: **B** (consequence of H06). Status: `open`.
- Evidence: Linux caps a single argv element at 128 KiB (`MAX_ARG_STRLEN`); the
  contract source limit is 262,144 bytes. `execution.process` has argv only.
- Workaround: none proposed; needs design in E28-3 (evidence supporting H06).
- Usefulness beyond MCP: follows H06. Removable code: none yet.
- Disposition: evidence for H06; do not treat as an independent feature.
- Raised in: E28-1 reconnaissance.
- E28-6 final disposition: Post-R28 follow-up candidate: a general facility beyond MCP (recorded here and in `docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and the shape in `docs/process/08-roadmap-ticketing.md`; no release number assigned). R28 ships the narrow host workaround named above. Status stays `open` until the completion synchronization. Evidence for H06; solved by the stdin pipe (M:L1).

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
- E28-6 final disposition: Post-R28 follow-up candidate: a general facility beyond MCP (recorded here and in `docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and the shape in `docs/process/08-roadmap-ticketing.md`; no release number assigned). R28 ships the narrow host workaround named above. Status stays `open` until the completion synchronization. Evidence: cancellation works through the supervisor and multiplexer (M:X1–X10).

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
- E28-6 final disposition: Post-R28 follow-up candidate: a general facility beyond MCP (recorded here and in `docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and the shape in `docs/process/08-roadmap-ticketing.md`; no release number assigned). R28 ships the narrow host workaround named above. Status stays `open` until the completion synchronization. Evidence: the 8 MiB multiplexer back-pressure is the documented limitation (M:L8).

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
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. A clone without `.git`/`git` fails closed with one stderr line (documented prerequisite); no general build-identity facility is proposed.

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
- E28-6 final disposition: Post-R28 follow-up candidate: a general facility beyond MCP (recorded here and in `docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and the shape in `docs/process/08-roadmap-ticketing.md`; no release number assigned). R28 ships the narrow host workaround named above. Status stays `open` until the completion synchronization. The only workaround is `reject_start` in `mcp.genia` (a deliberate undefined-name error, exit 1, nothing on stdout).

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
- Disposition: implemented as designed (E28-2: `hosts/python/mcp_parse_capability.py`,
  no builtin added); stays `open` for the E28-6 audit, which decides whether a general
  facility is worth a proposal.
- Raised in: E28-2 design.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. One explicit host capability returns normalized parse JSON; no Genia builtin was added (M:P1–P12).

**R28-H18 — No code-point length or substring helpers**
- Class: **B**. Status: `open`.
- Evidence: `length("héllo")` and `substring`/`slice`/`chars` are unavailable;
  `byte_length` exists. Contract §2.4 names a character `maxLength` guard, and
  parse diagnostics would ideally give line/column.
- Workaround: the byte limit check subsumes the character guard (more than
  262,144 chars implies more than 262,144 bytes); diagnostics report a character
  offset only.
- Usefulness beyond MCP: high (text processing in general).
- Disposition: workaround implemented in E28-2 (byte-limit check native; diagnostics
  are a character offset only, no line/column); evidence preserved for the E28-6 audit.
- Raised in: E28-2 design.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. Parse diagnostics are a character offset only (no line/column); limits are UTF-8 bytes (M:P4, P8, L5).

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
- Disposition: implemented in E28-2 (`hosts/python/mcp_host.py`, explicit
  `serve(revision, host)` argument); kept as the provisioning boundary for R28. The
  E28-6 audit decides together with H05 whether a general mechanism is worth a proposal.
- Raised in: E28-2 design.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. `serve(revision, host)` is the explicit provisioning boundary; `docs/mcp/host-portability.md` lists the host's responsibilities.

**R28-H21 — Stale #703 wording ("official MCP client contract tests")**
- Class: **N (process/documentation drift)**. Status: `closed`.
- Evidence: #703 predates the native-Genia architecture (same drift as H13).
- Disposition: corrected — #703 body rewritten to the native-Genia scope and the
  raw JSON-RPC stdio harness (no SDK).
- Raised in: E28-2 design.



**R28-H22 — Parse AST integers beyond the strict JSON safe-integer range cannot cross the native boundary**
- Class: **B** (also a contract conflict: §2.4 requires `ast` "unchanged"). Status: `closed` (resolved by Clarification A3 and implemented in E28-2; see Disposition).
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
- Disposition: **Option (i) selected by explicit decision** (originally listed as option
  C; the rejection recorded for C above was for unvalidated host splicing and is
  superseded by the constrained form below). Contract **Clarification A3** (contract §16)
  and design §6.1 record it. The capability serializes the existing normalized AST
  losslessly (`json.dumps`, exact integers); `mcp.genia` validates the capability header
  and limits natively and inserts the AST fragment opaquely into the result using
  ordinary string operations, never decoding it through R9 `json_decode` nor encoding it
  through R9 `json_encode`.
- Why R9 is unchanged: no R9 function, safe-integer rule, parser, AST shape, or Genia
  integer semantics is touched; the AST simply never enters the R9 data domain. R9
  `json_decode`/`json_encode` still reject integers beyond +/-(2^53-1) (regression
  tests unchanged).
- Why this is transport, not new Genia semantics: the splice is a local `genia_parse`
  function in an application program built from existing `split`/`join`/`json_encode`;
  it is not a general raw-JSON facility, builtin, type, or language rule. Unlike the
  rejected form, native code still owns status handling, error normalization, the
  fragment shape check, and the source and result byte limits.
- Client note: a lossless wire fragment is not a guarantee about IEEE-754-only client
  decoders (outside E28-2).
- Raised in: E28-2 implementation.

**R28-H23 — Normalized parse AST collapses most nodes (for example negative literals) to `{kind}` only**
- Class: **N (existing behavior; normalization coverage, not a parser defect)**. Status: `closed` (observation; follow-up candidate only through the parse-spec process).
- Evidence: `parse_and_normalize("-9007199254740992")` returns `{"kind": "ok", "ast":
  {"kind": "Unary"}}`; `-1`, `-x`, `!x`, and `-(1+2)` give the same, and `- 1 + 2` gives
  `Binary` with `left: {"kind": "Unary"}`. `hosts/python/parse_adapter.py` `normalize_ast`
  handles only a minimal set of node types and ends with `# Add more node kinds as
  contract expands` / `return {'kind': node_type}`. `spec/parse/README.md`: parse spec
  coverage expands only when forms are explicitly added; unary operators are specified
  at the IR level (`spec/ir/unary-operators.yaml`), not in parse specs. The parser
  itself builds `Unary(op, expr)` (`src/genia/ast_nodes.py`).
- Classification: expected existing minimal-normalization behavior, not a parser or
  semantic defect, and not caused by E28-2. Consequence for R28: `genia_parse` returns
  that normalized AST unchanged (parity), so a negative integer literal cannot appear
  with its magnitude in the AST today, and large negative integers cannot exercise the
  H22 transport. E28-2 does not bless a test of that shape as meaningful transport
  proof and does not change normalization.
- Disposition: closed as an observation; no R28 change. Follow-up candidate (not R28, not scheduled): extend the shared parse contract to
  cover unary and other node kinds through the normal parse-spec process, which would
  make the MCP AST richer without any MCP change.
- Raised in: E28-2 implementation (H22 follow-up).

**R28-H24 — No restricted-authority evaluation profile in Genia**
- Class: **B**. Status: `open`.
- Evidence: in command mode `read_file("/etc/hostname")` succeeds; the default global
  environment has 241 bindings and 234 prelude autoload entries. Authority-bearing
  ones include file/zip/resource I/O, `_http_send`/`_serve_http`/`_cors`, config/secret/
  declassification/model/embedding/retrieval bindings, `input`, `stdin_keys`, and the
  `file`, `web`, `execution`, and `resource` modules. `make_global_env` accepts sink,
  stdin, and snapshot-provider overrides but no allowlist or denylist.
- Workaround (E28-3 design, approved D1/D2): the host worker applies a default-deny
  classification (`hosts/python/mcp_worker_profile.py`): only explicitly allowed bindings
  and autoloads survive, `env.load_module` is replaced by a denial, and a drift test
  fails when any binding is unclassified.
- Usefulness beyond MCP: high (any untrusted-source consumer).
- Removable code: the profile module, if Genia gains a capability-restricted
  environment facility.
- Disposition: preserve evidence; the E28-6 audit decides whether a general facility is
  worth a proposal.
- Raised in: E28-3 design.
- E28-6 final disposition: Post-R28 follow-up candidate: a general facility beyond MCP (recorded here and in `docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and the shape in `docs/process/08-roadmap-ticketing.md`; no release number assigned). R28 ships the narrow host workaround named above. Status stays `open` until the completion synchronization. Evidence: the default-deny classification and its drift test (M:A18).

**R28-H25 — Normalized parse AST is too coarse for MCP policy**
- Class: **N/B** (consequence of H23). Status: `closed` (resolved by Clarification A4; implemented in E28-3).
- Evidence: `read_file("x")` normalizes to `{"kind": "Call"}` and `import web` to
  `{"kind": "ImportStmt"}`; callees and import targets are not in the normalized AST,
  so contract section 3's native "policy over normalized parse data" cannot detect
  prohibited calls or imports.
- Disposition: **resolved by contract Clarification A4** (decision D1): policy runs in
  the worker over the raw parser AST; the shared normalized surface is not expanded.
  Implemented in E28-3: `hosts/python/mcp_worker_profile.py` `policy_violation` walks the
  raw parser AST (a test asserts the normalized surface cannot see the callee while the
  raw AST can). Normalization expansion remains a separate parse-spec follow-up (see H23).
- Raised in: E28-3 design. Resolved in: E28-0 Clarification A4 (issue #704).

**R28-H26 — `execution.process` cannot launch the E28-3 worker**
- Class: **A** (refines H04, H06, H07). Status: `open`.
- Evidence: stdin is `DEVNULL`, argv elements cap near 128 KiB (source limit is
  262,144 bytes), the executable is a host-bound symbol, and the call is one
  synchronous operation (STATE 9.40).
- Workaround (E28-3 design, approved D2): a narrow supervisor
  (`hosts/python/mcp_run_capability.py`), leaving `execution.process` unchanged.
  Responsibilities (the best-effort namespace profile is determined once at host
  initialization, bounded at 5 s and cached, never inside a request; see H33): fresh
  process per call; private empty temporary cwd removed after
  reap; fixed environment allowlist (no `PATH`/`HOME`); `close_fds`; own process group;
  source over a stdin pipe while draining output; monotonic 5,000 ms deadline measured from
  worker readiness, with bootstrap separately bounded at 30 s (H34);
  incremental byte caps; kill and reap on timeout, cancel, limit, or failure; worker
  stderr discarded; reply shape check only; any exception becomes `internal_error`.
- Removable/generalizable: the whole supervisor if a general cancellable
  process-with-stdin capability lands (H05-H08).
- Disposition: implemented in E28-3 as designed; stays `open` for the E28-6 audit (which
  decides, with H05-H08, whether a general cancellable process-with-stdin capability is worth
  a proposal).
- Raised in: E28-3 design.
- E28-6 final disposition: Post-R28 follow-up candidate: a general facility beyond MCP (recorded here and in `docs/strategy/roadmap/parking-lot.md`; **not ticketed**, because ticketing needs the owner's approval and the shape in `docs/process/08-roadmap-ticketing.md`; no release number assigned). R28 ships the narrow host workaround named above. Status stays `open` until the completion synchronization. The supervisor is the only code that would disappear (H05–H08).

**R28-H27 — Cancellation versus the native single-threaded stdin loop**
- Class: **B** (refines H08, H09). Status: `open`.
- Evidence: `serve_lines` processes one request synchronously, so a
  `notifications/cancelled` message sits unread in stdin while `genia_run` blocks.
  Contract section 5 requires cancellation to terminate and reap the worker; E28-3 may
  not ignore it (decision D3).
- Investigation (prototype in the session scratchpad, not committed): a Python line
  multiplexer fed to the existing public `make_global_env(stdin_provider=...)` hook, plus
  a host `select` loop that calls a **Genia closure** (`is_cancel`) for each raw line,
  honored (a) a cancel line queued in the same write as the request, (b) a cancel
  arriving one second into the run, and (c) kept a non-cancel line that arrived during
  the run, answered in order afterwards. Protocol interpretation (method, request id)
  stayed in the Genia closure; the host only multiplexes, forwards raw lines, and
  terminates. No move of the MCP loop into Python was required, so no Clarification A5.
- Workaround (E28-3 design): `hosts/python/mcp_stdin.py` (multiplexer) plus the
  supervisor's select loop; native builds `is_cancel`. Limits: while more than 8 MiB of
  input is pending the multiplexer stops reading (back-pressure), so a flooding client
  cannot be observed for cancellation (best effort); a transport closure may prevent
  delivery of any envelope (contract section 5).
- Removable code: the multiplexer, if Genia gains a bounded/non-blocking stdin source.
- Disposition: implemented in E28-3 (`mcp_stdin.py`, supervisor select loop, native
  `cancel_matcher`); verified by `tests/unit/test_r28_mcp_run.py` (cancel queued with the
  request, mid-run, other id ignored, after completion ignored, other lines preserved in
  order, worker reaped) and the supervisor tests. Stays `open` for the E28-6 audit.
- Raised in: E28-3 design.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. Cancellation is implemented and tested (M:X1–X10); above 8 MiB of pending input it is best effort (documented).

**R28-H28 — Shell stages bypass environment pruning**
- Class: **A**. Status: `open`.
- Evidence: `$(cmd)` lexes to `SHELL_STAGE`; the evaluator's `_eval_shell_stage` calls
  `subprocess.run(shell=True)` directly, not through a global binding, so removing
  bindings cannot deny it.
- Workaround (E28-3 design): policy rejects `ShellStage`; the worker stubs subprocess and
  process-creating `os` functions at runtime; the network/user namespace and
  `RLIMIT_FSIZE` limit damage where available. The classification test asserts a shell
  stage creates no marker.
- Usefulness beyond MCP: moderate (an evaluator-level capability gate).
- Disposition: implemented as designed in E28-3 (policy rejects `ShellStage`; runtime stubs
  for `subprocess`, process-creating `os` functions, and sockets; tests assert a shell stage
  creates no marker with policy on and off). Preserve evidence; audit decides.
- Raised in: E28-3 design.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. Static policy, runtime stubs, and the optional namespace are each asserted (M:A10, A9, A22).

**R28-H29 — Contract "no implicit entrypoint" versus STATE command-mode `main` dispatch**
- Class: **N (contract versus documented CLI behavior)**. Status: `open`.
- Evidence: contract section 2.5 requires command-source evaluation semantics with no
  file-mode `main` dispatch or implicit entrypoint; STATE section 9 states that in file
  and `-c` command mode `main/1` is preferred over `main/0`, and `_resolve_program_result`
  dispatches it. The contract text is explicit.
- Disposition: implemented as stated (`main` is not dispatched; pinned by a test). The contract wins for the MCP profile: the worker evaluates with
  `run_source` and renders the resulting value without dispatching `main`; a regression
  test pins that a source defining `main` is not invoked. Parity tests with ordinary
  command mode use sources without `main`. No contract change needed; recorded so the
  difference is not rediscovered as a defect.
- Raised in: E28-3 design.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. The contract wins for MCP; the difference from CLI `-c` is pinned (M:R9) and documented in `docs/mcp/reference.md`.

**R28-H30 — Canonical value rendering cannot be bounded incrementally**
- Class: **B**. Status: `open`.
- Evidence: `format_debug` returns a finished string; contract section 5 asks for
  incremental limit enforcement and the 1 MiB value limit.
- Workaround (E28-3 design): the worker bounds the rendering with the wall-clock
  deadline and `RLIMIT_AS`, then checks the size; an overflow is `result_limit`.
- Usefulness beyond MCP: moderate (a bounded renderer).
- Disposition: implemented as designed (channel limits enforced incrementally in the worker
  sinks; value limit checked after rendering, bounded by the deadline and `RLIMIT_AS`).
  Preserve evidence; audit decides.
- Raised in: E28-3 design.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. Bounded by the deadline, `RLIMIT_AS` and a post-check (M:L8); documented.

**R28-H31 — The E28-1 server did not flush responses on a live pipe**
- Class: **N (defect found in an earlier phase; native Genia fix)**. Status: `closed`.
- Evidence: a persistent client got no response because `writeln(stdout, ...)` left each
  frame in a block-buffered pipe until exit; every E28-1/E28-2 test used a batch run (all
  stdin, then read all stdout) and could not see it. E28-3's live cancellation tests
  exposed it: a launcher session answered `tools/list` only after stdin closed.
- Disposition: fixed in native `mcp.genia` (`emit(text)` writes then calls `flush(stdout)`),
  with the live-session tests as the regression guard. No host or language change.
- Raised in: E28-3 implementation.

**R28-H32 — The canonical debug renderer exposes host representations**
- Class: **N (existing behavior; observation)**. Status: `open`.
- Evidence: `genia_run` of `print` returns `<function make_global_env.<locals>.print_fn at
  0x...>` and of a user function `GeniaFunctionGroup(name='f', functions={1: <function
  f/1>}, ...)`, exactly what ordinary command mode prints, so MCP inherits Python class and
  function names and a non-deterministic address for such values. Contract section 2.5 says
  the value is rendered by the existing renderer, not claimed to be a serialization.
- E28-5 evidence (matrix Z1): with a protected carrier injected into the real worker, a closure that
  captures it (`(x) -> CARRIER`), a named function returning it, and builtins all render only
  host text (`<function ... at 0x...>`, `GeniaFunctionGroup(...)`): the sentinel never appears in
  any byte of the session, because a closure's environment is not rendered. Callable values are
  excluded from every deterministic comparison (the 55-program parity corpus contains none), and the
  shape equals ordinary command mode (same renderer). No R28 contract violation was found.
- Disposition: not changed (a renderer change is outside R28). E28-5 recommends documenting it as an
  accepted limitation for R28 (non-deterministic address text, Python class names, no leakage); the
  E28-6 audit decides whether a portable rendering for callable values is worth a proposal.
- Raised in: E28-3 implementation. Refined in: E28-5.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. Audit: the contract (§2.5) says the value is rendered by the existing canonical debug renderer and is not claimed to be lossless JSON or a new serialization, so host text for callable values violates no requirement; E28-5 proved a captured protected value is never rendered and no deterministic comparison uses callable values. Documented as debug text, not a portable format. No renderer change. A portable callable rendering would be a separate proposal.

**R28-H33 — Live-process tests raced server bootstrap, and the namespace probe sat in the request path**
- Class: **A** (host-initialization responsibility) and **N** (test-synchronization finding). Status: `closed`.
- Evidence: PR CI (self-hosted runner, Python 3.14.7, 16 xdist workers) failed
  `test_cancel_arriving_mid_run_cancels_and_reaps` and
  `test_deadline_returns_timeout_and_reaps_the_worker[sleep]` with `assert set()` after a fixed
  `sleep(1.0)` measured from the send time. Reproduced locally with 12 CPU-bound processes plus
  12 xdist workers on 4 cores (3 of 7 live tests failed, identical symptom). Measured timeline of
  the first run request: server bootstrap (launcher, `git rev-parse`, host start, Genia import,
  `mcp.genia` load) dominated, with the governed worker first observable at 0.5-0.65 s unloaded
  and 1.8-2.2 s loaded; the one-time namespace probe cost only 20-40 ms in both cases but is
  bounded only by a 15 s timeout, a latent hazard. Independently, `LauncherSession.workers()`
  counted the probe's `python -S -c ... /proc/net/dev` process as "a worker", so "a worker was
  observed" could be satisfied by the probe and the reap assertions then checked the probe's
  pid rather than the governed worker. `process_children`-based discovery matched the actual
  topology (the worker is a direct child of the host, and `unshare` execs in place, so no
  wrapper process exists); topology was not a contributing cause, but the tests no longer
  depend on it. A reaped-but-zombie check (`pid_alive` ignoring zombies) could also hide a reap
  failure.
- Disposition: fixed in E28-3 (PR #1073) without changing the 5,000 ms deadline or disabling
  isolation. Product: `RunCapability` determines the best-effort namespace profile once at
  construction, which happens during host initialization before the server reads any request;
  the probe is bounded at 5 s (`PROBE_TIMEOUT_S`) and cached, and requests only consume it, so
  first-request behavior never depends on a capability probe. Tests: a readiness barrier
  (`wait_ready`), bounded observable polling for the governed worker (`wait_for_worker`, matched
  by its `-m hosts.python.mcp_worker` command line, not by depth or parentage and never the
  probe), strict reap checks (identity = pid + start time; an unreaped zombie fails), and
  load-independent timing assertions (the deadline lower bound is measured from before the send,
  so it holds under any load). Discriminating evidence: recording fake `unshare` tests prove the
  probe runs exactly once, before readiness, even when slow or hanging, and that a hung probe
  delays startup (bounded) rather than a request; seven probe tests fail against the previous
  product code.
- Raised in: E28-3 implementation (CI repair).

**R28-H34 — The execution deadline charged worker launch time to the program**
- Class: **A** (supervisor responsibility). Status: `closed`.
- Evidence: after the H33 repair, PR CI on `eb39aaf8` still failed three tests with `timeout`
  where the source normally finishes in about a second: two policy-denied wire tests
  (`[secret]`, `[shell stage side effect]`) and `test_eof_during_a_run_lets_the_run_finish`,
  which uses a trivial fake Python worker with the default 5 s deadline, so the host was
  stalled globally, not merely slow at importing Genia. The same job runs beside the C++ host
  parity and Node jobs on a shared self-hosted runner. Local reproduction under 40 processes on
  4 cores slows each wire test to 16-19 s without a timeout, showing how close worker launch
  gets to 5 s. The exact stall source on the CI host is **not proven**: candidates are CPU
  oversubscription and kernel-wide network-namespace create/destroy serialization (not
  reproduced locally: 160 `unshare --user --net` launches at 16-way showed a 91 ms maximum).
  The design charged the deadline from process spawn, but contract section 5 bounds parse/policy/
  evaluation/render and excludes startup; launch time (interpreter, imports, namespace creation)
  grows with host load and is not user code.
- Disposition: fixed in E28-3 without changing the 5,000 ms value or the single deadline: the
  worker writes a readiness marker to its real stderr after its trusted bootstrap and before
  reading or evaluating any source, and the supervisor starts the clock there; bootstrap is
  bounded separately (`STARTUP_LIMIT_MS`, 30 s; a worker that never becomes ready is
  `internal_error`). Cancellation works throughout. Discriminating evidence: a recording fake
  `unshare` makes the real worker's launch take 6 s (longer than the whole deadline); the run
  completes with the new supervisor and is a `timeout` with the previous one. Supervisor unit
  tests unrelated to the deadline now use a generous deadline and no kernel namespace.
- Raised in: E28-3 implementation (second CI repair).

**R28-H35 — The CI host class denies unprivileged namespaces; tests assumed it worked**
- Class: **N (environment observation; test assumption)**. Status: `closed`.
- Evidence: after the H34 repair PR CI moved to GitHub-hosted runners and two tests failed with
  `0 == 2` / `0 == 1`: `test_isolation_probe_runs_once_during_initialization_before_readiness` and
  `test_slow_worker_launch_is_not_charged_against_the_5000_ms_deadline` expected governed workers to
  pass through the `unshare` wrapper. On that host class `unshare --user` is denied, so the
  one-time probe (correctly) fails and workers run unwrapped. Simulating it locally with an
  `unshare` that always fails reproduced exactly those two failures and no others (386 other R28
  tests passed). Earlier self-hosted runs permitted namespaces, which hid the assumption.
- Disposition: tests fixed, not the product (the honest degrade is the specified behavior): the
  probe-once test asserts the wrapper count only for the outcome the host actually permits; the
  slow-launch injection test skips with a stated reason where a real namespace is unavailable (the
  property is covered without a namespace by the supervisor tests); a new wire test using a denying
  fake `unshare` proves the degrade deterministically everywhere (probe runs once before
  readiness, runs succeed, no wrapper is claimed or used). The suite now passes with the
  namespace both working (391 passed) and denied (388 passed, 3 skipped). Consequence: on CI of this
  class the namespace layer is not exercised; its behavior is verified only where available.
- Raised in: E28-3 implementation (third CI repair).

**R28-H36 — Default-configured official SDK clients use the legacy `initialize` handshake**
- Class: **N (contract-mandated limitation; interoperability risk)**. Status: `open`.
- Evidence: the official TypeScript client `@modelcontextprotocol/client` 2.2.0 (2026-09-28, spec
  2026-07-28) defaults to `DEFAULT_VERSION_NEGOTIATION_MODE = "legacy"`. Against the launcher its
  `connect()` sent `{"method":"initialize","params":{"protocolVersion":"2025-11-25",...}}` and
  received `-32601 Method not found` (contract 7.1 makes `initialize` an unknown method). With
  `versionNegotiation` `auto` or `{pin: "2026-07-28"}` the same client connected, listed exactly the
  three tools, and called `genia_capabilities` and `genia_run`. The v1 SDK `@modelcontextprotocol/sdk`
  1.31.0 knows no protocol newer than `2025-11-25` and has no `server/discover`. Whether VS Code and
  Copilot negotiate the modern era is not stated in the VS Code documentation source fetched in this
  phase and could not be run here.
- Disposition: not changed in E28-4 (supporting `initialize` is a contract amendment, section 7). The
  limitation and the required client mode are documented; the E28-5/E28-6 phases and the recorded
  VS Code run decide whether an amendment is needed.
- E28-5 investigation (evidence: `tools/mcp_acceptance/negotiation.mjs`, pinned by
  `tests/unit/test_r28_mcp_official_client.py::test_version_negotiation_evidence_for_ledger_h36`):
  with client 2.2.0 the SDK default and `legacy` both fail with `Method not found`; `auto` and
  `{pin: '2026-07-28'}` both connect and list exactly the three tools. The SDK documents the
  negotiation as **opt-in** (`legacy` is "byte-identical to a client without this option") and its
  source says changing the default "is a flip of this single line"; `auto` probes `server/discover` and
  falls back to `initialize` only when the probe is not definitive modern evidence. Public notes on the
  2026-07-28 revision describe SDKs that keep backward compatibility on every endpoint. The v1 SDK
  1.31.0 has no `server/discover` at all.
  1. *Merely an SDK-default issue?* At the SDK level yes: one line of client configuration
     (`auto` or a pin) works with no Genia change. It is transitional, not a protocol defect.
  2. *Can mainstream target clients use modern negotiation without Genia changes?* Programmatic SDK
     clients: yes. GUI hosts: **unverified**. No VS Code or Copilot negotiation behavior could be
     observed or found documented (H39).
  3. *Does `.mcp.json` provide enough information?* No, and it cannot: the portable format carries
     command, args and type only; it has no protocol-version or negotiation field. Era selection is
     entirely the host client's decision.
  4. *Would supporting legacy `initialize` materially improve interoperability?* Potentially yes, for
     every client whose SDK default or only mode is the 2025 era (all v1-SDK clients). How many target
     hosts that is cannot be established without the H39 run.
  5. *Burden?* A second protocol era in `mcp.genia`: `initialize` and `notifications/initialized`,
     protocol and capability negotiation, the session-initialized state the stateless contract (7.1,
     A1) forbids, `ping`, 2025-era result shapes (no `resultType`, `ttlMs`, `cacheScope`, per-request
     `_meta`) and error codes, a second conformance matrix, and an amended contract section 7 and
     Clarification A1. Native Genia could carry it, but it expands the approved protocol surface.
  6. *Is an amendment necessary before release?* **Not demonstrated by E28-5 evidence.** It becomes
     necessary only if the E28-6 VS Code/Copilot run (or the chosen release host) cannot negotiate the
     modern era. **Recommendation for E28-6:** do not amend now; obtain the H39 run first; if the
     target host negotiates modern (or `auto`), keep the contract and document the client requirement;
     if it cannot, stop and decide on this proposed amendment before claiming mainstream-host
     interoperability: "accept `initialize` with a requested `protocolVersion` of 2025-11-25 or
     earlier, answer once with the current capabilities and a legacy-compatible result shape, treat
     `notifications/initialized` as a no-op, keep every other behavior stateless". E28-5 implemented
     none of this.
- Raised in: E28-4 pre-flight. Refined in: E28-5.
- E28-6 final disposition: **Held open; decided by run 1 and amended — see the run 1 and amendment A5 paragraphs below.** Original text, written before run 1: No legacy `initialize` support was added. E28-6 evidence adds to E28-5's: the official Inspector 2.9.0 (CLI mode) also defaults to the legacy handshake and fails with `Method not found`, and works with `--protocol-era auto`; so both official tools need a one-line opt-in. Disposition once H39 is executed: `server/discover` observed means accepted compatibility limitation (legacy-only clients cannot connect; no legacy state); `initialize` observed means stop and decide on the amendment proposal above.

- Run 1 evidence (2026-10-05, authentic owner run; `docs/mcp/acceptance/vscode-copilot-evidence.md` run 1):
  VS Code 1.138.0 with GitHub Copilot Chat 0.66.0 on macOS (Darwin x64 24.6.0) discovered `.mcp.json`,
  started the launcher, and sent `initialize` with `protocolVersion: "2025-11-25"` and no `_meta`; the server
  answered `-32601 Method not found`; VS Code reported the failure and never reached tool discovery. This
  proved the question left open above: the target host uses the `2025-11-25` handshake, so an amendment was
  required. VS Code did not call `server/discover`.
- Pre-flight and approved amendment (E28-6, issue #707): `docs/design/r28-e28-6-protocol-compat-preflight.md`
  and contract Amendment A5 (section 18): exactly two revisions, `2026-07-28` and `2025-11-25`, selected per
  request; `initialize` (version-checked, never negotiated down), one process-local state bit, `ping`,
  silent `notifications/initialized`, `2025-11-25` result shapes; no tool, resource, prompt, transport,
  authority, or limit added; client capabilities grant nothing.
- Implementation: entirely native Genia in `apps/mcp/mcp.genia` (a single `ref` cell); no Python host change
  (architecture tests assert it). Automated evidence: `tests/unit/test_r28_mcp_compat.py` replays VS Code's
  exact `initialize` bytes; `tests/unit/test_r28_mcp_compat_conformance.py` and matrix section K repeat
  the corpus, authority, protected-value, limit, timeout, cancellation, and lifecycle rows in the compat
  era; the official client connects on the SDK default, `legacy`, `auto`, and `2026-07-28` pin paths and the
  Inspector 2.9.0 connects on its default and `auto` eras.
- E28-6 amendment A5 final disposition: **Implemented; remains open.** Automated and official-client
  evidence is not VS Code evidence: H36 closes only when run 2 (post-amendment, authentic) passes (see H39).
  Not verified for VS Code: the `initialized` notification, when `tools/list` is sent, `ping` use.

**R28-H37 — A stdio client may launch the server more than once, through a wrapper chain**
- Class: **N (client behavior, observed)**. Status: `closed`.
- Evidence: the official v2 client in `auto` mode launched the server twice for one connection
  (process 1: a `server/discover` probe, then closed; process 2: `tools/list`, `tools/call`). Under
  `uv run` the process chain is `uv` (stays alive) -> launcher -> host -> worker, four levels, with
  every level inheriting the client's stdio descriptors.
- Disposition: tests prove each launch is independent and stateless and that the chain shuts down
  and cleans up under EOF and signals (see H38).
- Validated by `tests/unit/test_r28_mcp_stdio_launch.py` (independent and double launches) and
  `tests/unit/test_r28_mcp_stdio_lifecycle.py`.
- Raised in: E28-4 design.

**R28-H38 — A worker and its temp directory outlive a host that dies mid-run**
- Class: **A** (host lifecycle; refines H26). Status: `closed`.
- Evidence: measured on the E28-3 code: SIGKILL to the host while a worker evaluated
  `sleep(60000)` left the worker alive for at least 25 s; SIGTERM to the host did the same and left
  the private `genia-worker-*` directory behind; SIGTERM to the launcher left the host and worker
  running as orphans. EOF on stdin (idle or mid-run, with stdout closed) was already clean (0.06 s
  and 2.3 s respectively).
- Workaround (E28-4 design, section 6): launcher signal forwarding; a host SIGTERM handler that
  unwinds so the supervisor kills and reaps the worker group and removes the directory; a worker
  orphan backstop (one-shot `SIGALRM` 8 s after readiness; not a second deadline).
- Removable code: all of it, if a general supervised-process facility lands (H05-H08).
- Disposition: implemented as designed (`hosts/python/mcp_launch.py`, `mcp_host.py`,
  `mcp_worker.py`). A SIGKILLed host can still leave an empty private temp directory (documented).
  Validated by `tests/unit/test_r28_mcp_stdio_lifecycle.py`, red before the change and green after.
- Raised in: E28-4 design.

**R28-H39 — VS Code/Copilot acceptance cannot be executed in the development environment**
- Class: **N (process limitation)**. Status: `open` (for the E28-6 audit).
- Evidence: this environment has no GUI and no GitHub authentication, and the proxy blocks
  `code.visualstudio.com`. Configuration facts were taken from the `microsoft/vscode-docs` source
  (pre-flight section 3), which does not state VS Code's protocol versions.
- Disposition: the executed acceptance is the official SDK client; a documented manual VS Code
  procedure and evidence record stay required by contract 12.2 before the final audit. Nothing
  claims a VS Code run.
- E28-5 re-check: still not executable. No `code` binary, no GUI, no Copilot authentication in the
  cloud container; `code.visualstudio.com` is unreachable through the proxy. **H39 stays open and no
  VS Code or Copilot acceptance is claimed.** The manual procedure in `docs/mcp/stdio-development.md`
  was made exact. E28-6 must obtain, before release closure: the VS Code version and Copilot
  extension version; the workspace folder opened and trusted; the MCP servers view showing `genia`
  running (or the output-log error); the tool list showing exactly the three tools; a `genia_parse`
  then `genia_run` exchange performed from the host (not scripted); and whether the host sent
  `initialize` or `server/discover` (the server's stderr stays empty, so this is read from the host's
  MCP log). That record also settles H36.
- Raised in: E28-4 pre-flight. Refined in: E28-5.
- E28-6 final disposition: **Held open: release blocker.** The E28-6 environment again had no VS Code, no GUI, no Copilot authentication, and no reachable marketplace. The procedure is `docs/mcp/vscode-copilot-acceptance.md`; the record is `docs/mcp/acceptance/vscode-copilot-evidence.md` (status `NOT EXECUTED`); `tests/unit/test_r28_release_gate.py` blocks any completion claim until it is executed and passes. Note that E28-4 (#705) required that a mainstream host connect end to end and was closed on official-SDK evidence only; this entry carries that acceptance.

- Run 1 (2026-10-05, executed by the owner; VS Code 1.138.0, Copilot Chat 0.66.0, macOS Darwin x64 24.6.0):
  `.mcp.json` discovery succeeded, the launcher started (state "Running" until the failure), and
  initialization **failed** (`-32601` for `initialize` `2025-11-25`; H36); tool discovery, parse, run, and
  lifecycle were not reached. Recorded as `EXECUTED` / `FAIL`, `failed_at: initialize`, unedited; the
  repository revision of that run was not recorded.
- E28-6 amendment A5 final disposition: **Held open: release blocker.** The post-amendment rerun (run 2) is
  pending and is the only evidence that can close this entry; the gate treats the latest run as governing,
  accepts `initialize`/`2025-11-25` or `server/discover`/`2026-07-28`, and requires exactly three tools, no
  resources or prompts, accepted parse and run, and a clean disconnect. The procedure the owner follows is
  `docs/mcp/vscode-copilot-acceptance.md`.

**R28-H40 — UTF-16 surrogate escapes in program strings cannot cross the JSON boundary unchanged**
- Class: **N (host string representation; documented limitation)**. Status: `open` (for the E28-6 audit).
- Evidence: found by the E28-5 channel matrix. Genia `\u` escapes build strings holding UTF-16
  surrogate code units, which are not Unicode scalar values. Direct evaluation keeps them
  (`"\ud83d\ude00"` renders as two code units). Through MCP the worker reply is JSON: a valid pair is
  merged by the decoder into the real scalar U+1F600 (rendered value and stdout differ from the direct
  result), and a lone surrogate (`"\ud800"`, written to stdout, stderr, or returned) makes the reply
  undecodable, so the call fails closed as `internal_error` with the fixed message and no partial data.
  No data leaks and no framing is affected.
- Disposition: not changed. It is pinned by
  `tests/unit/test_r28_mcp_conformance_run.py::test_utf16_surrogate_escapes_are_a_documented_transcoding_limitation`
  and matrix row C10. The E28-6 audit decides whether to document it only (recommended) or to ask
  for a Genia string-semantics decision (surrogates in strings are a Python-host detail a second host
  need not share).
- Raised in: E28-5.
- E28-6 final disposition: Accepted R28 limitation, compatible with the contract and documented in `docs/mcp/security-and-deployment.md` / `docs/mcp/host-portability.md`. Status stays `open` until the completion synchronization. Audit: the contract (§2.4, A2) requires rejecting invalid Unicode at the JSON-RPC boundary and does not require preserving UTF-16 surrogate code units created by string escapes; the path fails closed with a fixed message, leaks nothing, and framing is intact. Not a contract violation and no Genia string semantics are changed. A language-level ticket would need its own pre-flight and owner approval; none is created.

**R28-H41 — SIGHUP left the worker running and its private temp directory behind**
- Class: **A** (host lifecycle; refines H38). Status: `closed`.
- Evidence: the E28-5 lifecycle matrix sent SIGHUP to the client-launched process mid-run. The
  launcher forwarded it, but the host only handled SIGTERM, so SIGHUP's default action ended the host
  without unwinding: the worker survived until its 8 s orphan backstop and its `genia-worker-*`
  directory was never removed. STATE 9.44 and the E28-4 design describe SIGHUP forwarding; they claimed
  cleanup only for SIGTERM, so this was a gap in E28-4's hardening, not a contract violation.
- Disposition: fixed in E28-5 (red test `7503510`, fix `2568176`): `mcp_host.main` handles SIGHUP like SIGTERM
  (host plumbing only). `tests/unit/test_r28_mcp_conformance_lifecycle.py::test_sighup_to_the_client_launched_process_stops_the_chain_and_cleans_up`
  is red before and green after.
- Removable code: with the rest of H26/H38 if a general supervised-process facility lands.
- Raised in: E28-5. Resolved in: E28-5.

**R28-H42 — A failed run gives an agent no diagnostic text**
- Class: **N (design consequence; documented limitation)**. Status: `open` (accepted limitation).
- Evidence: found by the E28-6 skeptical audit while building the demo. `genia_run` failures carry only a
  fixed message (`Genia source failed during evaluation`) and parse failures only a character offset
  (no line/column, H18), because contract sections 2.2 and 6 forbid raw diagnostics, source text, and host
  exceptions in any response. An agent therefore cannot learn *why* a program failed (for example a missing
  builtin) from MCP alone; during this work the author fell back to direct Python/CLI evaluation to read the
  exception. That fallback is exactly the "agent bypass" that contract section 12.3 asks the audit to
  inventory.
- Disposition: not changed. The demo keeps its diagnostics inside the program's own values (the validation
  report), which cross the boundary as data. A normalized, bounded diagnostic facility would be a
  follow-up candidate (general usefulness beyond MCP: tooling and agents); it would need contract work
  first. Documented in `docs/mcp/demo.md` and `docs/mcp/reference.md`.
- E28-6 final disposition: Accepted R28 limitation; post-R28 follow-up candidate (recorded in the parking lot; not ticketed).
- Raised in: E28-6.

**R28-H43 — The platform evidence is Linux only**
- Class: **N (evidence gap; documentation correction)**. Status: `open` (accepted limitation).
- Evidence: every lifecycle and process test reads `/proc` and the namespace layer uses `unshare`; CI is a
  Linux host. Earlier text said "POSIX (Linux or macOS)". No macOS run exists.
- Disposition: documentation corrected in E28-6 to "Linux verified; macOS not verified; Windows not
  supported". No code change.
- E28-6 final disposition: Accepted R28 limitation (stated in `docs/mcp/demo.md`, `reference.md`, `security-and-deployment.md`, `stdio-development.md`, and the release page).
- Run 1 (macOS) at actual strength: it proved only that VS Code discovered `.mcp.json`, started the launcher, and spoke stdio JSON-RPC to it on macOS. It did **not** reach tool execution, so it says nothing about the worker, process groups, the namespace layer, temp-directory cleanup, or cancellation on macOS. Those remain unverified there; Linux remains the only platform with lifecycle evidence.
- Raised in: E28-6.

**R28-H44 — The release gate could not represent a failed authentic run**
- Class: **N (process; test schema)**. Status: `closed`.
- Evidence: the first gate recognised only `NOT EXECUTED` and a passing record, so the owner's real run 1 (executed, failed at `initialize`) had no truthful place to be recorded.
- Disposition: fixed in E28-6 amendment work: the evidence file holds numbered runs; a run is not executed, executed-failed (`failed_at` plus `not reached`/`not recorded`), or executed-passed; the latest run governs; permanent mutation tests prove each state. Run 1 was preserved verbatim.
- Raised in: E28-6 (A5).

**R28-H45 — VS Code's post-`initialize` behavior is inferred, not observed**
- Class: **N (evidence gap)**. Status: `open` (accepted until run 2).
- Evidence: only `initialize` was observed. Whether VS Code then sends `notifications/initialized`, when it lists tools, and whether it pings, is taken from the v1 SDK 1.31.0 reference. The server is therefore deliberately tolerant: it does not require `notifications/initialized`, answers `ping` in every state, and serves `tools/*` as soon as `initialize` succeeded.
- Disposition: closed by run 2.
- E28-6 final disposition: Held open for run 2 (H39); the tolerance rules are pinned by `tests/unit/test_r28_mcp_compat.py`.
- Raised in: E28-6 (A5).

**R28-H46 — The repository revision of the first authentic run was not recorded**
- Class: **N (evidence provenance)**. Status: `open` (accepted limitation).
- Evidence: the owner's trace did not include the commit that run used; run 1 records `repository_revision: not recorded` rather than a guess.
- Disposition: the run 2 procedure makes `git rev-parse HEAD` the first step and the gate requires it.
- E28-6 final disposition: Accepted: run 1 is history, not release evidence; run 2 must carry its revision.
- Raised in: E28-6 (A5).

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
| E28-2 H22 resolution | H22 resolved by contract Clarification A3 / design §6.1 (lossless opaque AST transport); H23 added and closed (normalization collapses unary nodes; not a defect) |
| E28-2 documentation | `GENIA_STATE.md` section 9.42 added; H17, H18, H20 dispositions updated to implemented (still `open` for the E28-6 audit); no further entries added |
| E28-3 design | H24–H27 added (restricted-profile gap, coarse normalized AST, supervisor vs `execution.process`, cancellation); H04, H06–H09 refined |
| E28-0 Clarification A4 | H25 resolved by A4 (policy over the raw AST in the worker; closes at implementation) |
| E28-3 final design | decisions D1–D4 approved; H27 mechanism proven by prototype (no A5); H24, H26 refined; H28 (shell stage bypass), H29 (no implicit entrypoint vs STATE), H30 (rendering not boundable) added |
| E28-3 failing tests | no new entries; tests pin H24 (default-deny classification), H26 (supervisor floor), H27 (cancellation), H28 (shell stage), H29 (no `main` dispatch), H30 (render limit) |
| E28-3 implementation | H25 closed; H26, H27, H28, H29, H30 implemented as designed; H31 (responses not flushed on a live pipe) found and fixed natively; H32 (renderer exposes host representations) added |
| E28-3 documentation | `GENIA_STATE.md` section 9.43 added; roadmap status updated |
| E28-3 CI repair (PR #1073) | H33 added and closed (probe moved to host initialization; live tests synchronize on readiness and observable worker state); H26 responsibilities refined |
| E28-3 CI repair 2 (PR #1073) | H34 added and closed (the 5,000 ms deadline starts at worker readiness; bootstrap separately bounded); H26 refined |
| E28-3 CI repair 3 (PR #1073) | H35 added and closed (CI host class denies unprivileged namespaces; two tests assumed otherwise; suite verified with the namespace working and denied) |
| E28-4 pre-flight and design | H36 (legacy-handshake clients), H37 (multiple launches, wrapper chain), H38 (worker and temp dir outlive a dead host), H39 (VS Code run not executable here) added with evidence |
| E28-3 audit | _not started_ |
| E28-4 audit | Findings: two narrow-import allowlist tests (launcher, host bootstrap) needed `signal`/`contextlib` and were updated with a comment; no other defect. Suites verified with namespaces available and denied |
| E28-4 implementation | H37 and H38 closed; H36 and H39 stay open (documented limitations, for E28-5/E28-6) |
| E28-5 pre-flight and tests | matrix design recorded; the matrix found H40 (surrogate escapes) and H41 (SIGHUP leak); H41 fixed and closed |
| E28-5 evidence | H32 (renderer: no leak, no destabilization), H36 (investigation and recommendation), H39 (re-checked, still open) refined; no entry closed except H41 |
| E28-6 amendment A5 (after run 1) | H36 (executed evidence, amendment, implementation), H39 (run 1 recorded; rerun pending), H43 (macOS evidence stated at actual strength) updated; H44 (gate schema; closed), H45 (post-initialize behavior inferred; open), H46 (run 1 revision not recorded; accepted) added |
| E28-6 final audit (release candidate) | all 22 non-closed entries dispositioned (H01 closed; H36 and H39 held open as release blockers; the rest accepted R28 limitations or post-R28 follow-up candidates, none ticketed); H42 and H43 added and dispositioned; the release gate test blocks any completion claim until the VS Code/Copilot evidence passes |
