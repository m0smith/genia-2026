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
- `flow` — **active** (executable shared spec files; first-wave coverage only)
- `parse` — **active** (executable shared spec files; initial coverage only)
- `error` — **active** (executable shared spec files; initial coverage only)

Browser execution is planned to use the Python reference host on a backend service in the current playground direction; this does not add a second implemented host today.

**Purpose:**
- Keep all hosts aligned with the same language/runtime/CLI contract
- Validate behavior at the parse, Core IR, eval, CLI, flow, and error boundaries
- Reduce semantic drift between hosts

## Directory Layout

- `parse/`: implemented parse cases (active; initial coverage only)
- `ir/`: implemented IR cases (active)
- `eval/`: implemented eval cases (active)
- `cli/`: implemented CLI cases (active)
- `flow/`: implemented Flow cases (active; first-wave coverage only)
- `error/`: implemented error cases (active; initial coverage only)

**Note:**
- `eval/`, `ir/`, `cli/`, `flow/`, `error/`, and `parse/` contain executable shared spec files in this phase.
- Flow shared coverage is intentionally limited to first-wave observable contract cases.
- Error shared coverage is intentionally limited to initial observable normalized error contract cases.
- Parse shared coverage is intentionally limited to initial stable syntax forms; parse spec coverage expands only when new forms are explicitly added and tested.

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

## Parse Specs

Parse specs live under `spec/parse/` and use `category: parse`.

Parse `input` fields:

- `source`

Parse `expected` fields:

- `parse` — a mapping with:
  - `kind: ok` plus `ast: {...}` for a successful parse
  - `kind: error` plus `type: SyntaxError` and `message: "..."` for a parse failure

For `kind: error` cases, `message` is matched as a substring of the actual error message.

Parse specs validate the normalized parse boundary: the parser produces a deterministic, host-neutral AST snapshot for valid inputs, and a deterministic error type plus message for invalid inputs. Only stable, already-implemented syntax forms may appear in parse specs.

**Normalization:**
- In the implemented eval suite, stdout/stderr line endings are normalized to `\n`. Trailing newlines remain significant.
- In the implemented CLI suite, stdout/stderr line endings are normalized to `\n` and trailing newlines are stripped before comparison.
- In the implemented Error suite, stdout/stderr line endings are normalized to `\n`. Trailing newlines remain significant.
- Internal whitespace is not trimmed or collapsed. Stderr is not otherwise normalized.
- In the implemented Error suite, the asserted surface remains only `stdout`, `stderr`, and `exit_code`; current cases require `stdout: ""`, exact `stderr`, and `exit_code: 1`.
- In the implemented IR suite, portable Core IR is normalized before comparison.
- In the implemented Parse suite, the asserted surface is `expected.parse`; successful cases compare the normalized AST exactly; error cases compare `type` exactly and `message` as a substring.

**Test Types:**
- Shared contract tests: validate the cross-host contract for the categories above
- Host-local tests: validate host-specific or implementation details, but do not override shared spec results

**GENIA_STATE.md is the final authority for implemented behavior. All other docs/specs must align with this contract.**
