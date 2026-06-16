# Lifecycle Vocabulary

## Status

This document defines proposed R4 lifecycle vocabulary and non-goals. It is proposed R4 architecture vocabulary, not implemented runtime behavior.

`GENIA_STATE.md` is the final authority for implemented behavior. This document does not describe implemented runtime behavior unless `GENIA_STATE.md` and tests prove that behavior, and it does not change current execution semantics.

Lifecycle vocabulary is host-independent. It must not be defined as Python-only behavior, and Python implementation sketches do not define portable lifecycle semantics.

## Purpose

This document gives later R4 work one shared vocabulary for lifecycle plans, phases, scopes, bindings, ordering, cleanup, and failure rules.

It is an architecture boundary document. It is not a language feature announcement, runtime contract, tutorial, lifecycle runner design, or host adapter API.

## Source of truth

For implemented behavior, use this order:

1. `GENIA_STATE.md`
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. executable specs and tests
6. architecture and host-interop docs

If this document appears to conflict with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Scope

In scope:

- proposed R4 lifecycle vocabulary
- lifecycle plan, phase, scope, binding, cleanup, failure, and ordering terms
- lifecycle annotation binding vocabulary
- explicit non-goals that prevent vocabulary work from becoming runtime work
- host-independent wording for later portable lifecycle contracts

Out of scope:

- runtime behavior
- parser or syntax changes
- lifecycle runner implementation
- annotation execution behavior
- import/load activation semantics
- host adapter rewrites

## Vocabulary

`lifecycle` means an ordered conceptual model for entering scopes, running phases, handling resources, reporting failures, and giving owned cleanup a chance to run. In this document it is vocabulary only.

`LifecyclePlan` or lifecycle plan means a named portable description of a lifecycle. A lifecycle plan may name phases, scopes, ordering rules, lifecycle resources, lifecycle cleanup, lifecycle failure expectations, and optional bindings. A lifecycle plan is not an implemented runtime value, executable phase graph, YAML runner, plugin surface, or host adapter API.

`LifecyclePhase` or lifecycle phase means a named step inside a lifecycle plan. A phase may state its lifecycle scope, ordering rule, cleanup or failure expectations, and bindings for candidate discovery. Lifecycle phases decide execution in a future implemented lifecycle.

`LifecycleScope` or lifecycle scope means a lifetime boundary for resource ownership, cleanup opportunity, and failure reporting. Possible future vocabulary scopes include execution, module, test, source, and flow. These names do not mean generalized lifecycle scopes are implemented today.

`entered scope` means a scope whose lifecycle has begun. If an owned scope is entered, its cleanup gets a chance to run according to the relevant cleanup rule in a future implemented lifecycle.

`resource ownership` means the explicit rule that says which lifecycle scope owns a resource and is responsible for cleanup. Resource ownership must not be inferred from annotation presence alone.

`lifecycle resource` means a resource whose lifetime is associated with a lifecycle scope. The vocabulary requires explicit resource ownership before lifecycle cleanup responsibilities can be assigned.

`CleanupRule` or lifecycle cleanup means the rule for cleanup opportunity after an owned scope is entered. The base vocabulary is: if an owned scope is entered, its cleanup gets a chance to run. This does not implement cleanup hooks.

`FailureRule` or lifecycle failure means the rule for how phase failures affect later phases, cleanup opportunity, and reporting. Future lifecycle behavior must state which phase failed, which scope was active, whether later phases are skipped, whether cleanup still runs, and how the failure is reported.

`LifecycleBinding` or lifecycle binding means a rule that connects a lifecycle phase to discoverable candidates. A binding may identify a phase name, candidate source, filters, ordering rule, required or optional behavior, and failure behavior.

`lifecycle annotation binding` means a lifecycle binding whose candidate source is annotation metadata. Annotations may mark declarations as annotation candidates, but annotation metadata does not run the declaration by itself.

`annotation candidate` means a declaration or value marked with annotation metadata and available for possible selection by a future lifecycle binding.

`inert annotation rule` means annotations are metadata unless a future lifecycle phase explicitly consumes them through a lifecycle binding.

`OrderingRule` means deterministic participant order within a phase. Initial ordering vocabulary includes `source_order` and `reverse_source_order`.

`source_order` means candidates are processed in deterministic source order.

`reverse_source_order` means candidates are processed in the reverse of deterministic source order.

`ExecutionMode` means the way Genia source is invoked and run, such as file, command, pipe, REPL, or native test mode. `execution mode lifecycle` is vocabulary for a possible future lifecycle associated with an execution mode; it is not a runtime execution-mode refactor in this issue.

`test lifecycle` means vocabulary for a possible lifecycle shape around native-test execution. Existing native test behavior must not be generalized into setup or teardown lifecycle semantics.

`module lifecycle` means vocabulary for a possible lifecycle shape around module loading or module-level resources. It is not module instance lifecycle behavior and does not change import/load semantics.

`load/import/activation boundary` means the separation between loading source, importing modules, and activating lifecycle work. Load/import is not activation.

## Inert annotation rule

Annotations mark candidates. Lifecycle phases decide execution.

Annotations do not execute merely because they exist.

Imports and loading must not auto-run lifecycle work. The presence of annotation metadata must never by itself cause evaluation, setup, teardown, import-time work, activation, resource acquisition, or cleanup.

Current annotation behavior remains limited to behavior documented in `GENIA_STATE.md`. Existing test/native annotation behavior must not be generalized into lifecycle setup/teardown semantics.

## Load / import / activation boundary

Load/import is not activation.

Loading source or importing a module may make declarations available, but it must not secretly start lifecycle work. A future lifecycle design must state the activation point explicitly.

This document does not add hidden import/start behavior.

## Ordering vocabulary

Lifecycle participant ordering must be deterministic.

The initial vocabulary terms are:

- `source_order`
- `reverse_source_order`

Illustrative/proposed, not current runtime behavior:

```text
unit_test_lifecycle
  module_before
  test_before
  test
  test_after
  module_after
```

This text block is not runnable Genia syntax and does not describe implemented lifecycle execution.

## Cleanup and failure vocabulary

If an owned scope is entered, its cleanup gets a chance to run.

Cleanup rules must state which scope owns cleanup responsibility and how cleanup participants are ordered.

Failure rules must state:

- which lifecycle phase failed
- which lifecycle scope was active
- whether later phases are skipped
- whether cleanup still gets a chance to run
- how the failure is reported

This vocabulary does not add a new runtime error type or structured diagnostic format.

## Current implementation status

Generalized lifecycle plans are not implemented runtime behavior.

Lifecycle runners are not implemented runtime behavior.

Phase graph execution is not implemented runtime behavior.

Setup/teardown lifecycle hooks are not implemented runtime behavior.

Generalized annotation bindings are not implemented runtime behavior.

Python is currently the reference host, as described by `GENIA_STATE.md`, but lifecycle vocabulary is not Python-only behavior.

Native test behavior remains the current behavior documented in `GENIA_STATE.md`. Native-test annotation discovery does not imply setup/teardown lifecycle hooks, generalized annotation execution, module lifecycle behavior, or execution mode lifecycle behavior.

## Non-goals

This issue explicitly excludes:

- no lifecycle runner implementation
- no runtime execution-mode refactor
- no setup/teardown execution
- no parser syntax changes
- no Core IR changes
- no YAML lifecycle runner
- no server lifecycle implementation
- no actor lifecycle implementation
- no plugin lifecycle implementation
- no browser lifecycle implementation
- no notebook/playground lifecycle implementation
- no module instance lifecycle implementation
- no module instance lifecycle behavior
- no hidden import/start behavior
- no host adapter rewrite
- no Flow/Seq behavior changes
- no native test runner lifecycle refactor
- no broad runtime architecture rewrite
- no annotation execution behavior
- no lifecycle plan runtime value
- no executable phase graph

## How later R4 issues use this document

Later R4 issues may cite this document for terminology and boundaries.

They must still define, test, and document any implemented behavior in the correct source-of-truth files. This document alone does not make lifecycle behavior available.

Later work should prefer references to this document over restating the vocabulary in every issue. If later work changes implemented behavior, it must update `GENIA_STATE.md`, relevant docs, and tests in the appropriate phase.
