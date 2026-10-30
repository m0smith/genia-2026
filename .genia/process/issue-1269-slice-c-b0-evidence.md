# #1269 / #1250 — Slice C B0 (TEST-only amendments) evidence

Process evidence only. **Not implemented-truth documentation.** B0 changes tests, shared spec cases and the known-gap case list. It changes **no** file under `src/`, `hosts/`, `tools/` or `apps/`, no capability advertisement, no manifest, no comparator or runner, and no C++ file.

## 0. Authority

- RED authority: Codex PASS [6374055115](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6374055115) at `9a7808be18352da7acd41e4b0975851dab9f39ad`.
- Maintainer decision and bounded GREEN authorization: [6378516076](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6378516076) — G1 Option A, A4 retention-aware domain-exact fast path, B0 first, B1–B10 only after an independent Codex B0 PASS.
- B0 base: `0f5d73d2d7dde803d9d511cf6e3321eb830f0f0a` (= RED SHA plus the documentation-only GREEN package; `git diff 9a7808be..0f5d73d` is exactly `.genia/process/issue-1269-slice-c-green-package.md`).

## 1. G1 — six portable shared cases (R7-D9, Option A)

Rule encoded: the CLI entry selector runs `main` automatically only when the **entire** group is plain legacy identifier-header clauses with unique required-arity keys. Any mixed legacy/pattern group, or a fixed/rest same-minimum group, silently preserves the source result, regardless of declaration order. No pattern discovery, guard evaluation, representative record or new diagnostic. Explicit dispatch, REPL, pipe, test and serve are untouched.

All six are `category: cli`, file mode, `argv: [--x]`, `requires: [default_open_functions]`, expect stdout `top` / `42`, empty stderr, exit 0. argv is chosen so that a record that is wrongly selected would run and print.

| id | group | wrong-selection tell |
|---|---|---|
| `model-b-c-main-g1-mixed-main0-plus-pattern` | legacy `main()` + pattern `main(["--x"])` | prints `main0` |
| `model-b-c-main-g1-mixed-main1-plus-pattern` | legacy `main(args)` + pattern `main(["--x"], extra)` (arity 2) | prints `main1` |
| `model-b-c-main-g1-main1-plus-pattern-arity1-legacy-first` | legacy `main(args)` then matching pattern `main(["--x"])` | prints `legacy` or `pattern` |
| `model-b-c-main-g1-main1-plus-pattern-arity1-pattern-first` | matching pattern `main(["--x"])` then legacy `main(args)` | prints `pattern` or `legacy` |
| `model-b-c-main-g1-fixed-plus-rest-same-minimum` | `main(a)` + `main(a, ..r)` | prints `fixed` or `rest` |
| `model-b-c-main-g1-legacy-rest-plus-pattern-arity1` | legacy `main(a, ..r)` + matching pattern `main(["--x"])` | prints `rest` or `pattern` |

Files: `spec/cli/model-b-c-main-g1-*.yaml` plus sibling `.genia` (the existing `model-b-c-main-*` layout).

Baseline at B0 (Python, gate bypassed, observed): five fail with `Error: model-b-not-implemented: declaration evaluation is not available`; `fixed-plus-rest-same-minimum` fails with `Error: Duplicate function definition: main/1`. Both are the documented causes in the GREEN package §1.2. They fail by real mismatch — they are not skipped, not xfail, not `unsupported`-counted.

Bookkeeping that follows from the six cases (and nothing else):

- `tests/spec/test_model_b_slice_c_red.py`: new `SLICE_C_G1_IDS` (6). The 137 approved id tuples (`SLICE_C_GUARD_IDS` 55, `SLICE_C_GATED_IDS` 82) are **byte-for-byte unchanged**; `SLICE_C_RED_CASE_IDS` (=137) is asserted explicitly and the new totals are derived sums: gated 88, all 143. `SLICE_C_REQUIRES` gains six `("default_open_functions",)` rows.
- `spec/known_host_gaps.json`: the existing `default_open_functions` (cpp) entry's `affected_tests` grows 82 → 88 (six ids inserted in sorted order, no reformatting). Reason, tracking issue and removal condition untouched. Nothing is waived: the nine C++ FAIL ids stay outside the gap list.
- `tests/unit/test_model_b_slice_c_capability_evidence.py`: the "unsupported without invoking the host" loop now covers 88 ids.

## 2. A1–A4 boundary review

| ID | Review result | B0 change |
|---|---|---|
| **A1** records/owner identity | The HL-1 tests already pin invariants through boundaries that exist (dispatch results, group identity, alias liveness, arity index, duplicate provenance, state after rejection). They read no field that B2 will rename. | **None.** Exact-field assertions for the record/owner fields are *additions* in B2, once those names exist; no behavioral test is removed. |
| **A2** pure-key entry points | The 34 key tests called `_open_dispatch_key`, `_structural_key` and `OpenClauseRecord` directly. | Routed through three helpers in `tests/unit/model_b_slice_c_support.py` (`dispatch_key`, `structural_key`, `build_clause_record`). Pure indirection: no assertion, parameter, id or expected value changed. A GREEN signature change becomes a one-place edit. |
| **A3** retention location | The retention walker (`_clauses`) lived in the retention test. | Moved to `reachable_case_clauses` in the support module, behavior identical. All three retention assertions (`retained == original`, equal arm keys/ordinals/guards/provenance, later declarations not reordered) are unchanged. GREEN may extend the walker to read the declaration record. |
| **A4** on/off divergence | The existing test only compared on vs. off (a circular oracle). | Added exact tests, below. |

Rewrite participation is **not** relaxed: `test_nil_empty_arm_reaches_the_nth_style_rewrite_today` is untouched and a new `test_a4_rewrite_participation_is_unchanged_so_a_decline_cannot_pass_silently` states that a safe decline needs its own reviewed amendment.

## 3. A4 — exact, non-circular oracle (retained original-case semantics)

`tests/unit/test_model_b_slice_c_optimizer_retention.py` gains `A4_EXACT` (15 ids). Each row pins the **unoptimized** stdout/stderr/exit literally and asserts both the unoptimized and the optimized run equal it.

- In-domain (numeric counter, list `xs`): `in-domain-found`, `-offset`, `-zero-float`, `-empty`, `-short`, `-negative`, `-fractional` — pass today; they keep the fast path honest.
- Out-of-domain, failing today with the real divergence:
  - non-list `xs` (`pick(0, 7)`, `pick(0, "ab")`, `pick(1, 5)`, `pick(2, {a: 1})`): unoptimized raises `No matching case for function pick/2 with arguments [...]` (terminal grouped miss); optimized returns `none("nil")`.
  - non-numeric counter (`pick("a", [1])`, `pick([1], [2])`): unoptimized returns `none("type-error", {source: "-", left: "string"|"list", right: "int"})`; optimized returns `none("nil")`.
- Out-of-domain controls that agree today and must keep agreeing: `ood-bool-counter`, `ood-none-xs`.
- `test_a4_out_of_domain_fallback_preserves_effect_order_and_terminal_grouped_miss`: call-site argument effects print `counter` then `xs`, then the terminal grouped miss; on == off.
- `test_a4_in_domain_calls_in_the_same_program_as_out_of_domain_calls_do_not_interfere`.

## 4. Counts and evidence

Focused set = `tests/unit/test_model_b_slice_c_*.py` + `tests/spec/test_model_b_slice_c_red.py`, per-test ids compared against a clean baseline at `0f5d73d` (`git stash -u`):

| | baseline `0f5d73d` | B0 | delta |
|---|---|---|---|
| failed | 230 | 244 | +14 = 6 G1 cases + 8 A4 divergences |
| passed | 191 | 201 | +10 = 9 in-domain/control A4 rows + 1 participation control |
| total | 421 | 445 | +24 |

- **No baseline test disappeared and no baseline test changed status** (per-id diff of sorted `PASSED/FAILED` lists is empty in both directions).
- `uv run python -m tools.spec_runner` (in-process): `Summary: total=1044 passed=956 failed=88 invalid=0` — the RED `1038 / 956 / 82` plus exactly the six G1 cases (the pass count is unchanged at 956: no existing case changed). The 88 failures are the 82 approved future cases and the six G1 cases, each a real stdout/stderr/exit mismatch.
- `uv run pytest tests/spec tests/doc -m "not slow and not loopback" --deselect tests/spec/test_model_b_slice_c_red.py -n auto`: 611 passed, 35 skipped, 0 failed.
- `uv run ruff check .`: clean.
- Python production code, `src/`, `hosts/`, `tools/`, comparator, runner and the 137 approved YAML/fixtures are unchanged (`git diff 0f5d73d -- src hosts tools apps` is empty).

Frozen-oracle check: `git diff 0f5d73d --name-status -- spec` lists only the 12 added G1 files (6 `.yaml`, 6 `.genia`) and the modified `spec/known_host_gaps.json`.

## 5. What B0 does not do

No production change, no capability transition, no C++ change, no Slice D/E or lifecycle, no new diagnostic, no comparator/runner/oracle edit, no skip/xfail. B1–B10 do not start until an independent Codex PASS on this B0 diff is recorded.
