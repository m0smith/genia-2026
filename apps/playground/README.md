# Genia Playground App Scaffold

This directory is a scaffold for a future browser playground app.

Current status:

- Python is the only implemented host today.
- documentation scaffold only
- no production browser app implementation yet

V1 runtime plan:

- browser app frontend
- runtime execution served by backend Python reference host through a runtime adapter API

Later runtime plan:

- browser-native runtime (JavaScript host or Rust/WASM host) behind the same runtime client boundary

## Intended folder shape

Suggested future structure:

- apps/playground/src/ui/
  - App shell
  - editor pane
  - stdout pane
  - stderr pane
  - result pane
  - stdin/argv controls
  - mode switch controls
- apps/playground/src/runtime/
  - runtime client adapter
  - request/response type definitions
- apps/playground/src/state/
  - execution/session state
- apps/playground/src/security/
  - sandbox and capability policy helpers

## Runtime client boundary

The app should call a runtime client adapter, not host-specific code directly.

Adapter responsibilities:

- normalize browser UI inputs into adapter requests
- call backend API in V1
- map response to UI panes

See contract:

- docs/browser/RUNTIME_ADAPTER_CONTRACT.md

## Backend API expectations for V1

V1 backend should expose at least:

- run({ mode, source, stdinText, argv }) -> { ok, result, stdout, stderr, error }

Optional, if provided:

- parse(source) -> AST JSON envelope
- lower(source) -> Core IR JSON envelope

## Future Worker-based runtime model

For browser-native execution (later), prefer:

- runtime hosted inside a Web Worker
- same runtime adapter contract shape at the client boundary

This allows swapping backend-Python execution with browser-native host execution without changing browser semantics.

## Alignment requirements for future work

When behavior or examples change, keep synchronized:

- GENIA_STATE.md
- relevant core docs and specs
- relevant docs/cheatsheet pages
- docs/host-interop/*
- spec/manifest.json
- tools/spec_runner/README.md
- docs/browser/*
