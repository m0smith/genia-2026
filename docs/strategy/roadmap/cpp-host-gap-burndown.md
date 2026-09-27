# C++ Host Gap Burn-Down

Status: Planning guide -- non-authoritative. `GENIA_STATE.md` remains final authority for implemented behavior.

This report groups the current C++ host gaps recorded in
`spec/known_host_gaps.json` into the roadmap releases that should close them.
It does not make any planned behavior implemented, and it does not replace the
host-parity CI gate. A gap is closed only when the C++ host declares the
capability `supported`, the relevant shared evidence passes, and
`tools/spec_runner/host_parity_gate.py` reports the capability as `PARITY_OK`.

The current checked-in gap entries are issue-backed by
`m0smith/genia-2026#1018`, which installed the parity gate and known-gap
discipline. Before implementation, each release slice below should receive its
own pre-flight and focused issue set.

## Summary

| Bucket | Gap count | Intent |
|---|---:|---|
| R26 -- C++ REPL and Data Bridges | 2 | Close REPL and the Bytes/UTF-8 + strict JSON data-bridge gap already named by R26 (`debugger_stdio` deferred; ZIP removed from R26 -- see below). |
| R27 -- C++ Flow, Pipe Mode, and HTTP Serving | 4 | Close the largest runtime/CLI/server parity gaps already named by R27. |
| Later release / separate gate | 14 | Keep provider, host-interop, resource, shell, config, AI, retrieval, external-process, `debugger_stdio`, and ZIP work outside R26/R27 unless a later pre-flight promotes it. |

## R26 -- C++ REPL and Data Bridges

**Scope narrowed by `docs/analysis/r26-release-size-preflight.md` and the R26-0/R26-2 decisions (#1015, #1024): `debugger_stdio` deferred (#1025, closed) and ZIP removed from R26 entirely (tracked in "Later Release / Separate Gate" below, pending its own contract-first placement).** The `bytes_json_zip` capability name itself is not yet split/renamed -- that is an E26-0 contract decision, not done by this planning update.

| Gap | Current tracking | Planned issue | Affected tests / spec area | Removal condition |
|---|---|---|---|---|
| `repl` | `m0smith/genia-2026#1023` | R26-1 REPL contract/evidence issue (contract approved, `docs/design/r26-cpp-repl-contract.md`; capability-gated shared evidence landed against Python; C++ implementation not started) | `spec/cli/repl_persistent_binding_basic.yaml`, `spec/cli/repl_failed_submission_diagnostic.yaml`, `spec/cli/repl_none_result_rendering.yaml` (`requires: [repl]`) | Remove when `genia-cpp` declares `repl` supported and the host parity gate reports `PARITY_OK`. |
| `bytes_json_zip` | `m0smith/genia-2026#1024` | R26-2 Bytes/UTF-8 + strict JSON contract/evidence issue (scope decision recorded: ZIP excluded, capability vocabulary replacement pending E26-0) | bytes/json requires-gated shared specs (to be added in E26-0; ZIP evidence explicitly out of scope here) | Remove or replace once E26-0 decides the capability vocabulary, `genia-cpp` declares the resulting capability/capabilities supported, and the host parity gate reports `PARITY_OK`. |

R26 should not absorb pipe/Flow or HTTP serving. Those remain R27 per
`docs/strategy/roadmap/r25-r29.md`. R26 also does not include `debugger_stdio`
(deferred, #1025) or ZIP (removed, see "Later Release / Separate Gate" below).

## R27 -- C++ Flow, Pipe Mode, and HTTP Serving

| Gap | Current tracking | Planned issue | Affected tests / spec area | Removal condition |
|---|---|---|---|---|
| `flow_phase_1` | `m0smith/genia-2026#1018` | R27 Flow phase 1 contract/evidence issue | `spec/flow/**`; Flow requires-gated shared specs | Remove when `genia-cpp` declares `flow_phase_1` supported and the host parity gate reports `PARITY_OK`. |
| `cli_pipe_mode` | `m0smith/genia-2026#1018` | R27 pipe-mode contract/evidence issue | `spec/cli/**` | Remove when `genia-cpp` declares `cli_pipe_mode` supported and the host parity gate reports `PARITY_OK`. |
| `http_server` | `m0smith/genia-2026#1018` | R27 HTTP serving contract/evidence issue | HTTP server requires-gated shared specs | Remove when `genia-cpp` declares `http_server` supported and the host parity gate reports `PARITY_OK`. |
| `http_outbound_transport` | `m0smith/genia-2026#1018` | R27 outbound HTTP disposition issue | HTTP outbound transport requires-gated shared specs | Remove when `genia-cpp` declares `http_outbound_transport` supported and the host parity gate reports `PARITY_OK`. |

R27 should close only capabilities it can prove with shared evidence. If outbound
HTTP remains outside the approved C++ runtime boundary, the R27 pre-flight
should explicitly keep it as a later gap rather than claiming partial closure.

## Later Release / Separate Gate

| Gap | Current tracking | Candidate bucket | Planned issue | Affected tests / spec area | Removal condition |
|---|---|---|---|---|---|
| ZIP (`zip_entries`/`zip_read`/`zip_write`/`entry_*`, currently bundled in the `bytes_json_zip` capability) | `m0smith/genia-2026#1024` | Removed from R26; later contract-first placement, roadmap home explicitly TBD | ZIP contract issue (not yet created): entry-name/traversal rules, duplicates, directories, compression, timestamps/determinism, resource limits, R35 authority reconciliation, dependency-policy amendment for DEFLATE, and reconciling the eager `zip_entries` vs. Flow-based `zip_read`/`zip_write` split | Remove/replace once ZIP has its own contract-first placement, `genia-cpp` declares the resulting capability supported, and the host parity gate reports `PARITY_OK`. Zero shared evidence exists today. |
| `debugger_stdio` | `m0smith/genia-2026#1018` | Deferred developer-tooling/host-capability work (decided #1025, closed) | Not created -- the R26-1 REPL contract does not require it | debugger stdio requires-gated shared specs | Remove when `genia-cpp` declares `debugger_stdio` supported and the host parity gate reports `PARITY_OK`. |
| `allowlisted_host_interop` | `m0smith/genia-2026#1018` | Later host-interop work | Host interop contract/evidence issue | allowlisted host-interop requires-gated shared specs | Remove when `genia-cpp` declares `allowlisted_host_interop` supported and the host parity gate reports `PARITY_OK`. |
| `shell_stage` | `m0smith/genia-2026#1018` | Later host-interop work | Shell-stage disposition issue | shell-stage requires-gated shared specs | Remove when `genia-cpp` declares `shell_stage` supported and the host parity gate reports `PARITY_OK`. |
| `resource_io` | `m0smith/genia-2026#1018` | R35 or later resource work | Resource I/O contract/evidence issue | resource I/O requires-gated shared specs | Remove when `genia-cpp` declares `resource_io` supported and the host parity gate reports `PARITY_OK`. |
| `configuration_environment_snapshot` | `m0smith/genia-2026#1018` | R40 or separate config host work | Configuration environment snapshot issue | configuration environment snapshot requires-gated shared specs | Remove when `genia-cpp` declares `configuration_environment_snapshot` supported and the host parity gate reports `PARITY_OK`. |
| `configuration_dotenv_snapshot` | `m0smith/genia-2026#1018` | R40 or separate config host work | Configuration dotenv snapshot issue | configuration dotenv snapshot requires-gated shared specs | Remove when `genia-cpp` declares `configuration_dotenv_snapshot` supported and the host parity gate reports `PARITY_OK`. |
| `model_deterministic_fixture` | `m0smith/genia-2026#1018` | Later AI-composition host work | Deterministic model fixture issue | model deterministic fixture requires-gated shared specs | Remove when `genia-cpp` declares `model_deterministic_fixture` supported and the host parity gate reports `PARITY_OK`. |
| `model_gemini_rest` | `m0smith/genia-2026#1018` | Later AI-composition host work | Gemini REST model capability issue | model Gemini REST requires-gated shared specs | Remove when `genia-cpp` declares `model_gemini_rest` supported and the host parity gate reports `PARITY_OK`. |
| `embedding_deterministic_fixture` | `m0smith/genia-2026#1018` | Later retrieval host work | Embedding fixture issue | embedding deterministic fixture requires-gated shared specs | Remove when `genia-cpp` declares `embedding_deterministic_fixture` supported and the host parity gate reports `PARITY_OK`. |
| `indexing_deterministic_fixture` | `m0smith/genia-2026#1018` | Later retrieval host work | Indexing fixture issue | indexing deterministic fixture requires-gated shared specs | Remove when `genia-cpp` declares `indexing_deterministic_fixture` supported and the host parity gate reports `PARITY_OK`. |
| `retrieval_deterministic_fixture` | `m0smith/genia-2026#1018` | Later retrieval host work | Retrieval fixture issue | retrieval deterministic fixture requires-gated shared specs | Remove when `genia-cpp` declares `retrieval_deterministic_fixture` supported and the host parity gate reports `PARITY_OK`. |
| `reranking_deterministic_fixture` | `m0smith/genia-2026#1018` | Later retrieval host work | Reranking fixture issue | reranking deterministic fixture requires-gated shared specs | Remove when `genia-cpp` declares `reranking_deterministic_fixture` supported and the host parity gate reports `PARITY_OK`. |
| `multi_file_eval` | `m0smith/genia-2026#1018` | Later module/open-function host work | Multi-file eval issue | shared specs using `eval.input.modules`; multi-file eval requires-gated shared specs | Remove when `genia-cpp` declares `multi_file_eval` supported and the host parity gate reports `PARITY_OK`. |
| `execution_process` | `m0smith/genia-2026#1018` | Separate host-capability work | External process execution issue | `execution.process` requires-gated shared specs | Remove when `genia-cpp` declares `execution_process` supported and the host parity gate reports `PARITY_OK`. |

## Recommended Creation Order

1. R26 pre-flight for REPL/data bridges (#1015, GO recorded).
2. R26-1 contract/evidence issue for `repl` (#1023 -- contract approved, evidence landed against Python; C++ implementation next).
3. R26-2 contract/evidence issue for Bytes/UTF-8 + strict JSON (#1024 -- scope decision recorded: SPLIT, ZIP removed; E26-0 contract reconciliation next).
4. R26-X disposition issue for `debugger_stdio` (#1025 -- decided: deferred, closed).
5. ZIP contract-first placement issue (not yet created; roadmap home TBD, out of R26).
6. R27 pre-flight for Flow/pipe/HTTP.
7. R27 contract/evidence issue for `flow_phase_1`.
8. R27 contract/evidence issue for `cli_pipe_mode`.
9. R27 contract/evidence issue for `http_server`.
10. R27 disposition issue for `http_outbound_transport`.
11. Later-host-gap review for the remaining entries after R27 scope is settled.

Do not create implementation tickets directly from this report. Use
`docs/process/08-roadmap-ticketing.md` after the relevant pre-flight approves a
release slice.
