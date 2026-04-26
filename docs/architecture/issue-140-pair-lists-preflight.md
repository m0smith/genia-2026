# Issue #140 Preflight — Normalize Pair-Like Values to Lists

**Phase:** preflight
**Branch:** `issue-140-pair-lists-preflight`
**Issue:** #140 — Normalize Pair-Like Values to Lists (Remove Tuple Leakage from Public API)

---

## BRANCH

- Starting branch: `main`
- Working branch: `issue-140-pair-lists-preflight` (newly created)
- No semantic code changes are made in this phase.

---

## 1. CHANGE NAME

**Normalize Pair-Like Values to Lists — Remove Tuple Leakage from Public API**

---

## 2. SCOPE LOCK

### Change includes

- Full inventory of remaining public-facing Python tuple leakage after issue #162 first slice
- Confirming which current public APIs already return proper 2-element Genia lists
- Identifying any remaining surfaces where Python tuples can reach public API callers
- Defining the exact contract for `pairs(xs)` / `pairs(xs, ys)` as a new function
- Adding formal spec coverage for the pair-like list contract (spec phase only)
- Adding failing tests before any implementation (test phase)
- Implementing the `pairs` function and any remaining normalization (implementation phase)
- Syncing docs to reflect the settled contract (docs phase)

### Change does NOT include

- Adding tuple pattern matching
- Adding tuple destructuring syntax
- Formalizing tuples as a public Genia value type
- Changing AST / IR / function-dispatch tuple internals unless the inventory proves they are public leakage
- Changing `_split_flow_pair` internal defensive tolerance
- Changing `_freeze_map_key` internal hashing tuples
- Changing `TailCall` or dispatch-arg tuple use in the evaluator
- Changing host-interop `_genia_map_key_to_host` or freeze internals
- Any broad stdlib normalization beyond the pair-like contract (that is issue #162)
- New syntax forms
- Repo-wide renames
- Implementing anything in this pre-flight phase

---

## 3. SOURCE OF TRUTH

### Authoritative files (read for this pre-flight)

1. `GENIA_STATE.md` — final authority; pair-like shape described in §2 (value model), §11 (map), §19 (flow)
2. `GENIA_RULES.md` — implementation invariants; §4 and §8 for tuple patterns as internal-only
3. `GENIA_REPL_README.md` — `tee(flow)` documented as returning `[left_flow, right_flow]` as a public two-element list pair
4. `README.md` — confirms `[left_flow, right_flow]` as the tee pair contract
5. `docs/architecture/issue-162-stdlib-phase-1-normalization-audit.md` — audit of first slice; explicitly notes remaining #140 scope

### Relevant implementation / tests / docs to inspect

- `src/genia/interpreter.py` — `GeniaMap.items()`, `tee_fn`, `zip_flow_fn`, `scan_fn`, `seeded_rand_fn`, `seeded_rand_int_fn`, `_split_flow_pair`, `_python_host_to_genia`, `_freeze_map_key`
- `src/genia/utf8.py` — `format_debug`, `format_display` (no Python tuple branch; would fall through to `repr(t)` if a tuple leaked to display)
- `src/genia/std/prelude/map.genia` — `map_items`, `map_item_key`, `map_item_value`, `map_keys`, `map_values`
- `src/genia/std/prelude/flow.genia` — `tee`, `zip`, `merge`, `scan`
- `src/genia/std/prelude/cli.genia` — `cli_parse` return shape
- `spec/eval/map-items.yaml` — confirms `map_items` returns `[["a", 1], ["b", 2]]`
- `spec/flow/flow-zip-list-pairs.yaml` — confirms `zip` emits `[[left, right], ...]`
- `spec/flow/flow-tee-zip-list-pairs.yaml` — confirms `tee |> zip` chain emits list pairs
- `tests/test_maps.py` — `test_map_items_returns_key_value_pairs`
- `tests/test_pairs.py` — tests for Genia Pair primitives (`cons`, `car`, `cdr`)

### Any conflicts or unclear truth

- There is no current `pairs` function in the public API despite the issue description naming it as a surface to normalize. Its exact signature and semantics need definition in the spec phase.
- The `_split_flow_pair` internal function accepts both Python `tuple` and `list` as defensive tolerance — this is intentional internal behavior, not a public API. No conflict.

---

## 4. CURRENT BEHAVIOR

### Where tuple leakage currently exists

After issue #162 first slice (`67f7618`), the following surfaces were confirmed clean:

| Surface | Current return shape | Status |
|---|---|---|
| `GeniaMap.items()` | `[[raw_key, raw_value], ...]` — Python list of lists | ✓ Clean |
| `map_items(m)` | `[[key, value], ...]` — 2-element Genia lists | ✓ Clean |
| `tee(flow)` | `[left_flow, right_flow]` — Python list (not tuple) | ✓ Clean |
| `zip(f1, f2)` or `zip(pair)` | emits `[left, right]` per item | ✓ Clean |
| `rand(rng_state)` | `[GeniaRng, float]` — Python list | ✓ Clean |
| `rand_int(rng_state, n)` | `[GeniaRng, int]` — Python list | ✓ Clean |
| `cli_parse(args)` | `[opts, positionals]` — Genia 2-element list | ✓ Clean |

**Remaining potential leakage surfaces requiring verification in later phases:**

| Surface | Assessment | Action needed? |
|---|---|---|
| `_split_flow_pair` accepts `tuple \| list` | Purely internal; `tee` already returns a list; defensive tolerance only | No |
| `_freeze_map_key` returns Python tuples | Internal map key hashing; never exposed as a Genia value | No |
| `TailCall(target, tuple(args))` | Internal dispatch arg packaging; never exposed as a Genia value | No |
| `format_debug` / `format_display` | No Python tuple branch; would use `repr(t)` as fallback — a latent display risk if any tuple leaked | Guard by ensuring no function returns Python tuple |
| `_python_host_to_genia` converts Python tuples → Genia lists | Already normalizes at host boundary | ✓ Clean |
| Public `scan(step, init, flow)` | Requires user step to return `[state, output]` — a Genia list; enforced at runtime | ✓ Clean |

**No remaining known public tuple leakage** after issue #162 first slice. Verification in the test phase (exhaustive runtime checks) remains needed to confirm no edge case.

### Whether each occurrence is public API or internal implementation

- All confirmed Python tuple uses are internal: dispatch, hashing, parser/IR fields, TailCall packaging, type annotations.
- No public function currently returns a Python tuple as a visible Genia value.
- `pairs(xs)` does not yet exist.

---

## 5. DESIRED BEHAVIOR

### Exact public contract for pair-like values as 2-element lists

All public APIs that produce pair-like structured values must return ordinary 2-element Genia lists. Pattern matching on `[a, b]` must work against every publicly produced pair.

Current clean surfaces (already implemented):
- `map_items(m)` → `[[key, value], ...]`
- `zip(flow1, flow2)` → emits `[left, right]` per item
- `tee(flow)` → `[flow1, flow2]` as a 2-element list

New function to add:
- `pairs(xs, ys)` → `[[xs_item, ys_item], ...]` — zip two lists into a list of 2-element lists. This is the value-level analog of `zip` for flows. Length is bounded by the shorter list.
- `pairs(xs)` is a single-arg form: if `xs` is already a list of lists, return it as-is with shape validation; alternatively, reserve as an identity/alias for now. The spec phase must resolve whether `pairs(xs)` has a meaningful single-arg form or is arity-2 only.

Pair helper functions (already exist and are clean):
- `map_item_key([k, v])` → `k`
- `map_item_value([k, v])` → `v`

No tuple-based pattern matching should be required by any public API consumer.

---

## 6. FEATURE MATURITY

- `map_items` / `map_item_key` / `map_item_value` / `tee` / `zip` pair-like shape: **Stable** (implemented, tested, spec-covered)
- `pairs(xs, ys)` new function: **Experimental** — not yet defined; must go through spec → design → test → implementation before being labeled anything else
- Tuple-free public API invariant: **Partial** — the main surfaces are clean; `pairs` is not yet defined; no formal "no public tuple leakage" shared spec guard exists

Docs should describe `pairs` as **Experimental** in all phases until the audit confirms it is test-covered.

---

## 7. CONTRACT vs IMPLEMENTATION

### Portable semantics

- Pair-like public values are 2-element ordinary Genia lists.
- Pattern matching `[a, b]` must work against any publicly produced pair.
- There is no `Pair` type in the public value model for structured results; `cons`/`car`/`cdr` Pairs are a separate linked-list primitive.
- `pairs(xs, ys)` is portable if specified: it is a pure list operation with no host-specific behavior.

### Python reference-host implementation details

- `GeniaMap.items()` returns Python `list[list[Any]]` — already a Python list of lists.
- `tee_fn` returns a Python `list` of two `GeniaFlow` values.
- `zip_flow_fn` yields Python `list` `[left, right]` per item.
- `seeded_rand_fn` and `seeded_rand_int_fn` return Python `list` `[state, value]`.
- `_split_flow_pair` accepts both Python `tuple` and `list` as internal defensive tolerance; this must not change.
- `_python_host_to_genia` already converts Python tuples to Genia lists at the host boundary.
- A new `pairs_fn` in `interpreter.py` would use Python list comprehension and return a Python list of Python lists.

### What remains internal tuple usage

The following internal Python tuple uses are correct and must not change:
- `TailCall(target, tuple(args))` — function dispatch
- `_freeze_map_key` result tuples — map key hashing
- Parser/AST dataclass fields typed as `tuple` — `TuplePattern.items`, `IrPatTuple.items`
- `CompiledGlobPattern.tokens: tuple[GlobToken, ...]` — immutable token sequence
- `GlobToken("CLASS", (negated, tuple(entries)))` — immutable class definition
- Type annotations: `tuple[GrobToken, ...]`, `tuple[str, int]`, etc.
- Internal helper return types: `_line_col`, `_flatten_pipeline_ast`, `try_parse_function_header`, etc.

---

## 8. TEST STRATEGY

### Existing tests likely affected

- `tests/test_maps.py` — `test_map_items_returns_key_value_pairs` already passes; add a guard that no item is a Python tuple
- `tests/test_pairs.py` — tests Genia Pair primitives; confirm naming does not conflict with new `pairs` function
- `tests/test_flow_phase1.py` — `test_tee_public_result_is_list_pair_not_python_tuple` already passes
- `spec/eval/map-items.yaml` — already passes; no change needed
- `spec/flow/flow-zip-list-pairs.yaml` and `flow-tee-zip-list-pairs.yaml` — already pass

### New failing tests needed before implementation

1. `test_pairs_two_lists_produces_list_of_pairs` — `pairs([1, 2], [3, 4])` returns `[[1, 3], [2, 4]]`
2. `test_pairs_shorter_list_bounds_result` — `pairs([1, 2, 3], [10, 20])` returns `[[1, 10], [2, 20]]`
3. `test_pairs_empty_input` — `pairs([], [1, 2])` returns `[]`
4. `test_pairs_items_are_2_element_lists_not_tuples` — each item is a Python `list`, not a Python `tuple`
5. `test_pairs_items_are_pattern_matchable` — `[a, b] -> ...` pattern matches every result element
6. (Optional) `test_pairs_single_arg_behavior` — only if the spec phase defines a single-arg form
7. Shared spec case: `spec/eval/pairs-basic.yaml` — `pairs([1, 2], [3, 4])` stdout `[[1, 3], [2, 4]]`
8. Shared spec case: `spec/eval/pairs-shorter-bound.yaml` — shorter-list bounding behavior
9. (If format_debug guard wanted) `test_no_public_tuple_in_display_output` — confirm `format_debug` never receives a Python tuple from any public API

### Regression tests for pipelines and display

- `map_items |> map(map_item_key)` — existing spec case; must not regress
- `map_items |> map(map_item_value)` — existing spec case; must not regress
- `tee |> zip |> collect` — existing spec case; must not regress
- `zip(f1, f2) |> collect` — existing spec case; must not regress

---

## 9. DOC IMPACT

### `GENIA_STATE.md`

- Add `pairs` to the documented public map/list helper surface (§11 or a dedicated pair-like section) once implemented.
- Add a pair-like contract note: "Public pair-like values use 2-element Genia lists; Python tuples are not a public value type."
- Note `pairs(xs, ys)` maturity as Experimental until audit-confirmed.
- **Do not update `GENIA_STATE.md` until the implementation phase is complete and audit-ready.**

### `GENIA_RULES.md`

- No change required in this phase.
- If a pair-like invariant should be locked in rules (e.g., "public pair-like return values must use 2-element Genia lists"), add it in the docs phase.

### `README.md`

- Add `pairs` to the autoloaded prelude list once it is implemented.
- No pre-flight or spec-phase changes.

### `GENIA_REPL_README.md`

- Likely no change; tee/zip pair shape already documented there.
- If `pairs` is added, add a usage example showing `pairs([1, 2], [3, 4])` → `[[1, 3], [2, 4]]`.

### Cheatsheets or examples if relevant

- `docs/cheatsheet/core.md` — may need a `pairs` example once implemented
- `docs/cheatsheet/quick-reference.md` — add `pairs` to the list helper section once implemented
- No cheatsheet changes until after the implementation and audit phases

---

## 10. CROSS-FILE IMPACT

### Files likely to change in later phases

| File | Why |
|---|---|
| `src/genia/interpreter.py` | New `pairs_fn` host primitive and `_map_items` correctness guard |
| `src/genia/std/prelude/map.genia` | New `pairs` prelude wrapper function |
| `spec/eval/pairs-basic.yaml` | New shared spec case |
| `spec/eval/pairs-shorter-bound.yaml` | New shared spec case (shorter-list bounding) |
| `tests/test_maps.py` | New `pairs` tests and optional tuple-guard test |
| `tests/test_spec_ir_runner_blackbox.py` | Register new spec case names |
| `GENIA_STATE.md` | Add `pairs` to pair-like surface once implemented |
| `README.md` | Add `pairs` to autoloaded helpers once implemented |
| `docs/cheatsheet/core.md` | Add `pairs` example once implemented |
| `docs/cheatsheet/quick-reference.md` | Add `pairs` entry once implemented |

### Risk of drift

- **Low** if scope stays bounded. The `pairs` function is a pure list operation with no Flow, Option, or host-interop complexity.
- **Medium** if the single-arg `pairs(xs)` form is added without clear semantics — it could drift into a type-checking or normalization helper that expands scope.
- **Low** for existing surfaces since `map_items`, `tee`, and `zip` are already clean.
- **Latent** risk: if `format_debug`/`format_display` ever receive a Python tuple (from a future regression), the output would be Python `repr` format `(a, b)` which violates display semantics. A guard in the display path is worth considering but is not in this issue's scope.

---

## 11. PHILOSOPHY CHECK

- **Preserves minimalism?** YES. Adding `pairs` is additive and small. No existing API changes.
- **Avoids hidden behavior?** YES. `pairs` is a plain list operation with explicit semantics. No Option propagation magic.
- **Keeps semantics out of host-specific hacks?** YES. `pairs` can be implemented as a Genia-level function or a thin host primitive; either way the semantics are portable.
- **Aligns with pattern-first design?** YES. The explicit goal is that every element produced by `pairs` is pattern-matchable as `[a, b]` without tuple knowledge.

---

## 12. PROMPT PLAN

### spec

Define the exact observable contract for `pairs`:
- `pairs(xs, ys)` — arity-2, zip two lists into `[[x, y], ...]`, bounded by the shorter list
- Confirm whether `pairs(xs)` single-arg form is in scope or deferred
- Add formal spec YAML cases for basic behavior, shorter-list bounding, and empty inputs
- Lock the spec case names and expected output format before writing tests

### design

Describe the implementation approach:
- New `pairs_fn` host primitive in `interpreter.py` vs pure Genia prelude implementation
- Exact prelude entry in `src/genia/std/prelude/map.genia` or a new `std/prelude/pairs.genia`
- Registration via `env.register_autoload`
- `@doc` annotation and `help("pairs")` behavior

### failing tests

Add failing tests before any implementation:
- New pytest tests in `tests/test_maps.py` or `tests/test_pairs.py`
- New shared spec YAML files
- Register new spec names in `tests/test_spec_ir_runner_blackbox.py`
- All tests must fail (red) at commit time

### implementation

Implement only what the failing tests require:
- Add `pairs_fn` and register it
- Write the Genia prelude wrapper
- Reference the failing-test commit SHA in the implementation commit message

### docs

Update docs in this order:
- `GENIA_STATE.md` first
- `GENIA_RULES.md` if a pair-like invariant is added
- `README.md` — add `pairs` to the autoloaded helper list
- `GENIA_REPL_README.md` if an example is added
- Cheatsheets

### audit

- Run `pytest -q` full suite
- Run shared spec runner
- Confirm `pairs` passes all spec cases
- Confirm no regression in `map_items`, `tee`, `zip` spec cases
- Confirm no Python tuple appears in any public output via display check
- Confirm `GENIA_STATE.md` maturity label matches implementation completeness

---

## 13. FINAL GO / NO-GO

### Ready for spec phase?

**GO.**

- Sources of truth are clear and consistent.
- The main remaining work is defining and adding the `pairs` function.
- No semantic code changes are needed in this phase.
- No blockers.

### Blocking unknowns

1. **`pairs(xs)` single-arg semantics** — unresolved. The spec phase must decide: arity-2 only, or also a single-arg form that validates/normalizes a list of `[a, b]` items. Recommendation: arity-2 only in this phase to stay minimal; defer single-arg if no concrete use case exists.
2. **Where to place `pairs` in prelude** — minor. Logically belongs near `map_items` in `map.genia` or in a new `pairs.genia`. The spec phase may defer this to the design phase.

---

## Recommended next prompt (SPEC phase)

```
You are working in the Genia repo on issue #140:
Normalize Pair-Like Values to Lists (Remove Tuple Leakage from Public API)

Pre-flight is complete. Branch: issue-140-pair-lists-preflight.
Pre-flight doc: docs/architecture/issue-140-pair-lists-preflight.md

The main remaining deliverable is defining and adding the `pairs` function:
  pairs(xs, ys) -> [[xs_item, ys_item], ...]

Spec phase task:
1. Define the exact observable contract for `pairs(xs, ys)`:
   - arity-2: zip two lists into a list of 2-element Genia lists
   - bounded by the shorter list
   - elements are pattern-matchable as [a, b]
2. Decide: is a single-arg `pairs(xs)` form in scope? (Recommendation: NO — arity-2 only.)
3. Write the spec YAML cases:
   - spec/eval/pairs-basic.yaml
   - spec/eval/pairs-shorter-bound.yaml
   - spec/eval/pairs-empty.yaml
4. Commit with prefix: spec(pairs): define pairs(xs, ys) contract for issue #140

Do NOT implement. Do NOT write failing tests. Do NOT update behavior docs.
Only write spec YAML files and commit the spec.
```
