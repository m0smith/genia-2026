# E18-4 Reconcile Patterns, Assertions, and Equality-like Surfaces — Documentation Phase

ISSUE: #794

---

## Changed — `GENIA_STATE.md`

1. **Equality section retitled** to "R18 — E18-1 through E18-4 landed", with a
   "Landed by E18-4" block listing every surface that now answers as `==` does,
   and the statement that no surface consults host-language equality or a host
   container's key rules for a semantic question. The not-yet-landed list is
   **now empty**.

2. **Sheet column-name legality recorded**, because this issue changed a
   rejection boundary: column-name uniqueness uses Genia equality, the legal
   family matches the legal map-key family, `true` and `1` are distinct columns,
   and values outside the family (maps, Outcomes) are rejected at construction.
   Added both in the equality section and on the `sheet(columns)` helper line, so
   a reader of the Sheets section is not left with the old implication.

3. **`assert_eq` sharpened** from "according to current Genia equality behavior"
   to "exactly when `actual == expected` under the one Genia equality relation",
   which is now a precise, testable claim rather than a deferral.

## Checked and correct as-is

- `GENIA_STATE.md` "pair equality is structural" and "duplicate binding names
  follow normal duplicate-binding equality semantics" — both true, and the second
  is now precise rather than vague, since "normal" is a single defined relation.
- `GENIA_RULES.md` "pair equality is structural" — true.

## Deliberately unchanged

- `GENIA_RULES.md`'s single-relation rule remains #796's, as recorded in E18-1's
  distillation. It can now be written truthfully for the first time, since all
  four surfaces it names have landed — that is exactly why #796 owns it.
- `README.md`, `GENIA_REPL_README.md` — no user-facing or CLI surface changed.
- `docs/contract/semantic_facts.json`, `tests/doc/test_semantic_doc_sync.py` —
  #796's scope.
- `docs/design/r18-portable-value-equality-contract.md` — unchanged.
- `docs/reference/**`, cheatsheets, composability matrix — no public prelude
  function or family member changed; all sync tests pass.

## Validation

- `uv run pytest -q tests/doc` → 205 passed
- `uv run python -m tools.spec_runner` → total=664 passed=664 failed=0 invalid=0
- `uv run ruff check .` → clean
