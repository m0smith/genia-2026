# Hosts Layout

This directory documents Genia's intended multi-host monorepo layout.

Current status:

- Python is the only implemented host today.
- The working Python implementation still lives at the repo root in:
  - `src/genia/`
  - `tests/`
  - `std/prelude/`
- The `hosts/*` directories are scaffold/placeholder directories in this phase.

## Target Layout

The intended long-term structure is:

- `hosts/python/`
- `hosts/node/`
- `hosts/java/`
- `hosts/rust/`
- `hosts/go/`
- `hosts/cpp/`
- `std/prelude/`
- `spec/`
- `tools/spec_runner/`

## Migration Strategy

This phase does not move the working Python host.

Instead it adds:

- shared host-interop docs
- shared spec scaffolding
- per-host placeholders
- explicit agent guidance to keep semantics aligned

Future moves should happen only when they can preserve current Python behavior and keep the shared docs/specs synchronized.

## Host Status

| Host | Status | Notes |
| --- | --- | --- |
| Python | Implemented | current reference host/prototype |
| Node.js | Planned | placeholder docs only |
| Java | Planned | placeholder docs only |
| Rust | Planned | placeholder docs only |
| Go | Planned | placeholder docs only |
| C++ | Planned | placeholder docs only |
