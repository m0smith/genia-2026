# Exact regression selections

First four selections ran on authority main09804b; final selection ran on correction checkout. UV_CACHE_DIR=/workspace/.cache/uv; UV_PROJECT_ENVIRONMENT=/workspace/genia-2026/.venv; PYTHONPATH selects each checkout src. Host/stress/generator/doc commands are in closeout-report.md.

```sh
uv run --no-sync pytest -q tests/doc tests/unit/test_model_b* tests/spec/test_model_b* tests/unit/test_r20* tests/spec/test_r20* tests/unit/test_modules_phase1.py tests/unit/test_f2_p3_module_read_isolation.py tests/unit/test_repl_env_characterization.py tests/unit/test_cells.py tests/unit/test_processes.py

uv run --no-sync pytest -q -n 4 tests/unit/test_r25_concurrency_fixture.py tests/unit/test_concurrency_examples.py tests/unit/test_invariant_concurrency.py tests/unit/test_r28_mcp_language_profile.py tests/unit/test_doc_style_sync.py tests/unit/test_cheatsheet_*.py tests/unit/test_examples.py

uv run --no-sync pytest -q -n 4 tests/unit/test_flow_phase1.py tests/unit/test_flow_adjacent_186.py tests/unit/test_pipeline_operator.py tests/unit/test_outcome_native_tests.py tests/unit/test_cli_args.py tests/unit/test_cli_pipe_mode.py tests/unit/test_r28_mcp_language_outcomes.py tests/unit/test_r28_mcp_language_flow.py tests/unit/test_r28_mcp_portability.py

uv run --no-sync pytest -q -n 4 tests/unit/test_ir.py tests/unit/test_ir_shared_spec.py tests/unit/test_ir_shared_spec_contract.py tests/unit/test_r21_tagged_numeric_ir_854.py tests/unit/test_execution_process_core_ir_regression.py tests/spec/test_spec_ir_runner_blackbox.py

uv run --no-sync pytest -q tests/doc/test_semantic_doc_sync.py tests/doc/test_state_anchors_and_registry_sync.py tests/doc/test_portability_contract_sync.py
```

Hosted full CI is separate evidence. Original test settings/skip markers were unchanged. Full external-host/stress requests used10s. Stress additionally needs the authority checkout on PYTHONPATH. Container script/scratch Dockerfile preserve actual executed commands with unchanged product sources and a mounted public CA bundle. Per-case ledgers reconstruct canonical discovery with explicit nonpass records; counts match producer evidence. They are not another host execution or an artifact ZIP-byte validation.
