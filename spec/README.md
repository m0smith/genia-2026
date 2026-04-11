# Shared Spec Suite

This directory is the scaffold for Genia's shared cross-host spec suite.

Purpose:

- keep future hosts aligned with the same language/runtime/CLI contract
- validate behavior at the parse, Core IR, eval, and CLI boundaries
- reduce semantic drift between hosts

Core IR scope note:

- shared IR snapshots target the minimal portable Core IR contract
- host-local post-lowering optimized IR is intentionally out of scope for shared Core IR snapshots

Browser playground adapter note:

- browser runtime adapter docs are scaffolded under `docs/browser/`
- this is currently a contract/planning surface, not a second implemented host
- shared browser-adapter metadata is tracked in `spec/manifest.json`

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
- capability-bridge behavior when a host implements optional allowlisted host interop or optional HTTP serving

## Directory Layout

- `parser/`:
  - parse snapshots and parse acceptance/rejection cases
- `ir/`:
  - minimal portable Core IR snapshots and lowering-focused cases
- `eval/`:
  - runtime result behavior for lowered programs
  - when a host supports allowlisted host interop, this also covers boundary cases such as host `None` -> Genia `none` and normalized explicit host errors
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
