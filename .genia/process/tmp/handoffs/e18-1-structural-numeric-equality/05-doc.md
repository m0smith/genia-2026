# E18-1 Structural and Exact Numeric Equality — Documentation Phase

ISSUE: #791
STATUS: documentation synchronized with landed behavior

---

## Decision

E18-6 (#796) owns authoritative R18 release truth. This issue therefore keeps
release-level wording minimal. But `AGENTS.md`'s non-negotiable rule requires
`GENIA_STATE.md` to be updated by any change to language behavior, and E18-1
changed observable behavior (`true == 1` is now `false`; equal byte values now
compare equal; NaN non-reflexivity now propagates through containers). Leaving
`GENIA_STATE.md` silent would leave the final authority describing a relation
the runtime no longer implements.

So: one concise, strictly truthful section was added, and it explicitly names
what has **not** landed so no reader can infer completed R18.

## Changed

- `GENIA_STATE.md` — new section "Portable value equality (Experimental, R18
  partial — E18-1 landed)", placed after the R17 integer portability section.
  It states only what E18-1 implements, names the reference-host module, and
  lists the families still owned by E18-2/E18-3/E18-4 as unchanged.

## Deliberately unchanged

- `GENIA_RULES.md` — no rule contradicts the landed behavior. Its existing
  numeric rules already exclude booleans from numeric domains (for example
  "integers excluding booleans", "non-boolean predicate result is misuse"),
  which agrees with boolean/number separation rather than conflicting with it.
- `GENIA_REPL_README.md`, `README.md` — no user-facing statement contradicts the
  landed behavior; broad release wording is #796.
- `docs/contract/semantic_facts.json` and `tests/doc/test_semantic_doc_sync.py`
  — durable cross-doc equality guards are #796's scope, once the relation is
  complete. Adding a guard now would encode a half-landed relation.
- `docs/design/r18-portable-value-equality-contract.md` — unchanged. It remains
  the approved contract/design record and still correctly carries its
  "not implemented" status for the release as a whole.
- `docs/reference/**` and `mkdocs.yml` — no public prelude function was added or
  had its `@doc`/`@meta` changed, so no regeneration is required.
- Cheatsheets — no cheatsheet example depended on boolean/number coercion or on
  byte-value identity; the cheatsheet sync tests pass unchanged.

## Contradiction sweep performed

Searched the authoritative documents and `docs/` for statements that a boolean
equals a number, that a predicate returning a truthy non-boolean is included by
`filter`/`any?`, and for existing equality claims. Findings:

- No document claimed boolean/number equality.
- `GENIA_STATE.md` line ~558 documents protected equality as including
  carried-value equality. That is still exactly the current behavior; #793
  changes both the behavior and that line together.
- `GENIA_STATE.md`'s R17 note that map equality "remains unresolved outside R17"
  is still accurate; #792 resolves it.

## Validation

- `uv run pytest -q tests/doc` → 205 passed
- `uv run python -m tools.spec_runner` → total=651 passed=651 failed=0 invalid=0
