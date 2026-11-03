# #1285 — public frozen-runner preparation and design gate

Date: 2026-11-03. **PROPOSED / PUBLIC ONLY / NON-AUTHORITATIVE.**
Agent: Codex. Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285).
Report baseline: `0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5` (merged #1295).
Branch: `issue-1285-public-frozen-runner`.

**NO-GO for calling a public runner frozen or verified.** Original lock/source
identity passes. A candidate base manifest and seven candidate backend wheels
were inspected without installing or executing them. No image was pulled,
built, run or published. Independent **Claude Code review is BLOCKED**: neither
`claude` nor `claude-code` is on PATH, and no authenticated Claude review route
is supplied. No substitute Codex review is represented as Claude review.

## Scoped preflight and authorization

1. Identity/classification: required infrastructure, release-independent public
   reproducibility for the validated-pipeline experiment; owner is the repository
   maintainer. Includes provenance verification, public metadata/artifact inspection,
   dependency-gap inventory, runner design and direct BENJAMIN instructions.
   Excludes benchmark material, oracle/candidate code, comparisons, R29 work,
   root dependency-policy changes, CI edits/dispatch, merge and issue closure.
2. Authority: latest AGENTS blob `e913e9d093f5913a4797173f56524c80380b815c`;
   STATE remains final authority. Read authority navigation and material sections
   in STATE/RULES/REPL/README, roadmap, killer workflow, Human–AI strategy,
   run-change, preflight template, LLM wrapper/system/contract, token-efficient
   workflow, execution-realization and MCP stdio guidance. Read all returned #1285
   comments, #1292/#1293/#1295 metadata/discussions and committed evidence, and the
   public #1286 design at `4ee8713ecfa391e1a8f74610b2e1dcad745d0779`.
   No private annex was sought. Current guidance differs from the older handoffs;
   their old AGENTS fingerprint is not reused as a current-instructions check.
3. Maturity: N/A, process/data only. Proposed controls are not implemented language
   guarantees. Registry discovery is not authority or a security boundary.
4. Contract/implementation: existing Python reference-host semantics unchanged;
   C++ unaffected. Complete immutable runner and direct BENJAMIN replay unverified.
5. Verification: Git/byte/hash equality, TOML/JSON parsing, read-only Docker info,
   registry manifest digest, downloaded wheel hashes and declared requirements,
   relevant instruction/profile checks, shell syntax, links and diff scope.
   Missing pins or failed controls block acceptance; no retries to erase failures.
6. Examples: shell/process instructions only; no Genia program or benchmark input.
7. Complexity: a single scoped runner proposal and public evidence; no new
   supervisor, dependency platform or alternate semantic conformance mechanism.
   Existing development image is unsuitable as-is: Python 3.14.7/uv 0.12.18,
   moving apt inputs and a broad C++ toolchain differ from this pairing.
8. Cross-file impact: this record, adjacent public-runner evidence/manifest, and
   a forward link from the earlier replay record. STATE/RULES/REPL/README, book,
   cheatsheets, shared specs and generated MCP knowledge remain accurate without
   edits: this task changes no implemented behavior or language example.
   MCP language-knowledge impact: none. Evidence accuracy is the material drift risk.
9. Philosophy: minimalism YES; explicit behavior YES; semantics outside adapters
   YES; pattern-first model preserved YES; validated-pipeline evidence relevance YES.
10. Phase plan: authorized public preparation/preflight/design, then STOP for
    independent Claude Code review and design acceptance before build implementation.
    AGENTS says agents must not “mix design and implementation in a single step”;
    run-change requires separate design/implementation phases. The owner explicitly
    requests a proposal when an additional design gate is needed. Historical
    public-preparation GO is not acceptance of this new backend/OS/build design.
    Language contract/RED/runtime implementation and code maintainability phases
    are N/A here: no implementation is added. Future build code needs its applicable
    tests, maintainability review, docs and independent evidence audit.
11. Seven portability fields: (a) STATE authority unchanged; (b) boundary is public
    Linux execution infrastructure, not Genia values/Core IR; (c) existing tests
    provide future evidence, no new semantic oracle; (d) Python/Linux amd64 only,
    no new capability vocabulary; (e) no Python/C++ parity claim; (f) no new host
    gap/skip policy; (g) synchronize experiment evidence only. No portable semantic
    change; cross-host implementation sequencing is N/A.
12. Decision: preparation findings publishable with a **BLOCKED** review handoff;
    frozen-runner acceptance NO-GO. Original pair is already approved; no new
    approval is requested merely to read or preserve it. Build design acceptance
    and missing artifact pins remain prerequisites to implementation.

## Verified pair and source drift

| Item | Exact identity |
|---|---|
| Approved executed-source pin | `9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90` |
| Original BENJAMIN lock SHA-256 | `02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8` |
| Original lock length | 284838 bytes; 51 entries / 47 names |
| Paired pyproject SHA-256 | `cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc` |
| Target interpreter / uv | CPython 3.12.15 / uv 0.13.5 |

Versioned lock bytes equal the baseline Git blob and the approved provenance hash.
No root `uv.lock` was written, synchronized, regenerated, force-added or deleted.
Metadata compatibility/fresh install are historical #1292/#1293 evidence, not
newly executed installation checks in this task.

The report baseline and approved source have identical pyproject blobs, but
**341 changed paths, including 14 in `src/`**. Their `src/genia` tree IDs are
`491de3eec4aadf5f91fcd764183eec32fb6ae5b7` and
`3119817ef9b91c0235868677a939a8dd232ca3a3`, respectively. The #1295 reviewed
branch at `b25494f39e86d77857ccdb9fce911a0d02e56404` has the latter runtime tree
and the corrected fixture; its merge into later main does not make those source
trees identical. **Proposal: preserve the approved original pair with no source
overlay**, and test proper init supervision there. The old fixture remains part
of that source and must pass unchanged. A fixture overlay or newer source would
be a separately identified/reviewed pairing, not original-pair replay.

## Remaining dependencies and candidate evidence

[preparation-evidence.json](../experiments/issue-1285/public-runner/preparation-evidence.json)
records exact observations, commands, hashes, wheel URLs/metadata and limitations.
[base-amd64.manifest.json](../experiments/issue-1285/public-runner/base-amd64.manifest.json)
is the exact registry manifest; its bytes reproduce the platform digest below.

| Surface | Verified now | Still required before freeze |
|---|---|---|
| Python base | `python:3.12.15-slim-trixie`, linux/amd64 manifest `sha256:e8a38829209aea82774882e5157e1f7c3e8c8393ff53a697b3580896e57f345c`; raw manifest hash matches descriptor | Pull/config/layer byte verification, actual interpreter/stdlib/shared-library inventory and smoke; manifest version annotation alone is not execution evidence |
| Build backend | pyproject requires unpinned `hatchling`; original lock omits hatchling/editables/tomlkit/trove-classifiers | Separate reviewed, hash-complete build closure including dynamic editable requirements; offline build proof |
| Candidate backend closure | Downloaded/hashed wheels: hatchling 1.32.4, editables 0.6, tomlkit 0.15.2, trove-classifiers 2026.9.21.13, packaging 26.3, pathspec 1.1.1, pluggy 1.7.0 | These are proposed inputs, not installed/approved backend pins; metadata is not proof of complete dynamic closure |
| Runtime/dev packages | Original universal lock includes artifact hashes; three candidate shared backend wheels also match it | Record selected platform artifacts, hash every download, reject unexpected sdists/builds, install offline and inventory all distributions/import paths |
| uv | Target 0.13.5; current host is 0.12.23 | Exact distribution/archive and executable hash; use same binary for outer and nested commands; no PATH fallback |
| OS tools | Git required by launcher/revision/tests; shell, core utilities, procfs/process tools and namespace probing affect tests | Pin Git, init, CA roots, shell/coreutils, procps/util-linux and their complete .deb/shared-library closure from one immutable snapshot; no moving apt update in final recipe |
| Optional acceptance tools | Node + installed MCP client, Wasmtime and other tool-gated tests can change skip reasons | Inventory applicability; compare skipped IDs/reasons, report missing coverage; do not omit tools or add skips to manufacture PASS |
| Image build | No final runner image exists | Pin builder/frontend, build argv/context hashes/platform, package manifests, SOURCE_DATE_EPOCH and generated files; record image config ID separately from distributable manifest digest |
| Runtime host | Local Docker 28.4.0, containerd 1.7.28, runc 1.3.0; kernel 6.18.57; vfs/cgroup v2 | Owner host engine/runtime/kernel/WSL versions, security profile, filesystem and cgroup controllers; host kernel is outside image identity |
| Environment | Current outer limit: two aggregate CPUs, 8 GiB, PID limit `max`; PID 1 is `tail` | Actually enforced per-container limits, init adoption/wait, locale/timezone, sanitized environment, mount policy and bounded outputs |

Candidate wheel hashes are hashes of downloaded **wheel bytes**, independently
compared with PyPI's advertised hashes, unlike #1293's historical METADATA-only
hashes. ZIP metadata was read without installing/importing package code. Hatchling's
ordinary CPython 3.12 requirements name packaging/pathspec/pluggy/tomlkit/
trove-classifiers; its `tomli` condition is Python <3.11. No optional pathspec extras
are selected. Editables is included from historical build observations; dynamic
build hooks were not executed. Do not claim this proves a complete build closure.

The base config digest is
`sha256:a33c10a97f11005523814c6eee013986119fe41f3122f444518117536675c8e1`.
That is registry metadata, not a verified local image ID. The multi-platform index
digest and final runner digest are **not recorded because not verified**. The
base's Debian-parent annotation is also metadata, not a separately pulled OS image.
An official Python image can differ from the historical managed CPython build
despite the same patch version; a new image replay must disclose this difference.

## Proposed minimal immutable runner — not implemented

Use the candidate base by **platform manifest digest**, never tag-only, and one
public-only source export with real Git metadata at the approved source SHA.
Bake the original lock, pinned uv, pinned init, selected wheels/build inputs and
installed environment into the image. Keep the source/venv paths fixed so editable
references and nested launcher commands resolve the same source/interpreter.
No live checkout, user site-packages, host cache, credentials or Docker socket is
mounted at runtime. No C++ compiler/toolchain is needed for this Python-only scope.

Use a pinned in-image Tini as PID 1, exec form `tini -g -- COMMAND...`, foreground
supervision and exit-status propagation. Its exact release artifact/version/hash
must be reviewed before build. `tail`, shell keepalives and process-group killing
alone do not provide orphan adoption/wait. The locally observed docker-init is
Tini 0.19.0/de40ad0, executable SHA-256
`8cc70470bb4b21c25ddca7108c5820fa14d5019b5f1ec7e94bfca65de2479990`;
this does **not** establish provenance for a future in-image init binary. Docker
`--init` is an alternative only if its actual binary is pinned/recorded on each
daemon; a flag alone does not freeze that external dependency.

Build from staged hash-verified artifacts offline after public acquisition.
Retain the original lock unchanged; put backend requirements/hashes in a separate
experiment artifact. Isolated build constraints alone do not pin download hashes.
Prefer an explicitly populated isolated backend environment and hash-enforced
offline editable build with no implicit dependency acquisition. Prove all extra
build requests are covered and fail if unexpected. Do not switch to source-only
PYTHONPATH execution or remove editable installation merely to avoid backend pins.
The final acceptance install should preserve the approved dependency selection.

Proposed runtime: linux/amd64, nonroot UID/GID 10001, read-only root filesystem,
no network except the private namespace's loopback, all capabilities dropped,
no-new-privileges, no host PID namespace, two CPU quota, 4 GiB memory with no extra
swap, PID limit 256, 1 GiB private `/tmp`, 64 MiB `/dev/shm`, core dumps disabled,
one public verifier at a time. Evidence directory is the only host write mount.
PID/tmpfs/shm values are new proposal values, not previously measured controls.
Filesystem restrictions must be tested against existing tests; don't weaken tests
or silently increase privileges if they fail. A writable scratch source copy may
be proposed separately if a real test requirement establishes the need.

Set UTF-8 locale, UTC, PYTHONHASHSEED=0, PYTHONNOUSERSITE=1, bytecode/cache paths
in private scratch, and PYTEST_XDIST_AUTO_NUM_WORKERS=2. Fix PATH to the pinned
venv/uv/system tools. Strip ambient Python/uv/project-selection variables while
preserving managed proxy/CA/auth guards during acquisition only. Use the provided
CA as a build secret for networked steps; never bake session CA/credentials in
layers. Final execution is offline. No unapproved Python download or uv sync at run.

Public regression uses both existing pytest partitions sequentially, preserving
their normal deadlines and all failures. A proposed 1800-second external watchdog
per partition is an infrastructure limit, not a change to a test deadline or a
benchmark invocation. Record raw stdout/stderr/exit, monotonic duration, selected
test IDs, skip reasons, OOM/PID events and controls observed inside the container.
Future benchmark limits remain the public design's **60 s wall, 4 GiB and 16 MiB
per stdout/stderr stream**; this preparation neither implements grading capture
nor changes that contract. Disk/log overflow controls need separate verification.

Acceptance after design review: fresh install from absent cache; offline repeat
from reviewed artifacts; lock/source/inventory equality; existing docs checks/demo;
original reaping test unchanged under init; neutral EOF/TERM/parent-SIGKILL adoption
and wait observations using stable PID/start tokens; graceful and watchdog cleanup;
both full regression partitions with no unexplained failures or extra omissions;
resource/network/mount controls; exact distributable image digest and a second
public replay. Record kernel/runtime differences and failures. No claim of equal
independent candidate workers follows from these controls.

## Direct BENJAMIN replay instructions and evidence classes

**Not executed on BENJAMIN here.** Prior owner observations are 7,134 passed /
60 skipped in 550.48 s, source `9d930d07...`, lock `02faf4e8...`, uv 0.13.5 and
effective Python 3.12.15. System Python 3.10.12 is a different interpreter.
The reported Docker Engine 29.1.3 is not this workspace's Engine 28.4.0.

Existing local historical evidence remains: #1293 fresh install PASS, archive-only
failure, corrected run 7,133 pass / 60 skip / 1 fail; #1295 unchanged old target
passed under a process-local subreaper, then fixture-corrected source passed
7,136 / 60 / 0. None is an image execution at this report's baseline. This task
ran only the read-only preparation/static checks listed in evidence JSON; no new
project regression is claimed.

The following **process-only draft** preserves the live checkout. It verifies
the approved pair in a new public export without installation. Run it from the
existing BENJAMIN checkout after fetching the reviewed report branch. It requires
pre-existing exact tools and stops if unavailable; it does not provision them.

```bash
set -euo pipefail
checkout=$(pwd)
artifact_commit=0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5
source_commit=9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90
replay=$(mktemp -d /tmp/genia-1285-public-precheck.XXXXXX)
if test -f "$checkout/uv.lock"; then
  sha256sum "$checkout/uv.lock" > "$replay/live-lock.before"
fi
git rev-parse HEAD > "$replay/owner-checkout-sha.txt"
git show "$artifact_commit:.genia/experiments/issue-1285/dependencies/BENJAMIN.lock" \
  > "$replay/BENJAMIN.lock"
test "$(sha256sum "$replay/BENJAMIN.lock" | cut -d ' ' -f 1)" = \
  02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8
mkdir "$replay/source"
git archive "$source_commit" | tar -x -C "$replay/source"
cp "$replay/BENJAMIN.lock" "$replay/source/uv.lock"
chmod 444 "$replay/source/uv.lock"
cd "$replay/source"
test "$(sha256sum pyproject.toml | cut -d ' ' -f 1)" = \
  cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc
unset VIRTUAL_ENV CONDA_PREFIX PYTHONPATH PYTHONHOME UV_PROJECT UV_PYTHON
unset UV_WORKING_DIRECTORY UV_PROJECT_ENVIRONMENT UV_CACHE_DIR
export UV_CACHE_DIR="$replay/check-cache" UV_PYTHON_DOWNLOADS=never
export PYTHONNOUSERSITE=1
uv_0135=$(command -v uv)
test "$("$uv_0135" --version | cut -d ' ' -f 2)" = 0.13.5
python_31215=$("$uv_0135" --no-config python find --offline --no-python-downloads 3.12.15)
test "$("$python_31215" -c 'import platform; print(platform.python_version())')" = 3.12.15
"$uv_0135" --version > "$replay/uv-version.txt"
"$python_31215" -VV > "$replay/python-version.txt"
sha256sum "$uv_0135" "$python_31215" > "$replay/tool-executable-hashes.txt"
sha256sum uv.lock pyproject.toml > "$replay/before.sha256"
set +e
"$uv_0135" --no-config lock --check --offline --no-python-downloads \
  --python "$python_31215" > "$replay/check.stdout" 2> "$replay/check.stderr"
check_rc=$?
set -e
printf '%s\n' "$check_rc" > "$replay/check.exit"
sha256sum -c "$replay/before.sha256"
if test -f "$replay/live-lock.before"; then
  sha256sum -c "$replay/live-lock.before"
fi
printf 'evidence=%s; lock-check exit=%s\n' "$replay" "$check_rc"
test "$check_rc" -eq 0
```

For full direct-host replay after the build design is accepted, create independent
Git metadata in that disposable export using the exact source (the #1293
`git init/fetch/reset --mixed` recipe), provision only approved pinned tools/backend
inputs, and install with the reviewed hash-enforced offline recipe. That concrete
build/install recipe does not exist yet; **do not run the earlier unpinned sync
recipe and label it frozen**. Record WSL/kernel/Docker/init versions, actual CPU,
memory/PID limits, process tree and package/tool inventory. A WSL PID 1 or daemon
version is not by itself proof of correct reaping. Then capture each command below
separately, including both partitions even if the first fails:

```bash
uv --no-config run --offline --no-sync python tools/validate_llm_instructions.py
uv --no-config run --offline --no-sync python tools/gen_function_docs.py --check
uv --no-config run --offline --no-sync python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage
uv --no-config run --offline --no-sync python -m genia.interpreter examples/validated_pipeline_demo.genia
PYTEST_XDIST_AUTO_NUM_WORKERS=2 uv --no-config run --offline --no-sync pytest -n auto -q -m 'not loopback'
PYTEST_XDIST_AUTO_NUM_WORKERS=2 uv --no-config run --offline --no-sync pytest -n auto -q -m loopback
```

These are draft verification commands, not executed results or a benchmark recipe.
The demo has a historically recorded nonfatal runpy warning. No Genia output
normalization/grading is implemented. Preserve failed logs and sanitize local
paths before public sharing. Send only public evidence; never annex/hidden data.

## Review packet, cost and next action

Claude Code should read this exact committed diff, source/lock provenance, earlier
failure/reaping evidence and the adjacent manifest/JSON, verify hashes and scope,
and return findings by severity plus PASS/FAIL/BLOCKED for the **design only**.
Check preservation of original source, backend closure limits, immutable OS/tool
inputs, Tini adoption/wait/signal behavior, offline execution, honest evidence
classes, resource enforcement plan and $0 policy. Reviewer must not access private
material, install/build/run the proposal, invent a digest, or authorize trials.
Record actual reviewer/model/session and exact reviewed SHA; pending is not PASS.

Current review status: **BLOCKED — Claude Code unavailable**. A draft/publication
does not imply independent review. No authenticated alternative route was supplied
and no paid API, subscription or additional worker was provisioned. Token usage,
review time, existing host/account invoices and performance savings were not measured.
Budget remains **$0 incremental spending**; public downloads and existing workspace
compute only, no Actions dispatch, image registry upload or paid artifact storage.

**Single next owner action:** arrange independent Claude Code review through an
existing $0 access path for the exact proposal SHA. After review, accept/revise the
public-only build design and missing pin completion before implementation. The
approved original pair needs no provenance reapproval. Final image/OS/tool/backend
freeze, offline install/full regression, observed init behavior and direct BENJAMIN
replay remain unverified. Private custody/identities, independent workers, hidden
fixtures/annex/oracle, candidates and comparative trials remain **NO-GO**. #1285
stays open; no merge, closure or unrelated R29 work is authorized by this handoff.
