# Host Capability Matrix

Status legend:

- `Implemented` = working in this repo today
- `Python-host-only` = working only in the Python reference host today and not part of the shared portability contract
- `Scaffolded` = docs/placeholder layout exists, but no host implementation yet
- `Planned` = intended future work only

Python is the full-language reference host. C++ is the bounded R27 production
host; all other hosts below are placeholders for planned work.
`hosts/python/` is also a placeholder directory for the future monorepo layout; the live Python implementation remains in `src/genia/`.

For the formal per-capability contract (name, Genia surface, input/output shapes, normalized error behavior, and portability status), see `capabilities.md`.
For the three-dimensional architecture classification, see
`../architecture/host-capability-taxonomy.md`. External direct process
execution (`execution.process`) is now implemented in the Python
reference host (row below) and registered as `execution_process` in
`spec/manifest.json`; its architecture boundary is recorded in
`../architecture/external-process-execution.md`, its approved contract is
`../design/execution-process-contract.md`, and its implementation design
is `../design/execution-process-design.md`. It has a **portable semantic
contract**, but its R16 `supported` self-declaration is not yet exercised
by any shared-spec case — see `capabilities.md`'s `execution.process`
entry for the runtime-implementation-vs-conformance-evidence distinction.

Browser playground adapter note:

- documentation scaffold exists under `docs/browser/`
- this is not an implemented browser runtime host capability yet
- `spec/manifest.json` records no implemented browser runtime adapter hosts in this phase
- browser execution is planned to use the Python reference host on a backend service before any browser-native host exists

| Capability | Python | Node.js | Java | Rust | Go | C++ | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| parser | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented (R24 subset) | Python parser/lowering live in `src/genia/interpreter.py`; C++ supports its declared floor |
| AST lowering | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented (R24 subset) | Both lower through the portable Core IR boundary |
| minimal portable Core IR contract | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented (R24 subset) | Frozen in `docs/architecture/core-ir-portability.md`; host-local optimized nodes are excluded |
| Core IR eval | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Partial (R24 floor) | Python remains the full semantic reference host |
| CLI file mode | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | `genia path/to/file.genia` |
| `-c` | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | command mode |
| `-p` | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | pipe mode; C++ (R27 E27-2) passes the 16 `requires: [cli_pipe_mode]` shared cases, with no trailing script arguments and no config/model/Template/`json_compat` pipelines |
| REPL | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | portable `repl` contract in `../design/r26-cpp-repl-contract.md`; C++ implements the scripted-session observations, including complete semicolon-separated submissions without implicit main dispatch, and declares `repl` supported; interactive terminal mechanics remain host-local |
| Flow phase 1 | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | lazy pull-based single-use Flow; C++ (R27 E27-1, E27-5) passes the 37 `requires: [flow_phase_1]` shared cases; `tee`/`merge`/`zip`, `rules`/`refine`, list-form `scan` and Flow display are not implemented in C++ |
| configuration environment snapshot | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python snapshots `os.environ` only during explicit immutable provider construction; portable hosts may report capability unavailable; E13-7 verifies public portability wording |
| configuration `.env` snapshot | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python reads bytes from one exact explicit path once during provider construction; portable hosts may report capability unavailable; E13-7 verifies public portability wording |
| deterministic model fixture | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E11-1/E11-4 fixture injected only for explicitly selected shared eval/error/Flow/CLI spec and test environments; E11-7 verifies its public runnable examples; no real provider or ambient binding |
| Gemini model REST adapter | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | E11-3 explicit host factory; direct standard-library unary REST, one attempt, fake transport in automated tests, no ambient binding or general HTTP API |
| deterministic embedding fixture | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E12-2 fixture explicitly injected only by Python tests; exact chunk/query identity, one attempt, no network adapter or ambient binding |
| deterministic indexing fixture / opaque handle | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E12-3 fixture; explicit injection, one attempt, private compatibility/corpus state, opaque non-serializable handle, no public vector-store API |
| deterministic paired retrieval fixture | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E12-4 fixture paired with indexing; explicit query embedding, identity/space/dimension checks, exact indexed provenance, no hidden embedding or networking |
| deterministic reranking fixture | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E12-5 fixture; empty zero-attempt path, duplicate-aware evidence/provenance preservation, finite reranker-native scores, no normalization or networking |
| HTTP serving | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | synchronous blocking HTTP bridge with exact-path routing, response-header composition, CORS preflight, and request/response maps |
| HTTP outbound transport | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | R14 E14-6 private capability, no Genia surface; one synchronous `urllib.request` attempt, no redirects/retries, closed timeout/connect/tls/dns/other failure kind; consumed internally by `web.http_send` (E14-7) and, through it, `web.send_annotated` (E14-9) |
| refs | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | Portable R25 contract; Python and C++ pass shared evidence |
| cell primitives | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | Portable R25 `cell_primitives` contract; Python and C++ pass shared evidence |
| process primitives | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | Portable local R25 contract; Python and C++ pass shared evidence; not Actor or external `execution.process` |
| bytes/UTF-8 | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | Bytes value + `utf8_encode`/`utf8_decode`; portable `bytes_utf8` contract in `../design/r26-cpp-data-bridge-contract.md`; C++ (R26-2) implements `utf8_decode` for well-formed input and `<bytes N>` display alongside R24 E24-3's Bytes value + `utf8_encode`, declares `bytes_utf8` supported, and passes the shared evidence |
| JSON (strict) | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented | `json_decode`/`json_encode`; portable `json_strict` contract in `../design/r26-cpp-data-bridge-contract.md`; C++ (R26-2) widens R24 E24-7's scalar-numeric slice to the full grammar (objects, arrays, strings/Unicode, booleans, null, nesting/duplicate-key limits, deterministic sorted-key/indented encode layout), declares `json_strict` supported, and passes the shared evidence |
| JSON (compatibility) | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | `json_parse`/`json_stringify`/`json_pretty`/`parse_jsonl_record`; decided not portable in `../design/r26-cpp-data-bridge-contract.md` section 5 |
| resource-io | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | `fs` backend only; `import resource as res`; ResourceRef `{uri, backend}` pattern |
| allowlisted host interop | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | current Python host exposes only `python` / `python.json` with explicit conversion rules |
| debugger stdio | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python debug adapter mode documented today |
| prelude autoload | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Partial (bounded R24 prelude) | public stdlib surface is prelude-centered |
| doc/help support | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | `help()` / `help("name")` in Python host |
| shared spec runner support | Partial | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Partial | generic runner evidence covers the declared R24 floor; pinned totals are in `docs/releases/R24.md` |
| shell pipeline stage `$(...)` | Python-host-only | N/A | N/A | N/A | N/A | N/A | Python-host-only; not part of portable Core IR |
| external process execution `execution.process` | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Portable semantic contract (`docs/design/execution-process-contract.md`), implemented only by the Python reference host today. Registered as `execution_process` in `spec/manifest.json`'s `optional_capabilities` (self-declared `supported` by the Python protocol adapter, matching `shell_stage`/`debugger_stdio`'s existing name-only registration precedent); no shared-spec case requires it yet, since no host-neutral capability-provisioning fixture mechanism exists — see `docs/host-interop/capabilities.md`'s entry for the runtime-implementation-vs-conformance-evidence distinction. Distinct from `$(...)`: structured argv, no shell, no `PATH` search. See `GENIA_STATE.md` section 9.40. |
| open functions (R20) | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Implemented (local only) | C++ supports the R24 local grouped/repeated evidence; cross-module contribution remains gated by unsupported `multi_file_eval`; the host has no tail-call optimization (call-depth limit 300), so deep mutual-tail-call cases report unsupported; a grouped open clause that captures a header name (contract section 3.3) is refused as unsupported, not diagnosed |
| multi-file eval fixture (R16/#836) | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Optional protocol-v1 `eval.input.modules` transport, advertised as `multi_file_eval`; independent of `open_functions`, and never sent to a host that does not claim it supported |

### C++ integration source revision

The host-parity and Docker development-environment workflows select
`78e61181a2c9ce32c33060b936b662c2f65ab2f0`, the independently reviewed
implementation merged by [genia-cpp #58](https://github.com/m0smith/genia-cpp/pull/58)
at `930ea94c0407ee3d150d131a05e1b5f27560e256`. It preserves the earlier
Cell/Process quiescence correction and repairs ordinary header capture,
duplicate/alias rejection, inline metadata, fixed-arity accumulation, complete
semicolon-separated REPL submissions and parser-depth safety. No capability,
protocol or language semantics are added.

The source revision is distinct from the adapter's declared semantic contract
revision, `6402e668ae85a1e7efe94b3ac3d51f233b730ca4`. Runs using a newer
`genia-2026` checkout provide ancestor-contract compatibility evidence, not
exact-contract conformance or satisfaction of required Model B syntax gaps.
Historical release counts above and below retain their original scope; selecting
this source revision alone is not evidence of a passing workflow.

### Model B declarations: parser/lowering, immutable-binding and default-open boundary

Python parses and lowers `=:` declarations, atomic closed groups and ordinary
pattern/guard headers using `IrImmutableBind`, `IrClosedFuncDef` and
`IrPatternFuncDef`. Python evaluation executes `IrImmutableBind` (optional
capability `immutable_bindings`, shared evidence `spec/*/model-b-b-*`) and
`IrPatternFuncDef` as default-open ordinary function clauses (optional capability
`default_open_functions`, shared evidence `spec/*/model-b-c-*`, which the in-process
runner executes against the Python reference host); closed groups are rejected with
`model-b-not-implemented`. Closed-function execution is not claimed. The Python
protocol adapter advertises `default_open_functions` as `supported`, and the 143
`model-b-c-*` cases (55 existing-behavior guards plus 88 gated cases) pass through that
adapter; the 18 Python-host-only fixture/debug cases remain the only `unsupported`
results of the external Python run.
C++ does not claim `immutable_bindings` or `default_open_functions`: both are listed
gaps in `spec/known_host_gaps.json` (tracking `genia-2026#1261` and `genia-2026#1269`;
parser/lowering owned by genia-cpp #50).

Python details (`GENIA_STATE.md` section 3 is authoritative): diagnostics are
`Cannot assign to immutable binding: x`, `Cannot rebind immutable binding: x` and
`Cannot declare immutable binding x: name is already bound in this scope` /
`name is reserved by the runtime`. Import, `open` and `use` targets are checked
before loading or linking. Direct route/server/CORS discovery rejects closed and
pattern carriers and a `=:` annotated `@route`/`@server`/`@cors`; an ordinary `=:`
is a plain statement there. Earlier statements' effects stand before an
unimplemented declaration.

The C++ adapter reports the new syntax outside its supported scope. Observations
against a binary pinned to ancestor contract
`6402e668ae85a1e7efe94b3ac3d51f233b730ca4` (43 parser/lowering cases: 5 PASS /
38 UNSUPPORTED, including all five `IrPatErr`/`IrPatNamed` IR cases) are
compatibility/gap observations, not current-contract conformance or parity.
Required `parser`/`ast_lowering` obligations are not hidden behind optional
capabilities: `spec/known_host_gaps.json` admits only optional-capability gaps,
and an adapter's `unsupported` response (including for negative parse cases)
remains an unmet syntax obligation, not a passing diagnostic. A green
optional-capability gate does not certify it.

Owner: m0smith integration owner and C++ implementer, tracked in
[genia-cpp #50](https://github.com/m0smith/genia-cpp/issues/50) under #1250.
The boundary is removed only after the bounded C++ parser/lowering implementation
passes the affected shared cases at a current contract revision. Until then, no
C++ conformance or new-carrier parity is claimed. Default-open dispatch,
cross-module linking changes and closed publication are not implemented on any host.
