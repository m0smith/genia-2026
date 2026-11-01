# Core IR as the Portability Boundary

This document freezes the minimal portable Core IR contract for Genia.

Python is the current full-language reference host and may use additional host-local optimized IR after lowering.
C++ implements its bounded R27 host subset through this same portable boundary;
this does not imply support for every portable node or optional capability.
Those host-local optimized nodes are explicitly outside the shared portability contract.

Implemented external direct execution on the Python host adds no Core IR node. Its architecture
boundary is recorded separately in
[External Process Execution Architecture](external-process-execution.md).

## Layer Separation

Hosts must keep these layers conceptually separate:

1. Surface syntax
2. Host parser AST (host-local shape)
3. Minimal portable Core IR (shared contract)
4. Host-local post-lowering optimized IR/execution strategy (host-local shape)

Only layer 3 is the shared Core IR portability boundary.

## Minimal Portable Core IR (Frozen Contract)

The minimal portable Core IR node families are:

- `IrAnnotation`
- `IrLiteral`
- `IrOptionNone`
- `IrOptionSome`
- `IrVar`
- `IrQuote`
- `IrDelay`
- `IrQuasiQuote`
- `IrUnquote`
- `IrUnquoteSplicing`
- `IrUnary`
- `IrBinary`
- `IrPipeline`
- `IrCall`
- `IrExprStmt`
- `IrBlock`
- `IrList`
- `IrMap`
- `IrSpread`
- `IrCaseClause`
- `IrCase`
- `IrLambda`
- `IrAssign`
- `IrImmutableBind`
- `IrPatternFuncDef`
- `IrClosedFuncDef`
- `IrFuncDef`
- `IrNamedPatternDef`
- `IrImport`
- `IrOpenFuncDef`
- `IrOpenContribution`
- `IrOpenUse`

Pattern families in the portable contract are:

- `IrPatLiteral`
- `IrPatBind`
- `IrPatWildcard`
- `IrPatRest`
- `IrPatTuple`
- `IrPatList`
- `IrPatMap`
- `IrPatGlob`
- `IrPatSome`
- `IrPatNone`
- `IrPatErr`
- `IrPatNamed`

## Lowering Invariants Hosts Must Preserve

Hosts must preserve these lowering invariants:

- pipelines lower as one explicit `IrPipeline(source, stages=[...])` node with ordered stages
- `some(x)` lowers as `IrOptionSome(...)`
- `none(...)` lowers as `IrOptionNone(...)` — see field-level detail below
- `nil` lowers to `IrOptionNone(IrLiteral("nil"), None, ...)`
- bare `none` lowers to `IrOptionNone` with `reason=null` and `context=null`
- `none(reason, ctx)` — the reason argument is wrapped in `IrQuote` (not lowered); it is a quoted label, not an evaluated expression
- dot is the canonical named-access separator: `lhs.name` lowers as `IrBinary(op=SLASH, named_access=true, left=IrVar(lhs), right=IrVar(name))`; legacy `lhs/name` compatibility has been removed — this is narrow named access, not general field-path lookup, and hosts must not introduce a separate access node; ordinary slash/division lowers as `IrBinary(op=SLASH)` without `named_access`
- case/function patterns lower into explicit `IrPat*` pattern families
- `none` in pattern position lowers as `IrPatNone(reason=null, context=null)`, distinct from expression-position `IrOptionNone`
- `IrAssign` is a statement-level node; it appears directly in `IrBlock.exprs` and at the top level of a program — it is not wrapped in `IrExprStmt`
- lowering output uses only the minimal portable Core IR node families listed above
- R20 open functions: `IrOpenFuncDef.clauses`, `IrOpenContribution.clauses` are ordered `IrCaseClause` lists reused verbatim from the existing case-dispatch representation — grouped (`|`) and repeated local clause surface syntax both normalize to the identical clause list, each entry keeping its own original source span; `IrOpenUse` carries only names (`local_name`, `target_module_alias`, `target_name`, `contribution_module_aliases`) and no clause data. See `docs/design/r20-open-functions-syntax-ir-design.md`.
- R21 E21-2 numeric `IrLiteral` payload: a numeric source literal's `IrLiteral.value` is a canonical tagged payload, not a bare host number — `{"kind": "integer", "digits": "<canonical unsigned decimal text>"}` or `{"kind": "decimal", "coefficient": "<canonical text>", "exponent": "<canonical text>"}` (value = coefficient × 10^exponent; zero normalizes to coefficient `"0"`, exponent `"0"`; trailing base-10 zeros are stripped from the magnitude with a matching exponent increase). Every field is a string; no host-native binary float appears in the payload. Source sign stays outside the payload as ordinary `IrUnary(MINUS, ...)`, and `/` stays ordinary `IrBinary(op=SLASH)`. String/bool/nil `IrLiteral` payloads are unchanged. `IrPatLiteral` (case-pattern numeric literals) is unaffected by this ticket. See `docs/design/r21-numeric-source-portable-representation-contract.md` section 4.

### Optional Fields in Normalized Form

The following fields are omitted from the normalized portable IR when empty or absent:

| Node | Optional field | Present when |
|---|---|---|
| `IrFuncDef` | `rest_param` | varargs function |
| `IrFuncDef` | `docstring` | function has a docstring |
| `IrFuncDef` | `annotations` | function has annotations |
| `IrLambda` | `rest_param` | varargs lambda |
| `IrAssign` | `annotations` | assignment has annotations |
| `IrCaseClause` | `guard` | clause has a guard expression |
| `IrImport` | `alias` | import uses `as` alias |
| `IrOpenFuncDef` | `docstring` | reserved; lowering never sets it (open clauses have no docstring position, R20 contract 7.2) |
| `IrOpenFuncDef` | `annotations` | declaration carries `@doc`/`@meta` interface metadata (R20 contract 7.2.1) |

## Executable Validation

This portability contract is executable in the shared Semantic Spec System for
the Python reference host and the supported C++ subset.

Shared IR cases under `spec/ir/` validate:

- parse
- lower
- normalize portable Core IR
- compare against shared expected IR

Contract rule:

- shared IR validation happens before host-local optimization
- host-local optimized nodes are rejected from the shared IR path

The generic runner executes shared source-based parse/lower/eval cases through
Python and C++ host adapters. C++ returns `unsupported` for lowering requests
outside its implemented subset. This does not establish arbitrary serialized-IR
execution or universal portable-node support. The browser-native execution path
remains planned, not an implemented host.


## Strict Error Normalization and Category Boundaries

**As of Phase 2, all errors at the Core IR boundary must be strictly normalized:**

- Error objects must include required fields: category, message, and span (when applicable).
- Error categories are strictly separated: parse, runtime, and CLI errors are distinct and never conflated.
- No host-local or Python-specific error leakage is allowed in normalized output.

---

## Explicitly Not in the Portable Contract
The following are not part of the minimal portable Core IR contract:

- parser AST class names/structures
- evaluator execution strategy (interpreter vs VM vs compiler)
- host runtime representation choices for values/capabilities
- host-local optimization passes and host-local optimized IR nodes
- debug-print formatting of internal host objects

## Host-Local Post-Lowering IR (Current Python Host)

Current known host-local post-lowering optimized node(s):

- `IrListTraversalLoop`

Contract:

- these nodes may appear only after host-local optimization passes
- they must not appear in the minimal lowered Core IR output
- they must preserve the same observable Genia semantics

## Validation and Drift Guard

The Python reference host now includes a lightweight guard:

- lowered programs are validated against the minimal portable Core IR boundary before host-local optimization
- this helps detect accidental host-local IR creep into the portable contract layer

Shared conformance work should continue to assert:

- lowering snapshots/shape
- executable shared IR cases at the portable boundary
- eval behavior after lowering
- CLI/Flow/error contracts at observable boundaries

## Current Status

Implemented today:

- frozen minimal portable Core IR contract (this document)
- Python-host guard to detect host-local node leakage before optimization
- executable shared IR semantic-spec validation in the Python reference host
- bounded C++ parse/lower/eval support and the generic external-host spec runner
- tests that lock the boundary between lowered portable IR and host-local optimized IR

Not implemented today:

- universal execution of every portable node on every host
- Model B closed-function execution and ordinary-function cross-module linking
  (the carriers below are not execution claims)

## Model B declaration carriers (Partial)

Python D1's private module-completion records detach existing syntax while
preserving closure/runtime-value identities. They are not new Core IR carriers
or a serialized artifact format. Source/lowered behavior and the public
ordinary-linking/closed-publication boundary remain unchanged.

LANGUAGE CONTRACT: `GENIA_STATE.md` section 3 governs these additive carriers.
`IrImmutableBind(name, expr, annotations=[], span)` represents a fresh binding.
`IrPatternFuncDef(name, pattern, guard, body, annotations=[], span)` requires one
full `IrPatTuple` header; it has no params/rest_param/docstring alternative.
`IrClosedFuncDef(name, declarations, span)` is one atomic nonempty ordered list
of same-name `IrFuncDef` or `IrPatternFuncDef` records. Nested groups/declarations
in closed bodies, expression-as-pattern carriers, competing header fields and
pattern/guard headers with grouped case bodies are invalid direct IR.

Pattern wire delta: `IrPatErr(reason, context)` and `IrPatNamed(name, inner)`
are declared portable pattern carriers. The normalizer serializes them in every
position, including ordinary lambda and case patterns; programs containing them
no longer raise `unsupported pattern`. `IrPatErr` serializes an absent
context as `null` (as `IrPatNone` does); `IrPatNamed` carries the name only and
resolution stays host semantics. `IrPatSome.context` is the one position-dependent
field: it is serialized only inside `IrPatternFuncDef` headers, and omitted
elsewhere to preserve the legacy wire. Shared cases `model-b-a-pattern-err*`,
`model-b-a-pattern-named` and `model-b-a-legacy-lambda-*` pin both positions.
C++ support for these carriers is not claimed (issue #1250 gap).

Legacy `IrFuncDef` wire fields remain unchanged. New absent annotations and
guards are omitted, and spans are never serialized. Patterns/guards/annotations
retain source provenance internally. Walkers include new declaration children
and existing R20 clauses and annotation values; portable validation rejects
nested host-local optimized nodes.

PYTHON REFERENCE HOST: parsing, lowering, normalization and validation are
implemented. Evaluation executes `IrImmutableBind` with an Env-owned
immutable-write policy (no Core IR change) and `IrPatternFuncDef` as an ordinary default-open
clause (ordered group record, one shape stratum and first-match dispatch); closed declarations
reject with `model-b-not-implemented` before child effects. This adds no linker or
closed-publication state machine. Optimizers preserve the atomic group and retain a rewritten
list-traversal declaration's original grouped case.
C++ new-carrier support is not claimed; issue #1250 owns that follow-up.
`core_ir_version` and R16 protocol stay unchanged; exact `contract_revision`
continues to pin evidence. Syntax support implies no optional execution claim.
