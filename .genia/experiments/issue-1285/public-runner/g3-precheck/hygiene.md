# G3 evidence hygiene — iteration 2 (non-authoritative)

Codex; 2026-11-07 UTC. **G3 UNQUALIFIED / BLOCKED.** Bounded paperwork under
[maintainer authorization](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6708635427),
addressing [review 6708318227](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6708318227)
of `b3c59883b39b0c1623d87d70332a16c1506f2322`. Original receipts are unchanged.
Accepted frontend stays `fd74a5830c76373d724bbd40a603ea85870f0aca`.
No Docker API call or venue probe was made in this hygiene session.

## Reproducible sanitized Docker metadata (future receipt recipe)

The old hand projection has no raw-output hash and cannot be retroactively made
reproducible. Its canonical projection hash is retained in
[hygiene-budget.json](hygiene-budget.json) for integrity only, not authenticity.
For a separately authorized future metadata check, use the following fixed field
allowlist and type checks; retain the exact recipe/tool versions and SHA256 of
its emitted UTF-8 JSON+LF bytes. Never publish raw Docker JSON, stderr, paths,
proxy, registry, node identity, labels or arbitrary warnings in public CI logs.
Disable shell tracing; capture errors privately and publish only exit status and
a fixed error class. Raw output may be hashed privately without retaining it;
a raw hash alone does not prove that the published projection was derived from it.

Proposed pipeline, **not run here** (jq 1.6+; pipefail required). Each allowed
scalar has an exact type; unexpected/missing fields fail rather than broaden the
projection. SecurityOptions are emitted as fixed booleans, never free text.

```sh
set -o pipefail
env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH docker --host=unix:///var/run/docker.sock info --format '{{json .}}' |
jq -ceS '
  . as $d |
  ["Containers","ContainersRunning","ContainersStopped","Images","NCPU","MemTotal"] as $numbers |
  ["MemoryLimit","SwapLimit","CpuCfsPeriod","CpuCfsQuota","CPUSet","PidsLimit"] as $bools |
  ["Driver","CgroupDriver","CgroupVersion","KernelVersion","OperatingSystem","OSType","Architecture","ServerVersion","DefaultRuntime"] as $strings |
  {Driver:"^(vfs|overlay2|overlayfs|btrfs|zfs|devicemapper|fuse-overlayfs)$",
   CgroupDriver:"^(cgroupfs|systemd)$", CgroupVersion:"^[12]$",
   KernelVersion:"^[0-9][0-9A-Za-z.+_-]{0,127}$",
   OperatingSystem:"^(Debian GNU/Linux 13 \\(trixie\\) \\(containerized\\)|Ubuntu [0-9.]+( LTS)?)$",
   OSType:"^linux$", Architecture:"^(x86_64|amd64)$",
   ServerVersion:"^[0-9]+[.][0-9]+[.][0-9]+$", DefaultRuntime:"^runc$"} as $patterns |
  if (all($numbers[]; ($d[.]|type)=="number") and
      all($bools[]; ($d[.]|type)=="boolean") and
      all($strings[]; . as $k | ($d[$k]|type)=="string" and ($d[$k]|test($patterns[$k]))) and
      ($d.SecurityOptions|type)=="array" and
      all($d.SecurityOptions[]; type=="string")) then
    reduce ($numbers+$bools+$strings)[] as $k ({}; .[$k]=$d[$k]) |
    .SecurityOptions = {
      seccomp_builtin: ($d.SecurityOptions|index("name=seccomp,profile=builtin")!=null),
      cgroupns: ($d.SecurityOptions|index("name=cgroupns")!=null),
      rootless: ($d.SecurityOptions|index("name=rootless")!=null)
    }
  else error("unexpected metadata schema") end
' > docker-info.sanitized.json
```

The anchored platform-string patterns are intentionally narrow: unsupported
platform/version metadata STOPs for recipe review rather than being echoed.
Review the output before emitting it into a public log; do not use a broad redaction denylist as a
substitute for this allowlist. Retain exit status for both pipeline stages,
projection hash, command, versions, timestamp and venue/image identifier with
unnecessary environment IDs omitted. This is a receipt design, not new executable
runner implementation, CI wiring, or a claim to repair the historical raw gap.

## Reconcile resource scopes

| View | Historical observation | Meaning and missing proof |
|---|---|---|
| Docker daemon API | NCPU=3; MemTotal=10452459520 bytes (about 9.73 GiB) | Daemon-reported host/resource view, not executor entitlement or worker limit |
| Executor cgroup | cpu.max=200000 100000; memory.max=8589934592 bytes (8 GiB); swap.max=max; pids.max=max | Executor has aggregate 2 CPU quota and 8 GiB limit; no finite swap/PID cap shown |
| Future selected BuildKit/worker | UNVERIFIED | Must prove 2 CPU, 4294967296-byte memory, no extra swap, finite PID limit and page accounting in the actual worker cgroup |

These are different scopes, not interchangeable capacity estimates. No retained
PID/cgroup ancestry links the daemon or future workers to the executor cgroup;
Docker-launched work may be outside it. Neither min(daemon,executor) nor the
advertised flags prove a worker ceiling. Later authorized receipts must identify
daemon PID/cgroup and worker PID/cgroup ancestry, sanitized inspect limits, and
inside-worker cpu.max/memory.max/memory.swap.max/pids.max, plus OOM/PID negative
controls and accounting of tmpfs/shm/evidence pages inside the 4-GiB budget.
Do not mutate cgroups to resolve this documentation question.

Socket 0660 UID65534:GID1000 with executor UID/GID1000 means the executor group
can technically send mutating Docker API requests. **Socket access is not build,
run, pull or export authorization.** The protection here is procedural; no
technical restriction to info-only has been demonstrated. Installed tools and a
successful info response never grant permission. SecurityOptions names seccomp
and cgroupns but no rootless token: weak non-conclusive evidence only, not proof
of Docker mode and no evidence of pinned rootful BuildKit mode. Daemon UID65534
alone also cannot resolve that question.

## Draft numerical caps and feasibility

All values below are proposed **hard upper caps**, not measured requirements,
reservations or implemented quotas. Each root and each archive has its own cap;
clean roots may not share caches/state. No serial deletion/reuse is assumed to
make the arithmetic pass. vfs/native expansion, dependency closure, frontend
retention and two canonical OCI outputs still need measured size/inode estimates.

| Allocation | Byte cap | Inode cap | Backing |
|---|---:|---:|---|
| Pinned inputs | 1073741824 | 65536 | Separate read-only staged disk mount |
| Clean BuildKit root A | 2147483648 | 131072 | Separate quota-controlled disk mount |
| Clean BuildKit root B | 2147483648 | 131072 | Separate quota-controlled disk mount |
| OCI archives A | 1073741824 | 16384 | Separate quota-controlled disk mount |
| OCI archives B | 1073741824 | 16384 | Separate quota-controlled disk mount |
| Text/logs (existing 512 MiB budget) | 536870912 | 32768 | Separate quota-controlled disk mount |
| /evidence (existing 64 MiB budget) | 67108864 | 4096 | tmpfs, charged within worker 4 GiB |
| Unallocated filesystem margin | 1073741824 | 65536 | Disk reserve, unavailable to build caps |

Disk caps total **8053063680 bytes / 393216 inodes**. With margin they require
**9126805504 bytes / 458752 inodes**. Historical disk total is 8417406976 bytes,
524288 inodes; available was 7888793600 bytes / 517981 inodes. Byte caps alone
exceed available by **164270080 bytes**; caps+margin exceed total by **709398528
bytes** and available by **1238011904 bytes**. Inodes fit arithmetically (with
margin 59229 historical free inodes remain), but neither enforcement nor future
workload sufficiency is proved. Evidence tmpfs is not counted as disk space; its
67108864 bytes and 4096 inodes require separate tmpfs limits and consume worker
memory (leaving at most 4227858432 bytes before other memory consumers).

**INFEASIBLE on the observed executor filesystem under this draft.** Do not shrink
caps, omit a build root/archive or consume the margin to declare success. Operator
must supply an independently approved $0 venue with adequate *available* capacity,
measured workload estimates plus margin, enforceable separate byte/inode quotas,
per-mount df -B1/df -i and overflow controls. Filesystem total is not a quota.
Even a bigger disk alone cannot qualify G3; no quotas were created or tested here.

## Venue status, blockers and handoff

Public GitHub-hosted Linux/amd64 remains a **proposed candidate only: UNQUALIFIED,
not approved or selected**. The prior smoke job did not qualify it. Its image,
rights, resource limits, quota controls, offline behavior, reaping and two clean
workers need separate direct receipts and independent review. $0 availability
needs confirmation under the project's cost policy for the precise runner/job;
no workflow dispatch or paid provisioning is authorized. BENJAMIN is permanently
excluded from active venue selection and prerequisites; archive references only.

Maintainer/operator owns venue choice, cost confirmation and separate bounded
probe authorization. Rootful pinned BuildKit 0.24.0/native snapshotter/process
sandbox/bridge/parallelism1/GC-off/no fallback, cgroup and quota enforcement,
offline controls, reaping, build/run/export rights and two independent OCI
manifest/config/layer/canonical-archive equality remain unverified. G1 remains
independently BLOCKED. G2/G5, official CPython3.12.15 target, custody and benchmark
gates remain unchanged. No policy/cgroup mutation, container operation, CI,
private material, spend, merge, closure or R29 work occurred in this phase.

Validation is bounded static JSON/arithmetic, original-receipt/pin/tree equality,
branch and whitespace checks. No runtime tests or Docker commands were run.
Existing infrastructure preflight applies: no portable behavior, host parity,
shared spec, capability vocabulary, MCP language knowledge or authority-document
impact. KEEP these non-authoritative records for independent delta review; no
new process gate. Usage and review effort unmeasured. Stop after publication.
