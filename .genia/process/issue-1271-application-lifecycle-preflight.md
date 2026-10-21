# #1271 Application Lifecycle — contract/design pre-flight

Status: **PROPOSED — NOT APPROVED — NOT IMPLEMENTED**. Contract/design publication only.

## Change identity and authorization

- Change: host-selected Application Lifecycle, default ordinary main entry.
- Issue: #1271; implementation release TBD, unnumbered infrastructure follow-up.
- Branch: `issue-1271-application-lifecycle-contract`; author: Codex.
- Source baseline: `6d50a36d23cc4b894f0456ee502deb5d7796e99b`.
- Latest AGENTS blob: `b072beb55d22d5856d3d356d73c60704e04d197f`.
- Prior investigation: #1271 comment 6326759433; integration-owner direction:
  comment 6326938758. The user expressly requests contract plus companion design,
  a dedicated branch, draft PR and issue handoff. This authorizes both documents,
  not the later TEST or implementation phases.
- Slice C: #1269 / PR #1270 at read-only head
  `585f6aa229a55bbd3e3110c975dcaaa94a61e93e`; U2 and RED NO-GO remain separate.

## 1. Scope lock

Includes: proposed default-main contract, mode matrix, R14 ownership/failure
requirements, decision register, companion implementation mapping and future
validation plan. Excludes: runtime/parser/IR/public API changes, RED/spec cases,
Slice C changes, implemented-truth/profile/capability edits, release assignment,
merge, independent self-approval and child-ticket stacks.

## 2. Authority and ambiguities

STATE §§1, 3, Program entrypoint convention, 9.7, 9.8, 9.41; RULES §18;
REPL README Program entrypoint behavior; README execution modes. R14 contract,
R8 STATE contract/coordinator, approved Model B #1255/#1259 and #1269 decisions;
MCP execution contract; roadmap, killer-workflow, LLM contract and run-change
procedure were consulted. STATE is implemented authority. Prior investigation
is evidence, not new semantics. New documents explicitly remain proposals.

Open compatibility choices: ordinary group invocation vs representative record,
legacy rest keys, argv rebinding/absence propagation, interruption/misuse
normalization, failure/exit projection and host gaps. Contract decision register
D1–D8 names the proposed choices and approval boundaries.

## 3. Maturity and portable boundary

This change is N/A for runtime maturity (documentation only); proposed application
execution is not implemented on Python or C++. Existing R14 remains Experimental
Python reference-host behavior; existing Model B execution is partial. No claim
or capability advertisement changes.

### 3a. PORTABILITY ANALYSIS — seven fields

1. Authority/observable boundary: future shared contract for file/command entry,
   argument recipe, ordinary dispatch, owned unwind, diagnostics and status.
   Implemented behavior remains STATE; approval of the new contract is pending.
2. Representation: existing declarations/calls and LifecycleResult. Internal
   entry plans and host-control bookkeeping add no Core IR node or public value.
3. Executable evidence plan: existing R16 CLI/eval/error categories for portable
   observables, source/direct-IR twins where feasible as host-local tests, OS
   interruption/invoker tests on Python. Detailed future cases belong to companion
   design, not the semantic contract. No new executable cases in this phase.
4. Applicability: reuse cli_file_mode/cli_command_mode/repl/cli_pipe_mode,
   relevant open_functions/multi_file_eval/resource_io/config capabilities.
   default_open_functions is planned by #1269, absent at this baseline. No
   standalone lifecycle tag exists. D8 requires a case-level applicability and
   gap decision using existing R16, without hiding mandatory CLI regressions.
5. Host evidence: Python has R14 but not proposed application execution; C++
   lacks R14 and evidenced main/argv parity, config/protected resources, MCP and
   Model B local ordinary-pattern execution. No inherited parity/TCO claim.
6. Gaps/merge conditions: issue-backed affected host/cases/area, owner, reason,
   removal condition before any later implementation merge. Required capability
   gaps are not optional downgrades. #1271 tracks unresolved planning; no new gap
   record or ticket stack is created. Python-first requires an explicit temporary
   gap decision. Unsupported never counts as PASS.
7. Synchronization: after verified implementation update STATE, RULES, REPL
   README, README, relevant book/examples, semantic facts/MCP registry/generated
   profile, host docs/gaps/evidence and roadmap/release material. This draft
   changes none of those implemented claims.

## 4. Contract versus implementation

Portable candidate: linked contract. Python today: direct required-arity record
selection, no application scope; existing R14 callback error paths have measured
cleanup/expiry/text gaps. C++: bounded CLI floor, no demonstrated application
lifecycle. Not implemented: candidate scope, ordinary pattern-main launching,
proposed robust interruption/misuse handling. No production source is changed.

## 5. Validation strategy

Documentation validation only: focused existing truth/lifecycle/semantic sync
tests, generated MCP-profile check, staged strict MkDocs build, local link/scope
inspection and git diff whitespace check. Future behavior and security evidence
is planned in the design; no RED or runtime regression claim follows from doc
checks. Record exact results in the issue/PR handoff after execution.

## 6. Examples and product value

Design classifies existing main(args) as implemented Python behavior and future
pattern-main as proposed/unimplemented. Killer workflow: explicit validated
record pipeline with report plus diagnostics and bounded resource lifetime.
No executable proposal goes into a cheatsheet, release page or language profile.

## 7. Complexity

Reveals existing host entry policy; reuses one R14 engine. No new user surface,
ambient scope, DI, registry or scheduler. Shared-engine hardening is a necessary
candidate dependency, not silently authorized by a thin-adapter label.

## 8. Cross-file impact and MCP knowledge

Only this process record and two new docs/design proposal files. Current drift
risk: limited by status labels and unchanged authorities; eventual semantic
integration risk: high. No new public bindings or source examples are shipped.
MCP knowledge impact now: none (proposal only). Eventual verified behavior:
yes, entry advice changes while genia_run still does not dispatch main.

## 9. Philosophy check

Minimalism YES; hidden activation avoided YES; portable semantics fixed by a
contract rather than invented by a host YES; pattern-first YES; validated-data
pipeline alignment YES. No topology/vendor/process-local implementation detail
becomes language semantics.

## 10. Prompt plan

Prior architecture pre-flight -> this contract/design proposal publication ->
later independent Codex review -> maintainer decisions -> separately authorized
contract/design completion -> TEST/RED -> implementation -> maintainability ->
truth sync -> independent audit -> distillation. Stop after this draft PR/issue
handoff. Future phases are described, not performed.

## 11. Host parity/conformance

Prospective affected hosts: Python, C++, future hosts. Portable semantics change
only after approval and later implementation; no behavior changes in this PR.
No specs/claims/gaps changed now. Shared evidence must lead implementation;
Python-first requires the explicit owned-gap policy in section 3a.

## 12. Gate

GO for the user-authorized **draft documentation publication only**. NO-GO for
contract acceptance, RED, implementation, release assignment or merge. Reviewer:
independent review requested for a later phase, not performed by this author.
The integration comment expressly says the #1226 observation is already posted;
do not duplicate it for this continuation of the same task.
