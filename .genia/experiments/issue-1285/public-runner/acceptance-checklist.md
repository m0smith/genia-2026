# Public-runner acceptance — proposed, all execution items pending

This checklist implements review amendments A5–A8 as **requirements**, not results.
It authorizes no execution. [Design](../../../process/issue-1285-public-frozen-runner.md),
[pins](pins.json), [gaps](pin-gaps.md), [offline recipe](offline-build-recipe.md).

## Implemented host evidence, not target acceptance

RED tests: `de1f455823e18f049a87cccbc2934bcb0bc20e11`;
implementation `150d9cb8da3d5e34aa86efa39ffa6b656fc28b8c`;
[host implementation/evidence](frontend-evidence/implementation.json).
The following execution checklist stays unchecked: CPython3.12.14/UID1000 host
tests do not establish official3.12.15/UID10001, read-only mounts, full regression,
resource controls, OCI output or runner acceptance. The implementer generated and
checked [exact expected modes](frontend/expected-modes.json); independent Claude
maintainability/security/behavior review of source/tests/artifacts is pending.

## Gates and receipts

- [ ] G1 OS/Git/Tini `.deb` closure and Release/signature/index/hash chain complete.
- [ ] R3 compatibility table covers all 87 base packages: Debian-version comparison
  to signed snapshot candidates passes; no required downgrade; every proposed
  base upgrade explicitly reviewed. Earlier candidate snapshot is not assumed
  compatible merely because its date is near the base creation time.
- [ ] Qualify an available approved **$0 Linux/amd64 venue** by actual build/run/
  OCI-export/cgroup-inspect and enforcement receipts, pinned rootful BuildKit
  profile and finite disk/inode/evidence quotas. [Venue decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6643155880):
  BENJAMIN is offline, not required; no current host qualifies by declaration.
- [x] Independent Claude design delta review at d591ecf5 completed with mandatory
  corrections carried into implementation ([review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6643785950)).
  This is design evidence, not source/host/production acceptance.
- [ ] Independent Claude maintainability/security/behavior review PASS on exact
  implemented code, tests, source pins, expected modes and host evidence.
- [ ] Complete independent review of the authorized implemented candidate frontend. Pin every
  reviewed bootstrap/validation/hook/build/metadata source file, entrypoint
  and manifest hash in input-sha256.txt. Experimental helpers are evidence only.
- [ ] Verify installer wheel URL, **453838 bytes**, SHA256
  `05d1933f0a5ba7d8d6296bb6d5018e7c94fa473ceb10cf198a92ccea19c27b53`;
  retain first-use/no-publisher-attestation limitation. All earlier source, lock,
  wheel, uv, BuildKit and Python-base artifact hashes remain unchanged.

- [ ] Maintainer separately authorizes bounded offline build, then acceptance
  runs. No private work, custody or independent-worker authorization follows.
- [ ] Two independent build receipts, offline proof and OCI archive/index/
  manifest/config/layer comparison pass before any “frozen” claim.
- [ ] R6 pinned BuildKit metadata-only lint/local-OCI/source-policy gate passes
  with no RUN/image export; rootful OCI/native snapshotter/bridge/process-sandbox
  profile verified by worker receipts, identical across A/B. OCI timestamp-export
  semantics are checked separately in the authorized build, not inferred from lint.
- [ ] Fresh independent Claude review of actual implementation/evidence SHA,
  followed by owner acceptance. No merge/closure is implied.

## Installation, source and observation

- [ ] Empty initial package/build caches; manifest byte/size hashes checked before
  use; only binary third-party wheels; no online or implicit acquisitions.
- [ ] Official CPython 3.12.15 runtime: executable and libpython hashes, `python -VV`,
  sysconfig compiler/config/ABI, OpenSSL/SQLite/zlib versions, glibc and loaded
  library paths collected. Compare explicitly with original Clang 22.1.3 build;
  same Python patch number is not interpreter equivalence.
- [ ] Assert `umask 022` for scaffold, tool bootstrap, every install and editable
  hook/build/install. As root build identity, produce 0644 regular files, 0755
  directories/executables and explicit reviewed symlink targets/lstat modes.
  Full scaffold/directory/file/link byte/mode/uid/gid inventories match A/B after
  declared deployment ownership 10001:10001. Verify readability/traversal/execution
  as runtime UID 10001; historical umask-077 0600/0711 manifests cannot satisfy this.
- [ ] Explicit `posix_prefix` on official 3.12.15: purelib/platlib exactly
  `<prefix>/lib/python3.12/site-packages`, scripts `<prefix>/bin`, data `<prefix>`,
  headers under `<prefix>/include`. Assert every dist-info under site-packages and
  every mapped destination under fixed `/opt/genia/venv` or isolated builder prefix.
  No implicit Debian scheme or symlink escape; pinned scaffold links are distinct.
- [ ] Entire installer bootstrap and builder input sets validate before their
  destination writes. Before any deployment venv/scaffold writes validate the
  entire runtime+generated-editable set: archive hashes, identities/tags, all
  RECORD contents/hash/size/coverage, ZIP members, safe mapped paths and collisions. Safe zero-size canonical type-
  directory members mode0755 may be absent from RECORD and create no output.
  Generated editable is validated after building but before installation. No
  per-wheel verify/install loop or implied runtime-failure transaction guarantee.
- [ ] Fail-closed negative controls place the bad wheel **last after a valid one**:
  wrong archive hash, missing wheel, matching-archive-hash RECORD corruption,
  unrecorded/duplicate member, unsafe path, wrong identity and destination conflict.
  Each proves zero destination writes (including directories). Reject existing
  unexpected files, conflicting script names, parent type aliases and symlink parents.
- [ ] Fixed runtime43 then editable-Genia phase order; wheels within phases sorted
  by normalized name/version string/filename/SHA256, bytewise
  LC_ALL=C; native member/entrypoint/RECORD ordering retained, with no extra adapter or
  post-generation metadata sort. Actual plan/write receipts must agree.
- [ ] Target editable hook exactly `["editables~=0.3"]`; isolated
  `/opt/genia/build-venv` has precisely the seven unchanged pinned backend wheels.
  Run reviewed Hatchling build_editable on fixed `/opt/genia/source`, using only
  that builder and stdlib, no acquisition. Generated editable wheel hash equal A/B
  at fixed `/opt/genia/editable-wheel`; scratch-path hashes are not target pins.
- [ ] Recompute expected inventory identities from unchanged pin records: **47**
  unique runtime/backend union, historical uv pre-editable 47, selected runtime
  pre-editable **43**, isolated builder **7**, final **44** = runtime43+Genia0.1.14.
  Verify all wheel hashes and three overlap hashes, not counts alone. Include
  colorama; exclude inactive variants, exceptiongroup/tomli/typing-extensions.
  No backend-only, installer-tool, system/user package leakage in deployment.
- [ ] `uv --no-config pip check --python /opt/genia/venv/bin/python --offline`
  passes after runtime wheels and after editable; check builder consistency and
  exact installed name/version/artifact/import paths separately. No online repair.
- [ ] Hash/size-validate **every installed RECORD row**, generated scripts and
  initial INSTALLER/direct_url metadata included; validate all rows/coverage after
  install and after runtime commands. Only RECORD's own row has empty hash/size.
  Enumerate all installed files not owned by RECORD; only reviewed venv scaffold
  exceptions allowed, no unexplained lib/bin payload or duplicate owners.
- [ ] Initial metadata matches policy: INSTALLER `installer\n`, deterministic
  editable PEP-610 file:///opt/genia/source + dir_info.editable=true in RECORD;
  no REQUESTED, wheel-local direct_url, uv_cache/uv_build or .lock generated.
  Tool-root read-only permissions0444/0555 are declared separately from installed
  deployment modes0644/0755; preserve the actual15 ZIP-executable members, including
  ruff and the non-binary Python payloads, plus15 generated wrappers.
  Validate expected differences from uv and unchanged METADATA/WHEEL/entry_points.
  Compare every generated byte A/B including wrapper templates, pyvenv.cfg,
  scaffold, .pth and symlinks; never patch/delete/ignore metadata to pass.
- [ ] **All 15 console wrappers** as UID 10001 under official 3.12.15: coverage,
  coverage-3.12, coverage3, genia, ghp-import, idna, markdown_py, mkdocs,
  mkdocs-get-deps, normalizer, py.test, pybabel, pygmentize, pytest, watchmedo.
  Record exact bounded smoke argv, outputs/exits and shebang/interpreter paths;
  also `genia -c '1 + 1'`, uv list/freeze/show/tree/check. Host wrapper evidence
  does not complete target acceptance.
- [ ] Import actual compiled extensions (verify __file__, extension suffix and
  shared-library resolution): charset-normalizer, coverage, markupsafe, pyyaml,
  tree-sitter and tree-sitter-{bash,cpp,rust,typescript}, watchdog's applicable
  native/platform paths. Run ruff executable under target glibc 2.41. Fail on
  unexpected pure-Python fallback; classify platform-only Python paths honestly.
- [ ] Editable .pth routes live source under `/opt/genia/source/src`, no copied
  Genia or PYTHONPATH. In an isolated disposable source copy, an edit and new
  module are visible without reinstall; restore/verify bytes. From another cwd
  and minimal environment imports resolve correctly with user site disabled.
  Repeat smoke against final read-only approved-source mount without mutation.
- [ ] Zero .pyc in source/venv/builder, bytecode generation disabled; no silent
  deletion. Precompilation or runtime bytecode-cache policy needs separate review.
- [ ] Exact `uv --no-config run --frozen --offline --no-sync` for project commands,
  selected interpreter proven against **read-only venv**. Trace attempted writes,
  before/after bytes/modes/lock hashes, no .lock/new env or editable auto-rebuild.
  Preserve the configured launcher's separate **--no-project** argv/behavior.

- [ ] Exactly one distinct uv executable on effective PATH, version 0.13.5 and
  SHA256 `8a70db72685b7138121bfcda71fa1a00cb709ed9f1fdc4ecf1dd871e8e167e52`;
  record outer and nested fixture resolution. No uv 0.12.23 fallback.
- [ ] Original source/lock/pyproject hashes unchanged at each phase; canonical
  `.git` bytes equal across builds; Git works as runtime UID 10001 with no dubious
  ownership bypass. No overlay of #1295's corrected fixture or newer semantics.
- [ ] Capture an observed full `execve` inventory (including subprocess descendants),
  and actual writes. Reconcile with package pins/writable set; static source grep
  and observed launcher controls alone are not complete execution inventories.

## PID 1, cleanup and watchdog (A7)

- [ ] Run with the in-image pinned `/usr/bin/tini -g -- ...` as PID 1; record
  executable hash, `/proc/1/comm`, argv and `docker inspect` init/entrypoint.
  No Docker `--init`, shell/tail keepalive or second init.
- [ ] Neutral subprocess control, original unchanged reaping test alone, and that
  same test in both full-partition evidence: record stable `(pid,starttime)`
  identities, PPID/PGID/SID/state. Demonstrate orphan PPID 1 then wait/reap;
  no surviving zombie/descendant within a fixed **10-second neutral-control**
  observation bound. Preserve the original test's own existing deadlines.
  Exact original-pair node:
  `tests/unit/test_r28_mcp_conformance_lifecycle.py::test_a_discover_probe_launch_followed_by_a_session_launch_leaves_nothing_behind`.
  The two `test_r28_mcp_fixture_teardown.py` tests added by #1295 are not in the
  original source; do not overlay them or cite their PASS as original-pair evidence.
- [ ] EOF, TERM and deliberate intermediate-parent SIGKILL controls; Tini remains
  alive while supervising the neutral control, adopts and waits the orphan. The
  old process-local subreaper result is not an image result.
- [ ] Record normal exit 0 and 7 and child death by TERM/KILL: raw process status,
  Tini status and Docker exit code/signal mapping. No unproved equivalence between
  Python negative signal status and container `128+signal` conventions.
- [ ] External watchdog for public partitions: proposed 1800 s, TERM through PID 1,
  10 s bounded grace then Docker KILL; record actual signal targets/tree/waits and
  wall deadlines. A watchdog failure stops that run, retains evidence and still
  permits collecting the complementary partition as a separate result.
  Benchmark invocation 60 s / 16 MiB per stream remains a separate future gate.

## CPU, memory and PID controls — measure effective values

- [ ] One verifier at a time; record host load/competing work. Proposed allocation
  two CPU quota and 4 GiB memory, no extra swap. Capture `docker inspect` and
  inside-container `cpu.max`, `memory.max`, `memory.swap.max`, `pids.max`, controller
  availability, cgroup path/version and cpuset. Expected `cpu.max` 200000/100000,
  memory.max 4294967296 and memory.swap.max 0; report actual values.
- [ ] Bounded CPU-busy probe: measure wall/CPU and `cpu.stat` delta, including
  throttled periods/time. `os.cpu_count()` may report host CPUs; explicitly set
  `PYTEST_XDIST_AUTO_NUM_WORKERS=2` and record actual worker count.
- [ ] Separate disposable memory probe under the same limit: a bounded child
  allocates beyond the cap, an outside observer records `memory.events` OOM/
  oom_kill increments and actual death. Check `memory.peak`; don't label ordinary
  MemoryError or a configured flag as proof of cgroup OOM enforcement.
- [ ] Separate finite PID-cap probe (at most cap+2 children, short watchdog,
  cleanup all children): demonstrate EAGAIN and `pids.events` max increment,
  record peak `pids.current`. Python threads count too. No unbounded fork loop.
- [ ] Diagnostic calibration uses a declared pids.max **1024**, not claimed as
  final acceptance. Record full-run peak PID/thread use. Propose final
  `max(256, ceil(1.25*peak)+32)`; if it exceeds 1024 or calibration hits the cap,
  STOP for review rather than silently increasing it. Rerun effective-control
  proof and full acceptance at the reviewed final limit. 256 is not yet measured.
- [ ] `/tmp` tmpfs proposed 1 GiB, `/dev/shm` 64 MiB and `/evidence` 64 MiB:
  verify mounts/caps and account for all their pages **inside** the 4 GiB memory
  envelope, including evidence writes/copy-out. Their capacity ceilings total
  1152 MiB, leaving at most 2944 MiB for everything else if all fill; those are
  ceilings, not reservations or guaranteed heap capacity. Verify actual memory
  charging (especially a host tmpfs bind); if charged elsewhere, record/bound it
  and STOP the claimed 4 GiB profile until reviewed. No claim that
  these capacities are free additional RAM. Collect full-run peak RSS,
  memory.peak, pids.current peak, OOM/PID events and raw sampling timestamps.

## Network, filesystem and bounded evidence

- [ ] `--network=none`, private PID/cgroup namespace, nonroot UID/GID 10001,
  all capabilities dropped, no-new-privileges and explicit recorded seccomp
  profile/default. No privileged/host-network/daemon-socket mount.
- [ ] Prove namespace has only loopback/no external route; loopback TCP/UDP
  controls succeed where required, bounded external connect/DNS controls fail.
  Record actual syscall outcomes and `unshare` availability/probe behavior.
  Default seccomp/userns restrictions are evidence, not a reason to edit skips.
- [ ] Read-only source/venv/rootfs: attempted writes fail with EROFS as expected.
  Declared writable set is **only** `/tmp` (HOME, pytest
  basetemp/cache, uv cache, application scratch), `/dev/shm`, and `/evidence`.
  No writable source/index or extra mount without a reviewed deviation.
- [ ] `/evidence` bind comes from a dedicated selected-venue **64 MiB size-bounded
  tmpfs**, not an unbounded host directory; creation/mount rights remain unverified.
  Confirm ENOSPC on a finite probe and preserve existing logs. Bound inode count
  too. One verifier container runs the six commands **sequentially**. Container
  log driver: local, max-size 16 MiB, max-file 2 (32 MiB maximum working retention,
  not a complete evidence source). Per command allocate at most 16 MiB stdout +
  16 MiB stderr + 24 MiB JUnit/metrics/receipts = **56 MiB**, leaving 8 MiB free in
  the tmpfs. Enforce each cap and inode/count limits; overflow is a failed command,
  never truncated PASS. After every command, copy to bounded durable storage,
  verify hashes/lengths and acknowledge before deleting its tmpfs files or starting
  the next. Failed copy/ack STOPs; do not accumulate all six commands in 64 MiB.
- [ ] Implement and measure the per-stream mechanism below; configured tmpfs/log
  sizes alone are not enforcement of the stdout/stderr limit.
- [ ] The 512 MiB retained **text/test-control** budget is explicit: six command
  bundles at 56 MiB = 336 MiB; shared receipts 32 MiB; neutral/diagnostic controls
  64 MiB; one-container working Docker logs 32 MiB; headroom 48 MiB = 512 MiB.
  Diagnostic/repeated runs share these caps, never multiply them silently.
  OCI archives, pinned input blobs and BuildKit roots are not claimed to fit this
  log budget: set and verify separate finite manifest-backed storage quotas before
  build authorization. Until those caps/venue capacity are approved, storage is
  an open G5 prerequisite. Inspect public payload and sanitize local paths.
  No paid artifact service/registry or public Actions upload. Missing tmpfs/quota
  support is a STOP, not permission to use unbounded host disk.

### Required stream supervisor — proposed, not implemented or tested here

Use an external supervisor with separate nonblocking stdout/stderr pipes and a
selector loop (not buffered communicate/capture_output). Each stream has a
**16777216-byte** counter and capped artifact. Each read requests at most
`min(65536, remaining+1)` bytes; persist at most remaining bytes. The first excess
byte latches overflow and **command failure**, even if the command exits 0.
Record the offending stream, observed bytes, retained bytes and truncated=true;
never label a capped prefix as complete output. Exactly-at-limit is allowed only
after actual EOF, successful exit and all other checks.

On overflow request TERM through container PID 1/Tini, bound grace to 10 seconds,
then KILL the container if needed using the existing external watchdog. Continue
draining both pipes with constant bounded buffers during that finite cleanup,
discard excess bytes and record that loss; never resume acceptance. Preserve
raw exit/signal/overflow/watchdog receipts and bounded retained prefixes. Failed
cleanup, missing supervisor receipt, cap-counter failure or evidence write error
fails closed. Bound receipt/JUnit files and inode count separately under their
24 MiB allocation; RLIMIT_FSIZE bounds regular writes only and is insufficient
for pipe output. This leaves the existing 56/64/512 MiB budget unchanged.

Before acceptance, neutral producers must prove cap-1, cap, cap+1 behavior on
each stream and simultaneous saturation; include a producer that exits 0 after
overflow and a TERM-resistant producer. Verify bounded peak memory/storage and
cleanup, and that no overflow is reported PASS. These probes and supervisor code
are later authorized implementation/verification work, not results of this spike.

## Six public verification commands and skip policy (A5)

Capture each command as its own argv/environment receipt, stdout, stderr, exit,
monotonic duration and resource samples. Prefix each argv below with
`uv --no-config run --frozen --offline --no-sync`, setting
`UV_PROJECT_ENVIRONMENT=/opt/genia/venv` and
`UV_PYTHON=/opt/genia/venv/bin/python`. Experimentally verify the selected Python
and absence of lock/environment writes; no bare/system pytest. The original
source and test assertions are unchanged. For both pytest partitions
use `-vv -rA --color=no`, `--junitxml=<separate file>`,
`-o junit_family=xunit1`, declared cache/basetemp and two xdist workers. Preserve
collection output, full node IDs (including parameters), collection/setup/call/
teardown errors, skip/xfail/xpass reasons and plugin/version list. JUnit classname
alone or aggregate pass/skip counts cannot uniquely establish node-ID equivalence.

1. `python tools/validate_llm_instructions.py`
2. `python tools/gen_function_docs.py --check`
3. `python tools/lint_doc.py --scan-dir src/genia/std/prelude --require-coverage`
4. `python -m genia.interpreter examples/validated_pipeline_demo.genia`
5. `pytest -n auto -q -m 'not loopback'` plus evidence options above
6. `pytest -n auto -q -m loopback` plus evidence options above

Run **both** partitions even if the first fails. Demo's known runpy warning stays
recorded. A public demo/check is not benchmark correctness. The 7,136-pass #1295
fixture-corrected run is a different source, not original-pair acceptance evidence.

Node, installed official MCP client and Wasmtime are intentionally absent in the
minimal first runner per maintainer decision. Inventory each absence explicitly;
do not add fake commands or alter tests/markers/skips. For independent A/B runner results and any measured compatible comparison, compare sorted **full node-ID → outcome + phase + reason** maps,
plus collected/missing/extra IDs. Every extra skip, omitted test, xfail/xpass or
failure difference is a documented gap and blocks E2. The historical “60 skips”
contains no sufficient ID/reason set. A deliberately excluded tool is not a
passing equivalence result; installing it later needs new pins and review.

### R7 — diagnostic hardening differences, not relaxed acceptance

Pre-declare mismatch causes: HARDENING-CONTROL (seccomp/userns/network/RO policy),
OPTIONAL-TOOL-ABSENT, ENVIRONMENT-SELECTION, DEPENDENCY-INTEGRITY,
GENIA-REGRESSION or UNKNOWN. Record each full node ID, direct/hardened outcome,
raw error/skip reason and the evidence supporting attribution. A configured
hardening flag alone is not a causal diagnosis.

Only after separate owner authorization, an optional diagnostic may use the
**same image digest, source, packages, argv, deadlines and resource limits**, changing
one reviewed policy factor at a time: e.g. a private writable source copy (same
starting hashes), or a narrowly pinned seccomp user-namespace adjustment. If a
network diagnostic is justified, use an isolated internal test network with no
external egress. No privileged mode, host networking, Docker socket or unreviewed
blanket seccomp/capability relaxation. Record exact profile/mount deltas, syscall/
write observations and full diagnostic result maps. Do not execute it now.

Mark diagnostic artifacts `acceptance=false`. A relaxed-profile PASS may attribute
a mismatch; it cannot replace the hardened result, excuse an extra skip or make
E2 pass. Both original full partitions and every failure remain visible. If the hardened candidate differs from its declared comparison run, E2 remains
unestablished even when the cause is understood. A historical BENJAMIN aggregate
is contextual only and is not a mandatory replay or per-test acceptance oracle. No test/skip editing, omission or benchmark trial.

## Actual selected-venue receipts and E0–E3 (A8)

Collect on the selected approved $0 Linux/amd64 venue without publishing local
identifiers/secrets: OS/kernel and virtualization identity; Docker Engine/
containerd/runc; cgroup/runtime/storage/security; PID 1/controllers/limits;
CPU/memory; uv/Python paths/hashes/versions, python -VV, compiler/sysconfig/ABI,
OpenSSL/SQLite/zlib/glibc; Git/gated tools; locale/TZ; installed/import inventory;
original source/lock/pyproject; reaping/process-tree and six command receipts,
both full partition maps and resource peaks. Use a new public export, preserve
historical BENJAMIN lock/source records and failed evidence. BENJAMIN is offline
and direct replay there is not required. No host currently qualifies by assertion.
Declare PYTHONHASHSEED=0, LANG=C.UTF-8, TZ=UTC as candidate settings; historical
unknowns and environment differences remain explicit. Never infer equal workers.

| Class | Required evidence / permitted claim | Current status |
|---|---|---|
| E0 | Exact approved source/lock/pyproject, no overlays; not interpreter equality. | Pin identities retained; selected-venue execution receipts pending. |
| E1 | E0 plus exact installed name/version/artifacts, editable routing/import isolation. | Host proof only; official-target selected-venue receipt pending. |
| E2 | E0/E1 plus matching complete node-ID/outcome/phase/reason/tool-state maps for explicitly identified compatible comparison runs, both partitions, no omitted/extra skips. | NOT ESTABLISHED. Future A/B maps required; historical BENJAMIN 7134/60 aggregate lacks node IDs and is contextual only. |
| E3 | E0–E2 plus measured timing/resource/toolchain/kernel/filesystem and control differences. No timing speedup or equal-worker claim. | NOT ESTABLISHED; original interpreter differs. |

Historical BENJAMIN provenance remains immutable contextual evidence, not active
venue qualification or required acceptance equivalence. Without measured compatible
per-test data, do not claim historical E2/E3 parity. Public runner acceptance still
requires all target/full-test/control checks and two independent byte-equal OCI
builds; venue neutrality does not weaken those gates or authorize benchmarks.
