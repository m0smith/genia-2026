# Pipeline Semantics

Status: Design rationale

This note explains where Genia pipeline semantics live. It is not a replacement for `GENIA_STATE.md`, `GENIA_RULES.md`, or the shared semantic specs.

## Why

The old helper-first pipeline style made simple pipelines verbose and easy to get wrong. Automatic Option propagation lets maybe-returning helpers compose directly, so structured absence can travel through pipelines without turning normal missing-data cases into exceptions.

## Where semantics live

Pipeline behavior is split across clear layers:

- Parser/lowering: recognizes pipeline syntax and lowers it into Core IR.
- Core IR: preserves portable structure without embedding host-specific behavior.
- Evaluator/runtime: executes pipeline stages according to shared semantics.
- Prelude: provides user-facing helpers.
- Host bridge: exposes only the minimal host capabilities needed by the runtime.

## Portability boundary

Pipeline semantics must remain portable across hosts.

Rules:

- Do not define pipeline behavior in host-specific adapters.
- Do not make Python-only behavior part of the language contract.
- Keep Core IR as the portability boundary.
- Shared spec tests define expected behavior.
- Host implementations must conform to the shared contract rather than reinterpret it.

## Documentation rule

If pipeline behavior changes, update:

- `GENIA_STATE.md`
- `GENIA_RULES.md`
- relevant shared specs
- relevant examples
- this design note only if the architecture changes
