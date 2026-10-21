# #1261 Slice B: independent maintainability-review handoff

**Status: awaiting independent review. No review or audit verdict is claimed; the implementer is not the reviewer.** Do not merge; keep #1261/#1250 open; no Slice C.

Branch `claude/charming-gauss-dsstwt`, draft PR #1262. Review the diff `cf384030..HEAD`.

## Commits to review

| SHA | Phase |
| --- | --- |
| `b809a9ce` | pre-flight |
| `0469396b` | RED: 26 shared specs, host tests, manifest capability, C++ gap |
| `5d16b712` | GREEN: Env policy, evaluator wiring, discovery relaxation |
| `b4299e46` | fix: parity-gate tracking issue, harness-lint compliance, code-documentation, race/lock tests |
| `f3ced434` | docs sync (STATE, RULES, REPL README, README, semantic facts, MCP profile + golden, book, cheatsheet, Core IR, host matrix) |
| (this file's commit) | evidence + handoff |

Results: `.genia/process/issue-1261-slice-b-implementation.md` (non-loopback 7082 passed / 1 environment artifact resolved; loopback 31 passed; spec runner 900/900).

## Files to read first

1. `src/genia/environment.py`: `_BINDING_LOCK`, `DeclarationTicket`, `_immutable`, `set`/`_write_binding`, `assign`, `find_assign_target`, `check_assign_target`, `check_rebind_target`, `_check_declaration`, `prepare_/commit_immutable_declaration`, `merge_binding_metadata(declaration=)`, `_declared_prelude_names`.
2. `src/genia/evaluator.py`: `_eval_immutable_bind`, pre-checks in `IrAssign`/`IrImport`/`IrOpenFuncDef`/`IrOpenUse`.
3. `src/genia/server_{route,config,cors}_binding.py`: relaxed rejection.
4. `tests/unit/test_model_b_slice_b.py`, `spec/eval/model-b-b-*.yaml`, `spec/cli/model-b-b-*.yaml`.

## Concurrency and design concerns for the reviewer

1. **One global lock.** Every `Env.set`/`assign` now acquires a process-wide lock (measured cost up to about 8-12% on a call-heavy benchmark). Is a global lock acceptable versus per-Env or "lock only after first immutable declaration"? The latter has a first-declaration race that I rejected for correctness.
2. **Non-reentrancy is a convention.** Nothing under the lock may call another locking method. Check every path (`assign` calls `_write_binding`, not `set`).
3. **Check-then-act outside the lock.** `check_assign_target` and `check_rebind_target` are advisory pre-RHS/pre-load checks; the authoritative check is under the lock at write. A write could become invalid between the two; that yields the same error later, after RHS effects (documented N8 behavior).
4. **Prepare is not a reservation.** Two racing declarations both run their initializers; exactly one commit succeeds. Initializer effects are never rolled back.
5. **Unlocked writers remain.** `define_function` mutates an existing group, and `merge_binding_metadata` writes after an unlocked check. I argued these cannot race with an immutable commit (the name already exists, so commit rejects) but reviewers should challenge it.
6. **Trusted bootstrap writers bypass the policy** (`set_internal`, builtins install, MCP worker pruning).
7. **Reserved-name scope is entry-only**, based on the design's wording; module and nested scopes may shadow runtime names. Confirm against the contract's intent.
8. **Harness-root rule.** In an unregistered single-root harness, collision is checked before reservation, so messages differ from the entry-scope path.
9. **Exception class.** `ImmutableBindingError(RuntimeError)`: check normalized-diagnostic and Outcome interaction beyond the tested paths.
10. **Annotation timing.** Annotations evaluate after commit and are non-transactional.

## Unresolved / not claimed

- No C++ implementation or run; the C++ gap is listed with `genia-2026#1261` as tracker and `genia-cpp#50` as owner.
- No CI result for the final head was available at the time of writing.
- The independent behavioral/documentation truth audit, post-audit distillation and final-head CI remain.
- The Python adapter's `immutable_bindings` auto-claim followed the RED manifest entry, so intermediate commits carried a provisional claim.
