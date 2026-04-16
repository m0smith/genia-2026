# Host Capability Matrix

Status legend:

- `Implemented` = working in this repo today
- `Scaffolded` = docs/placeholder layout exists, but no host implementation yet
- `Planned` = intended future work only

Python is the only implemented host today.
All other hosts below are placeholders for planned work.
`hosts/python/` is also a placeholder directory for the future monorepo layout; the live Python implementation remains in `src/genia/`.

Browser playground adapter note:

- documentation scaffold exists under `docs/browser/`
- this is not an implemented browser runtime host capability yet
- `spec/manifest.json` records no implemented browser runtime adapter hosts in this phase

| Capability | Python | Node.js | Java | Rust | Go | C++ | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| parser | Implemented | Planned | Planned | Planned | Planned | Planned | Python parser/lowering live in `src/genia/interpreter.py` today |
| AST lowering | Implemented | Planned | Planned | Planned | Planned | Planned | Core IR lowering is part of current Python host |
| minimal portable Core IR contract | Implemented | Planned | Planned | Planned | Planned | Planned | Frozen in `docs/architecture/core-ir-portability.md`; host-local optimized nodes are excluded |
| Core IR eval | Implemented | Planned | Planned | Planned | Planned | Planned | Python is the current semantic reference host |
| CLI file mode | Implemented | Planned | Planned | Planned | Planned | Planned | `genia path/to/file.genia` |
| `-c` | Implemented | Planned | Planned | Planned | Planned | Planned | command mode |
| `-p` | Implemented | Planned | Planned | Planned | Planned | Planned | pipe mode |
| REPL | Implemented | Planned | Planned | Planned | Planned | Planned | Python REPL only today |
| Flow phase 1 | Implemented | Planned | Planned | Planned | Planned | Planned | lazy pull-based single-use Flow |
| HTTP serving | Implemented | Planned | Planned | Planned | Planned | Planned | synchronous blocking HTTP server bridge with request/response maps |
| refs | Implemented | Planned | Planned | Planned | Planned | Planned | host-backed runtime primitive with prelude wrappers |
| process primitives | Implemented | Planned | Planned | Planned | Planned | Planned | host-backed runtime primitive with prelude wrappers |
| bytes/json/zip | Implemented | Planned | Planned | Planned | Planned | Planned | host-backed bridge helpers |
| allowlisted host interop | Implemented | Planned | Planned | Planned | Planned | Planned | current Python host exposes only `python` / `python.json` with explicit conversion rules |
| debugger stdio | Implemented | Planned | Planned | Planned | Planned | Planned | Python debug adapter mode documented today |
| prelude autoload | Implemented | Planned | Planned | Planned | Planned | Planned | public stdlib surface is prelude-centered |
| doc/help support | Implemented | Planned | Planned | Planned | Planned | Planned | `help()` / `help("name")` in Python host |
| shared spec runner support | Scaffolded | Planned | Planned | Planned | Planned | Planned | contract docs/manifests exist; generic runner implementations do not yet |
| shell pipeline stage `$(...)` | Experimental | N/A | N/A | N/A | N/A | N/A | Python-host-only; not part of portable Core IR |
