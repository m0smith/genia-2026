# 08 — Roadmap Ticketing

Status: Process guide.

This phase turns approved roadmap items into GitHub issues.

It happens after strategy/pre-flight planning and before implementation work begins.

## Required Inputs

Read completely:

- AGENTS.md
- GENIA_STATE.md
- GENIA_RULES.md
- GENIA_REPL_README.md
- README.md
- docs/strategy/killer-workflow.md
- docs/strategy/release-roadmap.md

If sources conflict, GENIA_STATE.md wins for implemented behavior.

## Purpose

Create tickets that keep upcoming work aligned with the release roadmap.

This phase prevents agents from turning one approved direction into a pile of unrelated shiny objects.

## Scope

This phase creates or proposes issues.

It does NOT:

- implement code
- change language behavior
- update implemented-behavior docs
- claim planned work is current behavior
- expand roadmap scope without approval

## Roadmap Classification

Every proposed ticket must be classified as one of:

- Current release
- Next release
- Required infrastructure
- Follow-up
- Parking lot

If classified as Parking lot, do not create it unless explicitly approved.

## Ticket Shape

Each ticket must include:

- release target
- roadmap alignment
- problem statement
- scope includes
- scope excludes
- affected docs/tests/specs
- acceptance criteria
- non-goals
- risk of drift
- required process phases

## Required Acceptance Criteria

Each ticket must state:

- what behavior is expected
- how it will be tested
- which docs may need updates
- what must not change

## Ticket Ordering

Tickets should be ordered by dependency:

1. contract/spec clarification
2. failing tests/specs
3. minimal implementation
4. docs sync
5. audit/truth review
6. migration/follow-up

Do not create broad implementation tickets when smaller staged tickets are safer.

## Output

Produce:

- proposed issue list
- recommended creation order
- dependency notes
- parking-lot items, if any

## Final Check

Before creating tickets, answer:

- Does this support the current or next roadmap release?
- Is the scope small enough for one process run?
- Are speculative features clearly excluded?
- Are docs protected from claiming future behavior?