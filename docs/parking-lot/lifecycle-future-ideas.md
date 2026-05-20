# Lifecycle Future Ideas

Status: **Parking lot / non-authoritative**

This note captures future ideas only. It does not define implemented Genia behavior.
If this conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## Core concept

A lifecycle is a named phase plan.

```text
LifecyclePlan
  phases
  scopes
  annotation bindings
  ordering rules
  failure rules
  cleanup rules
```

Key rule:

```text
Annotations mark candidates.
Lifecycle phases decide what runs.
Nothing runs merely because it is annotated.
```

## Module lifecycle split

Preserve this distinction:

```text
import module      -> load module definition / namespace
init(module, cfg)  -> create module instance
start(instance)    -> activate instance
stop(instance)     -> cleanup instance
```

Avoid making `import` run lifecycle hooks automatically.

## Execution mode lifecycle idea

Execution modes could eventually be expressed as lifecycle plans:

```text
command mode
file mode
pipe mode
REPL mode
spec/test mode
server mode later
notebook/playground mode later
```

Generic phase categories:

```text
init
load_source
bind_inputs
before
evaluate
emit
after
finalize
```

## Portable phase plans

Long-term, phase plans should be ordinary Genia data, not Python callables and not YAML.

Use the current symbol form:

```genia
quote(command_mode)
quote(file_mode)
quote(pipe_mode)
quote(execution)
quote(source)
```

Hypothetical shape:

```genia
command_mode_lifecycle = {
  name: quote(command_mode),
  phases: [
    {
      name: quote(init_context),
      action: quote(lifecycle_init_context),
      scope: quote(execution)
    },
    {
      name: quote(evaluate_command),
      action: quote(lifecycle_evaluate_source),
      scope: quote(execution)
    },
    {
      name: quote(finalize),
      action: quote(lifecycle_finalize_context),
      scope: quote(execution),
      always: true
    }
  ]
}
```

Treat this as hypothetical until implemented and tested.

## Host boundary

Lifecycle semantics should mostly live in Genia/prelude.

Host adapters should provide only capabilities that Genia cannot provide itself, such as:

- file access
- stdin/stdout/stderr
- process exit code bridge
- host-backed source construction
- parser/evaluator entry point while Python remains the only implemented host
- resource finalization for host-owned resources

## Minimal implementation path idea

Possible future sequence:

```text
1. Define lifecycle plan shape as portable Genia data.
2. Add lifecycle prelude runner primitives.
3. Add Python host lifecycle bridge.
4. Move command/file/pipe execution mode plans to portable lifecycle plans.
5. Add annotation-discovered phases.
```

## Non-goals for now

- no YAML lifecycle runner
- no new syntax
- no automatic annotation execution
- no server lifecycle implementation
- no notebook lifecycle implementation
- no change to current CLI behavior unless explicitly scoped

## Promotion trigger

Promote when the project is ready to define the first lifecycle contract or refactor execution modes without behavior change.
