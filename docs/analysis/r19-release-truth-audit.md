# R19 Skeptical Release Truth Audit (E19-6)

Status: **PASS.** This is the final gate for R19 per
`docs/design/r19-unicode-diagnostic-portability-contract.md` §8 and issue
#825. It re-derives, from `main` as actually merged, whether E19-1 through
E19-5's claims hold — not from memory of intent.

## 1. Re-derivation of what actually merged

Diffed `main` from the last E19-0 commit (`300166f`, PR #819) to this
audit's base commit. R19's entire runtime footprint across E19-1 and E19-3
is exactly three files:

- `src/genia/utf8.py` (E19-1: U3 debug-escaping fix)
- `src/genia/builtins.py` (E19-1: U2 `utf8_decode` fix)
- `src/genia/evaluator.py` (E19-3: pattern-match-miss `format_debug` fix)

No other `src/genia/*.py` file changed. `git diff 300166f..HEAD -- src/genia
spec` contains no occurrence of `Decimal`, `Rational`, or `Float64` —
**confirms no exact-numeric-model behavior was smuggled into R19** (contract
§4 / §9 requirement).

Merged PRs: #826 (E19-1), #827 (E19-2), #828 (E19-3), #829 (E19-4), #830
(E19-5). Each PR's stated behavior-changed/unchanged claims were spot-checked
against its actual diff (via `git log`/`git show`) rather than trusted from
the PR body text alone; no discrepancy found.

## 2. Per-slice claim verification

- **E19-1** (#826): claims U1 evidence-only (no code change to
  `utf8_codepoints`/`utf8_safe_slice_by_codepoint`), U2 `utf8_decode` fix,
  U3 full C0/DEL/C1 escaping. Verified: `git show 37bd536` (the impl commit)
  touches only `utf8_decode_fn`'s except-branch and `_escape_for_debug`,
  matching the claim exactly. `tests/unit/test_r19_unicode_portability.py`
  (30 cases) and 6 `spec/eval/r19-unicode-*.yaml` cases pass on current
  `main`.
- **E19-2** (#827): claims analysis-only, no runtime change. Verified: PR
  diff is exactly one new file, `docs/analysis/r19-diagnostic-mechanical-inventory.md`.
  Re-spot-checked 15 of the 146 listed cases against current `spec/error/*.yaml`
  content — all still match the inventory's recorded first-line text (as
  expected, since E19-2 changed nothing).
- **E19-3** (#828): claims the pattern-match-miss `{args!r}` fix plus 4
  deliberately-updated exact-text cases. Verified: `git show ed15234` shows
  exactly the `_format_args_for_diagnostic` helper and its 3 call sites;
  the 4 spec files' current content matches the new text
  (`error-pattern-miss`: `[99]`, `error-pattern-guard-all-fail`: `[10]`,
  `error-lambda-pattern-miss`: `[[1]]`, `first-on-flow-type-error`:
  `[<flow evolve ready>]`) — re-ran `python -m tools.spec_runner` and all 4
  pass on current `main`.
- **E19-4** (#829): claims no runtime change, two follow-up candidates
  recorded, one documentation flag raised. Verified: PR diff is exactly
  `docs/analysis/r19-host-default-leak-audit.md` + a `GENIA_STATE.md`
  pointer paragraph; no `src/genia` file touched. Independently re-grepped
  `src/genia/*.py` for `str(exc)`/`{exc}`/`repr(` on runtime values beyond
  the E19-1/E19-3 fixes — found the same sites the audit doc already lists,
  no new ones. Confirms the audit's completeness claim.
- **E19-5** (#830): claims `docs/releases/R19.md` added with verified
  runnable examples, roadmap docs updated, no completion claim. Verified:
  `docs/releases/R19.md` exists on `main`, its status line explicitly
  states R19 is not complete pending E19-6, and
  `tests/unit/test_r19_release_doc_examples.py` (3 cases) passes on current
  `main`, confirming its examples remain accurate.

## 3. Independent-host acceptance criterion

Attempted the required reproducibility check directly: read only
`docs/design/r19-unicode-diagnostic-portability-contract.md` and
`docs/releases/R19.md` (not Python source) and confirmed a non-Python host
implementer could derive, byte-for-byte:

- U1's slice-bound normalization rule and its five contract-pinned examples
  (`"abcdef"[1:4]` → `"bcd"`, etc.) — stated in both documents without
  reference to Python semantics.
- U2's boundary-query rules and the exact `utf8_decode` failure message
  shape (`utf8_decode invalid UTF-8 at byte offset N`) — the byte-offset
  fact is portable and independently computable from any correct UTF-8
  decoder, with no CPython-specific text.
- U3's exact escaping table (five short escapes, `\uXXXX` for the three
  named control ranges, literal otherwise) plus two runnable examples
  showing the exact expected output string.
- The one fixed diagnostic case's before/after rendering, demonstrating the
  "use `format_debug`, never host `repr`/`str`" rule concretely.

**Result: PASS.** Nothing in this reproduction required consulting Python
`str` behavior, Python exception wording, or Python source as an
undocumented specification.

## 4. Cross-release invariant re-check

Re-ran the R17/R18/R19-tagged test selection (`pytest -k "r17 or r18 or r19"`):
249 passed, 0 failed, on current `main`. Combined with the full-suite run
below (which includes every R9/R10/R16-tagged case), no regression found in
any preserved invariant:

- R17 (ordered-map/integer): unchanged, no file touched.
- R18 (equality): unchanged, no file touched, no `==`/normalization
  behavior added.
- R9 (JSON boundary): unchanged, `json_decode`'s UTF-8 handling untouched
  by E19-1 (confirmed in E19-1's preflight and by diff).
- R10 (protected-value non-leakage): unchanged; `format_debug`'s protected
  branch precedes the string/control-character branch in both the old and
  new `_escape_for_debug`.
- R16 (adapter-outcome taxonomy): unchanged; `utf8_decode` still raises
  through the same Python-exception-based mechanism as before, not a new
  runner/protocol outcome.

## 5. Full regression and shared-spec evidence (re-run on this audit's base commit)

- `uv run pytest -n auto -q -m "not loopback"`: **4247 passed, 2 failed.**
  The 2 failures are `tests/unit/test_native_test_runner.py::TestNativeTestRunnerFileHandling::test_file_not_readable`
  and `::TestNativeTestRunnerExitCodes::test_exit_2_file_not_readable` —
  both `chmod(0)`-based root-environment failures, present and triaged as
  unrelated to R19 as far back as E19-1's audit (#826), and confirmed again
  here to reproduce identically regardless of any R19 change (root bypasses
  `chmod(0)` in this sandbox). **Not an R19 regression.**
- `uv run pytest -n auto -q -m loopback`: **26 passed, 0 failed.**
- `python -m tools.spec_runner`: **674 passed, 0 failed, 0 invalid.**
- `uv run mkdocs build --strict` (after `tools/stage_docs_for_mkdocs.py`):
  clean build, 0 warnings.
- `uv run ruff check .`: all checks passed.

## 6. Documentation truthfulness re-check

- `GENIA_STATE.md`'s "Unicode and diagnostic portability" section: read in
  full; every sentence traces to a merged commit; no aspirational claim; the
  header names exactly E19-1/E19-2/E19-3/E19-4 (matching what is actually
  implemented — E19-5/E19-6 correctly do not add a "complete" claim to this
  header, since they are docs/audit slices, not implementation slices).
- `docs/releases/R19.md`: confirmed to explicitly state R19 is not complete
  pending this audit.
- `docs/strategy/roadmap/r16-r20.md` and `sequence.md`: confirmed their R19
  status lines list #826–#830 and correctly withhold a "complete" claim.
- `GENIA_RULES.md`/`GENIA_REPL_README.md`/`README.md`: re-confirmed (as in
  E19-5) that no existing statement in these files is contradicted by
  anything R19 implemented.

## 7. Verdict

**PASS.**

R19 (E19-1 through E19-5) is verified, from the actually-merged `main`, to:

- implement exactly the approved U1/U2/U3 Unicode contract and the one
  confirmed diagnostic-portability fix, with no scope creep and no
  exact-numeric-model behavior smuggled in;
- preserve R17/R18/R9/R10/R16 invariants with zero regression;
- pass full regression (modulo the two long-standing, pre-existing,
  independently-reproduced-as-unrelated root-environment failures) and the
  complete shared-spec suite;
- satisfy the independent-host acceptance criterion by direct reproduction
  attempt from the contract and release doc alone;
- keep every durable doc (`GENIA_STATE.md`, `docs/releases/R19.md`, roadmap
  docs) truthful and non-overclaiming.

**R19 is complete as of this audit.** The next roadmap release is R20 —
Open Functions and Extensible Pattern Dispatch, per
`docs/strategy/roadmap/r16-r20.md`. R20's own contract gate has not been
run; nothing in this audit authorizes R20 implementation to begin.

The C++-host prerequisite set (`docs/design/r21-cpp-host-preflight.md`,
R21's dependency list in `docs/strategy/roadmap/sequence.md`) is unchanged
by R19: R21 still depends on R16, R17, R18, completed R19 (now satisfied),
completed R20 (not yet), and the separately gated exact-numeric-model
contract (not yet approved). R19's completion removes one item from that
waiting list; it does not itself change what R21 requires.
