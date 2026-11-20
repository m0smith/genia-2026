# #1334 requirement → test traceability (Model B D+E), main `5ed34eff`

Method: contract/design clauses (contract `docs/design/pre-r29-default-open-and-immutable-binding-contract-DRAFT.md`,
Slice E design §§10.1–10.4) were matched to (a) shared `spec/**/model-b-*` cases (314 in total, by family, positive
and negative) and (b) host-local `tests/unit/test_model_b_*` / `tests/spec/test_model_b_*` modules. Per-module pass
counts come from `logs/full-nonloopback.xml` (JUnit, run #2). The case/module mapping is by id family and module
name plus targeted greps, NOT an exhaustive per-assertion audit; the independent reviewer should sample it. "C++" =
genia-cpp `fef41e58` via the shared runner (run #8, all non-pass outcomes are UNSUPPORTED, zero failure classes).

| Requirement | Shared cases (Python 1128+18 unsupported overall) | Host-local modules (all PASS) | C++ (per family) |
|---|---|---|---|
| A. Grammar/parser/Core IR carriers; source ≙ direct IR (contract §§3–4; A) | `model-b-a-*` 43 (ir 27, parse 14, eval 2) | `unit/test_model_b_slice_a` 41, `spec/test_model_b_slice_a` 41, E2-L7 in `slice_e2_4_source` (source vs direct IR, malformed IR, forbidden annotations) | **5 PASS / 38 UNSUPPORTED — genia-cpp#50 unmet** |
| B. Immutable `=:` bindings, shadowing, closures, REPL | `model-b-b-*` 27 (eval 25, cli 2) | `slice_b` 32, `slice_b_races` 3 | 1 PASS / 26 UNSUPPORTED |
| C. Default-open ordinary functions, clause grouping, keys, dispatch, ownership, metadata, main selection, optimizer equivalence (§§2.1–2.3, 5.1–5.2) | `model-b-c-*` 143 (eval 74, error 37, cli 32) incl. negatives (duplicate/ambiguous keys, alias/extend rejection) | `slice_c_*` (blocks 17, capability_evidence 145, consumers 35, identity 25, keys 34, optimizer_equivalence 73, optimizer_ir 115, optimizer_retention 36, ownership 21, records 16, repl_main 11), `optimizer_regression` 5, `spec/test_model_b_slice_c_red` 149 | 20 PASS / 123 UNSUPPORTED |
| D1. Completion snapshots/three metadata channels (§5.1–5.3) | `model-b-d1-*` 4 | `d1_completion` 24, `d1_preparation_failures` 10, `spec/test_model_b_d1_preservation` 4 | 0 PASS / 4 UNSUPPORTED |
| D2a/D2b. Ordinary cross-module linking, authority, atomic coherence, frozen views, Outcome-awareness, import inertness | `model-b-link-*` 33 (eval 15, error 18) | `d2a_link_core` 29, `d2a_link_dispatch` 17, `d2a_link_publish` 12, `d2b_public` 17, `d2b_store_synchronization` 2, `spec/test_model_b_d2b_red` 38 | 0 PASS / 33 UNSUPPORTED (`multi_file_eval` known gap) |
| E1. Closed callable construction/sealing/use guards/transport/capture exclusion (design §10.1, E1-01…E1-14) | (host-local by design) | `slice_e1_construction` 9, `e1_red_a` 1, `e1_red_b` 30, `e1_red_c` 77 | n/a |
| E2.1–E2.3. Descriptor/lineage/barriers, guarded slots, T4–T7 publication, F5/T7 single-fault recovery, L2a allocation faults, L8 fast path | (host-local; §10.3 declares no shared twin) | `e2_1` 18, `e2_1_boundaries` 19, `e2_2` 49, `e2_3_corrections` 17, `e2_3_red_a` 5, `e2_3_red_b` 73 (incl. `test_l2a_*`, `test_l8_*`) | n/a |
| E2.4. T0–T3 + source/direct-IR activation, §10.4 oracle transition, `closed_functions` capability (design §10.2, §10.3 L1/L2/L5/L6/L7/L9–L12) | `model-b-closed-*` 64 (eval 19, cli 29, error 16) + `model-b-c-stage-closed-rejected` | `e2_4_source` 26, `e2_4_host_local` 52 (L1, L2, L5, L10–L12), `spec/test_model_b_closed_red` 66 | **0 PASS / 64 UNSUPPORTED — `closed_functions` KNOWN_GAP (never PASS)** |
| REPL/CLI behaviour (alias/rebind, second group, failed-publication reuse) | cli cases in c (32), closed (29), b (2) | `slice_c_repl_main`, `e2_4_source`, `e2_3_red_a` | UNSUPPORTED except 20+1 passing families above |
| Callable reflection / `doc`/`meta`/`help` (E1-08, failed-introspection, annotation introspection while initializing) | `closed-failed-introspection`, `closed-annotation-introspection-while-initializing`, `link-meta-doc-channels`, `c-meta-*` | `e1_red_b`, `e1_red_c`, `e2_1`, `e2_3_corrections`, `e2_4_*` | `doc_help` unsupported |
| Outcome (`none`/`err`) pipeline behaviour | `closed-failed-call-none/-err`, `closed-failed-pipeline-upstream-none-skips`, `link-outcome-awareness`, `c-opt-*` | `d2b_public`, `d2a_*`, `e2_4_source`, `e1_*` | unsupported (closed/link), see families |
| Flow | `closed-failed-flow-pulled/-not-pulled`, `c-opt-*` | `e1_red_c`, `e2_1`, `closed_red` | `flow_phase_1` supported; closed cases unsupported |
| Protected values | — no Model-B-specific shared case | `e1_red_b`, `e1_red_c` (E1-10: no protected sentinel in any rendering/diagnostic); broader protected suites in full run (≈103 tests / 7 modules by name match, heuristic) | n/a |
| MCP policy/profile | profile fact for closed functions | `tests/unit/test_r28_mcp_language_profile` (asserts `<closed-function f>` and closed-scoped catalogue); `gen_mcp_language_profile.py --check` exit 0; 1356 MCP-named tests passed / 8 skipped by name match | MCP not a C++ surface |
| Docs/semantic sync | — | `tests/doc/*` incl. `test_semantic_doc_sync`, `test_portability_contract_sync`, state-anchor/registry tests (357 pass / 34 skipped by name match) | — |

Observations for the independent reviewer (not defects found by me):
1. Protected-value evidence specific to closed/linked functions is limited to E1 sentinel checks; there is no shared
   case combining protected values with closed publication or linking. That may be intended (R10 boundary suites cover it) but is not traced here.
2. E2-L2a/L8 etc. are named in tests; several design ids (E1-xx, E2-L3/L4) are not cited by literal id (L4's writer matrix is E2.2 evidence per `e2_3_red_b` docstring) — mapping is by content.
3. Seven Node-dependent checks and 18 WIT/wasmtime checks were skipped locally (hosted CI executes the Node ones).
