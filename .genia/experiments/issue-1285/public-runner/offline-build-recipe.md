# Offline public runner recipe — review draft, DO NOT BUILD

Current status: [maintainer accepted exact frontend `fd74a583`](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6702416476)
after independent Claude PASS; earlier frontend-review-pending prose below is
historical. See the [current process status](../../../process/issue-1285-public-frozen-runner.md)
for carried Low-1–Low-4/R6/R7 debt and unchanged later gates. `pins.json` remains
byte-identical accepted-head historical metadata. [Fresh G1 evidence](g1-precheck/README.md)
is BLOCKED (proxy403); G3 is separate, no venue/build acceptance follows.


This is a design artifact. The maintainer selected installer 0.7.0 and authorized this text-only revision,
not image construction. Subsequent
[authorization](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6644232395)
permits the frontend implementation and bounded host tests only; independent
Claude returned [PASS-WITH-REVISIONS](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6649295319); the [authorized R1–R5 correction](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6658033204) now requires a fresh independent delta review. The host code is not production-ready. [G1–G5](pin-gaps.md) and independent Claude delta review remain open.
No image-construction command below was executed.
[Current R1–R5 host evidence](frontend-evidence/r1-r5-correction/summary.json) (earlier [implementation evidence](frontend-evidence/implementation.json) is historical) is separate from
image, official-target and runner acceptance. Commands with unknown
OS inputs deliberately cannot be completed; this is not a runnable accepted build.
The [R1–R8 correction evidence](recipe-correction-evidence.json) tests only bounded
host-side backend-wheel CLI behavior. It does not establish target installation.

## 1. Complete/acquire inputs before the separate build gate

Use the original source/lock and exact artifacts in [pins.json](pins.json).
Verify bytes, sizes and SHA256s on every acquisition/re-export. For Debian, verify
Release signature against a recorded Debian archive keyring fingerprint, verify
the Release SHA256 of the amd64 Packages index, solve Depends/Pre-Depends/virtual
Provides/alternatives against the **effective base inventory**, then record every
new/upgraded `.deb` filename, version, architecture, size and SHA256. Check both
metadata dependency closure and actual ELF/shared-library closure later. The 87
base-installed packages are supplied by immutable base layers, not reinstalled
from an unpinned apt repository. No moving apt index, guessed version or local
docker-init substitution is allowed. Currently the snapshot endpoint is blocked.

**R3 STOP condition:** the candidate snapshot `20261021T000000Z` precedes the
base manifest's creation (`2026-10-21T01:00:53Z`); compatibility is untested. From
the verified signed index set, compare **all 87** installed base package versions
with available snapshot candidates, using Debian epoch/revision ordering
(`dpkg --compare-versions`), not PEP 440 or lexical comparison. Every base version
must be less than or equal to its snapshot candidate. A missing package/version,
unreviewed origin (including any required security pocket), or required downgrade
STOPs. Solve against the exact base inventory; no automatic base upgrade either:
each required upgrade must identify old/new version, artifact hash, reason and
affected shared-library closure, and receive explicit review before installation.
Never pass `--allow-downgrades`. A later fixed snapshot with margin may be selected
only after verified indices establish compatibility; no timestamp change is
claimed now. The base image and all verified pins stay unchanged.

Record all selected input hashes in a sorted `input-sha256.txt`; its own reviewed
hash is part of the build candidate. Stage only the 43 `target_selected=true`
runtime wheels and seven backend wheels. Each ambiguous wheel choice
is already resolved to one explicit filename/hash **per lock variant** in pins;
installation does no tag ranking or resolver selection. Do not stage alternate
versions, excluded-marker packages or any sdist. The universal frozen uv export
was checked read-only; narrow it to the reviewed target selections, not a new lock.

Stage these fixed paths in a **new public-only context**:

```text
source/                    exact tracked approved-source export, no overlay
source/uv.lock             exact original lock (ignored by original .gitignore)
source/.git/               fresh public shallow metadata, canonicalized below
runner-input/wheels/       49 exact artifacts: runtime/backend union47 + installer + uv wheels
runner-input/source.tar    original approved git archive, exact pinned SHA256
runner-input/uv.lock       original BENJAMIN lock bytes, exact pinned SHA256
runner-input/pins.json     reviewed source/artifact/selection manifest
runner-input/debs/         complete reviewed .deb closure — CURRENTLY MISSING
runner-input/uv            extracted, hash-verified uv 0.13.5 binary
runner-input/frontend/    implemented sources, expected modes and tool/source manifests
runner-input/frontend_tests/ host verification sources, retained as explicit inputs
runner-input/runtime.requirements.txt
runner-input/backend.requirements.txt
runner-input/input-sha256.txt
```

The unchanged requirement files retain their historical `/opt/runner-input/
runtime` and `backend` paths and single artifact hashes as frozen cross-check
inputs. They are **not executed** by the new frontend or passed to uv install.
The frontend consumes pins.json and the flat exact49-artifact wheelhouse; no
path alias or requirement-file rewrite is introduced. Re-hash the lock and verify every
tracked source blob against the approved tree before/after export, hook, install
and context creation. Hash all recipe/config/requirement files as well as packages. Include the installer
wheel, every frontend source file, entrypoint and source manifest in sorted
`input-sha256.txt`. [Source pins](frontend/source-pins.json) and [input-sha256.txt](input-sha256.txt)
now name exact implemented source/mode/tool manifest hashes. The latter also
includes pins.json, uv binary/wheel, every selected wheel, original source.tar/
uv.lock and unchanged requirements. Its expected SHA256 is supplied separately
by the reviewed caller; verify it and every source entry before executing Python.
Missing independent source review still STOPs build authority. No signature or
self-verification establishes its own trust.
The checked-in65-entry input manifest is the **frontend/host closure**, not a
complete image-context pin closure. Future reviewed G1 OS/deb and Dockerfile/Git/
builder-config inputs must extend the image candidate's manifest and receive a
new separately supplied expected hash. No missing OS/recipe hash is invented.
The context `source/` above is an optional export cross-check/Git input, not a
preinstalled output: never copy it to `/opt/genia/source` before the frontend.
The CLI creates that source output from verified source.tar, then canonical Git/
ownership construction occurs only in the later separately authorized image step.
Never copy a live `.git`, venv, user config, credentials, caches or private data.

Prepare a local OCI **base input layout** only after build authorization: its
manifest/config/layer blobs are the acquired, hash-verified bytes; `oci-layout`
declares 1.0.0 and `index.json` references the exact platform manifest. No tag
lookup or registry source is needed during construction. Current work downloaded
the blobs as archives only; it did not assemble this layout or a root filesystem.

## 2. Canonical source/Git metadata and ownership (A6)

Fetch the exact approved commit into an independent empty-template repository
during public acquisition (`--depth=1 --no-tags`, reflogs disabled). Its public
object data is an input; do not preserve fetch/index/reflog timestamps. Inside the
future build, with the **pinned Git**, canonicalize into a fresh `.git`:

1. Enumerate exactly HEAD plus its shallow reachable tree/blob objects, sorted by
   object ID (`LC_ALL=C`). Keep `shallow` containing the approved commit plus LF;
   do not fetch parents or copy another checkout's history/config.
2. Repack those objects using `git pack-objects --stdout --threads=1 --compression=9
   --window=0 --depth=0 --no-reuse-object --no-reuse-delta`; write the pack under
   its content-derived name and `git index-pack --index-version=2`. Use fixed
   object order and pinned Git/zlib. No automatic gc/maintenance/reflogs.
3. Write fixed config (format version 0, bare false, filemode true,
   logAllRefUpdates false, gc.auto 0), HEAD `ref: refs/heads/public-replay` and the
   exact ref. Delete FETCH_HEAD/ORIG_HEAD/logs/hooks/description/remote config and
   old indexes/packs; only the canonical pack/index/config/ref/shallow remain.
4. `git read-tree HEAD` creates an index with no filesystem-stat refresh; pin
   index version 2 and disable optional locks. Do not run status/update-index
   refresh during the build. Normalize metadata timestamps to SOURCE_DATE_EPOCH.
5. Source and `.git` are owned by runtime UID/GID **10001:10001**, with tracked
   executable modes preserved. No wildcard `safe.directory` exception. Verify
   `git rev-parse HEAD`, `git cat-file -e HEAD^{commit}` and each tracked blob as
   UID 10001. If any required test mutates tracked source or index, STOP and
   review a declared deviation; do not add a writable mount silently.

This algorithm is a **proposed** determinism mechanism. The two-build comparison
must verify actual `.git` bytes and source paths; a description alone is not proof.

## 3. Offline image operations and selected installer design (A3)

**Implemented host candidate; target/independent source delta review pending.** [Maintainer selection](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6643051249)
adopts PyPA installer **0.7.0 as the candidate**, with a separately isolated,
hash-pinned Hatchling PEP-660 builder. The experimental helper is retained evidence,
not accepted production code. The stdlib validator/native writer is [offline_install.py](frontend/offline_install.py);
[build_frontend.py](frontend/build_frontend.py) orchestrates the isolated builder
and complete final batch. RED commit `de1f455823e18f049a87cccbc2934bcb0bc20e11`
precedes implementation. Focused host tests and source pins exist; independent
Claude maintainability/security/behavior review is still mandatory before build use. G1/G3 and separate build authorization remain blocking.

Use a Dockerfile **without `# syntax=`**: builtin dockerfile.v0 is pinned by
BuildKit 0.24.0. `FROM public-base` uses the local OCI binding in section 4.
Every RUN has `--network=none`; no ADD URL, git fetch, apt update or downloads.

Before installation, verify the expected hash of sorted `input-sha256.txt`, then
every listed byte/size/hash, original source and lock. Reject missing/extra inputs
and unsafe paths. Install only the G1-closed `.deb` set offline using
`apt-get --no-download --no-install-recommends --no-remove --yes` with local
arguments, no sources/sourceparts/network. No online repair; record resulting
dpkg and ELF closure. Tini comes from that verified snapshot. This is blocked now.
Copy the pinned uv to `/usr/local/bin/uv`, check binary hash/version, and reject
any other distinct uv on PATH; do not install uv into the deployment venv.

### Fixed identities, paths and permissions

Build operations use UID 0; final runtime is UID/GID **10001:10001**. Set and assert
**`umask 022` before each venv creation, tool extraction, wheel installation,
editable hook/build and editable installation**. Each separate RUN/subprocess must
inherit or explicitly reassert it; a later chmod cannot substitute for this rule.
After the applicable complete prevalidation pass below, create unseeded venvs using pinned uv and official `/usr/local/bin/python3.12`,
without interpreter download or system/user site packages, at these fixed paths:

```bash
set -euo pipefail
umask 022
export UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1 PYTHONHASHSEED=0 TZ=UTC LANG=C.UTF-8
export UV_CACHE_DIR=/tmp/uv-cache
# Builder scaffold: only after all original tool/runtime/backend inputs validate.
/usr/local/bin/uv --no-config --no-cache venv --offline --no-python-downloads \
  --python /usr/local/bin/python3.12 /opt/genia/build-venv
# Deployment scaffold: later, only after the generated editable wheel and the
# complete final-prefix plan validate; these are argv patterns, not a script
# to run back-to-back before validation.
/usr/local/bin/uv --no-config --no-cache venv --offline --no-python-downloads \
  --python /usr/local/bin/python3.12 /opt/genia/venv
```

Every pinned uv 0.13.5 call in install/build uses **`--no-cache`**, including
both scaffolds, the runtime-phase dependency check and final builder/deployment
checks. `--cache` remains an explicit scratch selector; it alone did not govern
installer calls before R1. No ambient `UV_CACHE_DIR` is required for correctness.
Fresh-HOME tests unset it and prove no persistent HOME writes. Prevalidation also
reserves `bin`, `lib`, `lib/python3.12` and site-packages before any scaffold writes.

The reviewed frontend is invoked by `/usr/local/bin/python3.12 -I -S -B` at
`/opt/runner-input/frontend/`; bootstrap only the hash/RECORD-validated installer
wheel into `/opt/runner-tools/installer`, with that sole non-stdlib import root.
The selected bootstrap is **stdlib-first only**: validate the exact installer
archive and all original inputs without destination writes, then extract its
23 verified files to the isolated tools root. Rehash that complete tree against
installer-files.json before every code import. No read-only zipimport alternative. Bootstrap extraction itself
must follow the same validate-first path policy below. No ambient site-packages, PYTHONPATH, user config, plugins or network acquisition.
The CLI requires `-I -S -B` and explicit input-manifest/hash arguments; verifies
the entire input tree before any output, and rejects selectors outside that tree.
It verifies original tar/lock bytes, then projects Git archive0664/0775 entries
through the declared umask022 to canonical tracked0644/0755. Source bytes and
executable status stay unchanged; generated package metadata is never normalized.
Record interpreter/library hashes under official 3.12.15; host proof is insufficient.

For each prefix explicitly call `sysconfig.get_paths(scheme="posix_prefix", vars=...)`
with `base`, `platbase`, `installed_base`, `installed_platbase` all bound to that
prefix. Do not rely on Debian's default scheme. Assert purelib and platlib equal
`<prefix>/lib/python3.12/site-packages`, scripts equal `<prefix>/bin`, data equal
`<prefix>`, and headers/include mappings remain under `<prefix>/include`.
Pass the explicit scheme mapping to installer, with `script_kind="posix"`,
`interpreter=<prefix>/bin/python` and `bytecode_optimization_levels=[]`.
Assert every dist-info under that prefix's exact site-packages root. Realpath and
lexical containment checks must agree; scaffold interpreter symlinks to the pinned
base are declared separately and never authorize wheel writes outside the prefix.

Expected deployment regular files are **0644**, executable wheel payloads/generated scripts
**0755**, and directories **0755**, with no group/world write or setuid/setgid/sticky
payload bits. Enumerate executable paths from reviewed wheel attributes and script
generation; reject unexpected permission bits/types. Symlink mode is recorded via
lstat (Linux typically 0777), never chmod-followed; allow only reviewed scaffold
links with exact targets. Inventory scaffold, all directories, regular files and
links, modes, link targets and uid/gid. The expected per-path
[mode manifest](frontend/expected-modes.json) includes runtime/builder files,
all ancestor directories, exact scaffold files/links and editable additions.
It preserves all **15 ZIP-executable members** (ruff's data script is one), plus
**15 generated console wrappers** including Genia. The non-binary executable
Python members remain executable as shipped. Genuine zero-size type-directory
ZIP entries use mode0755 for traversal; they are not executable regular payload. Assign final deployment/source ownership
10001:10001 by the declared recipe before comparison; builder/tools remain build
inputs owned by 0:0. Verify all deployed files are readable and executables and
parent directories traversable as UID 10001. Read-only runtime is enforced by
rootfs/mount policy, not by substituting restrictive file modes. Compare A/B after
ownership assignment; original 0600/0711 host-proof modes are not target acceptance.

### Complete validation, then deterministic writes

The frontend consumes only explicit manifest-selected local wheels, never a
resolver, index, sdist or dependency downloader. Compute the full plan first:

1. Verify **all** 43 selected runtime plus seven backend inputs (47 unique
   name/version/hash identities after the three exact overlaps), installer tool
   inputs and source inputs before any destination creation or mutation, including
   the venv scaffolds. Validate filename/name/version/tag against pins and wheel
   METADATA/WHEEL, reject alternate/inactive variants and duplicate identities.
2. Validate each entire ZIP and every member RECORD hash/size using
   `WheelFile.validate_record(validate_contents=True)` plus strict member/RECORD
   coverage checks. Reject missing or duplicate rows/members, extra unrecorded
   payload, bad digests/sizes, malformed paths and unsupported signatures/types.
   **M1:** allow only canonical safe zero-size type-directory entries ending `/`,
   mode0755, omitted from RECORD; these create no output by themselves. Reject
   duplicate dirs, malformed/nonempty dirs and symlink/special/executable regular
   entries disguised as directories. Only payload has bidirectional RECORD coverage;
   only the wheel format's explicit RECORD self-row hash/size exemption is allowed.
   Reject absolute paths, traversal/dot aliases, backslashes, NULs, symlink/device
   archive entries, malformed `.data` schemes, and any unapproved payload.
3. Map all members, relocated `.data` files, generated wrappers, initial metadata
   and RECORD outputs to canonical destinations using `posix_prefix`. Reserve
   scaffold paths. Check all destination and parent types/containment before writes;
   reject file/directory aliases, duplicate script names, intra/inter-wheel path
   conflicts (even identical bytes), existing unexpected files or symlink parents.
   Shared package directories alone are allowed. Never overwrite a scaffold,
   another distribution's file or an unowned artifact. RECORD replacement is only
   the declared generation of that same distribution's installed RECORD.
4. Use fixed phases: the43 runtime wheels, then the singleton editable Genia.
   Within each phase sort by normalized name/version string/filename/SHA256 in
   bytewise `LC_ALL=C` order. Prevalidate the complete44 set before any venv writes;
   verify runtime43 RECORDs and run offline pip check at the phase boundary. **Retain each pinned wheel's original
   ZIP member/entrypoint/RECORD iteration order**, which is fixed by its bytes.
   No member-level adapter or post-generation sorting/patching is used. Native
   installer-generated output is checked against the complete destination plan. Hold inputs read-only and prevent
   concurrent destination mutation; recheck against replacement before writing.
5. Only after the complete first pass succeeds may scaffold/install writes start.
   Emit bounded validation/plan receipts. Negative controls with a valid wheel
   followed by a bad last wheel, wrong hash, missing wheel, RECORD mismatch, extra
   member, traversal, wrong identity or destination conflict must leave **zero
   destination writes**, including directories. This is prevalidation, not a
   transactional guarantee against disk failure or other errors during writing;
   a write-phase failure discards that build output and records the failure.

### Isolated editable builder and exact inventories

Install the seven unchanged `backend_wheels` into `/opt/genia/build-venv`, separate
from deployment: editables 0.6, hatchling 1.32.4, packaging 26.3, pathspec 1.1.1,
pluggy 1.7.0, tomlkit 0.15.2, trove-classifiers 2026.9.21.13. Each wheel's exact
URL/size/SHA256 remains in pins.json and backend.requirements.txt. Use the same
validated installer engine, umask, explicit scheme and sorted-order requirements;
no transient backend installation or uninstall in the deployment venv.

Use `/opt/genia/build-venv/bin/python -I -B` for reviewed hook/build orchestration,
allowing only stdlib, that builder's site-packages and the listed frontend sources.
At fixed `/opt/genia/source`, call `hatchling.build.get_requires_for_build_editable({})`
and require exactly `["editables~=0.3"]`, satisfied by pinned editables 0.6. Then
call `build_editable` into fixed `/opt/genia/editable-wheel`; no implicit build
isolation downloads or additional hooks. Hash the approved source/lock before and
after. The historical 190-file hook listing is preliminary evidence, not the
production frontend source pin; separately review every orchestration, validation, bootstrap and metadata-writing source.
Their exact hashes are now in source-pins.json and input-sha256.txt; independent
Claude R1–R5 delta review is pending. No third-party source build or dependency resolver exists.

Before writing the editable destination, validate the **entire generated wheel**
and RECORD, Genia 0.1.14 identity, source routing and full destination plan against
the existing runtime inventory. Its generated hash is recorded and must match A/B
at these fixed paths; do not reuse a scratch-path hash as a target pin. The builder
necessarily writes its own output before that generated wheel can be validated;
no editable installation writes occur until validation completes. Stage all
runtime and editable wheels for a complete final-prefix validation pass before
creating/installing the deployment venv. The seven-wheel builder pass is separate;
it must fully validate before any builder destination writes. Thus no runtime
wheel is installed while another final-prefix input remains unvalidated.

Require the historical 47-entry union and 44-entry final inventory in
[expected-inventory.json](expected-inventory.json) to stay exact by identity/hash,
not count alone. Selected layout is **43 runtime pre-editable + 7 separate builder**,
then **44 final = runtime 43 + editable Genia**, with no backend-only residue.
The union's three overlaps packaging/pathspec/pluggy must have identical hashes.
Run offline `uv --no-config pip check --python /opt/genia/venv/bin/python --offline`
after runtime installation and again after editable installation; independently
check the builder and exact installed sets. No resolver repair or lock regeneration.

Initial frontend metadata is deliberate: `INSTALLER` is `installer\n`; editable
Genia alone receives deterministic PEP-610 JSON (UTF-8, sorted keys, compact
separators, no trailing newline) containing exactly `dir_info: {editable: true}`
and `url: "file:///opt/genia/source"`. Include those bytes and generated scripts
in installed RECORD. Retain all generated metadata. Named third-party wheel
artifacts have no direct-URL requirement semantics; their provenance is in pins.
Unlike uv, do not generate `.lock`, REQUESTED, wheel-local direct_url.json,
uv_cache.json or uv_build.json. installer wrappers use its standard `re`-based
argv[0] cleanup template. These are intentional initial outputs, not deletions
or normalizations of uv output; METADATA/WHEEL/entry_points.txt stay unchanged.
See [metadata comparison](metadata-strategy.md) for retained exact differences.

Hatchling's installed `.pth` must route to live `/opt/genia/source/src` without
PYTHONPATH or copying Genia into site-packages. Accept only actual source imports
from that root with user site disabled, including another cwd/minimal environment.
Later isolated disposable-copy tests must prove a source edit and brand-new module
are visible without reinstall, restore/verify source bytes, then prove the final
read-only source mount works. No mutation of the approved export or source overlay.

Zero `.pyc` in deployment/source/builder output is mandatory; use `-B` and disable
installer bytecode. Unexpected bytecode fails rather than being silently deleted.
Runtime bytecode remains disabled; any future precompilation or `/tmp` bytecode
cache requires a separate reviewed policy. The existing fixed OS normalization
set remains `/var/log/apt/*`, `/var/log/dpkg.log`, `/var/cache/ldconfig/aux-cache`
and declared build caches; it never permits installed metadata changes. Fixed
`/opt/runner-input` is retained read-only. Inventory every actual byte including
pyvenv.cfg, scaffold, shebangs, .pth, symlinks and RECORD; unexpected paths or any
A/B metadata differences STOP. No patch/delete/ignore-on-diff policy is approved.

Final runtime configuration: `USER 10001:10001`, cwd `/opt/genia/source`,
PATH `/opt/genia/venv/bin:/usr/local/bin:/usr/bin:/bin`, exec entrypoint
`["/usr/bin/tini", "-g", "--"]`, no Docker `--init`. Source/venv/rootfs read-only;
HOME, uv/pytest caches and basetemp under `/tmp`. Public verification requires
exact `uv --no-config run --frozen --offline --no-sync` with
`UV_PROJECT_ENVIRONMENT=/opt/genia/venv`, `UV_PYTHON=/opt/genia/venv/bin/python`,
`UV_OFFLINE=1`, `UV_PYTHON_DOWNLOADS=never`. Host-tested defensive defaults also
set `UV_NO_SYNC=1`, `UV_FROZEN=1`; normal project argv still carries the explicit
flags, and launcher --no-project argv stays unchanged. No target behavior is
inferred from environment names alone. Prove no venv/lock writes or automatic
editable rebuild; omitting `--no-sync` previously attempted an offline rebuild
and wrote `.lock`. Keep the unchanged configured MCP launcher **`--no-project`**
behavior distinct: inspect its argv and do not replace it with project-run flags.
All official-target wrappers/imports/RECORD/full tests/control/OCI checks in the
[acceptance checklist](acceptance-checklist.md) remain pending.

### Exact invocation and retained closure

After a caller verifies the separately supplied expected hash of input-sha256.txt
and its complete contents, the future authorized target invocation is:

```bash
umask 022
/usr/local/bin/python3.12 -I -S -B /opt/runner-input/frontend/build_frontend.py \
  --pins /opt/runner-input/pins.json --inputs /opt/runner-input/wheels \
  --source-archive /opt/runner-input/source.tar --lock /opt/runner-input/uv.lock \
  --uv /opt/runner-input/uv --input-manifest /opt/runner-input/input-sha256.txt \
  --input-manifest-sha256 "$reviewed_input_manifest_sha256" \
  --receipt /tmp/frontend-receipt.json --cache /tmp/uv-cache
```

The target guard requires official3.12.15 and fixed /opt paths. Host tests use
explicit --host-test and a dedicated /workspace/work root, host interpreter and
relocated input tree; they do not execute this official-target command.

**Retention decision (L2):** retain `/opt/runner-input` including source tar,
original lock, all49 wheels, uv binary, frontend/test sources/manifests and both
requirements; `/opt/runner-tools/installer` (files0444, dirs0555); isolated
`/opt/genia/build-venv`; the generated wheel in `/opt/genia/editable-wheel`;
source and deployment venv; and the copied `/usr/local/bin/uv`. No backend/tool
distribution enters deployment44. Input/build/tool bytes are public and readable
by runtime UID10001. Full A/B comparisons include every retained byte/mode/link,
including input files, scaffold, builder and editable output. Only declared /tmp
caches/receipts are scratch; no opportunistic retained-file deletion is allowed.
Specifically, `/tmp/uv-cache`, `/tmp/frontend-receipt.json` and a dedicated declared
`TMPDIR` (for example `/tmp/frontend-tmp`) must be on **tmpfs**, or removed in the
**same future RUN before its layer is committed**. Never copy these paths, HOME
caches or kernel/interpreter cache receipts into a retained layer. Host evidence
preserves receipts separately; that does not authorize retaining them in an image.
Pinned `--no-cache venv` and `pip check` leave HOME/TMPDIR empty. The later `uv run`
smoke diagnostic leaves an empty `uv-*.lock` coordination file in TMPDIR even with
`--no-cache`; it is explicitly inventoried temporary scratch under the same policy,
not an installed-output exclusion. The non-root verification harness checks empty
HOME/TMPDIR immediately after build, then accepts only empty regular uv lock files
after smokes; HOME stays empty. Its first overbroad TMPDIR check and corrected
command-level probe are retained in the current evidence. Root execution is
rejected before harness writes; cleanup preserves primary errors and notes failures.
Future OS/Git canonicalization/ownership and image-layer work remain separately
authorized construction, not performed by this frontend or host test.

## 4. Offline OCI construction and two-build rule (A4)

Construction is a later authorization. Use the hash-pinned standalone BuildKit
0.24.0 native OCI worker and bundled runc on an approved, receipt-qualified $0 Linux/amd64 venue. No buildx/container
driver image is required. Give each build a fresh independent daemon root/socket,
no imported cache, the same readonly context/base layout and fixed platform.
Do not start either daemon now. Their actual command, version, worker/security/
snapshotter settings and external network denial must be recorded during execution.

**R5 provenance limit:** BuildKit is a first-use hash pin without publisher
attestation. The independent reviewer re-downloaded from the same release URL;
that corroborates bytes, not independent publisher provenance. The maintainer
accepted retaining this design limitation; no signature/checksum attestation is
implied, and no artifact hash changes here.

**R6 first build-phase gate, after separate authorization:** use rootful UID 0,
`--rootless=false --oci-worker-rootless=false --oci-worker=true
--containerd-worker=false --oci-worker-snapshotter=native
--oci-worker-binary=/opt/pinned-buildkit/bin/buildkit-runc
--oci-worker-platform=linux/amd64 --oci-worker-net=bridge
--oci-worker-gc=false --oci-max-parallelism=1`, and fresh explicit root/socket A/B.
Keep process sandboxing enabled; no insecure/host-network entitlements. Both
builds must match these settings. Verify root permissions and
`buildctl debug workers --verbose` labels/platform/snapshotter/executor against
the declared profile. No fallback to rootless, overlayfs or another worker if
the selected venue cannot support it; return to review. CLI help confirms these options
exist, not that this profile works on any selected venue.

Before any image build, run a **no-network, metadata-only frontend lint request**
with the pinned buildctl: same local context/base OCI binding/policy as below,
`--opt frontend.caps=moby.buildkit.frontend.subrequests --opt requestid=frontend.lint`,
and **no image/OCI output exporter**. Require successful parsing/context/policy
handling and inspect `result.statuscode`/lint metadata; retain failures and STOP
on unsupported syntax. No fictitious `--dry-run` flag is assumed. The request ID
comes from pinned BuildKit 0.24 source; no such solver/daemon request ran here.
Use [offline-source-policy.json](offline-source-policy.json); its JSON structure
is statically checked, while actual matching/denial semantics remain a build-phase
gate. Verify a forbidden remote-source request is denied before network activity.
Frontend lint does **not** prove `rewrite-timestamp` behavior on the OCI exporter:
validate that separately during the authorized export/two-build phase and STOP
if unsupported or non-deterministic. No current syntax check is called a build.

The intended build command uses documented BuildKit 0.24 local-OCI context syntax:

```bash
SOURCE_DATE_EPOCH=1793034850 /opt/pinned-buildkit/bin/buildctl \
  --addr unix:///run/runner-build-A.sock build --no-cache --progress plain \
  --frontend dockerfile.v0 \
  --local context="$context" --local dockerfile="$context" \
  --oci-layout public-base="$base_layout" \
  --opt context:public-base=oci-layout://public-base@sha256:e8a38829209aea82774882e5157e1f7c3e8c8393ff53a697b3580896e57f345c \
  --opt platform=linux/amd64 --opt build-arg:SOURCE_DATE_EPOCH=1793034850 \
  --source-policy-file "$context/offline-source-policy.json" \
  --metadata-file "$out/build-A.metadata.json" \
  --output type=oci,dest="$out/build-A.raw.oci.tar",oci-mediatypes=true,rewrite-timestamp=true,compression=gzip,compression-level=9,force-compression=true
```

No provenance/SBOM attestation is requested; direct buildctl has no buildx default
attestation. Reject unexpected attestation descriptors in the resulting index.
The source policy DENYs wildcard `docker-image://*`, `http://*`, `https://*` and
`git://*`; only pinned local inputs/OCI layout are allowed. Also deny builder
egress at the host boundary: source policy and RUN network flags alone do not
prove all daemon activity is offline. No host-network/insecure entitlement.

Repeat with fresh root/socket/output B, without importing A's cache. Preserve
both outputs, failures, stdout/stderr, traces, durations and manifests. Extract
the OCI archives safely and hash raw `index.json`, the referenced linux/amd64
manifest/config and every layer. Verify descriptor sizes/hashes and platform.
Report **archive SHA256, index SHA256, manifest digest, config digest and layer
digests separately**. A local Docker image ID is only config identity.

If the raw OCI carrier tar has varying headers/order, record both raw hashes and
canonicalize only the carrier: sorted USTAR entries, uid/gid 0, fixed names/modes
and SOURCE_DATE_EPOCH; do not modify any OCI JSON/blob to force equality. Hash the
canonical distributable archive too. Require equal image manifest/config/layer
digests across builds and equal canonical archive bytes. Record index equality
and any exact carrier-only differences. Any manifest/layer nondeterminism or
unexplained byte difference blocks “frozen”; list differing bytes rather than
retry-to-green or accepting an image ID as a substitute. No registry upload or
paid storage is needed for OCI export. No final digest is claimed in this phase.
