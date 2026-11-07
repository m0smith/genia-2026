# G3 — venue-neutral infrastructure precheck (iteration 1)

Codex, 2026-11-07 UTC. **BLOCKED — no execution venue qualified.** Public-only
infrastructure evidence under the [maintainer decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6702416476).
Accepted frontend remains `fd74a5830c76373d724bbd40a603ea85870f0aca`;
that host-only acceptance does not authorize an image build. This lane is
independent of G1. [Receipts](receipts.json) contain bounded command results,
with daemon identity/proxy/registry details omitted. No artifact pins changed.

## Scope and preflight

Existing #1285 public runner preflight/design applies. This is a nonsemantic,
medium-risk evidence/documentation delta; no new process requirement or runtime
implementation. Portability analysis: (1) observable language behavior: none;
(2) semantic authority: STATE unchanged; (3) shared specs: unchanged, no new
behavior to specify; (4) capability vocabulary: unchanged; (5) Python/C++ host
claims: unchanged, executor metadata is not host conformance; (6) host gaps:
none added or removed; (7) documentation synchronization: this current evidence
entry only, no implemented-truth change. MCP language-knowledge impact: none.
Reviewed AGENTS, authority-document scope/navigation and relevant runtime/host
boundaries, process handoff/change/token-efficiency guidance, public runner
pins/design/acceptance checklist and applicable strategy docs. Root intake read
the current #1285 ledger; this record implements only the cited latest decision.

## Candidate environments

| Candidate | Availability and cost basis | Qualification |
|---|---|---|
| Attached managed executor | Actually accessible Linux/x86_64, Debian 13, UID/GID 1000; already attached, no new service/API usage or provisioning | Candidate for current approved prechecks only; image build/run/export authorization absent and G3 requirements incomplete |
| Standard public-repository GitHub-hosted Linux/amd64 runner | Proposed $0 option in [existing cost decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6421145851); no runner session obtained | UNVERIFIED; no CI dispatch authorized or performed; advertised platform features do not establish this job's rights/quotas |
| BENJAMIN | Maintainer reports offline; not contacted | UNAVAILABLE and not a prerequisite; historical source/lock/baseline remains provenance only |
| Other operator-owned Linux/amd64 venue | None supplied or accessed | UNVERIFIED; no cloud account, paid provisioning or private endpoint discovery attempted |

No candidate is selected by this precheck. Token/cost usage and review effort are
not measured; incremental infrastructure spending $0. No external paid service
was invoked.

## Actual capabilities of the attached executor

| Capability | Status and direct evidence | Remaining requirement |
|---|---|---|
| Linux/amd64 | DEMONSTRATED: `uname -srm`, Docker reports linux/x86_64 | Official CPython 3.12.15 image execution remains unverified |
| Docker metadata access | DEMONSTRATED: explicit local socket `docker info` succeeds, Engine 28.4.0, vfs, 0 images/containers; socket 0660 UID65534 GID1000 | This does not prove build/run/export rights or authorize those operations |
| Rootful pinned BuildKit 0.24.0 | UNVERIFIED: buildctl/buildkitd unavailable on PATH, no conventional socket/state directory, no buildkitd in selected process listing | Operator must provide/authorize exact pinned rootful OCI worker and bundled runc; daemon UID65534 alone does not prove rootless/rootful mode |
| Native snapshotter/worker profile | UNVERIFIED: Docker vfs is observed, not BuildKit native snapshotter | Actual selected worker receipt must show native, process sandbox, bridge, max parallelism 1, GC disabled and no fallback; no bootstrap attempted |
| Buildx inventory | UNAVAILABLE through attempted command: `buildx ls` exits 1 trying mkdir in read-only HOME | Failure retained; no configuration override or daemon bootstrap; recipe does not use buildx |
| Cgroup inspection | DEMONSTRATED: v2 controllers cpuset/cpu/io/memory/hugetlb/pids; current cpu.max 200000/100000, memory.max 8589934592, swap.max and pids.max `max` | Current aggregate 2-CPU/8-GiB cgroup is not target 2-CPU/4-GiB/no-swap/finite-PID worker; enforcement controls unverified |
| Cgroup mutation | UNAVAILABLE directly: cgroup mount read-only, subtree-control writable access false | Docker-advertised CPU/memory/swap/PID flags are not measured enforcement or permission receipts; no writes attempted |
| Storage and inodes | DEMONSTRATED finite current filesystem capacity: 8417406976 bytes and 524288 inodes; free values in receipts are transient | Per-build/input/OCI/evidence quotas and separation UNVERIFIED; df is capacity, not an enforceable per-lane quota; quota tools unavailable on PATH |
| Offline execution/build | UNVERIFIED: no namespace/egress-denial or semantic BuildKit source-policy probe performed | Restricted outbound policy is not offline operation; later safe authorized deny controls required |
| Orphan reaping | UNVERIFIED for candidate runner: outer PID1 is tail | No Tini image process or adoption/wait/TERM/SIGKILL receipts; no orphan probe performed; historical subreaper evidence does not qualify this venue |
| OCI export and reproducibility | UNVERIFIED; export not authorized or attempted | Exact manifest/config/layer/canonical-archive equality from two independent builds remains mandatory |

No inference from metadata access, installed CLI, advertised API feature or
finite backing filesystem establishes rootful-worker rights, quota enforcement,
secure custody or equivalent workers. No daemon was started, no image was
constructed/pulled/run/exported, and no privileged, namespace, cgroup or network
policy change was made. All commands were bounded read-only inspections; the
buildx command failed before creating its state directory.

## Blockers and next action

Owner/operator must identify an available approved $0 Linux/amd64 venue and
explicitly authorize the next bounded qualification operations on it, including
rootful pinned BuildKit/native-worker setup if absent, cgroup enforcement and
finite storage/inode/evidence controls. Provide actual build/run/OCI-export
permission receipts without treating a permission statement as execution proof.
First supply numerical, enforceable separate caps for pinned inputs, both clean
BuildKit roots and OCI archives, plus the existing 64-MiB bounded evidence tmpfs
and 512-MiB retained text budget. Do not silently use the whole backing disk as
an allocation. Stop if those controls cannot be established at $0.

Before any image authorization, obtain independent Claude Code review of this
exact committed evidence and the selected venue/profile. Review is requested
through the separate #1285 handoff; it has not been performed locally. No Claude
Code executable/reviewer is available in this lane. G1 remains independently
open. G2 actual target exec/write inventories, G5 official-target/full-regression,
read-only/nonroot controls, reaping and two-independent-build OCI proof remain
later obligations. No hidden fixtures/oracle/candidates, benchmark trial, CI
dispatch, merge, issue closure or R29 work is authorized.

Validation: branch guard PASS; JSON parse PASS; whitespace/diff scope checks PASS;
pins, source, lock, frontend, tests and four authority documents unchanged against
accepted frontend. No runtime tests were run for this evidence-only delta.
