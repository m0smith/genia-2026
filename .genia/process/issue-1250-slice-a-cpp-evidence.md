# Slice A C++ compatibility evidence

## Initial implementation evidence (2026-10-16)

Unmodified source HEAD: 87204407543f2b175c6b185bdc7e625edeb19251.
Adapter contract_revision: 9ab0d3a323c9add045d47db1f476aead96af1e77. Ancestor compatibility evidence, not current pinned conformance.

Existing R16 fetch_capabilities/execute_spec_via_host; timeout 10 seconds; parser/ast_lowering requirements unchanged.

- model-b-a-annotated-immutable.yaml: UNSUPPORTED
- model-b-a-calls.yaml: PASS
- model-b-a-closed-grouped.yaml: UNSUPPORTED
- model-b-a-closed-run.yaml: UNSUPPORTED
- model-b-a-closed.yaml: UNSUPPORTED
- model-b-a-guard-identifier.yaml: UNSUPPORTED
- model-b-a-guard-pattern.yaml: UNSUPPORTED
- model-b-a-immutable.yaml: UNSUPPORTED
- model-b-a-legacy-rest.yaml: UNSUPPORTED
- model-b-a-legacy-some-context.yaml: UNSUPPORTED
- model-b-a-ordinary-independent.yaml: PASS
- model-b-a-pattern-list.yaml: UNSUPPORTED
- model-b-a-pattern-literal.yaml: UNSUPPORTED
- model-b-a-pattern-map.yaml: UNSUPPORTED
- model-b-a-pattern-some-context.yaml: UNSUPPORTED
- model-b-a-pattern-string-body.yaml: UNSUPPORTED
- model-b-a-pattern-tuple.yaml: UNSUPPORTED
- model-b-a-split.yaml: UNSUPPORTED
- model-b-a-guard-arrow.yaml: UNSUPPORTED
- model-b-a-guard-grouped.yaml: UNSUPPORTED
- model-b-a-index.yaml: UNSUPPORTED
- model-b-a-missing-body.yaml: UNSUPPORTED
- model-b-a-missing-init.yaml: UNSUPPORTED
- model-b-a-mixed-reverse.yaml: UNSUPPORTED
- model-b-a-mixed.yaml: UNSUPPORTED
- model-b-a-nested.yaml: UNSUPPORTED
- model-b-a-pattern-arrow.yaml: UNSUPPORTED
- model-b-a-pattern-grouped.yaml: UNSUPPORTED
- model-b-a-target.yaml: UNSUPPORTED

Counts: {'unsupported': 27, 'pass': 2}

UNSUPPORTED is the adapter’s explicit outside-scope response, not PASS. #1250 owns the bounded C++ parser/lowering follow-up. No executable capability claim changed.

## Closeout recheck (2026-10-19)

Unmodified available C++ source HEAD: `bb7c7474001f18e2e27fd94b7be9e9b725ba3473`.
Existing binary: `build/genia-adapter`, SHA-256
`609d9807e5753574bd6e518ea4cad77c782b824ee45f9d154788e2853daf2df3`.
Its advertised contract revision is `6402e668ae85a1e7efe94b3ac3d51f233b730ca4`,
a resolvable ancestor of this branch, not the current contract. No C++ source
or capability claim was changed. Binary provenance beyond the available source
checkout and advertised revision is not independently certified.

The same existing R16 `fetch_capabilities` / `execute_spec_via_host` APIs ran all
38 `spec/*/model-b-a-*.yaml` cases, timeout 10 seconds per request. These are
selected compatibility/gap observations, not a full C++ suite or current pinned
conformance. Outcomes below include the original 29 plus 9 closeout cases.

- `spec/eval/model-b-a-recursion-in-list.yaml`: **UNSUPPORTED**
- `spec/eval/model-b-a-recursion-in-map.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-annotated-immutable.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-calls.yaml`: **PASS**
- `spec/ir/model-b-a-closed-grouped.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-closed-run.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-closed.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-guard-identifier.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-guard-pattern.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-immutable.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-legacy-dotted-assignment.yaml`: **PASS**
- `spec/ir/model-b-a-legacy-dotted-function-arrow.yaml`: **PASS**
- `spec/ir/model-b-a-legacy-dotted-function-block.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-legacy-dotted-function.yaml`: **PASS**
- `spec/ir/model-b-a-legacy-rest.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-legacy-some-context.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-ordinary-independent.yaml`: **PASS**
- `spec/ir/model-b-a-pattern-list.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-pattern-literal.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-pattern-map.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-pattern-some-context.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-pattern-string-body.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-pattern-tuple.yaml`: **UNSUPPORTED**
- `spec/ir/model-b-a-split.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-dotted-closed-target.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-dotted-guard-target.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-dotted-pattern-target.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-guard-arrow.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-guard-grouped.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-index.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-missing-body.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-missing-init.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-mixed-reverse.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-mixed.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-nested.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-pattern-arrow.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-pattern-grouped.yaml`: **UNSUPPORTED**
- `spec/parse/model-b-a-target.yaml`: **UNSUPPORTED**

Total: **5 PASS / 33 UNSUPPORTED / 0 failure-class outcomes**. The original 29
remain 2 PASS / 27 UNSUPPORTED; the 9 new cases are 3 PASS / 6 UNSUPPORTED.
The new unsupported cases include ordinary dotted block headers, both collection
recursion eval cases, and all three new restricted-target parse diagnostics.
UNSUPPORTED negative diagnostics are not PASS. Python's observations do not
manufacture C++ parity.

N9 disposition: `spec/known_host_gaps.json` accepts optional capabilities only;
required parser/ast_lowering syntax gaps are recorded in this exact case ledger
and `docs/host-interop/HOST_CAPABILITY_MATRIX.md`, under #1250. No required
capability is weakened, no new optional syntax escape hatch is added, and a
green optional-capability parity gate does not certify these cases. Owner:
#1250 integration owner plus C++ implementer. Removal requires bounded C++
implementation and passing affected shared cases at a current contract revision.
Until then the required-syntax boundary remains explicitly unmet; this report
settles where to report it, not whether the host has implemented it.
