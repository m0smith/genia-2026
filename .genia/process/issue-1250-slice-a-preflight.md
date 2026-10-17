# #1250 Slice A preflight
Owner: Codex; 2026-10-16. Branch: issue-1250-slice-a. Base: d85a56fa66d3369806ab9951b7572c79db98eba3.
Classification: approved pre-R29 semantic foundation follow-up; partial syntax/IR support.
Includes parser/AST/lowering/portable schema/validation/traversal and explicit transitional rejection. Excludes B–E execution, linking, dispatcher changes and merge.
Authority: STATE §§4,4.7,8; RULES function/binding rules; approved #1255 contract and #1259 design with final reviewer pins superseding §11. Current ordinary execution and R20 remain authoritative.
Existing Python/C++: no Model B syntax/carriers. New execution remains unsupported.
Complexity: explicit carriers prevent legacy evaluators dropping authority; reuse R20 pattern grammar. No competing matcher or dispatcher.
Examples: `x =: 1`, `f([x]) = x` are portable parse/lower examples only; not executable Model B claims.
Tests: shared R16 ir success and parse error cases; Python direct-IR malformed groups, traversal, token tables and transitional diagnostics. Baseline ordinary/R20 snapshots retained. Exact RED/green/regression evidence recorded separately.
Portability analysis:
1. Observable: accepted syntax, atomic closed group, normalized IR, parse errors.
2. Boundary: three explicit portable node families; stable legacy IrFuncDef wire shape.
3. Shared evidence: spec/ir/model-b-a-* and spec/parse/model-b-a-* using existing runner.
4. Applicability: required parser/ast_lowering; no optional execution capability changes.
5. Hosts: both affected; Python implementation first, C++ exact case outcomes required. Unsupported never PASS; mandatory syntax failures cannot be hidden behind optional capabilities.
6. Truth sync: four root docs, book, cheatsheets, IR boundary, node-family inventories after verification. MCP impact is partial syntax knowledge, no executable claims; assess guarded projection after verification.
7. No unresolved portable semantic ambiguity; final review pins define carrier/grammar/error identities.
Host merge: only with passing applicable syntax or exact documented #1250-owned temporary boundary; no self-merge. Existing #1229/#1230 work preserved.
Philosophy: minimalism YES; explicit behavior YES; semantics outside adapters YES; pattern-first YES; approved foundation for pipeline work YES.
Drift risk: HIGH. Maintained source documentation required; no generated/prelude function changes expected.
Phases: existing contract/design approved; explicit user authorization permits RED commit → implementation commit → verification → docs → open PR and independent review gate. Independent audit/maintainability PASS not claimed.
GO for bounded RED and implementation; no permission to begin B–E.
