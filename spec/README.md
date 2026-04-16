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
- `browser_runtime_adapter.implemented_hosts` is empty in this phase; there are no implemented browser runtime adapter hosts

Python is the only implemented host today.
The live Python implementation is still under `src/genia/`; `hosts/python/` is a future-layout documentation scaffold.
The spec layout is being added now so future hosts can validate against the same contract instead of growing host-local behavior.
The shared spec runner layout is still scaffolded/planned in this phase, not implemented as generic multi-host execution tooling.

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


## Phase 2 Strictness, Normalization, and Error Contract

**The Python reference host enforces strict, deterministic, and unambiguous conformance as of Phase 2.**

- All observable outputs (runtime, CLI, errors) are strictly normalized to canonical forms; no host-local or Python-specific leakage is allowed.
- Error objects must include required fields: category, message, and span (when applicable). Categories are strictly separated (parse/runtime/CLI).
- Malformed, missing, or unsupported cases must fail validation with explicit normalized errors; nothing is silently skipped.
- Output ordering and structure must be deterministic and stable.
- Only the minimal portable Core IR node families are used in lowering and output (see `docs/architecture/core-ir-portability.md`).
- CLI and flow behaviors must be strictly validated for output, error, and exit code normalization.
- GENIA_STATE.md is the final authority for implemented behavior; all specs and docs must align with it.

See also:

- `spec/manifest.json`
- `tools/spec_runner/README.md`
- `docs/host-interop/HOST_INTEROP.md`
