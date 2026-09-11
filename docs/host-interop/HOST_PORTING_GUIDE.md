# Host Porting Guide

This is the practical checklist for adding a new Genia host.

Python is the current reference host.
New hosts should align with Python's implemented semantics, not redefine them.

A ready-to-copy host template lives at `hosts/template/`. Copy it and follow `hosts/template/EXAMPLE.md` as your starting point.

## External Host Repository Model (R16 E16-6, issue #763)

A **substantial, independently versioned production host** belongs in its
own dedicated repository, not in this one. `m0smith/genia-cpp` is the
first such repository: R16 bootstraps it as a repository shell only (its
own `README.md`/`AGENTS.md`, a pinned `genia-2026` contract revision plus
E16-1 adapter-protocol version declaration, and a minimal
protocol-participation placeholder), with no real C++ interpreter — that
implementation work is R20, entirely in that repository.

The rule this establishes for any later external host (Node.js, Java,
Rust, Go, or another C++-style production effort):

- `genia-2026` remains the sole authority for the Genia language contract,
  Core IR portability boundary, shared specs (`spec/`), the generic
  conformance runner (`tools/spec_runner`), and the E16-1 host-adapter
  protocol. An external host repository implements Genia; it never
  defines Genia, and it never forks or copies `GENIA_STATE.md`,
  `GENIA_RULES.md`, `GENIA_REPL_README.md`, Core IR docs, or shared specs
  as editable local truth — it reads them from `genia-2026`.
- The external repository declares an exact pinned `genia-2026` contract
  revision and E16-1 adapter-protocol version (see `tools/spec_runner/
  protocol.py` and `tools/spec_runner/revision.py`), and updates that
  declaration deliberately as it advances, never silently.
- When the host's behavior disagrees with shared evidence, the host does
  not guess from another host's implementation. Per the drift-handling
  rule in `docs/strategy/roadmap/multi-host-conformance-policy.md`: fix
  the host if the contract is clear; if the contract is ambiguous, stop
  and clarify it upstream in `genia-2026` first.
- The corresponding `hosts/<name>/` directory in `genia-2026` stays a
  scaffolded placeholder (see `hosts/cpp/README.md` for the pattern) so no
  duplicate, authoritative-looking implementation ever exists in two
  repositories at once. It transitions to an explicit pointer only once
  the external repository actually exists.

A host small enough to develop entirely inside `genia-2026` (a thin
reference/experimental adapter, not a substantial independent production
effort) may still use the in-repository `hosts/<name>/` template path
below without a separate repository; that is a judgment call for each
host's own bootstrap ticket, not a rule this guide fixes.

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
10. relevant core docs/specs for the feature area you are touching

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
- HTTP serving
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
- **value equality and map-key identity** (R18) — see below

## What May Be Native Per Host

These may differ internally by host:

- parser implementation strategy
- AST node class design
- Core IR data structure representation
- evaluator engine internals
- threading/runtime primitives used for refs/processes
- package/build layout
- debugger transport internals

Rule:

- different internals are fine
- different observable Genia semantics are not

## Value Equality (R18)

Equality is the portability trap most likely to be missed, because a host gets a
plausible-looking `==` for free from its own language. Do not take it.

- Genia has **one** semantic equality relation. `==` denotes it, `!=` is exactly
  its negation, and it is **not user-overloadable**.
- Implement it as one internal operation with explicit dispatch over Genia
  semantic kinds. Do **not** fall back to the host language's equality for
  unrecognized values, and do **not** let a host container's key rules decide map
  keys.
- Literal patterns, repeated pattern bindings, `assert_eq`, map lookup/presence/
  insertion/replacement/removal/duplicate detection, and Sheet column-name
  identity must all answer exactly as `==` does. Implementing `==` correctly while
  leaving these on host equality is a non-conforming host.
- Booleans are a distinct kind and never equal numbers. If your host represents
  booleans as integers, test for booleans **before** any numeric branch.
- An integer equals a float only when the float is finite, integral, and denotes
  the same mathematical integer. Convert the float upward; never narrow an
  arbitrary-precision integer to a float.
- NaN is unequal to everything including itself, and that non-reflexivity must
  propagate through containers. A container comparison that shortcuts on element
  identity will get this wrong.
- Protected-carrier equality observes carrier identity only and must never
  disclose whether two independently acquired carriers hold equal payloads —
  through equality, containers, keys, patterns, assertions, rendering, or
  diagnostics. This is a security boundary, not a convenience.
- Map equality is equality of mappings and ignores insertion order; map
  **iteration** order is a separate observable governed by the unchanged R17
  contract.

Conformance evidence: the 24 `spec/eval/r18-*` and `spec/error/r18-*` cases. Start
with `r18-conformance-cross-family-summary.yaml`, whose failing index names the
broken family. Full contract: `docs/design/r18-portable-value-equality-contract.md`;
release summary: `docs/releases/R18.md`.

R18 defines no opaque-token surface reachable from Genia source, so a host is not
expected to demonstrate token equality; that family has no shared cases by design.

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
- if the host implements the optional HTTP serving capability, it must preserve:
  - request/response map shapes documented in `capabilities.md`
  - synchronous blocking phase-1 behavior
  - prelude-first user-visible routing/response semantics
  - exact-path routing only unless shared docs/specs are expanded
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
- relevant core docs/specs
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

If a host-local shortcut would change user-visible Genia behavior, do not take it.
