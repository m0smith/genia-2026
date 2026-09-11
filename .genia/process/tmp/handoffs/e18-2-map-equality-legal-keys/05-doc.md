# E18-2 Map Equality, Legal Keys, and Key Equivalence — Documentation Phase

ISSUE: #792
STATUS: documentation synchronized with landed behavior

---

## Changed — `GENIA_STATE.md`

1. **Equality section retitled** to "R18 partial — E18-1 and E18-2 landed", with
   a new "Landed by E18-2" block covering map equality, the key relation, the
   closed legal-key family, reflexivity and NaN rejection, rejection on every
   operation, and explicit preservation of R17 order.

2. **R17 open question resolved.** The R17 map section previously recorded as a
   "current limitation/open question" that separately constructed equal-content
   maps compare by host-object identity. That is no longer true, so leaving it
   would have left the final authority contradicting the runtime. Replaced with a
   pointer to the equality section plus an explicit statement that no order rule
   in that section changed.

3. **Key family wording corrected.** "list keys are supported by stable
   structural key-freezing" became recursive structural key *canonicalization*,
   and the tuple-key line now says plainly that host tuple keys are a
   runtime-level interop accommodation and **not** a public Genia key family.
   This implements the approved contract's instruction that the existing host
   tuple/`None` support "is not authority to introduce a new public tuple/null
   key kind" — the accommodation keeps working, but it is no longer documented
   in a way that reads as a public key kind.

## Deliberately unchanged

- `GENIA_RULES.md` — no rule contradicts the landed behavior. The single-relation
  rule remains handed to #796, as recorded in E18-1's distillation, because
  `assert_eq`, literal patterns, and duplicate bindings are still #794's.
- `README.md`, `GENIA_REPL_README.md` — no user-facing statement contradicts the
  landed behavior; no CLI or REPL surface changed.
- `docs/contract/semantic_facts.json` and `tests/doc/test_semantic_doc_sync.py` —
  durable cross-doc equality guards remain #796's scope, once the relation is
  complete.
- `docs/design/r18-portable-value-equality-contract.md` — unchanged; still the
  approved contract for the release as a whole.
- `docs/reference/**`, `mkdocs.yml`, cheatsheets — no public prelude function was
  added or changed; cheatsheet sync tests pass unchanged.
- `docs/design/composability-matrix.md` — no Template, representation, or matcher
  family member was added, renamed, or removed, so the matrix's derived family is
  unchanged; `tests/doc/test_composability_matrix_sync.py` passes.

## Contradiction sweep

Searched the authoritative documents for claims about map equality, map key
identity, and keyable families.

- The one genuine contradiction (the R17 open question) is fixed above.
- The protected-equality line still correctly describes current behavior; #793
  changes the behavior and that line together.
- No document claimed that `true` and `1` are the same key or that NaN is keyable.

## Validation

- `uv run pytest -q tests/doc` → 205 passed
- `uv run python -m tools.spec_runner` → total=657 passed=657 failed=0 invalid=0
