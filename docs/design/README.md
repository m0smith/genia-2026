# Design Notes

These documents describe proposed or exploratory features for Genia's design.
They are NOT authoritative and may not reflect current implementation.

See GENIA_STATE.md for actual behavior.

## Topics

- **00-patterns.md** — Pattern matching as the core model; templates, named patterns, and binding.
- **01-reefinement.md** — Refinement templates for value constraints (e.g., NaturalNumber = n when n >= 0).
- **02-open-shapes.md** — Open shape templates for flexible, partial structure (e.g., {name, email}).
- **03-closed-shapes.md** — Closed shape templates for fixed structure (e.g., Point2(x, y)).
- **04-contract.md** — Contracts as boundary guarantees, referencing patterns for function signatures.
- **05-variant-identity.md** — Variant templates (ADTs) for closed alternatives (e.g., Result = Ok | Err).
- **absence-and-structures.md** — Design note on explicit absence, composable structures, and reducing null.
- **value-templates.md** - Design for value templates for giving structure and meaning to data
