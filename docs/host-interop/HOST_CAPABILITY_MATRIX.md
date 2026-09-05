# Host Capability Matrix

Status legend:

- `Implemented` = working in this repo today
- `Python-host-only` = working only in the Python reference host today and not part of the shared portability contract
- `Scaffolded` = docs/placeholder layout exists, but no host implementation yet
- `Planned` = intended future work only

Python is the only implemented host today.
All other hosts below are placeholders for planned work.
`hosts/python/` is also a placeholder directory for the future monorepo layout; the live Python implementation remains in `src/genia/`.

For the formal per-capability contract (name, Genia surface, input/output shapes, normalized error behavior, and portability status), see `capabilities.md`.

Browser playground adapter note:

- documentation scaffold exists under `docs/browser/`
- this is not an implemented browser runtime host capability yet
- `spec/manifest.json` records no implemented browser runtime adapter hosts in this phase
- browser execution is planned to use the Python reference host on a backend service before any browser-native host exists

| Capability | Python | Node.js | Java | Rust | Go | C++ | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| parser | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python parser/lowering live in `src/genia/interpreter.py` today |
| AST lowering | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Core IR lowering is part of current Python host |
| minimal portable Core IR contract | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Frozen in `docs/architecture/core-ir-portability.md`; host-local optimized nodes are excluded |
| Core IR eval | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python is the current semantic reference host |
| CLI file mode | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | `genia path/to/file.genia` |
| `-c` | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | command mode |
| `-p` | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | pipe mode |
| REPL | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python REPL only today |
| Flow phase 1 | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | lazy pull-based single-use Flow |
| configuration environment snapshot | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python snapshots `os.environ` only during explicit immutable provider construction; portable hosts may report capability unavailable; E13-7 verifies public portability wording |
| configuration `.env` snapshot | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python reads bytes from one exact explicit path once during provider construction; portable hosts may report capability unavailable; E13-7 verifies public portability wording |
| deterministic model fixture | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E11-1/E11-4 fixture injected only for explicitly selected shared eval/error/Flow/CLI spec and test environments; E11-7 verifies its public runnable examples; no real provider or ambient binding |
| Gemini model REST adapter | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | E11-3 explicit host factory; direct standard-library unary REST, one attempt, fake transport in automated tests, no ambient binding or general HTTP API |
| deterministic embedding fixture | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E12-2 fixture explicitly injected only by Python tests; exact chunk/query identity, one attempt, no network adapter or ambient binding |
| deterministic indexing fixture / opaque handle | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E12-3 fixture; explicit injection, one attempt, private compatibility/corpus state, opaque non-serializable handle, no public vector-store API |
| deterministic paired retrieval fixture | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E12-4 fixture paired with indexing; explicit query embedding, identity/space/dimension checks, exact indexed provenance, no hidden embedding or networking |
| deterministic reranking fixture | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Offline E12-5 fixture; empty zero-attempt path, duplicate-aware evidence/provenance preservation, finite reranker-native scores, no normalization or networking |
| HTTP serving | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | synchronous blocking HTTP bridge with exact-path routing, response-header composition, CORS preflight, and request/response maps |
| HTTP outbound transport | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | R14 E14-6 private capability, no Genia surface; one synchronous `urllib.request` attempt, no redirects/retries, closed timeout/connect/tls/dns/other failure kind; consumed only by later `web.http_send` (E14-7) |
| refs | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | host-backed runtime primitive with prelude wrappers |
| process primitives | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | host-backed runtime primitive with prelude wrappers |
| bytes/json/zip | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | host-backed bridge helpers |
| resource-io | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | `fs` backend only; `import resource as res`; ResourceRef `{uri, backend}` pattern |
| allowlisted host interop | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | current Python host exposes only `python` / `python.json` with explicit conversion rules |
| debugger stdio | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python debug adapter mode documented today |
| prelude autoload | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | public stdlib surface is prelude-centered |
| doc/help support | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | `help()` / `help("name")` in Python host |
| shared spec runner support | Partial | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | implemented runner with active eval, ir, cli, flow, error, and parse shared case coverage against the Python reference host |
| shell pipeline stage `$(...)` | Python-host-only | N/A | N/A | N/A | N/A | N/A | Python-host-only; not part of portable Core IR |
