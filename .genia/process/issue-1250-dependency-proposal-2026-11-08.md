# #1250 fresh acceptance dependency proposal — 2026-11-08

**PROPOSED — NOT APPROVED — DO NOT MERGE.** Author: Codex, single implementer.
Preparation only. Independent approval, activation, diagnostic smoke, G0/G1/G2,
CI GREEN, merge and closure are separate gates. None occurred in this task.

## Preflight / scope and authority

Issue: #1250. Branch: `issue-1250-fresh-dependency-baseline`, based on reviewed
infrastructure `9f96c6d9369bc29b87d6f63a97b3f7ce89bb7e05` (PR #1317).
Owner: maintainer m0smith; author Codex; independent reviewer pending.
[Preparation preflight](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6724799095).
Read current AGENTS.md, STATE/RULES/REPL README/README, relevant run-change,
preflight, token-efficient-agent and code-documentation rules; #1250 ledger,
registration, runner, workflow and offline tests; historical dependency evidence
and [November 8 independent review](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6724356675).
The user explicitly authorizes this combined preparation/evidence/code/test task;
no language contract or acceptance approval is inferred.

Includes one fresh solve and isolated installation, proposed data fixtures,
shared-lock provisioning design, offline guard tests, provenance and comparison.
Excludes acceptance, dispatch/CI, test oracles, executor A/#1316, merge, closure,
accepted-baseline updates and claims about resolving the historical failures.
Maturity: N/A, process/tooling only. Complexity: one fixture and one shared helper
rather than per-subject resolution. Risk: high evidence-integrity impact, bounded
code surface. Core invariants: literal digest equality, exact normalized freeze,
clean pinned subject, one fixture for every subject, closed approval gate.
Example: a valid unit fixture provisions a throwaway git subject; one-byte drift
raises before invoking uv. These are host-local preparation tests.

Portability (seven fields): Python-only CI tooling; C++ unaffected; portable
contract unchanged; Core IR unchanged; capability vocabulary unchanged; shared
semantic specs inapplicable (offline Python/OS guard tests); no new host gap.
MCP language-knowledge impact: none. STATE §0/§3 and RULES §8.5.1 remain unchanged,
as do book, cheatsheets and generated semantic facts: no Genia behavior changes.
Philosophy: preserves minimalism and explicit authority; no adapter semantics;
pattern matching unchanged; supports authorized R29 prerequisite infrastructure.
GO for authorized preparation only; NO-GO for activation/acceptance. Separate
independent maintainability and evidence/truth reviews remain pending.

## Proposed identity and provenance

Fixture: `tools/issue_1250/dependencies/proposed-2026-11-08/acceptance.lock`.
SHA-256: **`2bb0f5f5a5b073539ba0df6e92820a461d3cfb5364ca8951a99717b3c684a8bf`**.
55 universal-lock package records, including editable Genia and alternative
Python/platform packages; 42 non-editable installed distributions.

One solve: 2026-11-08T17:39:13.345732+00:00 through
17:39:14.510869+00:00. Linux Debian 13.6, kernel 6.18.57, x86_64, glibc 2.41.
CPython 3.12.14, Clang 22.1.3, executable
`/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3`.
uv 0.13.5, executable SHA-256
`8a70db72685b7138121bfcda71fa1a00cb709ed9f1fdc4ecf1dd871e8e167e52`.
Default `https://pypi.org/simple`; no UV_/PIP_ environment overrides or
user/system uv/pip configuration found, no cutoff or new dependency constraints.
Existing declarations retained: Python >=3.10, PyYAML>=6.0, dev minimums,
ruff==0.15.18 and the five tree-sitter pins. Build backend: hatchling.

Subject: disposable `git archive` of baseline
`0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5` at
`/workspace/1250-proposed/subject`. Candidate
`e3562f620020023ea39c44273068872d6bc73fe6` has byte-identical pyproject:
SHA-256 `cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc`
(blob `ecdc7c009fe1ada11d9ae1e43ca796677913fceb`). No candidate solve or install.

Commands, from that archive:

```sh
uv lock --no-python-downloads --python /opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3
uv sync --dev --locked --no-python-downloads --python /opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3
uv pip freeze
```

All returned 0. Installation only into its new `.venv`, 17:39:27.649768 through
17:39:29.545711 UTC. Post-sync lock digest unchanged. `provenance.json`, raw
lock/sync logs, `freeze.txt`, `proposal.json` and `freeze-diff.json` retain exact
facts; freeze normalization sorts/lowercases non-editable lines, as before.
The editable archive path differs naturally. No acceptance tests ran.

## Dependency differences

Against historical approved registration (42 entries): **no added names, no
removed names; 41 unchanged versions; one changed version**:

| Distribution | Historical approved | Proposed Python 3.12.14 |
|---|---|---|
| pymdown-extensions | 12.3 | 13.0 |

Historical literal lock digest remains
`27ca5a9328ba8641ce18078782c7edecdc8a753aa6b4fd3ca57932a66d49f291` (54 records
reported). Original lock bytes are unavailable. Therefore historical full graph,
marker, artifact/hash and byte differences are **unknown**, not asserted equal.
The fresh lock is byte-identical by SHA-256 to the hosted smoke lock reported in
[dependency handoff](https://github.com/m0smith/genia-2026/issues/1250#issuecomment-6723856264).
That comparison uses published artifact evidence, not a new independent download.

PyPI metadata read separately (no solve) confirms 12.3 requires Python >=3.10;
13.0 requires >=3.11.5 and its wheel uploaded 2026-11-08T14:20:27.756832Z.
Both declare the same direct dependencies: markdown>=3.6, pyyaml, and
pygments>=2.19.1 only with extra `extra`. MIT license expression unchanged;
artifacts not yanked at metadata fetch. Saved metadata includes wheel/sdist
URLs, hashes, requirements, licenses and upload instants.
Thus the known changed node replaces 12.3 with 13.0 at Python 3.12.14, without
new direct dependency names. Mkdocs-material's marker-selected pymdown edge
now selects 13.0 for >=3.11.5; older Python retains 12.3. This does not prove
that every other historical graph edge or marker is identical.

The full proposed adjacency/marker inventory is `graph.json`; all artifact URLs
and hashes are in the lock itself. Global forks: >=3.11.5, >=3.11 and <3.11.5,
and <3.11. Multi-version nodes in this proposal:

| Node | Versions and resolution markers |
|---|---|
| backrefs | 8.1 (`python_full_version < '3.11'`), 8.2 (`python_full_version >= '3.11.5'; python_full_version >= '3.11' and python_full_version < '3.11.5'`) |
| coverage | 7.16.2 (`python_full_version < '3.11'`), 7.17.2 (`python_full_version >= '3.11.5'; python_full_version >= '3.11' and python_full_version < '3.11.5'`) |
| markdown | 3.10.3 (`python_full_version < '3.11'`), 3.11.3 (`python_full_version >= '3.11.5'; python_full_version >= '3.11' and python_full_version < '3.11.5'`) |
| mkdocs-material | 9.7.7 (`python_full_version < '3.11'`), 9.8.1 (`python_full_version >= '3.11.5'; python_full_version >= '3.11' and python_full_version < '3.11.5'`) |
| platformdirs | 4.12.4 (`python_full_version < '3.11'`), 4.14.5 (`python_full_version >= '3.11.5'; python_full_version >= '3.11' and python_full_version < '3.11.5'`) |
| pymdown-extensions | 12.3 (`python_full_version >= '3.11' and python_full_version < '3.11.5'; python_full_version < '3.11'`), 13.0 (`python_full_version >= '3.11.5'`) |
| python-dateutil | 3.0.0 (`python_full_version < '3.11'`), 4.0.0 (`python_full_version >= '3.11.5'; python_full_version >= '3.11' and python_full_version < '3.11.5'`) |
| watchdog | 6.0.0 (`python_full_version < '3.11'`), 7.1.0 (`python_full_version >= '3.11.5'; python_full_version >= '3.11' and python_full_version < '3.11.5'`) |

Other conditional edges/platform packages remain explicit in `graph.json`.
No installation/conformance claim is made for non-3.12.14 or non-Linux forks.

## Risks, reproducibility and original failures

- New major pymdown release may change documentation rendering/extensions;
  changelog behavior, vulnerability status and documentation build were not
  audited here. No security-clean or compatibility claim follows from hashes.
- Historical graph cannot be reconstructed from the freeze. 54→55 records does
  not prove exactly one graph change. No historical lock was recovered/modified.
- Immutable bytes + artifact hashes remove a fresh project dependency solve
  during acceptance. Package availability, platform wheel selection and uv/Python
  builds remain external prerequisites. PyPI artifacts were not vendored.
- **Build-tool limitation:** pyproject's `hatchling` requirement is unpinned.
  `uv sync --locked` may independently resolve isolated PEP 517 build dependencies
  for editable Genia; these are absent from the 42-package installed freeze.
  The preparation installation used that default behavior; its hidden build
  inputs were not pinned. The prepared acceptance helper instead passes
  `--no-build-isolation`, which prevents uv from resolving build dependencies
  and fails if the backend is absent. Before activation, the reviewer must require
  separately pinned/preprovisioned build evidence (and a corresponding strict
  freeze), or approve a build-free strategy. A cold environment cannot currently
  provision successfully; the approval sentinel blocks execution meanwhile. Do not call this a completely
  hermetic build or approve it without addressing that limitation.
- Linux/Clang here differs from hosted Ubuntu/GCC and original executor context.
  No new cold-host baseline/candidate provisioning or acceptance was performed.
- Dependency drift explains the prior provisioning rejection only. Earlier
  independent source inspection found no pymdown/mkdocs/markdown reference in the
  original22 modules, architecture test, helper or launcher. That suggests limited
  relevance, not proof. No experiment here tests the original failures; no claim
  that the new baseline preserves, fixes or explains them is justified.

## Implementation and approval boundary

`provision()` now writes BLOCKED evidence and raises while
`APPROVED_DEPENDENCIES is None`. No CLI or environment override. Registration,
historical `LOCK`, original22 and all workflow dispatch guards are untouched.
The proposal file's status is `PROPOSED_NOT_APPROVED` and is never loaded by an
acceptance entry point. Changing that status alone cannot activate it.

The internal `provision_locked()` helper takes one fixture and exact registered
lock/pyproject/freeze evidence for baseline, candidate and both scratch paths.
It requires a clean pinned checkout, hashes fixture before installation, rejects
changed pyproject and conflicting/symlink existing uv.lock, copies exact bytes,
uses `uv sync --dev --locked --no-python-downloads --no-build-isolation`,
hashes again, saves normalized
freeze + missing/extra diff and checks strict list equality, then rechecks clean
subject identity. No `uv lock` call remains. Sync errors preserve logs/exits;
lock and freeze errors are distinct. This implements project-dependency guards;
the build-tool limitation above remains an explicit activation prerequisite.

## Validation and review plan

Offline fake-uv tests use a real throwaway git subject; no acceptance nodes.
Test-only RED against unmodified infrastructure: 13 failed, 42 deselected, all
for the missing preparation interface/approval gate. New implementation: 55
preparation tests passed; ruff passed. Final exact-head checks and logs are
recorded in the top-level handoff / `validation.json` beside the fixture.

Negative cases: missing fixture, tamper, conflicting existing lock, symlink,
changed declarations, changed/missing/extra installed package, failed sync,
rewritten lock, dirty subject; positive: shared fixture installs with locked
sync and clean checkout. Historical digest/freeze/original22 and inactive
proposal are tripwires. No portable semantics or acceptance credit from these
unit tests. No full regression, G0/G1/G2, hosted smoke, CI or signal test run.

Independent reviewer should inspect actual diff, literal hashes/manifests,
freeze normalization, graph unknowns, build-input gap and approval gate. If
accepted, a separate registration/activation change must preserve historical
metadata, register the reviewed new evidence, close the build-input gap and
obtain its own exact-SHA authorization before any diagnostic/acceptance run.

Rollback: revert this proposal's commits as one reviewed revert, restoring
prior fail-closed provisioning; fixture is additive. Never dispatch the old live
solver to manufacture historical approval. No historical ledger entry, run,
artifact, failure result or oracle is removed by rollback.

**Evidence preservation:** historical 22 failures and their original contexts,
registration, approved digest/freeze, prior repair/closeout records, smoke run
42497808332/artifact 13623249823 and all append-only ledger comments remain
unmodified. The new proposal supplies a different future comparison environment,
not replacement evidence for any past outcome. #1250 remains open; GREEN blocked.
