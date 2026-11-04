# Public runner pin gaps — A1–A8 revision

Status: **review candidate; BLOCKED for build authorization**. No runner is built,
frozen or accepted. See [pins.json](pins.json) for exact acquired artifacts and
[acquisition evidence](pin-acquisition-evidence.json) for commands/failures.

| ID | Gap / current evidence | Required disposition / owner |
|---|---|---|
| G1 | Immutable Debian snapshot `20261021T000000Z` metadata request failed: proxy tunnel HTTP 403. The active policy does not include `snapshot.debian.org`. No Release/index signature/hash, `.deb` list, Git package closure or Tini artifact is verified. Their fields are null/empty; `closure_complete=false`. | Environment operator enables the host through supported policy configuration; then Codex acquires and verifies the immutable Release/signature/Packages chain and every selected `.deb` (filename/version/architecture/size/SHA256). The user intends to enable it; intent is not observed access. Never substitute a moving apt index or invent package hashes. |
| G2 | Static approved-source references identify Git, Python, uv, `/bin/sh`, unshare, ps and lsof; historical reaping evidence observes Python/uv. A complete BENJAMIN `execve` trace and writable-path trace do not exist here. Proposed new roots are Git, Tini, procps and lsof; 87 base installed-package entries (including util-linux/shell/coreutils) are inventoried from verified base bytes. | BENJAMIN operator captures full public verification exec/write inventories. Reconcile the package closure and declared writable set before acceptance. Static references are not a dynamic observed execution inventory. Unexpected required binaries/writes STOP; no silent extra tools/mounts. |
| G3 | BENJAMIN is the maintainer-selected **proposed** venue; build/run/export/cgroup-inspection privileges and standalone BuildKit worker support remain unverified. Current-executor observations do not establish those rights. | Owner demonstrates permissions/cgroup access using public, bounded operations in a separately authorized phase. No present build authorization. |
| G4 | Claude reviewed `00b95b62...` PASS-WITH-REVISIONS, confirmed R1–R8/pins and measured the ctime mechanism. This installation spike/four design corrections have not received independent delta review. No callable Claude Code route is available here. | Request narrow Claude Code delta review of this exact new SHA, helper and full installation evidence; then maintainer chooses metadata strategy. Later review OS/venue deltas when G1/G3 receipts exist. No Codex self-review substitutes for Claude. |
| G5 | Seven backend wheels and the requirements-hook output are verified on host Python 3.12.14; official target is 3.12.15 with different compiler/linkage. No target install, editable build, control probe, regression, two-build OCI export or direct replay has run. | After complete pins, delta review and separate build authorization, rerun hook in target (exact expected output), prove offline installation/closure, then obtain the separately authorized acceptance evidence. These are future execution gates, not claimed acquisition results. |
| Metadata strategy | **UNSELECTED.** Current uv recipe is predicted to fail strict two-build equality. Host proof: 94 wheel-stage and 88 editable-stage files differ from ctime-derived uv_cache and RECORD. PyPA installer 0.7.0 gives zero differences in its two full deployment-prefix comparisons, including PEP-660 Genia; host 3.12.14 only. | Independent delta review, then maintainer selects/rejects strategy and authorizes any production recipe/frontend change. Existing commands remain draft; no metadata rewriting/deletion/exclusions, no weakened equality. Official runtime, script/metadata/bootstrap behavior and full tests remain unproved. |

## Completed acquisition

- Original source `9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90`, original lock
  `02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8` /
  284838 bytes and pyproject hash preserved. No overlays/regeneration.
- Official base linux/amd64 manifest `e8a38829…f345c`, config and all four layer
  blobs: exact bytes/size/hash verified by archive inspection, without assembly or
  execution. Effective base dpkg inventory has 87 installed packages.
- uv 0.13.5: exact wheel URL/filename/size/hash and extracted executable hash;
  executable matches the earlier replay hash. `uv --version` passed.
- Runtime lock: one exact compatible wheel for **all 50 non-project variants**;
  all downloaded bytes/size/hash match the original lock. Marker graph selects
  **43** third-party distributions, plus editable Genia = **44** final entries.
  Alternate versions are acquisition inventory only, never staged for install.
- Seven backend wheels, preliminary declared metadata consistency and local editable-requirements
  hook (`["editables~=0.3"]`), satisfied by editables 0.6. Official target hook
  remains pending; no wheel build/install was performed.
- BuildKit 0.24.0 linux/amd64 archive/binaries and version checks are retained;
  same-URL re-download corroborates hashes without publisher attestation.
- Historical read-only `uv export --frozen --offline` passed in a disposable
  approved-source export with unchanged lock; target requirements narrow that
  universal export to the 43 exact selected artifacts.

The preceding acquisition bullets describe the historical pin phase. R4 now
qualifies closure as **preliminary host metadata/hook consistency**, with
[190 listed/hashed hook inputs](hook-library-inputs.json). R1/R2 correction checks
installed only tiny backend-wheel sets into disposable host environments; no
project/official-target installation was performed. See
[retained correction evidence](recipe-correction-evidence.json).

## R3 / R5–R8 prerequisites retained

- G1 must compare all 87 base versions against verified signed snapshot candidates
  with Debian version ordering. No downgrade; every required base upgrade/origin
  delta reviewed. The earlier timestamp is a candidate, not tested compatibility.
- BuildKit remains a first-use hash pin without publisher attestation. Independent
  same-URL re-download does not create a second provenance channel.
- G3/G5 include the explicit rootful OCI/native/bridge worker profile and future
  no-network lint/context/policy dry-run gate; current help checks are not solver
  execution or proof of OCI timestamp rewriting.
- Hardened-container differences receive cause attribution, never E2 exceptions.
  Optional same-image relaxed diagnostics require separate authorization and are
  labeled non-acceptance; no skip/test edits or replacement of hardened failures.
- G5 includes sequential per-command evidence drain/verification, all tmpfs memory
  charging, 512 MiB text/control budget arithmetic, and separately approved finite
  build/input/OCI storage quotas. Neither a 64 MiB tmpfs nor the log budget is an
  unlimited storage allowance.
- The [new spike](metadata-strategy.md) confirms exact wheel/project ctime-derived
  uv_cache timestamps, RECORD differences and editable uv_build.json. The separate
  directories.src clock mapping remains unconfirmed. Keep historical evidence;
  the unchanged recipe is predicted to fail, requiring a strategy decision before
  build authorization. Fixed paths/mtime/exporter timestamp rewriting cannot fix
  generated content bytes.

## Newly completed TEST/DESIGN evidence, not target closure

One experimental installer pin (0.7.0, no declared dependencies), identical-byte
43-wheel installation and separately pinned seven-wheel Hatchling PEP-660 build
were evaluated on host CPython 3.12.14. All four final identity/import/consistency/
public smoke checks pass. Full venv file manifests, metadata, RECORD checks and
negative/failure evidence are committed under installation-proof. The isolated
builder is not deployment output and is not claimed byte-reproducible. Neither
this evidence nor the expected inventory makes the official closure verified.
Source-policy matchType is explicitly WILDCARD with a new configuration digest;
semantic solver denial remains untested. Enforceable per-stream overflow handling
is specified in the checklist but not implemented or exercised here. G1/G3 stay open.

## Review correction — preserve the lock, not an incorrect exclusion

The original review says colorama must be excluded on Linux. The actual lock,
downloaded `mkdocs_material-9.8.0` wheel METADATA (`colorama>=0.4`, unconditional),
read-only target graph and frozen uv export all select it. MkDocs 1.6.1 and pytest
have Windows-only edges, but those do not negate the Material edge. Keep colorama
0.4.6. Exclude exceptiongroup, tomli and typing-extensions on this target, and the
four alternate below-3.11 version variants. No lock/requirements change is made
to force agreement with the review. The historical 44-entry installed inventory
also includes colorama; this agreement is not a new direct BENJAMIN E1 proof.

The earlier `api.github.com` release-metadata request also failed proxy 403. The
documented public `github.com/moby/buildkit/releases/download/...` endpoint was
used for the archive within the existing allowlist, retaining proxy/TLS checks.
Both failures are preserved. No network-policy bypass or paid service was used.
