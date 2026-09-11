# E18-3 Identity, Opaque Token, and Protected Equality — Doc Distillation

ISSUE: #793

---

## 1. EXTRACTED DURABLE CONTENT

- identity-bearing values compare by logical runtime entity identity, and
  equality never dereferences, invokes, advances, or inspects the entity
- protected carriers compare by carrier identity only; independently acquired
  carriers are unequal despite equal payloads; payload comparison requires
  authorized declassification
- protected non-interference across every observable
- opaque semantic tokens: equal iff three hidden identities are equal, compared
  as data, no issuer contact, no comparator; closed to comparator extension and
  open to domain extension; **no implemented source-level feature in R18**
- all three families are terminal and are not legal map keys

## 2. DESTINATION

All of the above → `GENIA_STATE.md`: the "Landed by E18-3" block in the
"Portable value equality" section, plus the corrected protected-equality line in
the configuration/secrets section. Landed in the documentation phase.

Nothing maps to `README.md`, `GENIA_REPL_README.md`, or `docs/design/*`.

## 3. CARRIED FORWARD

1. **#794** — fix `sheet.py::_freeze_column_name`, still a second key-identity
   relation merging `true` with `1` (from #792's audit).
2. **#794 / #797** — confirm no semantic site decides map sameness with host `==`
   (from #792's audit).
3. **#797** — standing constraint: a future structural Genia value must not be
   callable, or it must be excluded from `_is_identity_bearing`'s final check
   explicitly, because the three families are classified before the structural
   branches.
4. **#795** — the absence of opaque-token shared specs is deliberate, not a
   coverage gap: R18 exposes no way to mint or observe a token from source.
5. **#796** — still owns the `GENIA_RULES.md` single-relation rule, and must not
   present token facilities as implemented source-level features.

## 4. FILES UPDATED

None by this step.

## 5. CONSISTENCY CHECK

`GENIA_STATE.md`, `GENIA_RULES.md`, `README.md`, `GENIA_REPL_README.md`, the R18
design record, and the updated shared spec were checked against each other and
against landed behavior. No contradictions. The configuration/secrets section and
the equality section now state the same protected rule rather than two different
ones.

## 6. CLEANUP

`.genia/process/tmp/handoffs/e18-3-identity-token-protected/` retained until the
release-wide distillation at #797, per E18-0's recorded decision.

## 7. COMPLEXITY CHECK

[x] Minimal and clear
