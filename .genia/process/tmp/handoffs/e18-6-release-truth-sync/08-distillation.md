# E18-6 R18 Authoritative Documentation and Release Truth Sync — Doc Distillation

ISSUE: #796

---

## 1. EXTRACTION

This ticket *is* the extraction step for R18: the durable content from every
prior slice's handoffs has now landed in canonical documents.

| Durable content | Destination |
|---|---|
| the one relation and its surfaces | `GENIA_STATE.md`, `GENIA_RULES.md` §9.6, `docs/releases/R18.md` |
| four equality families | `GENIA_STATE.md`, `docs/releases/R18.md` |
| numeric matrix | `GENIA_STATE.md`, `docs/releases/R18.md` |
| map equality, legal keys, R17 order separation | `GENIA_STATE.md`, `docs/releases/R18.md` |
| protected security boundary | `GENIA_STATE.md` (both sections), `docs/releases/R18.md` |
| conformance breadth | `docs/releases/R18.md`, `HOST_PORTING_GUIDE.md` |
| the five non-claims | `GENIA_STATE.md`, `docs/releases/R18.md` |
| cross-doc guard | `docs/contract/semantic_facts.json` + sync test |

Nothing durable remains stranded in a handoff.

## 2. HANDOFF DIRECTORIES

Seven R18 handoff directories now exist under
`.genia/process/tmp/handoffs/`: `r18-portable-value-equality` (E18-0) and
`e18-1-…` through `e18-6-…`.

**#797 makes the release-wide retain-or-delete decision** for all of them
together, as E18-0's own design specified. They live under `.genia/`, not
`docs/`, so they do not violate the rule that no process artifact may live in
`docs/` after merge.

## 3. CARRIED FORWARD TO #797

1. **Flip the status lines to complete** after recording a PASS verdict:
   `docs/releases/R18.md`, `docs/releases/README.md`,
   `docs/strategy/release-roadmap.md` (three places),
   `docs/strategy/roadmap/r16-r20.md`, and
   `docs/design/r18-portable-value-equality-contract.md`. Deliberately left
   pending so the audit's verdict is not cosmetic.
2. Confirm no source-reachable value lands in the relation's unclassified
   identity terminal.
3. Re-check the standing constraint that a future structural Genia value must not
   be callable, because the three non-structural families are classified before
   the structural branches.
4. Make the release-wide handoff-directory decision.

Already discharged, and not to be re-searched blind: #792's map-sameness
obligation (discharged by #794's post-change sweep, recorded there).

## 4. CONSISTENCY CHECK

`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
`AGENTS.md`, both roadmap surfaces, the releases index, `HOST_PORTING_GUIDE.md`,
the R17 and R18 release pages, and the R18 design record were checked against each
other and against the runtime. No contradictions.

R17's page was corrected without rewriting its history: its audit narrative now
records that map equality was open *at the time of that audit* and was later
resolved by R18, rather than being edited to appear as though it knew.

## 5. COMPLEXITY CHECK

[x] Minimal and clear — one new release page, one new rules section, one semantic
fact, one porting-guide section, and status corrections. No new doc category.
