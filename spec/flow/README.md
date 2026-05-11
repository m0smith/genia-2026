# Flow Specs

This directory contains executable shared spec files for the active `flow` category.

Flow shared coverage is intentionally partial and limited to first-wave observable contract cases in this phase.

Flow shared specs cover the Flow side of the Seq contract only.
They do not define a public Seq runtime value, Seq syntax, or host iterator semantics.
List-side Seq behavior is covered through eval/list specs where applicable.

Flow cases in this directory must:

- include explicit terminal consumption through `collect` or `run`
- be deterministic
- test only observable behavior

Current first-wave Flow shared coverage proves only:

- lazy pull-based observable behavior through early termination (`stdin-lines-take-early-stop`)
- single-use enforcement (`flow-single-use-error`)
- deterministic outputs (`stdin-lines-collect-basic`)
- `evolve(init, f)` progression (`evolve-init-f-integer-progression`, `evolve-init-f-doubles-from-seed`)
- `refine(..steps)` behavior (`refine-step-emit-deterministic`)
- `rules(..fns)` compatibility behavior (`rules-rule-emit-deterministic`)
- `step_*` / `rule_*` equivalence (`step-rule-helper-equivalence`)
- `rules()` identity stage (`rules-identity-stage`)
- selected rule result defaulting and context persistence (`rules-defaulting-and-context`)
- structured `none(reason, context)` as a no-effect rule result (`rules-structured-none-skips`)
- error propagation via invalid-reducer-on-flow diagnostic (`flow-error-propagation-sum-on-flow`)
- deterministic Option filtering in Flow pipelines via `keep_some(...)` (`flow-keep-some-parse-int`)
- focused core stdlib Flow coverage: direct `map` over a Flow (`flow-map-basic`), direct `filter` over a Flow (`flow-filter-basic`), and a composed `map`/`filter` chain (`flow-map-filter-chain`)
- focused `scan` coverage over Flow inputs (`seq-compatible-flow-scan-basic`) and bounded infinite progression (`seq-compatible-flow-scan-bounded-evolve`)
- Seq-compatible `each` tap behavior preserving original Flow items while running effects (`seq-compatible-flow-each-preserves-items`)
- Seq-compatible terminal composition over `evolve` with `each(print) |> run` (`seq-compatible-evolve-each-run`)
- resource lifecycle composition over `drop |> take |> collect` with bounded pulling and correct output (`seq-finalization-drop-take`)

This directory does not define full Flow coverage.
Close/finalization counts remain covered by Python reference-host unit tests because shared specs expose only stdout, stderr, and exit_code.
