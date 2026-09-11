# E18-2 Map Equality, Legal Keys, and Key Equivalence — Doc Distillation

ISSUE: #792

---

## 1. EXTRACTED DURABLE CONTENT

- map equality is equality of mappings, independent of insertion history
- mapped values use the full relation; a map holding NaN as a value is
  legitimately non-reflexive
- for legal keys, key identity is exactly `==`, across lookup, presence,
  insertion, replacement, removal, and duplicate detection
- the closed legal-key family
- key reflexivity, and therefore NaN rejection at any depth, on every operation
- R17 order is unchanged and is a separate observable from equality
- host tuple/`None` keys are an internal accommodation, not a public key family

Discarded as process text: phase logs, scope negotiation, measurement tables,
and the before/after defect narrative.

## 2. DESTINATION

All of the above → `GENIA_STATE.md`, in the "Portable value equality" section
and in the two corrected lines of the R17 map section. Landed in the
documentation phase; distillation confirms this is the right and only
destination and that nothing durable is stranded in a handoff.

Nothing maps to `README.md` or `GENIA_REPL_README.md` (no user-facing surface
changed) or to `docs/design/*` (the R18 design record already covers the
release).

## 3. CARRIED FORWARD (recorded so it is not lost)

Two items must survive this issue:

1. **#794 must fix `sheet.py::_freeze_column_name`.** It is a second,
   independent key-identity relation that still merges `true` with `1`, so
   `sheet([[true, [1]], [1, [2]]])` is wrongly rejected as duplicate column
   names. Out of scope here; in scope for #794's equality-like surface
   reconciliation.
2. **#794 and #797 must confirm no semantic site decides map sameness with host
   `==`.** `GeniaMap` deliberately has no host `__eq__`; the canonical relation
   lives in `equality.py`.

3. **#796 still owns** the `GENIA_RULES.md` single-relation rule, as recorded in
   E18-1's distillation.

## 4. FILES UPDATED

None by this step; the documentation phase already placed the content canonically.

## 5. CONSISTENCY CHECK

`GENIA_STATE.md`, `GENIA_RULES.md`, `README.md`, `GENIA_REPL_README.md`, and the
R18 design record were checked against each other and against landed behavior.
No contradictions. The R17 map section and the equality section now agree
explicitly rather than by omission.

## 6. CLEANUP

`.genia/process/tmp/handoffs/e18-2-map-equality-legal-keys/` is retained until
the release-wide distillation at #797, following E18-0's recorded decision and
E18-1's precedent. These files live under `.genia/`, not `docs/`.

## 7. COMPLEXITY CHECK

[x] Minimal and clear
