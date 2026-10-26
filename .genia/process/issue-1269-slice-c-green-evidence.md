# #1269 / #1250 — Slice C GREEN evidence (Python)

Process evidence only. Final B9 commit: `539a1f14585fcc9c3ee3fc9bbc5ad05459bfa408` (on top of test-amendment `486caea0`, RED `9a7808be`). Per-case results: `issue-1269-slice-c-green-per-case.json` (143 `model-b-c-*` ids, all `pass` through the real protocol adapter, capability `supported`).

Environment: `uv sync --dev` venv (Python 3.12, ruff 0.15.18 as pinned). C++ untouched.

| Check | Command | Result |
|---|---|---|
| In-process shared | `python -m tools.spec_runner` | `total=1044 passed=1044 failed=0 invalid=0` |
| External Python adapter | `python -m tools.spec_runner --host "<py> -m hosts.python.protocol_adapter" --host-jobs 2 --host-timeout 120` | `total=1044 passed=1026 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0` |
| Exact-18 parity (file unchanged) | `pytest tests/spec/test_python_protocol_adapter_parity_762.py` | 1 passed |
| Capability + per-id adapter PASS | `pytest tests/unit/test_model_b_slice_c_capability_evidence.py tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py -n4` | 157 passed |
| Host-local, optimizer, slices A/B/C, RED harness | `pytest tests/unit/test_model_b_slice_c_*.py tests/unit/test_model_b_optimizer_regression.py tests/unit/test_model_b_slice_{a,b,b_races}.py tests/spec/test_model_b_slice_c_red.py -n4` | 668 passed |
| Fast partition | `pytest -q -m "not slow and not loopback" -n 4` | 7458 passed, 60 skipped |
| Loopback partition | `pytest -q -m "not slow and loopback" -n 4` | 31 passed |
| Docs | `pytest tests/doc -n4` | 397 passed, 35 skipped |
| MCP profile / LLM instructions | `tools/gen_mcp_language_profile.py --check`; `tools/validate_llm_instructions.py` | pass; pass |
| Ruff | `python -m ruff check .` | All checks passed |
| MkDocs | `python -m mkdocs build --strict -d <scratchpad>` | exit 0 |
| MCP SIGINT | 3 repeated runs of the SIGINT lifecycle test; also inside the fast partition | passed every time; no failure observed, so no flake claim made |

No spec, manifest, comparator, runner, oracle or C++ file changed in B9.
Not run here: the full `slow` marker set beyond the files above; final-head GitHub CI (py3.14 matrix, Node jobs) and the pinned C++ host run are merge requirements.
