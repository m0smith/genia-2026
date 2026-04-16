# Core IR as the Portability Boundary

This document freezes the minimal portable Core IR contract for Genia.

Python is the current reference host and may use additional host-local optimized IR after lowering.
Those host-local optimized nodes are explicitly outside the shared portability contract.

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
- `IrFuncDef`
- `IrImport`

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

## Lowering Invariants Hosts Must Preserve

Hosts must preserve these lowering invariants:

- pipelines lower as one explicit `IrPipeline(source, stages=[...])` node with ordered stages
- `some(x)` lowers as `IrOptionSome(...)`
- `none(...)` lowers as `IrOptionNone(...)`
- `nil` lowers to `IrOptionNone(IrLiteral("nil"), None, ...)`
- case/function patterns lower into explicit `IrPat*` pattern families
- lowering output uses only the minimal portable Core IR node families listed above

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
- eval behavior after lowering
- CLI/Flow/error contracts at observable boundaries

## Current Status

Implemented today:

- frozen minimal portable Core IR contract (this document)
- Python-host guard to detect host-local node leakage before optimization
- tests that lock the boundary between lowered portable IR and host-local optimized IR

Not implemented today:

- second host implementation
- generic multi-host spec runner implementation
