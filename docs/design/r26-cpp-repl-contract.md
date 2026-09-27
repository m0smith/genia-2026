# R26-1 — C++ REPL Contract

Status: **Approved contract; not implemented by the C++ host.** Issue #1023
defines this focused portability slice under the completed R26 pre-flight
(#1015). `GENIA_STATE.md` remains final authority for implemented behavior.

## 1. Purpose

This contract defines the smallest portable REPL observation boundary needed
before a second host implements a REPL. It does not promote the Python
reference host's terminal UI or implementation heuristics into language
semantics.

The `repl` capability is independently claimable. It does not imply support
for Flow, pipe mode, HTTP, data bridges, debugger stdio, resource I/O, shell
stages, configuration/providers, AI/retrieval, or any R27 surface.

## 2. Portable observations

A host declaring `repl: supported` must provide these observations:

1. Invoking the CLI with no mode or program arguments selects a REPL session.
2. The session evaluates a sequence of complete Genia programs in one
   persistent top-level environment. Bindings established by a successful
   submission are available to later submissions.
3. A submission may span multiple input lines. Evaluation starts only after
   the host parser determines that the accumulated source is a complete
   program. Parser correctness remains governed by the existing parse
   contract; this requirement does not standardize a textual completeness
   heuristic.
4. A non-empty successful submission writes its final value, rendered by the
   existing canonical debug renderer, followed by one newline to `stdout`.
   This includes `none("nil")`. Program output occurs through the existing
   output-sink contract and is not suppressed by the REPL echo.
5. A failed submission writes the existing normalized CLI diagnostic in the
   form `Error: <diagnostic>` followed by one newline to `stderr`. The session
   remains available for a later submission. This contract makes no rollback
   guarantee for effects or bindings performed before the failure.
6. End-of-input terminates the session successfully after all complete
   submissions have been processed. An incomplete buffered submission at
   end-of-input is discarded and is not evaluated.
7. REPL evaluation does not perform file/command mode's implicit `main/1` or
   `main/0` dispatch.

The portable observation is the complete session's ordered `stdout`, ordered
`stderr`, and exit code. It does not require cross-stream event ordering.

## 3. Host-local mechanics

The following remain host-local and are not conditions of `repl` support:

- banner text, primary and continuation prompts, colors, line editing,
  history, terminal detection, and whether prompts are emitted for
  non-interactive input;
- the parser-completeness algorithm, provided incomplete source is not
  evaluated and complete source is evaluated;
- interrupt and signal handling;
- Python's `:help`, `:env`, and `:quit` commands, including the contents and
  ordering of `:env`;
- exposure of host implementation names or host-global environment details;
- per-submission cross-stream interleaving beyond each stream's own order.

A host may offer host-local conveniences, but shared conformance evidence must
not depend on them. In particular, the Python banner, `>>> ` / `... ` prompts,
and colon commands are not portable output.

## 4. Evidence boundary

Portable parity is a combination of:

- shared executable, capability-gated whole-session CLI observations for the
  requirements in section 2; and
- bounded host-specific tests for terminal/UI mechanics that section 3 keeps
  outside the portable contract.

Shared REPL observations use the existing `cli` category, `repl` optional
capability, R16 subprocess protocol, and E16-7 evidence document. They do not
create a second protocol, evidence format, runner, category, or capability.
Every shared REPL case must declare `requires: [repl]`.

The existing protocol can represent a deterministic scripted, non-TTY,
whole-session observation. TTY behavior, interrupts, and per-submission
cross-stream timing are not portable parity evidence.

## 5. Capability and gap rule

Python implements the section 2 observations. Shared executable REPL evidence
now exists as three capability-gated `cli` cases declaring `requires: [repl]`
(`spec/cli/repl_persistent_binding_basic.yaml`,
`spec/cli/repl_failed_submission_diagnostic.yaml`,
`spec/cli/repl_none_result_rendering.yaml`), and they pass via the R16 runner
against the Python reference host. C++ remains unsupported for `repl`.

The C++ host must not declare `repl: supported`, and the known-host-gap entry
must remain, until it passes this capability-gated shared REPL evidence via
the R16 runner. Removing the gap additionally requires the host parity gate to
report `repl` as `PARITY_OK`.

Making this evidence honestly comparable required one narrow Python
reference-host fix: `repl()` previously wrote its banner and `>>> `/`... `
prompts to `stdout` unconditionally, even though section 3 already documents
them as host-local cosmetics outside the portable contract. `repl()` now
checks `sys.stdin.isatty()` and suppresses both when `stdin` is not an
interactive tty, so a scripted/piped session's `stdout` is exactly the
section 2 portable observation. This is a reference-host defect repair, not a
semantic or contract change: section 2's observations are unchanged, and
interactive terminal use is unaffected.

## 6. Exclusions

R26-1 adds no syntax, parser form, Core IR node, evaluator behavior, builtin,
prelude function, Flow behavior, pipe behavior, data bridge, host capability,
or C++ implementation. It does not claim Python/C++ feature parity.

Implementation begins only after a separate test phase lands the failing
shared evidence against the unsupported C++ host. C++ implementation and the
eventual capability/gap update are follow-up work, not part of this contract
change.
