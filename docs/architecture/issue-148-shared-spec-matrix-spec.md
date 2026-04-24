# Issue #148 Spec — Shared Spec Matrix For Pipeline, CLI, And Flow Modes

## 1. Scope

This issue defines the next shared-semantic coverage expansion for already-implemented pipeline, CLI, and Flow-mode behavior in the Python reference host.

Included in this phase:

- shared executable coverage for already-documented pipeline `|>` behavior where it is observable through current `eval`, `cli`, or `flow` contract surfaces
- shared executable coverage for deterministic non-interactive CLI file mode
- shared executable coverage for deterministic non-interactive CLI `-c` command mode
- shared executable coverage for deterministic non-interactive CLI `-p` pipe mode
- shared executable coverage for the already-documented observable differences between command/file mode and pipe mode
- runner-test expansion only if required to load or execute already-documented case shapes

Excluded from this phase:

- new language semantics
- parser redesign
- CLI redesign
- Flow redesign
- new host behavior
- broad refactors
- any attempt to execute parse cases through a new mechanism beyond what the current runner already supports
- non-Python hosts

This issue expands proof of the current contract. It does not define new semantics.

## 2. Portable observable contract

The shared contract to prove now is limited to these already-documented observable behaviors:

- pipeline `|>` preserves ordinary call shape in command/eval contexts
- CLI file mode executes a source file deterministically
- CLI file and command mode apply the documented runtime `main` convention where it already exists
- CLI command mode executes inline source deterministically
- CLI pipe mode wraps the provided stage expression as `stdin |> lines |> <stage_expr> |> run`
- CLI pipe mode is Flow-oriented and therefore differs intentionally from command/file mode
- pipe mode rejects explicit unbound `stdin`
- pipe mode rejects explicit unbound `run`
- pipe mode reports clear guidance when a bare per-item function receives the whole Flow
- pipe mode reports clear guidance when a bare reducer or other non-Flow final result is used where the implicit final `run` requires a Flow
- command/file mode and pipe mode must not be blurred into one execution contract

This contract does not prove implementation internals such as argument-parser structure, Python subprocess details, internal wrapper source generation, or prelude layout.

## 3. Category boundaries

This issue intentionally spans three active shared categories, but the boundary between them must stay explicit:

- `eval`
  - use only when the behavior being proved is ordinary source evaluation rather than CLI dispatch
  - suitable for a small pipeline call-shape proof such as `1 |> inc`
- `cli`
  - use for file mode, `-c`, `-p`, trailing argv behavior, `main` dispatch behavior, and mode-specific diagnostics
- `flow`
  - use for direct command-source Flow behavior that does not depend on CLI mode selection

Boundary rule:

- `-p` wrapper behavior is CLI contract, not Flow-category contract
- direct `stdin |> lines |> ...` Flow behavior without CLI mode selection belongs to `flow`
- ordinary non-CLI pipeline semantics belong to `eval` or `ir`, depending on what is being asserted

## 4. Covered behaviors

Shared specs added later for this issue should cover exactly these behavior groups:

- pipeline call-shape proof in ordinary command/eval context
  - a minimal `|>` case should prove already-documented stage application behavior without involving CLI wrapper logic
- file mode execution path
  - at least one case should prove file execution through the shared CLI suite
  - file mode may also prove current `main(argv())` behavior only if that behavior is already documented and stable
- command mode execution path
  - at least one case should prove inline command execution
  - command mode may also prove current trailing `argv()` exposure and/or `main` dispatch behavior only if already documented and stable
- pipe mode execution path
  - at least one case should prove stdin lines flowing through a valid Flow stage expression
  - at least one case should prove that pipe mode remains a Flow contract, not a per-item direct-call contract
- flow-vs-command differences
  - at least one paired proof should show that a final value is valid in `-c` or file mode but rejected in `-p`
  - at least one paired proof should show that a bare per-item function is invalid in `-p` unless wrapped in a Flow stage such as `map(...)`

This issue should prove the smallest useful matrix for the documented behavior, not an exhaustive CLI catalog.

## 5. Minimal initial matrix

The later test/implementation steps should target a small matrix like this:

- `eval` / pipeline:
  - ordinary pipeline call-shape proof such as `1 |> inc`

- `cli` / file mode:
  - basic file execution
  - file mode `main(argv())` dispatch if already documented and stable

- `cli` / command mode:
  - basic inline execution
  - trailing `argv()` behavior
  - command-mode success for a final collected/reduced value when already implemented

- `cli` / pipe mode:
  - valid Flow-stage execution over stdin lines
  - rejection of explicit `stdin`
  - rejection of explicit `run`
  - rejection of bare per-item stage such as `parse_int`
  - rejection/guidance for bare reducer such as `sum`
  - rejection/guidance for non-Flow final result such as `collect`

- paired mode-difference proofs:
  - `-c` success vs `-p` failure for a final reduced/materialized value
  - `-p map(parse_int)` success vs `-p parse_int` failure

Case naming should stay concrete and behavior-oriented. This note does not choose the final filenames.

## 6. Failure / error cases

Cover now:

- explicit unbound `stdin` in pipe mode
- explicit unbound `run` in pipe mode
- bare per-item function misuse in pipe mode
- bare reducer misuse in pipe mode
- non-Flow final result misuse in pipe mode
- deterministic malformed mode/argument combinations only where the current wording/exit behavior is already stable enough to be shared-contract proof

Do not broaden now to:

- REPL behavior
- host tracebacks
- shell-tokenization behavior
- undocumented malformed invocation cases
- debugger transport/runtime behavior beyond current deterministic argument validation

Narrowing choice:

- if a diagnostic is already documented as clear guidance in `GENIA_STATE.md`, `GENIA_REPL_README.md`, or `README.md`, it is a candidate for shared proof
- if the wording is not yet clearly frozen or is only covered in host-local tests, leave it out of this issue

## 7. Core invariants

All shared cases added later in this issue must preserve these invariants:

- compared behavior is portable and observable
- each case executes independently
- cases remain deterministic
- CLI mode differences are explicit rather than inferred
- pipe mode remains Flow-oriented
- command/file mode remain ordinary source execution paths
- shared cases do not depend on Python-specific leakage
- uncovered CLI or Flow behavior remains unguaranteed

## 8. Non-goals

Out of scope for this issue:

- expanding the pipeline operator semantics
- changing `main` dispatch behavior
- changing `argv()` behavior
- broadening Flow semantics beyond current first-wave coverage
- proving every existing host-local CLI test in the shared suite
- REPL coverage
- parse shared-spec redesign
- browser or other host behavior

## 9. Truth alignment notes

This spec step exposes two immediate alignment facts for later phases:

- the shared-spec documentation should describe CLI shared coverage as active, not scaffold-only
- later docs-sync work must describe the expanded shared matrix only to the exact extent the executable cases and runner support actually land

Expected later alignment points:

- `GENIA_STATE.md`
- `GENIA_REPL_README.md`
- `README.md`
- `spec/README.md`
- `spec/cli/README.md`
- `spec/flow/README.md`
- `tools/spec_runner/README.md`

Those broader truth-synchronization edits belong to later phases unless required to correct a direct contradiction in the current spec docs.

## 10. Acceptance criteria for the later implementation step

This issue is complete only when all of the following are true:

- executable shared cases prove a small documented matrix across pipeline, file mode, command mode, pipe mode, and mode-difference behavior
- the shared suite proves only already-implemented behavior
- pipe mode and command/file mode remain clearly distinct in the shared contract
- any runner-test additions prove only already-supported or newly-required shared case loading/execution paths
- no new semantics are introduced
- docs later describe the exact expanded matrix and no more

## Spec decision summary

This issue defines a narrow expansion of the shared semantic-spec matrix:

- one small ordinary pipeline proof
- clearer CLI file / command / pipe coverage
- explicit shared proof that pipe mode is a Flow wrapper rather than a generic command-evaluation mode
- paired proofs for the already-documented differences between `-p` and `-c` / file mode

The next Design step must map this contract into exact case inventory, category placement, and runner expectations without changing semantics.
