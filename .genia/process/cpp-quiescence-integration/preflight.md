# Corrected C++ host integration pre-flight

Owner: Codex. Date: 2026-10-20. Tracking: genia-2026 #1261 / PR #1262;
C++ #51 / merged PR #52. Branch: issue-1261-cpp-quiescence-integration.
Base: 21691ff818f914e0f39ce1bb138178d7773ca865, verified against GitHub main.

1. Scope: pin the two existing main-repository C++ checkout workflows to
   44456baea06b4bb7bdf727e39939dd7150261ee6; explain revision provenance in
   host matrix and development-container documentation. No runtime/spec changes,
   capabilities, protocol changes, contract repin, Slice B merge or Slice C.
2. Authority: GENIA_STATE C++ host status and Ref/Cell/Process sections;
   GENIA_RULES section 10; GENIA_REPL_README; README host status;
   R25 stateful-runtime-concurrency contract and concurrency evidence design.
   Both repositories' AGENTS read. No semantic conflict identified.
3. Maturity: N/A infrastructure/docs. Existing bounded host claims remain.
4. Portable contract: staged nested sends commit only after successful work.
   Python remains reference; corrected C++ host uses private causal accounting.
   Actor, unsupported Model B syntax and optional host gaps remain excluded.
5. Validation: actual GitHub host-parity, Docker, CI and docs workflows at exact
   integration head, inspect immutable run/job links and conformance counts.
   Local docs checks supplement those gates. Never substitute ancestor-compatible
   evidence for exact-contract conformance or green optional gaps for syntax parity.
6. Example: both checkout steps use the full corrected SHA. Process-only example;
   no new Genia program or runnable language example.
7. Complexity: reveals existing structure; replace moving main with reviewed SHA.
8. Impact: two workflow YAML files, host matrix, development-container guide,
   process evidence. Low drift risk; no semantic surface or generated docs change.
   STATE/RULES/REPL README/README, book and cheatsheets need no semantic edit:
   this integration selects an implementation of unchanged contract behavior.
   MCP language-knowledge impact: none; no language fact or idiom changes.
9. Philosophy: minimalism YES; avoids hidden behavior YES; semantics outside
   adapters YES; pattern-first YES; approved multi-host reliability infrastructure.
10. Phases: preflight -> pin implementation -> documentation -> verification ->
    independent Claude review. Contract/design/RED language tests N/A: immutable
    dependency selection only, no runtime implementation. Audit remains independent.
11. Hosts: both exercised, C++ source selection changes; portable semantics NO.
    Shared R16 cases and existing gap manifest remain unchanged. Host integration
    must verify before #1262 recheck/maintainer merge. No host-gap exemption added.
12. GO for bounded preparation. NOT YET VERIFIED for integration/review handoff.
    GitHub confirms #52 merged at requested SHA. Independent maintainability,
    truth audit and final documentation spot-check all PASS WITH NON-BLOCKING
    FINDINGS (links below). Runtime credentials/network and required workflow
    execution remain unresolved, not waived.

## Portability analysis

- Authority: STATE and approved R25 contract above.
- Representation: existing ordinary opaque runtime values, existing R16 fixture.
- Observable behavior: unchanged; only corrected implementation selected.
- Shared evidence: existing R16 corpus and unchanged R25 nested-send case.
- Applicability: existing manifest capability gates; no new vocabulary.
- Capability claims: unchanged; retain required-syntax and ancestor limitations.
- Truth synchronization: host matrix/container revision provenance, actual results
  only after execution; no new language/MCP claims.

## Verified upstream review evidence

- https://github.com/m0smith/genia-cpp/pull/52
- https://github.com/m0smith/genia-cpp/pull/52#issuecomment-6297673785
- https://github.com/m0smith/genia-cpp/pull/52#issuecomment-6301362049
- https://github.com/m0smith/genia-cpp/pull/52#issuecomment-6302179224

The first two verdicts cover af023998; final documentation spot-check covers
5c052f77. They are upstream evidence, not an independent integration review.
