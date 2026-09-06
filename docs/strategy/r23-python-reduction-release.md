# Release R23 — Python Reference Host Size Reduction

Status: **Proposal — non-authoritative, not adopted.** Styled to match `docs/strategy/release-roadmap.md`. Numbered R23 to avoid colliding with R15 (drafted, not yet merged into the main roadmap file) and the R16–R22 C++ host plan already proposed alongside this (`docs/strategy/cpp-host-release-plan-r16-r22.md`). This release is independent of both — it touches only the Python reference host's internal implementation, not language semantics, Core IR, or any host contract — so it can run in parallel with either, or be resequenced to any open release slot without dependency conflicts.

Source: `docs/analysis/python-code-reduction-review.md`, a 26-item ranked review of `src/genia/*.py` (~18,255 lines) covering pure-Python refactors (deduplication, table-driven dispatch) and a small set of Python-to-Genia-prelude migrations.

## Theme

> Reduce the reference host's Python footprint without changing one observable byte of Genia behavior.

This is explicitly an internal-quality release: no user-visible language feature changes, no new syntax, no Core IR changes, no capability changes. Every item preserves exact current behavior — the review's own confidence ratings (high/medium/low) reflect how mechanically verifiable each change is, not whether it's worth doing.

## Why now

The codebase has never had a dedicated pass for this, and mechanical duplication (three near-identical `server_*_binding.py` files, duplicated import-fallback blocks in `lowering.py`/`interpreter.py`/`callable.py`/`evaluator.py`, four byte-identical validator functions in `retrieval.py`) accumulates cost on every future change to those files — including the C++ porting work in R16–R22, which will need to read and cross-reference this same Python code as the reference behavior to match. A leaner, less duplicated reference implementation is lower-risk to port from, not just smaller.

## Scope

### E23-1 — Mechanical deduplication (highest confidence, do first)

The six highest-confidence, lowest-risk items from the review, all pure Python-to-Python refactors with no behavior change:

- Collapse duplicated import-fallback blocks in `lowering.py`, `interpreter.py`, `callable.py`, and `evaluator.py` (~255 lines combined — items #1 and #5 in the review).
- Table-driven `register_autoload` calls in `builtins.py` (~165 lines — item #2).
- Shared annotation-binding scaffolding across `server_cors_binding.py`/`server_config_binding.py`/`server_route_binding.py` (~100 lines — item #3).
- Deduplicate the four `_valid_*_error` and four `_validate_*_config` functions in `retrieval.py` (~150 lines combined — items #4 and #6).

Estimated: ~670 lines removed. Each item is independently verifiable by running the full test suite (`pytest`) and the shared spec runner (`python -m tools.spec_runner`) before/after with zero diff in observable output.

### E23-2 — Secondary refactors (do after E23-1 lands cleanly)

The remaining pure-Python items from the review, roughly items #7–#22 excluding the Genia-migration items below: `_runtime_type_name` dispatch table, `construct_embed/index/retrieve/rerank` factory, vararg-resolution dedup in `callable.py`, `lifecycle_scope.py`/`lifecycle_plan.py` validator dedup, `take`/`drop` fused-flow builder, `_reject_*_metadata_replacement` trio, `eval_binary` dispatch table, `env.set` six-liner collapse, `GeniaCell`/`GeniaProcess` mixin, `GeniaOptionErr` context helper, `iter_ir_nodes` children method, `diagnostic_error_fn`/`diagnostic_skipped_fn` dedup, scattered string type-checks, `__genia_handles_none__` marker batching, `server_lifecycle.py` tidy-up. Estimated: ~170–200 additional lines. Lower individual impact; batch into one or two PRs rather than 15 separate ones.

`docs/design/00-patterns.md`'s non-authoritative status is a reminder worth generalizing here: skip `ast_nodes.py`'s dataclass-field-repetition item (#9 in the review, ~30 lines) unless a full call-site audit confirms no positional-construction breakage — the review flagged this as the one item where the mechanical savings don't clearly outweigh the risk.

### E23-3 — Python-to-Genia-prelude migrations (separate PRs, separate review)

The four candidates for moving pure-logic Python out of `builtins.py` into the `.genia` prelude: `sum` (→ `math.genia`, ~13 lines), `cli_flag?`/`cli_option`/`cli_option_or` (→ `cli.genia`, ~15 lines), `update_entry_bytes` (→ zip/archive prelude helper, ~8 lines), `entry_json?` (→ zip/archive prelude helper, ~3 lines). Small individually (~39 lines total) but qualitatively different from E23-1/E23-2: each trades a specific diagnostic-message regression (a less precise error on bad input) for fewer Python lines. Each needs its own before/after error-message comparison, not just a test-suite pass, and should be reviewed as a deliberate trade-off per item rather than batched.

## Acceptance criteria

- Full `pytest` suite passes with zero new failures.
- `python -m tools.spec_runner` reports zero regressions across all active categories (`eval`, `ir`, `cli`, `flow`, `error`, `parse`).
- No change to any file under `docs/` describing implemented behavior (this release changes implementation, not documented semantics) — except `GENIA_STATE.md`/`GENIA_RULES.md` wording only if an E23-3 item's error-message change is judged acceptable and needs documenting.
- Line-count reduction is verified by direct `wc -l` diff on touched files, not estimated.
- Each E23-3 item ships with an explicit before/after comparison of its error message(s) on invalid input, reviewed and accepted on its own merits.

## Excluded

- Any change to Core IR, parser grammar, or observable Genia semantics.
- Any change bundled with unrelated feature work (R15, R16–R22, or the R13 follow-ups in `claude/post-r13-configuration-followups.md`).
- Performance optimization — this release is about line count and duplication, not speed.
- The four Genia-migration candidates being treated as equivalent in risk to the pure-Python refactors — they are not, and must not be batched with E23-1/E23-2 in the same PR.

## Non-goals

Explicitly not a code-style or linting pass beyond what the review identified; not a rewrite of any subsystem; not a prerequisite for R16–R22 (helpful to have done first, since it reduces what a C++ port needs to cross-reference, but not blocking).
