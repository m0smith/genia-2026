# Shared Spec Suite


This directory holds the shared cross-host spec suite for Genia.

**Python is the only implemented host today.**
The Python host adapter implements the shared host contract for these categories:
  - parse
  - ir
  - eval
  - cli
  - flow
  - error

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

**Purpose:**
- Keep all hosts aligned with the same language/runtime/CLI contract
- Validate behavior at the parse, Core IR, eval, CLI, flow, and error boundaries
- Reduce semantic drift between hosts

**Spec Categories:**
- parse snapshots
- IR snapshots
- eval behavior
- stdout/stderr/exit-code behavior
- CLI behavior
- Flow behavior
- error normalization behavior

**Directory Layout:**
- `parser/`: parse snapshots and parse acceptance/rejection cases
- `ir/`: minimal portable Core IR snapshots and lowering-focused cases
- `eval/`: runtime result behavior for lowered programs, including host interop boundary cases
- `cli/`: file mode, `-c`, `-p`, REPL-adjacent CLI behavior, stdout/stderr, exit codes
- `errors/`: normalized category/message/span expectations
- `flows/`: Flow phase-1 and `rules(..fns)` behavior

Prelude behavior may live in the most relevant category for now, usually `eval/`, `cli/`, or `flows/`.

**Normalization:**
All observable outputs (values, errors, IR, CLI, flow) are normalized to canonical, host-neutral forms. No Python-specific details are allowed in normalized outputs. Only the minimal portable Core IR node families are used in the contract. Error objects are normalized with required fields and strict category separation.

**Test Types:**
- Shared contract tests: validate the cross-host contract for the categories above
- Host-local tests: validate host-specific or implementation details, but do not override shared spec results

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
