# Error Shared Specs

This directory now holds the active executable shared error specs for the current phase.

## Scope

- Error specs assert normalized observable behavior only.
- The asserted surface is:
  - `stdout`
  - `stderr`
  - `exit_code`
- In this phase:
  - `stdout` must be exactly `""`
  - `stderr` must be an exact match
  - `exit_code` must be exactly `1`

## Execution Model

- Error specs reuse the eval execution path.
- There is no separate error execution path or subprocess.
- The runner uses the same shared YAML envelope as other executable categories.

## Notes Field

- `notes` is informational only.
- `notes` is not read by the runner and is not machine-asserted.
- `notes` may document human-readable contract concepts such as:
  - `error_phase`
  - `error_category`
  - `message_source`

## Current Coverage

- Coverage is active but initial, not complete.
- Phase, category, and message remain contract concepts, but they are not structured runner fields in this phase.
- The current initial inventory is:
  - `error-eval-undefined-name`
  - `error-parse-bad-rest-pattern`
  - `error-eval-assignment-target`
