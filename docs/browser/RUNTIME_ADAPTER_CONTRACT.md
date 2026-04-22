# Browser Runtime Adapter Contract (Scaffold)

This document defines a minimal runtime adapter contract for the browser playground.

Status:

- scaffold/contract documentation only
- not a claim that every host implements this today
- Python remains the current implemented reference host

The goal is a stable browser-facing boundary so runtime backends can be swapped without changing browser semantics.

## Contract principles

- browser transport is separate from language semantics
- request/response shape should stay stable across runtime backends
- mode behavior should align with shared CLI/runtime contracts where applicable
- Core IR remains the portability boundary for host semantics

## Minimal API surface

Required V1 method shape:

- run(request) -> response

Optional scaffold methods:

- parse(request) -> response
- lower(request) -> response

## Run contract

Request shape:

- mode: one of command | pipe | repl_turn
- source: Genia source text
- stdinText: optional string
- argv: optional list of strings

Response shape:

- ok: boolean
- result: optional rendered result payload
- stdout: string
- stderr: string
- error: optional normalized error object

Example JSON sketch:

{
  "mode": "command",
  "source": "1 + 2",
  "stdinText": "",
  "argv": []
}

{
  "ok": true,
  "result": "3",
  "stdout": "",
  "stderr": "",
  "error": null
}

Error object sketch:

{
  "phase": "parse|lower|eval|cli|io",
  "category": "SyntaxError|TypeError|NameError|RuntimeError|FileNotFoundError",
  "message": "human-readable message",
  "span": {
    "filename": "optional",
    "line": 1,
    "column": 1
  }
}

## Optional parse contract

Request:

- source: Genia source text

Response:

- ok: boolean
- ast: host JSON AST payload when ok=true
- error: normalized error object when ok=false

## Optional lower contract

Request:

- source: Genia source text

Response:

- ok: boolean
- ir: Core IR JSON payload when ok=true
- error: normalized error object when ok=false

## Mode notes

- command should follow command-mode semantics
- pipe should apply the same pipe wrapper semantics conceptually used by CLI mode
- repl_turn should represent one interactive evaluation step and return captured result/stdout/stderr

This contract does not redefine Genia REPL internals.
It is a browser-facing transport shape.

## Host implementation notes

V1 backend (planned):

- adapter implemented by Python runtime service using current reference host behavior

Later browser-native adapters (planned):

- JavaScript host adapter, or
- Rust/WASM host adapter

Both should satisfy the same contract shape so browser semantics remain stable.

## Relation to shared spec artifacts

This browser adapter contract is complementary to shared host contracts under:

- docs/host-interop/HOST_INTEROP.md
- spec/manifest.json
- tools/spec_runner/README.md

If this adapter contract becomes part of shared host conformance expectations, update those artifacts explicitly.

## AI-agent sync note

Future browser/runtime work must keep docs/spec/book/cheatsheets synchronized.
At minimum update, when relevant:

- GENIA_STATE.md
- relevant core docs and specs
- relevant docs/cheatsheet pages
- docs/host-interop/*
- spec/manifest.json
- tools/spec_runner/README.md
- docs/browser/*
