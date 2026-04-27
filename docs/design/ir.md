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

## Field-Level Lowering Invariants

These are the field-level contract details observed from the `spec/ir/` cases and
the Python reference implementation. The docs phase for issue #119 must add these
to `docs/architecture/core-ir-portability.md`.

### IrOptionNone

Three distinct lowering paths, each producing a different `reason` field value:

| Source form | `reason` field | `context` field |
|---|---|---|
| `nil` | `IrLiteral("nil")` | `null` |
| `none` (bare) | `null` | `null` |
| `none("str", ctx)` | `IrQuote(String AST)` → `{kind: Literal, value: str}` | lowered IrMap |
| `none(identifier, ctx)` | `IrQuote(Var AST)` → `{kind: Var, name: identifier}` | lowered IrMap |

Key point: the `reason` argument to `none(...)` is wrapped in `IrQuote` (not lowered
with `lower_node`). This is a deliberate design: the reason is treated as a quoted
label, preserving its syntactic shape rather than evaluating it.

Spec coverage: `spec/ir/option-constructors.yaml`, `spec/ir/none-bare.yaml`

### IrBinary — SLASH operator

Named slash access `lhs/name` lowers as `IrBinary(op=SLASH, left=IrVar(lhs), right=IrVar(name))`.
This is the portable Core IR form. Hosts must not introduce a separate `IrSlashAccess` node.

Spec coverage: `spec/ir/slash-accessor.yaml`, `spec/ir/import-pipeline-stage.yaml`

### IrAssign placement

`IrAssign` is a statement-level node. It appears directly in `IrBlock.exprs` and at
the top level of a program. It is NOT wrapped in `IrExprStmt`. Only expression
statements at block/top level use `IrExprStmt`.

Spec coverage: `spec/ir/block-and-assign.yaml`

### Optional fields

The following fields are omitted from the normalized form when empty or absent:

| Node | Optional field | Present when |
|---|---|---|
| `IrFuncDef` | `rest_param` | varargs function |
| `IrFuncDef` | `docstring` | function has a docstring |
| `IrFuncDef` | `annotations` | function has annotations |
| `IrLambda` | `rest_param` | varargs lambda |
| `IrAssign` | `annotations` | assignment has annotations |
| `IrCaseClause` | `guard` | clause has a guard expression |
| `IrImport` | `alias` | import uses `as` alias |

Spec coverage: `spec/ir/funcdef-varargs.yaml`, `spec/ir/lambda-varargs.yaml`,
`spec/ir/funcdef-annotated.yaml`, `spec/ir/case-patterns.yaml`

### IrPatNone in pattern position

When `none` appears as a pattern (not an expression), it lowers as
`IrPatNone(reason=null, context=null)`. This is distinct from `IrOptionNone`
which is used in expression position.

Spec coverage: `spec/ir/option-patterns.yaml`

### IrQuote — inner syntax normalization

`IrQuote` and `IrQuasiQuote` store the raw parser AST node, not a lowered IR node.
The normalizer serializes quoted inner syntax using a separate `_normalize_quoted_syntax`
path that handles: `String`, `Number`, `Boolean`, `Var`, `ListLiteral`, `MapLiteral`.

Forms not yet handled by the quoted syntax normalizer:
- `Unquote` / `UnquoteSplicing` inside `quasiquote` (known normalization limitation)

Spec coverage: `spec/ir/quote-expr.yaml`, `spec/ir/quasiquote-basic.yaml` (simple
list only; no unquote)

---

## Docs Phase Checklist (issue #119)

The docs phase must update these surfaces:

- `docs/architecture/core-ir-portability.md`:
  - Add field-level detail for `IrOptionNone` (reason variants above)
  - Explicitly document SLASH accessor as `IrBinary(op=SLASH)`
  - Document optional fields for `IrFuncDef`, `IrLambda`, `IrAssign`, `IrCaseClause`, `IrImport`
  - Document `IrAssign` placement rule (not wrapped in `IrExprStmt`)
  - Note quasiquote+unquote normalization as a known limitation
- `GENIA_RULES.md §8.4`:
  - Sharpen `none(...)` lowering description to name the IrQuote wrapping
  - Confirm SLASH accessor lowering form

---

## What This Document Is Not

- Not the frozen contract — that is `docs/architecture/core-ir-portability.md`
- Not the complete node inventory — that is `docs/architecture/core-ir-portability.md`
- Not a spec — the spec is `spec/ir/`
- Not implementation guidance for adding new IR nodes (that requires the full change protocol above)
