# Shared Spec Suite


This directory holds the shared cross-host spec suite for Genia.


# Shared Spec Suite

**Python is the only implemented host today.**

## Canonical Semantic-Spec Categories

- parse
- ir
- eval
- cli
- flow
- error

## Implemented Shared Spec Coverage

- `eval` — **active** (executable shared spec files)
- `ir` — **active** (executable shared spec files)
- `parse`, `cli`, `flow`, `error` — **scaffold-only** (no executable shared spec files yet)

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

**Purpose:**
- Keep all hosts aligned with the same language/runtime/CLI contract
- Validate behavior at the parse, Core IR, eval, CLI, flow, and error boundaries
- Reduce semantic drift between hosts

## Directory Layout

- `parse/`: parse scaffold only
- `ir/`: implemented IR cases (active)
- `eval/`: implemented eval cases (active)
- `cli/`: CLI scaffold only
- `flow/`: flow scaffold only
- `error/`: error scaffold only

**Note:**
- `eval/` and `ir/` contain executable shared spec files in this phase.
- Other category directories are present as scaffolds only and must contain only `README.md`.

**Normalization:**
- In the implemented eval suite, stdout/stderr line endings are normalized before comparison.
- In the implemented IR suite, portable Core IR is normalized before comparison.

**Test Types:**
- Shared contract tests: validate the cross-host contract for the categories above
- Host-local tests: validate host-specific or implementation details, but do not override shared spec results

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
