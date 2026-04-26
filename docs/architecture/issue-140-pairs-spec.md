# Issue #140 Spec — Normalize Pair-Like Values to Lists

**Phase:** spec
**Branch:** `issue-140-pair-lists-preflight`
**Issue:** #140 — Normalize Pair-Like Values to Lists (Remove Tuple Leakage from Public API)

This phase defines expected behavior only.
It does not add spec YAML files, failing tests, implementation, or documentation sync edits.

---

## 1. Source Of Truth

Final authority: `GENIA_STATE.md`

Supporting:
- `GENIA_RULES.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/architecture/issue-140-pair-lists-preflight.md`
- `docs/architecture/issue-162-stdlib-phase-1-normalization-spec.md`

Relevant existing truths:
- Python is the only implemented host and is the reference host.
- Active shared eval specs assert normalized `stdout`, `stderr`, and `exit_code`.
- Public pair-like values use 2-element Genia lists (settled by issue #162 first slice for `map_items`, `tee`, `zip`).
- Pattern matching `[a, b]` works against any 2-element Genia list.
- There is no `pairs` function in the current public API.
- `pairs` is named in issue #140 as a surface that should expose 2-element Genia lists.

---

## 2. Scope Decision

### Included in this spec

- Define the exact observable contract for `pairs(xs, ys)`.
- Define arity-2 behavior only.
- Confirm that `pairs` elements are 2-element Genia lists, pattern-matchable as `[a, b]`.

### Explicitly excluded from this spec

- `pairs(xs)` single-arg form — deferred. No current use case justifies it and adding it without a clear contract risks scope drift. Arity-2 only.
- Tuple destructuring syntax.
- Formalizing tuples as a public value type.
- Changes to internal dispatch, hashing, or AST/IR tuple uses.
- Any broad stdlib normalization beyond the pair-like surface.
- Implementation, failing tests, or docs sync.

---

## 3. `pairs(xs, ys)` Contract

### Signature

```
pairs(xs, ys)
```

- `xs` — a Genia list
- `ys` — a Genia list
- Returns a Genia list of 2-element Genia lists

### Semantics

`pairs(xs, ys)` zips two lists together, producing a list of `[x, y]` pairs.

The result length is bounded by the shorter of the two input lists.
If either input is empty, the result is `[]`.
If both inputs are the same length, every element of each list appears in exactly one output pair.

Each output element is an ordinary 2-element Genia list: `[xs_item, ys_item]`.
Each element is pattern-matchable without tuple knowledge:

```genia
pairs([1, 2], [3, 4]) |> map([a, b] -> a + b)
```

Must produce `[4, 6]`.

### Classification

`pairs` is a **value helper**:
- receives two ordinary Genia lists
- returns an ordinary Genia list of 2-element lists
- no Flow, no Option, no host-only behavior

It is the value-level analog of `zip` for Flows.
It does not accept Flow values as input; using `pairs` with a Flow is a type error.

### Maturity

**Experimental** in the initial implementation phase.
`GENIA_STATE.md` must label it Experimental until the audit confirms stable coverage.

---

## 4. Observable Cases (to become YAML in the test phase)

The following cases define the expected observable behavior.
These are not test code — they describe the contract.
YAML files are written in the test phase (before implementation).

### Case: pairs-basic

```
source: pairs([1, 2], [3, 4])
stdout: "[[1, 3], [2, 4]]\n"
stderr: ""
exit_code: 0
```

### Case: pairs-shorter-first

```
source: pairs([1, 2], [10, 20, 30])
stdout: "[[1, 10], [2, 20]]\n"
stderr: ""
exit_code: 0
```

The first list is shorter; result has 2 elements.

### Case: pairs-shorter-second

```
source: pairs([1, 2, 3], [10, 20])
stdout: "[[1, 10], [2, 20]]\n"
stderr: ""
exit_code: 0
```

The second list is shorter; result has 2 elements.

### Case: pairs-empty-first

```
source: pairs([], [1, 2])
stdout: "[]\n"
stderr: ""
exit_code: 0
```

### Case: pairs-empty-both

```
source: pairs([], [])
stdout: "[]\n"
stderr: ""
exit_code: 0
```

### Case: pairs-strings

```
source: pairs(["a", "b"], ["x", "y"])
stdout: "[[\"a\", \"x\"], [\"b\", \"y\"]]\n"
stderr: ""
exit_code: 0
```

Confirms non-numeric element types produce correct 2-element list output.

### Case: pairs-pattern-match

```
source: pairs([1, 2], [3, 4]) |> map(([a, b]) -> a + b)
stdout: "[4, 6]\n"
stderr: ""
exit_code: 0
```

Confirms output elements are pattern-matchable as `[a, b]` without tuple knowledge.

---

## 5. Cases NOT in scope

- `pairs(xs)` — arity-2 only; single-arg form is not defined.
- `pairs(flow, flow)` — Flow input is a type error; not a case to spec.
- Mixed list/flow inputs — type error; not a case to spec.
- Error cases for non-list input — type error coverage may be added in the test phase if the design requires it.

---

## 6. Cross-phase notes

### For the design phase

- Decide: implement as a pure Genia prelude function or a thin host primitive in `interpreter.py`.
- A pure Genia implementation using `reduce` or recursion is portable. A host primitive avoids Genia-level recursion for large lists.
- Recommendation: host primitive for correctness and performance, exposed as a thin prelude wrapper in `src/genia/std/prelude/map.genia` (alongside `map_items` and related pair helpers). Final decision in design phase.
- Register at arity-2: `env.register_autoload("pairs", 2, "std/prelude/map.genia")`.
- Add `@doc` annotation.

### For the test phase

Write these files (failing before implementation, passing after):
- `spec/eval/pairs-basic.yaml`
- `spec/eval/pairs-shorter-first.yaml`
- `spec/eval/pairs-shorter-second.yaml`
- `spec/eval/pairs-empty-first.yaml`
- `spec/eval/pairs-empty-both.yaml`
- `spec/eval/pairs-strings.yaml`
- `spec/eval/pairs-pattern-match.yaml`
- Pytest cases in `tests/test_maps.py` asserting shape and Python-list-not-tuple
- Register new spec case names in `tests/test_spec_ir_runner_blackbox.py`

### For the docs phase

In order:
1. `GENIA_STATE.md` — add `pairs` to pair-like helper surface; note Experimental maturity
2. `GENIA_RULES.md` — add pair-like invariant if warranted
3. `README.md` — add `pairs` to autoloaded prelude list
4. `GENIA_REPL_README.md` — add usage example if warranted
5. Cheatsheets — add `pairs` example once stable

---

## 7. Recommended next prompt (DESIGN phase)

```
You are working in the Genia repo on issue #140:
Normalize Pair-Like Values to Lists (Remove Tuple Leakage from Public API)

Spec is complete. Branch: issue-140-pair-lists-preflight.
Spec doc: docs/architecture/issue-140-pairs-spec.md

Design phase task:
1. Decide: implement pairs(xs, ys) as a pure Genia prelude function or a host primitive + thin wrapper.
   - Pure Genia: portable, uses existing list operations, but recursive for large lists
   - Host primitive: add pairs_fn in interpreter.py, register at arity-2, wrap in map.genia
   Recommendation: host primitive + thin prelude wrapper (consistent with map_items pattern)
2. Confirm placement: src/genia/std/prelude/map.genia alongside map_items
3. Describe the exact implementation steps (no code — design document only):
   - What goes in interpreter.py
   - What goes in map.genia
   - What register_autoload call is needed
   - What @doc annotation looks like
4. Commit with prefix: design(pairs): implementation plan for pairs(xs, ys) issue #140

Do NOT implement. Do NOT write tests. Do NOT update behavior docs.
Only write the design document and commit it.
```
