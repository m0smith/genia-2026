# Genia Browser Playground Architecture (V1 Scaffold)

This document defines the V1 browser playground architecture as a documentation scaffold.
It does not claim that a browser app is implemented today.

## Purpose

- provide a clear browser playground architecture
- keep browser execution as a host-capability adaptation
- preserve the same source -> AST -> Core IR -> evaluation conceptual pipeline
- keep Python explicit as the current runtime behind V1
- define a stable runtime adapter boundary for future browser-native hosts

## Non-goals

- no language semantics change
- no browser-only Genia dialect
- no second implemented host

## High-level architecture

V1 shape:

1. Browser UI shell
2. Runtime client adapter
3. Backend runtime service (Python reference host)

Future shape (same UI semantics):

1. Browser UI shell
2. Runtime client adapter
3. Browser-native runtime adapter implementation (JS host or Rust/WASM host, likely in a Web Worker)

The runtime client adapter boundary is the stability point.
The UI should not care whether execution is backend-Python or browser-native.

## Browser UI shell

Planned UI regions:

- editor pane
- stdout pane
- stderr pane
- result pane
- stdin input area
- argv input area
- mode switch:
  - command mode
  - pipe mode
  - REPL-ish mode (interactive turn-by-turn evaluation)

Mode behavior should mirror documented CLI/runtime semantics where applicable.

## Capability adaptation model

Browser controls adapt host capabilities instead of redefining language semantics.

Capability mapping example:

- stdinText textarea -> runtime stdin capability input
- argv input -> runtime argv capability input
- stdout pane -> runtime stdout capture
- stderr pane -> runtime stderr capture
- help output -> ordinary runtime stdout/stderr/result handling
- files (if added later) -> explicit backend or browser sandbox capability bridge

Contract rule:

- UI adaptation changes transport only
- Genia semantics remain host/runtime semantics from shared docs/specs

## V1 backend runtime service

V1 explicitly uses the current Python reference host as backend runtime.

Recommended backend responsibility:

- expose a small runtime adapter API
- run parse/lower/eval and mode wrappers using existing Python host behavior
- return normalized outputs to browser client

This preserves current truth:

- Python is the only implemented host
- browser work is currently architecture/contract scaffolding

## Future browser-native runtime path

Later, the backend can be replaced without changing browser semantics by implementing the same adapter contract with:

- JavaScript host, or
- Rust/WASM host

Recommended runtime placement for browser-native execution:

- Web Worker (to isolate execution and keep the UI thread responsive)

Why Worker-first:

- reduced UI blocking
- cleaner message boundary
- easier sandbox posture

## Security and sandbox notes

V1 backend-Python posture:

- treat runtime execution as untrusted input handling
- isolate process/container boundaries
- enforce request size/time limits
- capture and sanitize error output

Future browser-native posture:

- run runtime in Worker context
- avoid exposing powerful host APIs directly
- use explicit capability bridge surfaces only

## Implemented now vs planned

Implemented now:

- this architecture documentation
- runtime adapter contract documentation scaffold

Planned for V1:

- browser playground app using backend Python runtime service
- UI panes/controls listed above

Planned later:

- browser-native runtime implementation using JS host or Rust/WASM host
- same adapter contract, same browser semantics

## AI-agent sync note for future work

Future Codex/Copilot browser or host tasks must keep these synchronized when behavior or user-facing examples change:

- GENIA_STATE.md
- relevant docs/book chapters
- relevant docs/cheatsheet pages
- docs/host-interop/*
- spec/manifest.json
- tools/spec_runner/README.md
- docs/browser/*

GENIA_STATE.md remains the final authority for implemented behavior.
