# Public runner pin gaps — A1–A8 revision

Status: **review candidate; BLOCKED for build authorization**. No runner is built,
frozen or accepted. See [pins.json](pins.json) for exact acquired artifacts and
[acquisition evidence](pin-acquisition-evidence.json) for commands/failures.

| ID | Gap / current evidence | Required disposition / owner |
|---|---|---|
| G1 | Immutable Debian snapshot `20261021T000000Z` metadata request failed: proxy tunnel HTTP 403. The active policy does not include `snapshot.debian.org`. No Release/index signature/hash, `.deb` list, Git package closure or Tini artifact is verified. Their fields are null/empty; `closure_complete=false`. | Environment operator enables the host through supported policy configuration; then Codex acquires and verifies the immutable Release/signature/Packages chain and every selected `.deb` (filename/version/architecture/size/SHA256). The user intends to enable it; intent is not observed access. Never substitute a moving apt index or invent package hashes. |
| G2 | Static approved-source references identify Git, Python, uv, `/bin/sh`, unshare, ps and lsof; historical reaping evidence observes Python/uv. A complete BENJAMIN `execve` trace and writable-path trace do not exist here. Proposed new roots are Git, Tini, procps and lsof; 87 base installed-package entries (including util-linux/shell/coreutils) are inventoried from verified base bytes. | BENJAMIN operator captures full public verification exec/write inventories. Reconcile the package closure and declared writable set before acceptance. Static references are not a dynamic observed execution inventory. Unexpected required binaries/writes STOP; no silent extra tools/mounts. |
| G3 | BENJAMIN is the maintainer-selected **proposed** venue; build/run/export/cgroup-inspection privileges and standalone BuildKit worker support remain unverified. Current-executor observations do not establish those rights. | Owner demonstrates permissions/cgroup access using public, bounded operations in a separately authorized phase. No present build authorization. |
| G4 | Original Claude Code review is PASS-WITH-REVISIONS at `aebcd4cb...`; that is not review of this new pin set. No callable Claude Code CLI/connector/session is available here. | Independent Claude Code delta reviewer reviews the resulting exact commit, A1–A8, pins, correction to the colorama statement, failures and offline recipe. Record exact reviewed SHA/verdict; no substitute/self-review represented as Claude. |
| G5 | Seven backend wheels and the requirements-hook output are verified on host Python 3.12.14; official target is 3.12.15 with different compiler/linkage. No target install, editable build, control probe, regression, two-build OCI export or direct replay has run. | After complete pins, delta review and separate build authorization, rerun hook in target (exact expected output), prove offline installation/closure, then obtain the separately authorized acceptance evidence. These are future execution gates, not claimed acquisition results. |

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
- Seven backend wheels, declared target closure and local editable-requirements
  hook (`["editables~=0.3"]`), satisfied by editables 0.6. Official target hook
  remains pending; no wheel build/install was performed.
- BuildKit 0.24.0 linux/amd64 archive, bundled binaries, `buildctl`/`buildkitd`
  version checks. Native OCI worker uses the bundled runc. Builtin dockerfile.v0;
  no external frontend or buildx dependency. Archive hash computed from downloaded
  bytes; independent publisher checksum/signature was not acquired. Review that
  provenance limit rather than calling it a publisher attestation.
- `uv --no-config export --frozen --offline --no-python-downloads --all-groups
  --no-emit-project --no-header --no-annotate --format requirements.txt` passed in
  a disposable approved-source export. Lock bytes remained identical. This export
  is universal; installation uses the exact target-wheel requirement files instead.

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
