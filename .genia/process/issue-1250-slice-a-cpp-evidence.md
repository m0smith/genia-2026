# Slice A C++ compatibility evidence

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
