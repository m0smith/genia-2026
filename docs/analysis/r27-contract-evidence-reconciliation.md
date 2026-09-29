# R27 Contract and Evidence Reconciliation

Status: **Planning/architecture record. Non-authoritative.** This document
changes no Genia language or runtime behavior and implements nothing.
`GENIA_STATE.md` remains final authority for implemented behavior. Roadmap and
analysis documents remain planning guidance only.

Tracking issue: [#1033](https://github.com/m0smith/genia-2026/issues/1033)

## 1) Purpose

R27 is currently titled **C++ Flow, Pipe Mode, and HTTP Serving**. The release
size preflight in `docs/analysis/r27-release-size-preflight.md` found that this
title describes a theme, not one safe implementation slice.

This reconciliation records the contract/evidence lanes that should govern R27
before implementation begins. It does not add shared specs, edit
`spec/known_host_gaps.json`, update a host capability declaration, or start any
C++ implementation.

SICP and learning-content work remain out of scope for R27. They should wait
until the language is more mature and should not influence the C++ host
portability plan.

## 2) Current Truth Inventory

| Area | Current authoritative truth | Shared evidence today | C++ status today | R27 disposition |
|---|---|---|---|---|
| Flow phase 1 | `GENIA_STATE.md` documents lazy, pull-based, single-use Flow behavior with partial shared coverage; `docs/host-interop/HOST_INTEROP.md` preserves the host/runtime versus prelude split. | `spec/flow/*.yaml` category cases. | `flow_phase_1` is an optional capability and a known C++ gap. | Ready for the first R27 implementation lane, after a narrow C++ target set is chosen. |
| CLI pipe mode | `GENIA_REPL_README.md`, `README.md`, `spec/README.md`, and `docs/host-interop/HOST_INTEROP.md` document `genia -p`, automatic `stdin |> lines`, final Flow consumption, `stdin`/`run` rejection, and no `main` dispatch. | `spec/cli/*pipe*.yaml` plus related cross-mode pipe cases. | `cli_pipe_mode` is an optional capability and a known C++ gap. | Ready after the required Flow subset is implemented. |
| HTTP server | `docs/host-interop/capabilities.md` classifies the current HTTP server as Python-host-only synchronous blocking behavior with no shared web spec category. | Focused Python tests and Genia-native wrapper tests; no shared HTTP server spec corpus. | `http_server` is an optional capability and a known C++ gap. | Defer from the first R27 delivery lane; needs a separate portable-contract decision before implementation. |
| HTTP outbound transport | `docs/host-interop/capabilities.md` classifies the transport as a private Python-host capability consumed by `web.http_send`/`web.send_annotated`; it has no Genia surface of its own. | Focused Python tests with fake transport/local loopback fixtures; no shared outbound HTTP spec corpus. | `http_outbound_transport` is an optional capability and a known C++ gap. | Defer from the first R27 delivery lane; needs a separate authority/protected-sink contract decision before implementation. |

## 3) Flow Evidence Lane

The first C++ Flow lane should target the current shared Flow category, but it
should start with the smallest slice that proves the runtime kernel before
absorbing higher-level compositions.

Relevant current sources:

- `GENIA_STATE.md`: Flow is implemented in Python and shared Flow coverage is
  active but partial.
- `docs/host-interop/HOST_INTEROP.md`: hosts should preserve the split between
  the Flow runtime kernel and prelude/user-facing helpers.
- `spec/manifest.json`: `flow_phase_1` is an optional capability.
- `spec/known_host_gaps.json`: `flow_phase_1` is a known C++ gap with the
  removal condition tied to a supported declaration plus a host-parity
  `PARITY_OK` result.

Recommended first C++ Flow target:

| Capability slice | Representative shared cases |
|---|---|
| `stdin |> lines` source and `collect` materialization | `spec/flow/stdin-lines-collect-basic.yaml` |
| bounded pull over stdin | `spec/flow/stdin-lines-take-early-stop.yaml` |
| `evolve` plus `take` | `spec/flow/evolve-init-f-integer-progression.yaml`, `spec/flow/evolve-init-f-doubles-from-seed.yaml` |
| `map` and `filter` over Flow | `spec/flow/flow-map-basic.yaml`, `spec/flow/flow-filter-basic.yaml`, `spec/flow/flow-map-filter-chain.yaml` |
| single-use enforcement | `spec/flow/flow-single-use-error.yaml` |
| Seq-compatible terminals | `spec/flow/issue-306-seq-boundary-flow-collect.yaml`, `spec/flow/issue-306-seq-boundary-flow-each.yaml`, `spec/flow/issue-306-seq-boundary-flow-run.yaml` |
| bounded `drop`/`take` finalization | `spec/flow/issue-306-seq-boundary-flow-drop.yaml`, `spec/flow/seq-finalization-drop-take.yaml` |
| `scan`/`reduce` over bounded Flow | `spec/flow/seq-compatible-flow-scan-basic.yaml`, `spec/flow/seq-compatible-flow-scan-bounded-evolve.yaml`, `spec/flow/reduce-flow-bounded-evolve.yaml`, `spec/flow/reduce-flow-range-basic.yaml` |

Cases that compose Flow with other optional or Python-host-heavy surfaces should
not define the first C++ runtime slice. Examples include model, retrieval,
configuration-provider, Template, JSON compatibility, and other cross-release
proving cases. They remain useful evidence after the base Flow kernel is
working, but they should not be allowed to expand E27-1.

## 4) Pipe-Mode Evidence Lane

Pipe mode should follow Flow because pipe mode's observable contract is
Flow-backed. The pipe-mode contract already has shared CLI evidence.

Relevant current sources:

- `GENIA_REPL_README.md`: pipe mode runs a stage expression over
  `stdin |> lines`, consumes the final Flow automatically, bypasses `main`, and
  rejects explicit unbound `stdin` and `run`.
- `spec/README.md`: CLI specs select pipe mode with `input.command` plus
  non-empty `input.stdin`; shared coverage includes basic pipe execution,
  explicit `stdin`/`run` rejection, guidance for bare item stages, bare
  reducers, and non-Flow final values.
- `docs/contract/semantic_facts.json`: protects the documented fact that pipe
  mode bypasses `main`.
- `spec/manifest.json`: `cli_pipe_mode` is an optional capability.
- `spec/known_host_gaps.json`: `cli_pipe_mode` is a known C++ gap with the
  removal condition tied to a supported declaration plus a host-parity
  `PARITY_OK` result.

Recommended first C++ pipe-mode target:

| Contract slice | Shared cases |
|---|---|
| basic Flow-stage execution | `spec/cli/pipe_mode_basic.yaml` |
| per-item parsing through Flow helpers | `spec/cli/pipe_mode_map_parse_int.yaml` |
| explicit `run` rejection | `spec/cli/pipe_mode_explicit_run_error.yaml` |
| explicit `stdin` rejection | `spec/cli/error_pipe_mode_explicit_run.yaml` |
| non-Flow final result rejection | `spec/cli/pipe_mode_collect_error.yaml` |
| bare item-stage guidance | `spec/cli/pipe_mode_bare_parse_int_error.yaml` |
| bare reducer guidance | `spec/cli/pipe_mode_sum_error.yaml` |
| aggregate record-pipeline boundary | `spec/cli/pipe_mode_record_pipeline_collect_validated_boundary_error.yaml` |
| `argv()` shape in pipe mode | `spec/cli/pipe_mode_argv_empty.yaml` |
| `main` bypass | `spec/cli/pipe_mode_bypass_main.yaml` |

Cross-release pipe cases such as `r10-cross-mode-pipe`,
`r13-cross-mode-pipe`, `r15-cross-mode-pipe`,
`validated_record_pipeline_killer_workflow`, and `r11-model-fixture-pipe`
should be treated as later hardening evidence after the base pipe-mode
contract passes.

## 5) HTTP Server Decision

HTTP serving should not be part of the first R27 implementation lane.

Current evidence says:

- `docs/host-interop/capabilities.md` labels the current HTTP server boundary
  as **Python-host-only** and states that there is no shared web spec category
  in this phase.
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md` records HTTP serving as
  Python-host-only for Python and not implemented for C++.
- `spec/manifest.json` includes `http_server` as an optional capability, and
  `spec/known_host_gaps.json` records it as a known C++ gap.

R27 should create a separate HTTP server contract decision only if the project
wants to promote a small deterministic portable subset. That future issue would
need to decide the shared spec route, request/response shape, socket authority,
serve-mode lifecycle interaction, and test strategy before any C++ work starts.

Recommended disposition: **defer from the Flow/pipe delivery lane.**

## 6) HTTP Outbound Transport Decision

Outbound HTTP should not be part of the first R27 implementation lane.

Current evidence says:

- `docs/host-interop/capabilities.md` labels the current transport as a private
  Python-host capability with no Genia surface of its own.
- The public Genia-visible operation is `web.http_send`, which performs
  `HttpOperation` validation, R10 protected-value declassification, and
  normalized transport handling before calling the private transport.
- `docs/host-interop/HOST_CAPABILITY_MATRIX.md` records outbound HTTP transport
  as Python-host-only for Python and not implemented for C++.
- `spec/manifest.json` includes `http_outbound_transport` as an optional
  capability, and `spec/known_host_gaps.json` records it as a known C++ gap.

R27 should create a separate outbound HTTP contract decision only if the project
wants to promote a fixture-backed portable subset. That future issue would need
to define authority creation, protected-header rejection/declassification,
failure taxonomy, fixture behavior, and lifecycle/configuration interaction
before any C++ work starts.

Recommended disposition: **defer from the Flow/pipe delivery lane.**

## 7) Known-Host-Gap Disposition

The existing R27-related known gaps remain valid as planning markers, but their
tracking should move from the broad preflight issue to lane-specific issues as
soon as those issues exist.

| Capability | Current gap entry | Reconciliation result |
|---|---|---|
| `flow_phase_1` | Present in `spec/known_host_gaps.json` | Keep until the C++ Flow implementation issue declares support and host parity reports `PARITY_OK`. |
| `cli_pipe_mode` | Present in `spec/known_host_gaps.json` | Keep until the C++ pipe-mode implementation issue declares support and host parity reports `PARITY_OK`. |
| `http_server` | Present in `spec/known_host_gaps.json` | Keep as deferred unless a future HTTP server contract issue promotes a portable subset. |
| `http_outbound_transport` | Present in `spec/known_host_gaps.json` | Keep as deferred unless a future outbound HTTP contract issue promotes a portable subset. |

No host-gap edit is required by this reconciliation PR.

## 8) Recommended R27 Issue Split

Recommended immediate sequence:

1. **E27-1: C++ Flow phase 1.** Implement the narrow runtime-kernel slice
   listed in section 3, declare `flow_phase_1` only when the chosen shared
   cases pass, and remove the stale known-gap entry only when the host parity
   gate reports `PARITY_OK`.
2. **E27-2: C++ CLI pipe mode.** Implement `genia -p` after E27-1 or after a
   deliberately smaller Flow subset that satisfies the section 4 cases.
3. **E27-5: Flow/pipe hardening.** Add the cross-release Flow and pipe cases
   that are still in scope for the bounded C++ host, plus host-gap freshness.
4. **E27-6: release truth sync/audit.** Close R27 honestly if HTTP remains
   deferred.

Recommended separate decision issues:

- **E27-3: HTTP server contract decision.** Decide whether HTTP serving gets a
  portable, deterministic, capability-gated contract now or is moved out of
  R27.
- **E27-4: HTTP outbound transport contract decision.** Decide whether
  outbound HTTP gets a fixture-backed portable contract now or is moved out of
  R27.

## 9) Final Recommendation

R27 should proceed with **Flow phase 1 followed by CLI pipe mode** as the
implementation lane. HTTP server and outbound HTTP should remain
contract-decision lanes and should not block the Flow/pipe delivery path.

The next implementation issue to create is:

```text
E27-1: implement C++ Flow phase 1 runtime kernel
```

That issue should name its initial shared case set before implementation and
must not claim `flow_phase_1` support until the evidence and host parity gate
support that claim.
