# Host Capability Matrix

Status legend:

- `Implemented` = working in this repo today
- `Python-host-only` = working only in the Python reference host today and not part of the shared portability contract
- `Scaffolded` = docs/placeholder layout exists, but no host implementation yet
- `Planned` = intended future work only

Python is the only implemented host today.
All other hosts below are placeholders for planned work.
`hosts/python/` is also a placeholder directory for the future monorepo layout; the live Python implementation remains in `src/genia/`.

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
| HTTP serving | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | synchronous blocking HTTP server bridge with request/response maps |
| refs | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | host-backed runtime primitive with prelude wrappers |
| process primitives | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | host-backed runtime primitive with prelude wrappers |
| bytes/json/zip | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | host-backed bridge helpers |
| allowlisted host interop | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | current Python host exposes only `python` / `python.json` with explicit conversion rules |
| debugger stdio | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python debug adapter mode documented today |
| prelude autoload | Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | public stdlib surface is prelude-centered |
| doc/help support | Python-host-only | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | `help()` / `help("name")` in Python host |
| shared spec runner support | Partial | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Not Implemented | Python host adapter implements contract for parse, ir, eval, cli, flow, error; no generic multi-host runner exists |
| shell pipeline stage `$(...)` | Python-host-only | N/A | N/A | N/A | N/A | N/A | Python-host-only; not part of portable Core IR |
