# E18-1 Structural and Exact Numeric Equality — Doc Distillation

ISSUE: #791
BRANCH: `issue-791-structural-numeric-equality`

---

## 1. EXTRACTED DURABLE CONTENT

From the handoffs, only these are durable (everything else is phase log,
planning, or scope negotiation and is discarded):

- one non-overloadable Genia equality relation; `!=` is exactly its negation
- kind separation, with kind difference yielding `false` rather than an error
- the exact numeric matrix: booleans are not numbers; exact int/float bridge with
  no lossy conversion; signed zero equal; matching infinities equal; NaN
  non-reflexive and propagating through containers
- structural comparison by named semantic contents for the E18-1 families
- equality purity
- the explicit statement of which families have **not** changed yet

## 2. DESTINATION FOR EACH ITEM

All of the above → `GENIA_STATE.md`, section "Portable value equality
(Experimental, R18 partial — E18-1 landed)". This landed in the documentation
phase; distillation confirms it is the right and only destination and that no
content remains stranded in a handoff.

Nothing maps to `README.md` or `GENIA_REPL_README.md`: E18-1 adds no CLI, REPL,
or user-facing surface.

Nothing new is added to `docs/design/*`. The durable design record
`docs/design/r18-portable-value-equality-contract.md` already exists from E18-0
and covers the whole release; duplicating a slice of it would create a second
source of truth.

## 3. DELIBERATELY DEFERRED TO #796 (recorded so it is not lost)

`GENIA_RULES.md` should carry the durable semantic rule that Genia has one
equality relation, that `==` is permanently non-user-overloadable, and that
literal patterns, duplicate bindings, `assert_eq`, and map-key identity do not
get separate equality rules.

That rule is deliberately **not** added here. Three of the four surfaces it names
are still owned by #792 and #794, so stating it now would make `GENIA_RULES.md`
claim more than is implemented — the one thing the documentation truth model
forbids. **#796 must add it**, once the relation is complete.

## 4. FILES UPDATED

None by this step. The documentation phase already placed the extracted content
in its canonical destination, and distillation found nothing to move, deduplicate,
or correct.

## 5. CONSISTENCY CHECK

Checked `GENIA_STATE.md`, `GENIA_RULES.md`, `README.md`,
`GENIA_REPL_README.md`, and the R18 design record against each other and against
the landed behavior. No contradictions.

Two statements were specifically re-verified as still true rather than stale:

- `GENIA_STATE.md`'s protected-equality description (includes carried-value
  equality) still matches the runtime; #793 changes the behavior and that line
  together.
- `GENIA_STATE.md`'s R17 note that map equality "remains unresolved" is still
  accurate; #792 resolves it.

## 6. CLEANUP

`.genia/process/tmp/handoffs/e18-1-structural-numeric-equality/` is **retained
until E18-7 (#797)**, not deleted now.

This follows the decision already recorded in E18-0's own design, which placed
the R18 handoff artifacts under "the normal Doc Distillation decision at E18-7",
and matches the precedent that E18-0's handoff directory was retained on `main`
when PR #805 merged. These files live under `.genia/`, not `docs/`, so they do
not violate the rule that no process artifact may live in `docs/` after merge.

#797 performs the release-wide distillation decision for all R18 handoff
directories together.

## 7. COMPLEXITY CHECK

[x] Minimal and clear

One section in one canonical document, no new doc categories, no duplication.
