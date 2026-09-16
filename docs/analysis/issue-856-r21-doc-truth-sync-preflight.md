# Issue #856 Preflight — E21-4 R21 Documentation and Release-Example Truth Sync

Status: process artifact for issue #856 (E21-4). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority.

## Scope

Documentation-only, per issue #856: re-read merged `main` (E21-1 through
E21-3, #853–#855), reconcile `GENIA_STATE.md`, `GENIA_RULES.md`,
`GENIA_REPL_README.md`, `README.md`, Core IR/host-interop docs, and roadmap
status only where R21 makes them stale, and publish `docs/releases/R21.md`
with runnable examples. No parser/lowering/runtime implementation phase is
authorized.

## Truth inventory (what actually changed since #852 opened)

- `GENIA_STATE.md`: already updated by #853 (section 9.21) and #854
  (section 9.22); nothing further required — #855 added no new behavior.
- `GENIA_RULES.md`: had **no** numeric-literal grammar/invariant section
  at all before this ticket (grep confirmed zero matches for
  "DIGIT+"/"numeric literal"/etc.) — this is a genuine gap this ticket
  fills with a new section 8.6.
- `GENIA_REPL_README.md`: already updated by #853's literals bullet;
  nothing further required.
- `README.md`: has no dedicated numeric-literal grammar section to go
  stale; its only numeric mentions are generic (`sum` expecting plain
  numbers, `Number` as a core value kind) and remain accurate. No change.
- `docs/architecture/core-ir-portability.md`: already updated by #854;
  nothing further required.
- `docs/host-interop/*`: grep for `IrLiteral`/numeric-literal mentions
  found none — no staleness introduced by R21.
- Roadmap status: `docs/strategy/release-roadmap.md`,
  `docs/strategy/roadmap/r21-r24.md`, and
  `docs/strategy/roadmap/sequence.md` all still said R21 was "Planned, not
  active" despite E21-1 through E21-3 being merged — genuine drift this
  ticket corrects to "In Progress" (not "Complete" — #857 has not run
  yet).
- `docs/releases/README.md` and `mkdocs.yml` nav: missing an R21 entry
  (both also already missing R19/R20 entries pre-existing this ticket —
  tracked separately in issue #859, not repaired here to stay in scope);
  added only the R21 entry.

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?** None — pure
   documentation; no code, parser, lowering, or Core IR change.
2. **Does this change alter the minimal portable Core IR node family?**
   No.
3. **Does this change require a host-native binary float?** No.
4. **Does this change require another host implementation to consult
   Python-specific behavior?** No — if anything this ticket reduces that
   risk by giving an independent host a written R21 summary page.
5. **Does this change affect R16/R17/R18/R19/R20?** No.
6. **Is any part of this change host-local-only?** No.
7. **What new portable evidence must exist?** None beyond what #853/#854/
   #855 already produced; this ticket adds a documentation-verification
   test (`tests/unit/test_r21_release_doc_examples_856.py`) proving the
   new release page's examples are accurate, mirroring
   `test_r19_release_doc_examples.py`'s established pattern.

## Conclusion

Preflight is complete. No R22/R23 semantics are described as implemented;
every claim in the new/updated docs is traceable to #853/#854/#855's
merged, audited behavior.
