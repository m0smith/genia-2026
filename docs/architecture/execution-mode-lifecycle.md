# Execution Mode Lifecycle Proposal

## Status

This is an R4 execution-mode lifecycle proposal. It is not implemented runtime behavior.

`GENIA_STATE.md` is the final authority for implemented behavior. Current behavior remains unchanged: this document does not change runtime, CLI, parser, Core IR, annotation, Flow, host adapter, prelude, native-test, or REPL behavior.

This document is an architecture proposal and contract surface for future lifecycle work. It does not make execution-mode lifecycle plans executable.

## Purpose

Execution-mode lifecycle vocabulary describes how Genia source could be run under explicit mode contracts without making load/import behavior implicit or surprising.

For each execution mode, the proposal shape is:

```text
source/input acquisition
  -> context binding
  -> evaluation
  -> output/normalization
  -> cleanup/finalization
```

The exact phases may vary by mode. A lifecycle plan is a named phase plan, not a fixed global sequence.

## Core Concepts

`ExecutionMode` describes how Genia source is run under a mode contract. A mode defines source acquisition, input binding, context or session state, evaluation, output, failure, and finalization expectations.

`LifecyclePlan` describes an ordered phase plan for an execution mode. A plan may name phases, scopes, ordering rules, cleanup rules, failure rules, and optional bindings. This is not an implemented runtime object in this proposal.

`LifecycleBinding` describes which annotations, resources, or functions a phase consumes. A binding may define the phase name, candidate kind, filters, ordering, required or optional status, and failure behavior.

Proposal-only symbolic names should use current Genia symbol form when symbols are needed:

```genia
quote(command_mode)
quote(file_mode)
quote(pipe_mode)
quote(repl_mode)
quote(spec_mode)
quote(execution)
quote(source)
quote(flow)
```

These examples show symbol spelling only. They are not executable lifecycle examples.

## Shared Contract Rules

Annotations are inert until consumed by a lifecycle phase.

Annotations mark candidates. Lifecycle phases decide what runs.

Annotations never execute themselves. Only lifecycle phases with explicit bindings consume annotations.

Loading source or importing a module is not lifecycle activation. Loading/importing source must not automatically run lifecycle hooks.

Cleanup/finalization is designed around entered scopes: if a scope was entered, cleanup runs for entered scopes and gets a chance to release owned resources in future lifecycle work.

Ordering must be deterministic. Setup-like proposal phases use source order where applicable; teardown-like proposal phases use reverse source order where applicable.

Failure reporting should be phase-aware in the proposal. A future diagnostic should identify the execution mode, phase, scope, reason, and source location when available.

## Common Proposal Shape

```text
execution_mode_lifecycle:
  init
  load_source
  bind_inputs
  mode_before
  evaluate
  mode_after
  emit
  finalize
```

This shape is proposal only. It does not imply implemented phase execution, a lifecycle runner, setup/teardown hooks, or current CLI behavior changes.

## Command Mode

Proposed contract: command mode is one-shot execution of command source under an isolated command context.

```text
command_mode_lifecycle:
  init
  load_command_source
  bind_command_context
  command_before
  evaluate_command
  command_after
  emit_result
  finalize
```

`command_before` and `command_after` are proposal phases only. They do not implement annotation execution or setup/teardown behavior.

## File Mode

Proposed contract: file mode runs a source file using current file-mode behavior as the behavioral authority.

```text
file_mode_lifecycle:
  init
  load_file
  bind_argv
  file_before
  evaluate_file
  dispatch_main
  file_after
  emit_result
  finalize
```

Loading a file is distinct from lifecycle activation. Main dispatch remains limited to current implemented behavior in `GENIA_STATE.md` and `GENIA_REPL_README.md`.

## Pipe Mode

Proposed contract: pipe mode binds an input source, builds a pipeline, consumes the pipeline according to current Flow behavior, and finalizes owned source resources.

```text
pipe_mode_lifecycle:
  init
  bind_stdin_source
  load_pipe_source
  build_pipeline
  pipe_before
  consume_pipeline
  pipe_after
  finalize_source
  finalize
```

Pipe-mode lifecycle language must preserve current lazy, pull-based Flow behavior without adding new Flow behavior. `pipe_before` and `pipe_after` are proposal phases only.

## REPL Mode

Proposed contract: REPL mode is a persistent session with repeated form evaluation.

```text
repl_mode_lifecycle:
  init
  activate_session
  repl_before
  repeat:
    read_form
    evaluate_form
    emit_result
  repl_after
  finalize
```

REPL mode exists today, but shared executable spec coverage does not include REPL mode unless `GENIA_STATE.md` says otherwise. `repl_before` and `repl_after` are proposal phases only.

## Spec/Test Execution Mode

Proposed contract: spec/test execution mode runs isolated cases with explicit input binding and normalized output comparison where current spec infrastructure defines it.

```text
spec_mode_lifecycle:
  init
  load_spec_case
  bind_spec_inputs
  evaluate_case
  normalize_outputs
  finalize_case
  finalize
```

This execution-mode lifecycle is separate from the Genia-native unit-test lifecycle. It must not expand current native-test behavior, annotation discovery, output, or exit-code behavior.

## Annotation Binding Example

Proposal example, not current behavior:

```text
phase command_before:
  annotation: setup
  filters:
    scope: command
  ordering: source_order
```

Meaning at the proposal level: a future lifecycle phase could consume declarations marked as setup candidates for command scope. `@setup runs automatically` is a forbidden implemented-behavior claim; `@setup` behavior is not implemented.

`@teardown runs automatically` is also a forbidden implemented-behavior claim; teardown-like behavior is not implemented. `@route does not start a server`.

## Future-Only Examples

Server mode is future-only and not implemented:

```text
server_mode_lifecycle:
  init
  load_server_source
  bind_server_config
  server_before
  activate_listener
  repeat:
    accept_request
    bind_request
    handle_request
    finalize_request
  deactivate_listener
  server_after
  finalize
```

Notebook/playground mode is future-only and not implemented:

```text
notebook_mode_lifecycle:
  init
  load_document
  activate_session
  repeat:
    select_cell
    evaluate_cell
    emit_cell_result
  save_session_state
  finalize
```

These examples are proposal sketches only. They do not implement server mode, notebook/playground mode, browser runtime behavior, route annotations, or new host capabilities.

## Non-Implementation Boundary

This issue implements no lifecycle runner.

This issue implements no annotation execution.

No setup/teardown hook support is claimed as implemented.

This issue implements no `@setup` behavior and no `@teardown` behavior.

This issue implements no server mode.

This issue implements no notebook/playground mode.

This issue adds no new syntax.

This issue makes no current CLI behavior changes.

This issue makes no runtime behavior changes.

This issue makes no host adapter changes.

This issue makes no Core IR changes.

Generalized lifecycle runner is implemented only if future work updates `GENIA_STATE.md`, relevant docs, and tests to say so. This proposal does not do that.
