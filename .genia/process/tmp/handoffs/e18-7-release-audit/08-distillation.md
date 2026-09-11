# E18-7 — R18 Release-wide Doc Distillation

ISSUE: #797

---

## 1. EXTRACTION IS ALREADY COMPLETE

E18-6 was the extraction step for the release: every durable fact from all seven
slices now lives in a canonical document.

Re-verified during this pass that nothing durable remains only in a handoff:

| Durable content | Canonical home |
|---|---|
| one relation; the surfaces that share it | `GENIA_STATE.md`, `GENIA_RULES.md` §9.6, `docs/releases/R18.md` |
| four equality families | `GENIA_STATE.md`, `docs/releases/R18.md` |
| numeric matrix | `GENIA_STATE.md`, `docs/releases/R18.md` |
| map equality, legal keys, R17 order separation | `GENIA_STATE.md` (both sections), `docs/releases/R18.md` |
| protected security boundary | `GENIA_STATE.md` (equality + secrets sections), `docs/releases/R18.md` |
| conformance breadth and the host trap | `docs/releases/R18.md`, `HOST_PORTING_GUIDE.md` |
| the five non-claims | `GENIA_STATE.md`, `docs/releases/R18.md` |
| cross-doc guard | `docs/contract/semantic_facts.json` + sync test |
| audit verdict and method | `docs/releases/R18.md` "Skeptical release audit" |

The audit's three decisive results were added to `docs/releases/R18.md` in the
audit commit, because "we checked for host leakage and found none" is durable
release truth a future reader needs, not process narrative.

## 2. HANDOFF DIRECTORY DECISION: DELETE

All eight R18 handoff directories are deleted:

- `r18-portable-value-equality` (E18-0)
- `e18-1-structural-numeric-equality`
- `e18-2-map-equality-legal-keys`
- `e18-3-identity-token-protected`
- `e18-4-reconcile-equality-surfaces`
- `e18-5-multi-host-conformance`
- `e18-6-release-truth-sync`
- `e18-7-release-audit`

Reasons, in order of authority:

1. `docs/process/08-distillation.md` directs that after extraction the entire
   handoff directory is marked safe to delete, and that handoff files must not be
   migrated into docs. Extraction is complete (§1).
2. E18-0's own design assigned the fate of its directory to this issue:
   "Temporary `.genia/process/tmp/handoffs/r18-portable-value-equality/*`
   artifacts are subject to the normal Doc Distillation decision at E18-7." This
   is explicit authorization to remove another slice's artifacts.
3. `.genia/process/tmp/` is git-ignored by default — each file had to be
   force-added — which records the repository's intent that these are transient.
4. Keeping them would create a second, unmaintained copy of semantic truth that
   can drift away from `GENIA_STATE.md` without any test noticing. That is the
   precise failure mode the documentation truth model exists to prevent.

Nothing is lost: every handoff was committed, so all eight directories remain
fully recoverable from git history, and the commit messages and PR descriptions
carry the reasoning independently.

## 3. CONSISTENCY CHECK

`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
`AGENTS.md`, both roadmap surfaces, the releases index, `HOST_PORTING_GUIDE.md`,
the R17 and R18 release pages, and the R18 design record agree with each other
and with the runtime. All status lines now read complete with a PASS verdict, and
R17's page still records its own history honestly rather than being rewritten.

## 4. NOT DONE, DELIBERATELY

R19 was not started. R18's completion does not authorize any R19 work; the
`docs/process/08-roadmap-ticketing.md` gates apply to it as to any release.

## 5. COMPLEXITY CHECK

[x] Minimal and clear
