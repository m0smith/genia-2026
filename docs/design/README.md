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
- **ir.md** — Core IR and optimization contract: what the IR represents, what must not change (semantics), and what may change (performance).
- **r9-value-template-representation-contract.md** — approved R9 design contract; E9-1 through E9-7 are implemented and E9-8 completed the release truth audit.
- **r10-configuration-protected-value-contract.md** — approved R10 configuration and protected-value contract; E10-1 through E10-8 are complete.
- **r11-ai-composition-contract.md** — approved R11 contract; E11-1 through E11-4 are implemented and later slices remain planned.
- **execution-concepts.md** — Proposed separation of file/source, module, annotation, lifecycle, unit test, and execution mode; dangerous merges to avoid.
- **composability-matrix.md** — Non-authoritative matrix of implemented composition boundaries and explicit later-release constraints.
