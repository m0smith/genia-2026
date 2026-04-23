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
- `cli` — **active** (executable shared spec files)
- `parse`, `flow`, `error` — **scaffold-only** (no executable shared spec files yet)

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

**Purpose:**
- Keep all hosts aligned with the same language/runtime/CLI contract
- Validate behavior at the parse, Core IR, eval, CLI, flow, and error boundaries
- Reduce semantic drift between hosts

## Directory Layout

- `parse/`: parse scaffold only
- `ir/`: implemented IR cases (active)
- `eval/`: implemented eval cases (active)
- `cli/`: implemented CLI cases (active)
- `flow/`: flow scaffold only
- `error/`: error scaffold only

**Note:**
- `eval/`, `ir/`, and `cli/` contain executable shared spec files in this phase.
- Other category directories are present as scaffolds only and must contain only `README.md`.

## Shared YAML Envelope

Executable shared specs use one top-level envelope:

- `name`
- `id` (optional)
- `category`
- `description` (optional)
- `input`
- `expected`
- `notes` (optional)

## CLI Specs

CLI specs live under `spec/cli/` and use `category: cli`.

CLI `input` fields:

- `source`
- `file`
- `command`
- `stdin`
- `argv`
- `debug_stdio`

CLI `expected` fields:

- `stdout`
- `stderr`
- `exit_code`

CLI mode mapping:

- file mode: `input.file`
- command mode: `input.command` with empty `input.stdin`
- pipe mode: `input.command` with non-empty `input.stdin`

For CLI specs, `stdin` is piped input data, not program text. Current shared pipe-mode specs use non-empty `stdin` to select `-p <command>`. Shared executable specs do not cover REPL mode.

**Normalization:**
- In the implemented eval suite, stdout/stderr line endings are normalized to `\n`. Trailing newlines remain significant.
- In the implemented CLI suite, stdout/stderr line endings are normalized to `\n` and trailing newlines are stripped before comparison.
- Internal whitespace is not trimmed or collapsed. Stderr is not otherwise normalized.
- In the implemented IR suite, portable Core IR is normalized before comparison.

**Test Types:**
- Shared contract tests: validate the cross-host contract for the categories above
- Host-local tests: validate host-specific or implementation details, but do not override shared spec results

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
