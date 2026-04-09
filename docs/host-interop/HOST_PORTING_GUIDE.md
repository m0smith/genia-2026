# Host Porting Guide

This is the practical checklist for adding a new Genia host.

Python is the current reference host.
New hosts should align with Python's implemented semantics, not redefine them.

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
10. relevant `docs/book/*` chapters for the feature area you are touching

## Minimal Host Requirements

A minimal conforming host should provide:

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

These may arrive later for a new host, but they must be marked honestly:

- `-p` / `--pipe`
- REPL
- Flow phase 1 runtime
- allowlisted host interop bridge
- refs
- process primitives
- bytes/json/zip bridge
- debugger stdio

Browser-target note (planned path):

- if a host targets browser playground execution, implement the browser runtime adapter contract scaffold documented in `docs/browser/RUNTIME_ADAPTER_CONTRACT.md`
- keep adapter behavior aligned with shared host contract docs/specs
- do not treat browser transport differences as language semantic differences

If a capability is missing:

- mark it missing in `HOST_CAPABILITY_MATRIX.md`
- keep docs truthful
- do not silently emulate different semantics under the same public surface

## What Must Stay Portable

These must preserve shared semantics across hosts:

- surface syntax acceptance/rejection
- AST->Core IR lowering meaning
- evaluation behavior after lowering
- public prelude helper behavior
- CLI mode behavior
- Flow contract
- normalized error behavior relied on by shared tests/docs

## What May Be Native Per Host

These may differ internally by host:

- parser implementation strategy
- AST node class design
- Core IR data structure representation
- evaluator engine internals
- threading/runtime primitives used for refs/processes
- package/build layout
- debugger transport implementation details

Rule:

- different internals are fine
- different observable Genia semantics are not

## Parser / IR / Runtime Checklist

- parser accepts current documented syntax only
- parser rejects invalid case placement and invalid patterns as documented
- lowering preserves current explicit pipeline IR semantics (source + ordered stages)
- Core IR remains the semantic boundary
- lowering output stays inside the frozen minimal portable Core IR node families defined in `docs/architecture/core-ir-portability.md`
- host-local optimized/post-lowering IR nodes remain outside the minimal portable Core IR contract
- runtime preserves current value families and callable behaviors
- if the host implements allowlisted host interop, the bridge must preserve:
  - host-null/host-None -> Genia `none`
  - explicit host errors for exceptions
  - no implicit Flow crossing at the bridge
- public helpers prefer prelude-backed behavior where feasible
- capability-backed builtins stay small and explicit

## Test Checklist

- add or update shared spec coverage under `spec/`
- run the host-local test suite
- ensure the host can satisfy the shared spec runner contract
- compare parse/lower/eval/CLI behavior against shared docs/spec expectations
- add regressions for any drift you fix

## Documentation Checklist

When you add or change host behavior, update:

- `GENIA_STATE.md` if Python behavior changes or if shared status changes
- relevant `docs/book/*`
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md`
- `spec/manifest.json` if the host contract changes
- host-local README/AGENTS files

If you add a new public capability:

- document it in the interop docs
- update the capability matrix
- add shared spec coverage

## Common Drift Risks

Avoid these:

- treating parser output as the portability boundary instead of Core IR meaning
- leaking host-local optimized IR nodes into the shared minimal lowered Core IR contract
- adding host-only convenience helpers that become de facto language features
- changing error wording/prefixes that user code or shared tests rely on
- keeping host-local docs more up to date than shared docs
- growing a second host-local help/discovery registry when prelude docstrings already provide the public source of truth
- treating planned hosts as implemented before code/spec coverage exists

## Final Rule

Shared spec tests and shared docs win over host-local convenience.

If a host-specific shortcut would change user-visible Genia behavior, do not take it.
