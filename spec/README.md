# Shared Spec Suite

This directory is the scaffold for Genia's shared cross-host spec suite.

Purpose:

- keep future hosts aligned with the same language/runtime/CLI contract
- validate behavior at the parse, Core IR, eval, and CLI boundaries
- reduce semantic drift between hosts

Python is the only implemented host today.
The spec layout is being added now so future hosts can validate against the same contract instead of growing host-local behavior.

## Spec Categories

The shared suite is intended to hold at least these categories:

- parse snapshots
- IR snapshots
- eval behavior
- stdout/stderr/exit-code behavior
- CLI behavior
- Flow behavior
- error normalization behavior
- prelude behavior

## Directory Layout

- `parser/`:
  - parse snapshots and parse acceptance/rejection cases
- `ir/`:
  - Core IR snapshots and lowering-focused cases
- `eval/`:
  - runtime result behavior for lowered programs
- `cli/`:
  - file mode, `-c`, `-p`, REPL-adjacent CLI behavior, stdout/stderr, exit codes
- `errors/`:
  - normalized category/message/span expectations
- `flows/`:
  - Flow phase-1 and `rules(..fns)` behavior

Prelude behavior may live in the most relevant category for now, usually `eval/`, `cli/`, or `flows/`.

## Contract

Shared specs are the cross-host authority for conformance as they are added.

Hosts may keep additional host-local tests, but they should not redefine behavior that shared specs already cover.

See also:

- `spec/manifest.json`
- `tools/spec_runner/README.md`
- `docs/host-interop/HOST_INTEROP.md`
