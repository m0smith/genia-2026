# Documentation sync — issue #676 R13 validated-pipeline proving case

## Summary

Synchronized implemented truth from E13-5 to E13-6 and documented the verified offline proving composition. The release page now includes the exact observed runnable output. No semantic rule changed.

## Files updated

- `GENIA_STATE.md`: authoritative E13-6 composition, failure, non-leakage, portability, and Python fixture boundary.
- `README.md`: runnable proving-case guidance and exclusions.
- `docs/releases/R13.md` and `docs/releases/README.md`: E13-6 delivered status and exact runnable example/output.
- `docs/design/r13-configuration-resolution-contract.md`: implemented-through status and remaining gate.
- `docs/design/composability-matrix.md`: records that E13-6 proves the existing provider/Outcome/Template composition without changing it.
- `docs/strategy/release-roadmap.md` and `docs/strategy/r13-configuration-resolution-ergonomics.md`: planning/status synchronization.
- `docs/ai/LLM_CONTRACT.md` and `AGENTS.md`: cross-tool release-boundary synchronization.

`GENIA_RULES.md` and `GENIA_REPL_README.md` were reviewed and need no update because E13-6 adds no semantics or mode behavior. No `docs/book/` directory exists. Cheatsheets and host-interop docs need no change because no API/call shape or host capability changed.

## Key wording

- APIs remain Experimental.
- Python remains the only implemented host and shared/multi-host conformance remains Partial.
- The credential is public only as `<protected>`; matching host-boundary tests reveal/audit/attempt exactly once.
- E13-6 adds no API, runtime semantics, network, retry/fallback, ambient provider, or lifecycle behavior.
- E13-7 and E13-8 remain gated.

## Validation

- Ran the exact example and copied its observed output to `docs/releases/R13.md`.
- `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q tests/doc/test_semantic_doc_sync.py tests/doc/test_portability_contract_sync.py tests/doc/test_composability_matrix_sync.py tests/unit/test_host_boundary_labels.py tests/unit/test_no_overclaim_language.py tests/unit/test_r13_validated_pipeline_proving_case_676.py tests/spec/test_r13_validated_pipeline_shared_specs_676.py`
- Result: 524 passed.

## Risks/ambiguities

None. Changes are minimal status/truth synchronization around tested composition artifacts.
