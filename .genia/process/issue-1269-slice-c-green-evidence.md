# #1269 / #1250 — Slice C GREEN evidence (Python)

Process evidence only (no behavior claims beyond the tests cited). Per-case results: `issue-1269-slice-c-green-per-case.json` (143 `model-b-c-*` ids, all `pass` through the real protocol adapter, capability `supported`).

## Tested source
- Code SHA the tests ran on: `539a1f14585fcc9c3ee3fc9bbc5ad05459bfa408` (B9). Later evidence commits `44217d49` and this update change only `.genia/process/*` (`git diff 539a1f1 44217d4 --stat`: the evidence markdown and per-case JSON); the second fast partition and the A4 run below executed at `44217d49`.
- Lineage: RED `9a7808be` → B0–B10 → `486caea0` (three-file amendment, independent PASS) → `539a1f14` (B9) → `44217d49` (evidence). PR #1270 head verified equal to `44217d49` before this update.
- Authorized branch: `claude/slice-c-test-amendment-review-a2h7fj`; PR head branch `claude/nice-brahmagupta-1e17ws`. Updates are plain fast-forwards; nothing was force-pushed.
- Environment: `uv sync --dev` virtualenv, Python 3.12, ruff 0.15.18 (pinned). All results below are **author-run**; none is independently reviewed yet.

## Results (author-run)
| Area | Command | Exit | Result |
|---|---|---|---|
| Shared in-process | `python -m tools.spec_runner` | 0 | `total=1044 passed=1044 failed=0 invalid=0` |
| Python external adapter | `python -m tools.spec_runner --host "<py> -m hosts.python.protocol_adapter" --host-jobs 2 --host-timeout 120` | 0 | `total=1044 passed=1026 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0` |
| Exact-18 parity (assertion file unchanged since RED: `git diff 9a7808be HEAD -- tests/spec/test_python_protocol_adapter_parity_762.py` empty) | `pytest tests/spec/test_python_protocol_adapter_parity_762.py` | 0 | 1 passed, 530.97 s standalone |
| Full `tests/spec` | `pytest tests/spec -v -n 4 --durations=15` | 0 | 442 passed in 530.06 s; parity test alone 513.27 s |
| Capability / C0 / per-id adapter | `pytest tests/unit/test_model_b_slice_c_capability_evidence.py tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py -n4` | 0 | 157 passed |
| Host-local Model B, optimizer, slices A/B/C, RED harness | `pytest tests/unit/test_model_b_slice_c_*.py tests/unit/test_model_b_optimizer_regression.py tests/unit/test_model_b_slice_{a,b,b_races}.py tests/spec/test_model_b_slice_c_red.py -n4` | 0 | 668 passed |
| Fast partition, run 1 | `pytest -q -m "not slow and not loopback" -n 4` | 0 | 7458 passed, 60 skipped in 383.38 s |
| Fast partition, run 2 (at `44217d49`) | same | 0 | 7458 passed, 60 skipped in 340.89 s |
| Loopback partition | `pytest -q -m "not slow and loopback" -n 4` | 0 | 31 passed |
| Docs | `pytest tests/doc -n4` | 0 | 397 passed, 35 skipped |
| MCP profile | `python tools/gen_mcp_language_profile.py --check` | 0 | pass |
| LLM instructions | `python tools/validate_llm_instructions.py` | 0 | pass |
| Ruff | `python -m ruff check .` (0.15.18) | 0 | All checks passed |
| Strict MkDocs | `python -m mkdocs build --strict -d <scratchpad>` | 0 (captured `$?` of mkdocs itself) | built |

## Per-case and capability evidence
- `default_open_functions` is advertised `supported`; `_VOCABULARY_ONLY_CAPABILITIES` is empty (`hosts/python/protocol_adapter.py`). All 143 `model-b-c-*` cases (55 guards, 88 gated incl. six G1) return `kind == pass` through the real adapter (`test_every_slice_c_case_passes_through_the_real_protocol_adapter[...]`, 143 parametrized tests, plus the committed JSON). The only `unsupported` results of the external run are the 18 Python-host-only fixture/debug cases. `unsupported` is never counted as a pass.

## Optimizer on/off (HL-8, A3/A4)
`pytest tests/unit/test_model_b_slice_c_optimizer_retention.py -v`: 36 passed. The 15 A4 controls (`in-domain-*` x7, `ood-*` x8) each assert the literal unoptimized oracle and identical optimized stdout/stderr/exit; additional tests assert effect order with terminal grouped miss, mixed in/out-of-domain calls, and unchanged rewrite participation (a decline cannot pass silently). Retention tests keep original arms, keys, ordinals, guards and provenance.

## MCP SIGINT investigation
The lifecycle SIGINT test (`test_r28_mcp_stdio_lifecycle.py`, parametrized SIGTERM/SIGINT) did not fail in either complete fast-partition run, in the full `tests/spec` context, or in 13 repeated isolated runs (3 plus 10, the 10 executed while the second fast partition ran at `-n 4` to add load). Observed failure frequency in this session: 0 of 16 executions (fast partition x2, full `tests/spec`, 13 isolated runs). I could not reproduce the earlier failure, so I make no root-cause claim and changed no code or tests for it; the earlier failure report is not something I observed directly and remains unexplained. No skip, xfail or waiver was added.

## `tests/spec` stall
The earlier apparent stall near 97-99% was the exact-18 parity test (about 513 s, continuously spawning `hosts.python.protocol_adapter` processes), i.e. slow execution, not a deadlock; the full directory completes with 442 passed.

## Frozen-spec continuity
Since RED (`9a7808be`) the only changes under `spec/**/model-b-c-*` and `tests/spec` are: six approved G1 cases (12 files, B0), the two approved CLI print-and-echo oracle amendments, and the matching RED-harness inventory update. The failure-class identity amendment is in `tests/unit/test_model_b_slice_c_identity.py`. The parity assertion, comparator, runner and manifest are unchanged by B9.

## Documentation synchronization
STATE, RULES, REPL README, README, semantic facts, MCP profile/golden, host capability matrix, release roadmap and `docs/architecture/core-ir-portability.md` were audited against the tests above; the doc, MCP-profile and LLM-instruction checks pass. They describe default-open ordinary functions and pattern/guard headers as implemented on the Python host; closed `=:` functions, cross-module linking (Slice D/E) and C++ support are stated as not implemented.

## Not run / remaining
- Independent Codex GREEN review (required; nothing above is independently verified).
- Final-head GitHub CI (py3.14 matrix, Node jobs) and the pinned C++ host conformance run; genia-cpp #53-#57 (CPP-D1..D5) remain open; `known_host_gaps.json` still lists `default_open_functions` for C++ as unsupported. The #1251 foundation audit is separate.
- Slow-marked tests outside `tests/spec` and the Model B files; no whole-repo slow run was made.
