# Flow Specs

This directory contains executable shared spec files for the active `flow` category.

Flow shared coverage is intentionally partial and limited to first-wave observable contract cases in this phase.

Flow cases in this directory must:

- include explicit terminal consumption through `collect` or `run`
- be deterministic
- test only observable behavior

Current first-wave Flow shared coverage proves only:

- lazy pull-based observable behavior through early termination (`stdin-lines-take-early-stop`)
- single-use enforcement (`flow-single-use-error`)
- deterministic outputs (`stdin-lines-collect-basic`)
- `refine(..steps)` behavior (`refine-step-emit-deterministic`)
- `rules(..fns)` compatibility behavior (`rules-rule-emit-deterministic`)
- `step_*` / `rule_*` equivalence (`step-rule-helper-equivalence`)
- `rules()` identity stage (`rules-identity-stage`)
- error propagation via invalid-reducer-on-flow diagnostic (`flow-error-propagation-sum-on-flow`)
- deterministic Option filtering in Flow pipelines via `keep_some(...)` (`flow-keep-some-parse-int`)

This directory does not define full Flow coverage.
