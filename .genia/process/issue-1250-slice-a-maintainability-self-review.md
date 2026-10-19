# Slice A maintainability self-review

Reviewer: Codex, the implementer; **not independent**. Range b3ffef4..13869b3.
Verdict: **PASS for this disclosed self-review only**. Independent Claude maintainability review and independent truth audit remain required; this is not merge approval.

Inspected the actual parser, IR, lowering, normalization, evaluator, optimizer, route discovery and code-documentation diffs with adjacent call sites, the approved contract/design and direct-IR/source tests.

- Parsing: balanced lookahead preserves bare calls; lambda-pattern parsing reuses R20 grammar; submission-local grouping preserves child annotation ownership and rejects operator mixing. Nested tuple atoms were removed from the erroneous test rather than added to the grammar.
- Schema: distinct carriers prevent legacy consumers dropping binding/dispatch authority. Ordinary normalized IrFuncDef remains unchanged. No dispatcher or version negotiation introduced.
- Validation/traversal: closed children are nonempty same-name declaration records; malformed/nested groups and expression-as-pattern carriers reject. R20 and annotation expression children are traversed. Direct evaluation validates new carriers before transitional rejection and child effects.
- Scope: B–E environment, dispatch, linking and publication remain untouched. Optimizer call counting uses the existing IR walker; it does not optimize closed children into a new execution model.
- Discovery: native tests reject through evaluation; route discovery explicitly rejects new declarations; maintained documentation walks child records and recognizes pattern declarations.
- Documentation: changed bindings have source contracts; the maintained-code checker passes without adding baseline debt. New source spans stay out of normalized IR.
- Portability: C++ remains an exact documented unsupported boundary, not parity. No optional capability or gap registry was changed.

No blocking finding remains in this self-review. Independent inspection should concentrate on parser lookahead/grouping, direct-IR validation depth, the conservative optimizer traversal, pattern context normalization, and the C++ merge boundary. Concurrency/performance guarantees and B–E behavior are outside this slice.

Known validation limit: one full-suite MCP assertion requires Linux /proc and fails on macOS. Two output-limit failures under xdist passed in isolation. Final CI must confirm Linux results; no full-regression PASS is claimed from that run.
