# R4 issue triage matrix (issue #456)

GENIA_STATE.md is the final authority for implemented behavior. This document
is a committed, audit/triage-only artifact. It records **proposed** issue
actions; it does not perform any of them.

This matrix was originally produced as the issue #456 R4 lifecycle truth-audit
follow-up triage. It previously lived only in the gitignored process scratch
tree (`.genia/process/tmp/handoffs/...`), which made the guardrail test depend
on non-committed scratch input. It is now committed here as the source of truth
for the R4 issue triage guardrail.

Every row records `NO` in the `Action taken?` column: triage records
recommendations only. No GitHub issue closure, labeling, assignment, comment,
or follow-up issue creation is implied by this document. Any later issue action
requires explicit operator approval in a separate phase.

## Issue triage table

| Issue | State | Title | Classification | Recommended action | Rationale | Action taken? |
|---|---|---|---|---|---|---|
| #345-#356 | mixed / historical | Earlier lifecycle and execution-mode planning cluster | needs operator decision | no action | Historical scope should be reviewed individually before any mutation; some items may be obsolete, duplicate/superseded, or post-R4 deferred. | NO |
| #373 | historical | Earlier lifecycle-related follow-up | post-R4 deferred | defer/post-R4 | Keep outside R4 unless a later approved phase proves it is a small current-release blocker. | NO |
| #435 | historical | Earlier lifecycle-related follow-up | obsolete/close candidate | close as not planned | If it implies execution-mode runner, actor/server/plugin lifecycle, or setup/teardown behavior, it should not remain active R4 scope without operator approval. | NO |
| #442 | historical | Related infrastructure / prerequisite candidate | R4 follow-up | keep open | Treat as a possible follow-up only if it remains small and directly supports lifecycle truth/guardrails. | NO |
| #447 | R4 issue set | R4 kickoff reconciliation | completed/no action | close as completed | Current R4 sequence has already moved beyond kickoff reconciliation; confirm exact state before action. | NO |
| #448 | R4 issue set | Lifecycle vocabulary/non-goals | completed/no action | close as completed | docs/architecture/lifecycle.md and its guardrails cover this proposal boundary. | NO |
| #449 | R4 issue set | Lifecycle plan/phase data shape | completed/no action | close as completed | Current docs describe the internal validator as implemented without claiming runtime execution. | NO |
| #450 | R4 issue set | Lifecycle scope model | completed/no action | close as completed | Current docs describe internal scope-tree validation without runtime execution. | NO |
| #451 | R4 issue set | Cleanup/failure/result policy validation | completed/no action | close as completed | Current docs describe root policy map validation only. | NO |
| #452 | R4 issue set | Annotation binding model | completed/no action | close as completed | Current docs describe internal participant selection data only, not participant execution. | NO |
| #453 | R4 issue set | Deterministic ordering / reconciliation | completed/no action | close as completed | Current lifecycle docs include source_order, reverse_source_order, and stable_name_order boundaries. | NO |
| #454 | R4 issue set | Native test as first lifecycle consumer | completed/no action | close as completed | Current docs describe inert native-test descriptor validation with unchanged native-test behavior. | NO |
| #455 | CLOSED / COMPLETED | R4 lifecycle: document execution-mode lifecycle proposals without implementation | completed/no action | no action | #455 dependency is already completed/closed; its proposal-doc boundary is preserved. | NO |
| #456 | OPEN | R4 lifecycle: truth audit and follow-up issue triage | R4 follow-up | create small follow-up issue | Keep open until operator reviews this audit and approves any later issue-action phase; create follow-up only if a specific uncovered gap remains. | NO |

## Approved classifications represented

- R4 blocker
- R4 follow-up
- post-R4 deferred
- parking lot
- duplicate/superseded
- obsolete/close candidate
- completed/no action
- needs operator decision

## Recommended action labels represented

- keep open
- close as completed
- close as not planned
- close as duplicate/superseded
- relabel
- defer/post-R4
- create small follow-up issue
- no action

No table row performs an action. Every row records `NO` in the `Action taken?`
column.
