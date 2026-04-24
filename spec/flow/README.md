# Flow Specs

This directory contains executable shared spec files for the active `flow` category.

Flow shared coverage is intentionally partial and limited to first-wave observable contract cases in this phase.

Flow cases in this directory must:

- include explicit terminal consumption through `collect` or `run`
- be deterministic
- test only observable behavior

Current first-wave Flow shared coverage proves only:

- lazy pull-based observable behavior through early termination
- single-use enforcement
- deterministic outputs
- `refine(..steps)` behavior
- `rules(..fns)` compatibility behavior
- `step_*` / `rule_*` equivalence
- `rules()` identity stage

This directory does not define full Flow coverage.
