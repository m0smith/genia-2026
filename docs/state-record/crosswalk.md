# Legacy section crosswalk (non-authoritative)

> Maps every numbered section heading of `GENIA_STATE.md` at the distillation baseline (`d401f322c692e8c3620509854065692c2605c61a`) to where its content lives now.
> Section numbers are legacy identifiers; documents outside `GENIA_STATE.md` may still cite retired numbers, and this table resolves them. `GENIA_STATE.md`
> governs; verbatim displaced text is in the named record. Verified by `tests/doc/test_state_distillation_gates.py`.

| Baseline section | Heading | Now | Verbatim record |
|---|---|---|---|
| 0 | 0) Multi-host status | section 0 (retained) | — |
| 0.1 | 0.1) Browser playground status | section 0.1 (retained) | — |
| 1 | 1) Shared Conformance — Semantic Spec System | section 1 (retained; duplicate heading number, disambiguated by anchor) | — |
| 0.2 | 0.2) Repository documentation publishing workflow | section 0.2 (pointer) | [`tooling-and-examples.md`](tooling-and-examples.md) |
| 0.3 | 0.3) `@doc` linter (`tools/lint_doc.py`) | section 0.2 (pointer) | [`tooling-and-examples.md`](tooling-and-examples.md) |
| 0.4 | 0.4) `@doc` style synchronization tests (`tests/test_doc_style_sync.py`) | section 0.2 (pointer) | [`tooling-and-examples.md`](tooling-and-examples.md) |
| 1 | 1) Execution model | section 1 (retained; duplicate heading number, disambiguated by anchor) | — |
| 2 | 2) Implemented runtime value categories | section 2 (retained) | — |
| 3 | 3) Implemented syntax and expression forms | section 3 (retained) | — |
| 4 | 4) Functions and dispatch | section 4 (retained) | — |
| 4.1 | 4.1) Python host interop layer (implemented, allowlisted) | section 4.1 (retained; duplicate heading number, disambiguated by anchor) | — |
| 4.1 | 4.1) Symbols and quote | section 4.1 (retained; duplicate heading number, disambiguated by anchor) | — |
| 4.2 | 4.2) Pairs | section 4.2 (retained) | — |
| 4.3 | 4.3) Promises | section 4.3 (retained) | — |
| 4.4 | 4.4) Streams (stdlib) | section 4.4 (retained) | — |
| 4.5 | 4.5) Programs-as-data helper layer (stdlib) | section 4.5 (retained) | — |
| 4.6 | 4.6) Metacircular evaluator (stdlib) | section 4.6 (retained) | — |
| 4.7 | 4.7) R20 open functions and extensible pattern dispatch (Experimental, R20 complete through E20-8) | section 4.7 (retained) | — |
| 5 | 5) Case expressions and pattern matching | section 5 (retained) | — |
| 6 | 6) Builtins (runtime) | section 6 (retained) | — |
| 7 | 7) Autoloaded stdlib | section 7 (retained) | — |
| 8 | 8) Tail calls and optimization behavior | section 8 (retained) | — |
| 9 | 9) Debug/runtime tooling | section 9 (retained) | — |
| 9.1 | 9.1) Native test kernel core (Python reference host, Experimental) | section 9.1 (retained) | — |
| 9.1.1 | 9.1.1) Native test assertion helpers (Python reference host, Experimental) | section 9.1.1 (retained) | — |
| 9.2 | 9.2) Native test CLI (Python reference host, Experimental) | section 9.2 (retained) | — |
| 9.3 | 9.3) Lifecycle plan data-shape support (Python reference host, Experimental) | section 9.3 (retained) | — |
| 9.4 | 9.4) Lifecycle scope tree data-shape support (Python reference host, Experimental) | section 9.4 (retained) | — |
| 9.5 | 9.5) Lifecycle annotation binding helper (Python reference host, Experimental) | section 9.5 (retained) | — |
| 9.6 | 9.6) Native test lifecycle contract consumer (Python reference host, Experimental) | section 9.6 (retained) | — |
| 9.7 | 9.7) R8 server execution contract | section 9.7 (retained) | — |
| 9.8 | 9.8) R14 E14-1 lifecycle instance and parent/child execution scopes | section 9.8 (retained) | — |
| 9.9 | 9.9) R14 E14-2 peer lifecycle attachment and deterministic unwind | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.10 | 9.10) R14 E14-3 repeated element-scoped lifecycle execution | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.11 | 9.11) R14 E14-4 lifecycle-owned configuration provider binding | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.12 | 9.12) R14 E14-5 common HTTP operation representation | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.13 | 9.13) R14 E14-6 outbound HTTP transport capability | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.14 | 9.14) R14 E14-7 outbound HTTP client lifecycle | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.15 | 9.15) R14 E14-8 protected HTTP credential sinks | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.16 | 9.16) R14 E14-9 declarative outbound HTTP annotations | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.17 | 9.17) R14 E14-10 server/request/outbound-client composition | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.18 | 9.18) R14 E14-11 repeated record lifecycle proving case | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.19 | 9.19) R14 E14-12 YouVersion Bible proxy proving application | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.20 | 9.20) R14 E14-13 cross-mode lifecycle and HTTP hardening | section 9.8 (digest) | [`r14-lifecycle-http-records.md`](r14-lifecycle-http-records.md) |
| 9.21 | 9.21) R21 E21-1 numeric source classification and lexical exactness (issue #853) | section 9.21 (retained) | — |
| 9.22 | 9.22) R21 E21-2 tagged portable numeric IrLiteral payloads (issue #854) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.23 | 9.23) R22 E22-1 exact Decimal runtime materialization (issue #887) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.24 | 9.24) R22 E22-2 Rational runtime value and rational(...) (issue #888) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.25 | 9.25) R22 E22-3 exact-family +, -, *, and unary negation (issue #889) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.26 | 9.26) R22 E22-4 exact division and floor remainder (issue #890) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.27 | 9.27) R22 E22-5 explicit Float64 value and conversions (issue #891) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.28 | 9.28) R22 E22-6 Float64 arithmetic and mixed-domain rejection (issue #892) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.29 | 9.29) R22 E22-7 mathematical comparison, equality, and R18 map-key reconciliation (issue #893) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.30 | 9.30) R22 E22-8 numeric misuse, resource limits, and diagnostic normalization (issue #894) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.31 | 9.31) R22 E22-9 cross-surface conformance and compatibility hardening (issue #895) | section 9.21 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.32 | 9.32) R23 E23-1 canonical numeric rendering (issue #911) | section 9.32 (retained) | — |
| 9.33 | 9.33) R23 E23-2 field-format-spec integration (issue #913) | section 9.32 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.34 | 9.34) R23 E23-3 strict generic JSON boundary for Integer and Decimal (issue #915) | section 9.32 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.35 | 9.35) R23 E23-4 strict generic JSON boundary for Rational and Float64 (issue #921) | section 9.32 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.36 | 9.36) R23 E23-5 compatibility JSON reconciliation (issue #923) | section 9.32 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.37 | 9.37) R23 E23-6 diagnostics normalization sweep + docs/release truth sync (issue #925) | section 9.32 (digest) | [`numeric-r21-r23-records.md`](numeric-r21-r23-records.md) |
| 9.38 | 9.38) Provider Composition P8 — retrieve/4 alternate-provider substitution proof (issue #945) | section 9.38 (retained) | — |
| 9.39 | 9.39) Provider Composition P9 — Genia<->WIT interoperability proof (issues #947, #949, #951) | section 9.38 (digest) | [`provider-proof-records.md`](provider-proof-records.md) |
| 9.40 | 9.40) External direct process execution (`execution.process`) | section 9.40 (retained) | — |
| 9.41 | 9.41) R28 E28-1 native Genia MCP server skeleton (`apps/mcp/mcp.genia`) | section 9.41 (retained) | — |
| 9.42 | 9.42) R28 E28-2 `genia_parse` over the native Genia MCP server | section 9.41 (digest) | [`r28-mcp-records.md`](r28-mcp-records.md) |
| 9.43 | 9.43) R28 E28-3 `genia_run` over the native Genia MCP server | section 9.41 (digest) | [`r28-mcp-records.md`](r28-mcp-records.md) |
| 9.44 | 9.44) R28 E28-4 local stdio client configuration and lifecycle (issue #705) | section 9.41 (digest) | [`r28-mcp-records.md`](r28-mcp-records.md) |
| 10 | 10) Explicitly not implemented (current) | section 10 (retained) | — |
| 11 | 11) Example demos shipped in-repo | section 11 (pointer) | [`tooling-and-examples.md`](tooling-and-examples.md) |
| 9.45 | 9.45) R28 E28-5 MCP conformance and parity matrix (issue #706) | section 9.41 (digest) | [`r28-mcp-records.md`](r28-mcp-records.md) |
| 9.46 | 9.46) R28 E28-6 demo, publishing documentation, and release-candidate audit (issue #707) | section 9.41 (digest) | [`r28-mcp-records.md`](r28-mcp-records.md) |
| 9.47 | 9.47) R28 E28-6 amendment A5: the `2025-11-25` compatibility era (issue #707) | section 9.41 (digest) | [`r28-mcp-records.md`](r28-mcp-records.md) |
| 9.48 | 9.48) R28 E28-6 macOS portability of the governed `genia_run` profile (issue #707, ledger R28-H47) | section 9.48 (retained) | — |
| 9.49 | 9.49) R28 completion: authentic VS Code + GitHub Copilot acceptance (issue #707, epic #700) | section 9.49 (retained) | — |
| 9.50 | 9.50) R28 follow-up amendment A6: `genia_language_profile` (MCP adapter affordance) | section 9.50 (retained) | — |
| 9.51 | 9.51) R28 follow-up: MCP grounded-evidence example (issue #1087) | section 9.51 (retained) | — |
