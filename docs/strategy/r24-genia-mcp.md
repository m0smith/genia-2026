# R24 — Genia MCP Server

Status: **Planned, not active.** This document is planning guidance only and does
not define implemented Genia behavior. `GENIA_STATE.md` remains the final
authority for implemented language/runtime behavior.

Release epic: **#700**
Contract gate: **#701 — E24-0 Genia MCP contract and threat model**

## Theme

> Publish Genia as a governed MCP execution and inspection surface.

R24 exposes existing Genia capabilities to MCP-capable hosts through a narrow
adapter boundary. MCP does not become a second Genia semantics path, an agent
runtime, or a general workspace/server framework.

The proving product story is:

```text
agent intent
  -> MCP tool call
  -> Genia parse / governed execution boundary
  -> structured result + diagnostics
```

## Initial public MCP surface

The first release is deliberately small:

- `genia_capabilities` — report adapter/server identity, supported operations,
  protocol/version information, Python-reference-host limitations, and policy
  constraints without duplicating language truth
- `genia_parse` — accept explicit Genia source text and return normalized
  parse/inspection output plus structured diagnostics without execution
- `genia_run` — execute explicit Genia source through approved existing
  Python-host execution path(s) and return normalized value/output/diagnostic
  results under the R24 policy

Resources may expose versioned capability/release information where useful. MCP
prompts are not required for R24 unless a concrete consumer need is demonstrated.

## Architectural rules

- MCP adapts existing Genia behavior; it does not define new syntax, Core IR, or
  evaluation semantics.
- Direct Python-host execution and MCP execution must remain observably aligned
  for representative programs within the approved capability set.
- Python SDK/runtime details remain host-local implementation details; the
  MCP-facing contract must be portable enough for a future C++ host to implement
  without copying Python internals.
- Source text is explicit tool input, never an instruction to browse the host
  workspace or discover ambient files.
- Protocol, parse, policy, execution, timeout/cancellation, and transport failures
  remain distinguishable in structured results.
- Protected configuration/secret behavior from R10/R13 remains authoritative;
  MCP results and diagnostics must not provide a new declassification path.

## Execution and safety boundary

E24-0 must explicitly contract the following before runtime implementation:

- accepted source/execution-mode inputs
- stdout/stderr-like emitted output versus returned values
- timeout and cancellation semantics
- maximum input/result/diagnostic sizes
- filesystem policy
- process environment and configuration policy
- secret/protected-value redaction rules
- network-capable Genia primitive policy
- remote HTTP exposure policy
- version/capability negotiation and compatibility expectations

At minimum, R24 must defend against hostile source text, prompt-injected requests
for host data, environment/secret disclosure, unbounded execution, oversized
results, diagnostic leakage, and accidental capability widening.

## Transport posture

Local **stdio** is the required proving transport.

Streamable HTTP may ship only if E24-0 explicitly approves it without implying a
production multi-tenant sandbox or weakening configuration/secret boundaries.
Remote transport is therefore optional scope, not a release prerequisite.

## Proving application

A mainstream MCP client should be able to:

1. discover the Genia MCP server and its capabilities
2. submit a small Genia validated-data-pipeline program for inspection
3. receive deterministic parse/diagnostic output
4. execute that program through the governed Python-host boundary
5. receive a stable structured value/output/diagnostic response
6. observe behavior consistent with direct Python-host execution

The example should exercise Outcome-aware validation so the MCP demo reinforces
Genia's product north star rather than becoming a protocol-only hello world.

## Approved issue path

1. **#701 — E24-0:** MCP contract and threat model
2. **#702 — E24-1:** Python-host MCP adapter skeleton and capabilities
3. **#703 — E24-2:** MCP parse and inspection tool
4. **#704 — E24-3:** governed MCP execution tool
5. **#705 — E24-4:** stdio transport; Streamable HTTP only if contract-safe
6. **#706 — E24-5:** MCP conformance and direct-host parity test matrix
7. **#707 — E24-6:** runnable demo, publishing docs, and release truth audit

Dependency order:

```text
#701 -> #702 -> #703 -> #704 -> #705 -> #706 -> #707
```

No implementation ticket is authorized to invent unresolved behavior that
belongs to #701.

## Critical acceptance criterion

An ordinary MCP client can discover the server, parse and run a small
Outcome-aware Genia validated-data-pipeline program, and receive deterministic
structured results/diagnostics equivalent to the approved direct Python-host
behavior, while prohibited host access and protected-value disclosure remain
blocked.

## Explicit non-goals

- making Genia itself an MCP client
- agent orchestration or autonomous tool-selection framework
- arbitrary filesystem/workspace browsing
- shell/command execution
- Git integration
- implicit environment or secret exposure
- a remote multi-tenant execution sandbox
- exposing every CLI option as an MCP tool
- new language syntax or Core IR solely for MCP
- claiming portable multi-host MCP behavior before another host implements and
  passes the approved contract

## Roadmap placement

R24 follows the already-planned R23 slot to avoid renumbering existing releases.
That placement is scheduling order, not a claim that all R14–R23 work is a strict
technical prerequisite. R24 primarily depends on existing Python-host parse and
execution surfaces, R10/R13 protected-value boundaries, and the repository truth
hierarchy. Future multi-host implementations may additionally consume the R16+
portability infrastructure.

R24 remains **planned, not active** until its normal release activation and
E24-0 approval gates are satisfied.
