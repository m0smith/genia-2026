# Release R24 — Facet Identity via Named Patterns

Status: **Proposal — non-authoritative, not adopted.** Styled to match `docs/strategy/release-roadmap.md`. Numbered R24, after the R23 Python-reduction release proposed alongside it. Independent of R23 and R16–R22 (C++ host work) — this touches the Experimental R9 generic carrier/representation slice only.

Source: `docs/design/facet-identity-named-patterns-swot.md` — full exploration, reading comparison (opaque token vs. structural predicate vs. named pattern), and SWOT for replacing string-identified carrier facets with named-pattern identity.

## Theme

> Stop making facet identity a spelling exercise — reuse the named-Pattern mechanism the language already has instead of asking every caller to get a string exactly right.

## Why now

The generic carrier/representation system (`represent`/`representation_match`/`strip_representation`) is still marked Experimental in `GENIA_STATE.md`, which is the cheapest point in its lifecycle to change facet identity — no stability guarantee is broken by moving off bare strings. The fix reuses existing machinery (`pattern Name(value) = body`) rather than adding a new primitive, which keeps the change small, but it surfaced a real, independent gap during exploration (named-pattern values have almost no introspection story today) that has to be closed first or the fix would make facet-mismatch debugging worse, not better, in the interim.

## Scope

### E24-1 — Named-pattern introspection foundation (do first; this is a hard sequencing dependency, not a nice-to-have)

- Add a deliberate `display`/`debug_repr` rendering branch for `GeniaNamedPattern` values in `format_display`/`format_debug` (`src/genia/utf8.py`). Today this falls through to a generic `str(value)` catch-all that only happens to show `<pattern X>` because Python's `str()` defaults to `__repr__()` — not a spec'd, intentional rendering the way `<protected>`/`<represented>`/`<index-handle>` already are. Decide the canonical rendered form (`<pattern Name>` is the natural continuation of current accidental behavior) and document it as a real contract.
- Add a spec'd `pattern_name(p)` accessor, analogous to the existing `format_template`/`format_tag` accessors for `Format` values: takes a named-pattern value, returns its declared name as a string, raises a deterministic `TypeError` for non-pattern input. This is the part that actually matters for facet debugging — it travels with the *value*, unlike `meta()`/`doc()`, which are keyed by the current environment binding name and lose the thread once a value is aliased, imported under a different name, or stored away from its original binding.
- Optional, low-cost addition: default an `@name` metadata entry to the binding's own declared name on every annotatable top-level binding (function, assignment, named pattern) when no explicit `@name`/other name-bearing annotation is present. `eval_annotations` in `evaluator.py` already receives `target_name` on every call site; this only requires using it as a default rather than discarding it. Weaker than `pattern_name(p)` for the facet use case specifically (still binding-keyed), but cheap and independently useful for `help()`/`meta()` introspection generally.
- Spec coverage: new `spec/eval` cases asserting the exact `display`/`debug_repr` string for a named-pattern value, and for `pattern_name(p)` on valid and invalid input.

### E24-2 — Facets as named patterns (depends on E24-1)

- Loosen `represent`'s facet-argument runtime check (`isinstance(facet, str)`) to also accept a `GeniaNamedPattern` value.
- Change `representation_match`/`strip_representation`'s facet comparison to identity equality when the facet argument is a named-pattern value (string facets keep string equality, at least through a transition window — see Non-goals).
- Migrate the JSON boundary's internal `"json"` string facet to a canonical exported named pattern (e.g. `pattern Json(value) = some(value)`, living in the JSON prelude module) as the reference example of the new convention.
- Update the R9 design/contract docs (`docs/design/r9-value-template-representation-contract.md` and neighbors), the cheatsheet (`docs/cheatsheet/core.md`), and the existing test suite together, per `AGENTS.md`'s documentation checklist.
- Improve the mismatch error: today `representation_match` returns a generic `none("representation-mismatch")` with no facet identity in the payload. With `pattern_name(p)` available from E24-1, consider whether the mismatch context should name the expected facet (not the candidate's actual facet, to avoid leaking unrelated carrier information across boundaries — needs its own small design decision, not assumed).

## Acceptance criteria

- `pattern X(v) = some(v)` values render a documented, spec-asserted string via `display`/`debug_repr` — not an incidental Python fallthrough.
- `pattern_name(p)` exists, is spec'd, and is covered by `spec/eval` cases for both valid named-pattern input and a deterministic error on non-pattern input.
- `represent(Json, value)` / `representation_match(Json, value)` work end-to-end for a named-pattern facet, verified against a real test case (not just the JSON boundary's internal migration).
- The JSON boundary's internal facet is migrated and all existing JSON-boundary tests (`spec/eval`, `tests/unit/*`) pass unchanged in observable behavior.
- `GENIA_STATE.md`/`GENIA_RULES.md` updated to describe named-pattern facet identity as a supported (Experimental) form, alongside — not instead of — the existing string form, unless E24-2's scope decision explicitly deprecates strings (see Non-goals).

## Excluded

- Reading B from the exploration (facet as structural predicate/matcher) — rejected outright; conflates representation identity with Template validation, which `GENIA_STATE.md` deliberately keeps separate.
- Any new parser syntax or Core IR node for declaring or using facet-patterns — this stays within the existing "no parser syntax, no Core IR node" invariant the generic carrier slice already holds itself to.
- Giving a facet-pattern's `body` real behavioral meaning (e.g., threading the carried value through the facet's own matcher as bonus validation) — representation stays identity-only; validation stays a separate, explicit Template composition step, as today.
- Revisiting the reserved `"secret"` facet's implementation — it already gets the benefit of this change for free (an unexported, unimportable facet pattern can't be spelled by ordinary code, the same way index handles already can't be source-constructed), but reworking the protected-value system itself is out of scope.

## Non-goals

Not deciding, in this release, whether string facets are deprecated or kept indefinitely alongside named-pattern facets — that's a real open question (see the SWOT's "footgun" and "ecosystem-fragmentation" notes: two independently-declared facet patterns with the same name/body are NOT the same facet, unlike two occurrences of a string) worth a dedicated design conversation before committing either way. This release only needs to make named-pattern facets work; whether they eventually replace strings is a follow-up decision.

## Portability note

Both E24-1 and E24-2 add cross-host contract surface beyond what `docs/analysis/cpp-host-porting-readiness.md` already flagged: identity-based facet equality needs the same "same declared value across module loads" guarantee already required for general callable/closure identity (fold into the R17 general-equality contract work from `docs/strategy/cpp-host-release-plan-r16-r22.md`), and the new `display`/`debug_repr`/`pattern_name` contract items need their own spec coverage so a future C++ host has something concrete to conform to, not just "whatever Python's `__repr__` happens to produce."
