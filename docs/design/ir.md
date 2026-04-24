# Intermediate Representation (IR) and Optimization Contract

*This document describes current implemented behavior. See [`docs/architecture/core-ir-portability.md`](../architecture/core-ir-portability.md) for the frozen portable contract and `GENIA_STATE.md` for final authority.*

---

## Purpose

Core IR is the portability boundary between the parser and the evaluator/optimizer.

- Lets future hosts consume a shared, host-neutral representation of Genia programs
- Keeps source syntax details out of evaluation logic
- Keeps evaluation strategy details out of the language contract
- Defines what every host must produce from lowering and what every host must preserve through optimization

---

## Layer Model

Hosts must keep four layers conceptually separate:

```
1. Surface syntax          (host-local)
2. Parser AST              (host-local)
3. Core IR                 (shared portability boundary)
4. Host-local optimized IR (host-local, post-lowering only)
```

- Only layer 3 crosses host boundaries
- Layers 1, 2, and 4 are implementation details of each host
- Python is the only implemented host today

Core IR is **not directly executed**. In the current Python reference host, the evaluator walks the lowered IR to produce observable behavior. The IR is a structural representation, not a runtime instruction set.

---

## What IR Represents

Core IR is a small, explicit, host-neutral representation of Genia programs produced by the AST→IR lowering pass.

Key structural choices made explicit in lowered form:

- Pipelines are explicit ordered stage lists, not nested call nodes
- Option constructors are explicit nodes, not generic call nodes
- Patterns are explicit node families, not generic AST nodes

The complete frozen list of node and pattern families is in [`docs/architecture/core-ir-portability.md`](../architecture/core-ir-portability.md). That frozen minimal portable list is the contract; this document does not duplicate it.

The Python reference host validates lowered programs against the minimal portable Core IR contract before any host-local optimization.

---

## Semantic Firewall: What Must Not Change

Observable program behavior must be identical before and after any host-local optimization pass.

Lowering invariants every host must preserve:

- `pipeline` → `IrPipeline(source, stages=[...])` — never nested calls
- `some(x)` → `IrOptionSome(...)` — never a generic call node
- `none(...)` → `IrOptionNone(...)` — never a generic call node
- `nil` → `IrOptionNone(IrLiteral("nil"), None, ...)`
- case/function patterns → explicit `IrPat*` families
- lowered output uses only the minimal portable node families

These invariants are the semantic firewall. Any change that violates them breaks the portability contract.

The shared `spec/ir/` cases are the executable validation of this firewall. They run parse → lower → normalize → compare against expected portable IR, and they reject host-local optimized nodes at the shared boundary.

---

## Performance Zone: What May Change

The following are host-local implementation details. They must not appear at the shared portability boundary, but may be changed freely within a host:

- Host-local post-lowering optimization passes (example: `IrListTraversalLoop`)
- Evaluator/execution strategy — interpreter, VM, compiler, JIT
- Runtime value representation
- Parser AST class names and structures
- Debug-print formatting of internal host objects

These may be added, changed, or removed within a host without affecting the shared contract, provided observable semantics are preserved.

---

## Validation Boundary

The Python reference host inserts an explicit validation point between lowering and host-local optimization:

1. Parse source → produce host AST
2. Lower AST → produce minimal portable Core IR
3. **Validate** — reject any host-local IR node at this boundary
4. Apply host-local optimization passes (may introduce host-local nodes)
5. Evaluate

The shared `spec/ir/` cases assert correctness at steps 2–3. They do not test step 4.

IR stability status: **Partial** — the contract is frozen and validated in the Python reference host; no second host implementation exists yet.

---

## Change Protocol

To change the Core IR contract — adding, removing, or altering a node family or a lowering invariant — all of the following must be updated together:

1. `GENIA_STATE.md` (final authority — update first)
2. `GENIA_RULES.md`
3. `docs/architecture/core-ir-portability.md`
4. Affected `spec/ir/` cases
5. Implementation in `src/genia/`

No doc may claim more than `GENIA_STATE.md`. A change that is not reflected in all five surfaces is incomplete.

---

## What This Document Is Not

- Not the frozen contract — that is `docs/architecture/core-ir-portability.md`
- Not the complete node inventory — that is `docs/architecture/core-ir-portability.md`
- Not a spec — the spec is `spec/ir/`
- Not implementation guidance for adding new IR nodes (that requires the full change protocol above)
