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
- **r11-ai-composition-contract.md** — approved R11 contract; E11-1 through E11-8 are complete, with E11-8 limited to the final truth audit and distillation.
- **r12-retrieval-grounding-contract.md** — approved R12 contract; E12-1 through E12-9 are complete, with E12-9 limited to the final truth audit and distillation.
- **r13-configuration-resolution-contract.md** — approved R13 contract; E13-1 through E13-8 are complete, with E13-8 limited to the final truth audit and distillation.
- **r14-composable-lifecycle-contract.md** — approved R14 contract; E14-1 through E14-15 are complete, with E14-14 documentation-only and E14-15 limited to the final truth audit and distillation.
- **r15-validated-value-modeling-contract.md** — E15-0 R15 contract, approved and fully implemented through E15-9.
- **r16-multi-host-conformance-infrastructure-contract.md** — E16-0 R16 contract (issue #757): adapter protocol/envelope, stdout/stderr channel ownership, failure taxonomy, capability/revision/evidence model, and external-host repository boundary. Approved; E16-1 through E16-8 not started.
- **execution-concepts.md** — Proposed separation of file/source, module, annotation, lifecycle, unit test, and execution mode; dangerous merges to avoid.
- **composability-matrix.md** — Non-authoritative matrix of implemented composition boundaries and explicit later-release constraints.
- **facet-identity-named-patterns-swot.md** — Exploration/SWOT (not adopted): replacing string-identified carrier facets with named-Pattern identity, plus a related `GeniaNamedPattern` introspection gap.
