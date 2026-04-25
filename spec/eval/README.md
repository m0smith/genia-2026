# Eval Specs

Shared eval conformance cases for the Semantic Spec System.

This directory contains YAML cases for the active shared `eval` category.

Current shared eval coverage is limited to the executable eval contract surface:

- normalized `stdout`
- normalized `stderr`
- `exit_code`

Current eval case inventory covers deterministic command-source eval behavior for:

- final rendered expression results
- direct `stdout` output
- direct `stderr` output
- combined `stdout`/`stderr` output separation
- stdin-fed eval cases whose compared surface remains `stdout`, `stderr`, and `exit_code`
- direct Option rendering (`some(...)`, `none(...)`) in deterministic final-result output
- pipeline Option propagation (`some(...)` lift and `none(...)` short-circuit) in deterministic final-result output
- deterministic eval failures

This directory does not define shared coverage for:

- CLI mode selection
- pipe-mode execution
- REPL behavior
- parse, flow, or error category execution outside active eval cases
