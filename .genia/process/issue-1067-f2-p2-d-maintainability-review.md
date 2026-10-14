# F2/P2-D code quality & maintainability review (issue #1067, tracker #1229)

- Gate: docs/process/code-maintainability-review.md (origin/main, #1233).
- Reviewed range: `cb593207a635fe46ffa26cc10387aee6b2cac442..7b61b42e` (src, hosts, tests, .github baseline) plus adjacent call sites.
- Reviewer: independent read-only subagent (not the implementer). Limitation: read/grep/git only, no test execution; test results are in the P2-D evidence file.
- **Verdict: PASS WITH NON-BLOCKING FINDINGS. No blocking findings.**

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | non-blocking | `discover_annotated_test_units` repeated the "entry-owned or declared runtime-owned" rule inline; the new precondition lived only in a docstring | Fixed: rule lives in `Env.binding_owner` (single, non-re-resolving); discovery uses it. Precondition stays documented (single caller) |
| 2 | non-blocking | `_resolve_identifier` pays `type(value) is FunctionType` + a failed `getattr` on plain builtins | Measured instead of changed: fib(20) 349–380 ms (P2-C) vs 349–368 ms (P2-D), noise level; frozenset-membership alternative tracked in #1238 |
| 3 | non-blocking | `Env._scope_bound` closure cycle relies on cycle GC | Documented in `Env.scope_bound` (fixed) |
| 4 | non-blocking | Magic attribute string shared by builtins and evaluator | Fixed: `Env.SCOPE_BINDER_ATTR` |
| 5 | informational | Value-based marking cannot be spoofed by Genia code or name strings | No action |
| 6 | informational | No P2-E/P3 code in the diff | No action |
| 7 | informational | Baseline ratchet reduction (5 entries) matches the added docstrings | No action |
| t1 | non-blocking nit | Serve wrong-accessor edit should assert the message | Fixed: asserts "Undefined name" |
| t2 | non-blocking | `inc(41)` replacement no longer covers a higher-order callable under `eval` | Not applicable: the metacircular evaluator parses neither lambda nor list syntax (P1 too); recorded in the evidence file |

Review follow-up fixes were committed after the review (`binding_owner`, constant, doc note, test nit); the fixes are covered by the final full regression recorded in the evidence file.
