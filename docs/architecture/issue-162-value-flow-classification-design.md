# Issue #162 — Value-vs-Flow Classification (Deferred Slice) Design

## 1. Design summary

No interpreter changes are required. All four boundary error cases already
produce clean, actionable Genia errors. The work is:

1. Register the four new spec names in `test_spec_ir_runner_blackbox.py`
2. Add a classification table to `GENIA_STATE.md` (docs phase)

This is a tests + docs phase only. The implementation phase will be a no-op.

## 2. Scope lock (from spec)

Included:
- `test_spec_ir_runner_blackbox.py` — add 4 new names to discovery assertions
- `GENIA_STATE.md` — add classification table (deferred to docs phase)

Excluded:
- Any interpreter change
- Any prelude function change
- Any error message wording change

## 3. Architecture overview

The slice stays entirely in the **Specs / Tests / Docs zone**.

```
spec/eval/each-on-list-type-error.yaml      ← already committed
spec/eval/reduce-on-flow-type-error.yaml    ← already committed
spec/eval/first-on-flow-type-error.yaml     ← already committed
spec/flow/count-as-pipe-stage-type-error.yaml ← already committed
        │
        ▼
tools/spec_runner (unchanged)
        │
        ▼
tests/test_spec_ir_runner_blackbox.py  ← 4 new names added to assertions
        │
        ▼
GENIA_STATE.md  ← classification table added (docs phase)
```

No new runtime pathways. No new prelude surface.

## 4. Key finding: map and filter are intentionally hybrid

The interpreter has a special override at `interpreter.py:4652–4684`. When
`map` or `filter` is called with a `GeniaFlow` as the second argument, the
call site short-circuits Genia body resolution and returns a new `GeniaFlow`
directly. This is by design, not a gap.

Consequence: there is **no** boundary error case for `map(f, flow)` or
`filter(f, flow)`. The spec correctly omits these.

## 5. File changes

### Test phase

**`tests/test_spec_ir_runner_blackbox.py`**

`test_discover_specs_includes_eval_cases` — add to the subset assertion:
```python
"each-on-list-type-error",
"reduce-on-flow-type-error",
"first-on-flow-type-error",
```

`test_discover_specs_includes_flow_cases` — add to the subset assertion:
```python
"count-as-pipe-stage-type-error",
```

No other test changes needed. The spec runner already executes and validates
all four cases; the blackbox test additions are discovery guards only.

### Docs phase

**`GENIA_STATE.md`** — add a "Prelude Function Classification" section with
the table from the spec document. Placement: after the stdlib/prelude surface
description, before or within the existing "Standard Library" section.

Table columns: Function | Category | Flow input OK? | Flow output?

### Implementation phase

No files to change. Mark as no-op.

## 6. Complexity check

- [x] Minimal
- [x] Necessary
- [ ] Overly complex

The only mechanical change is four string additions to one test assertion and
one table addition to GENIA_STATE.md.

## 7. Risk

Low. All four specs are already passing. The test change is additive (subset
assertion). The GENIA_STATE.md change is documentation-only.

The one risk is if the error message text for `first` changes in the future
(it contains the internal label `<flow tick ready>` which depends on `tick`'s
label). This is acceptable — the spec is documenting current behavior.

## 8. Final check

- No implementation details beyond what spec requires
- No scope expansion beyond preflight/spec
- Consistent with `GENIA_STATE.md` authority model
