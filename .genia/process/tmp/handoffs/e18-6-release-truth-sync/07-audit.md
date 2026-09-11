# E18-6 R18 Authoritative Documentation and Release Truth Sync — Audit

ISSUE: #796
BRANCH: `issue-796-r18-release-truth-sync` (not `main`; matches change)

Audited skeptically, with the skepticism a documentation ticket invites: prose
can be confidently wrong and still pass every test.

---

## 1. SUMMARY

Status: **[x] PASS**

Every claim in the new and edited documents was checked against the runtime or
the code rather than against the other documents. Four stale claims are closed,
the deferred `GENIA_RULES.md` rule is landed, and the release's non-claims are
explicit in the two places a reader is most likely to look.

---

## 2. CLAIM-BY-CLAIM VERIFICATION

A documentation ticket's real risk is an assertion that sounds right. Each
substantive claim in `docs/releases/R18.md` was therefore verified against
independent evidence, not against another document:

| Claim | Verified against |
|---|---|
| `[true == 1, false == 0, 1 == 1.0, 1 == 1.5, 0.0 == -0.0]` → `[false, false, true, false, true]` | run directly; matches |
| map example output `[true, ["x", "y"], ["y", "x"]]` | run directly; matches |
| `map_count(...)` with `true` and `1` keys → `2` | run directly; matches |
| "24 shared cases" | enumerated from the loader: exactly 24 `r18-` cases |
| "zero cases reported `unsupported`" | `test_r18_conformance_protocol_evidence_795.py` asserts `declined == []` |
| "the carrier type itself defines no host equality" | read `values.py`: `GeniaProtected` has no `__eq__`; `__hash__ = None` |
| "no new public function, builtin, operator, syntax, capability, or Core IR node" | `git diff main...` across R18: no parser/IR/lowering change; `spec/manifest.json` untouched |
| "no C++ host was implemented" | `hosts/cpp` unchanged across R18 |

The two code examples embedded in the release page are executable and were run,
not transcribed from memory.

## 3. THE FIVE NON-CLAIMS

Each is stated in **both** `GENIA_STATE.md` (final authority) and
`docs/releases/R18.md` (the page a host implementer reads), because a reader who
finds one is unlikely to consult the other:

1. no C++ host — Python remains reference and only production host
2. `==` is not user-overloadable, including by future open functions
3. no token-domain syntax, minting API, or token value; no source-level token
   surface at all
4. no storage `Revision`
5. map iteration order unchanged and distinct from map equality

Checked that none of these is phrased as a future promise, which would be its own
form of over-claiming.

## 4. STALE CLAIMS CLOSED

- `docs/releases/R17.md` said twice that map equality remains unresolved. Fixed in
  a way that preserves R17's historical record rather than rewriting history: the
  audit narrative now says map equality "was a separately gated open question at
  the time of this audit, and was subsequently resolved by R18". Editing a
  completed release's audit conclusion to pretend it knew about R18 would have
  been dishonest.
- `docs/design/r18-portable-value-equality-contract.md` carried "not
  implemented". Now records what landed, and explicitly retains its planning
  sections as historical rather than deleting them.
- Both roadmap surfaces called R18 planned/not active. Now show E18-0–E18-6
  delivered with E18-7 as the remaining gate.

## 5. STATUS HONESTY

R18 is **not** recorded as complete anywhere. Every status line says E18-0
through E18-6 delivered with the E18-7 audit pending. This matches R17's
precedent, where the audit slice itself flipped the status to complete after
recording a PASS verdict.

Challenged: should #796 have marked it complete, since the task's completion
checklist expects "roadmap status says R18 complete"? No — that check belongs
after #797 records a PASS. Marking complete before the audit would make the
audit's verdict cosmetic, which is exactly what a skeptical release gate must not
be. **#797 must flip these status lines**, and that obligation is recorded in the
distillation.

## 6. NEW GUARD TEST

`test_authoritative_docs_capture_the_one_equality_relation` requires both
`GENIA_RULES.md` and `GENIA_STATE.md` to state that there is one relation and
that it is not user-overloadable.

Challenged as a weak string-match test. It is, deliberately: it cannot verify
prose is correct, only that the claim has not been silently deleted. That is the
realistic failure mode — a later release adding an equality protocol and quietly
removing the sentence that forbade it. Recorded as a floor, not a substitute for
reading the section.

Semantic facts grew 21 → 22, with the cap raised in the same change so the
"intentionally small" intent stays enforced rather than removed.

## 7. VALIDATION

- `uv run pytest -q tests/doc tests/unit/test_doc_style_sync.py` → 225 passed
- `uv run python tools/gen_function_docs.py --check` → up to date
- `uv run python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage` → 0 errors, 0 warnings
- `uv run mkdocs build --strict` → built, with the new R18 nav entry
- `uv run ruff check .` → clean
- full regression `-m "not loopback"` → **2 failed / 4202 passed**, exactly the
  two pre-existing root/`chmod 000` cases
- no file under `src/` changed

## 8. VERDICT

**PASS.** Obligations for #797: flip the status lines to complete after recording
a PASS verdict; confirm no source-reachable value lands in the unclassified
identity terminal; re-check the standing constraint that a future structural
Genia value must not be callable.
