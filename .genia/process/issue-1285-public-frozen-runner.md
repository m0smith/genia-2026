# #1285 — revised public runner design and pin acquisition (A1–A8)

## Current status — maintainer decision, 2026-11-07 capture

The [maintainer decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6702416476)
accepts the host-verified frontend at exact SHA
`fd74a5830c76373d724bbd40a603ea85870f0aca`, following independent Claude
[PASS](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6659717443)
and its [directory-count correction](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6659720450).
Earlier frontend-review-pending statements below describe historical phases;
that frontend gate is closed. Low-1–Low-4 and R6/R7 remain maintainer-owned debt;
no new mandatory frontend review loop is required. Dedicated TMPDIR retention
policy, no scratch/cache/receipt/HOME bytes in OCI layers,
PYTHONDONTWRITEBYTECODE and runtime non-root/read-only behavior remain later
image-gate obligations. The immutable `pins.json` is preserved byte-for-byte
from that accepted head; its old review-status fields are historical metadata,
not the current coordination decision.

[G1's fresh public precheck](../experiments/issue-1285/public-runner/g1-precheck/README.md) is BLOCKED by proxy HTTP 403;
G3 venue qualification is a separate lane and is not established here. Neither
frontend acceptance nor parallel prechecks authorizes image build/run/export,
CI dispatch, private work, benchmark trials, merge, issue closure or R29 work.
Strict two-independent-build OCI equality and all later target/resource/reaping,
G2/G5/custody/benchmark gates remain intact; incremental spending stays $0.


Date: 2026-11-04. **PUBLIC ONLY / DESIGN CANDIDATE / NOT BUILT, FROZEN OR ACCEPTED.**
Agent: Codex; branch `issue-1285-offline-frontend` (authorized frontend/host-only phase).
Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285).
Original proposal: `aebcd4cb65946d42a14315407b2e8ea616948c3c`.

The [independent Claude Code review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6617856864)
returned **PASS-WITH-REVISIONS** for the original design. It supersedes that
proposal's historical “Claude review unavailable” status, not its execution gates.
The [maintainer decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6634461919)
authorizes this A1–A8 design amendment and pin acquisition only. **STOP before
image construction.** A fresh independent Claude Code delta review of this exact
resulting commit is still pending; the original review does not approve new pins.

The [Track A preliminary delta review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6635654084)
then independently confirmed the retained pins/43-entry graph at
`778bb1a4e9c24331915005c759b4a44780522b03`, returned PASS-WITH-REVISIONS and proved
the uv flag defect. The [maintainer authorization](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6636833906)
permits only R1–R8/low-severity design corrections and bounded pinned-tool checks.
The R1–R8 revision preserved the verified artifacts. Claude's
[subsequent independent review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6639484157)
confirmed those corrections at `00b95b62842f1907bf2174694b1e3de17ffeccbe` and
identified ctime-derived generated metadata as a predicted two-build failure.
The [maintainer decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6641293474)
authorizes the installation TEST/DESIGN spike and four design corrections below,
**not** adoption of an installer, recipe change or image construction.

**Design-phase decision (historical): installer 0.7.0 SELECTED AS CANDIDATE;
subsequent frontend implementation authority/status is recorded below.** [Independent Claude review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6642696319)
at starting `3fdb037a27dcc555bc5ada85dfe88fe18233f522` returned PASS-WITH-REVISIONS;
[maintainer selection](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6643051249) authorizes only this design/recipe revision.
The historical d591ecf5 revision ran no installation or image experiment.
The later authorized host implementation follow-up below records new results.
The historical host proof uses CPython 3.12.14 (Codex) / 3.12.3 (Claude), not the
official 3.12.15 target. Full regression and independent two-build OCI remain open.
[Current venue policy](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6643155880) removes offline BENJAMIN as an active dependency;
qualify an available approved $0 Linux/amd64 venue by actual receipts. No venue
is qualified here. Historical source/lock/baseline labels remain immutable.

The [selected recipe](../experiments/issue-1285/public-runner/offline-build-recipe.md)
requires umask 022, explicit posix_prefix, complete-set validation before writes,
sorted installation/rejected destination conflicts, isolated pinned Hatchling,
reviewed hashed frontend source, deliberate initial metadata, mandatory project
`uv --no-config run --frozen --offline --no-sync` and distinct launcher --no-project.
The experimental helper remains historical, not production code. G1 signed
immutable Debian OS/Git/Tini closure and venue-neutral G3 receipts remain blocking.
That design delta review completed; the next gate is independent Claude
maintainability/security/behavior review of the implemented candidate.
[Revision evidence](../experiments/issue-1285/public-runner/installer-design-revision-evidence.json)
records bounded static checks; no target tests were executed. No generated
metadata normalization or weakening of two-build equality is approved.

## Authorized frontend implementation follow-up

The later [Claude design delta review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6643785950)
and [implementation authority](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6644232395)
permit RED → frontend implementation → focused host verification, not images.
Implementation commit `150d9cb8da3d5e34aa86efa39ffa6b656fc28b8c` and
[verified implementation/host handoff](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6645166659)
follow RED commit `de1f455823e18f049a87cccbc2934bcb0bc20e11` and its
[verified handoff](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6644332896)
precede code. [Implemented source pins](../experiments/issue-1285/public-runner/frontend/source-pins.json)
and [evidence](../experiments/issue-1285/public-runner/frontend-evidence/implementation.json)
record that historical candidate status. Its initial Claude review and current
R1–R5 delta-review gate are recorded below; no self-approval or production-readiness claim.

M1 permits safe zero-size directory entries omitted from RECORD without output;
M2 preserves all15 ZIP-executable members (ruff included), plus15 wrappers, in the
expected mode inventory. Stdlib-first bootstrap is selected; no member-order
adapter or generated metadata normalization. Builder/tools/editable wheel and
complete input closure are explicitly retained and compared. Source/lock and all
settled artifact pins remain unchanged. Host3.12.14/UID1000 does not establish
official3.12.15/UID10001 or independent OCI equality. G1/G3 remain STOPs. No language
or MCP profile fact changed; authority documents require no edits.

## Focused frontend R1–R5 correction (2026-11-05)

The [independent Claude review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6649295319)
on `65c345100f5c36698364522d5ac4fc5a6e7ceef0` returned PASS-WITH-REVISIONS.
The [maintainer decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6658033204)
authorized only public $0 revisions. Strengthened TEST-ONLY RED
`9b87b220a5a9168f22087cecae748faa8a6def34` and its
[verified handoff](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6658357008)
precede corrected implementation/evidence `2da6d870bed443059eeb56f45709fd23a30b9ccd`
and [host handoff](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6658657164).
All RED tests are frozen. [Current evidence](../experiments/issue-1285/public-runner/frontend-evidence/r1-r5-correction/summary.json)
supersedes earlier source-review-pending status with **independent R1–R5 delta
review pending**, not frontend acceptance or image authority.

Corrections force pinned uv --no-cache, reserve scaffold directories before writes,
reject root at harness entry, preserve primary probe errors through cleanup and
normalize unsupported ZIP compression. The strengthened battery uses RECORD-listed
members and specific diagnostics; 17 validator-removal mutants are assertion-killed.
29 focused tests and 47-wheel validation pass; 7 CLI negatives have zero destination
writes. Two fresh same-host installs differ in all 65 input ctimes/mtimes and match
all 21,073 retained paths (bytes/modes/uid/gid/symlinks); each has exact 44 distributions,
17,780 RECORD rows, 15 wrappers and 10 compiled imports. Original source/lock and all
settled wheel/uv/base/BuildKit pins are unchanged. The input manifest now has 65 entries.

Fake-HOME/no-ambient-cache builds leave HOME/TMPDIR empty. Subsequent uv project
smokes leave only an empty declared TMPDIR coordination lock. The first overbroad
TMPDIR assertion failed and is retained, along with a command-level probe,
initial lint/setup failures and all RED negatives. The recipe requires named
cache/receipt/dedicated TMPDIR paths on tmpfs or removal within the same future RUN
before layer commit. No retained install output is deleted, rewritten or excluded.

Codex separately inspected the committed implementation diff and adjacent call
sites: PASS WITH NON-BLOCKING FINDINGS, with self-review limitation disclosed.
Original R6/R7 debt remains maintainer-owned on #1285 (function length, coordinated
pins/generator, environment/deadline/path policy, bytecode ENV and exclusive
ownership/TOCTOU assumptions); no broad refactor is authorized. Independent Claude
Code delta-only maintainability/security/behavior review is requested before
frontend acceptance. This self-review does not satisfy that independent gate.

This remains CPython3.12.14/UID1000 host evidence, not official3.12.15/UID10001,
read-only mounts, full regression, independent workers or OCI acceptance. G1 signed
OS/Git/Tini closure, venue-neutral G3 qualification, separate image authority and
strict two-independent-build manifest/config/layer/canonical-archive equality
remain required. No image/container build/run/export, private benchmark work,
CI dispatch, merge, closure or R29 work occurred; incremental spending $0,
usage/review effort unmeasured. Authority docs and language semantics are unchanged.

## Scoped preflight

1. Classification/owner: required infrastructure, release-independent public
   reproducibility for the Outcome-aware validated-pipeline experiment. Maintainer
   owns decisions. Scope is amended design, exact public pins/gaps, offline recipe,
   bounded frontend RED/implementation, focused host A/B and negative controls,
   source pins, documentation and issue handoffs; prior spikes remain historical. Excludes private data,
   oracle/candidate code, benchmark comparisons, runtime/semantic changes, R29 work, CI edits/
   dispatch, paid services, merge and issue closure.
2. Sources: fetched main remains `0b25d2b45722f4397fd712f2f4b8eb3ea294f6e5`.
   Latest AGENTS blob `e913e9d093f5913a4797173f56524c80380b815c`; authority and
   process/strategy files match the original-proposal baseline. Read current
   navigation/material sections of STATE/RULES/REPL/README, AGENTS, roadmap,
   killer workflow, applicable run-change/preflight/LLM/token-efficient guidance,
   execution-realization, issue handoffs, original design, review and maintainer
   decisions. STATE remains final language authority, never these experiment pins.
3. Maturity: N/A, test/design/data/process only. All controls/OCI behavior remain proposed.
4. Portable/host boundary: no language, Core IR, Python or C++ implementation
   change. Linux amd64 acquisition targets only the Python reference-host experiment.
5. Historical R1–R8 verification: bounded pinned-uv matrix, listed host requirements-hook
   replay, path-metadata probe, retained pin/requirement equality, CLI help and
   JSON/shell/link/scope/authority checks. Earlier acquisition/graph/export proofs
   are retained with their original scope, not misrepresented as new executions.
   Full regression and build tests are later gates, not replaced by these checks.
   Historical authorized proof: one pinned alternative, two distinct-ctime scratch
   installations per strategy, complete venv byte/mode/link comparison, PEP-660
   Genia/import/identity/offline-consistency/public smoke checks, negative controls
   and retained failed attempts. Target runtime mismatch is explicit.
6. Examples: process-only recipe/checklist; no new Genia program or benchmark case.
7. Complexity: one candidate manifest, two exact wheel requirement files, evidence,
   recipe/gap inventory/checklist and isolated experimental helper. No production supervisor, alternate semantic runner or
   repository-wide dependency policy is introduced.
8. Cross-file impact: this process record and public-runner artifact directory,
   plus forward-link maintenance in the historical replay record. STATE/RULES/
   REPL/README/book/cheatsheets/specs remain accurate without edits because no
   implemented behavior/example changes. MCP language-knowledge impact: none.
   Pin accuracy/provenance and honest unresolved gates are material risks.
9. Philosophy: minimalism, explicit authority, semantics outside adapters,
   pattern-first preservation and validated-pipeline relevance: YES.
10. Phases: accepted design → independent Claude delta review → maintainer
    RED/implementation authority → separate RED commit → frontend implementation
    and focused host verification → current non-authoritative docs/handoffs.
    Independent Claude maintainability/security/behavior review is pending.
    No language contract/semantic RED phase is applicable; these are infrastructure
    tests only. Stop before separate image/build/target acceptance authority.
11. Seven portability fields: STATE authority unchanged; boundary is Linux public
    execution infrastructure; existing specs/tests remain future evidence; no new
    capability vocabulary; no host-parity claim; no new host gaps/skips; synchronize
    experiment evidence only. Python/C++ semantic implementation effects: none.
12. GO/BLOCKED: candidate selection and later frontend implementation authority verified;
    RED/implementation/focused host publication authorized. Original provenance
    and artifacts retained. OS closure, venue qualification, independent source
    review and later build/target/acceptance remain BLOCKED. No build authority is
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
This is **preliminary host metadata/hook consistency**, not complete target closure.
The overstrong `declared_target_closure_complete` field is replaced by explicitly
preliminary status. [Hook input listing](../experiments/issue-1285/public-runner/hook-library-inputs.json)
records all 190 files/size/SHA256 from the same seven wheel inputs and a clean
isolated `-B` host replay, with unchanged source/library bytes. It does not
retroactively attest the earlier unlisted directory or the official target.

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

An available approved $0 Linux/amd64 venue must demonstrate build/run/OCI-export,
cgroup inspection/enforcement, pinned rootful OCI/native worker, finite disk/inode/
evidence bounds, reaping and offline controls. BENJAMIN is offline and not required;
historical source/lock/baseline evidence stays intact. No host qualifies by
declaration or current-executor inspection. Two independent builds remain required.

## A3 — fully offline, hash-enforced procedure

[Offline recipe](../experiments/issue-1285/public-runner/offline-build-recipe.md)
now selects installer 0.7.0 as candidate wheel writer, with complete archive/RECORD/
path/destination validation before any installation writes, deterministic sorted
order and explicit posix_prefix roots. umask 022 covers every scaffold/install/
editable step. Full file/directory/link mode/ownership inventories must prove
0644/0755 deployment access as UID 10001, distinct from root build identity.
The original helper's implicit scheme/per-wheel checks/umask 077 are not adequate
production evidence. The implemented host candidate is linked above; independent source review
and official-target execution remain pending.

The isolated builder contains exactly seven unchanged pinned wheels at
/opt/genia/build-venv; target hook output must equal ["editables~=0.3"]. Only
first-party source-hash-verified Genia is built editable at fixed /opt/genia/source.
All reviewed orchestration/validation/bootstrap/ordering/metadata sources need
their own hashes in input-sha256.txt before later use. Runtime prefix has 43 then
44 distributions; historical 47-entry union and seven builder identities stay exact.
No third-party source build, implicit acquisition, transient backend uninstall or
lock regeneration. Offline uv consistency checks and exact import/artifact
inventories are required after runtime wheels and editable installation.

Retain uv 0.13.5 for venv/check/test/launcher use. Project commands require exact
`uv --no-config run --frozen --offline --no-sync` against the read-only selected
venv; prove no lock/write/automatic rebuild. Preserve the unchanged configured
MCP launcher's distinct --no-project behavior. Initial INSTALLER/PEP-610/RECORD/
wrapper policy and intentional uv differences are explicit in the recipe; no
post-hoc metadata patching/deletion/exclusion is permitted. Zero .pyc required.

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
R5 keeps BuildKit's **first-use hash pin without publisher attestation** explicit;
same-URL reviewer re-download is byte corroboration, not independent provenance.
R6 declares rootful OCI/native snapshotter settings, a pinned metadata-only lint/
local-OCI/source-policy first gate, and separate OCI-export semantics verification.
No daemon/solver dry run or image build has run in this correction phase.

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

Collect selected-venue runner A/B **full per-test node-ID → outcome/phase/reason**
maps, collection sets and both partitions, retaining JUnit/verbose full-ID logs
and skip reasons. Compare historical BENJAMIN only as context unless compatible
measured per-test data exists; direct replay there is not required. Every extra skip or omission is an explicit E2 gap. Aggregate
historical “60 skips” is insufficient. Intended optional exclusion does not make
missing coverage pass equivalence. New optional tools later require pins/review.
R7 pre-declares cause classifications and separately authorized, one-factor
diagnostic profiles of the same image. Diagnostic relaxed-profile PASS is never
acceptance or E2; every hardened mismatch/extra skip remains an E2 gap.

## A6 — deterministic Git and declared writable paths

Recipe canonicalizes a fresh public shallow exact-commit `.git`: sorted object
order, single-thread non-reusing fixed-compression pack, deterministic index,
fixed config/ref/shallow, no reflogs/fetch metadata/hooks, fixed timestamps. Runtime
UID/GID 10001 owns source/.git; no wildcard safe.directory workaround. Verify actual
bytes across builds and Git access as that UID. No live-checkout `.git` is copied.

Declared runtime writes: `/tmp` (HOME, pytest cache/basetemp,
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
cleanup receipts and both partitions retained. `/evidence` is proposed as a
64 MiB host tmpfs bind whose capacity/inode bound must be verified; logs/stream copies
and total retained evidence have explicit caps/overflow failure. Mount privileges
are unverified. R8 makes capture sequential: each 56 MiB maximum command bundle
(two 16 MiB streams plus 24 MiB metadata) must be copied, hash-verified and cleared
before the next, leaving 8 MiB free in 64 MiB. The 512 MiB text/control budget is
itemized; OCI/build storage needs a separate finite quota before authorization.
Require verified accounting of all tmpfs pages, including evidence, in the 4 GiB
envelope; overflow fails. No capacity/enforcement result is claimed yet.
Future benchmark 60 s/16 MiB invocation bounds remain unchanged.

## A8 — actual selected-venue receipts and E0–E3

The checklist requires direct selected-venue versions/kernel, Docker cgroups/
runtime/storage/security, pinned Python/uv/Git and ABI/shared libraries, full
installed/import/source/lock identity, reaping/process tree, six command results,
both partition full-ID maps, times/peaks and measured effective controls. Qualify
the actual approved $0 Linux/amd64 venue; no direct BENJAMIN replay is required.
Preserve its historical source/lock/baseline provenance and report limits honestly.

E0 = exact source/lock; E1 adds installed-set/artifact/import evidence; E2 requires
matching full outcome/phase/reason maps between specified compatible runs; E3 adds
measured timing/resource/toolchain context. Historical 7134/60 aggregate cannot
establish per-test parity. E2/E3 historical equivalence is unestablished, not a
public-runner acceptance prerequisite. Full target tests, controls and independent
two-build OCI equality remain acceptance gates. No custody/equal-worker claim.

## Historical R1–R8 evidence and handoff

| Correction | Disposition / evidence boundary |
|---|---|
| R1 | Both install commands use only binary-only enforcement, no conflicting flag. Pinned uv reproduced old exit 2 and corrected success/hash rejection. |
| R2 | Offline consistency checks after wheel install and transient removal, plus exact 47/44 inventories. Tiny host checks pass and detect five missing hatchling dependencies; target checks not run. |
| R3 | All 87 base versions must be compatible with signed snapshot candidates; no downgrade, reviewed upgrades only. Data/access still missing. |
| R4 | Preliminary host consistency replaces complete-target wording; 190 hook-library files listed/hashed. Official target closure remains unverified. |
| R5 | First-use BuildKit hash pin retained without publisher attestation; no verified pin changed. |
| R6 | Explicit rootful OCI/native/bridge settings and future metadata-only lint/context/policy gate; help/JSON checks only now, exporter semantics unverified. |
| R7 | Same-image one-factor diagnostics separately authorized/non-acceptance; understood hardening differences still block E2. |
| R8 | Per-command drain/copy acknowledgement fits 64 MiB; itemized 512 MiB text/control budget and all tmpfs memory charging. Capacity enforcement remains future evidence. |

Low-severity refinements pin the original reaping node, declare environment
differences and fixed retained staging paths, and include actual installer path/
cache metadata in later A/B checks. The host cache-timestamp negative probe is
retained; no target reproducibility is inferred or metadata rewritten.

[R1–R8 correction evidence](../experiments/issue-1285/public-runner/recipe-correction-evidence.json)
retains 17 bounded pinned-uv invocations (including setup and intended rejection
controls), the initial harness/cache failures, listed host hook replay and tool
help checks. No project dependency set, image or benchmark was installed/executed.
Verified wheel/backend/uv/BuildKit/base pin records and both requirement files
remain identical to the independently reviewed candidate.

[Pin acquisition evidence](../experiments/issue-1285/public-runner/pin-acquisition-evidence.json)
records read-only export/hook and downloaded archive/wheel checks, actual tool/
interpreter scope and preserved network failures. Old
[preparation-evidence.json](../experiments/issue-1285/public-runner/preparation-evidence.json)
is explicitly the original task's historical snapshot; new base-byte acquisition
supersedes only its metadata-only acquisition limit, not an execution gate.
[Gap inventory](../experiments/issue-1285/public-runner/pin-gaps.md) separates
completed pins from STOP conditions. Static checks do not replace future offline
installation, measured controls, two-build OCI or full original-source regression.

The prior handoff requested independent Claude Code **text** delta review of the
R1–R8/low-severity diff, corrected CLI evidence, qualified hook inputs, preserved
artifact identities, unresolved OS fields and gate language, with
reviewer/session/model, exact reviewed SHA, ranked findings and verdict.
That historical R1–R8 review is linked above. The later installer review covers
3fdb037a; neither reviews this new text-only revision.

The historical next action was independent Claude text delta review. That review
and the candidate selection are now linked above. Current next action is independent Claude review of the new implemented
frontend/tests and complete source/mode/input closure.
G1 supported snapshot access and signed closure, venue-neutral G3 qualification,
independent frontend source/test review and separate build/run authorization stay
open. No image construction, CI dispatch, private benchmark/custody/equal-worker
claim, paid infrastructure, merge, closure or R29 change. Token usage, review
time and savings are not measured.

## Historical installation proof and four design corrections

The [proof report](../experiments/issue-1285/public-runner/metadata-strategy.md)
records the separately committed helper, exact commands, original-source/lock
checks, full installed-file/metadata manifests and retained failures. At fixed
paths/mtime/SOURCE_DATE_EPOCH, pinned uv 0.13.5 writes wheel/project **ctime** into
uv_cache.json to ns precision; RECORD changes too. Editable uv_build.json is
inventoried. Historical uv draft is **predicted to fail** strict two-build equality,
not just an untested risk. The varying directories.src field's exact clock mapping
is not established by this spike. No metadata cleanup or byte exclusions follow.

One hash-pinned pure Python candidate, PyPA installer 0.7.0, produced identical
complete venv file bytes/modes/links in its wheel and PEP-660 editable A/B pairs.
It uses the same 43 runtime wheel bytes plus a separate seven-wheel pinned
Hatchling builder. Initial standard INSTALLER/PEP-610 metadata is explicit and
reviewable. Source remains live through the installed editable .pth, without
PYTHONPATH; original tracked bytes/modes/links and lock remain unchanged. Public
import/consistency/CLI/demo checks pass; host 3.12.14 is not official-image 3.12.15.
This is not target closure, OCI reproducibility, full-test parity or E1–E3 evidence.

The [expected installation inventory](../experiments/issue-1285/public-runner/expected-inventory.json)
enumerates name/version/wheel hashes and import roots for historical uv's 47
pre-editable and 44 final entries; pins.json records its digest. Alternative
pre-editable deployment prefix is 43 with seven backend packages isolated.
Source-policy selectors now explicitly use WILDCARD and their configuration hash
is updated; BuildKit syntax/worker/snapshotter/semantic-denial gates and first-use
provenance limitation remain. The checklist specifies nonblocking separate pipe
counters enforcing 16777216 bytes per stream; first excess byte fails closed,
triggers bounded Tini/watchdog cleanup, records overflow and preserves capped
evidence. It is a proposed control requiring implementation and boundary probes;
the 56/64/512 MiB budgets and strict E2 criteria are unchanged.

**Next action:** independent Claude Code maintainability/security/behavior review
of the exact implemented code/tests/source pins/modes/evidence, including M1/M2,
complete prevalidation and zero-write controls, native member order, phase sorting,
RECORD/direct-url bytes, live source, no-sync and retained intermediates. Return
reviewer/session/model, exact SHA, ranked findings and verdict. This implementer
does not self-approve. Separate build authority remains required.

G1 signed immutable Debian/OS/Git/Tini closure and 87-base-package compatibility
remain blocked by supported proxy policy. G3 approved $0 Linux/amd64 venue rights/worker/storage/control
receipts remain unverified; BENJAMIN is offline and not required. Later target installation, controls, per-test direct
receipts and two-build OCI comparison retain their separate gates. All authority
language docs remain accurate without edits: this changes neither Python/C++
runtime semantics nor any MCP language-profile fact. No private/benchmark/R29
work, paid infrastructure, merge or issue closure was performed.
