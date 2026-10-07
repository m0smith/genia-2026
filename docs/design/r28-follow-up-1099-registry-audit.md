# Audit: governed MCP language-profile registry (#1099, PR A)

Status: **PASS WITH ISSUES (one defect found and fixed during audit), 2026-10-07.**
Scope: phases 1–3 of the #1099 pre-flight (sync architecture), with the owner's
semantic-anchor amendment. STATE distillation (PR B) is not started.

## Findings

- **Defect found and fixed:** the full regression failed
  `test_r28_mcp_architecture.py::test_no_python_module_defines_mcp_application_literals`
  because a docstring in `tools/gen_mcp_language_profile.py` contained the tool-name
  literal. The guard was correct; the docstring was reworded. The guard was not weakened.
- Contract vs implementation: registry shape, anchors, crosswalk, generator, and
  generated block match `r28-follow-up-1099-registry-contract.md`. `within` (anchor
  nesting) was added to the crosswalk during implementation so registry-only validation
  can check evidence containment; the doc test verifies it against real STATE spans.
- Wire: `genia_language_profile` output is byte-identical to the pre-change output
  (golden snapshot captured before any change; plain-file and launcher modes).
- Authority: STATE now states the no-`if`, no-loop-syntax, recursion, and ordered-resolution
  claims in language sections (`state:control-flow`, `state:pattern-matching`); the
  `if_and_loops` evidence no longer depends on the MCP section.
- Scope: no file under `src/`, `hosts/`, or `spec/` changed; no STATE restructuring beyond
  anchor markers, four added statements, and the 9.50 maintenance text.

## Known limits (honest)

- A new MCP-relevant claim that is neither pinned, probed, nor cross-checked is still
  caught only by the template/process rule. The optional parser-derived classification
  test (pre-flight C7) was not built; it needs a feasibility check against the AST
  vocabulary.
- The 12-row table in STATE 9.50 and the A7 summaries in the contract/pre-flight
  documents are still hand-maintained copies; PR B replaces the STATE table with a pointer.
- Section numbers on the wire remain legacy values via the crosswalk; duplicate heading
  numbers (`1`, `4.1`) are untouched and deferred to PR B.
- No new authentic client acceptance run (Node acceptance in `tools/mcp_acceptance/`
  needs an external client); the four-tool surface is covered by the existing Python suites.

## Verification

Full regression, both partitions, on the audited tree (before the docstring fix):
`-m "not loopback"` 6262 passed, 40 skipped, 1 failed (the defect above); `-m loopback`
31 passed. After the fix: the architecture and registry suites pass (39), and
`tools/gen_mcp_language_profile.py --check` and `tools/validate_llm_instructions.py` pass.
The complete suite is re-run once more after the fix (see the branch tip).
