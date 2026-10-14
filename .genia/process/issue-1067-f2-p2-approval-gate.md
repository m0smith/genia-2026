# F2/P2 contract ratification — approval gate (issue #1067)

Phase: **contract reconciliation and planning only.** No runtime, test, STATE, RULES,
REPL README, README or shared-spec change. `GENIA_STATE.md` remains final authority and
describes single-root behavior. The contract text of §16.1–§16.7 is unchanged; proposed
amendments are in contract §16.8.

## Verified baseline

| Item | Verified |
|---|---|
| #1227 (P2-0 contract) | merged by m0smith 2026-10-14T14:58Z; merge commit `7b02512`; head `801c3ce` |
| #1228 (P2-A characterization) | merged by m0smith 2026-10-14T15:10Z; merge commit `7b3b524`; head `b10eb8c` |
| `origin/main` at start | `d35ef3a` (contains both) |
| Maintainer approval of §16 | **None found.** The newest #1067 comments (6155448975 carry-forward; 6171402648 P2-A hand-off) are not approvals; the PR merges are not approvals; §16 still reads PROPOSED |
| #1220, #1221 | open; #1220 body already carries the reclassified criteria (pending approval) |
| Existing P2 tracking | none; created #1229 (execution) and #1230 (fallback removal) |

Gate: **P2-B and P2-C are not started.** Approval-dependent work stops here.

## Reconciliation of P2-A evidence against §16

No contradiction. Findings:

1. **Premises reproduced.** `map_acc` is not initially bound and not autoload-registered; the
   list-file load installs it into R. An entry `map_acc/3` before the load succeeds, then poisons
   the load with the exact duplicate diagnostic. This confirms the manifest is needed and that a
   plain child E (shadow/hide, characterized) is *not* the P1 behavior.
2. **Reflection.** Module string `doc`/`meta`/`help` capture R even in a real module, so a module's
   own helper is not found (P2R-2 observable change 1 is an improvement); function-valued
   `help(probe)` already works. `map_acc` is directly visible after the load but has empty metadata
   and is absent from the `help()` catalogue, so manifest ownership must **not** be treated as
   catalogue membership (new P2-B assertion).
3. **Fallback.** Module function reads are live; top-level reads are import-time snapshots and make
   the import fail when the name is absent (loading guard clears). Contribution closures keep the
   declaring module as owner. Strict mode must therefore be proven at import time, call time and
   contribution time.
4. **`eval`.** `empty_env()` is a non-rebinding child of R that reads live entry names; writes stay
   local. P2R-4 is an observable change exactly as labeled.
5. **Sinks and entry accessor.** `_emit_error`/`_write_stdout`/`_write_stderr` ignore a sink on an
   inherited scope and fall back to process streams; plain-child `main` is ignored. Both are real
   red targets for P2R-6.
6. **#1220.** Root and runtime accessors coincide, so the accessor spelling cannot be a red test;
   the E-vs-R catalogue misuse and the AST guard are the discriminating tests (P2R-5 confirmed).
7. **Inventory.** 13 program / 3 tooling / 15 direct = 31 independently confirmed; classification in
   contract §16.8 A3.
8. **Stale §2.1.** The prelude local-assignment instances were repaired by #1205/#1206; §2.1 now
   carries a status note.
9. **Limits carried forward.** Manifest counts not re-derived in P2-A (P2-B drift test); MCP pruning
   characterized on a root and a plain child, not a worker E; Node/VS Code, official-SDK job and C++
   were not validated in P2-A; the P2-A full run had 4 disclosed load-sensitive failures that passed
   on serial retry — P2 full-regression evidence must be a clean run or restate its failures.

## Proposed decision table D1–D6 (all PROPOSED; none approved)

| | D1 runtime-owned names / collisions | D2 reflection and help | D3 compatibility fallback | D4 metacircular `eval` | D5 #1220 | D6 registration / testing |
|---|---|---|---|---|---|---|
| Disposition | **Conditional approval** — approve §16.1 plus amendment A1 | **Approve** — §16.2 as written | **Approve §16.3 mechanism; revise deadline** — amendment A2 required | **Approve** — §16.4 as written | **Approve** reclassified criteria §16.5 | **Conditional approval** — §16.6 plus clarification A3 |
| Supporting P2-A evidence | first/map/map_acc before/after load collisions; rows/0 joins host rows/1; assignment replaces `log`; plain child shadows (so child-E is not "unchanged") | module string reflection uses R; module own helper missed; function-valued help works; map_acc undocumented and uncatalogued | module and contribution reads of entry names, no warning today; import-time vs call-time; top-level failure + guard clear | `empty_env` child of R, live entry reads, local writes | root==runtime accessors; pruned root catalogue observable | plain-child main ignored; sinks ignore inherited child; 13+3+15 inventory; real native discovery/serve/REPL/debugger |
| Observable behavior change | None for collisions (preserves single-root outcomes incl. failures); non-runtime-owned entry names stop being visible to prelude | (1) module `doc("own_helper")` resolves; (2) module reflection of E-resident entry name stops resolving; (3) frame-first lookup: a local/param named like the target wins | New host-local warning stream and strict switch; module reads of E-resident entry names remain working (with warning) in P2 | Entry/module `eval(…, empty_env())` can no longer name E-resident entry functions; workaround: `define` explicitly | None (behavior-neutral) | None for programs; host entry points evaluate in E |
| Remaining compatibility risk | Entry declaration of a runtime-owned name stays visible to modules/prelude (hijack of e.g. `map` via `map_acc`) and `internal_values` shadowing — **P3 obligation, gate A1** | Third-party reliance on module reflection of entry names unknown | Third-party module→entry reliance unknown; strict mode does not see reads of entry-declared runtime-owned (R-resident) names | Third-party eval of entry names unknown; repository evidence shows none | Misreading catalogue from lookup scope would silently empty `help()` | Single-root tests pass without proving separation; `internal_values` hardening deferred |
| Required implementation tests | T-D1a–d (see P2-B brief groups 1–3, 7) | T-D2 (group 5; direct, indirect, higher-order, module, transferred, user-rebound) | T-D3 (group 4; eligibility, dedupe, no leak, never for writes/reflection/exports/prelude/eval/runtime-owned, strict mode, event count) | T-D4 (group 6; entry, runtime, module-owned names; `define`) | T-D5 (group 11; AST guard, E/M/R identical `help()`, control `E.autoloads == {}`, pruned) | T-D6a–e (groups 1, 7–10, 12; non-aliased fixture; wrong-accessor variant per boundary) |
| Required documentation updates (at implementation) | STATE net-small, RULES §8.2/§8.3, REPL README, semantic facts | STATE, RULES, book reflection/function chapters, cheatsheets with sidecars, doc/help generated refs | STATE single marker, host-interop, REPL README, CI config; removal in P3 | STATE, eval book chapter, cheatsheet | none unless behavior changes; evidence on #1067 | STATE, REPL README, host-interop, code-documentation for changed bindings |
| Modifies §16? | **Yes** — A1 adds the measurable P2→P3 retirement gate (§16.8, not yet in §16.7 text) | No | **Yes** — A2 changes §16.3.5 and §11.4 closing paragraph | No | No | **Yes (clarifying)** — A3 inventory classification |

MCP language-knowledge impact (for the implementation slices, answered now so it is not skipped):
**probable yes** — the profile advertises scope/`doc` behavior only if a registry fact covers it;
each slice must check `docs/contract/semantic_facts.json` `mcp_language_profile` and either update
it and regenerate `apps/mcp/mcp.genia` or record "no" with a reason. This planning change: none.

## Exact items requiring maintainer approval

1. **D1:** approve §16.1 (runtime-owned set including the static prelude manifest; write-through
   for entry operations on runtime-owned names; no per-arity machinery) **and A1**.
2. **D2:** approve §16.2, including the three labeled observable changes.
3. **D3:** approve §16.3 items 1–4 and 6; **approve A2** (evidence-gated deadline: R29 start is a
   hard gate, 60 days is a review checkpoint). If A2 is rejected, the existing "earlier of 60
   days / R29" wording stands and the maintainer must confirm it as written.
4. **D4:** approve §16.4 including the observable `empty_env()` change.
5. **D5:** approve §16.5 reclassified #1220 criteria.
6. **D6:** approve §16.6 and A3.
7. **Process:** confirm the slice order P2-B → P2-G of #1229 and that #1230 is the removal issue
   (owner @m0smith unless reassigned).

A single comment on #1067 stating "Approved: D1–D6 with A1–A3" (or per-item exceptions) suffices.

## Out of scope here (unchanged)

P3: D2/D2b finality, per-arity shadowing, `NameError` for module reads, fallback and write-through
removal, `internal_values` hardening, export/privacy, C++ module system. R9–R28 behavior untouched.
