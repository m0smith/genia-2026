# Issue 202 Contract: Internal `ExecutionMode` CLI Refactor

## 1. Purpose

Introduce a minimal internal `ExecutionMode` abstraction for CLI execution with no user-visible behavior change.

This contract defines preservation requirements only. It does not add a new Genia language feature, CLI mode, flag, runtime lifecycle, or public API.

## 2. Scope

Included:

- Represent the existing CLI execution branches with a minimal internal `ExecutionMode` structure.
- Preserve current file mode behavior exactly.
- Preserve current `-c` / `--command` behavior exactly.
- Preserve current `-p` / `--pipe` behavior exactly.
- Preserve current REPL fallback behavior exactly.
- Preserve current debug-stdio validation behavior exactly if the touched code crosses that path.

Excluded:

- No rows/awk mode.
- No lifecycle system.
- No annotation changes.
- No module system changes.
- No CLI flag changes.
- No output changes.
- No error message changes.
- No docs claiming new user-facing features.
- No registry, plugin system, or generalized mode framework beyond what is minimally needed for this refactor.

## 3. Behavior Definition

Observable CLI behavior must be byte-for-byte equivalent after line-ending normalization already used by existing tests/specs.

For each existing mode, the following are contract surfaces:

- `stdout`
- `stderr`
- process/entrypoint return code
- source filename used for diagnostics where already observable
- `argv()` contents
- stdin consumption behavior
- broken-pipe handling
- parse/runtime error formatting

The internal abstraction must not change parser behavior, evaluator behavior, Core IR lowering, Flow behavior, Option behavior, module loading, annotation behavior, or output rendering.

## 4. Mode Semantics To Preserve

File mode:

- `genia path/to/file.genia [args ...]` reads and evaluates the file.
- Remaining tokens after the file path are exposed through `argv()`.
- After top-level evaluation, `main/1` is preferred and called with `argv()`.
- If `main/1` is absent and `main/0` exists, `main()` is called.
- If neither entrypoint exists, the existing top-level result behavior is preserved.
- Option-like program paths remain rejected unless passed after `--`, exactly as today.

Command mode:

- `genia -c "source" [args ...]` evaluates inline source.
- Bare and option-like trailing tokens are exposed through `argv()` exactly as today.
- `--` handling remains exactly as today.
- After top-level evaluation, the same `main/1` then `main/0` convention as file mode is applied.
- Existing final-result printing behavior is preserved.

Pipe mode:

- `genia -p "stage_expr"` and `genia --pipe "stage_expr"` behave as:
  - `stdin |> lines |> <stage_expr> |> run`
- Pipe mode expects one stage expression, not a full program.
- Pipe mode bypasses the `main` convention.
- Explicit unbound `stdin` and explicit unbound `run` remain rejected with the current messages.
- Lambda parameters or ordinary local bindings named `stdin` or `run` remain allowed where currently allowed.
- Empty stdin, early termination, Flow single-use behavior, and broken-pipe behavior remain unchanged.
- Pipe-mode error guidance remains unchanged.

REPL mode:

- `genia` with no file, command, or pipe arguments still starts the existing REPL.
- No automatic `main` invocation is added in REPL mode.

Debug-stdio:

- Existing `--debug-stdio` validation remains unchanged:
  - rejects `-c`
  - rejects `-p`
  - requires exactly one program path
  - rejects missing program paths with the current parser error text
- The debug adapter behavior itself is not changed by this issue.

## 5. Failure Behavior

All existing failure behavior is preserved.

The refactor must not change:

- argparse exit code `2` cases
- `Error: ...` prefixes for runtime failures
- pipe-mode explanatory guidance
- file-not-found or invalid file-path behavior
- parse error text
- runtime error text
- stderr/stdout routing
- quiet broken-pipe behavior

Failures must not be converted into success values, structured `none(...)`, or different exception categories.

## 6. Invariants

- This issue introduces no new user-visible behavior.
- `ExecutionMode` is internal structure only.
- Existing mode selection inputs select the same effective execution path as before.
- Existing `stdout`, `stderr`, and exit codes remain identical for file, command, pipe, and relevant debug-stdio validation cases.
- `argv()` contents remain identical in file, command, and pipe modes.
- Pipe mode still wraps exactly as `stdin |> lines |> <stage_expr> |> run`.
- Pipe mode still bypasses `main`.
- File and command modes still apply the `main/1` then `main/0` convention.
- No current CLI flag is added, removed, renamed, or reinterpreted.
- No language semantics move into host-specific cleverness.

## 7. Examples

These examples are behavior-preservation examples, not new functionality.

Command mode:

```bash
genia -c "[1,2,3] |> count"
```

Expected observable behavior remains:

```text
stdout: 3
stderr:
exit_code: 0
```

Pipe mode:

```bash
printf 'a\nb\n' | genia -p 'head(1) |> each(print)'
```

Expected observable behavior remains:

```text
stdout: a
stderr:
exit_code: 0
```

File mode:

```bash
genia script.genia --pretty input.txt
```

The program still sees:

```genia
argv() == ["--pretty", "input.txt"]
```

## 8. Non-Goals

- Do not introduce rows/awk mode.
- Do not add lifecycle hooks.
- Do not alter CLI parsing.
- Do not alter program evaluation.
- Do not alter `run_source`.
- Do not alter `argv()`.
- Do not alter stdin or Flow semantics.
- Do not alter docs to describe a new user-facing feature.

## 9. Implementation Boundary

The contract is behavior-level and host-portable where the existing CLI contract is portable.

Implementation may organize the Python reference host CLI code internally, but:

- the abstraction is not part of the Genia language contract
- the abstraction is not part of Core IR
- future hosts are not required to expose the same internal class names or code shape
- shared conformance remains based on observable CLI behavior

## 10. Doc Requirements

`GENIA_STATE.md` already describes the user-visible CLI contract. Because this issue has no behavior change, it should not gain new semantic claims.

If docs are updated in the docs phase, they must say only that the refactor is internal/no-behavior-change. They must not claim new modes, lifecycle support, rows/awk behavior, or new CLI capabilities.

## 11. Complexity Check

Minimal: yes.

Necessary: yes.

Overly complex: no, if later phases keep the abstraction small and private.

Explanation:

The only allowed outcome is simpler internal organization around the already-implemented CLI branches. Any abstraction that changes behavior, exposes a new public model, or anticipates future modes beyond a narrow internal shape is too broad.

## 12. Final Check

- No implementation details required by this contract.
- No scope expansion.
- Consistent with `GENIA_STATE.md`.
- Behavior is precise and testable through `stdout`, `stderr`, and exit-code comparisons.
- Ready for design phase.
