# E18-3 Identity, Opaque Token, and Protected Equality — Documentation Phase

ISSUE: #793

---

## Changed — `GENIA_STATE.md`

1. **The protected-equality line was false and is corrected.** It previously
   said protected equality "includes provider identity, purpose, and
   carried-value equality". Carried-value equality is exactly the oracle this
   slice removes, so leaving it would have left the final authority documenting a
   security property the runtime no longer has — and documenting the wrong one.
   It now states carrier-identity-only equality, that independently acquired
   carriers are unequal despite equal payloads, and that payload comparison
   requires authorized declassification first.

2. **Equality section retitled** to "E18-1, E18-2, and E18-3 landed", with a
   "Landed by E18-3" block for the three families that are never compared by
   contents, and the not-yet-landed list narrowed to E18-4 alone.

3. **Opaque tokens are described as a contract/design property only.** The
   wording states explicitly that R18 adds no token value, token-domain
   declaration, minting API, or syntax, implements no storage or `Revision`, and
   that no token can be created or observed from Genia source. This implements
   the issue's instruction not to present future token facilities as implemented
   source-level features, while still recording the equality rule and the
   closed-to-comparators / open-to-domains property that makes the family
   future-compatible.

## Deliberately unchanged

- `GENIA_RULES.md` — the single-relation rule remains handed to #796, as recorded
  in E18-1's distillation; `assert_eq` and pattern surfaces are still #794's.
- `README.md`, `GENIA_REPL_README.md` — no user-facing or CLI surface changed.
- `docs/contract/semantic_facts.json` and `tests/doc/test_semantic_doc_sync.py` —
  durable cross-doc guards remain #796's scope.
- `docs/design/r18-portable-value-equality-contract.md` — unchanged; still the
  approved contract for the release.
- `docs/reference/**`, cheatsheets, composability matrix — no public prelude
  function or Template/representation/matcher family member changed.

## Note on a superseded shared spec

`spec/eval/protected-secret-acquisition-and-matching.yaml` asserted that two
independent `secret_get` acquisitions compare equal. That assertion encoded the
payload-comparing behavior, so it was updated with an explicit note recording
what changed and why.

This is consistent with the truth hierarchy rather than an override of it:
`spec/*` sits below `GENIA_STATE.md`, the approved R18 contract defines
carrier-identity-only equality, and #793's own scope is "protected-carrier
equality by carrier identity only". `GENIA_STATE.md` and the spec were updated
together, so no authoritative source is left contradicting another.

## Validation

- `uv run pytest -q tests/doc` → 205 passed
- `uv run python -m tools.spec_runner` → total=660 passed=660 failed=0 invalid=0
