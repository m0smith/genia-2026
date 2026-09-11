# E18-6 R18 Authoritative Documentation and Release Truth Sync — Pre-flight

ISSUE: #796
PARENT: #789
BLOCKED BY: #791, #792, #793, #794, #795 — all merged (PRs #806–#810)
STATUS: pre-flight

---

## 0. BRANCH

Branch slug: `r18-release-truth-sync`
Expected branch: `issue-796-r18-release-truth-sync`
Base: `main` @ `ded6533`

---

## 1. SCOPE LOCK — documentation only

### Includes

- `docs/releases/R18.md` (new; required)
- `GENIA_RULES.md` — the single-relation rule, deferred here since E18-1
- `GENIA_STATE.md` — finalize the R18 section
- `docs/contract/semantic_facts.json` and `tests/doc/test_semantic_doc_sync.py` —
  a durable cross-doc guard for the central R18 invariant
- `docs/design/r18-portable-value-equality-contract.md` — status line only
- `docs/releases/R17.md` — correct a statement R18 made false
- roadmap status
- `README.md` / `GENIA_REPL_README.md` / host-portability docs where affected

### Excludes

- any runtime or semantic change
- speculative token, storage, or C++ behavior
- the release audit and final completion status (#797)

---

## 2. CONTRADICTION SWEEP (performed before scoping)

Searched every document for claims R18 has now falsified.

| Location | Current text | Problem |
|---|---|---|
| `docs/releases/R17.md:72-74` | "Map equality also remains unresolved: the current Python host's identity-based `==` observation … is not portable structural-equality semantics" | False since #792. A published release page is asserting behavior the runtime no longer has. |
| `docs/releases/R17.md:96` | "map equality remains a separately gated open question" | Same. |
| `docs/design/r18-portable-value-equality-contract.md:3` | "Status: **E18-0 contract/design candidate — not implemented.**" | False since #791–#795. |
| `docs/strategy/roadmap/r16-r20.md:107` | "Status: Planned foundational portability contract, not active." | False. |
| `GENIA_RULES.md` | no single-relation rule | Not a contradiction, but the durable semantic rule is still missing; deferred here since E18-1's distillation precisely because it could not be stated truthfully until #794 landed. It now can. |

`GENIA_STATE.md` is already accurate — each slice updated it as it landed — and
needs only its status line finalized.

---

## 3. THE FIVE NON-CLAIMS THIS RELEASE MUST MAKE EXPLICIT

Documentation must leave no room to infer any of these, because each is a
plausible misreading of a release called "Portable Value Equality":

1. Python remains the reference and only production host; **no C++ host was
   implemented** by R18.
2. `==` is **not user-overloadable**, and no open-function or extension
   mechanism can redefine it.
3. **No token-domain syntax, minting API, or token value** exists; opaque
   semantic tokens are a contract/design family with no source-level surface.
4. **No storage `Revision`** was implemented merely by defining opaque-token
   equality.
5. Map **iteration order** remains the R17 contract and is a separate observable
   from map equality.

---

## 4. PORTABILITY ANALYSIS

All seven fields resolved; no `TBD`.

1. **Portability zone** — *documentation*. This ticket records the portable
   contract already implemented; it defines no behavior.
2. **Core IR impact** — `none`. No `Ir*` node family touched; no source change.
3. **Capability categories affected** — `none`. No capability added or altered;
   `spec/manifest.json` untouched.
4. **Shared spec impact** — `none`. No spec case added, changed, or removed.
5. **Python reference host impact** — `none`. No file under `src/` changes.
6. **Host adapter impact** — `none`.
7. **Future host impact** — this is the ticket a future host implementer reads
   first. `docs/releases/R18.md` plus the R18 design record and the 24 shared
   cases must be sufficient to implement conforming equality without reading
   Python source, and must be explicit about what R18 did **not** do so an
   implementer does not go looking for token or storage surfaces.

---

## 5. TEST STRATEGY

Documentation tests, cheatsheet sync, composability matrix sync, and the strict
docs build. A new semantic-fact guard is added, which requires updating both
`semantic_facts.json` and its sync test — both are explicitly in this issue's
scope.

Baseline: `main` @ `ded6533` — `-m "not loopback"` 2 failed / 4200 passed,
`-m loopback` 26 passed, shared specs 668/668, docs 205 passed, `ruff` clean.

---

## 6. COMPLEXITY CHECK

[x] Revealing structure — it makes an implemented contract legible and closes
four stale claims.

---

## 7. DOC DISTILLATION CHECK

Creates process artifacts? YES. Adds `docs/design` files? NO — the R18 design
record already exists and is only status-corrected. Adds `docs/releases/R18.md`,
which is a durable release page, not a process artifact.

Doc drift risk: [x] High — this is the drift-closing ticket itself.

---

## 8. PHILOSOPHY CHECK

- preserves minimalism? YES — concise pages, no new doc category
- avoids hidden behavior? YES
- keeps semantics out of host? YES
- aligns with pattern-matching-first? YES

---

## KILLER WORKFLOW ALIGNMENT

[x] Indirectly — accurate equality documentation is what lets pipeline authors
rely on comparison, keying, and assertions behaving the same everywhere.

---

## 9. PROMPT PLAN

Preflight → Contract → Design → Docs → Audit → Distillation. No failing-test or
implementation phase: this ticket changes no behavior, and inventing one would be
process theatre.

---

## FINAL GO / NO-GO

**YES.** All blockers merged.
