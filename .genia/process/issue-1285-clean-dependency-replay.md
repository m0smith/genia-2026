# #1285 — clean dependency replay and public runner gate

Date: 2026-10-27. Status: **PUBLIC-ONLY VERIFICATION / NON-AUTHORITATIVE**.
Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285).
Approved artifact: [merged #1292](https://github.com/m0smith/genia-2026/pull/1292).
Previous inventory: [draft #1291](https://github.com/m0smith/genia-2026/pull/1291).
This record supersedes their pending fresh-install finding with executed evidence;
it preserves the original lock and historical provenance records.

## Scope and preflight

Owner-authorized scope is a $0 public-only clean installation, existing public
verification, evidence and independent review of the actual proposed commit.
No benchmark run, hidden fixture/annex, oracle, candidate solution or paid service
is authorized. Branch: `issue-1285-clean-dependency-replay`. Author: Codex.

Latest AGENTS blob `b072beb55d22d5856d3d356d73c60704e04d197f`, STATE, RULES,
REPL README, README, issue discussion, merged #1292, draft #1291 and applicable
run-change/experiment process records were reviewed. Core guidance is unchanged;
STATE remains final language authority. Report branch starts from the #1292 merge
`7f47be9c802edb86af8b7225a85798d3ab69cf32`; **executed source is the older pin
below**, not that merge's working tree.

Maturity N/A, evidence/docs-only. Scope includes a clean public source export,
fresh dependency installation and public tests; excludes all language/runtime,
MCP/spec/CI/root-lock-policy changes. Portable behavior and both host implementations
remain unchanged. Verification strategy is hash checks, fresh-path assertions,
installed inventory/import-path inspection, existing checks and both regression
partitions. Failures are retained, not patched away. Examples below are process
commands. Complexity is recorded evidence, not a new platform. MCP knowledge
impact: none; no STATE/book/cheatsheet/registry changes. Drift risk is environment
and evidence accuracy, not semantics. Minimalism, explicit authority and the
validated-pipeline priority are preserved.

Seven portability fields: (1) STATE authority unchanged; (2) boundary is installed
Python environment, not language values/Core IR; (3) existing shared/pytest tests
are evidence, not new contracts; (4) Python reference host on Linux x86_64 only;
(5) no new capability/parity claim; (6) environment failures remain visible, no
new host-gap entries; (7) update process/provenance evidence only. Phases are
preflight, authorized verification, documentation and requested actual-commit
review; language contract/RED/runtime implementation phases are inapplicable.

## Exact baseline and isolation

| Property | Observed value |
|---|---|
| Executed source commit | `9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90` |
| Original/versioned lock SHA-256 | `02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8` |
| Lock bytes | 284838 |
| Source `pyproject.toml` SHA-256 | `cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc` |
| Actual installation/execution uv | **0.13.5**, matching the requested reference |
| uv executable SHA-256 | `8a70db72685b7138121bfcda71fa1a00cb709ed9f1fdc4ecf1dd871e8e167e52` |
| Actual interpreter | **CPython 3.12.15**, Clang 22.1.3 |
| Interpreter executable SHA-256 | `0886fb76ceec8ff568d23079b5da6342bb41675e216e11525d4d6a9e65988d10` |
| OS / kernel / machine | Debian 13.6 trixie / Linux 6.18.55 / x86_64, glibc 2.41 |
| Host Git | 2.52.0 |
| Outer resource allocation | CPU quota 200000/100000 (two aggregate CPUs), 8 GiB cgroup memory |
| pytest worker choice | `-n auto`, explicitly capped to 2 via `PYTEST_XDIST_AUTO_NUM_WORKERS=2` |

The original uploaded lock, versioned artifact and the other environment's live
ignored lock were never overwritten or regenerated. Only a copy was placed as
read-only `uv.lock` in a new disposable public export. Hashes were verified before
and after installation. All 2,457 tracked exported blobs matched the pinned Git
objects during independent inspection; final source equality is checked again.

The export initially had **no `.venv`, `.git` or package cache**. The package cache
path did not exist when installation started. No BENJAMIN files, virtual environment
or caches were accessed. The managed CPython interpreter from the preceding public
task was reused as a base interpreter, not as a project environment; no base
site-packages were inherited. User site was disabled, ambient PYTHONPATH/PYTHONHOME,
VIRTUAL_ENV/CONDA_PREFIX and UV project-selection variables were removed.
Explicit UV project/cache paths and `--no-config` prevented reuse of project/user
uv configuration. Runtime proxy/CA/authentication guard settings were preserved.
Only the listed variables were sanitized; this was not a completely allowlisted
or hermetic host process environment. Host Git, shell, libc, kernel and permitted
execution facilities remain external prerequisites to freeze and record.

uv 0.13.5 itself was downloaded into a separate disposable target using existing
uv 0.12.23 `pip install --no-cache --target ... 'uv==0.13.5'` with CPython 3.12.15.
The older uv bootstrapped the tool only; it did not install the project. This used
public package-network access, not an existing uv project environment or cache.

## Fresh installation — PASS

Exact installation argv, with task-specific absolute paths represented by variables:

```bash
UV_CACHE_DIR="$replay/package-cache" \
UV_PROJECT_ENVIRONMENT="$replay/source/.venv" \
PYTHONNOUSERSITE=1 PYTHONHASHSEED=0 TZ=UTC UV_PYTHON_DOWNLOADS=never \
"$uv_0135" --no-config sync --locked --no-python-downloads \
  --python "$python_31215" --default-index https://pypi.org/simple --link-mode copy
```

Executed from the disposable source root. **Exit 0; 6.357557 seconds captured
wall time.** uv reported `Creating virtual environment at: .venv`,
`Resolved 51 packages`, `Prepared 44 packages`, `Installed 44 packages`.
Public network access was used for downloads and isolated build dependencies;
the fresh package cache was populated by this run. This is not an offline install.
`--locked` checked freshness without changing the approved lock; no unconstrained
resolution/update or forced lock replacement was used.

The full 44-distribution inventory is versioned in
[clean-replay-evidence.json](../experiments/issue-1285/dependencies/clean-replay-evidence.json).
All installed name/version pairs exist in the approved lock. The universal lock
has 51 entries, including alternative markers/unneeded distributions; 44 installed
packages is not a missing-install count. Inventory confirmed the new `.venv` prefix,
`site.ENABLE_USER_SITE == false`, and no external `site-packages` import path.
The base interpreter's standard library and the exact editable source are expected.

Important limitation: `pyproject.toml` build-system requirement is unpinned
`hatchling`. Additional metadata observed in the fresh build cache was hatchling
1.32.4, editables 0.6, tomlkit 0.15.2 and trove-classifiers 2026.9.21.13. Their
metadata fingerprints are recorded, **not misrepresented as complete wheel hashes
or a complete pinned build environment**. This install succeeded without inherited
dependencies, but a hermetic build/toolchain freeze remains future work.

## Public verification and the Git metadata prerequisite

Every command used the new environment through:

```bash
"$uv_0135" --no-config run --offline --no-sync COMMAND...
```

No further synchronization/install occurred. The explicit clean UV project path,
disabled user site and sanitized Python variables remained in effect. Both pytest
partitions were run with approved local loopback socket access, not skipped for
socket restrictions. Tests/runtime were never altered to obtain a pass.

| Existing public check | Result | Exit | Captured wall seconds |
|---|---|---:|---:|
| `python tools/validate_llm_instructions.py` | PASS, instruction validation passed | 0 | 0.020679 |
| `python tools/gen_function_docs.py --check` | PASS, function reference up to date | 0 | 0.283332 |
| `python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage` | PASS, 24 files/286 doc strings, 0 errors/0 warnings | 0 | 0.097280 |
| `python -m genia.interpreter examples/validated_pipeline_demo.genia` | PASS execution, native clean records/diagnostics | 0 | 0.137732 |

The documented demo emitted 863 stdout bytes and the existing 200-byte nonfatal
runpy warning on stderr. It is a public example execution, **not** ci-results.v1
benchmark wire-output validation. Captured stream hashes are in the evidence JSON.

### First attempt: plain archive — FAIL retained

| Command after the uv prefix | Counts | Exit | Captured wall seconds |
|---|---|---:|---:|
| `pytest -n auto -q -m 'not loopback'` | 6387 passed, 60 skipped, 478 failed, 238 errors | 1 | 122.567683 |
| `pytest -n auto -q -m loopback` | 31 passed | 0 | 4.483244 |

The plain archive has no Git revision metadata. The dominant observed failure
was `launcher: unable to determine the repository revision`; additional failures
explicitly reported `git rev-parse HEAD` exit 128. Existing
`hosts/python/mcp_launch.py` and spec revision plumbing require the repository
revision. These executed failures are retained; they are not labeled blocked,
deleted, attributed blindly to all dependencies or converted into skips.

### Environment correction: independent public Git metadata

Without editing any source/test, lock, installed package or project dependency,
the same clean export received newly initialized Git metadata populated from the
public repository, anchored to the exact source commit:

```bash
git init --initial-branch=replay
git fetch --depth=1 https://github.com/m0smith/genia-2026.git \
  9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90
git reset --mixed 9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90
git rev-parse HEAD
git status --short
```

HEAD matched exactly; status was clean and lock/metadata hashes were unchanged.
No checkout state, history, configuration or dependencies were copied from a live
project environment. This is an explicit environment correction, not a language,
MCP or test change. A source archive alone is insufficient for this full test set.
Both full partitions were rerun because this diagnosed prerequisite changed.

### Corrected full partitions — one reproduced failure

| Command after the uv prefix | Counts | Exit | Captured wall seconds |
|---|---|---:|---:|
| `pytest -n auto -q -m 'not loopback'` | 7102 passed, 60 skipped, 1 failed, 0 errors | 1 | 420.776606 |
| `pytest -n auto -q -m loopback` | 31 passed | 0 | 4.349044 |
| Combined corrected full suite | **7133 passed, 60 skipped, 1 failed** | FAIL | 425.125650 total |

The remaining failure is
`tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_discover_probe_launch_followed_by_a_session_launch_leaves_nothing_behind`.
It asserts `a launch left processes behind`. One unchanged targeted rerun with
`pytest -q --showlocals` reproduced it: **1 failed**, exit 1, 60.458684s wall
(pytest reported 60.29s). That diagnostic is not added to the full-suite counts.
No deadlines, skip rules, tests or runtime were altered and no repeated-until-green
suite was attempted. The reproduction confirms a remaining cleanup issue in this
execution environment; it does not establish which layer is responsible.
After the targeted failure, a read-only `/proc` check confirmed one captured
stable process identity still existed in zombie state `Z`, reparented to PID 1;
the other captured identity had disappeared. The test helper explicitly counts
unreaped zombies as existing. This records the observed symptom, not proof of
which component should be changed. No process/controller/runtime was modified.

The owner-reported BENJAMIN context is 7134 passed/60 skipped/0 failures in
550.48s. It is not a required count, performance target or independent host
attestation. Platform/resource/worker-count and Git-state differences must remain
visible; timings are not a Genia-vs-Python comparison. The corrected suite's
one-pass difference is the retained cleanup failure, not removed or added test
coverage. The Git correction eliminated the broad archive-only failures in this
rerun; no claim is made that dependencies caused the residual failure.

## Repeatable public procedure

Use an artifact checkout containing the merged #1292 lock only to read the
approved bytes. Do not sync or replace its live ignored root lock. The two exact
tool executables below must already be provisioned and version-checked; no silent
fallback interpreter/uv is permitted.

```bash
set -euo pipefail
artifact_checkout=$(pwd)
lock="$artifact_checkout/.genia/experiments/issue-1285/dependencies/BENJAMIN.lock"
replay=$(mktemp -d /tmp/genia-1285-clean-replay.XXXXXX)
export UV_CACHE_DIR="$replay/tool-cache"
test "$(sha256sum "$lock" | cut -d ' ' -f 1)" = \
  02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8
uv_0135=$(command -v uv)
test "$("$uv_0135" --version | cut -d ' ' -f 2)" = 0.13.5
python_31215=$("$uv_0135" python find --offline --no-python-downloads 3.12.15)
test "$("$python_31215" -c 'import platform; print(platform.python_version())')" = 3.12.15
mkdir "$replay/source"
git archive 9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90 | tar -x -C "$replay/source"
cp "$lock" "$replay/source/uv.lock"
chmod 444 "$replay/source/uv.lock"
cd "$replay/source"
test "$(sha256sum pyproject.toml | cut -d ' ' -f 1)" = \
  cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc
git init --initial-branch=replay
git fetch --depth=1 https://github.com/m0smith/genia-2026.git \
  9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90
git reset --mixed 9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90
test "$(git rev-parse HEAD)" = 9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90
test ! -e .venv
test ! -e "$replay/package-cache"
unset VIRTUAL_ENV CONDA_PREFIX PYTHONPATH PYTHONHOME UV_PROJECT UV_PYTHON UV_WORKING_DIRECTORY
export UV_CACHE_DIR="$replay/package-cache" UV_PROJECT_ENVIRONMENT="$replay/source/.venv"
export PYTHONNOUSERSITE=1 PYTHONHASHSEED=0 TZ=UTC UV_PYTHON_DOWNLOADS=never
export PYTEST_XDIST_AUTO_NUM_WORKERS=2
sha256sum uv.lock pyproject.toml > "$replay/before.sha256"
"$uv_0135" --no-config sync --locked --no-python-downloads \
  --python "$python_31215" --default-index https://pypi.org/simple --link-mode copy
sha256sum -c "$replay/before.sha256"
"$uv_0135" --no-config run --offline --no-sync python tools/validate_llm_instructions.py
"$uv_0135" --no-config run --offline --no-sync python tools/gen_function_docs.py --check
"$uv_0135" --no-config run --offline --no-sync python tools/lint_doc.py \
  --scan-dir src/genia/std/prelude --require-coverage
"$uv_0135" --no-config run --offline --no-sync python -m genia.interpreter \
  examples/validated_pipeline_demo.genia
"$uv_0135" --no-config run --offline --no-sync pytest -n auto -q -m 'not loopback'
"$uv_0135" --no-config run --offline --no-sync pytest -n auto -q -m loopback
sha256sum -c "$replay/before.sha256"
```

These commands stop on error. For retaining both partition results on failure,
capture each exit separately and still run the second partition. The task did so;
exact argv, stdout/stderr hashes, counts and monotonic durations are versioned in
the adjacent evidence JSON. Raw logs remain local scratch; they contain only
public test data but local paths require inspection before broader sharing.
No cache deletion, root lock overwrite or dependency-policy edit is necessary.

## Assessment, review and next gate

| Dimension | Classification | Evidence / limit |
|---|---|---|
| Lock integrity | PASS | Approved hash preserved before/after install and verification |
| Lock-to-source compatibility | PASS | Pinned source metadata verified; reference uv `sync --locked` accepted without rewrite |
| Fresh dependency installation | PASS | New absent cache/venv, actual 44-package install, isolated import-path checks |
| Public documentation checks | PASS | Three existing validation commands exit 0 |
| Public full regression | FAIL | Corrected full partitions: 7133 pass/60 skip/1 failure; targeted cleanup failure reproduced |
| Validated-pipeline demo | PASS | Documented interface exit 0; existing warning disclosed; not benchmark validation |
| Immutable complete environment/image replay | NOT TESTED | No image/backend artifact freeze or second independent complete replay attempted |
| Public frozen-runner preparation gate | NO-GO | Resolve/attribute reproduced lifecycle cleanup failure before declaring this public verification gate passed |
| Hidden/oracle/candidate/comparison gates | NO-GO | Outside authorization; custody and independent grading prerequisites unchanged |

The initial archive-only run is also **FAIL**, not BLOCKED. No required package
artifact or reference tool was unavailable, so fresh installation was not BLOCKED.
The recorded outer limits are not evidence of equal future candidate controls.

Independent inspection during execution confirmed the source blobs, lock and
44-package inventory, and draft review found no blocking wording/command issue.
Final actual-commit review is a separate requirement: its result and reviewed
commit identity belong in the PR/issue handoff. The earlier draft review is not
represented as review of the final regression result or committed payload.

Full environment freezing remains unverified: no immutable image/OS package lock,
full backend artifact pins, offline wheelhouse/reinstallation, second independent
image replay, equal future worker resource limits, capture overflow enforcement
or candidate-principal isolation/recovery test was established. A fresh package
environment is not a security boundary and public test success is not trial approval.

Only existing workspace compute, public package downloads and repository tools
were used. No paid infrastructure, larger runner, model API, artifact storage,
subscription or billing setting was provisioned/changed. No CI configuration was
edited and no workflow was manually dispatched; a requested PR may trigger the
repository's existing standard public CI.
Budget remains $0 incremental spending; invoice totals and existing host costs
were not audited. No private material was accessed, generated or transferred.

All #1285 hidden-material/oracle/candidate/comparative-trial NO-GO boundaries
remain in effect independently of the public-only runner-preparation verdict.

**Single next recommended action:** investigate the reproduced probe/session
process-reaping failure and propose a separately reviewed environment or lifecycle
remediation supported by evidence. Do not freeze the runner as verified, weaken
the test or begin benchmark work to work around it.
