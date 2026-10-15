# F2/P2-E code quality & maintainability review (issue #1067, tracker #1229, retirement #1230)

- Gate: docs/process/code-maintainability-review.md (origin/main, #1233).
- Reviewed range: `b674674de946b632b18cc12145f6310e33a83256..858fc6ad` (src, tests, .github) plus adjacent call sites.
- Reviewer: independent read-only subagent (not the implementer). Limitation: read/grep/git only; test results are in the P2-E evidence file.
- **Verdict: PASS WITH NON-BLOCKING FINDINGS. No blocking findings.** Removal simplicity, eligibility, scope-binding and protected-value handling were assessed as sound.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | non-blocking | `_warn` guarded only the `sys.stderr` branch against BrokenPipe/OSError | Fixed: both branches guarded; test `test_a_failing_warning_stream_never_changes_the_program_result` added |
| 2 | non-blocking | Warning sink is R's `stderr` binding, which an entry-declared runtime-owned `stderr` could replace | Documented in `_warn` docstring (host-configured stream; intended) |
| 3 | non-blocking | Event set is unlocked; check-then-add could duplicate a warning under concurrent evaluation | Documented in the helper docstring; harmless (set stays correct) |
| 4 | non-blocking | `fallback_events is None` (hand-made R) returns the value unrecorded | Documented in the helper docstring |
| 5 | non-blocking | Negative tests are vacuous without the fallback; write/reflection/export/eval exclusions | Positive tests exist (pairs, lambda/closure, look-alike, protected, B4 default cases); the seven exclusion operations (write, export, reflection, runtime_owned, local, eval, host_get) are covered by `test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events` (P2-B) |
| 6 | non-blocking | STATE marker and `TRACKING_ISSUE` literal | STATE marker added once in the documentation sync; `#1230` literal kept deliberately (the issue is the retirement record) |
| CI | informational | Strict steps duplicate the default steps with the env var per step, no job-level leak | No action; the full strict run is in the evidence file |
