# #1261 Slice B RED evidence

Base: `b809a9ce` (pre-flight) on merged Slice A (`cf38403`). Baseline before RED: `python -m tools.spec_runner` = 874 passed / 0 failed / 0 invalid.

Added (tests/specs/vocabulary only; no production code):

- 24 shared `spec/eval/model-b-b-*.yaml` cases and 2 `spec/cli/model-b-b-repl-*.yaml` cases.
  25 require the new optional capability `immutable_bindings`; `model-b-b-parameter-remains-mutable` is a no-capability regression guard and passes today by design.
- `tests/unit/test_model_b_slice_b.py`: Env prepare/commit API, racing and reentrant commits, bypass writers (set/assign/set_host/define_function/metadata/metacircular/import/named pattern), direct Core IR, N5 manifest over new declaration nodes, N8 effect staging.
- `spec/manifest.json`: `immutable_bindings` added to `optional_capabilities` (vocabulary needed for cases to load). The Python adapter auto-claims manifest names, so this claim is **provisional until GREEN**: it is only a true claim once the cases below pass.
- `spec/known_host_gaps.json`: honest C++ optional-capability gap `immutable_bindings`, tracking `m0smith/genia-cpp#50`, exact affected cases. No parity claim.

Expected-failing evidence:

- Shared subset (scratch filter over `discover_specs` for `model-b-b-*`): `selected=26 passed=1 failed=25 invalid=0`. 23 fail with `Error: model-b-not-implemented: declaration evaluation is not available`; the rest fail because declaration evaluation is absent (empty stdout).
- `uv run pytest tests/unit/test_model_b_slice_b.py`: 15 failed, 4 passed (legacy/preserved behavior), 5 errors (fixture needs the unimplemented API).

Diagnostics chosen for the specs (no contract-fixed text exists): `Cannot assign to immutable binding: <n>` (ordinary `=`), `Cannot rebind immutable binding: <n>` (other writers), `Cannot declare immutable binding <n>: name is already bound in this scope`, `Cannot declare immutable binding <n>: name is reserved by the runtime`.
