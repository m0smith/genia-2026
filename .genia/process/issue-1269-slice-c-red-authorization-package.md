# #1269 / #1250 — Model B Slice C RED authorization package (R1–R5, G1 recorded)

**Status: DOCUMENTATION ONLY. No failing test, spec, manifest, adapter, known-gap, production or implemented-truth file is added or changed by this package. RED is NOT started and NOT authorized by this document. GREEN is NOT authorized. G1 is recorded, NOT approved.**

| Item | Value |
| --- | --- |
| Tracking issue | [#1269](https://github.com/m0smith/genia-2026/issues/1269) (child of [#1250](https://github.com/m0smith/genia-2026/issues/1250)) |
| Package base | `main` at `79c073b4…` (`79c073b`, merge of #1272; includes merged C0 = PR #1273) |
| Accepted pre-flight | PR #1270, revision 4 `585f6aa229a55bbd3e3110c975dcaaa94a61e93e`; this package is revision 5 of the same branch (companion edits in `issue-1269-slice-c-preflight.md` and `issue-1269-slice-c-red-test-plan.md`) |
| Authority | `GENIA_STATE.md` (final); contract #1255 / design #1259; integration authorization [6327837022](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6327837022); C0 acceptance [#1273 6333148622](https://github.com/m0smith/genia-2026/pull/1273#issuecomment-6333148622); independent reviews [6327597044](https://github.com/m0smith/genia-2026/pull/1270#issuecomment-6327597044) and [#1273 6333124626](https://github.com/m0smith/genia-2026/pull/1273#issuecomment-6333124626) |
| Not this package | C++ work, #1271 / #1272 Application Lifecycle, RED/GREEN code, `GENIA_STATE.md` / `GENIA_RULES.md` / `GENIA_REPL_README.md` / `README.md` / semantic-facts / MCP-profile edits |

**Evidence labels (used throughout):** **exec** = executed in this session against the stated head, output observed; **rehearsal** = executed in a throw-away worktree (never committed) to observe *capability and runner mechanics only* — it is **not** a RED result and uses no Slice C case; **read** = from source or docs; **inferred** = reasoned, not run. **No Slice C RED case exists yet, so no RED outcome below is observed; every RED/GREEN expectation is `inferred`** (with the mechanism it relies on labelled exec/rehearsal/read).

Implemented behavior = what `GENIA_STATE.md` records on `main`. Approved future behavior = contract/design/maintainer decisions D1, D3, D3b, D4 (numeric keys), D5, D8 in the pre-flight. Inferred = the outcome tables here. Unresolved = §8.

---

## 0. What was refreshed and verified

- `origin/main` is `79c073b`. The commits since the pre-flight base (`6d50a36`) are: C0 (#1273: `0e63dc1`, plus the maintainer's two documentation-gate repair commits `e9246ed`/`ac7c270`/`2ccd8c8`) and #1271/#1272 (application-lifecycle contract/design **drafts** and a pre-flight under `docs/design/*-DRAFT.md` and `.genia/process/`). **exec:** `git diff --stat 6d50a36 origin/main` touches no `src/`, `spec/`, `tools/spec_runner`, root authority file or Slice C document. No intervening change to the Slice C plan or implementation. #1271/#1272 stay out of Slice C.
- **C0 mechanism verified on merged `main` (read):** `hosts/python/protocol_adapter.py` defines `_VOCABULARY_ONLY_CAPABILITIES: frozenset[str] = frozenset()`; `_python_claimed_capabilities` raises `ValueError` for names outside `known_capabilities()` and reports staged names `unsupported` ahead of the `partial`/`supported` branches. The 11 C0 tests (`tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py`) pass (exec, §2.2). The independent C0 review (#1273 `6333124626`) is PASS; the integration owner accepted and merged.
- The accepted pre-flight architecture (D1, numeric keys, D3, D3b, D5, D8, U2 boundary, C-MAIN, C0 design) is **not reopened**. This package adds R1–R5 detail, records G1, and corrects directly relevant stale facts (§8.4).

---

## 1. R-conditions at a glance

| Condition | Disposition in this package | Section |
| --- | --- | --- |
| R1 command / CI matrix | Done: 12 execution paths, observed baselines (exec), inferred RED/GREEN counts derived from an exact case-ID set, capability-mechanics **rehearsal** | §2 |
| R2 exact non-slow harness and case set | Done: harness specified; **127 shared case IDs** (51 G, 1 ungated R, 75 gated RG) plus host-local inventory; oracle status per case (D 73 / A 41 / L 13) and one blocked case (B) reserved, not created | §3 |
| R3 anti-false-GREEN | Done: assertions GA-1…GA-12, RED→GREEN capability sequence | §4 |
| R4 diagnostic paths | Done per the directed disposition; grounded command-/file-mode examples (exec); one **design-text clarification required before RED** (§5.5) | §5 |
| R5 manifest / docs sync | Done: manifest edit, override timing, test impact (rehearsal), intentional phase-guard changes, GREEN removal | §6 |
| G1 | **Recorded only; pending maintainer approval before GREEN**; GREEN tests identified | §7 |
| Unresolved | O-1 … O-6 (gating consistency of the D5 breaking changes, ungated cases vs the C++ evidence path, R4 design text, plan source defects, one blocked oracle, one wrong program) | §8 |

---

## 2. R1 — RED/GREEN execution matrix

### 2.1 Observed baselines (exec; `main@79c073b`, clean, `.venv` from `uv sync`)

| # | Path | Exact command | Observed baseline |
| --- | --- | --- | --- |
| E1 | In-process shared runner (`ci.yml`, `regression.yml`, canary, self-hosted smoke use this) | `uv run python -m tools.spec_runner` | `Summary: total=901 passed=901 failed=0 invalid=0`, exit 0 |
| E2 | External Python protocol adapter | `uv run python -m tools.spec_runner --verbose --host-jobs 8 --host "<venv>/bin/python -m hosts.python.protocol_adapter" --host-timeout 30 --evidence py_evidence.json` | `total=901 passed=883 failed=0 unsupported=18 protocol_error=0 crash=0 timeout=0 invalid=0`, exit 0; evidence `counts` `{pass 883, fail 0, unsupported 18, protocol_error 0, crash 0, timeout 0, invalid 0}`, 35 capabilities |
| E3 | Existing Python protocol parity test (`regression.yml` job *Full Python protocol conformance*) | `uv run pytest -q -m full_conformance tests/spec/test_python_protocol_adapter_parity_762.py` | `1 passed in 527.73s`, exit 0 (asserts `unsupported == 18`, `passed == total − 18`, all failure classes 0, exit 0) |
| E4 | Host parity gate (Python side, C++ unavailable) | `uv run python -m tools.spec_runner.host_parity_gate --python-evidence py_evidence.json --cpp-unavailable-reason "no genia-cpp checkout in this session" --known-gaps spec/known_host_gaps.json` | `C++ PARITY NOT EVALUATED …`, `OK`, exit 0. **Limit:** the C++ comparison (`docker`/`genia-cpp` build in `host-parity.yml`) was not run here |
| E5 | Focused suites | `uv run pytest -q -p no:cacheprovider tests/spec/test_r20_open_functions_shared_specs.py tests/unit/test_python_protocol_adapter_762.py tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py tests/unit/test_spec_runner_capabilities.py tests/unit/test_host_parity_gate.py tests/unit/test_model_b_slice_a.py tests/unit/test_model_b_slice_b.py tests/unit/test_model_b_optimizer_regression.py` | `216 passed` |
| E6 | `tests/doc` | `uv run pytest -q -p no:cacheprovider tests/doc -n 4` | `397 passed, 35 skipped`, exit 0 |

The Slice B-era "874 passed" figure in the plan is stale; **901** is the measured count.

### 2.2 Runner semantics this matrix relies on (read, with exec corroboration)

- **In-process** (`runner.py::_run_in_process` → `executor.execute_spec` → `comparator.compare_spec`): `requires` is validated by the loader but **never consulted**; the buckets are `passed / failed / invalid` only; exit 1 iff `failed` or `invalid` is non-zero. **Rehearsal:** with `default_open_functions` staged `unsupported`, a gated throw-away case was *executed* and reported `FAIL` (`total=903 passed=901 failed=2 invalid=0`, exit 1). So the in-process run cannot report a gated case `unsupported`, and a RED head fails it.
- **External host** (`_run_via_host` → `host_executor.execute_spec_via_host`): a case whose `requires` are not all `supported` in the host's claimed map is `unsupported` **before the adapter is invoked for that case** (the `capabilities` request itself is still made once). Exit is non-zero iff `failed`, `protocol_error`, `crash`, `timeout` or `invalid` is non-zero; **`unsupported` never affects the exit code**.
- **Pytest** `-m "not slow and not loopback"` (the required `ci.yml` / `regression.yml` selection) collects every test not marked `slow`/`loopback`. `full_conformance`-marked tests are `slow` and excluded from that selection (`pytest.ini`), and are run by the dedicated `regression.yml` job.

### 2.3 Expected counts, derived from the exact case set in §3 (inferred)

Let `N=127` new shared cases = 51 **G** (pass today) + 1 **R** (ungated P5 tripwire; fails today) + 75 **RG** (gated by `default_open_functions`; fail today). Existing suite: 901.

| Path | Baseline (exec) | RED expectation (inferred) | GREEN expectation (inferred) |
| --- | --- | --- | --- |
| In-process runner | 901 / 0 / 0, exit 0 | `total=1028 passed=952 failed=76 invalid=0`, **exit 1** (76 = P5 + 75 gated, all executed because the gate is not applied) | `total=1028 passed=1028 failed=0 invalid=0`, exit 0 |
| External Python host | `passed=883 unsupported=18`, others 0 | `total=1028 passed=934 failed=1 unsupported=93 protocol_error=0 crash=0 timeout=0 invalid=0`, **exit 1** (the single failure is the ungated P5 case; 93 = 18 + 75 gated, all `unsupported` before invocation, **not** passes) | `total=1028 passed=1010 failed=0 unsupported=18 …`, exit 0 |
| `test_python_protocol_adapter_parity_762.py` (**unmodified**) | passes (`unsupported == 18`) | **fails**: `counts["unsupported"] == 18` (actual 93), then `failed == 0` (1) and `exit_code == 0` (1) would also fail. Expected and honest; the assertion must **not** be edited to 93 | passes, unchanged: `unsupported == 18`, `passed == total − 18` |

Why P5 is ungated and why that matters: with every Slice C gated case `unsupported`, an external run would otherwise exit **0** with 75 more unsupported cases and no failure — a false green. The ungated P5 tripwire (it changes ungated ordinary behavior) is the one case that makes the external run non-zero at RED, and the unchanged `unsupported == 18` assertion is the permanent guard that no gated case may stay `unsupported` at GREEN. (But see O-2 for the C++ consequence of ungated cases.)

### 2.4 Full path matrix

| # | Path | Command (exact) | Baseline | RED expectation | GREEN expectation | Exit | Evidence | Guard against false GREEN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | Direct RED harness | `uv run pytest -q tests/spec/test_model_b_slice_c_red.py` | file absent; analogous R20 wrapper passes (E5) | 127 parametrized + structural tests: **76 fail** (P5 + 75 gated, with `compare_spec` messages retained), 51 G pass, structural tests pass | all pass; harness becomes the thin wrapper | RED 1 → GREEN 0 | harness absent now → inferred; mechanism exec (E5) | exact ID-set equality; static no-skip/xfail/slow guard (§4 GA-8); RG cases assert `requires` contains the capability |
| P2 | Default in-process runner | E1 command | 901/0/0 | `1028/952/76/0`, exit 1 | `1028/1028/0/0`, exit 0 | 1 → 0 | mechanism rehearsal; counts inferred | cannot hide: no gate applied |
| P3 | External Python adapter | E2 command | `883 pass / 0 fail / 18 unsupported` | `934 / 1 / 93 / 0…`, exit 1 | `1010 / 0 / 18 / 0…`, exit 0 | 1 → 0 | mechanism rehearsal; counts inferred | P5 ungated; GA-4 requires gated IDs `pass` not `unsupported` |
| P4 | Existing parity test | E3 command | pass | **fails** (3 assertions, see §2.3) | passes unchanged | fail → pass | read + arithmetic; mechanism exec (E2) | assertion unmodified |
| P5a | Host parity gate unit tests | `uv run pytest -q tests/unit/test_host_parity_gate.py` | pass | pass unchanged (fabricated evidence; no real C++ build) | pass unchanged | 0 | exec (E5) | — |
| P5b | Host parity gate CLI (`host-parity.yml`) | E4 command, plus C++ evidence in CI | `OK` (Python side) | the workflow's *Generate Python reference-host evidence* step exits 1 (P5) before the gate; if evidence were fed to the gate, `fail ≥ 1` is an `EVIDENCE FAILURE`. With the C++ entry present, `default_open_functions` is `KNOWN_GAP` (not `UNDOCUMENTED_GAP`); **see O-2 for ungated new cases on the C++ side** | gate `OK`; `default_open_functions` stays `KNOWN_GAP` (C++ undeclared, entry present — not `STALE_GAP`) | 1 → 0 | rehearsal for Python side; C++ side inferred | gap entry `affected_tests` must equal the gated ID set exactly (GA-9) |
| W1 | `ci.yml` *Fast tests (py3.14)* | `ruff check .`; `pytest -q -vv --maxfail=1 --cov=genia -m "not slow and not loopback" -n auto`; `… -m "not slow and loopback"`; `python -m tools.spec_runner` | green | red: the first pytest step fails (P1 is non-slow and collected); remaining steps skipped by `--maxfail`/step failure; the `tools.spec_runner` step would also exit 1 | green | 1 → 0 | source (workflow) + inferred | the harness is not slow/xfail/skip |
| W2 | `regression.yml` *Compatibility (py matrix)* | same two pytest selections + `python -m tools.spec_runner` | green | red (same as W1) | green | 1 → 0 | source + inferred | — |
| W3 | `regression.yml` *Slow tests (sections)* | `pytest -q -v -m "slow and not full_conformance" tests/<section>/` | green | unchanged (harness is not `slow`) | unchanged | 0 | source | — |
| W4 | `regression.yml` *Full Python protocol conformance* | `pytest -q -v -m full_conformance tests/spec/test_python_protocol_adapter_parity_762.py` | green | red (= P4) | green | 1 → 0 | source + inferred | unmodified assertion |
| W5 | `github-hosted-runner-canary.yml` | `tools/validate_llm_instructions.py`; `python -m tools.spec_runner`; `pytest -q tests/unit/test_cheatsheet_*.py` | green | the semantic-specs step exits 1 | green | 1 → 0 | source + inferred | — |
| W6 | `self-hosted-runner-smoke.yml` | `python3 -m tools.spec_runner` (plus toolchain checks) | green | exits 1 | green | 1 → 0 | source + inferred | — |
| W7 | `host-parity.yml` (path-triggered by `spec/**`, `hosts/**`, `tools/spec_runner/**`, `src/genia/**`) | Python evidence (`--host-jobs 8`), C++ evidence, `host_parity_gate` | green | red at the Python evidence step (P5) | green | 1 → 0 | source + inferred | see P5b / O-2 |
| W8 | `code-documentation.yml` | `python -m tools.code_documentation [--base-ref <base>] --inventory …`; `pytest -q tests/unit/test_code_documentation.py` | green | **new or changed bindings in the harness and adapter must be documented in the same commit** (C0 needed two repair commits for this); do not add baseline entries | same | — | read (C0 history) | follows `docs/contract/code-documentation.md` |
| W9 | `docs.yml` (mkdocs `--strict`), `validate-llm-instructions.yml`, `docker-dev-environment.yml` | as workflows | green | not triggered by RED (no `docs/`, `README.md` or `docker/` change). **GREEN's documentation edits do trigger them** (`README.md` triggers the docker/C++ conformance job) | green | — | source | — |

*Requirement placed on RED authorization:* RED is a red head by definition — W1, W2, W4, W5, W6 and W7 are **expected** to fail on the RED commit and must not be "fixed" by editing the harness, the parity test, the runner, counts, or by marking anything `slow`/`xfail`/`skip`/`unsupported`. The RED evidence note must record the measured counts against the table in §2.3.

### 2.5 Capability-mechanics rehearsal (exec; throw-away worktree, **not** RED)

To observe the mechanics in §2.2 without writing any Slice C case, a scratch worktree of `main@79c073b` was given: `default_open_functions` appended to `optional_capabilities`, the name added to the override, a C++ gap entry, and **two throw-away eval cases** (one with `requires: [default_open_functions]`, one ungated), each expecting impossible output. Nothing was committed or pushed.

| Rehearsal run (scratch worktree of `main@79c073b`, never committed) | Command | Observed |
| --- | --- | --- |
| In-process runner | `python -m tools.spec_runner` | `total=903 passed=901 failed=2 invalid=0`, exit 1 — **both** throw-away cases were *executed* and reported `FAIL` (the gated one too: the in-process path does not apply the capability gate) |
| External Python host | `python -m tools.spec_runner --verbose --host-jobs 8 --host "<venv>/bin/python -m hosts.python.protocol_adapter" --host-timeout 30 --evidence reh_evidence.json` | `total=903 passed=883 failed=1 unsupported=19 protocol_error=0 crash=0 timeout=0 invalid=0`, exit 1; the gated case printed `UNSUPPORTED` (0.000 s, adapter never invoked for it); the ungated case printed `FAIL`; evidence `capabilities["default_open_functions"] == "unsupported"` (36 names), `counts.unsupported == 19`, `applicable_cases == 903` |
| Host parity gate on that evidence | `python -m tools.spec_runner.host_parity_gate --python-evidence reh_evidence.json --cpp-unavailable-reason rehearsal --known-gaps spec/known_host_gaps.json` | `EVIDENCE FAILURE: python evidence has fail=1 (must be 0)`, `FAIL`, exit 1 |
| `check_parity` with fabricated C++ evidence (name undeclared by C++) | direct call | with the gap entry: `KNOWN_GAP`; without it: `UNDOCUMENTED_GAP`, `ok == False` |
| `tests/doc` with manifest + override + gap edits | `pytest -q tests/doc -n 4` | `397 passed, 35 skipped` — unchanged from baseline |
| Capability / adapter / Slice A·B unit suites with the same edits | `pytest -q tests/unit/test_python_protocol_adapter_762.py tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py tests/unit/test_spec_runner_capabilities.py tests/unit/test_host_parity_gate.py tests/unit/test_model_b_slice_a.py tests/unit/test_model_b_slice_b.py` | `4 failed, 147 passed` — the four failures are exactly four C0 phase-guard tests (§6.3); nothing else moved |

This confirms, by execution, the +1 `unsupported` / +1 `failed` arithmetic that §2.3 scales to 75 / 1, that an ungated failing case is what makes the external run exit non-zero, and that only the C0 phase guards (not `tests/doc`, not the parity gate unit tests) break on the manifest + override edit.

---

## 3. R2 — exact RED harness and case set

### 3.1 Harness specification (design only; not implemented here)

File `tests/spec/test_model_b_slice_c_red.py`. It reuses only existing machinery: `tools.spec_runner.loader.discover_specs/load_spec`, `tools.spec_runner.executor.execute_spec`, `tools.spec_runner.comparator.compare_spec` (the pattern of `tests/spec/test_r20_open_functions_shared_specs.py`). It creates no runner, comparator, evaluator, protocol or expected-output store.

1. **Selection.** Constants `SLICE_C_CASE_IDS` (the 127 IDs of §3.3, literal), `SLICE_C_GATED_IDS` (75), `SLICE_C_UNGATED_RED_IDS = ("model-b-c-disp-p5-varargs-minima-ambiguity",)`. `test_case_id_set_is_exact` loads all specs, selects names starting `model-b-c-`, and asserts **set equality in both directions** and `len == 127` (non-vacuous; a missing or extra file fails).
2. **Applicability checks.** `test_gated_cases_require_the_capability` — every ID in `SLICE_C_GATED_IDS` has `default_open_functions` in `spec.requires`, and no other `model-b-c-` ID has it. `test_guard_cases_keep_original_requires` — every G case's `requires` ⊆ the pre-existing capability vocabulary (never the new name). `test_p5_tripwire_is_ungated`.
3. **Per-case test.** `@pytest.mark.parametrize("spec", specs, ids=name)`: `actual = execute_spec(spec)`; `failures = compare_spec(spec, actual)`; `assert not failures, <expected/actual retained>`. Ordinary assertions only. It executes **every** selected case, including gated ones — this is the one place the external-host gate is bypassed, which is what makes RED visible.
4. **Markers.** None of `slow`, `xfail`, `skip`, `skipif`, `loopback`. Runs under the ordinary required selection (`-m "not slow and not loopback"`); `tests/spec` is already collected by W1/W2.
5. **Genuine RED.** Against the current implementation the 75 RG cases and P5 fail; the 51 G cases pass. This split is an **inferred** expectation for the RED author to *prove* by running the harness and recording `selected / passed / failed / invalid / unsupported(=0)` and each failure message. A G case that fails today, or an RG/R case that passes today, is a stop condition (the oracle or the classification is wrong), not something to adjust.
6. **Ungated C-MAIN guards.** `main-legacy-*`, `main-no-qualifying`, `main-command-mode` (and `main-repl-never-selects` with `requires: repl`) are G cases in the set; they pass today (exec) and must pass through every refactor.
7. **No hiding through capability staging.** The harness never consults capability claims; staging only affects the external-host path.
8. **Host-local tests** (§3.4) live in `tests/unit/test_model_b_slice_c_*.py`, run in the required selection, and say in their module docstrings that they cover Python internals (per AGENTS "Portable-behavior test placement").

### 3.2 Oracle status legend

- **D** — derived: the expected result follows from an approved decision/contract text *and* (where a current-behavior fact is cited) was observed in this session.
- **A** — author-at-RED: the observation and its expected outcome follow from an approved rule, but the accepted plan does not pin the source text (or a dependent API). The RED author writes the source, byte-characterizes the baseline, and **stops** (SC) if the result contradicts the stated outcome. Not an invented oracle: no expected value is changed without a recorded amendment.
- **L** — literal-lock: the outcome class and shape are derived, but the exact diagnostic string is locked only after byte-characterization at the RED baseline (maintainer directive, U4). Where an `open` twin already produces the renderer text (exec), the expected string is shown.
- **B** — blocked: the oracle cannot be derived from accepted sources. Listed for traceability, **not created** in RED until resolved.

"exec" in the Baseline column means the program was run through the existing in-process adapter (`hosts.python.adapter.run_case`, the path the shared runner uses) or the CLI on `main@79c073b`; `model-b-not-implemented: …` abbreviates `model-b-not-implemented: declaration evaluation is not available` (exec, same text for every pattern-bearing declaration).

### 3.3 Exact case-ID inventory (shared R16 YAML, `spec/{eval,error,cli}/model-b-c-*.yaml`)

Kinds: **G** passes today, original applicability, must stay green · **R** ungated, fails today · **RG** fails today, `requires` includes `default_open_functions`. 128 rows listed, 127 created (one **B** reserved).


#### C-OPEN

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `open-noncontiguous-arities` | G | - | exec: `[1, 3]` | `[1, 3]` | D |
| `open-alias-sees-later-arity` | G | - | exec: `3` | `3` | D |
| `open-immutable-alias-stays-live` | G | immutable_bindings | exec: `3` | `3` | D |
| `open-call-before-later-clause` | G | - | exec: `No matching function: f/2. Available: f/1` | same (byte-identical) | D |
| `open-pattern-after-plain` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[0, 1]` (earlier catch-all wins) | D |
| `open-noncontiguous-pattern` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | stdout `a` then `["a", "b"]` (`f(0)="a"; g(y)=y; print(f(0)); f(1)="b"; [f(0), f(1)]`) | D |
| `open-lambda-factory-distinct` | G | - | exec (corrected source, see §2 note): `[2, 3, true, false]` | `[2, 3, true, false]` for `mk(k) { g = (x) -> x + k; g }` | D |
| `open-persistent-env` | RG | default_open_functions, repl | REPL transcript fails (no clause install) | group grows across submissions; `f(0, 5)` → `5` | L |

#### C-PAT

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `pat-literal-base-case` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `120` | D |
| `pat-guard-selects` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `["pos", "other"]` | D |
| `pat-guard-sees-header-binding` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[3, 6]` | D |
| `pat-match-local-shadows-outer` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `1` | D |
| `pat-list-rest` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[2, 3]` | D |
| `pat-map` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `5` | D |
| `pat-some` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `3` | D |
| `pat-err` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `"bad"` | D |
| `pat-wildcard` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `1` | D |
| `pat-first-match-wins` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `1` | D |
| `pat-fixed-miss-no-varargs-fallthrough` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: No matching case for function f/1 with arguments [5]`, exit 1 | D |
| `pat-fixed-miss-two-args-varargs` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `2` | D |
| `pat-named-matcher` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | named pattern (`pattern Name(value) = body`, STATE §3) used as a header; result per matcher | A |
| `pat-string-body-is-body` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `f("a")` → body string; `doc` observation not derivable yet | A |

#### C-KEY

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `key-true-vs-one` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[1, 2]` | D |
| `key-one-vs-one-point-zero` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[10, 10]` | D |
| `key-same-binary64-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (renderer reproduced by the executed `open` twin) | L |
| `key-spelling-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (renderer reproduced by the executed `open` twin) | L |
| `key-alpha-equivalent-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (renderer reproduced by the executed `open` twin) | L |
| `key-guard-alpha-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` (renderer reproduced by the executed `open` twin) | L |
| `key-guard-differs-ok` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `[1, 2]` | D |
| `key-free-name-syntactic` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `limit = 1; cap = 1`, guards `x > limit` / `x > cap` → both install; `f(5)` → first | D |
| `key-lambda-shadow-dup` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | duplicate error (text as above) | A |
| `key-lambda-shadow-outer-slot-distinct` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | both install (inner binder shadowing an outer pattern binder is not collapsed with one referencing the outer slot) | A |
| `key-quote-unquote` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | quoted names are data; active unquote participates | A |
| `key-repeated-binders-distinct` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `f(x, x)` vs `f(a, b)` — **repeated-binder (non-linear) pattern semantics are not specified in the accepted plan or contract** | B |
| `key-rest-binders-legacy-duplicate` | G | - | exec: `Duplicate function definition: f/1` for `f(x, ..r)=1; f(y, ..s)=2` | unchanged legacy duplicate (both plain identifier headers) | D |
| `key-named-matcher` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | distinct matcher references distinct; same reference duplicate | A |
| `key-no-effects` | RG | default_open_functions, refs | `model-b-not-implemented: declaration evaluation is not available` | rejected duplicate runs no guard/matcher/body; `Ref` log empty (`ref`/`ref_update`/`ref_get` exist: exec) | A |
| `key-legacy-dup-id` | G | - | exec: `Duplicate function definition: f/1` | unchanged | D |
| `key-r20-delta-true-one` | RG | open_functions, default_open_functions | exec: `open-function-duplicate-clause … ('fixed', 1) …` (P13) | `[1, 2]` (approved R20 acceptance change) | D |
| `key-r20-delta-one-float` | RG | open_functions, default_open_functions | exec: duplicate error (P13) | `open f(1)=1; f(1.0)=2; f(1.0)` → `1` | D |

#### C-DISP

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `disp-p5-varargs-minima-ambiguity` | R | - | exec: `"min2"` (wrong) | `Error: Ambiguous function resolution: f/2. Matching varargs: f/1+, f/2+`, exit 1 | D |
| `disp-p5-migration-fixed-clause` | RG | default_open_functions | exec: `Duplicate function definition: f/2` | `"exact2"` | D |
| `disp-p5-migration-drop-lower` | G | - | exec: `"min2"` | `"min2"` | D |
| `disp-p7-same-arity-ambiguity` | G | - | exec: `Ambiguous function resolution: f/3. Matching varargs: f/1+, f/2+` | unchanged | D |
| `disp-fixed-over-varargs` | G | - | exec: `["exact", "varargs"]` | unchanged | D |
| `disp-fixed-and-varargs-same-arity` | RG | default_open_functions | exec: `Duplicate function definition: f/1` (P4) | `[1, 2]` | D |
| `disp-no-matching-function` | G | - | exec: `No matching function: f/2. Available: f/1` | byte-identical | D |
| `disp-no-matching-function-new-group` | RG | default_open_functions | exec: `Duplicate function definition: f/1` | `Error: No matching function: f/0. Available: f/1, f/2, f/1+` (executed `open` twin yields this exact text) | L |
| `disp-duplicate-pattern-header` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | duplicate error (renderer text as C-KEY; executed twin) | L |
| `disp-case-miss-identity` | G | - | exec: `No matching case for function f/1 with arguments [1]` | unchanged | D |
| `disp-case-miss-pattern-group` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: No matching case for function f/1 with arguments [5]` | D |
| `disp-no-clause-ambiguity-single-unit` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | overlapping pattern/guard clauses: first match, never `open-function-clause-ambiguity` | A |

#### C-HDR

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `hdr-block-prefix-once` | G | - | exec: `prefix` / `2` | unchanged | D |
| `hdr-block-prefix-miss` | G | - | exec: stdout `prefix`; `No matching case for function f/1 with arguments [2]` | unchanged | D |
| `hdr-block-prefix-multi-call` | G | - | exec: `prefix` / `prefix` / `[1, 2]` | unchanged | D |
| `hdr-grouped-body-captures-header` | G | - | exec: `[0, 10]` | unchanged | D |
| `hdr-guard-evaluated-once` | RG | default_open_functions, refs | `model-b-not-implemented: declaration evaluation is not available` | counter `1` after one call | A |
| `hdr-guard-order` | RG | default_open_functions, refs | `model-b-not-implemented: declaration evaluation is not available` | `[2, ["a", "b"]]` for three effect-logging guards | D |
| `hdr-guard-error` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | guard error propagates; later guards not run; no partial binding | A |
| `hdr-matcher-outcome` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | named matcher returning `none`/`err` follows existing pattern-outcome behavior | A |
| `hdr-recursion-tco` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | constant-stack twin of `r20-open-ordinary-mutual-tail-call` | A |

#### C-OPTIM

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `optim-collection-recursion` | G | - | exec: `6` | `6` | D |
| `optim-late-declaration` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | optimized declaration then later different-shape clause: both visible | A |

#### C-OPT

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `opt-none-pattern-in-group-dispatches` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | twin of `r20-option-none-pattern-in-stratum-dispatches` | A |
| `opt-other-arity-clause-not-aware` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | twin of `r20-option-other-arity-clause-not-aware` | A |
| `opt-delegation-to-aware-callee` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | twin of `r20-option-delegation-to-aware-callee` | A |
| `opt-err-pipeline-value-short-circuits` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | twin of `r20-option-err-pipeline-value-short-circuits` | A |
| `opt-plain-identity-none` | G | - | exec: `none("r")` | `none("r")` | D |
| `opt-pipe-lift` | G | - | not yet executed | existing `|>` lift behavior unchanged | A |

#### C-OWN

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `own-alias-call-live` | G | - | exec: `3` | `3` | D |
| `own-immutable-alias-live` | G | immutable_bindings | exec: `3` | `3` | D |
| `own-local-alias-rejected` | RG | default_open_functions | exec: installs, prints `<function a/2>` (P10) | `Error: function-declaration-not-owner: cannot declare a/2: 'a' refers to function 'f' declared by another binding in this scope` | L |
| `own-local-alias-state-after-rejection` | RG | default_open_functions | exec: group grows | `f(1)`→`1`, `a(1)`→`1`, `f(1, 2)`→`No matching function: f/2. Available: f/1` | D |
| `own-local-alias-owner-still-extendable` | RG | default_open_functions | n/a | after rejection `f(x, y) = x + y; a(1, 2)` → `3` | D |
| `own-local-alias-pattern-clause` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `… cannot declare a/2: …` same category | L |
| `own-local-alias-varargs` | RG | default_open_functions | exec: `Duplicate function definition: a/1` (appends to `f`) | `… cannot declare a/1+: …`; **ownership check must precede the duplicate check** | L |
| `own-alias-annotation-not-evaluated` | RG | default_open_functions, refs | exec: annotation would run | rejection first; effect log empty | A |
| `own-imported-alias-rejected` | RG | default_open_functions, multi_file_eval | P11 (Slice-C plan): installs, `3` | `function-declaration-not-owner: cannot declare h/2: 'h' refers to function 'g' owned by module 'lib'` | L |
| `own-imported-alias-owner-unchanged` | RG | default_open_functions, multi_file_eval | P11 | `lib.g(1, 2)` → `No matching function: g/2. Available: g/1`; `lib.g(1)` → `1` | D |
| `own-lambda-nonfunction-unchanged` | G | - | exec: `Cannot define function g/2: name already bound to non-function value` | unchanged | D |
| `own-builtin-nonfunction-unchanged` | G | - | exec: `Cannot define function p/2: name already bound to non-function value` | unchanged | D |
| `own-explicit-open-unchanged` | G | open_functions | exec (probe `open f(0)=1; g(x)=x; f(n)=n`): `open-function-redeclaration: 'f' is already declared open in module '<entry>'` | unchanged; the plan's quoted text (`Cannot define function … open function interface or linked view`) is **not** what this probe produces — program selection needs characterization | A |
| `own-import-inert` | G | multi_file_eval | not yet executed | import never changes dispatch elsewhere | A |
| `own-extend-ordinary-rejected` | G | multi_file_eval, open_functions | not yet executed | `open-function-target-not-open` unchanged | A |
| `own-use-ordinary-base-unchanged` | G | multi_file_eval, open_functions | not yet executed | current behavior characterized, unchanged | A |
| `own-two-modules-independent` | RG | default_open_functions, multi_file_eval | `model-b-not-implemented: declaration evaluation is not available` | independent groups | A |
| `own-entry-prelude-name` | G | - | exec: `["mine", [2, 3]]` (P12) | unchanged characterization | D |

#### C-D8

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `d8-forward-collision` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `["zero", "other"]` | D |
| `d8-reverse-collision` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `["clause", 5]` | D |
| `d8-terminal-grouped-miss` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `No matching case for function f/1 with arguments [9]` | D |
| `d8-earlier-pattern-miss-continues` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `No matching case for function f/1 with arguments [5]` | D |
| `d8-legacy-identical-header-dup` | G | - | exec: `Duplicate function definition: describe/1` | unchanged | D |
| `d8-grouped-decl-one-key` | G | - | exec: `["z", 6, 3]` | unchanged | D |
| `d8-prefix-and-capture` | G | - | not yet executed (composition of executed `hdr-*` cases) | prefix once per call, header capture preserved | A |
| `d8-r20-flattening-unchanged` | G | open_functions | exec: `open-function-duplicate-clause …` | unchanged (Option A not applied to `open`) | D |

#### C-IMM

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `imm-rebind-as-function` | G | immutable_bindings | exec: `Cannot rebind immutable binding: x` | unchanged | D |
| `imm-rebind-as-pattern-function` | RG | immutable_bindings, default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `Error: Cannot rebind immutable binding: x`; nothing installed | D |
| `imm-declare-after-function` | G | immutable_bindings | exec: `Cannot declare immutable binding f: name is already bound in this scope` | unchanged | D |

#### C-META

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `meta-binding-doc-merge` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-newer-key-overwrites` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-alias-no-copy` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-inline-doc-shared-via-alias` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-conflicting-inline-doc-before-install` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-three-channel-trio` | G | - | partially executed (`meta-doc-merge` probe printed `d1`); remainder not yet executed | contract §5.1 observation (see plan) | A |
| `meta-pattern-clause-annotations` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | pattern clauses accept annotations legal on legacy clauses | A |

#### C-ANN

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `ann-later-annotation-suppressed` | G | refs | `@doc 7` → exec: `@doc annotation expected a string, received int`; rest not yet executed | contract §5.2 observation | A |
| `ann-old-metadata-retained` | G | - | `@doc 7` → exec: `@doc annotation expected a string, received int`; rest not yet executed | contract §5.2 observation | A |
| `ann-installed-clause-visible-via-alias` | G | - | `@doc 7` → exec: `@doc annotation expected a string, received int`; rest not yet executed | contract §5.2 observation | A |
| `ann-prior-effects-persist` | G | refs | `@doc 7` → exec: `@doc annotation expected a string, received int`; rest not yet executed | contract §5.2 observation | A |
| `ann-pattern-clause-variants` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | same observations for pattern clauses | A |
| `ann-repl-recovery` | RG | default_open_functions, repl | `model-b-not-implemented: declaration evaluation is not available` | failure leaves session usable; group unchanged except installed clause | A |

#### C-MODE

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `mode-file-command-import-equivalence` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | file / `-c` / import / piped equivalents give identical program results | A |
| `mode-repl-failed-declaration-leaves-group` | RG | default_open_functions, repl | `model-b-not-implemented: declaration evaluation is not available` | duplicate/immutable/ownership failure leaves group unchanged and the name usable | A |

#### C-STAGE

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `stage-closed-rejected` | G | - | exec: stdout `before`, `model-b-not-implemented: declaration evaluation is not available` | unchanged; `child` never printed | D |

#### C-MAIN

| Proposed ID (`model-b-c-…`) | Kind | `requires` | Baseline (current `main`) | RED oracle | Status |
| --- | --- | --- | --- | --- | --- |
| `main-legacy-main1-preferred` | G | - | exec: `top` / `main1` / `11` | unchanged | D |
| `main-legacy-main0-fallback` | G | - | exec: `top` / `main0` / `10` | unchanged | D |
| `main-legacy-rest-main-selected` | G | - | exec: `top` / `mainrest` / `12` | unchanged | D |
| `main-no-qualifying` | G | - | exec: `top` / `42` | unchanged | D |
| `main-command-mode` | G | - | exec: `top` / `cmdmain` / `["x", "y"]` | unchanged | D |
| `main-repl-never-selects` | G | repl | not yet executed | transcript framing characterized from existing `model-b-b-repl-*` cases | L |
| `main-pattern-not-selected` | RG | default_open_functions | exec: `model-b-not-implemented: declaration evaluation is not available` | `top` / `42`; no `pattern-main` | D |
| `main-pattern-guard-not-evaluated` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `top` / `42`; no `guard-ran`, no `body` | D |
| `main-wildcard-not-selected` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `top` / `42`; no `wild` | D |
| `main-multi-pattern-group-not-selected` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `top` / `42`; no `A`, no `B` | D |
| `main-pattern-command-mode` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | source result only; no body output | D |
| `main-explicit-call-dispatches` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `pattern-main` (exactly once) / `1` / `42` | D |
| `main-explicit-call-miss` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `No matching case for function main/1 with arguments …`; argument rendering to be byte-characterized | L |
| `main-test-mode-unchanged` | RG | default_open_functions | `model-b-not-implemented: declaration evaluation is not available` | `@test` runs; pattern-bearing `main` produces no output | A |


**Reserved, not created (G1-dependent):** `model-b-c-main-g1-mixed-*` (five IDs, §7) — absent from the RED set until the maintainer approves G1.

**Existing specs cited, not duplicated or edited:** `error-r20-local-duplicate-clause`, `error-r20-varargs-ambiguity`, all `r20-*`, `f2-*`, `model-b-a-*`, `model-b-b-*`, `file_mode_main_argv`, `pipe_mode_bypass_main`, and the Slice A `parse-error-mixed-function-declaration-operators` pin (the plan's `stage-mixed-operators` case is therefore **not** added; exec shows `Error: mixed-function-declaration-operators`).

### 3.4 Host-local inventory (`tests/unit/test_model_b_slice_c_*.py`; not counted in the 127)

| ID | Test subject | Oracle source | Status |
| --- | --- | --- | --- |
| HL-1 | group record API: ordered records, legacy-only arity index consistency, owner/provenance | design §3; pre-flight §5.4 | D |
| HL-2 | pure key walker against the §2.2 table; no `repr`/host-equality fallback; malformed structure rejected | pre-flight §2.2 | D |
| HL-3 | writer atomicity/reentrancy: barriers, bounded joins, both orderings; user code never under `_BINDING_LOCK` | pre-flight §7 | D |
| HL-4 | consumer predicate table (route / HTTP / `@test` / lifecycle / `help`·`doc`·`meta`) + grep-level "no `get(n)` on multi-record group without cardinality check" | pre-flight §2.5 | D |
| HL-5 | autoload/prelude twin of `test_autoload_resolution_matches_non_autoload` with pattern clauses; P12 | pre-flight §5.4 | A |
| HL-6 | exception-class identity: `TypeError` legacy duplicate / `OpenFunctionDuplicateClauseError` / shape-miss `TypeError` / case-miss `RuntimeError` / ambiguity `TypeError` / `FunctionDeclarationNotOwnerError` | pre-flight §2.4 | D |
| HL-7 | source ↔ direct-IR equivalence for every source-expressible RG/R case | design | A |
| HL-8 | optimizer on/off equivalence; D8 arm retention (`optim-keys-retained`, `d8-arms-retained-not-checked`) | pre-flight §2.6 invariant 4 | D |
| HL-9 | C-MAIN structural: `_resolve_program_result` reached only from the `command`/`file` branches; no pattern/guard evaluation in it; no new `main` error category (read: `interpreter.py:513-528`, `:671`, `:687`) | pre-flight §2.5.1 | D |
| HL-10 | `Env.define_function` owner checks via module-identity/name provenance, not `callable(value)`; ordinary groups not accepted by `IrOpenContribution`/`IrOpenUse` target checks | pre-flight §2.3 | D |
| HL-11 | **R4 diagnostic safety:** ownership / foreign-alias messages contain no filesystem path, `0x…` address, source span or captured/protected value; module rendered by canonical identity or `<entry>`; protected R10 sentinel absent from case-miss / duplicate / ownership diagnostics | §5.3 | D |
| HL-12 | **R4 file-mode label characterization:** a duplicate involving a pattern clause, run through the CLI on a `tmp_path` file, renders the existing entry label (the host-resolved path, §5.2) — asserted as `str(Path(file).resolve())`, not a literal | §5.2 | D |
| HL-13 | capability evidence: exact RED capability map (a *new* constant, §6.2); every `SLICE_C_GATED_IDS` spec through `execute_spec_via_host` with a witness host that records invocations → all `unsupported`, zero invocations; non-vacuous counts | R3 | D |
| HL-14 | `immutable`-interaction: `_meta_define` cannot append to an immutable-owned name | pre-flight §6 | A |

### 3.5 Cases whose expected result cannot yet be derived unambiguously (flagged, no oracle invented)

1. **`key-repeated-binders-distinct` (B).** Whether `f(x, x)` is a legal non-linear header and how it compares with `f(a, b)` is not specified in the pre-flight, contract or design. Needs a maintainer/contract answer (or a documented existing-pattern-semantics characterization) before the case is created.
2. **`own-explicit-open-unchanged` (A).** The plan quotes `Cannot define function … open function interface or linked view`; the probe `open f(0)=1; g(x)=x; f(n)=n` yields `open-function-redeclaration: 'f' is already declared open in module '<entry>'` instead (exec). The program that triggers the quoted diagnostic must be identified from the existing R20 specs.
3. **All **L** cases** — exact strings locked at the RED baseline.
4. **Source defects in the accepted plan** (corrected here, §8.4): the lambda-factory program and the migration/new-group programs.
5. **`pat-string-body-is-body`, `pat-named-matcher`, `key-named-matcher`, `hdr-matcher-outcome`** — the `doc(...)` observation for an undocumented pattern group and the named-pattern body forms are not characterized; **A** until the RED author characterizes them on legacy twins.

Stop rule (unchanged): if writing any A/L case needs a semantic choice, stop and return to #1249; never replace the stated outcome silently.

---

## 4. R3 — GREEN anti-false-positive gate

Required for GREEN acceptance; every item is an automated assertion or a recorded command unless marked *checklist*.

| ID | Assertion | Type |
| --- | --- | --- |
| GA-1 | `default_open_functions` is in `spec/manifest.json["optional_capabilities"]` and **not** in `required_capabilities`; it was added only in the RED commit (before it, the C0 absence test holds; after, this) | static test |
| GA-2 | `hosts.python.protocol_adapter._VOCABULARY_ONLY_CAPABILITIES` does not contain `default_open_functions`; at GREEN it is `frozenset()` (or deleted with the mechanism covered, per the plan) | static test |
| GA-3 | `_python_claimed_capabilities()` **equals the literal** `GREEN_CAPABILITY_MAP` = the 35-entry C0 map plus `"default_open_functions": "supported"` (36 entries). Written as an explicit literal, never generated from code | test |
| GA-4 | For every ID in `SLICE_C_GATED_IDS`, `execute_spec_via_host(spec, <real adapter command>, host_capabilities=_python_claimed_capabilities())` returns `kind == "pass"` — **not** `unsupported`. The P5 case also returns `pass`. An aggregate asserts the set of kinds is exactly `{"pass"}` over all 127 | test (non-slow if run in the harness's sibling; may reuse the external run) |
| GA-5 | `tests/spec/test_python_protocol_adapter_parity_762.py` passes **unmodified** (`unsupported == 18`, `passed == total − 18`, zero failure classes, exit 0), because the applicability contract is unchanged | existing test |
| GA-6 | `python -m tools.spec_runner` exits 0 with `failed=0 invalid=0` and `total == 1028` | recorded command (W1–W6) |
| GA-7 | The harness is converted to a thin wrapper over the same ID set; no skip/xfail introduced | test |
| GA-8 | Static guard: `tests/spec/test_model_b_slice_c_red.py` (and its GREEN successor) contains no `skip`, `skipif`, `xfail`, `slow`, or conditional import-skip; present from the RED commit | static test |
| GA-9 | The `default_open_functions` entry in `spec/known_host_gaps.json` lists `affected_tests` equal to the gated ID set derived from the YAML `requires` (not typed twice by hand); present from RED, still true at GREEN | test |
| GA-10 | The Python evidence JSON from the external run shows `capabilities["default_open_functions"] == "supported"` **and** `counts.unsupported == 18` (supported is meaningful only with PASS evidence, never with a count of unsupported cases) | recorded command |
| GA-11 | `host_parity_gate` reports `default_open_functions` as `KNOWN_GAP` (C++ still undeclared) — not `UNDOCUMENTED_GAP` and not `STALE_GAP` | recorded command (CI) |
| GA-12 | The **C0 phase guards are updated deliberately** (§6.3), never regenerated or weakened; the original `PRE_C0_CAPABILITY_MAP` literal is kept as history | review checklist |

**An external runner that exits 0 because gated cases were classified `unsupported` is not GREEN.** GREEN is the conjunction GA-2 ∧ GA-3 ∧ GA-4 ∧ GA-5 ∧ GA-6.

### 4.1 Capability vocabulary / override sequence

| State | `spec/manifest.json` | `_VOCABULARY_ONLY_CAPABILITIES` | Python-advertised map | External-host gated cases | In-process gated cases | Known gap (C++) |
| --- | --- | --- | --- | --- | --- | --- |
| **Now** (`main@79c073b`) | name absent | `frozenset()` | 35 names (34 supported, `shared_spec_runner` partial) | n/a | n/a | none |
| **RED commit** | name appended to `optional_capabilities` | `frozenset({"default_open_functions"})` | 36 names, new one `unsupported` | `unsupported` before invocation | executed → fail | entry added: `m0smith/genia-2026#1269`, `affected_host: cpp`, `affected_tests` = 75 gated IDs |
| **GREEN commit** | unchanged | name **removed** (set empty again, or mechanism deleted) | 36 names, new one `supported` | `pass` | pass | entry unchanged |

The manifest edit and the override edit must be in the **same commit**: manifest-first would make the Python adapter advertise `supported` (the default branch) — a false claim; override-first would raise `ValueError` (unknown name); gated YAML without the name makes the loader reject `requires` (`invalid`). (Reasoning: read — `_python_claimed_capabilities`, `capabilities.validate_case_requirements`.)

---

## 5. R4 — diagnostic-path compatibility (directed disposition applied)

**Disposition (directed):** preserve the existing R20 duplicate-diagnostic renderer for pattern-clause duplicates, **including its established file-mode source-location format**. Apply stricter path redaction only to newly defined ownership / foreign-alias errors and specifically designated sanitized surfaces. No blanket ban on file paths across all new diagnostics.

### 5.1 Separation of diagnostic classes

| Class | Renderer / category | Path policy | Source |
| --- | --- | --- | --- |
| Existing R20 duplicate-clause rendering (`open …`) | `OpenFunctionDuplicateClauseError`, `callable.py::_format_open_span` | entry clauses render `<label>:<line>`; imported-module clauses render `<module-identity>:<line>` | exec, read |
| **New** pattern-duplicate messages (ordinary groups) | **reuse** the same class and renderer unchanged | identical to the existing renderer (command mode `<command>:N`; file mode the entry label as given) | pre-flight §2.4 D3 |
| Ownership / foreign-alias (`function-declaration-not-owner`) | new `FunctionDeclarationNotOwnerError` | **no** path, address, span or captured/protected value; canonical module identity or `<entry>` only | D5; design §3 |
| Case-miss / shape-miss | existing `RuntimeError` case-miss; `TypeError` shape-miss (`OpenFunctionNoMatchingFunctionError` rendering for new groups) | no spans at all; arguments via `format_debug` (protected values masked) | exec |
| Host-generated / protected-value diagnostics | unchanged; R10 sentinels never appear | existing protections | pre-flight §10 |

### 5.2 Grounded examples (exec, `main@79c073b`, `open` twin of the pattern-duplicate because the ordinary form does not execute yet)

| Mode | Program | Observed stderr |
| --- | --- | --- |
| command mode (`genia -c`) and shared `eval`/`error` category | `open f([a,b])=1` / `f([c,d])=2` | `Error: open-function-duplicate-clause: f in unit 'base' has two clauses with an identical dispatch key shape=('fixed', 1) (first at <command>:1, duplicate at <command>:2)` |
| file mode, invoked as `genia dup.genia` (relative) | same text in `dup.genia` | `… (first at /<absolute>/dup.genia:1, duplicate at /<absolute>/dup.genia:2)` — **the host-resolved absolute path, even for a relative or subdirectory argument** (`sub/dup.genia` also resolves to `/<absolute>/sub/dup.genia`) |
| file mode, invoked with an absolute path | same | identical absolute path |
| legacy-only duplicate, either mode | `f(x)=1` / `f(y)=2` | `Error: Duplicate function definition: f/1` (no span) |
| shape miss | `f(x)=1` / `f(1,2)` | `Error: No matching function: f/2. Available: f/1` |
| case miss | `f(x) = (0 -> x)` / `f(1)` | `Error: No matching case for function f/1 with arguments [1]` |
| new-group shape miss (`open` twin) | `open f(x)=1; f(x,y)=2; f(x,..r)=3; f()` | `Error: No matching function: f/0. Available: f/1, f/2, f/1+` |

### 5.3 Oracle placement that follows

1. **Shared YAML (`eval`/`error`) duplicate oracles use the `<command>` label.** The comparator compares stderr **exactly** (`comparator.py`), and a file-mode path is machine-dependent, so a shared file-mode duplicate oracle with an exact string is not expressible and is **not created**. (Existing precedent: `error-r20-local-duplicate-clause`.)
2. **File-mode behavior is pinned host-locally (HL-12)** by asserting the label equals `str(Path(file).resolve())` — preserving, not redacting, the existing renderer.
3. **Ownership / foreign-alias diagnostics** keep the stricter rule (HL-11): canonical module identity or `<entry>` only; shared cases `own-local-alias-*` / `own-imported-alias-*` use exact strings with no span.
4. The plan's blanket C-ERR sentence ("no filesystem path … in any new diagnostic") is **narrowed** accordingly in the revised RED plan.

### 5.4 Ownership-versus-duplicate ordering (found while grounding)

`f(x) = x; a = f; a(x, ..r) = x` currently fails with `Duplicate function definition: a/1` (the declaration appends to `f`'s group, exec). After D5 the ownership check must run **before** any duplicate check, otherwise the case would surface the legacy duplicate message instead of `function-declaration-not-owner` (`own-local-alias-varargs`, L).

### 5.5 Amendment required before RED (not made here)

The design (#1259) §3 says diagnostics "render canonical imported module names or the existing entry label, never filesystem paths", and §13.5 says "without leaking host-only absolute paths". The **existing entry label in file mode is the host-resolved absolute path** (exec above). The two statements conflict for file-mode pattern-duplicate diagnostics. The directed disposition resolves it by preserving the renderer; the design/contract text needs a **one-line maintainer-approved clarification** (e.g. "for diagnostics produced by the existing R20 duplicate renderer the entry label is the host's entry label, which in file mode is the resolved entry path; the 'never filesystem paths' rule applies to ownership/foreign-alias and other designated sanitized diagnostics") recorded as a decision on #1269 (no design-document edit is made in this phase). RED duplicate oracles for file mode must not be locked until that sentence is confirmed.

---

## 6. R5 — manifest, documentation and phase-guard synchronization

### 6.1 Manifest edit the RED phase must make (not made here)

`spec/manifest.json` has `required_capabilities` (8 names) and `optional_capabilities` (27 names; last entry `immutable_bindings`). Both are flat string arrays; no per-capability schema. The RED commit appends exactly one string, `"default_open_functions"`, to **`optional_capabilities`** (never `required_capabilities`: required capabilities are not relaxed and are ineligible for gap entries). `known_capabilities()` then returns 36 names. Because `host_parity_gate.optional_capabilities()` iterates the optional list, C++ (which does not declare it) needs the known-gap entry in the same commit or the parity gate reports `UNDOCUMENTED_GAP`.

### 6.2 What changes in RED, and what must not

| Artifact | RED | GREEN |
| --- | --- | --- |
| `spec/manifest.json` | + `default_open_functions` (optional) | unchanged |
| `hosts/python/protocol_adapter.py` | override becomes `frozenset({"default_open_functions"})` | override emptied/removed |
| `spec/known_host_gaps.json` | + C++ entry (`tracking_issue: m0smith/genia-2026#1269`, `affected_host: cpp`, exact gated IDs, reason, removal condition) | unchanged |
| `spec/{eval,error,cli}/model-b-c-*.yaml` + sibling `.genia` | + 127 cases | unchanged |
| `tests/spec/test_model_b_slice_c_red.py`, `tests/unit/test_model_b_slice_c_*.py` | added (failing) | thin wrapper; host-local tests green |
| C0 phase-guard tests | updated deliberately (§6.3) | updated deliberately |
| Existing parity/capability/R20/F2/Slice A·B tests, existing specs | **unchanged** | unchanged except §6.4 |
| `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/book`, cheatsheets, `docs/ai/LLM_CONTRACT.md`, semantic facts, MCP profile, host-capability docs, roadmap | **unchanged** (nothing is implemented) | updated to verified behavior only |

### 6.3 C0 phase guards that change intentionally (`tests/unit/test_python_protocol_adapter_c0_capability_staging_1269.py`)

- RED: `test_override_is_empty_and_immutable_in_production` → asserts `frozenset({"default_open_functions"})`; `test_empty_override_capability_map_equals_pre_c0_baseline_exactly` → keep `PRE_C0_CAPABILITY_MAP` as a historical literal and add `RED_CAPABILITY_MAP = PRE_C0_CAPABILITY_MAP + {"default_open_functions": "unsupported"}`, asserting equality with it; `test_default_open_functions_is_not_in_the_vocabulary_or_the_override` → inverted (name **is** in the vocabulary and in the override); `test_staged_known_capability_is_reported_unsupported_and_others_unchanged` → its expected dict is rebuilt from the RED map (rehearsal: it fails otherwise because the advertised map gains a 36th name). These are the **four** C0 tests the rehearsal showed failing; the remaining seven (unknown-name rejection, `shared_spec_runner` precedence, external-host no-invocation, ungated unaffected, R20 gating unchanged, full-vocabulary and status checks) passed unchanged.
- GREEN: override empty again; `GREEN_CAPABILITY_MAP = PRE_C0_CAPABILITY_MAP + {"default_open_functions": "supported"}` (GA-3).
- Every other test in that file (unknown-name rejection, external-host no-invocation, ungated unaffected, R20 gating unchanged) is retained as written.

### 6.4 Documentation and phase-guard tests

- **`tests/doc` must be rerun after the manifest edit** (R5, and every subsequent edit). **Rehearsal:** `397 passed, 35 skipped` after adding the name to the manifest (together with the override and a gap entry) in the scratch worktree — no documentation test depends on the new name. Re-run on the real RED commit and record the count.
- Tests that look at the manifest/capability lists: `tests/doc/test_portability_contract_sync.py::test_manifest_capabilities_cover_capability_matrix` checks matrix rows → manifest (one direction), so **adding a manifest name without a matrix row passes at RED**; at GREEN, adding the `default_open_functions` row to `docs/host-interop/HOST_CAPABILITY_MATRIX.md` requires adding its display name to that test's `display_to_key` mapping — an intentional, additive edit. `docs/host-interop/capabilities.md` is a separate runtime-capability registry and is not manifest-driven.
- **Phase guards that must change at GREEN, not RED** (they assert pattern headers are not executable today; they pass until GREEN):
  - `tests/unit/test_model_b_slice_a.py::test_transitional_rejection` — parameters `f([x]) = x` and `f(x) ? true = x` (the `f(x) =: x` parameter stays: closed groups remain unimplemented);
  - `tests/unit/test_model_b_slice_b.py::test_closed_and_pattern_declarations_remain_not_implemented` — the `f([x]) = x` half;
  - `tests/unit/test_r28_mcp_language_profile.py` (≈ line 208) and `tests/unit/test_r28_mcp_language_registry.py` (≈ line 184) — the un-`open`ed `gcd` pattern-clause rejection probes;
  - `tests/unit/test_model_b_slice_b.py` ≈ lines 306/313 — **inspect at GREEN** (closed/annotated discovery rejection; may stay);
  - `GENIA_STATE.md` ≈ lines 744 and 3626, `docs/contract/semantic_facts.json` ≈ lines 255 and 448, `tests/data/mcp_language_profile.golden.json`, `docs/host-interop/HOST_CAPABILITY_MATRIX.md` ≈ line 93, `docs/architecture/core-ir-portability.md` ≈ line 219, `docs/book/03-functions.md`, `docs/cheatsheet/core.md`, `docs/cheatsheet/unix-power-mode.md`, `docs/ai/LLM_CONTRACT.md` (the "literal first parameter needs `open`" sentence) — all synchronized with *verified* behavior only, with `tools/gen_mcp_language_profile.py --check`, `tests/doc/test_semantic_doc_sync.py`, `tests/doc/test_state_anchors_and_registry_sync.py`, cheatsheet/SICP/doc-style sidecar tests as AGENTS requires.
  - Retained unchanged: closed `f(...) =: body` still rejects with `model-b-not-implemented` (`stage-closed-rejected`, `test_native_discovery_explicitly_rejects_closed_test`, `test_transitional_rejection_precedes_body_effects`).
- **How GREEN removes the staged claim:** the same commit that makes the 75 gated cases pass removes the name from the override; GA-2…GA-5 then prove `supported` is true.

---

## 7. G1 — recorded, **pending maintainer approval before GREEN** (not implemented, not approved)

**Proposed conservative invariant** (integration comment 6327837022 §4, Codex 6327597044 §3):

> The existing CLI entry selector may invoke `main` automatically only when the entire function group contains legacy identifier-header records and no two records share the same required-arity key. Otherwise it silently preserves source-result fallback without executing a selected record, matcher, guard or body.

Where the group is eligible, the legacy `main/1`-then-`main/0` convention is unchanged (M1–M5, exec). Explicit calls to `main` continue through ordinary function dispatch. No new diagnostic.

**Why it matters (read):** `_resolve_program_result` looks up `main_group.get(1)` then `get(0)` and invokes the record directly (it does not go through dispatch). Mixed groups first become user-constructible at GREEN (at base they fail to construct: pattern headers give `model-b-not-implemented`; fixed+rest same minimum gives `Duplicate function definition`). Without G1 the selector would pick a representative record — forbidden by rule 5.

**Concrete GREEN tests once approved** (shared cases, `requires: default_open_functions`; CLI-shaped with sibling `.genia`; each asserts top-level output + source result and **no** `main` output). Programs `print("top")` … `42`, argv chosen so that a pattern record would match if (wrongly) selected:

| ID (reserved) | Group | Expected under G1 |
| --- | --- | --- |
| `model-b-c-main-g1-mixed-main0-plus-pattern` (SC-MAIN-1) | legacy `main()` + pattern record of another arity | `top` / `42`; nothing selected |
| `model-b-c-main-g1-mixed-main1-plus-pattern` (SC-MAIN-2) | legacy `main/1` + pattern record of another arity | `top` / `42` |
| `model-b-c-main-g1-main1-plus-pattern-arity1` (SC-MAIN-3, both declaration orders: two IDs) | legacy `main/1` and a pattern arity-1 record | `top` / `42`; the legacy body does **not** run even though it would match |
| `model-b-c-main-g1-fixed-plus-rest-same-minimum` (SC-MAIN-4) | `main(a)` + `main(a, ..r)` | `top` / `42`; no representative pick |
| `model-b-c-main-g1-legacy-rest-plus-pattern-arity1` (SC-MAIN-5) | legacy `main(a, ..r)` + pattern arity-1 record | `top` / `42` |
| host-local `HL-9b` | selector never reads a lossy/derived index to choose among records; a pure legacy group with unique required-arity keys still selects `main/1` then `main/0` | structural |

Two reading divergences G1 closes: (G) whole-group vs (S) legacy-only-index selection, and the declaration-order dependence in SC-MAIN-3/5. G1 as recorded takes reading (G). **Until the maintainer confirms G1 (and, if (S) is preferred instead, states the per-arity and ordering rules), no GREEN may be accepted and no G1 case is created.** #1271 / #1272 (host-selected application lifecycle) own any eventual new `main` behavior and are not part of Slice C.

---

## 8. Unresolved items and corrections

### 8.1 Open decisions for the integration owner (do not block this package; block RED authorization where marked)

- **O-1 — gating consistency of the D5 breaking changes (blocks locking `requires` for the `own-*-rejected` cases).** P5 is ungated because it changes ungated ordinary behavior. P10/P11 (alias / imported-binding declaration → `function-declaration-not-owner`) are the same kind of valid→error change on ungated programs (exec: `a(x, y) = x + y` through an alias still succeeds today), yet the pre-flight plan gates them. Choose one rule: *breaking changes to ungated behavior are ungated* (then `own-local-alias-rejected` family are `R`, affecting the O-2 C++ question and the counts: ungated R +N, gated −N) or *gated by `default_open_functions`* (then the P5 rationale needs restating). The counts in §2.3 assume the plan as written (gated).
- **O-2 — ungated new cases and the C++ evidence path (blocks RED).** Every ungated new case (51 G + P5 = 52) is *applicable* to the C++ host, and known-gap entries are capability-scoped. If the pinned C++ adapter fails any of them (P5 is a prime candidate; some G diagnostics are Python text), `host-parity.yml` gets a non-zero failure-class count with no gap mechanism to document it, and RED cannot be merged without a policy decision. This session cannot build `genia-cpp`. **Pre-RED action requested of the integration owner:** run the pinned C++ adapter against the 52 ungated candidates (or authorize `add_repo` of `m0smith/genia-cpp` read access for a build), then decide for each failing ungated case: re-gate by a pre-existing capability it genuinely needs, treat as a separately tracked pre-existing C++ discrepancy (as the plan already does for the R20 duplicate-clause discrepancy), or drop from the shared set (host-local only). The list of the 52 is §3.3 (all rows with `requires` not containing `default_open_functions`).
- **O-3 — R4 design-text clarification (blocks locking file-mode duplicate oracles; §5.5).**
- **O-4 — B case `key-repeated-binders-distinct` (does not block the rest; §3.5).**
- **O-5 — `own-explicit-open-unchanged` program selection (§3.5).**
- **O-6 — U4 literal strings (13 L cases)** are byte-locked at the RED baseline, as already directed.

### 8.2 Contract conflicts found

- Design §3 / §13.5 "never filesystem paths" vs the existing file-mode entry label (R4, §5.5).
- Plan C-ERR sentence "no filesystem path in any new diagnostic" — narrowed (§5.3).

### 8.3 What was *not* verified here

The C++ side (no `genia-cpp` checkout/build): `host-parity.yml` C++ evidence and `docker-dev-environment.yml` C++ conformance were not run. The 128-case inventory has not been run as YAML; its Baseline column for **exec** rows was run through the in-process adapter on the stated program text, and the RED/GREEN columns are inferred. No full-suite pytest run was made (only the suites listed in §2.1); the loopback partition was not run.

### 8.4 Stale or incorrect facts corrected in the plan (verified)

1. RED plan header said "(revision 3)" while the body was revision 4; now revision 5.
2. "Slice B recorded 874 passed" → measured **901**.
3. C0 "design-approved, NOT implementation-authorized" → implemented, independently reviewed and merged (#1273).
4. `model-b-c-open-lambda-factory-distinct` source `mk(k) = (x) -> x + k` is a **grouped-body arm** (exec: `mk(1)` evaluates the arm and returns `2`), not a lambda factory; corrected source is `mk(k) { g = (x) -> x + k; g }` with oracle `[2, 3, true, false]` (exec).
5. `model-b-c-disp-p5-migration-fixed-clause` baseline is `Duplicate function definition: f/2` (not "valid today"); `model-b-c-disp-no-matching-function-new-group` baseline is `Duplicate function definition: f/1` (fixed+rest same minimum, P4), not `model-b-not-implemented`.
6. The pre-flight said C0 "NOT authorized"; the later authorization (6327837022) governs.

---

## 9. Gate checklist

- [x] Sources: `AGENTS.md`, `docs/process/run-change.md`, both Slice C process documents, issue #1269 and the cited PR comments were read in full. `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`, `docs/ai/LLM_CONTRACT.md`, the strategy documents and contract #1255 / design #1259 were consulted **by targeted search for the specific claims cited here**, not re-read line by line (stated, not hidden; the pre-flight revision 4 and its two independent reviews already carry the line-by-line reads).
- [x] `main` refreshed; C0 mechanism verified on merged `main`.
- [x] R1 matrix with exec baselines; RED/GREEN counts derived from the exact ID set; unsupported never counted as success.
- [x] R2 harness specification and 127 exact IDs with oracle status; blocked/ambiguous cases flagged.
- [x] R3 assertions GA-1…GA-12 and the vocabulary/override sequence.
- [x] R4 disposition applied; command- and file-mode examples (exec); design-text clarification identified.
- [x] R5 manifest edit specified, `tests/doc` rerun results recorded, intentional phase-guard changes listed.
- [x] G1 recorded, **explicitly pending**.
- [ ] Independent review of this package (requested).
- [ ] Integration-owner decisions: O-1, O-2, O-3 (before RED); G1 (before GREEN).
- [ ] Separate RED authorization — **not given by this document**.

## 10. Evidence index

Pre-flight and RED plan (this branch); #1270 comments 6327597044 (Codex final-delta), 6327837022 (integration gate); #1273 comments 6332339182, 6333124626, 6333148622, 6340512475, 6340735417; `tools/spec_runner/{runner,host_executor,capabilities,comparator,host_parity_gate}.py`; `hosts/python/protocol_adapter.py`; `src/genia/interpreter.py:513-528`; `.github/workflows/{ci,regression,github-hosted-runner-canary,self-hosted-runner-smoke,host-parity,docker-dev-environment,code-documentation,docs,validate-llm-instructions}.yml`; `pytest.ini`; `spec/manifest.json`; `spec/known_host_gaps.json`; scratch characterization of the exec programs (not committed): 82 program texts run through `hosts.python.adapter.run_case`, 6 CLI programs, 4 file-mode/command-mode diagnostic probes.
