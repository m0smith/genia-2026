# Issue #131 Spec Note

## 1. Change Name

IR shared semantic-spec proof for Python reference host

## 2. Purpose

This change makes the documented Core IR portability boundary executable and testable in the shared Semantic Spec System.

Python is proving the existing shared contract. Python is not defining new language behavior in this change.

## 3. Scope Lock

### In Scope

- executable shared IR cases under `spec/ir/`
- portable lowering-shape assertions for the minimal Core IR
- manifest/runner category contract for IR cases
- verification that portable lowering excludes host-local optimized nodes
- doc wording needed to keep `GENIA_STATE.md`, `README.md`, spec docs, and related contract docs truthful

### Out of Scope

- Core IR redesign
- parser redesign
- eval redesign
- non-Python hosts
- generic multi-host runner
- including host-local optimized nodes in shared IR expectations
- snapshotting host parser ASTs or Python-specific internal objects

## 4. Source Of Truth

Repo truth order for this change:

1. `AGENTS.md`
2. `GENIA_STATE.md`
3. `GENIA_RULES.md`
4. `GENIA_REPL_README.md`
5. `README.md`
6. `spec/*`
7. `docs/host-interop/*`
8. `docs/architecture/*`

`GENIA_STATE.md` is the final authority.

If any existing doc, spec note, runner README, or host doc conflicts with `GENIA_STATE.md`, `GENIA_STATE.md` wins.

## 5. Current Implemented Reality

Implemented reality in the repository today:

- Python is the only implemented host and the reference host.
- Shared semantic-spec categories are `parse`, `ir`, `eval`, `cli`, `flow`, and `error`.
- `eval` and `ir` are currently executable in the shared spec runner.
- IR stability is `Partial`, not `Stable`.
- The minimal portable Core IR contract is already documented in `docs/architecture/core-ir-portability.md`.
- Host-local optimized nodes such as `IrListTraversalLoop` are explicitly outside the portable contract.

This spec note does not change that implemented reality by itself. It defines the contract that later Design and Implementation steps must make executable.

## 6. Portable IR Contract To Prove

Shared IR semantic-spec cases must assert the portable lowering contract already documented for the current Python reference host.

Required assertions:

- lowering output must use only the minimal portable Core IR node families listed in `docs/architecture/core-ir-portability.md`
- pattern lowering must use only the documented `IrPat*` families
- pipelines lower as one explicit `IrPipeline(source, stages=[...])` node with ordered stages
- `some(x)` lowers as `IrOptionSome(...)`
- `none(...)` lowers as `IrOptionNone(...)`
- `nil` lowers to `IrOptionNone(IrLiteral("nil"), None, ...)`
- host-local optimized nodes must not appear in the portable lowered IR output
- shared IR expectations must not depend on Python-specific object/class formatting

This contract is about lowering shape at the portable Core IR boundary only.

## 7. Case Format Requirements

An IR shared spec case must supply:

- source input as Genia source text
- any case metadata needed to identify the case and category
- one portable IR expectation for the lowered result at the minimal Core IR boundary

For the IR category, the runner must compare:

- the host-produced lowered portable IR representation
- against the case’s expected portable IR representation

The expected representation is not chosen by this spec step. The Design step must select it. Whatever representation is chosen must satisfy all of these constraints:

- portable
- deterministic
- host-neutral
- readable in diffs
- excludes host object noise

The representation may be full normalized IR text, structured normalized JSON, or another normalized portable form only if it satisfies those constraints.

Normalization requirements:

- normalization must remove Python-specific leakage such as class repr formatting, memory identity, module-qualified object names, and other host object noise
- normalization must preserve the observable portable lowering shape
- normalization must preserve ordered structure where order is part of the contract, including pipeline stage order and list/map entry order where lowering preserves it
- normalization must preserve explicit portable node-family names or an exact host-neutral equivalent that still proves the same contract

Pass/fail contract:

- pass: the lowered output matches the expected portable normalized representation exactly
- fail: any portable node-family mismatch, ordering mismatch, explicit constructor mismatch, unexpected host-local node, or host-specific leakage in the compared output

IR shared cases must not compare Python parser ASTs, Python dataclass reprs, or other Python-internal structures.

## 8. Category Boundary

IR shared specs assert lowering-shape conformance at the portable Core IR boundary.

They do not assert:

- eval results
- CLI behavior
- parser AST structure

Any host-local post-lowering optimization is outside the IR shared contract for this issue.

## 9. Required Case Inventory

Minimum first-wave IR coverage must include executable shared cases for the lowering shapes that are already documented and already lower today.

Required first-wave coverage:

- literals
- variable references
- calls
- pipelines
- blocks and expression statements where relevant to portable lowering shape
- lists, maps, and spread where already implemented
- option constructors: `some`, `none`, `nil`
- case lowering with pattern families that are already documented

Include function definitions, assignments, and imports only when both of these are true:

- they are part of the documented portable Core IR contract
- they already lower today in the Python reference host

The first wave must include at least one regression case proving exclusion of host-local optimized nodes from the portable lowered IR output.

## 10. Failure Modes The Spec Must Catch

The IR shared spec contract must catch at least these failures:

- portable lowering includes `IrListTraversalLoop`
- pipeline lowering regresses into nested calls instead of `IrPipeline`
- option constructors stop lowering to explicit `IrOptionSome` or `IrOptionNone`
- `nil` stops lowering to explicit `IrOptionNone(IrLiteral("nil"), None, ...)`
- pattern lowering stops using documented `IrPat*` families
- IR output depends on Python repr/class names
- docs imply broader IR shared coverage than the runner actually executes

## 11. Truthfulness Requirements

Docs may say IR shared semantic-spec coverage is active because the runner executes IR cases in the Python reference host today.

Docs must not imply:

- multi-host IR execution exists
- host-local optimized IR is part of the shared portable contract

Examples in docs must remain labeled consistently with the repository documentation truth model.

## 12. Acceptance Criteria

This issue is complete only when all of the following are true:

- `spec/ir/` contains executable shared IR cases
- the Python reference host executes the IR category in the shared spec runner
- IR expectations validate the documented minimal portable Core IR contract
- host-local optimized nodes are excluded from shared IR expectations
- `GENIA_STATE.md`, `README.md`, `docs/architecture/core-ir-portability.md`, and `tools/spec_runner/README.md` remain aligned

## 13. Non-Goals / Do Not Drift

Do not drift beyond the current documented contract:

- do not add new Core IR nodes
- do not broaden the contract beyond what docs already define
- do not collapse the boundary between portable IR and host-local optimized IR
- do not claim multi-host support exists
- do not redesign error normalization unless needed only to state the IR boundary truthfully

## 14. Handoff To Design

The Design step must decide exactly:

- exact spec case file schema for IR
- exact normalized representation used for IR expectations
- exact runner plumbing and manifest changes
- exact doc files that need wording changes
- exact tests needed for regression protection
