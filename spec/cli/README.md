# CLI Specs

This directory contains executable shared spec files for the active `cli` category.

CLI shared coverage is intentionally partial and limited to deterministic non-interactive behavior in this phase.

CLI cases in this directory must:

- cover only file mode, `-c` command mode, `-p` pipe mode, or explicit `--debug-stdio` argument validation
- assert only normalized `stdout`, normalized `stderr`, and exact `exit_code`
- remain deterministic
- avoid REPL behavior
- avoid Python-specific leakage that is not part of the documented CLI contract

Current CLI shared coverage proves:

- basic file mode execution (`file_mode_basic`)
- file mode trailing argv exposure (`file_mode_argv`)
- file mode preservation of option-like trailing argv as plain strings (`file_mode_double_dash`)
- file mode `main(argv())` dispatch (`file_mode_main_argv`)
- basic command mode execution (`command_mode_basic`)
- command mode trailing argv exposure (`command_mode_argv`)
- command mode preservation of option-like trailing args (`command_mode_double_dash`)
- command mode final-value execution (`command_mode_collect_sum`)
- basic pipe mode execution over stdin lines (`pipe_mode_basic`)
- pipe mode valid per-item stage usage (`pipe_mode_map_parse_int`)
- pipe mode empty trailing argv behavior (`pipe_mode_argv_empty`)
- pipe mode bypass of file/command `main` dispatch (`pipe_mode_bypass_main`)
- pipe mode rejection of explicit unbound `stdin` (`error_pipe_mode_explicit_run`)
- pipe mode rejection of explicit unbound `run` (`pipe_mode_explicit_run_error`)
- pipe mode guidance for a bare per-item stage (`pipe_mode_bare_parse_int_error`)
- pipe mode guidance for a bare reducer (`pipe_mode_sum_error`)
- pipe mode guidance for a non-flow final result (`pipe_mode_collect_error`)
- deterministic file-mode parse/runtime failures (`error_parse`, `error_runtime`)
- deterministic `--debug-stdio` / mode-validation behavior (`debug_stdio_suppression`)

Shared CLI coverage does not yet prove the full CLI surface.

In particular, this directory does not define executable shared coverage for:

- REPL mode
- every malformed mode/arg combination
- every pipe-mode guidance diagnostic
- every flow-vs-command difference already tested in host-local tests
- Python-host-only debugger runtime behavior beyond deterministic argument validation

The `flow` shared category proves direct Flow observable behavior.
CLI `-p` wrapper behavior belongs in this `cli` category, not in `spec/flow/`.
