# #1261 Slice B: disposition of Codex maintainability FAIL (review at `888f2123`, comment 6277728347)

**No independent re-review is claimed.** The implementer does not certify M1-M6; Codex re-review supersedes the FAIL or reports remaining blockers.

## Commits

| SHA | Phase |
| --- | --- |
| `888f2123` | starting head (reviewed) |
| `baf85a94` | RED: M1/M2 deterministic race regressions (2 failing, 1 guard passing) and observable Cell shared case |
| `809a41c7` | fix: atomic `define_function` and `merge_binding_metadata`; observable Cell host test; entry-only reservation pin |
| `669e44d8` | docs: M3 corrections |
| (this file's commit) | evidence |

RED evidence: `.genia/process/issue-1261-slice-b-review-fixes-red.md`. Original RED (`0469396b`) and GREEN (`5d16b712`) are untouched.

## Verification on `669e44d8`

- `pytest -n auto -m "not loopback"`: **7089 passed, 60 skipped, 0 failed** (617s).
- `pytest -n auto -m loopback`: **31 passed**.
- Shared R16 (`python -m tools.spec_runner`): **901/901** (874 baseline + 27 Slice B).
- Race tests repeated 6 times consecutively: 3/3 each, no flake. ruff, MCP profile `--check`, function-docs `--check`, `mkdocs build --strict`, code-documentation checker (0 errors): pass.
- Not run locally: the Docker/C++ workflow. See "Docker" below.

## Disposition

- **M1 (fixed).** `define_function` now performs the immutability check, group lookup, group creation/mutation and publication inside one `_BINDING_LOCK` section. The new-group path uses the lock-held `_write_binding` instead of the locking `set`, so there is no recursive acquisition. The docstring lists `ImmutableBindingError`. Test: `test_m1_function_writer_cannot_extend_group_after_name_becomes_immutable` failed at RED (both writers succeeded) and passes: exactly one serialization wins and the shared group gets no unauthorized clause.
- **M2 (fixed).** `merge_binding_metadata` now does owner lookup, declaration-ticket authority check and publication in one `_BINDING_LOCK` section, the same domain as `commit_immutable_declaration`. Annotation expression evaluation stays outside it. Authorized attachment (`declaration=ticket`) and non-transactional failure timing are unchanged (`test_m2_declaration_owned_metadata_still_attaches_after_commit`, evaluator annotation tests). Test: `test_m2_metadata_writer_cannot_land_in_the_partial_publication_window` failed at RED and passes.
- **M3 (fixed).** RULES, REPL README, README and the core cheatsheet now say the runtime-owned-name rejection applies **at entry scope only**. STATE section 3, `semantic_facts.json` and the generated MCP profile were checked: STATE already states "at entry scope"; the MCP profile text does not mention reservation. `test_runtime_reservation_applies_to_entry_scope_only` pins the current Python behavior for `print`, `map` and `map_acc`: entry rejects, nested scope returns 7. No semantic broadening.
- **M4 (open, owned).** The process-wide lock stays; no redesign, since equivalence of a narrower domain is unproven. Measured cost vs `cf384030` (recursion benchmark `fib(20)`, 3 alternating pairs of median-of-9): base 0.706/0.722/0.699s vs head 0.712/0.782/0.741s, roughly +1% to +8% (about +5% on average), noisy and uncontended; **contended multi-thread cost was not measured**. Remaining tradeoff: unrelated execution trees serialize on binding writes, and a cold reserved-manifest inspection can run under the lock. A smaller domain (execution tree or binding owner) must cover routing, nearest-owner resolution and revalidation, all writers and lock ordering, with race evidence, since a naive per-Env lock is unsafe (child `assign` can update an ancestor). Owner: #1261 design follow-up (Claude/m0smith).
- **M5 (fixed).** `spec/eval/model-b-b-cell-mutation-observable.yaml` (requires `immutable_bindings`, `cell_primitives`; fixture `r25_concurrency`) expects `2`; added to the C++ gap's affected tests. The old either-value smoke test is replaced by an exact-value host test that also checks rebinding is rejected.
- **M6 (deferred, owned).** `tools/code_documentation.py` still lacks explicit characterization of immutable/closed declaration ownership/documentation; only the static Env prelude inventory is complete. No shipped prelude uses these forms. Carry N5 until those consumers are characterized and before first shipped adoption. Owner: next prelude/documentation-consumer implementer, m0smith integration, #1261/#1250.

## Writer-coverage analysis (every table write in `src/genia/environment.py`)

| Write | Location | Synchronization |
| --- | --- | --- |
| immutable publication | `commit_immutable_declaration` | `_BINDING_LOCK`; revalidates |
| generic binding write | `_write_binding` (via `set`) | caller holds lock; checks `_immutable` |
| assignment target write | `assign` | `_BINDING_LOCK`; `find_assign_target` rejects immutable |
| function group create/mutate | `define_function` | `_BINDING_LOCK` (M1) |
| metadata merge | `merge_binding_metadata` | `_BINDING_LOCK` (M2) |

Outside `environment.py`, the only direct table mutation is `hosts/python/mcp_worker_profile.py` pruning (`del runtime.values[...]`), a trusted bootstrap step that runs before user code. The pre-RHS and pre-load checks (`check_assign_target`, `check_rebind_target`) remain advisory by design; the locked writers are authoritative.

## Docker / C++ `r25-cell-nested-send-transaction`

Not a Slice B regression per the review: a pre-existing C++ fixture quiescence race, tracked as m0smith/genia-cpp#51. This change touches no C++ code and does not rerun that workflow; it is **not** waived here. The required workflow must be green at a corrected reviewed head before merge. Nothing here weakens or reclassifies the case.

## Not done

Independent re-review, behavioral/docs truth audit, post-audit distillation, final-head CI, and the C++ fix (#51) remain. #1261/#1250 stay open; no Slice C.
