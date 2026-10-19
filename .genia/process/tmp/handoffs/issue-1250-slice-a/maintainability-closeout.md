# Slice A maintainability closeout — PR #1260 / issue #1250

Date: 2026-10-19. Integration owner: m0smith; correction/disposition author:
Codex (the original implementer, not an independent reviewer).

## Independent review source and bounded verdict

Claude's independent review of `d85a56fa66d3369806ab9951b7572c79db98eba3` through
`45a1def273810132d1cb9fd0dea13f9c9de002d1` is recorded at
https://github.com/m0smith/genia-2026/pull/1260#issuecomment-6269611436 .
Recorded verdict: **PASS WITH NON-BLOCKING FINDINGS**, conditional on explicit
tracking/ownership. Claude independently reported R16 860/860, focused 166 pass,
and all workflows successful at the old head. This is maintainability evidence,
not a behavioral/documentation truth audit.

Codex inspected the actual patch plus parser, IR validation/walker, optimizer,
server-discovery consumers, prelude name discovery and documentation visitor.
The correction recheck below is an implementer check, not a fresh independent
Claude review. **Closeout verdict: PASS WITH NON-BLOCKING FINDINGS** for
maintainability only, with N4–N9 explicitly owned below. No independent truth
PASS, merge approval, B–E support, or whole-epic completion is asserted.

## Preflight addendum

Reuses the existing `.genia/process/issue-1250-slice-a-preflight.md`, approved
#1255 contract and merged #1259 design. User explicitly authorized corrections,
regression verification, docs sync and preparation of the independent handoff.
No contract expansion or new design decision authorizes B–E execution.

Portability: (1) restore ordinary parser compatibility, reject new Python
host-discovery carriers and preserve collection-recursion results; (2) source /
portable normalized IR is the shared boundary, optimizer selection and direct
server calls are host internals; (3) seven new shared IR/parse cases plus two
shared eval twins, with Python direct-caller/internal tests; (4) retain required
parser/ast_lowering and existing eval applicability; (5) Python changes, C++
selected-case compatibility/gaps recorded without changing claims; (6) all four
root docs, book reference and host matrix checked/synchronized as applicable;
(7) no new optional capabilities, runner, schema, protocol or version labels.
MCP language-knowledge impact: no further profile edit is required. Canonical
ordinary/R20 forms and the already-generated parse/lower-only rejection guidance
stay accurate. N1 restores historical literal binding-name compatibility, not
new named access; N2/N3 guard Python internals. Registry/generator/golden tests
must remain unchanged and pass. No generated function reference or portable IR
field changed, so those artifacts are checked rather than rewritten.

## Finding dispositions

Claude reported N1–N9 as non-blocking findings; the user required N1–N3
corrections before this audit handoff. Locations below refer to `08a92c01`:
N1 `src/genia/parser.py:442,790`; N2 the `discover_entry_file_*` functions in
`src/genia/server_route_binding.py`, `server_config_binding.py`, and
`server_cors_binding.py`; N3 `src/genia/optimizer.py:195` and
`tests/unit/test_model_b_optimizer_regression.py`; N4 `src/genia/ir.py`'s
`assert_portable_core_ir`, `_validate_model_b_pattern` and `iter_ir_nodes`;
N5 `src/genia/environment.py:30` and `tools/code_documentation.py:107`;
N6 `src/genia/parser.py:_try_parse_model_b_function` guard parsing;
N7 `src/genia/parser.py:343` / `parse_parameter_list`;
N8 `src/genia/evaluator.py:1365`; N9 the optional-capability boundary in
`tools/spec_runner/host_parity_gate.py` and `spec/known_host_gaps.json`.

| Finding | Disposition, scope and evidence | Owner / dependency / removal condition |
| --- | --- | --- |
| N1 ordinary dotted `=` regression | Fixed. Four IR characterizations (`a.b = 1`, dotted function `=`, `->`, block) pass with the historical design-base parser, fail before the fix, pass after. `=:` and new pattern/guard dotted targets still reject. These are literal identifier binding names, not property writes. | Codex; #1250 Slice A. Completed by N1 commits below. |
| N2 inconsistent direct server discovery | Fixed. Route/config/CORS pre-scan the full entry-node list for immutable, pattern and closed declarations before any environment lookup, even if unannotated or preceded by an ordinary annotated node. 18 direct-caller tests fail before / pass after. No listener, handler, annotation or child expression is activated. | Codex; #1250 Slice A. Completed by N2 commits below. |
| N3 optimizer recursion coverage | Fixed with tests and explicit eligibility documentation; no further rewrite. Nested list/map calls count, quoted syntax does not. Extra collection-recursive case arms prevent nth optimization. Four tests fail with the pre-Slice-A optimizer; current tests and shared result twins pass. Canonical nth still optimizes. | Codex; #1250 Slice A. Completed by N3 commit below. |
| N4 IR validator/walker architecture | Accepted non-blocking follow-up. `ir.py` still combines centralized node validation with reflective dataclass pattern-child checks; per-node validators / explicit child ownership merit a separate bounded refactor. Preserve malformed-direct-IR rejection, R20 traversal, all current wire snapshots and host-local-node rejection. No speculative refactor in closeout. | Codex as #1250 implementation owner; m0smith integration owner. #1250 existing architecture follow-up; complete after explicit validator/child-visitor design and equivalent shared/direct-IR evidence. |
| N5 prelude AST and documentation consumers | Accepted non-blocking dependency. `environment.py:_declared_prelude_names` does not yet inventory new AST kinds. `tools/code_documentation.py:visit_genia` requires new-kind annotation/closed-group characterization, including ownership propagation. No shipped prelude adopts Model B here. | Codex, #1250 Slice B; documentation gate owner is the implementer changing that consumer. Resolve before first shipped Model B prelude declaration or immutable runtime-owned-name enforcement relies on this inventory. Never add baseline debt or call unrecognized kinds documented. |
| N6 invalid `?` diagnostic | Accepted non-blocking parser follow-up. Pin invalid header-question-mark diagnostics through the existing R16 parse/error vocabulary before improving wording; do not broaden grammar or change valid headers opportunistically. | Codex, #1250 parser follow-up. Remove after focused shared negative cases and diagnostics fix are reviewed. |
| N7 unused parser helpers | Accepted non-blocking, separately scoped cleanup under #1250; `try_parse_function_header` and its obsolete parameter-list path need caller inventory before deletion. No unrelated deletion now. | Codex, #1250 cleanup dependency; remove after source/test/direct-caller search, focused parser regression and review establish safe removal. No additional ticket needed. |
| N8 staged rejection timing | Accepted explicit Slice B design dependency. Slice A rejects when evaluation reaches each unsupported declaration, before its children; earlier ordinary effects persist. It does not promise preflight/rollback of an entire submission. A closeout probe observes the earlier binding remaining after rejection. Direct server discovery separately preflights its input before lookups. | Codex, #1250 Slice B design/implementation. Replace transitional rejection only with approved writer/publication behavior and tests preserving required effect timing. No B execution starts here. |
| N9 required C++ gap policy | Reporting question resolved: optional-only `spec/known_host_gaps.json` cannot represent required syntax gaps. Preserve requirements, record exact selected cases in the existing C++ evidence and durable host matrix under #1250, and disclose that optional parity success does not certify required syntax. No optional-capability masking or parity claim. Implementation remains incomplete. | m0smith integration owner and C++ implementer, tracked in [genia-cpp #50](https://github.com/m0smith/genia-cpp/issues/50) under #1250. Remove only after bounded C++ syntax/lowering implementation and passing affected shared cases at the current contract revision; evidence still limits merge claims. |

## Human maintainability assessment

Readability/cohesion: localized target checks and small explicit preflight loops
follow existing module conventions; no new dispatcher or discovery abstraction.
Complexity/duplication: three short checks deliberately align existing independent
entry-file adapters; no broad refactor. Testability: shared historical fixtures,
direct callers that fail on any lookup, and optimizer identity/result checks
exercise the observed risks. Scope/operational fitness: no new runtime language
surface; no IO or concurrency mechanism changed. Performance/scalability review
beyond conservative optimizer eligibility is not applicable to this closeout.
N4/N5 remain visible architecture debt, not silently certified as resolved.

## Exact correction commits

Starting PR head: `45a1def273810132d1cb9fd0dea13f9c9de002d1`.

- N1 RED: `8382cc517aac390e4e11d093e6520c73f3d550fa`.
- N1 fix/root/book sync: `721a9a7aa926c97f55406c9e11eb2d834ad2928a`.
- N2 RED: `197d170f97e3e85728664edeaf777cbde618ff7d`.
- N2 fix/STATE: `d9a161a53ea51a56a6895dc23daac3d8e9108733`.
- N3 regression/eligibility documentation: `41455262ea9c6b64b3fd27b172e2d93ba7589abe`.
- Host gap policy/test-method contracts: `c02e969c5f9c8cfb6700f2f181fd8dfc14e17a4b`.
- STATE budget condensation: `49f354a507c61349b531049b1b659150df8ac33f`.
- Preserved MCP anchor / root assignment invariants: `08a92c010ccef8b95fd67022622d41356bd1a749`.

`c02e969c` and `08a92c01` have identical production `src` tree
`92f21136cd12d9a45225f7641530c2b773369b7c` and shared `spec` tree
`36addc70b0fef2efa26c90ff55070da0a4eec585`. Later closeout commits change
process evidence only. The authoritative independent-audit target is the branch
head containing this handoff; identify its exact SHA from git/PR, not an
assumption that the original Claude review covers the correction diff.
