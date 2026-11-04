# #1285 — revised public runner design and pin acquisition (A1–A8)

Date: 2026-11-04. **PUBLIC ONLY / DESIGN CANDIDATE / NOT BUILT, FROZEN OR ACCEPTED.**
Agent: Codex; branch `issue-1285-public-runner-a1-a8`.
Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285).
Original proposal: `aebcd4cb65946d42a14315407b2e8ea616948c3c`.

The [independent Claude Code review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6617856864)
returned **PASS-WITH-REVISIONS** for the original design. It supersedes that
proposal's historical “Claude review unavailable” status, not its execution gates.
The [maintainer decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6634461919)
authorizes this A1–A8 design amendment and pin acquisition only. **STOP before
image construction.** A fresh independent Claude Code delta review of this exact
resulting commit is still pending; the original review does not approve new pins.

**Current decision: BLOCKED for complete pin closure/build authorization.** All
eight amendments are specified below and in the linked recipe/checklist. Public
wheel/tool/base-byte acquisition passed, but immutable Debian metadata/Git/Tini
closure is blocked by the current network policy. BENJAMIN execution access is
unverified. No image was assembled, built, run or exported; no project dependency
installation, Genia editable build or regression was performed in this phase.

## Scoped preflight

1. Classification/owner: required infrastructure, release-independent public
   reproducibility for the Outcome-aware validated-pipeline experiment. Maintainer
   owns decisions. Scope is amended design, exact public pins/gaps, offline recipe,
   static/acquisition checks and structured issue handoff. Excludes private data,
   oracle/candidate code, comparisons, runtime/semantic changes, R29 work, CI edits/
   dispatch, paid services, merge and issue closure.
2. Sources: fetched main remains `0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5`.
   Latest AGENTS blob `e913e9d093f5913a4797173f56524c80380b815c`; authority and
   process/strategy files match the original-proposal baseline. Read current
   navigation/material sections of STATE/RULES/REPL/README, AGENTS, roadmap,
   killer workflow, applicable run-change/preflight/LLM/token-efficient guidance,
   execution-realization, issue handoffs, original design, review and maintainer
   decisions. STATE remains final language authority, never these experiment pins.
3. Maturity: N/A, design/data/process only. All controls/OCI behavior remain proposed.
4. Portable/host boundary: no language, Core IR, Python or C++ implementation
   change. Linux amd64 acquisition targets only the Python reference-host experiment.
5. Verification: exact byte/size hashes, original lock graph and wheel metadata,
   read-only uv export, isolated editable-requirements hook (not build), public
   archive inspection, CLI version/help/static syntax, links/scope/authority checks.
   Full regression and build tests are later gates, not replaced by these checks.
6. Examples: process-only recipe/checklist; no new Genia program or benchmark case.
7. Complexity: one candidate manifest, two exact wheel requirement files, evidence,
   recipe/gap inventory/checklist. No supervisor, alternate semantic runner or
   repository-wide dependency policy is introduced.
8. Cross-file impact: this process record and public-runner artifact directory,
   plus forward-link maintenance in the historical replay record. STATE/RULES/
   REPL/README/book/cheatsheets/specs remain accurate without edits because no
   implemented behavior/example changes. MCP language-knowledge impact: none.
   Pin accuracy/provenance and honest unresolved gates are material risks.
9. Philosophy: minimalism, explicit authority, semantics outside adapters,
   pattern-first preservation and validated-pipeline relevance: YES.
10. Phases: authorized preflight/design amendment + acquisition → Claude delta
    review → STOP for separate build authorization. No runtime contract/RED/
    implementation phase is applicable now. Later executable build/control code
    requires its own applicable tests/maintainability review/evidence audit.
11. Seven portability fields: STATE authority unchanged; boundary is Linux public
    execution infrastructure; existing specs/tests remain future evidence; no new
    capability vocabulary; no host-parity claim; no new host gaps/skips; synchronize
    experiment evidence only. Python/C++ semantic implementation effects: none.
12. GO/BLOCKED: original provenance and completed acquisition checks PASS; complete
    OS/pin closure and independent delta review BLOCKED. No build authority is
    inferred from the previous review or the chosen venue.

## Immutable pair — preserved without overlays

| Input | Exact identity |
|---|---|
| Executed-source candidate | `9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90` |
| Source tree | `a1a2730e6d8ff7051d88ae118212b28209067152` |
| Original BENJAMIN lock | `02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8`, 284838 bytes |
| pyproject SHA256 | `cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc` |
| Runtime / tool | official CPython 3.12.15 linux/amd64 / uv 0.13.5 |
| SOURCE_DATE_EPOCH | `1793034850` (approved source commit time) |

The original lock was neither regenerated nor copied over a live checkout lock.
Only disposable exports received a read-only copy. It remained identical after
export and backend-hook checks; all tracked source blobs remained unchanged.
The later main baseline differs by 341 paths/14 src paths; same pyproject is not
same source. Preserve original runtime and old fixture. No #1295 overlay or later
semantic source substitution. Its fixture-corrected 7,136/60/0 evidence remains
historical evidence about another source, not this candidate's regression result.

## A1 — exact pin manifest, selection and explicit gaps

[pins.json](../experiments/issue-1285/public-runner/pins.json) is a **review
candidate**, not a claim of completed review or build readiness. It covers source,
base manifest/config/layers, effective base OS inventory, proposed Debian origin/
missing package fields, uv, BuildKit, seven backend wheels and all 50 non-project
lock wheel variants with exact filename/URL/size/SHA256. Each multi-wheel choice
is explicit, including backrefs, charset-normalizer, both coverage versions and
tomli; installation never resolves an ambiguous wheel name.

The immutable Debian origin is proposed as
`https://snapshot.debian.org/archive/debian/20261021T000000Z/`, suite trixie/main,
amd64. Release request failed proxy HTTP 403; active policy still excludes the
host. User intends to enable it, but observed access has not changed. Release/
signature/index hashes, Git/Tini/new-tool `.deb` filename/version/size/hash and
complete dependency/shared-library closure remain **null/empty and STOP-blocking**.
Do not use a moving apt index, guessed hashes or the current host's docker-init.
Verify the signed Release → Packages → `.deb` chain once access exists.

Verified base layers contain 87 installed-package entries, including libc6 2.41,
shell/coreutils/util-linux and their inherited libraries. Proposed additional roots:
Git, Tini, procps and lsof; actual full exec/writable-path inventory remains G2.
Inventory inherited bytes separately from newly supplied snapshot `.deb` closure.

Exactly one compatible wheel was selected and byte-hashed for each of all **50**
non-project lock variants. Read-only marker traversal selects **43** third-party
distributions for CPython 3.12/Linux, plus Genia = **44** final entries. All active
wheel metadata requirements are satisfied. The 50-item inventory includes inactive
variants for completeness; only 43 selected files enter runtime installation.
[runtime.requirements.txt](../experiments/issue-1285/public-runner/runtime.requirements.txt)
and [backend.requirements.txt](../experiments/issue-1285/public-runner/backend.requirements.txt)
use exact local wheel filenames and single allowed hashes, no sdist fallback.

**Review correction:** colorama stays selected: mkdocs-material 9.8.0 declares
unconditional `colorama>=0.4`; original lock graph and uv export agree. MkDocs and
pytest's Windows-only edges do not negate that edge. The review's exclusion
statement is incorrect for this approved lock. Exclude exceptiongroup, tomli and
typing-extensions plus the four inactive below-3.11 version variants instead.
No lock edits are made to conform to an incorrect exclusion.

uv wheel hash is `fa8d26e08e34c29c0c4e820cf3181757086d547240b4f4d31ff1d8bd810ca946`;
extracted executable hash is
`8a70db72685b7138121bfcda71fa1a00cb709ed9f1fdc4ecf1dd871e8e167e52`
(matches historical replay). BuildKit 0.24.0 archive and all bundled binaries are
hash-pinned; buildctl/buildkitd version checks passed. Use builtin dockerfile.v0,
native OCI worker/bundled runc, no external frontend/buildx dependency. BuildKit
archive bytes were hashed without an independent publisher checksum attestation.

Seven pinned backend wheels satisfy declared CPython 3.12 requirements. An isolated
host Python 3.12.14 requirements-hook call returned `["editables~=0.3"]`, satisfied
by editables 0.6. No build/install ran; official-image hook/installation validation
must still occur after authorization. Unexpected requests STOP, never download.

## A2 — official interpreter decision and unverified venue

Maintainer selected official digest-pinned CPython 3.12.15, **not interpreter-
equivalent to original BENJAMIN** (managed Clang 22.1.3 executable hash `0886fb76…`).
Verified platform manifest:
`sha256:e8a38829209aea82774882e5157e1f7c3e8c8393ff53a697b3580896e57f345c`.
Config and four layer bytes match descriptors. Archive-only inspection found
official interpreter executable hash
`0e6475dfda68a9b2d93501449fc47593ca169010e8f4881577b97463fd0c1263`
and GCC/static sysconfig facts; no interpreter execution is claimed. ABI/compiler/
crypto/SQLite/zlib/glibc runtime inventory remains required during later execution.
No multiarch index or final runner digest is invented.

BENJAMIN's existing WSL2/Docker is the **proposed** $0 venue. Actual build/run/
export/cgroup-inspection rights and standalone worker support are unverified.
Current-executor read-only daemon evidence is not a substitute or authorization.

## A3 — fully offline, hash-enforced procedure

[Offline recipe](../experiments/issue-1285/public-runner/offline-build-recipe.md)
specifies local OCI base input, immutable `.deb` closure, single uv, exact local
wheel requirements and `--require-hashes --only-binary :all: --no-build --no-deps
--offline --no-index` installation. Backend wheels have a separate hashed file.
Only the explicit, source-hash-verified first-party Genia PEP-660 operation uses
`--no-build-isolation`; no third-party source build, implicit hook download or
lock regeneration. Remove four transient backend-only packages; final inventory
must exactly equal 43 selected distributions plus Genia, with no import-path leak.
Use venv Python directly for public checks; unchanged nested uv is offline and
hash/version/PATH-verified. This removes unverified `uv run --no-sync` assumptions.

Read-only `uv export --frozen --offline` succeeded without lock mutation. Universal
export is a cross-check, not permission to install inactive variants. A missing
cache/metadata failure in the old lock-only precheck must retain stderr and be
classified as infrastructure-blocked/unknown rather than asserted lock drift.
That precheck never proves installability or E2 equivalence.

## A4 — deterministic OCI output and two-build comparison

The recipe pins BuildKit/frontend/worker inputs, fixed platform/context/source
time and no imported caches. Local OCI base removes registry lookups; deny remote
sources and daemon egress, and use RUN network=none. Export OCI locally with
timestamp rewriting and fixed compression; no registry push, SBOM/provenance
attestations or paid storage. Capture raw archive SHA256 plus index, manifest,
config and layer digests distinctly; image ID alone is not a manifest digest.

Two independent fresh daemon roots build identical reviewed inputs. Verify OCI
descriptors and compare manifest/config/layers; canonicalize only outer tar
headers/order if needed, recording raw/canonical hashes and exact differences.
Require equal manifest and canonical distributable bytes. Do not modify JSON/
layers or retry away failures. Any unexplained/non-carrier nondeterminism blocks
“frozen”; a byte-difference list is evidence, not automatic acceptance.

## A5 — optional tools and exact skip-set comparison

First runner excludes Node, installed MCP client and Wasmtime, by maintainer
decision. Inventory absence and other gated tools; unshare stays required from
base util-linux, with actual syscall/security behavior measured. No fake tools,
test edits, skip additions, omitted cases or deadline relaxation.

Compare direct BENJAMIN and runner **full per-test node-ID → outcome/phase/reason**
maps, collection sets and both partitions, retaining JUnit/verbose full-ID logs
and skip reasons. Every extra skip or omission is an explicit E2 gap. Aggregate
historical “60 skips” is insufficient. Intended optional exclusion does not make
missing coverage pass equivalence. New optional tools later require pins/review.

## A6 — deterministic Git and declared writable paths

Recipe canonicalizes a fresh public shallow exact-commit `.git`: sorted object
order, single-thread non-reusing fixed-compression pack, deterministic index,
fixed config/ref/shallow, no reflogs/fetch metadata/hooks, fixed timestamps. Runtime
UID/GID 10001 owns source/.git; no wildcard safe.directory workaround. Verify actual
bytes across builds and Git access as that UID. No live-checkout `.git` is copied.

Declared runtime writes: `/tmp` (HOME, bytecode if enabled, pytest cache/basetemp,
uv cache/scratch), `/dev/shm`, `/evidence` only. Root/source/venv are read-only.
G2 requires actual write tracing; unexpected writes demand reviewed deviation,
not silent writable-source mounts. Fixed build normalization paths are recorded
up front; no arbitrary post-comparison deletion to manufacture reproducibility.

## A7 — measured controls and bounded evidence

[Acceptance checklist](../experiments/issue-1285/public-runner/acceptance-checklist.md)
defines neutral reaping/EOF/TERM/intermediate-parent-SIGKILL controls, actual
PID 1/orphan PPID/wait/zombie observations, raw exit/signal propagation, original
unchanged reaping test alone and in full regression, and no double init. Prior
process-local subreaper evidence remains historical, not image verification.

Measure inside cgroups **and** Docker inspect: two CPU quota, 4 GiB memory, no
extra swap, PID cap; prove CPU throttling, bounded EAGAIN/PID events and separate
OOM-kill event probes. Record full-run memory/RSS/PID/thread peaks and competing
work; two xdist workers are explicit despite host os.cpu_count. Diagnostic PID
calibration at 1024 precedes reviewed final headroom selection; 256 is not assumed
sufficient. tmpfs/shm pages count within memory. Measure loopback/external network,
RO filesystem and writable mount behavior; do not infer enforcement from flags.

External watchdog uses TERM through PID 1 then bounded KILL, with actual signal/
cleanup receipts and both partitions retained. `/evidence` is a 64 MiB host tmpfs
bind with verified capacity/inode bound, not unbounded disk; logs/stream copies
and total retained evidence have explicit caps/overflow failure. Mount privileges
are unverified. Future benchmark 60 s/16 MiB invocation bounds remain unchanged.

## A8 — direct BENJAMIN capture and E0–E3

The checklist requires direct host versions/WSL/kernel, Docker cgroups/runtime/
storage/security, PID 1/controllers/limits, executable paths/versions/hashes,
Python compiler/ABI/crypto/SQLite/zlib/glibc, Git/gated tools, locale/TZ, installed
inventory/import paths, source/lock/pyproject hashes, process tree/reaping control,
six separate command logs, both per-test result maps, wall time and RSS/PID peaks.
Use a new disposable public export; preserve live lock/checkout. No access is
claimed or private material requested.

E0 = exact source/lock identity; E1 adds installed-set/import evidence; E2 adds
complete matching per-test outcome IDs/phases/reasons; E3 adds measured timing/
resource/toolchain context with differences disclosed. The original Python build
differs; no patch-version-based equivalence. Without direct per-test data only
E0–E1 can be claimed **when their own receipts pass**. This phase establishes
pin identities/acquired bytes, not a new direct E1/E2/E3 or worker-custody result.

## Evidence, delta review and next action

[Pin acquisition evidence](../experiments/issue-1285/public-runner/pin-acquisition-evidence.json)
records read-only export/hook and downloaded archive/wheel checks, actual tool/
interpreter scope and preserved network failures. Old
[preparation-evidence.json](../experiments/issue-1285/public-runner/preparation-evidence.json)
is explicitly the original task's historical snapshot; new base-byte acquisition
supersedes only its metadata-only acquisition limit, not an execution gate.
[Gap inventory](../experiments/issue-1285/public-runner/pin-gaps.md) separates
completed pins from STOP conditions. Static checks do not replace future offline
installation, measured controls, two-build OCI or full original-source regression.

Independent Claude Code delta review must inspect this exact committed diff and
pins, A1–A8 coverage, colorama correction, unresolved OS fields and gate language;
record reviewer/session/model and exact reviewed SHA, ranked findings and verdict.
No authenticated callable Claude route is available here. Publishing a review
request/handoff is not obtaining PASS; no Codex self-review is substituted.

**Next owner/operator actions:** complete supported snapshot-host access and
verified OS/Tini/Git pins, then obtain the independent Claude delta review. Owner
must separately demonstrate/authorize the BENJAMIN bounded build only after those
gates; later acceptance runs require their own authorization. This phase maintains
$0 incremental spending: existing workspace and public downloads only; no paid
API/infrastructure/storage/billing change, image construction, CI dispatch,
private benchmark/custody/equal-worker claims, merge, issue closure or R29 work.
Token usage, invoice totals, review time and savings are not measured.
