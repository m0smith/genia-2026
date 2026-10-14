# F2/P2-E evidence — temporary module compatibility fallback (issue #1067, tracker #1229, retirement #1230)

Stacked on P2-D (PR #1240, head `b674674de946b632b18cc12145f6310e33a83256`) → P2-C (#1239) → P2-B (#1235, red-test SHA
`163f5160f6486cb56fc78211edd0afc261a13c18`). Branch `issue-1067-f2-p2-e-fallback`. Approval:
[D1–D6 with A1–A3](https://github.com/m0smith/genia-2026/issues/1067#issuecomment-6171848719); the approved A2 retirement policy supersedes the
older §16.3.5 / §11.4 "earlier of 60 days / R29" wording. Implementation commit `858fc6ad`, hardening/docs head `3a07a869`
(later commits add only this record). **Do not merge the stack to `main` before P2-F/G.** #1067, #1229, #1230, #1238, #1220, #1221 stay open.

## Baseline reproduced before changes
75 P2-C green, 87 P2-D-assigned green, exactly 13 P2-E red (all `test_B4_*`), 4 other P2-E-assigned cases already green, shared specs 822/822.

## Delivered (Python reference host only; no other host implements it)
- `src/genia/module_fallback.py`: the single named path `temporary_compatibility_fallback_read` (marker `TEMPORARY COMPATIBILITY FALLBACK`), called from exactly one
  place, `Evaluator._resolve_identifier`, after the module chain, runtime, trusted internals and one autoload retry missed. Eligible only when an entry is registered, the
  name is bound in the entry scope's own values, the evaluating unit is a module (R20 contribution clauses count as their declaring module; entry, prelude and runtime never do)
  and strict mode is off.
- Per-execution event set `runtime.fallback_events` of distinct `(canonical module identity, name)` pairs on R; one value-free warning line per new pair (marker once, module,
  name, #1230) on the runtime stderr sink or the process stream; a failing stream is ignored.
- `GENIA_STRICT_MODULE_SCOPE=1` (exact value) read once in `make_global_env`; strict makes the same read the ordinary `Undefined name` `NameError`, records no event, writes no warning.
- Never reached from writes, `doc`/`meta`/`help`, exports, `eval`/`empty_env()`, host `Env.get`, REPL/debugger/discovery inspection, prelude, runtime-owned names or caller-created roots.
- CI: `.github/workflows/ci.yml` strict steps (non-loopback, loopback, semantic specs) on the existing `test` job, env var per step, same selectors as the default steps.

## The 13 formerly red tests (all green)
`test_B4_A_event_measurement_is_deduplicated_and_execution_local` (1), `test_B4_A_fallback_exclusions_preserve_scope_and_emit_no_events` (7: write, export, reflection,
runtime_owned, local, eval, host_get), `test_B4_B_distinct_pairs_warn_independently` (1), `test_B4_B_fallback_warns_once_per_module_name_pair` (3: call, top_level, contribution),
`test_B4_B_strict_switch_is_captured_once_at_runtime_construction` (1). No P2-B test was edited in P2-E. Added `tests/unit/test_f2_p2_e_fallback.py` (15 adversarial cases:
eligibility matrix, pair events and warning content, strict denial and exact-"1" spelling, legacy single root, lambda/closure ownership, MCP-pruned denied names, look-alike
entry value, protected carrier and warning non-leak, inspection never triggering it, runtime stderr sink, failing stream).

## Regression evidence (commands: `uv run pytest -n auto -q -p no:cacheprovider --tb=line -m "not loopback"`, `... -m loopback`, `uv run python -m tools.spec_runner`)
| Run | Default mode | Strict (`GENIA_STRICT_MODULE_SCOPE=1`) |
|---|---|---|
| First full pass, tree `858fc6ad` | 6912 passed, 60 skipped, 0 failed; loopback 31; specs 822/822 | 6912 passed, 60 skipped, 0 failed; loopback 31; specs 822/822 |
| Final tree (`3a07a869` minus evidence file) | **6913 passed, 60 skipped, 0 failed**, 423.9 s; loopback 31 passed; specs **822/822** | **6913 passed, 60 skipped, 0 failed**, 423.3 s; loopback 31 passed; specs **822/822** |
Also: ruff, maintained-code documentation (0 errors, baseline 2822→2821), generated function reference, prelude doc lint, MCP profile `--check`, `tests/doc` (395 passed, 35 skipped) pass.
No failure occurred in any run of this slice, so no retry was needed or hidden. P2-C 75/75 and P2-D 87/87 remain green; P2-E-assigned 17/17 green. Not run: Node/VS Code, official-SDK job, C++.

## Strict-mode evidence and its limits
The strict full suite (non-slow and slow selections as the default run; both loopback partitions; 822 specs) is green, so no repository test reads an entry name from module code through
the fallback; the only fallback-exercising tests are the deliberate ones, which clear the variable (`tests/unit/test_f2_p2_e_fallback.py` autouse fixture; P2-B B4 cases). Strictly,
this covers tests that build registered entry scopes through `make_program_env`/`make_test_env`; the many tests that evaluate in a caller-created single root cannot produce events
(a legacy root registers no entry) and are not evidence of strict coverage. Repository-program coverage (`src/genia/std`, `apps/`, `examples/`) is **not** re-established here: the
earlier #1067 survey found 0 free names in repository modules by static analysis only; the removal PR must supply the executed-program table (#1230 criteria). Known fallback dependents in the
repository today: 0 outside the deliberate tests (strict run green); third-party reliance unknown.

## MCP security verification
`hosts/python/mcp_worker.py` is unchanged (prune via `prepare=` before E registration). The fallback returns only the entry scope's own bindings, so a pruned capability stays
undefined to modules (`test_fallback_never_reaches_denied_capabilities_after_pruning`); an entry value named like a denied builtin is just that value; protected carriers are returned by identity
and neither the event set nor the warning contains the payload; the ten protected-value conformance cases and compat/lifecycle suites pass in both modes.

## Reviews
- Maintainability (`.genia/process/issue-1067-f2-p2-e-maintainability-review.md`): **PASS WITH NON-BLOCKING FINDINGS**; stream-failure guard, docstring limits (sink, unlocked set, hand-made R) addressed.
- Independent truth audit (read-only): **PASS WITH FINDINGS**, no blocking. Its two unverified items (suite-wide strict failures; default-mode stderr assertions) are closed by the full runs above;
  the entry-declared `stderr` redirect and the unlocked set are documented in the code and noted here; STATE margin is 2 words (`tests/doc/test_state_distillation_gates.py`).

## Documentation
`GENIA_STATE.md` §9 (marker once; ~16 trailing "in this phase" clauses removed to stay under the 43,000-word cap, no fact changed), `docs/architecture/python-host-injection.md`. RULES, REPL README, README: no
affected claim. MCP language profile / semantic facts: unaffected. No C++ claim; P2-F/G not claimed.

## #1230 retirement record (A2)
Removal requires the §11.4 evidence criteria; the start of R29 implementation is a hard planning gate; sixty days after warning-enabled P2 first merges to `main` is a mandatory review checkpoint,
never an automatic deletion; if not ready, record a visible blocker or an approved revised decision. No date is invented before the stack merges. Removal verification: zero events across executed
repository programs under strict mode, the P3 deletion list (module, one call, two `Env` attributes, two construction lines), docs updated, issue closed by the removal PR only.

## P2-F handoff
Integration/host conformance and the #1220/#1221 review packages: shared-spec candidates (`doc_help` + `multi_file_eval`) for module-own reflection and frame-first lookup, host-conformance statement
(Python only), the executed repository-program table for #1230, review/closure decisions for #1220 and #1221, #1238 N1/N2 and the metacircular reflection corner, and the documentation/audit slice (P2-G).

## #1226 dogfooding
No meaningful supporting Python/Bash/JS computation beyond routine git, grep, word-count and test invocations this phase (the earlier classifier was not reused). Disposition: **None**; nothing posted to #1226.
