# Public-runner acceptance — proposed, all execution items pending

This checklist implements review amendments A5–A8 as **requirements**, not results.
It authorizes no execution. [Design](../../../process/issue-1285-public-frozen-runner.md),
[pins](pins.json), [gaps](pin-gaps.md), [offline recipe](offline-build-recipe.md).

## Gates and receipts

- [ ] G1 OS/Git/Tini `.deb` closure and Release/signature/index/hash chain complete.
- [ ] Actual BENJAMIN build/run/export/cgroup-inspect rights demonstrated; no
  inference from the current executor's read-only daemon inspection.
- [ ] Independent Claude Code **delta** review PASS on exact amended design/pin
  commit; prior PASS-WITH-REVISIONS is not this review.
- [ ] Maintainer separately authorizes bounded offline build, then acceptance
  runs. No private work, custody or independent-worker authorization follows.
- [ ] Two independent build receipts, offline proof and OCI archive/index/
  manifest/config/layer comparison pass before any “frozen” claim.
- [ ] Fresh independent Claude review of actual implementation/evidence SHA,
  followed by owner acceptance. No merge/closure is implied.

## Installation, source and observation

- [ ] Empty initial package/build caches; manifest byte/size hashes checked before
  use; only binary third-party wheels; no online or implicit acquisitions.
- [ ] Official CPython 3.12.15 runtime: executable and libpython hashes, `python -VV`,
  sysconfig compiler/config/ABI, OpenSSL/SQLite/zlib versions, glibc and loaded
  library paths collected. Compare explicitly with original Clang 22.1.3 build;
  same Python patch number is not interpreter equivalence.
- [ ] Target editable-requirements hook exactly `["editables~=0.3"]`; pinned seven
  backend wheels satisfy it; no extra hook download or third-party source build.
- [ ] Final distributions exactly 43 selected wheels plus Genia; compare names,
  versions, artifact fingerprints, editable root and actual import paths. No
  backend-only residue or system/user site leakage. **Include colorama** from the
  unconditional mkdocs-material dependency; exclude exceptiongroup/tomli/
  typing-extensions and the four inactive version variants.
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
- [ ] `/tmp` tmpfs proposed 1 GiB and `/dev/shm` 64 MiB: verify mounts/caps and
  account for their pages **inside** the 4 GiB memory envelope. No claim that
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
  Declared writable set is **only** `/tmp` (HOME, bytecode if enabled, pytest
  basetemp/cache, uv cache, application scratch), `/dev/shm`, and `/evidence`.
  No writable source/index or extra mount without a reviewed deviation.
- [ ] `/evidence` bind comes from a dedicated BENJAMIN **64 MiB size-bounded
  tmpfs**, not an unbounded host directory; creation/mount rights remain unverified.
  Confirm ENOSPC on a finite probe and preserve existing logs. Bound inode count
  too. Container log driver: local, max-size 16 MiB, max-file 2. Cap each captured
  stream at 16 MiB with an explicit overflow failure; don't truncate then PASS.
- [ ] Before copying to durable local storage, enforce a 512 MiB whole-evidence
  budget plus per-file/count caps; inspect public payload and sanitize local paths.
  No paid artifact service/registry or public Actions upload. Missing tmpfs/quota
  support is a STOP, not permission to use unbounded host disk.

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
do not add fake commands or alter tests/markers/skips. For direct BENJAMIN and
runner results, compare sorted **full node-ID → outcome + phase + reason** maps,
plus collected/missing/extra IDs. Every extra skip, omitted test, xfail/xpass or
failure difference is a documented gap and blocks E2. The historical “60 skips”
contains no sufficient ID/reason set. A deliberately excluded tool is not a
passing equivalence result; installing it later needs new pins and review.

## Direct BENJAMIN receipt and E0–E3 (A8)

Collect on the actual owner host, without publishing usernames/hostnames/secrets:
WSL/Windows/kernel identity; Docker Engine/containerd/runc version, `docker info`
cgroup/runtime/storage/security; PID 1 and controllers/limits; CPU/memory; uv and
Python executable paths, hashes/versions and `python -VV`, sysconfig/compiler,
OpenSSL/SQLite/zlib/glibc/ABI; Git version; Node/MCP-client/Wasmtime/unshare/ps/lsof
availability; locale/TZ; distributions/import paths; original source/lock/pyproject
hashes. Capture the reaping test alone and full process-tree identities, six
separate command results, both partition JUnits/full-ID logs, times and peaks.
Preserve existing BENJAMIN lock bytes and live checkout; use a new public export.
Never transmit private benchmark material. Direct host and container observations
must be labeled separately, with exact execution SHA and target/environment pins.

| Class | Required evidence / permitted claim | Current status |
|---|---|---|
| E0 | Same exact approved source tree, lock and pyproject; no overlays. Does not imply interpreter/package equality. | Original pin identities verified here; new direct BENJAMIN receipt pending. |
| E1 | E0 plus same installed name/version set, editable source/import isolation; record artifact hashes and any unavailable owner-side artifact identity separately. | Proposed 44-entry set matches historical inventory; new installs/direct replay not executed. No new direct E1 claim. |
| E2 | E0/E1 plus identical complete per-test node-ID outcome/phase/reason maps and applicable tool state, both partitions, no unaccounted omissions/extra skips. | BLOCKED: direct BENJAMIN per-test evidence absent; aggregate historical counts insufficient. |
| E3 | E0–E2 plus measured timing/resource/toolchain/kernel/filesystem context, raw peaks/watchdog/cgroup results and declared differences. Contextual reproducibility, not equal independent workers or a speed claim. | NOT ESTABLISHED; official interpreter differs. |

Without BENJAMIN per-test data, claims can reach only E0–E1 when their own
receipts actually pass. Same source or installed set does not license E2/E3,
interpreter equivalence, custody, benchmark readiness or independent-worker claims.
