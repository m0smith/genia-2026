# Offline public runner recipe — review draft, DO NOT BUILD

This is a design artifact. The maintainer authorized pin acquisition, not image
construction. [G1–G5](pin-gaps.md) and independent Claude delta review remain open.
No command in the construction sections below was executed. Commands with unknown
OS inputs deliberately cannot be completed; this is not a runnable accepted build.

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
runner-input/runtime/      exactly 43 selected wheels
runner-input/backend/      exactly seven pinned backend wheels
runner-input/debs/         complete reviewed .deb closure — CURRENTLY MISSING
runner-input/uv            extracted, hash-verified uv 0.13.5 binary
runner-input/runtime.requirements.txt
runner-input/backend.requirements.txt
runner-input/input-sha256.txt
```

The requirement files use explicit `/opt/runner-input/.../<filename>.whl` paths
and a single allowed SHA256 for each artifact. Re-hash the lock and verify every
tracked source blob against the approved tree before/after export, hook, install
and context creation. Hash all recipe/config/requirement files as well as packages.
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

## 3. Offline image operations (A3)

Use a Dockerfile **without `# syntax=`**. Its builtin frontend is pinned by
BuildKit 0.24.0, not an implicitly fetched frontend image. `FROM public-base`
is supplied by the digest-bound local OCI named context in section 4. Every RUN
uses `--network=none`. No ADD URL, git fetch, apt update or package download.

After copying the manifest-verified context to fixed paths, the future build:

- Verifies `input-sha256.txt` and a separately supplied expected manifest hash.
  Rejects missing/extra artifacts and symlink/path traversal. Verifies original
  lock/source before any install. This validation code is still to be implemented
  and independently reviewed in the later build phase, not assumed to exist.
- Installs the closed `.deb` set offline with `apt-get --no-download
  --no-install-recommends --no-remove --yes`, local `.deb` arguments, no sources
  or sourceparts and no network. A missing dependency fails. Never invoke an
  online repair command. Record exact resulting dpkg inventory; inspect all
  Depends/Pre-Depends/ELF paths. Tini must come from this snapshot and its installed
  binary hash/version must be recorded. This operation is blocked by G1 today.
- Copies the single pinned uv executable to `/usr/local/bin/uv`. Does not install
  the uv Python distribution into the project venv. Verifies version and binary
  hash; rejects any second distinct uv executable on PATH.
- Creates the venv using official `/usr/local/bin/python3.12`, with no seed,
  system-site-packages or interpreter download. Backend acquisition/install uses
  only the seven pinned wheels. The following is the intended exact CLI pattern:

```bash
set -euo pipefail
export UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never PYTHONDONTWRITEBYTECODE=1
export PYTHONNOUSERSITE=1 PYTHONHASHSEED=0 TZ=UTC LANG=C.UTF-8
export UV_CACHE_DIR=/tmp/uv-cache
uv --no-config venv --offline --no-python-downloads \
  --python /usr/local/bin/python3.12 /opt/genia/venv
uv --no-config pip install --python /opt/genia/venv/bin/python \
  --offline --no-index --require-hashes --only-binary :all: --no-build --no-deps \
  -r /opt/runner-input/backend.requirements.txt
uv --no-config pip install --python /opt/genia/venv/bin/python \
  --offline --no-index --require-hashes --only-binary :all: --no-build --no-deps \
  -r /opt/runner-input/runtime.requirements.txt
```

Run `get_requires_for_build_editable({})` in that venv on the exact source; require
the recorded result `["editables~=0.3"]` and verify it is satisfied by the pinned
backend set. The local host 3.12.14 check is evidence, not a target-image check.
Unexpected requirements fail; no dynamic installation is permitted.

Only the **first-party Genia PEP-660 editable operation** is allowed next. Third-party
source/sdist builds remain prohibited. The source tree is hash-verified rather
than pretending an editable local directory can use pip's `--require-hashes`:

```bash
uv --no-config pip install --python /opt/genia/venv/bin/python \
  --offline --no-index --no-deps --no-build-isolation --editable /opt/genia/source
uv --no-config pip uninstall --python /opt/genia/venv/bin/python --offline \
  editables hatchling tomlkit trove-classifiers
```

Remove only those four transient backend-only distributions. Retain packaging,
pathspec and pluggy (they are original runtime/dev dependencies). If editable
metadata/runtime actually requires any removed distribution, STOP; do not hide
that discrepancy. Verify the final inventory is exactly the 43 target wheels
plus Genia 0.1.14, with their source/import paths, no excluded variants or user/
global site-packages, and no extra roots. Re-hash original lock and tracked source.
No `uv sync` or lock regeneration is part of this recipe.

Disable bytecode generation during construction, remove generated `.pyc` only
under new venv/source paths, and normalize declared volatile build files:
`/var/log/apt/*`, `/var/log/dpkg.log`, `/var/cache/ldconfig/aux-cache`, build caches
and temporary acquisition inputs. Record this fixed normalization set. Do not
delete arbitrary differences after seeing the two-build outcome. Any other
non-deterministic package-generated bytes require a design revision and review.

Final configuration: `USER 10001:10001`, working directory `/opt/genia/source`,
PATH `/opt/genia/venv/bin:/usr/local/bin:/usr/bin:/bin`, and exec-form entrypoint
`["/usr/bin/tini", "-g", "--"]`. No Docker `--init` (no double init). Source and
venv remain read-only at run time. HOME/uv cache/pytest basetemp/pytest cache live
under `/tmp`; no inherited Python/uv project selectors. `UV_OFFLINE=1` and
`UV_PYTHON_DOWNLOADS=never` prevent nested uv acquisition. Final public commands
follow repository policy through pinned `uv --no-config run --frozen --offline
--no-sync`, with `UV_PROJECT_ENVIRONMENT=/opt/genia/venv` and
`UV_PYTHON=/opt/genia/venv/bin/python`. Prove actual interpreter selection and no
lock/environment creation or writes in the target; do not infer that from
`--no-sync` alone. The unchanged MCP fixture invokes its configured pinned uv.

## 4. Offline OCI construction and two-build rule (A4)

Construction is a later authorization. Use the hash-pinned standalone BuildKit
0.24.0 native OCI worker and bundled runc on verified BENJAMIN. No buildx/container
driver image is required. Give each build a fresh independent daemon root/socket,
no imported cache, the same readonly context/base layout and fixed platform.
Do not start either daemon now. Their actual command, version, worker/security/
snapshotter settings and external network denial must be recorded during execution.

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
