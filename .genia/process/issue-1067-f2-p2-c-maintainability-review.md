# F2/P2-C code quality & maintainability review (issue #1067, tracker #1229)

- Gate: docs/process/code-maintainability-review.md (from origin/main, #1233).
- Reviewed range: `163f5160f6486cb56fc78211edd0afc261a13c18..8e40588968549105b1678586f824cb9d0c94c8ca` (src, hosts, tests, .github baseline) plus adjacent call sites.
- Reviewer: independent read-only subagent (not the implementer). Limitation: it could not run pytest; conclusions are from reading the diff. Implementer's test runs are recorded in the P2-C evidence file.
- **Verdict: PASS WITH NON-BLOCKING FINDINGS. No blocking findings.**

| ID | Severity | Location | Finding | Disposition |
|---|---|---|---|---|
| N1 | non-blocking | `environment.py` `_entry_route`/`binding_scope` | Routing helper records `entry_declared_runtime_owned` before the bind succeeds; failed attempts stay recorded | Documented as an attempt record in both docstrings (fixed). Exactness is for P2-D, which consumes the list (tracked in #1238) |
| N2 | non-blocking | `environment.py` `is_runtime_owned`/`_runtime_name_available` | Duplicated bound/autoload checks; linear autoload scan per top-level E operation; first call parses every autoload-target prelude file | Tracked follow-up: #1238: share one helper and cache autoload-name set; cost unmeasured, cached parse is once per process |
| N3 | non-blocking | `environment.py` `inspection_globals_scope` | Accessor returns the unit scope once E is registered, so REPL `:env` and debugger globals output changes in P2-C | Not a defect: required by contract 16.6.1 and P2-B tests B10; consumers untouched. Recorded in the P2-C evidence as P2-B-mandated accessor semantics |
| N4 | informational | `Env` class defaults | Immutable defaults, no shared mutable state | Covered by `test_ordinary_frames_share_no_registration_state` |
| N5 | non-blocking | `tests/fixtures/r28_mcp_conformance.py` | Fixture relies on `genia.make_program_env` call style | Comment pinning the call style added (fixed) |
| N6 | non-blocking | `builtins.py` `make_program_env` | Docstring lacked a Raises clause | Added (fixed) |

Red-test instrument edits (serve `Evaluator.eval_program` wrap, valid pipe stage, ignore trusted prelude autoload `internal_access=True`) were independently judged to preserve and not weaken the original assertions; the repaired cases were also re-run against the P1 tree and fail there with "program still evaluated in shared R=E". Existing-test seam edits were judged non-vacuous.

Durable follow-up record: https://github.com/m0smith/genia-2026/issues/1238 (N1, N2, N3 checklist; parent #1067, tracker #1229).
