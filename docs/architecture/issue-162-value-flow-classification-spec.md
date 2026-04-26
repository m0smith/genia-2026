# Issue #162 — Value-vs-Flow Classification (Deferred Slice) Spec

## 1. Purpose

This spec defines the behavior contract for the value-vs-Flow classification
slice of issue #162. It introduces **no new runtime semantics**. It adds four
shared spec cases that document and test the existing error surface at the
Flow/value boundary, and it prescribes the GENIA_STATE.md classification table
to be added in the docs phase.

## 2. Scope (from preflight)

### Included

- Four shared spec error cases covering the Flow/value boundary
- GENIA_STATE.md update: canonical classification table for all public prelude functions
- Unit test additions to `test_spec_ir_runner_blackbox.py` (spec discovery)
- Possibly one minimal interpreter guard if any misuse path currently crashes

### Excluded

- Any change to runtime semantics for `map`, `filter`, `reduce`, `each`, `first`, `last`, etc.
- New prelude functions or removal of existing ones
- Option-aware helper consistency (separate deferred slice)
- Pipe-mode guidance copy changes beyond what the classification table documents

## 3. Behavior definition

### Key finding from research

`map` and `filter` are **intentionally hybrid**: a special interpreter-level
override (interpreter.py:4652–4684) makes them work on both lists and Flows.
They are not "value functions that should error on Flow." This finding refines
the preflight's initial classification.

Revised classification:

| Function | Category | Flow input OK? | Flow output? |
|---|---|---|---|
| `map(f, xs)` | hybrid | YES (special case) | YES (returns Flow) |
| `filter(f, xs)` | hybrid | YES (special case) | YES (returns Flow) |
| `reduce(f, acc, xs)` | value | NO — errors | NO |
| `each(f, flow)` | Flow | NO (list → errors) | YES |
| `first(xs)` | value | NO — no matching case | NO |
| `last(xs)` | value | NO — no matching case | NO |
| `collect(flow)` | bridge | Flow only | NO (list) |
| `run(flow)` | bridge | Flow only | NO (nil) |
| `lines(source)` | bridge | list/string/Flow | YES |
| `tee(flow)` | Flow | Flow only | YES (`[Flow,Flow]`) |
| `merge(flow1,flow2)` | Flow | Flow only | YES |
| `zip(flow1,flow2)` | Flow | Flow only | YES |
| `tick()` / `tick(n)` | Flow | — | YES |
| `scan(step,init)` | stage | — | stage fn |
| `keep_some(...)` | Flow | Flow only | YES |
| `rules(..fns)` / `refine` | stage | — | stage fn |

### The four error cases specified

#### 1. `each` given a list (not a Flow)

```genia
each(print, [1, 2, 3])
```

Expected:
- stdout: `""`
- stderr: `"Error: each expected a flow, received list\n"`
- exit_code: `1`

#### 2. `reduce` given a Flow as its third argument

```genia
acc(a, b) = a
reduce(acc, 0, tick(3))
```

Expected:
- stdout: `""`
- stderr: `"Error: reduce expected a list as third argument, received flow\n"`
- exit_code: `1`

#### 3. `first` given a Flow

```genia
first(tick(3))
```

Expected:
- stdout: `""`
- stderr: `"Error: No matching case for function first/1 with arguments (<flow tick ready>,)\n"`
- exit_code: `1`

#### 4. `count` used as a Flow pipe stage

```genia
stdin |> lines |> count |> collect
```
stdin: `"1\n2\n3\n"`

Expected:
- stdout: `""`
- stderr: `"Error: pipeline stage 2 failed in Flow mode at count [<command>:1]: stage received flow; reduce expected a list as third argument, received flow\n"`
- exit_code: `1`

## 4. Semantics

### What is tested

Each case proves that the boundary is enforced by the runtime and the error
message is actionable. No silent type coercion is permitted.

### What is NOT tested

- `map(f, flow)` — intentionally permitted; no error spec needed
- `filter(f, flow)` — intentionally permitted; no error spec needed

## 5. Failure behavior

A test failure means either:
- the runtime no longer produces the exact error message (wording changed), or
- the runtime crashed (Python traceback) instead of producing a Genia error

## 6. Invariants

1. `each` accepts only GeniaFlow as its second argument.
2. `reduce` accepts only a list as its third argument.
3. `first` / `last` have no case matching GeniaFlow.
4. Value functions used as raw pipe stages produce pipe-mode error messages.
5. `map` and `filter` accept both list and Flow — this is by design, not a bug.

## 7. Spec file names

| File | Category |
|---|---|
| `spec/eval/each-on-list-type-error.yaml` | eval |
| `spec/eval/reduce-on-flow-type-error.yaml` | eval |
| `spec/eval/first-on-flow-type-error.yaml` | eval |
| `spec/flow/count-as-pipe-stage-type-error.yaml` | flow |

## 8. Non-goals

- Changing the error messages (spec must match current behavior)
- Changing `map`/`filter` hybrid behavior
- Adding new pipe-mode guidance in the error text

## 9. Implementation boundary

No implementation changes are required. All four error cases already produce
correct, actionable Genia errors. This spec only adds shared spec coverage
that documents and tests the existing surface.

If any of the four cases currently produces a Python traceback instead of a
Genia error, a minimal interpreter guard will be added before writing the spec.
(Investigation confirmed they do not — all four produce clean Genia errors.)

## 10. Documentation requirements

- `GENIA_STATE.md`: add the classification table from Section 3 above
- All other truth-hierarchy docs: no change required

## 11. Final check

- No implementation details that exceed preflight scope
- No scope expansion beyond preflight
- Consistent with `GENIA_STATE.md` authority model
- All four error messages confirmed by live execution
