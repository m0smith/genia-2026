# <Host Name> Host

TODO: replace `<Host Name>` with the target host language (e.g. `Node.js`, `Go`, `Java`).

## Status

scaffolded, not implemented

## Goal

TODO: describe this host's goal — e.g. "add a Go host that preserves the shared Genia semantics defined by the root docs, host-interop docs, and shared spec artifacts."

## Required Reading

Read these before writing host code:

1. `AGENTS.md`
2. `GENIA_STATE.md`
3. `GENIA_RULES.md`
4. `GENIA_REPL_README.md`
5. `docs/host-interop/HOST_INTEROP.md`
6. `docs/architecture/core-ir-portability.md`
7. `spec/README.md`
8. `spec/manifest.json`
9. `tools/spec_runner/README.md`
10. Relevant core docs/specs for the feature area you are touching

## Minimal Host Requirements

See `docs/host-interop/HOST_PORTING_GUIDE.md` §Minimal Host Requirements for the full list. A minimal conforming host must provide:

- lexer/parser for current surface syntax
- lowering into the shared Core IR meaning
- Core IR evaluation with current runtime semantics
- file mode CLI
- `-c` command mode
- raw `argv()` access
- prelude autoload/loading
- `help(name)` support for documented public helpers
- a way to participate in the shared spec runner contract

## Optional Capabilities

See `docs/host-interop/HOST_PORTING_GUIDE.md` §Optional Capabilities. These may arrive later, but must be marked honestly in `CAPABILITY_STATUS.md` and `docs/host-interop/HOST_CAPABILITY_MATRIX.md`:

- `-p` / `--pipe`
- REPL
- Flow phase 1 runtime
- HTTP serving
- allowlisted host interop bridge
- refs
- process primitives
- bytes/json/zip bridge
- debugger stdio

## Setup

TODO: describe host-language environment setup (e.g. runtime version, package manager, install command).

## Build

TODO: describe how to build the host (e.g. `go build ./...`).

## Test

Host-local: TODO (e.g. `go test ./...`)

Shared spec runner (required):

```bash
python -m tools.spec_runner
```

## Lint

TODO: describe the lint command (e.g. `golangci-lint run`).

## Known commands

| Task  | Command |
|-------|---------|
| setup | TODO    |
| build | TODO    |
| test  | TODO    |
| lint  | TODO    |

## References

- `docs/host-interop/HOST_PORTING_GUIDE.md` — porting checklist
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md` — per-host capability status matrix
- `hosts/template/EXAMPLE.md` — step-by-step bringup walkthrough
