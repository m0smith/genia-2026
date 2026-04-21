# Shared Spec Suite


This directory holds the shared cross-host spec suite for Genia.

**Python is the only implemented host today.**
Shared semantic-spec contract categories are:
  - parse
  - ir
  - eval
  - cli
  - flow
  - error

Implemented shared spec coverage in this phase:
  - `eval` (active, executable shared spec files)
  - `cli` (scaffold-only)
  - `flow` (scaffold-only)
  - `pattern` (scaffold-only)
  - `error` (scaffold-only)
  - `parse` (scaffold-only)
  - `ir` (scaffold-only)

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
- `parser/`: parse scaffold only
- `ir/`: IR scaffold only
- `eval/`: implemented eval cases (active)
- `cli/`: CLI scaffold only
- `errors/`: error scaffold only
- `flows/`: flow scaffold only

Prelude behavior may live in the most relevant category for now, usually `eval/`, `cli/`, or `flows/`.

**Normalization:**
In the implemented eval suite, stdout/stderr line endings are normalized before comparison. The current shared runner compares only `stdout`, `stderr`, and `exit_code`.

**Test Types:**
- Shared contract tests: validate the cross-host contract for the categories above
- Host-local tests: validate host-specific or implementation details, but do not override shared spec results

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
