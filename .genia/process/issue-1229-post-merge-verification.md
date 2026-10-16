# Issue #1229 — post-merge verification (F2/P2)

Phase: verification/evidence only. No production code, spec, or root-authority documentation was changed.
Executed 2026-10-16 UTC. Verdict: see "Independent review".

**Scope note.** #1229 was already closed (2026-10-16T14:28:39Z, "completed", via #1248) when this verification ran.
This report is a retroactive evidence link-back for a closed tracker, not a closing condition.

**Interpreters.** The supported range is Python >= 3.10 (`pyproject.toml`). Local full-regression runs used Python 3.12.3
(primary) and Python 3.10.20 (supplementary, added after review finding 1). Fast CI uses py3.14.

## 1. Exact merged state

| Item | Value |
|---|---|
| Integration PR | #1247, merged 2026-10-15T22:00:32Z |
| Merge commit | `22de326aab192a10f54a82ce40a318cb899c09d6` |
| Merge-commit tree | `bef5310ff604192cba5117146d1583d39685b2b9` |
| Parents | `1261ae27…` (main) and `02bbc489…` (candidate head) |
| Ancestry | `22de326a` is an ancestor of `origin/main` (verified) |
| Current `origin/main` | `e551021a713af555cb67a6aea37891e438fa9185`, tree `08105169911ba62817a4288fc1455ff8c12c1278` |

Four distinct trees must not be conflated:

1. PR candidate head `02bbc489` (pull_request CI, run 38811308116 et al.). GitHub's synthetic merge ref
   (`refs/pull/1247/merge`) is no longer fetchable, so its tree could not be compared directly.
2. The actual merge commit `22de326a` — the tree #1229 is about.
3. Later `main` commits (below).
4. Local runs in this task: clean `git worktree` checkouts of `22de326a` and `e551021a`.

`git diff 02bbc489 22de326a` is six documentation files only (`docs/ai/LLM_CONTRACT.md`,
`docs/process/{code-maintainability-review,llm-prompts,run-change}.md`,
`docs/strategy/{release-roadmap,roadmap/sequence}.md`), identical to main's own delta since the merge base. No
`src/`, `spec/`, `tests/`, `tools/`, `apps/`, or workflow file differs, so runtime-level pre-merge evidence is
tree-equivalent for code; it is not tree-identical, and this report does not rely on it for the matrix below.

### Later `main` commits (first-parent, after `22de326a`)
| Merge | Content | Invalidates 22de326a evidence? |
|---|---|---|
| #1248 `6e6cc56` | roadmap/tracking docs | No (docs) |
| #1252 `5852278`, #1253 `7368e20` | roadmap gate, #1249 preflight draft | No (docs) |
| **#1254 `e551021`** | **`feat(scope): remove module-to-entry compatibility fallback (#1230)`** | **Yes for runtime.** Changes `src/genia/{builtins,environment,evaluator}.py`, deletes `module_fallback.py`, removes the strict-mode CI steps, removes fallback-only tests and adds module read-isolation tests, adds 2 shared spec cases (one error, one isolation) and edits 1 (829 -> 831), edits STATE/RULES/README, `docs/architecture/python-host-injection.md`, the F2 design contract, `docs/design/README.md` and `roadmap/sequence.md`. |

So 22de326a evidence describes the tree that #1229 closed over; it is not evidence for current `main`.

## 2. Evidence matrix

"Local" = executed in this task, Python 3.12.3, 4 cores, `uv run`, clean worktree. "CI" = historical GitHub Actions
result for the same SHA, reused (not re-executed).

| Requirement | Tested SHA/tree | Result | Source | Remaining gap |
|---|---|---|---|---|
| Default full regression, non-loopback (includes slow tests; `-m "not loopback"`) | `22de326a` / `bef5310f` | **6975 passed, 60 skipped, 0 failed** (402.86 s) | Local | 60 skips not individually classified here |
| Strict full regression, non-loopback (`GENIA_STRICT_MODULE_SCOPE=1`) | `22de326a` / `bef5310f` | **6975 passed, 60 skipped, 0 failed** (395.59 s) | Local | same |
| Default loopback | `22de326a` | **31 passed** | Local | none |
| Strict loopback | `22de326a` | **31 passed** | Local | none |
| Shared specs, default | `22de326a` | **829/829**, 0 failed/invalid | Local | none |
| Shared specs, strict | `22de326a` | **829/829**, 0 failed/invalid | Local | none |
| Nightly multi-Python Regression workflow | `22de326a` (run 38900800273, `schedule`, attempt 1, 2026-10-16T12:28Z) | **FAILURE**: job "Compatibility (py3.10)" failed `tests/unit/test_f2_p2_corrections.py::test_r16_event_set_without_lock_raises_type_error_and_never_grants_the_read` with `AttributeError: __enter__` (`src/genia/environment.py:293`); `--maxfail=1` stopped it at 1 failed / 1717 passed / 35 skipped, so py3.10 loopback and specs were skipped. Success: py3.11, 3.12, 3.13, 3.14 (non-loopback, loopback, specs), py3.15 (experimental), full Python protocol conformance (py3.14), slow unit/spec/demo (py3.14). | CI | Classified below (section 5); py3.10 coverage gap closed locally by the supplementary rows below |
| Python 3.10 full regression, non-loopback | `22de326a` | **6974 passed, 1 failed, 60 skipped** (428.34 s); the one failure is the test above | Local (3.10.20) | Genuine deterministic failure on the supported minimum interpreter, in a fallback-only test later removed by #1254 |
| Python 3.10 loopback / specs | `22de326a` | 31 passed / 829/829 | Local (3.10.20) | none |
| Isolated reproduction | `22de326a`, py3.10.20 | Test fails alone (`AttributeError: __enter__`); passes on 3.12 in the full run | Local | none |
| Python 3.10 full regression + loopback + specs | `e551021a` | **6946 passed, 60 skipped, 0 failed**; loopback 31; specs 831/831 | Local (3.10.20) | none |
| Fast tests (non-slow) default+strict, loopback, specs | `22de326a` | success (run 38814088066, job "Fast tests (py3.14)", all 12 steps incl. strict steps) | CI | partition is *not* full regression; counts not retrieved (job-log tails only showed cleanup) |
| Documentation truth | `22de326a` | `tests/doc` ran inside full regression (above); CI "Docs" run 38814088189 (strict mkdocs), "Validate LLM instructions" 38814088007 success; CI "Docs coverage" job success; cheatsheet job success | Local + CI | none |
| Documentation tooling | `22de326a` | local: `ruff check .` clean; `gen_function_docs.py --check` up to date; `lint_doc.py --scan-dir src/genia/std/prelude --require-coverage` 286 `@doc`, 0 errors/0 warnings; `gen_mcp_language_profile.py --check` exit 0; `GENIA_STATE.md` 42,864 words (< 43,000 cap) | Local | none |
| Maintained-code documentation | `22de326a` | local: `python -m tools.code_documentation --base-ref 1261ae27` → 9573 records, 2819 legacy gaps, 1 classified exclusion, **0 errors**; `test_code_documentation.py` 26 passed; CI "Code documentation" run 38814088177 success | Local + CI | legacy gaps are pre-existing baseline debt |
| Host parity (Python vs C++) | `22de326a` | CI run 38814088096 success; C++ build restored from cache ("Configure and build C++ host" skipped, "Restore exact C++ build" ran), so the C++ commit actually exercised is not identified here. The gate covers only cases the C++ host supports; unsupported cases are not parity. | CI | **Exact total/pass/unsupported counts not independently retrieved**: artifact download was blocked by the sandbox proxy (HTTP 403, not worked around) and no C++ host is built locally. Last counts seen are historical, pre-merge stack: 825 total / 263 pass / 562 unsupported / 0 failure-class (P2-G record, C++ `bb7c7474`). Unsupported is not a pass. |
| Official MCP SDK acceptance | `22de326a` | CI job "MCP stdio client acceptance (official SDK)" success (run 38814088066) | CI | **Local full runs skipped the 6 official-client tests** (`test_r28_mcp_official_client.py`: Node harness not installed). SDK acceptance therefore rests only on that CI conclusion; the pass count was not retrieved (historical stack figure: 42 passed). |
| MCP security / strict scope | `22de326a` | MCP security/protected-value tests are ordinary pytest modules inside the full default and strict runs above (no marker excluded them) | Local | not a separate named gate; official-client coverage is CI-only (see SDK row) |
| VS Code extension | `22de326a` | CI job success | CI | none |

### Current `main` (e551021a, tree 08105169), supplementary
| Check | Result | Source |
|---|---|---|
| Full non-loopback | 6946 passed, 60 skipped, 0 failed (403.09 s) | Local |
| Loopback | 31 passed | Local |
| Shared specs | 831/831 | Local |
| Strict mode | Not applicable: `GENIA_STRICT_MODULE_SCOPE` and its CI steps were removed by #1254 | — |
| CI/parity/code-doc/validate-LLM runs for `e551021` | success (CI 38935727045, parity 38935727013, code-doc 38935726960, validate 38935726970); "Docs" run 38935726973 was **cancelled**, not failed | CI |

The suite-wide difference (6975 -> 6946) is a net -29, not a 1:1 deletion count: fallback-only tests were removed and module
read-isolation tests were added. It was not individually audited.

## 3. Commands executed (local)

```
git worktree add /tmp/claude-0/wt-22de326 22de326a        # and e551021a for supplementary
uv sync --dev
uv run pytest -n auto -q -m "not loopback" -p no:cacheprovider
uv run pytest -n auto -q -m loopback -p no:cacheprovider
uv run python -m tools.spec_runner
# repeated with GENIA_STRICT_MODULE_SCOPE=1 on 22de326a
# supplementary, UV_PROJECT_ENVIRONMENT=/tmp/claude-0/venv310, --python 3.10, on 22de326a and e551021a:
uv run --python 3.10 pytest -n auto -q -m "not loopback" -p no:cacheprovider   # also -m loopback, and tools.spec_runner
uv run ruff check .
uv run python tools/gen_function_docs.py --check
uv run python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage
uv run python tools/gen_mcp_language_profile.py --check
uv run python -m tools.code_documentation --base-ref 1261ae27… --inventory <scratch>
uv run pytest -q tests/unit/test_code_documentation.py
```

Raw logs are retained for the pytest/spec runs only; the ruff, `gen_function_docs`, `lint_doc`, `gen_mcp_language_profile`,
`code_documentation`, `test_code_documentation` and STATE word-count results were read from terminal output and are
not independently re-verifiable from retained logs.

A first `lint_doc.py --require-coverage` call without `--scan-dir` raised `IndexError` (wrong invocation by this task,
not a repository defect); re-run with the CI arguments passed. No test was retried; no failure occurred.

## 4. Historical evidence reused, and why

- CI results for `22de326a` (all runs share head SHA `22de326aab…`, `event: push`, `run_attempt: 1`): reused for
  host parity, official MCP SDK, VS Code, mkdocs strict build, cheatsheets and workflow-level doc checks, because
  those need infrastructure not available locally (C++ host, Node, locked MCP client) and the CI SHA is the exact
  merge commit.
- Pre-merge stack figures (6974/6975-style counts, 829 specs, 42 SDK, 825-case parity) quoted in #1229/#1247 are
  **not** used to satisfy any row; they are cited only where a count could not be retrieved.

## 5. Failure and retry history

- **In this task's Python 3.12 runs:** no test failed, no step was retried, no skip list was edited.
- **Scheduled Regression run 38900800273 on `22de326a` failed** (py3.10 job, see matrix). Root cause, established from the CI log
  and reproduced in isolation on Python 3.10.20: `claim_fallback_event` (`src/genia/environment.py:293`) enters a missing lock with
  `with self._fallback_lock:`; on Python 3.10, `with None:` raises `AttributeError: __enter__`, whereas Python >= 3.11 raises
  `TypeError`, which the test and the method docstring expect. This is a deterministic compatibility defect in a fallback-only code
  path and test, not a flake and not a one-off: it reproduced on 3.10.20 locally, and the full local 3.10 run on the same tree shows
  it as the only failure (6974 passed / 1 failed). It was removed along with the fallback by #1254 (`e551021a`), where the 3.10 full
  regression is clean (6946 passed). No production code was modified by this task. The failure is a real defect of the merged tree on
  a supported interpreter; its consequence is limited to the removed code path.
- No retries were performed. Tool-access limits (artifact download 403; job-log tails returned only cleanup lines) are in the matrix.
- Known load flake, not observed in these runs: #1254 reports `test_r28_mcp_stdio_lifecycle[SIGINT]` timing out (60 s `uv run`
  subprocess) under `-n 4` load, also on a pristine baseline. It did not occur in any run recorded here.

## 6. Findings

- **F-1 (process, needs maintainer attention): #1230 premise has changed.** The fallback first landed 2026-10-15T22:00:32Z
  (#1247) and #1254 removed it at 2026-10-16T16:55:36Z (about 19 h later), well before the 2026-12-14 checkpoint. #1230's body
  still reads "Status: implemented and active on main", it is still open, and its last comment is dated 2026-10-15. #1254's body
  says "Merging satisfies the R29 hard gate in #1230. #1230 should close on merge", but #1230 neither closed nor has a removal
  record. This task did not edit, close or re-own #1230 or #1238; the maintainer should reconcile #1230.
- **F-2: strict-mode regression coverage ends at `22de326a`.** Strict mode no longer exists on `main`; strict evidence
  applies only to the merged F2/P2 tree.
- **F-3: counts not retrieved** for CI host parity and SDK acceptance (see matrix); results are CI conclusions only.
- **F-4: the 60 skips (identical across default, strict, 3.10 and current-main runs) are environmental**, classified from an independent
  `-rs` re-run by the reviewer: 34 `tests/doc/test_state_anchors_and_registry_sync.py` (non-text evidence verified elsewhere);
  18 `test_p9_wit_retrieve_roundtrip.py` (WIT component / wasmtime unavailable); 6 `test_r28_mcp_official_client.py` (Node harness not
  installed); 1 `test_r28_release_gate.py`; 1 `test_state_migration_map.py`.
- **F-5:** the "Docs" run on `e551021` was cancelled (not failed); not re-run here. Its strict mkdocs build is
  not part of this report's `22de326a` conclusion.
- No dogfooding (#1226) observation recorded: no eligible Genia computation was considered or executed.

## 7. Independent review

(see appended section)

## 8. Recommendation

(see appended section)
