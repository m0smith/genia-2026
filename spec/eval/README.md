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
- deterministic pattern matching behavior for currently implemented pattern families (literal, wildcard, variable binding, list/tuple, map, option, guard, and glob forms)
- deterministic eval failures
- focused core stdlib list/absence helper behavior: `map` over lists (basic and empty), `filter` over lists (basic, no-match, and Option-element callbacks), `first` (some and empty-list), `last` (some and empty-list), `nth` (in-range and out-of-bounds)
- `apply_raw(f, args)` behavior: ordinary-value equivalence, none-arg body-execution (bypasses short-circuit), empty-args, and baseline contrast with normal none-propagating call (issue #188)
- `reduce` shared contract: basic left-fold over a non-empty list, empty-list base-case returning initial accumulator, and none-element delivery to callback without short-circuit (issue #190)

This directory does not define shared coverage for:

- CLI mode selection
- pipe-mode execution
- REPL behavior
- parse, flow, or error category execution outside active eval cases
