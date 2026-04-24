# Issue #131 Design Note

## 1. Design Summary

- Reuse the existing shared spec runner and its current YAML-based case discovery model, extending it minimally to load and execute `ir` cases in addition to `eval`.
- Add one IR-specific normalization path in the Python host adapter that converts lowered portable IR into a deterministic host-neutral structure before comparison.
- Capture IR exactly at the `parse -> lower` boundary and stop before any host-local optimization or evaluation path.
- Reject host-local optimized nodes in the shared IR path instead of filtering them out, so boundary violations fail loudly and immediately.
- Keep expectations diff-friendly by using a canonical structured representation with stable ordering and explicit portable node-family names, never Python `repr()` output.

## 2. IR Case Representation

Files under `spec/ir/` should use YAML, matching the current shared spec system and avoiding a second fixture format.

Each file should represent exactly one IR case.

Required top-level fields:

- `name`: unique case name; file stem must match
- `category`: must be `ir`
- `input`: mapping
- `expected`: mapping

Required `input` fields:

- `source`: Genia source text to parse and lower

Required `expected` fields:

- `ir`: normalized portable IR representation

Recommended optional top-level fields:

- `notes`: short contract note for maintainers only if needed

No `stdin`, `argv`, eval output fields, parser AST fields, or host-specific metadata should appear in IR cases.

Example shape at the schema level:

```yaml
name: example-name
category: ir
input:
  source: |
    some source
expected:
  ir:
    ...
```

### Expected IR Representation

The expected IR should be a canonical structured YAML mapping/list tree, equivalent to canonical JSON data but written in YAML for readability.

Node representation:

- each IR node is a mapping
- every node has a required `node` field containing the portable node-family name
- child nodes are nested mappings or lists
- optional fields that are absent in the portable contract are omitted rather than represented with Python-specific placeholders
- explicit `null` is allowed only where absence is part of the portable contract, such as the `context` side of `IrOptionNone(..., None, ...)`

Pattern representation follows the same rule:

- each pattern node is a mapping
- every pattern node has a required `node` field containing the portable `IrPat*` family name

Literal and identifier representation:

- literals are represented by portable scalar values or nested portable nodes where required by the contract
- identifiers are represented as plain strings in named fields such as `name`
- operator names use a canonical symbolic or enum string chosen once and used consistently across all cases

Ordering rules:

- program-level node order is preserved
- pipeline `stages` order is preserved
- list item order is preserved
- map entry order is preserved exactly as produced by portable lowering
- case clause order is preserved

This representation is portable, deterministic, and diff-friendly because it is plain structured data with explicit node-family names and no host object formatting.

## 3. IR Normalization Layer

The normalization layer should live in the Python host adapter area, alongside existing host normalization responsibilities.

Recommended module location:

- `hosts/python/ir_normalize.py` as a dedicated module

Alternative acceptable location:

- extend `hosts/python/normalize.py` only if IR normalization remains a clearly separate entrypoint

Inputs:

- the lowered IR tree produced by the current Python reference host at the portable Core IR boundary

Output:

- a canonical nested mapping/list/scalar structure suitable for YAML/JSON equality comparison in shared specs

Normalization guarantees:

- no Python class names beyond the portable contract node-family names
- no memory addresses
- no module-qualified repr output
- stable ordering for all ordered child collections
- only portable Core IR node families and documented portable pattern families

Normalization responsibilities:

- walk the lowered IR tree recursively
- emit canonical field names per node family
- preserve only portable semantic shape
- omit span/debug metadata and any host-local execution details

Host-local optimized node handling:

- preferred behavior is rejection, not filtering
- if a host-local optimized node appears anywhere in the tree being normalized for a shared IR case, normalization must stop and return an explicit failure

That rejection keeps the shared IR path honest. Filtering would hide a portability-boundary violation instead of proving the boundary.

## 4. Runner Integration

The IR category should plug into the existing spec runner as one more supported category, not as a separate tool.

### `spec/manifest.json`

Update the manifest so the shared host contract clearly marks IR as an executable shared category for the Python reference host once implementation lands.

Design intent:

- keep `ir` as an existing shared contract category
- update the host test contract entry for lowering so it matches the normalized portable IR comparison surface used by the runner
- do not broaden the manifest beyond the current Python reference host

### Loader / Discovery

Extend the current YAML loader so it can:

- discover files from `spec/ir/*.yaml`
- validate the IR case schema
- produce a loaded spec object carrying `category="ir"`, `input.source`, and `expected.ir`

This is best done by extending the current generic loader, not by creating a second standalone IR loader unless the existing loader becomes unreasonably contorted.

### Dispatch

Runner dispatch remains category-based:

- `eval` cases keep their current path
- `ir` cases dispatch to the Python host IR execution path

### Python host execution path

For `ir` cases, execution is:

1. parse source
2. lower source to portable Core IR
3. validate that no host-local optimized nodes appear
4. normalize portable IR into the canonical shared representation
5. compare actual normalized IR against expected normalized IR

### Pass Condition

An IR case passes only if:

- parsing and lowering succeed
- no forbidden host-local node appears
- normalized actual IR exactly equals normalized expected IR

### Failure Reporting

Failure output should be field-based like the current runner, but the compared field is `ir`.

Expected reporting shape:

- case header: `FAIL ir <name> (<path>)`
- failing field: `ir`
- readable expected vs actual rendering of the canonical normalized structure

If lowering leaks a forbidden host-local node, failure reporting should make that explicit instead of collapsing it into a generic runtime crash.

## 5. Lowering Pipeline Boundary

IR must be captured at:

`parse -> lower -> STOP`

It must not include:

- optimization
- evaluation
- CLI wrapping
- any host execution strategy after portable lowering

Exact boundary in the current Python reference host design:

- parse source with the existing parser entrypoint
- obtain lowered IR from the existing lowering function that returns the minimal portable Core IR program tree
- do not pass that tree through any optimization function

The design depends on the same lowering boundary already guarded by the current Python implementation and documented in `docs/architecture/core-ir-portability.md`.

This guarantees that shared IR validation is proving the portable Core IR boundary rather than a later host-local execution form.

## 6. Exclusion Of Host-Local Nodes

Enforcement mechanism:

- normalization performs an explicit validation pass over the entire lowered IR tree before or during recursive normalization
- forbidden node families are identified from the documented host-local post-lowering set, starting with `IrListTraversalLoop`

Preferred check location:

- during normalization, because the normalizer is already the last stop before shared comparison

Acceptable alternative:

- a dedicated validation helper immediately before normalization, as long as the shared IR path still fails before any comparison or serialization

Required behavior:

- if a forbidden node appears, the case fails with an explicit boundary error naming the forbidden node
- the error must say that host-local optimized IR appeared in the shared portable IR path

No silent dropping or rewriting of forbidden nodes is allowed.

## 7. Initial Case Set Design

First-wave IR cases should stay narrow and prove only the documented portable contract that already lowers today.

### Literals

Representative cases:

- single literal expression
- list of mixed literal forms including `nil`

What they validate:

- `IrLiteral` shape
- expression-statement wrapping where relevant
- explicit `nil -> IrOptionNone(IrLiteral("nil"), None, ...)` lowering

### Variables

Representative cases:

- bare variable reference
- variable inside a simple binary or call context

What they validate:

- `IrVar` lowering
- identifiers represented host-neutrally

### Function Calls

Representative cases:

- ordinary call with positional args
- call using spread where already implemented

What they validate:

- `IrCall` shape
- ordered argument lowering
- explicit `IrSpread` nodes where documented

### Pipelines

Representative cases:

- simple multi-stage pipeline
- pipeline containing a slash-accessor stage or call-shaped stage already proven locally today

What they validate:

- one explicit `IrPipeline` node
- ordered `stages` list
- no regression to nested call shape

### Blocks / Expression Statements

Representative cases:

- multi-expression block with final expression result shape
- top-level expression statement case

What they validate:

- `IrBlock`
- `IrExprStmt`
- ordered child expression lowering

### Lists / Maps / Spread

Representative cases:

- list literal with spread item
- map literal with documented key forms already normalized by lowering

What they validate:

- `IrList`
- `IrMap`
- `IrSpread`
- stable entry/item ordering

### Option Constructors

Representative cases:

- `some(x)`
- `none(reason, context)`
- `nil`

What they validate:

- explicit `IrOptionSome`
- explicit `IrOptionNone`
- exact portable absence shape for `nil`

### Pattern-Related Lowering

Representative cases:

- case/function with tuple and list patterns
- case/function with `some(...)`, `none(...)`, wildcard, bind, literal, rest, map, or glob patterns already documented and lowering today

What they validate:

- documented `IrPat*` families only
- preserved clause order
- explicit guard lowering where present

### Regression Boundary Case

Representative case:

- a source form known to produce a host-local optimization later in the Python host, but whose shared IR capture must remain portable at the pre-optimization boundary

What it validates:

- host-local optimized nodes do not appear in shared IR output
- the IR spec path stops before optimization

## 8. File / Module Impact

Expected files to add:

- `docs/architecture/issue-131-ir-shared-semantic-spec-design.md`
- `spec/ir/*.yaml`
- `hosts/python/ir_normalize.py` or equivalent dedicated IR normalization module

Expected files to modify:

- `spec/ir/README.md`
- `spec/README.md`
- `spec/manifest.json`
- `tools/spec_runner/README.md`
- `tools/spec_runner/loader.py`
- `tools/spec_runner/executor.py`
- `tools/spec_runner/comparator.py`
- `tools/spec_runner/reporter.py`
- `tools/spec_runner/runner.py` if summary/report flow needs category-aware handling
- `hosts/python/exec_ir.py`
- `hosts/python/adapter.py` only if needed to align the IR execution path with the new normalization contract
- `hosts/python/normalize.py` only if shared host normalization interfaces need a small extension rather than a new module

Scope discipline:

- prefer extending existing runner modules over adding a second runner stack
- keep changes localized to `spec/`, `tools/spec_runner/`, `hosts/python/`, and the required truth-sync docs
- avoid cross-cutting edits in runtime/evaluator code unless implementation later discovers a narrow adapter need

## 9. Doc Sync Plan (Design-Level)

Docs that will need updates after implementation exists:

- `GENIA_STATE.md`
- `README.md`
- `docs/architecture/core-ir-portability.md`
- `tools/spec_runner/README.md`
- `spec/README.md`
- `spec/ir/README.md`

Required doc changes in substance:

- state that the IR category is executable in the shared spec runner once that is true
- keep the distinction explicit between portable lowered IR and host-local optimized IR
- describe the shared comparison surface for IR as normalized portable IR, not Python object output
- remove scaffold-only wording for IR only after runner support and executable cases are present

## 10. Risks & Edge Cases

### Risk: normalization mirrors Python internals

If normalization simply serializes dataclass fields or `repr()` output, shared expectations will leak Python details.

Mitigation:

- define and implement an explicit portable schema
- allow only canonical portable field names and node-family names in normalized output

### Risk: ordering instability

If maps, clauses, or stage lists are normalized inconsistently, specs will flap or hide regressions.

Mitigation:

- preserve source/lowering order for ordered constructs
- define field order once in the normalizer and fixture examples

### Risk: partial lowering paths bypass the boundary

If one execution path uses optimized IR while another uses lowered IR, shared cases become unreliable.

Mitigation:

- make `exec_ir` call the direct parse/lower path only
- keep optimization and eval out of the IR category path entirely

### Risk: future IR node additions break snapshots unexpectedly

If new nodes are added locally without contract updates, IR cases may start failing in confusing ways.

Mitigation:

- make the normalizer reject unknown or non-portable nodes explicitly
- keep the portable contract synchronized through `docs/architecture/core-ir-portability.md` and `spec/manifest.json`

### Risk: forbidden host-local nodes are hidden

If forbidden nodes are filtered out instead of rejected, the shared suite may pass while the boundary is already broken.

Mitigation:

- reject forbidden nodes with explicit failure text
- keep the host-local node list anchored to the documented portability contract

### Risk: runner abstraction grows too much

If IR support introduces category-specific machinery everywhere, the simple runner becomes harder to maintain.

Mitigation:

- keep one generic loader/comparator structure with narrow category branches only where data shape differs
- reuse the existing reporting format

## 11. Non-Goals (Reinforced)

- no IR redesign
- no parser changes
- no eval coupling
- no multi-host support
- no expansion of the portable IR contract

This design exists only to make the current documented contract executable and provable in the Python reference host.

## 12. Design Validation Check

This design matches the Issue #131 spec note exactly:

- it reuses the current shared spec runner instead of creating a new system
- it adds only the minimum IR category extension needed for executable shared cases
- it introduces no new language semantics and no new IR node families
- it keeps Python-specific representations out of shared expectations
- it captures IR at the portable lowering boundary before optimization
- it treats host-local optimized IR as an explicit failure in the shared IR path
- it remains small, composable, and scoped to the current Python reference host only
