# E18-4 Reconcile Patterns, Assertions, and Equality-like Surfaces — Doc Distillation

ISSUE: #794

---

## 1. EXTRACTED DURABLE CONTENT

- every equality-like surface answers exactly as `==` does, and none consults
  host-language equality or a host container's key rules
- the specific per-surface consequences: literal patterns, duplicate bindings,
  `assert_eq`, the meta-evaluator's operators
- Sheet column-name identity is Genia equality, over the legal map-key family

## 2. DESTINATION

`GENIA_STATE.md` — the "Landed by E18-4" block, the `sheet(columns)` helper line,
and the `assert_eq` line. Landed in the documentation phase.

## 3. CARRIED FORWARD

1. **#796** now owns the `GENIA_RULES.md` single-relation rule and can finally
   write it truthfully: all four surfaces it names (literal patterns, duplicate
   bindings, `assert_eq`, map-key identity) have landed. This has been deferred
   since E18-1's distillation specifically to avoid claiming more than was
   implemented; that reason no longer applies.
2. **#797** — confirm no source-reachable value lands in the unclassified
   identity terminal; re-check the standing constraint that a future structural
   Genia value must not be callable.
3. **#792's obligation is discharged**: the post-change sweep confirms no
   semantic site decides map sameness with host `==`. Recorded here so #797 can
   verify the claim rather than repeat the search blind.

## 4. FILES UPDATED

None by this step.

## 5. CONSISTENCY CHECK

`GENIA_STATE.md`, `GENIA_RULES.md`, `README.md`, `GENIA_REPL_README.md`, and the
R18 design record checked against each other and against landed behavior. No
contradictions. The Sheets section and the equality section now state the same
column-name rule rather than only one of them mentioning it.

## 6. CLEANUP

`.genia/process/tmp/handoffs/e18-4-reconcile-equality-surfaces/` retained until
the release-wide distillation at #797.

## 7. COMPLEXITY CHECK

[x] Minimal and clear
