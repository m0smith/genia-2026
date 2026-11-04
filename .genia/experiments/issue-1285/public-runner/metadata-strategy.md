# Deterministic installer strategy — selected candidate and historical proof

Status: **HOST IMPLEMENTED CANDIDATE; independent source review and official target pending.**
Starting design/evidence SHA: `3fdb037a27dcc555bc5ada85dfe88fe18233f522`.
[Independent Claude PASS-WITH-REVISIONS](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6642696319) verified the host proof;
[maintainer decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6643051249) selects the candidate and authorizes text only.
[Venue update](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6643155880) removes BENJAMIN as an active execution prerequisite.
The [revised frontend/recipe specification](offline-build-recipe.md) is the current
design; the following spike evidence remains historical and unchanged in its files.
The frontend is implemented and host-tested under later authority, but no
production-ready frontend, official-target result or image is accepted.
All approved source/lock/wheel/uv/base/BuildKit pins and strict two-build acceptance
are preserved. Initial metadata is not silently normalized.

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

The historical uv recipe is therefore **predicted to fail** strict two-build OCI
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

This is the **only** alternative installer evaluated. The historical helper verifies SHA256 and RECORD per wheel immediately before
installing that wheel. It does **not** prevalidate the whole set: Claude's
`[good, tampered]` control wrote eight files before failure. The later production
design requires complete-set validation before any destination writes.
It supplies a fixed scheme/interpreter, POSIX script kind and no bytecode levels.
It installs only an explicit list of local wheels; it cannot resolve dependencies
or build sdists. The helper's single-invalid-input controls failed before destination creation;
that result is not a complete-set zero-write guarantee. The first RECORD-control
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
as three additional bounded smokes. Claude independently exercised all 15 wrappers with matching host outputs/exits
and uv list/freeze/show/tree/check without REQUESTED. Official-target/platform
behavior remains pending, not inferred from those host results.
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
This demonstrates current import routing and two public smoke calls; the full existing test suite was not run. Claude separately verified host live
source edits and a new module without reinstall; official-target live semantics
and read-only execution remain pending.

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

## Selected strategy, review corrections and next gate

The maintainer **selected** installer 0.7.0 plus the unchanged isolated seven-wheel
Hatchling builder, retaining uv 0.13.5 for scaffolding/checks/test/launcher use.
Selection does not accept the spike helper as production code. Installer's pin is
first-use SHA256 trust, corroborated by PyPI JSON and same-URL re-download, with
no publisher signature/attestation or independent provenance channel.

Claude's independent host CPython **3.12.3** results complement Codex's **3.12.14**:
0 wheel/final A/B differences; 17,736 reviewed installed RECORD entries valid;
47/44 inventories, all 15 wrappers and live-source routing reproduced. Its raw
18,127/18,138 paths include 339/341 directories; Codex's 17,788/17,797 count only
files/links. Different RECORD totals are attributed to their respective trees,
not silently reconciled. Neither environment is official CPython **3.12.15**.

High-priority correction: the committed Codex proof used umask 077, yielding
0600/0711 files; this does not prove UID 10001 readability. Current design requires
`umask 022` for scaffold/install/editable, 0644 files, 0755 directories/executables,
explicit ownership and full directory/file/link A/B inventories. Other required
corrections: explicit `posix_prefix` plus fixed-root assertions, validate all wheels
and RECORDs/destinations before writes, reject collisions, deterministic sorted
order, reviewed/hash-pinned frontend source, isolated builder, mandatory
`uv --no-config run --frozen --offline --no-sync` and distinct launcher `--no-project`.
The unchanged evidence files/helpers retain their historical limitations.

Intentional uv differences remain: 133 uv-only paths (one .lock, 44 REQUESTED,
43 wheel direct_url.json, 44 uv_cache.json, one uv_build.json); 104 common differing
files (44 INSTALLER, 44 RECORD, editable direct_url serialization, 15 wrappers).
No installer-only paths or METADATA/WHEEL/entry_points.txt differences were observed.
The new recipe specifies these as initial outputs, not post-install cleanup.
Zero bytecode remains required; precompilation requires separate review.

**Historical design next action:** the short text delta review of d591ecf5
completed in Claude6643785950. The implemented source/test review is still pending;
see the current implementation follow-up below. Only after separate production frontend
implementation authority, reviewed hashed source, G1/G3 closure and separate build
authority may official-target install/control/full-regression/two-build evidence
be collected. Equal manifest/config/layers and canonical archive bytes remain
mandatory; no exclusions, metadata patch/delete-on-diff or single-build substitute.

**G1** signed snapshot/OS/Git/Tini closure and all 87 base-package compatibility
checks remain blocked by supported network policy. **G3** qualification of an approved $0 Linux/amd64 venue (build/run/export/cgroup,
pinned rootful worker/snapshotter, finite storage, reaping and offline controls)
remains unverified; BENJAMIN is offline and not required. Historical BENJAMIN
provenance is retained, without claiming per-test equivalence. G2 dynamic execution/write inventory and G5 target/
resource/test/OCI acceptance remain open. No E1–E3, independent-worker or custody
claim follows. $0 incremental spending is preserved.

## Implemented frontend follow-up (host only)

Under [implementation authority](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6644232395),
the separately committed RED tests precede the minimal stdlib-first/native-writer
implementation. See [source pins](frontend/source-pins.json),
[mode manifest](frontend/expected-modes.json), [input hashes](input-sha256.txt) and
[new host evidence](frontend-evidence/implementation.json). Original experiment
helpers/logs/manifests remain untouched. New proof uses exact no-newline PEP610
metadata, preserves ZIP-executable regular members and native member order,
handles safe zero-size ZIP dirs as non-payload, verifies mode overrides and all
retained roots including inputs/builder/tools/generated wheel. UV_NO_SYNC and
UV_FROZEN are host-tested hardening; explicit project flags remain mandatory.
Independent Claude source/test maintainability/security/behavior review is the
next gate; design review is not that review. G1/G3 and official-target/full-test/
control/two-independent-OCI requirements remain unchanged and blocking.
