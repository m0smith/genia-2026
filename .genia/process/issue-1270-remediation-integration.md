# #1270 remediation integration — #1300 and #1299

Authorized scope: integrate the independently reviewed #1300 documentation and
the separately reviewed #1299 fixture repair into #1270's dedicated branch;
verify the final candidate. No #1270 merge to main, issue closure or R29 work.

## Preflight and provenance

Latest instructions were checked at main79c073b556ad16343051d545d7928248a6d0f6b0;
AGENTS and applicable process controls match the audited candidate. Main's
pre-Slice-C authority text is not substituted for the candidate's implemented
Slice C truth. STATE remains final authority.

#1300 reviewed sourcea305783f2455589ade2f1a7fa03afc29f91d3e6c was merged only into
the dedicated branch at655c5da6e564c81a72e8230926be5c84bb17077b; resulting tree
b877666725c40aef46d0214e76f8527c92a2bb25 is identical to that reviewed source.
The #1299 development sequence is explicitly backported through its own PR,
not silently inserted. Its preflight, unchanged contract, design, committed RED,
minimal repair, maintainability review and stress evidence accompany the change.

## Portability and truth

- Both Python and selected C++1f338866 are affected by the shared fixture repair.
- Portable authority is existing R25 contract6.1/6.2 plus STATE Process behavior.
- Shared executable representation remains the existing source-based YAML case.
- Existing `process_primitives` and `refs` capability vocabulary is unchanged.
- No host capability declaration, unsupported classification or expected oracle
  changes. Only admission ordering changes; accepted FIFO and terminal failure
  remain asserted. Existing host-specific negative diagnostics remain distinct.
- No Core IR node, protocol, runner, runtime or generated MCP profile change.
- Five authority documents retain their implemented scope; no speculative D/E
  claim is added. STATE candidate word count remains42997/43000.

The gap reason is synchronized from “unresolved fixture” to a historically
reproduced race with an admission-ordered candidate repair. #1299 remains tracked
pending main integration and final acceptance. Historical failures are retained.
Only the reason string changes; classifications and removal conditions do not.

## Verification and review obligations

Use full Python/C++ shared suites, exact selected source, per-case comparison,
native C++ checks, hosted parity/Docker/CI, default documentation tests and strict
MkDocs, generated-reference/profile checks, normal-deadline bounded stress, and
independent final-head semantic/documentation review. Report exact SHA/tree and
distinguish branch evidence from GitHub synthetic merge evidence. The retired
module-fallback strict mode is not an available test configuration.

Initial supplemental stress used30s rather than the runner's normal10s deadline;
that configuration is not accepted as the final stress gate. Preserve it and
rely on explicitly recorded normal-deadline batches. No test retries, sleeps,
skips, failure reclassification or timeout increases are part of the repair.

Final results belong in #1251 and #1270 comments after execution; this preflight
does not assert that pending verification passed. Maintainer controls #1251
acceptance, #53/#54 closure and R29 intake. Slice D/E remains incomplete.
