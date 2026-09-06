# Proposal: Facets as Named Patterns Instead of Strings — Exploration & SWOT

Status: **Exploration only, not adopted.** Written 2026-08-28 in response to a proposal that Genia's carrier "facets" (`represent`/`representation_match`/`strip_representation`) should be identified by something other than a bare string, because string identity is typo-prone and unenforced at the point of use — refined mid-discussion to specifically mean reusing the existing named-Pattern mechanism (`pattern Name(value) = body`) as the facet identity, rather than inventing a new primitive. Updated after a follow-up inspection pass turned up a real, related gap: named-pattern *values* currently have almost no introspection story, which bears directly on how well this proposal can deliver on its own debuggability promise. Per `docs/process/08-roadmap-ticketing.md`, nothing here is a commitment — it would need to go through roadmap ticketing before any implementation.

## Current state (as implemented today)

Facets are the identity tag on Genia's generic carrier/representation system (R9, Experimental):

- `represent(facet, value)` — `facet` must be a non-empty **string**; wraps `value` in one outer carrier layer.
- `representation_match(facet, value)` — returns `some(carried)` only when the outer facet **string** matches exactly; otherwise `none("representation-mismatch")`. Never searches inner layers.
- `strip_representation(facet, value)` — removes exactly one matching outer layer by the same string check; wrong facet or an unrepresented value is runtime misuse.
- Facets are ordered nested layers (you can `represent` a value multiple times with different facets); order and duplicates participate in equality.
- Represented-value equality is "exact facet plus ordinary carried-value equality" — today, facet comparison is Python string `==`.
- There is deliberately **no facet registry**: any string is a valid facet, chosen ad hoc by the caller. `GENIA_STATE.md` states this explicitly as a design principle, not a gap.
- One string, `"secret"`, is specially reserved: the generic `represent`/`representation_match`/`strip_representation` trio explicitly rejects it, forcing protected/secret values through the dedicated `protected_match`/`secret_get` API instead.
- `json_decode` uses this same mechanism internally — a decoded root is `represent("json", root)` — so `"json"` is a de facto standard-library facet, but it's just a string convention, not enforced identity.
- Implementation: `GeniaRepresented` is a frozen dataclass with a plain `facet: str` field (`src/genia/values.py`); equality falls out of the dataclass's generated `__eq__`, which compares the string.

The complaint is accurate: nothing stops two unrelated pieces of code from colliding on the same facet string by accident, and nothing catches a typo (`representation_match("Json", v)` against a value built with `represent("json", v)` just silently returns `none`, with no signal that the facet name was misspelled).

## What a named pattern actually is (grounding for the proposal)

Worth pinning down precisely, since the proposal leans on it: a named pattern is **not** literally a function, though it behaves like one almost everywhere. `GeniaNamedPattern` (`src/genia/values.py`) is its own distinct runtime type that wraps an ordinary `GeniaFunction` (the matcher):

```python
class GeniaNamedPattern:
    name: str
    matcher: Any        # an ordinary GeniaFunction underneath

    def __call__(self, *args):
        result = self.matcher(*args)
        if not isinstance(result, (GeniaOptionSome, GeniaOptionNone, GeniaOptionErr)):
            raise TypeError(f"named pattern {self.name} returned non-Outcome value")
        return result
```

`_runtime_type_name` gives it a dedicated label, `"named-pattern"`, distinct from `"function"`. It's callable, storable, importable, and passable like any function value — which is exactly what makes it usable as a facet argument with no parser/Core IR changes — but the runtime does not consider it a function, and it enforces one extra constraint (return value must be an Outcome) that ordinary functions don't.

One detail this surfaces directly: **the object already carries its own name internally** (`self.name`), always, unconditionally, at construction time — this is separate from and unrelated to the opt-in `@doc`/`@meta`-style annotation metadata discussed below.

## The introspection gap (found while stress-testing this proposal)

Before leaning further on named patterns as self-describing facet identities, a follow-up check of how much a `GeniaNamedPattern` value can currently be inspected turned up a real gap that the earlier "debuggability is not a net loss" argument was too optimistic about:

- `format_display`/`format_debug` (`src/genia/utf8.py`) have explicit, deliberate branches for every other opaque value type — `<protected>`, `<represented>`, `<declassification-authority>`, `<config-provider>`, `<index-handle>`, `<format>`. **There is no branch for `GeniaNamedPattern`.** `display(X)`/`debug_repr(X)` on a pattern falls through to the generic `str(value)` catch-all, which only happens to show `<pattern X>` because Python's `str()` falls back to `GeniaNamedPattern.__repr__()` by default. That's an accident of the Python host's object model, not a spec'd, intentional rendering the way the others are — nothing in `GENIA_STATE.md`/`GENIA_RULES.md` pins this string down, so a second host implementing `display`/`debug_repr` to the letter of the current spec could legitimately render it differently.
- `help('X')` (`_describe_runtime_name` in `builtins.py`) just checks Python's `callable(value)` and reports "X is a host-backed runtime function in this phase" — it doesn't know or say the value is a named pattern at all.
- There is no accessor at all for a pattern's own name — nothing analogous to `format_template`/`format_tag`, which exist precisely so callers can peek inside an otherwise-opaque `Format` value. `.name` is a Python-only attribute with zero Genia-source visibility.
- `meta(name)`/`doc(name)` are keyed by **the environment binding name string**, not by the value itself (`meta_fn` takes a string and calls `env.get_metadata(name)`). So even the annotation-metadata system doesn't travel with a `GeniaNamedPattern` value once it's passed around, aliased on import, or stored in a data structure detached from its original binding — which is exactly the situation a facet value ends up in once it's threaded through `represent`/`representation_match` calls elsewhere in a program.

Net effect on this proposal: the earlier claim that "debuggability is not a net loss, since represented values already render as `<represented>` either way" is still true for the *carried value*, but it undersold the risk on the *facet identity itself*. Today, if `representation_match` returns a mismatch, there is no reliable, spec'd way to report *which* facet was expected or found — not because facets-as-strings had a better story (a string could always be printed), but because facets-as-patterns would inherit an introspection gap that already exists independent of this proposal, and the proposal would be the first thing to depend on it being fixed.

## Closing the gap: two small, complementary additions

Both of these are small, self-contained, and useful independent of whether the facets proposal moves forward — but they become load-bearing prerequisites if it does.

**1. A deliberate `display`/`debug_repr` rendering for named-pattern values.** Give `format_display`/`format_debug` a real branch for `GeniaNamedPattern` (not an accidental fallthrough), decide and document exactly what it renders — plausibly still `<pattern Name>` — and back it with `spec/eval` coverage asserting the exact string, same discipline as every other opaque-value rendering already gets. This alone would make facet-mismatch debugging no worse than today's string facets for the common "just print it" case.

**2. A first-class `pattern_name(p)` accessor.** Spec'd the same way `format_template`/`format_tag` are: takes a named-pattern value, returns its declared name (as a string), with a deterministic `TypeError` for non-pattern input. This is the part that actually closes the gap for programmatic use — e.g., a facet-mismatch error handler could report `"expected facet " ++ pattern_name(Expected) ++ ", got " ++ pattern_name(Actual)"` without needing the caller to have kept the original binding name string around. Unlike `meta()`, this travels with the *value*, which is the property facet identities specifically need.

A related, smaller idea from the same discussion — giving every annotatable binding (function, assignment, *and* named pattern) a default `@name` metadata entry equal to its own declared name, so `meta('X')` on an undecorated `pattern X(v) = some(v)` would return `{name: "X"}` instead of `{}` — is worth doing too, and is nearly free to implement (`eval_annotations` in `evaluator.py` already receives `target_name` on every call site and currently discards it for defaulting purposes). But it's a weaker fix for the facet-debugging problem specifically, since it's still keyed by binding name via `meta()`, not by the value. Treat it as a nice-to-have alongside `pattern_name(p)`, not a substitute for it.

## What the proposal is (unchanged from the original exploration)

Three readings surfaced; the third is the one worth pursuing.

**Reading A — facet as a brand-new opaque token type.** Introduce a `facet()` constructor that mints a fresh unforgeable identity value, purpose-built for this one job. Solves the typo problem via lexical binding instead of string-spelling, but adds an entirely new primitive/type to the language for a role that turns out to already have a resident: see Reading C.

**Reading B — facet as a structural predicate/matcher (rejected).** The facet argument becomes a validating function (`representation_match(is_json_shaped, value)`) rather than an identity tag. This conflates "which carrier layer is this" with "does the payload look right," collapsing two things `GENIA_STATE.md` deliberately keeps separate ("Representation is separate from value templates"). Not the likely intent, and would blur a distinction the language works to preserve.

**Reading C — facet as a named Pattern (the "or a Pattern" refinement, recommended).** Instead of inventing a new opaque-token type, let the facet argument be an existing named-Pattern value. Sketch:

```genia
pattern Json(value) = some(value)     # an ordinary named pattern, doubles as the facet identity
represent(Json, value)                 # attach it as the outer carrier layer
representation_match(Json, value)      # match by identity, not string content
```

This is a stronger version of Reading A because **it needs no new language primitive at all.** A named pattern is already: a first-class value bound once in the lexical environment; directly callable; importable/exportable across modules like any other binding; and already documented as usable anywhere a callable value is. Passing `Json` as an ordinary argument to `represent(Json, value)` is *already legal Genia today* — no parser change, no new AST/Core IR node, no new runtime type. The only change needed is loosening `represent`'s current `isinstance(facet, str)` runtime check to also accept a `GeniaNamedPattern` value (and updating `representation_match`/`strip_representation`'s comparison from string equality to reference/identity equality on that value) — a small, contained, `builtins.py`-and-`values.py`-level change, not a new subsystem.

It also reads well conceptually: `docs/design/00-patterns.md` (non-authoritative, but philosophically aligned with what shipped) already states "Templates define patterns. Patterns match values." Letting a Pattern also double as a facet identity is a small, coherent extension of that idea — the same named binding that already means "a way to test this value" now also means "a way to tag this value," rather than introducing a third, unrelated concept.

## Exploration notes

- **The "no registry" principle survives.** Named patterns are still ordinary bindings assigned wherever the author likes (in a prelude module for shared/standard facets like `Json`, locally for one-off use) — there's still no central facet namespace, just lexical scoping instead of string-spelling as the collision boundary.
- **The reserved `"secret"` facet gets solved more robustly, for free.** Today `"secret"` is reserved by a runtime string blocklist — nothing stops user code from typing the literal string, it's just rejected when it does. With named-pattern identity, the protected-value system's internal facet pattern simply isn't exported/importable by ordinary code, so it can't be spelled at all, by construction, rather than being spelled and then rejected.
- **Debuggability now has a real answer instead of an assumed one.** See "Closing the gap" above — this used to be a hand-wave ("no worse than today, since represented values already render opaquely"); it's now a concrete two-item prerequisite (deliberate display/debug rendering + `pattern_name(p)` accessor) rather than an assumption.
- **The pattern's own body is inert in this role, which is worth deciding explicitly.** A named pattern declared as a facet (`pattern Json(value) = body`) still has a `body` that must return an Outcome per existing named-pattern rules — but as a facet tag, only its *identity* matters to `represent`/`representation_match`; the body's logic is never invoked by the representation system. That's fine (and keeps representation cleanly separate from validation, per the existing design principle), but it means a facet-pattern's body is somewhat vestigial — document the convention `pattern Json(value) = some(value)` as "the canonical trivial body for a facet-only pattern." The minimal, principle-preserving choice remains: don't thread the carried value through the facet's own matcher — keep representation identity-only, leave validation to explicit separate Template composition as today.
- **Equality/portability needs an explicit answer.** "Exact facet" equality today is string equality — trivially portable to any host (C++ included, per `docs/analysis/cpp-host-porting-readiness.md`/`docs/strategy/cpp-host-release-plan-r16-r22.md`). Named-pattern identity equality means "same facet" has to be defined precisely as "same named-pattern value," which requires every host to agree that loading a shared prelude module produces one singleton binding, not a fresh one per import site. Belongs in the general-equality portability contract work already proposed as R17 — and the new `display`/`debug_repr`/`pattern_name` contract items above should be folded into that same R17-adjacent spec work, since they're the same category of "currently Python-only incidental behavior that needs to become an explicit cross-host contract."
- **A footgun to design against:** two independently-declared named patterns with identical bodies (or even identical names in different modules that don't import each other) are not the same facet under identity comparison — `pattern Json(value) = some(value)` written in two unrelated files never matches across them, unlike two occurrences of the string `"json"`, which are trivially equal today. The mitigation is the same as for any shared identity in the language already: mint the canonical pattern once (e.g. in a prelude module), import it everywhere it's needed, and — now that `pattern_name(p)` is on the table — report both names in the mismatch error rather than the current generic `none("representation-mismatch")`.
- **Migration surface is real but contained.** The feature is explicitly Experimental (`GENIA_STATE.md` marks the whole generic carrier slice Experimental), which is the cheapest possible time to make this kind of change — no stability guarantee is being broken. The JSON boundary's internal `"json"` string facet would migrate to a canonical exported named pattern, and the R9 design/contract docs, cheatsheet examples, and test suite would need coordinated updates — the same discipline `AGENTS.md`'s documentation checklist already requires for any behavior change.

## SWOT

**Strengths**
- Directly fixes the stated problem: a misspelled facet becomes an undefined-name error instead of a silently-wrong `none`.
- Needs no new language primitive, type, syntax, or Core IR node — it reuses the named-Pattern mechanism that already exists. This is a meaningfully smaller and lower-risk change than inventing a dedicated `facet()` token type.
- Strengthens, rather than compromises, the "no registry" design principle.
- Makes the reserved-`"secret"`-facet special case unnecessary as a special case.
- Conceptually unifying: "a Pattern defines both how to test a value and how to tag it" is a small, coherent idea.
- Low blast radius for a breaking change, since the whole feature is still Experimental.
- **New:** the introspection prerequisites this proposal exposed (`pattern_name(p)`, deliberate display/debug rendering) are useful on their own, independent of whether the facets change ships — so the investment isn't wasted even in a partial-adoption scenario.

**Weaknesses**
- Adds an extra step to using a facet: you must declare or import a named pattern before you can `represent`/`match` with it, versus just typing a string literal.
- Two facets that are conceptually "the same" but declared independently become genuinely different and will never match each other — where today they'd accidentally interoperate via the shared string `"json"`. Cuts both ways (see Threats).
- A facet-pattern's `body` is vestigial in this role, which could read as confusing without a documented convention.
- **Revised:** debuggability is *not* a free carry-over from current behavior as originally claimed — it requires the two-item prerequisite work above to actually hold up. Shipping the facets change without that work would leave facet-mismatch debugging strictly worse than today's string facets (a string can always be printed; an un-rendered, un-inspectable pattern identity currently cannot).

**Opportunities**
- A natural moment to also formalize the standard-library facets (`Json` for the JSON boundary) as canonical exported named patterns from the prelude.
- Could unlock better error messages generally — now concretely, via `pattern_name(p)`, rather than as a vague aspiration: a mismatch handler can name both the expected and actual facet.
- Smallest-footprint version of this whole idea: because it reuses existing machinery, it's cheap enough to prototype and evaluate quickly.
- The `display`/`debug_repr`/`pattern_name` work is a reusable building block for anything else in the language that ends up wanting self-describing named-pattern values, not just facets.

**Threats**
- Portability risk: identity-based equality, plus the newly-identified need for spec'd display/debug rendering and a spec'd accessor, together form a larger cross-host contract than plain string facets ever needed. All of it lands in the same portability-gap territory already flagged for a future C++ host (`docs/analysis/cpp-host-porting-readiness.md`) and should be sequenced deliberately against R16–R22.
- Ecosystem-fragmentation risk: independently-authored code that *should* interoperate now needs to explicitly agree on importing the same named pattern, or it silently stops interoperating.
- Scope-creep risk: it would be easy to reach for new syntax or a Core IR node to make pattern-based facets more ergonomic, which would violate the existing "no parser syntax, no Core IR node" invariant. The `pattern_name(p)` accessor and display/debug work should stay ordinary calls/builtin behavior, not syntax.
- Recursive/self-referential misuse: named patterns already disallow recursive definitions; if a facet-pattern's body is ever given real meaning later, that constraint would need to be re-examined for facet-shaped patterns specifically.
- Sequencing risk (new): if the facets change ships ahead of the introspection prerequisites, the interim state is worse than the status quo on debuggability specifically (see Weaknesses). The two should not be decoupled in delivery order.

## Suggested next step

Revised from the original single-track plan: this is now naturally two small pieces of work, and the second should land no later than the first.

1. **Introspection foundation (do this first, or in the same slice):** add a deliberate `display`/`debug_repr` branch for `GeniaNamedPattern` values with spec coverage; add a spec'd `pattern_name(p)` accessor analogous to `format_template`/`format_tag`; optionally add the `@name`-defaults-to-binding-name metadata behavior as a low-cost complementary improvement (`eval_annotations` already has `target_name` in hand for every annotatable binding kind).
2. **Facets-as-patterns (depends on #1 for a debuggability story that isn't a regression):** loosen `represent`'s facet-argument check to accept a `GeniaNamedPattern` value in addition to (or, eventually, instead of) a non-empty string; change `representation_match`/`strip_representation` comparison to identity when the facet is a named pattern; migrate the JSON boundary's internal `"json"` tag to a canonical exported pattern; update the R9 design/contract docs, cheatsheet, and tests together, per `AGENTS.md`'s documentation checklist.

Given the small footprint of both pieces, this could be scoped as one Experimental-slice addition (two small tickets, sequenced) rather than needing its own numbered release — but that's a call for whoever owns the R9 slice, not this document.
