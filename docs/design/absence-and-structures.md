Here’s a compact design note for Genia.

## Genia design note: absence, composable structures, and reducing null

Genia already has two ingredients that make this direction promising: `some(...)` / `none(...)` are part of the current runtime surface, and map patterns are already partial-by-default in pattern matching. That means the language already has one foot in “explicit absence + shape-based matching,” even before full structures/types arrive. ([GitHub][1])

### 1. North star

When Genia gets structures, they should be:

* immutable
* composable at runtime
* matchable by shape
* able to distinguish **field omitted** from **field present but empty**

That aligns with Genia’s current philosophy: minimal, pattern-matching-first, immutable by default, and wary of hidden behavior. ([GitHub][2])

### 2. Core principle

Do not make raw `null` the semantic center of the language.

Instead, treat absence as explicit and structured.

The key distinction to preserve is:

* **omitted** — this field is not part of the current shape
* **empty/none** — this field is part of the shape, but has no value
* **value** — this field is present with a value

Those are not the same thing, and collapsing them causes trouble later.

### 3. Why this is a good direction

Languages that avoid raw nullable-by-default values usually end up with clearer semantics. Rust’s `Option` is explicitly either `Some` or `None`, and Gleam likewise uses `Option` instead of nullable values. ([Rust Documentation][3])

For Genia, this would buy you:

* cleaner pipelines
* matching on actual structure instead of placeholder checks
* safer composition of partial data
* fewer “is this null because it is missing, cleared, unknown, or not loaded yet?” bugs

In other words, less sludge, more shape.

### 4. Important warning: absence is not one thing

This is the trap.

If Genia replaces `null` with one universal `none`, it may still lose meaning. Real systems often need to distinguish:

* omitted
* explicitly cleared
* unknown
* not yet loaded
* not applicable
* invalid/error

GraphQL is a good cautionary example: omitted input and explicit `null` are treated differently because partial updates need that distinction. ([GitHub][4])

So the goal should not be “one sacred absence value rules them all.”

The goal should be “raw null is not the default; absence is modeled intentionally.”

### 5. Proposed semantic model for Genia

Without committing to syntax yet, I’d suggest thinking in these states:

* **omitted** — field not present in this structure
* **none** — field present, but empty / no value
* **value(x)** — field present with value
* **deferred** — field exists conceptually, but is not computed/loaded yet
* **error(e)** — field resolution failed

You do not necessarily need all five in the first version of structures. But you should reserve conceptual room for them.

My recommendation for the first practical model:

* **omitted**
* **none**
* **value**

Then treat `deferred` and `error` as higher-level wrappers or conventions later.

### 6. Structural composition rule to preserve

A future Genia structure system should be able to tell the difference between:

```genia
{name: "Ana"}
```

and

```genia
{name: "Ana", nickname: none}
```

Those should not mean the same thing.

The first says: nickname is not part of this shape.
The second says: nickname is part of this shape, and explicitly empty.

That distinction becomes critical for merges, updates, persistence, and pipeline routing.

### 7. Pattern matching implications

Pattern matching should eventually be able to express at least these ideas:

* require field presence
* match field value
* tolerate additional fields
* distinguish omitted from present-with-none

Genia already treats map patterns as partial-by-default, so this direction fits the existing language shape rather than fighting it. ([GitHub][5])

### 8. Merge/composition questions Genia will need to answer later

This is where elegant ideas either become a language or a support ticket.

When structures become composable, Genia will need explicit rules for:

* later value overwrites earlier value?
* does `none` overwrite a concrete value?
* does omitted mean “leave unchanged” or “remove”?
* how are conflicts resolved?
* how do partial updates compose?

These should be specified deliberately, not left to “whatever the host map merge did on Tuesday.”

### 9. Interop boundary rule

Even if Genia reduces or eliminates core-language `null`, host systems will still have it:

* SQL `NULL`
* JSON `null`
* Python `None`
* blank CSV fields

So Genia should define a boundary translation policy:

* external null-like things may enter through interop
* Genia normalizes them into explicit internal states
* internal semantics do not rely on raw host null as a core concept

That keeps the host bridge small and the language semantics honest, which also matches the project’s current philosophy. ([GitHub][2])

### 10. Main drawbacks

This direction is good, but it is not free.

Costs:

* more concepts to learn than a single `null`
* more subtle matching rules
* more design pressure on merge/update semantics
* more interop translation work
* temptation to overbuild a grand unified absence cathedral too early

So the risk is not that the idea is bad. The risk is building too much of it before structures themselves are grounded.

### 11. Recommendation for Genia

I would adopt this as a design principle now:

> Future Genia structures should be immutable, composable, and shape-matchable, with a semantic distinction between omitted fields and present-but-empty fields.

And I would avoid committing yet to:

* full type syntax
* final record syntax
* advanced deferred/error field semantics
* automatic magical propagation rules

That keeps the idea sharp without letting it sprawl.

### 12. Practical short version

My recommendation is:

* **yes** to reducing null in the core language
* **yes** to composable immutable structures
* **yes** to pattern matching on present structure
* **yes** to distinguishing omitted vs present-with-none
* **no** to collapsing every kind of absence into one value
* **no** to deciding syntax before the semantics are nailed down

That feels very Genia to me: small core, explicit semantics, shape over sludge.

## Promotion Criteria

This design moves to:
- GENIA_RULES.md when semantics are locked
- GENIA_STATE.md when implemented and tested

[1]: https://raw.githubusercontent.com/m0smith/genia-2026/main/README.md "raw.githubusercontent.com"
[2]: https://raw.githubusercontent.com/m0smith/genia-2026/main/AGENTS.md "raw.githubusercontent.com"
[3]: https://doc.rust-lang.org/std/option/?utm_source=chatgpt.com "std::option - Rust"
[4]: https://github.com/graphql-dotnet/graphql-dotnet/issues/3308?utm_source=chatgpt.com "Distinguishing between explicit null and omitted value ..."
[5]: https://raw.githubusercontent.com/m0smith/genia-2026/main/GENIA_RULES.md "raw.githubusercontent.com"
