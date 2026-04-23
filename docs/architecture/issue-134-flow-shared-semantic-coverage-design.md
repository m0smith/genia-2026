# Issue #134 Flow Shared Semantic Coverage Design

## 1. Design scope

This design covers only what is required to make the approved Flow shared-spec contract executable in the shared spec system.

In scope:

- minimal Flow case structure
- Flow category execution through the shared runner
- comparison of Flow observable outputs
- minimal failure assertion design for current documented Flow failures

Out of scope:

- new Flow semantics
- Flow runtime redesign
- spec-system redesign beyond activating the existing `flow` category
- broader category expansion
- docs-sync work
- non-Python hosts

Narrowing choice:

- Flow should become an active executable category.
- Flow should not invent a second comparison model if the existing eval-style process surface already proves the approved contract.

## 2. Case structure

Flow cases should keep the shared top-level envelope already used by active categories:

- `name`
- `id` optional
- `category`
- `description` optional
- `input`
- `expected`
- `notes` optional

Minimal behavioral structure for `flow`:

- `input.source` required
- `input.stdin` optional
- `expected.stdout`
- `expected.stderr`
- `expected.exit_code`

How Flow differs from eval:

- `flow` is a separate category because it proves Flow semantics, not general eval behavior
- Flow source must explicitly include the Flow pipeline under test
- Flow source must explicitly include the terminal boundary that consumes the Flow

How Flow consumption is represented:

- `collect` is written directly in `input.source` when the case proves Flow-to-value materialization
- `run` is written directly in `input.source` when the case proves effectful Flow consumption
- no extra `mode`, `sink`, or `materialize` field should be introduced

Narrowing choice:

- The case schema should stay eval-like.
- The only Flow-specific distinction is category plus the expectation that `source` contains explicit Flow consumption.

## 3. Execution model

Flow cases should execute as command-source programs in the Python reference host, using the same subprocess model already used for eval command-source execution.

Execution flow:

1. load one `flow` case
2. run `input.source` through the Python interpreter command-source path
3. provide `input.stdin` to subprocess stdin when present
4. let the Genia program itself decide whether Flow is consumed by `collect` or `run`
5. wait for subprocess completion
6. compare only normalized observable outputs

How Genia source is executed:

- through the command-source interpreter path, not CLI pipe mode
- no automatic wrapper such as `stdin |> lines |> <stage_expr> |> run`
- no special runner-side Flow injection

How stdin is provided:

- raw text is passed directly to subprocess stdin
- when `input.stdin` is omitted or empty, the subprocess receives no input text

How Flow is consumed:

- by explicit source text only
- a case that ends with an unconsumed Flow value is invalid for shared Flow coverage in this phase because it does not prove the contract

When execution is complete:

- when the subprocess exits
- for `collect` cases, completion means the Flow has been materialized and the final rendered value has been emitted by normal command-source execution
- for `run` cases, completion means the Flow has been consumed to terminal effect completion

When to use `collect` vs `run`:

- use `collect` when the contract being proved is the deterministic materialized result of a Flow pipeline
- use `run` when the contract being proved is effectful consumption through `stdout` or `stderr`

How to ensure the Flow is actually consumed:

- require every Flow case to include an explicit terminal boundary in source
- valid terminals in this phase are `collect` and `run`
- a source that stops at a Flow-producing stage such as `stdin |> lines |> take(2)` is not a valid shared Flow case

Narrowing choice:

- Flow execution should reuse the existing eval subprocess path under the hood.
- Flow should not go through CLI `-p` mode, because that would test CLI wrapper behavior rather than the Flow contract itself.

## 4. Observable comparison surface

The compared Flow surface should be:

- `stdout` text
- `stderr` text
- `exit_code`

Normalization should match eval, not CLI:

- normalize `\r\n` and `\r` to `\n`
- keep trailing newlines significant
- do not trim internal whitespace

Success cases:

- compare `stdout`, `stderr`, and `exit_code` exactly after line-ending normalization

Failure cases:

- compare `stdout` exactly
- compare `exit_code` exactly
- compare `stderr` exactly unless the case is one of the narrow documented prefix-only failures described in section 9

Explicit exclusions:

- Python repr output
- internal Flow objects
- iterator or generator structure
- timing behavior
- memory identity
- internal buffering details
- scheduler behavior

Narrowing choice:

- Flow should use the same observable process surface as eval because that already matches the approved contract and avoids a second result model.

## 5. Single-use enforcement design

Single-use should be proved by one ordinary command-source Flow case that binds one Flow value, consumes it once, then attempts to consume the same Flow again.

Required source shape:

- create one bound Flow, for example `x = stdin |> lines`
- consume it once with an explicit terminal, preferably `collect`
- attempt the same or another terminal consumption again on the same bound Flow

Why this shape:

- it proves single-use directly
- it avoids depending on CLI pipe wrappers
- it keeps the failure entirely inside documented Flow behavior

How failure is captured:

- through the same subprocess stderr and exit-code capture used for all shared executable categories

Comparison choice for the minimal initial case:

- exact `exit_code`
- exact empty `stdout`
- exact `stderr` if the current implementation output is sufficiently stable for the chosen source

Narrowing choice:

- first-wave single-use should not require a new matcher type if one exact case is stable enough.
- if implementation discovers exact stderr is not stable enough, stop and review before broadening matcher semantics.

## 6. Equivalence testing design

Equivalence should be proved with mirrored ordinary cases, not with a new paired-assertion mechanism in the runner.

`refine` vs `rules`:

- use separate Flow cases
- keep stdin the same
- keep the semantic pipeline shape the same
- change only the public orchestration surface being proved
- require identical expected outputs

`step_*` vs `rule_*`:

- use the same separate-case approach
- keep all surrounding source the same
- change only the helper alias being proved
- require identical expected outputs

Why separate cases:

- the runner already operates one case at a time
- no cross-case comparator is needed
- failure reporting stays simple and local to one YAML file

Narrowing choice:

- do not add a runner feature that compares two cases to each other.
- prove equivalence by mirrored one-case-one-file expectations.

Implementation note:

- if the first-wave mirrored `refine-step-emit-deterministic` and `rules-rule-emit-deterministic` cases differ only by the preferred vs compatibility names and still produce identical output, they may jointly satisfy both equivalence requirements without adding an extra runner feature.

## 7. Category integration

Flow should integrate as an active executable shared category.

Directory structure:

- `spec/flow/` becomes the location for executable Flow YAML cases
- keep the directory flat in this phase
- do not introduce subdirectories

Runner detection:

- add `flow` to the active executable category list used by discovery/loading
- load `spec/flow/*.yaml` the same way other active categories are loaded

Category shape:

- `flow` is a new active category in the shared runner
- it is not a rename of `eval`
- it does not extend CLI mode handling

Execution path:

- Flow should have a dedicated category branch in the executor for category clarity
- that branch should delegate to a Flow host adapter path
- the Flow host adapter path should reuse the existing command-source subprocess behavior rather than inventing a different runtime mechanism

Narrowing choice:

- activate the already-declared `flow` category instead of overloading `eval`
- reuse existing subprocess execution behavior underneath instead of creating a new process protocol

## 8. Minimal initial case set mapping

### `stdin-lines-collect-basic`

Required inputs:

- `input.source`: `stdin |> lines |> collect`
- `input.stdin`: deterministic multiline text such as `a\nb\n`

Expected outputs:

- `stdout`: rendered collected list
- `stderr`: empty
- `exit_code`: success

Execution behavior:

- command-source execution
- explicit `collect` materializes the Flow
- process completion proves the source was fully evaluated

### `stdin-lines-take-early-stop`

Required inputs:

- `input.source`: `stdin |> lines |> take(2) |> collect`
- `input.stdin`: at least three lines

Expected outputs:

- `stdout`: rendered list containing only the first two items
- `stderr`: empty
- `exit_code`: success

Execution behavior:

- command-source execution
- `take(2) |> collect` forces consumption
- the observable proof of laziness is the truncated materialized result, not timing or internal read counts

Narrowing choice:

- this case proves early termination only through final observable output
- it does not attempt to prove internal read-count mechanics in shared specs

### `flow-single-use-error`

Required inputs:

- `input.source`: bind one Flow, consume it, consume it again
- `input.stdin`: deterministic multiline text

Expected outputs:

- `stdout`: empty
- `stderr`: current documented single-use failure surface
- `exit_code`: failure

Execution behavior:

- command-source execution
- first terminal consumes the Flow
- second terminal triggers the user-facing failure

### `refine-step-emit-deterministic`

Required inputs:

- `input.source`: `stdin |> lines |> refine((row, ctx) -> ... |> flat_map_some(step_emit)) |> collect`
- `input.stdin`: deterministic multiline text already known to produce deterministic output

Expected outputs:

- `stdout`: deterministic rendered collected result
- `stderr`: empty
- `exit_code`: success

Execution behavior:

- command-source execution
- explicit `collect` materializes the refined Flow output

### `rules-rule-emit-deterministic`

Required inputs:

- `input.source`: `stdin |> lines |> rules((row, ctx) -> ... |> flat_map_some(rule_emit)) |> collect`
- `input.stdin`: same deterministic input as the matching `refine` case

Expected outputs:

- `stdout`: exactly the same deterministic rendered collected result as the matching `refine` case
- `stderr`: empty
- `exit_code`: success

Execution behavior:

- command-source execution
- explicit `collect` materializes the ruled Flow output

### `step-rule-helper-equivalence`

Mapping choice:

- no special runner assertion
- satisfy this requirement with mirrored ordinary cases whose only intended observable difference is none

Required inputs:

- same deterministic source input across the mirrored cases

Expected outputs:

- identical `stdout`
- identical `stderr`
- identical `exit_code`

Execution behavior:

- same as the surrounding mirrored success cases

Narrowing choice:

- do not introduce a dedicated equivalence-only spec shape.
- implementation may satisfy this requirement through the mirrored `refine` / `rules` pair if that pair isolates the alias difference cleanly enough.

### `rules-identity-stage`

Required inputs:

- `input.source`: source Flow followed by `rules() |> collect`
- deterministic source input, either stdin-backed or inline list-backed

Expected outputs:

- `stdout`: unchanged rendered collected items
- `stderr`: empty
- `exit_code`: success

Execution behavior:

- command-source execution
- `collect` materializes the identity-transformed Flow

Narrowing choice:

- this case should prove `rules()` identity only.
- `refine()` identity should not be added unless implementation can prove it as pure alias behavior without broadening the approved contract.

## 9. Failure handling design

Expected failures should be expressed using the same overall process surface:

- `stdout`
- `stderr`
- `exit_code`

Default rule:

- use exact comparison

Partial matching:

- not required for the minimal first-wave case set if the chosen single-use failure case can use exact stderr
- permitted only for narrow documented Flow failure fragments if later implementation includes such a case in this issue

If partial matching is needed, the only allowed design in this phase is:

- one optional Flow failure matcher for `stderr` prefix

Constraints on that prefix matcher:

- no regex
- no substring contains matcher
- no generic matcher language
- still require exact `stdout`
- still require exact `exit_code`

Intended use:

- documented `invalid-rules-result:` failures, if and only if implementation includes one and exact stderr would be too brittle because of surrounding stage-context wording

How to avoid brittle comparisons:

- prefer exact success cases
- keep failure coverage narrow
- compare only the smallest documented stable failure surface
- do not freeze Python tracebacks or host-local preambles

Narrowing choice:

- because the minimal initial case set does not require a `rules` failure case, implementation should avoid adding a prefix matcher unless it becomes strictly necessary.

## 10. Constraints

This design reaffirms:

- no new Flow behavior
- no Flow redesign
- no shared-schema redesign beyond the minimal activation needed for `flow`
- no docs-sync work in this step
- no host expansion
- no CLI pipe-wrapper testing under the Flow category
- no broader helper coverage than the approved spec note

If implementation discovers a need for broader schema or matcher changes, that is a stop-and-review issue, not an implicit extension of this design.

## Design summary

Key decisions:

- activate `flow` as its own executable shared category
- keep Flow cases flat under `spec/flow/`
- use the existing shared top-level envelope
- keep Flow input eval-like: `source` plus optional `stdin`
- require explicit Flow consumption in source via `collect` or `run`
- execute Flow through the command-source subprocess path, not CLI pipe mode
- compare `stdout`, `stderr`, and `exit_code` with eval-style normalization
- prove equivalence through mirrored separate cases, not a new paired assertion mechanism

Assumptions:

- the Python command-source path is the correct observable boundary for first-wave Flow shared coverage
- first-wave single-use can likely use one exact stderr assertion for the chosen source
- the initial mirrored `refine` / `rules` cases can also satisfy the helper-alias equivalence requirement if written carefully

Risks:

- failure wording may be more brittle than success output
- implementation may be tempted to route Flow through CLI `-p`, which would blur the Flow/CLI boundary
- implementation may be tempted to broaden shared Flow coverage to helpers not included in the approved spec

Implementation step must follow exactly:

- add `flow` as an active executable category
- keep Flow case shape minimal and close to eval
- require explicit terminal consumption in every Flow case
- implement category-specific execution without inventing new semantics
- keep comparison limited to normalized `stdout`, normalized `stderr`, and exact `exit_code`
- avoid new matcher features unless exact first-wave failure assertions prove insufficient
