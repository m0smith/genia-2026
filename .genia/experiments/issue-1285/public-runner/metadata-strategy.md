# Deterministic installation spike — decision evidence, not an adopted recipe

Status: **TEST/DESIGN ONLY; strategy UNSELECTED; STOP before image construction.**
Authorization: [maintainer decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6641293474).
This addresses the [Claude delta review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6639484157)
on `00b95b62842f1907bf2174694b1e3de17ffeccbe` without changing approved source,
lock, dependency pins, installation commands or strict two-build acceptance.

## Executed conditions and results

The separately committed [experimental helper](installation_spike.py), commit
`4dac9cce368c9e00cafdb5fd25af0b334c32bc3a`, ran from a fresh scratch root.
[Evidence](installation-proof/evidence.json) records its exact SHA256, full
command arguments, stdout/stderr, tool/runtime identities, failures and file
inventories. Host CPython **3.12.14 / Clang 22.1.3** is compatible with the selected
CPython 3.12 wheels; it is **not** the pinned official-image CPython 3.12.15.
No official target, image, BuildKit daemon, BENJAMIN replay or regression ran.

Both strategies reconstruct the approved `9d930d07` source and original lock,
use identical verified wheel bytes, fixed absolute source/venv/staging paths,
empty per-case uv caches, fixed wheel mtimes and SOURCE_DATE_EPOCH `1793034850`.
Every one of the 47 staged wheel ctimes differs between A and B. Sequentially
recreated environments have independent writes; they are not independent workers.
Third-party packages use wheels only. uv has explicit offline/no-index/no-deps
controls; the alternative has no resolver or download path. No packet-level
network isolation proof is claimed for these host experiments.

All **36** recorded commands in the confirmation run exited 0. The comparison
reads every installed file's bytes, file mode and symlink target, excluding
nothing within the deployment venv. Directory times/owners and OCI bytes are
not tested by this comparison. Dist-info METADATA/WHEEL, RECORD, INSTALLER,
direct_url.json, uv_cache.json, uv_build.json, scripts, .pth and resources are
included. All eight complete venv manifests include every file/link hash and
the full selected metadata text. No .pyc was produced.

| Pair | Distribution set | Paths per installation | Changed files | Equality |
|---|---|---:|---:|---|
| uv wheels | runtime 43 + backend union = 47 | 18042 | 94: 47 uv_cache.json + 47 RECORD | FAIL, expected negative control |
| uv editable, four backend-only packages removed | runtime 43 + Genia = 44 | 17930 | 88: 44 uv_cache.json + 44 RECORD | FAIL, expected negative control |
| installer wheels | runtime 43; backend 7 isolated separately | 17788 | 0 | PASS, scratch bytes only |
| installer editable | runtime 43 + Genia = 44 | 17797 | 0 | PASS, scratch bytes only |

All 94 wheel timestamps (47 in each uv trial) exactly match the staged wheel's
**ctime to the nanosecond**, despite fixed mtime and SOURCE_DATE_EPOCH. Genia's
uv_cache timestamp exactly matches pyproject.toml ctime in both trials. Its
`directories.src` timestamp also varies, but **does not equal** the helper's
sampled src-directory ctime. A supplemental directory probe retained all sampled
source stat values and found no exact match for that field; this spike does not
claim its precise clock mapping. That limitation does not change the reproduced
ctime failure in the wheel/project timestamps. Editable uv_build.json is `{}`
and equal across A/B. The corresponding RECORD entries change with uv_cache.
INSTALLER and direct_url.json are stable within each uv pair at fixed paths.
Flat-index/cache-mode findings remain attributed to Claude's independent review;
this spike used exact local wheel paths and did not repeat that matrix.

The current uv recipe is therefore **predicted to fail** strict two-build OCI
equality. Fixed paths, touch/mtime, cache isolation and exporter timestamp
rewriting cannot repair these content differences. No normalization, exclusion,
metadata deletion or weaker equality claim is authorized.

## One alternative: PyPA installer 0.7.0

[Candidate pin](installation-proof/installer-candidate.json):
`installer-0.7.0-py3-none-any.whl`, 453838 bytes, SHA256
`05d1933f0a5ba7d8d6296bb6d5018e7c94fa473ceb10cf198a92ccea19c27b53`.
Public PyPI release JSON and downloaded size/hash agree. There is no independent
publisher-signature attestation. The pure Python tool requires Python >=3.7 and
declares no dependencies. It is extracted from verified bytes and invoked with
`python -I -S -B`; the only added tool import root is that extracted wheel.
The evidence records the actual host interpreter executable hash/compiler and
library versions. The official target runtime and its required dynamic libraries
remain a target gate, not newly completed pins.

This is the **only** alternative installer evaluated. For each archive the
helper verifies SHA256 and validates every wheel RECORD hash/size before writes.
It supplies a fixed scheme/interpreter, POSIX script kind and no bytecode levels.
It installs only an explicit list of local wheels; it cannot resolve dependencies
or build sdists. Wrong archive hash, missing archive and deliberately corrupted
wheel RECORD controls fail before destination creation. The first RECORD-control
attempt had an invalid wheel filename and stopped earlier; that harness failure
and corrected rejection are both retained. Offline `uv pip check` checks the final exact identity
set. All 17780 installed RECORD entries in each alternative final venv validate.

The frontend supplies truthful initial `INSTALLER` bytes `installer\n`. Unlike
uv, the alternative does not generate uv_cache.json/uv_build.json or wheel-local
direct_url.json for the named wheel artifacts. Archive provenance remains in the
pin manifest. Metadata for a wheel without direct-URL requirement semantics need
not contain PEP-610 provenance. uv's INSTALLER is `uv` without a trailing newline;
its wheel-local direct URLs/cache files and RECORD consequently differ from the
alternative. No cross-installer byte-equality claim is made. The
[cross-installer inventory](installation-proof/cross-installer-differences.json)
finds 133 uv-only paths: .lock, 43 wheel direct URLs, 44 uv_cache files, one
uv_build file and 44 REQUESTED markers. There are no installer-only paths.
104 common files differ: 44 INSTALLER, 44 RECORD, Genia's direct_url serialization
and **15 generated console wrappers**. The latter use different standard wrapper
templates, including argv[0] suffix cleanup; full script texts are retained.
Alternative-B `genia -c '1 + 1'`, `pytest --version` and `mkdocs --version` pass
as three additional bounded smokes. Other wrapper behavior, REQUESTED consumers
and platform behavior remain review/test questions, not presumed equivalence.
Every difference is visible in the committed inventories. No installed file is patched
or removed to get the alternative's A/B equality.

## Editable Genia, separately evaluated

uv scaffolds an unseeded final venv and a **separate**, non-deployment backend
venv. The latter contains exactly the existing seven pinned backend wheels.
Hatchling's PEP-660 hook returns exactly `["editables~=0.3"]`; `build_editable`
builds only the approved first-party Genia source. No third-party source build,
backend upgrade, source overlay or lock regeneration occurs. The two resulting
editable wheel byte hashes match (exact hash in evidence; scratch-path-specific,
not a future target artifact pin).

installer installs this PEP-660 wheel into the final venv. At initial install the
frontend supplies canonical PEP-610 `direct_url.json` with `dir_info.editable=true`
and the fixed source URL, plus INSTALLER; these files are included in RECORD.
The installed Hatchling .pth makes **live approved source** importable. Each
`python -I -B` import resolves genia.__file__ under the exported `source/src`,
with user site disabled and no PYTHONPATH. Exact final name/version inventory,
`uv pip check --offline`, `1 + 1` CLI and the existing public validated-pipeline
demo pass in all four final environments. The helper compares exported source/
lock file bytes/modes/links before and after; no tracked content changes.
This demonstrates current import routing and two public smoke calls; the full
existing test suite and live-file-mutation semantics were not separately tested.

## Reproduction and retained failures

Acquire only the exact public artifacts in pins.json and the candidate installer
pin, independently verify hashes, and provide a fresh empty scratch directory
under `/workspace/work`. On the recorded host the invocation was:

```sh
python -B .genia/experiments/issue-1285/public-runner/installation_spike.py \
  --work /workspace/work/issue-1285-deterministic/run4
```

Defaults reference the recorded existing cache paths; use the explicit `--repo`,
`--uv`, `--installer`, `--wheels`, `--backend` options to supply equivalent verified
inputs. Run without `-O`. The helper rejects nonempty scratch roots and now checks
at least 3 GiB/free 230000 inodes before starting. Its 1 GiB logical snapshot and
200000 file/link caps are scratch evidence caps, **not** runner storage/resource
acceptance. Observed snapshot bytes/paths, actual preflight capacity and every
command's 90-second timeout are recorded; no CPU/cgroup isolation is claimed.

The first attempt failed in helper selection (`target_selected` missing on a
backend overlap row), after the uv pairs. Its exact helper/log/result are retained.
The corrected second attempt completed. A third attempt completed all commands
but exhausted **inodes** while copying its eighth snapshot: 524288/524288 used,
with 2350604 KiB disk space still available. It is a failed evidence-capture run,
not a completed comparison. Full stderr and seven complete manifests survive.
Only redundant generated directories were removed after preserving results and
manifests. The final committed helper adds fresh-root/optimization/capacity guards;
the fourth attempt completed under those guards. These failures are not replaced
by the final result. The mistaken postprocessing directory-stat assertion and
read-only default uv-cache failure are also recorded.

File manifests are losslessly recompressed as XZ JSON to avoid retaining eight
copies of package binaries in git. Their decoded hashes and original gzip hashes
are indexed in evidence.json; installed metadata text is retained in full.
Supplementary manifests describe the tool library, last editable wheel and last
isolated builder after the separately labeled timestamp probe. Earlier transient
builder trees are not retrospectively inventoried or claimed byte-reproducible.

## Recommendation and next gate

Recommend **reviewing** installer 0.7.0 as the final wheel writer with the isolated
pinned Hatchling PEP-660 frontend above, retaining uv for venv scaffolding,
consistency checks and the existing public command launcher. This preserves the
strict two-build requirement in the observed scratch pair. It is not approval to
adopt the helper or change the recipe. The production frontend, initial metadata
policy, tool bootstrap hash, canonical /opt paths, script behavior, absent uv cache
metadata and exact official-interpreter requirements need independent review and
a maintainer strategy decision before a separate recipe/build authorization.
The original source/lock and every existing artifact pin remain unchanged.

Independent Claude Code delta review should verify: exact helper/evidence SHA;
the decoded file inventories and ctime comparisons; all RECORDs/initial frontend
metadata and PEP-660/import assumptions; the explicit expected 47/44 inventory;
source-policy WILDCARD/hash correction; stream-overflow design; preserved strict
equality and failures. Return reviewer/session/model, exact reviewed SHA, ranked
findings and verdict. No callable Claude route is available here; this document
requests that review and does not claim it happened.

**G1** signed snapshot/OS/Git/Tini closure and all 87 base-package compatibility
checks remain blocked by supported network policy. **G3** direct BENJAMIN
build/run/export/cgroup inspection, worker/snapshotter and finite storage-quota
receipts remain unverified. G2 dynamic execution/write inventory and G5 target/
resource/test/OCI acceptance remain open. No E1–E3, independent-worker or custody
claim follows. $0 incremental spending is preserved.
