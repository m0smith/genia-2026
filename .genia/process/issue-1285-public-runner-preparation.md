# #1285 — public execution preparation and lock-provenance blocker

Status: **NON-AUTHORITATIVE / PUBLIC-ONLY / NO-GO for frozen runner construction**.
Date: 2026-10-26. Source baseline: `9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90`.
Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285).
Design: [#1286](https://github.com/m0smith/genia-2026/pull/1286), head
`4ee8713ecfa391e1a8f74610b2e1dcad745d0779`. Preflight:
[#1287](https://github.com/m0smith/genia-2026/pull/1287), head
`6c4c3ff1a85d9ecc360f58988a049d0a3db4a2e8`.

## Scope, authority and finding

The current request authorizes public infrastructure preparation and existing
public checks, or a reviewed executable plan if implementation is blocked.
It does not authorize an oracle, hidden fixtures, annex receipt, candidate
programs or comparative trials. Those NO-GO gates remain in force. Budget is
**$0 incremental spending**; no billing settings, service plans or release scope
are changed. This is a single process record in `.genia/process/`, not benchmark
application content in the semantics repository.

Latest remote AGENTS blob is `b072beb55d22d5856d3d356d73c60704e04d197f`.
The named source-of-truth docs and applicable killer-workflow, human–AI strategy,
roadmap, ticketing and run-change guidance were consulted; their contents are
unchanged from the prior inspected baseline. STATE stays final authority.
Issue comments and both PR descriptions, design/preflight findings and returned
review timelines were reviewed; PR timelines returned no additional comments.

**New blocking finding:** `uv.lock` is not committed at the specified baseline.
`git ls-tree HEAD uv.lock` and `git ls-files uv.lock` return no entries;
`git ls-files --error-unmatch uv.lock` exits 1; `git cat-file -e HEAD:uv.lock`
exits 128. `.gitignore` line 7 ignores it. An ignored local lock is not a
versioned artifact merely because the working tree appears clean.

Correction to earlier #1285 inventory terminology: the previously reported
“repository uv.lock SHA-256” was the ignored local artifact, **not a committed
repository dependency pin**. Neither local lock has been changed or adopted.
Do not run `uv lock`, synchronize, force-add a file or silently choose one hash
to resolve this conflict. The owner must approve a versioned source/lock pair
and artifact provenance before the frozen environment can be constructed.

This task therefore provides the permitted **executable replay/runner plan**
and observed public diagnostic evidence, not an implemented frozen benchmark
runner. It adds no runtime, workflow, dependency-policy or language change.
MCP language-knowledge impact: none. Python/C++ semantics and conformance are
unaffected; no authoritative documentation edits are needed.

## Public harness inventory

| Asset | Status and evidence | Approval / missing artifact |
|---|---|---|
| CI-results application contract | Proposed public design, #1286 section 1 | Proposal is not evidence of implementation or authority to build competitors |
| Public invocation definitions | Proposed seven-family allocation 4/5/7/3/4/4/3 = 30; hidden total remains 60 | Actual approved input bytes, manifest and public expected results missing |
| Public benchmark fixtures/check command | No #1285 bundle or entrypoint found in tracked main or the two PR diffs | Do not substitute native examples, conformance fixtures or #1226 data |
| Comparator / oracle | Interface/normalization specified in #1286 section 2; no implementation | Independent oracle construction remains prohibited |
| Existing public capability checks | CLI, JSON/JSONL and resource test modules listed below | Building-block evidence only; not benchmark correctness |
| Existing validated pipeline example | `examples/validated_pipeline_demo.genia` | Native debug/Outcome output, not `ci-results.v1` wire output |
| Existing subprocess byte-capture tests | `tests/unit/test_execution_process_byte_capture.py` | Host-internal tests, not the independent benchmark harness; not run here |
| Development Dockerfile | `docker/Dockerfile.dev`, Python 3.14.7 trixie base pinned by digest; uv 0.12.18 | Different from BENJAMIN's managed 3.12.15; apt packages unpinned; not adopted or built |
| Build context guard | `.dockerignore` allows only itself and development Dockerfile | Protects that narrow context; also prevents packaging runtime/source/lock; no global isolation proof |
| Project dependencies | `pyproject.toml`: Python >=3.10, PyYAML>=6, development tooling | No tracked uv.lock, complete wheelhouse or Pydantic arm lock |
| Linux runner startup | Issue evidence links successful manual [run 40361534009](https://github.com/m0smith/genia-2026/actions/runs/40361534009) | Prior recorded evidence, not re-executed here; smoke removed by #1290 |
| BENJAMIN | Owner-reported regression/fingerprint below | No direct host connection or independent attestation available in this task |

The tree search covered tracked main paths and the single-file design/preflight
diffs, not private storage. Generic `tests/fixtures` and model fixtures are
language test assets, not public benchmark data. No private annex was searched.

### Preserved workload and execution boundary

Future candidate recipes are argv arrays, `RUN PATH` or `RUN -` with stdin EOF;
no shell interpolation, domain logic in launch wrappers or exit translation.
Genia uses the Python reference host, not MCP or pipe mode as a substitute for
file/stdin subprocess tests. Stdlib has no third-party imports; the Pydantic
arm must use Pydantic for validation. No such recipes or solutions exist here.

Preserve strict UTF-8 JSONL framing, accumulated field diagnostics, accepted-only
first-wins duplicates, exact Unicode scalar equality and deterministic report
ordering. Completed runs require one `ci-results.v1` JSON report, exit 0 and
empty stderr. Fatal usage/input requires empty stdout, ordinary exit 1..125 and
the exact category-line predicate from the design. Raw signals/timeouts/overflow
are failures. Objects compare without key-order/insignificant-whitespace bias;
arrays, strings and integer types are exact. No bool/int coercion, Unicode
normalization, Outcome unwrapping or double-encoded JSON acceptance. Describing
these rules does not implement their comparator. Ambiguities A1–A3 from #1287
remain proposed approvals; the 30/60 allocation is unchanged.

## Environment evidence and differences

| Property | BENJAMIN, owner reported | This task, directly observed |
|---|---|---|
| Source SHA | `9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90` | Same fetched main baseline |
| Local uv.lock SHA-256 | `02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8` | `c9543edd814d8ab75fc668908ca48cdfafe94d536a74e56266258a7f219e1ba7` |
| Lock in Git tree | Not independently checked there | Absent at that exact SHA; ignore rule verified |
| Managed Python | 3.12.15 | 3.12.14 in existing environment |
| uv | Earlier owner comment reports 0.13.5 | 0.12.23 |
| Docker | Engine 29.1.3 | No Docker image/build/run performed in this task |
| OS | Ubuntu WSL2 on Windows | Debian 13.6, Linux 6.18.55, x86_64 |
| Full Python regression | 7,134 passed / 60 skipped / 0 reported failures, 550.48s | Not rerun; selected 115 tests only |

Owner figures are not promoted to independent attestation. Versions, lock bytes
and host environments differ, so timings are not performance comparisons.
`pyproject.toml` SHA-256 is
`cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc`.
Existing Genia environment: genia 0.1.14, PyYAML 6.0.3, pytest 9.1.1,
pytest-xdist 3.8.0. System Pydantic 2.13.4/pydantic-core 2.46.4 is inventory
only, not a provisioned arm or locked dependency choice.

## BENJAMIN replay instructions — diagnostic, then fail-closed gate

Run these in Ubuntu WSL2, from the existing public checkout. No remote access
is assumed. Preserve the current lock; these commands neither fetch private
material nor alter dependencies. Do not use the whole checkout as a Docker build
context. No package installation or network activity is needed for these checks.

```bash
cd ~/projects/genia-2026
git rev-parse HEAD
sha256sum uv.lock
git ls-files uv.lock
git check-ignore -v uv.lock
git cat-file -e 9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90:uv.lock
```

Expected on the recorded baseline: the reported source SHA; the owner's local
hash if unchanged; no tracked-file entry; ignore rule `.gitignore:7:uv.lock`;
and final command fails (exit 128). This is a **successful detection of a
missing pin**, not a successful frozen replay. If any fingerprint differs,
record it and stop rather than checkout/reset/delete the owner's files.

Optional existing-environment public checks, separate from frozen replay:

```bash
cd ~/projects/genia-2026
TZ=UTC PYTHONHASHSEED=0 uv run --offline --no-sync python --version
TZ=UTC PYTHONHASHSEED=0 uv run --offline --no-sync pytest -q \
  tests/unit/test_cli_args.py \
  tests/unit/test_json_representation_boundary.py \
  tests/unit/test_json_stdlib.py \
  tests/spec/test_parse_jsonl_record_shared_spec_389.py \
  tests/unit/test_resource_io.py -k 'not zip'
TZ=UTC PYTHONHASHSEED=0 uv run --offline --no-sync python -m genia.interpreter \
  examples/validated_pipeline_demo.genia
```

Expected: managed Python 3.12.15 if the recorded environment is unchanged;
115 passes on the selected baseline tests with exit 0; demo emits native clean
records/diagnostics and exits 0, potentially with the observed nonfatal runpy
warning on stderr. Missing cached dependencies/interpreter is a stop, not
permission to install or replace pins. `--no-sync` deliberately reuses an
existing environment and **does not verify it against a committed lock**.

For byte-preserving diagnostic capture of any one command above, use this
controller in the public checkout. Replace only the public argv vector; the
default vector is a neutral process smoke, not a benchmark implementation:

```bash
python3 - <<'PY'
import hashlib, json, os, pathlib, platform, signal, subprocess, tempfile, time
argv = ['uv', 'run', '--offline', '--no-sync', 'python', '-c',
        'import sys; sys.stdout.buffer.write(sys.stdin.buffer.read()); '
        'sys.stderr.write("public smoke stderr\\n"); sys.exit(7)']
payload = b'public smoke stdin\n'
dest = pathlib.Path(tempfile.mkdtemp(prefix='genia-public-evidence-'))
env = os.environ.copy()
env.update(TZ='UTC', PYTHONHASHSEED='0', UV_CACHE_DIR=str(dest/'uv-cache'))
start = time.monotonic()
p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, env=env, start_new_session=True)
expired = False
try:
    stdout, stderr = p.communicate(payload, timeout=60)
except subprocess.TimeoutExpired:
    expired = True
    os.killpg(p.pid, signal.SIGKILL)
    stdout, stderr = p.communicate()
elapsed = time.monotonic() - start
(dest/'stdout.bin').write_bytes(stdout)
(dest/'stderr.bin').write_bytes(stderr)
record = dict(argv=argv, cwd=str(pathlib.Path.cwd()), exit_code=p.returncode,
              timeout=expired, duration_seconds=elapsed,
              controller_python=platform.python_version(),
              kernel=platform.release(), architecture=platform.machine(),
              source_sha=subprocess.check_output(['git','rev-parse','HEAD'],
                                                 text=True).strip(),
              environment_overrides={'TZ':'UTC','PYTHONHASHSEED':'0',
                                     'UV_CACHE_DIR':str(dest/'uv-cache')},
              stdin_sha256=hashlib.sha256(payload).hexdigest(),
              stdout_sha256=hashlib.sha256(stdout).hexdigest(),
              stderr_sha256=hashlib.sha256(stderr).hexdigest(),
              local_uv_lock_sha256=hashlib.sha256(
                  pathlib.Path('uv.lock').read_bytes()).hexdigest())
(dest/'record.json').write_text(json.dumps(record, indent=2)+'\n')
print(dest)
print(json.dumps(record, indent=2))
PY
```

Expected neutral smoke: exit_code 7, timeout false, stdout exactly
`public smoke stdin\n` (19 bytes), stderr `public smoke stderr\n` (20 bytes).
This trusted-public-input diagnostic uses bounded-time `communicate`, not
bounded-output streaming, cgroups or Docker. Do not use it for untrusted candidates
or hidden input. It records explicit cwd/cache paths but no environment dump,
account inventory or credential values; sanitize paths before public sharing.
Keep raw captures local and inspect before publishing; never point it at grading.

## Frozen public runner plan — blocked, not implemented

1. Owner approves a public experiment artifact home and the exact source/lock
   pair, resolving the absent tracked lock and differing hashes. Version the
   approved lock in that public non-authoritative home or explicitly approve a
   repository dependency-policy change; do not force-add either local lock here.
2. At that approved source/export, require `git ls-files --error-unmatch uv.lock`
   to succeed, verify the approved SHA-256, and compare its bytes to the recorded
   commit. Run `uv lock --check --offline` only after provenance is established;
   lack of cached metadata must fail closed. No lock regeneration.
3. Pin uv executable, exact Python 3.12.15 build, Linux/amd64 base digest,
   build tooling and complete wheel/transitive hashes. Use `uv sync --frozen`
   against the approved lock in a disposable public build stage, then prove a
   clean offline reinstall. Pydantic and its transitive lock are separately
   unresolved. Record input hashes and final OCI digest/image ID, not just a tag.
4. Construct a fresh context from an explicit public-file allowlist: approved
   `pyproject.toml`, approved lock, LICENSE, README and `src/`, plus the reviewed
   Dockerfile. Reject symlinks and unlisted files; verify paths and hashes before
   build. Exclude `.git`, `.env*`, homes, credentials, issue/design history,
   `.genia/process`, annex, fixtures, expected outputs and grading artifacts.
   Use an export outside the authoritative checkout and private storage. Never
   use `COPY . .`, a home mount, or a generic checkout archive as the context.
5. On BENJAMIN's existing Docker Engine, validate only neutral smoke inputs under
   the same intended constraints for every future arm. No candidate runs now.
   Require image digest, `--pull=never`, `--network=none`, `--read-only`,
   `--cap-drop=ALL`, `--security-opt=no-new-privileges`, non-root UID/GID,
   two CPUs, 4 GiB memory and swap ceiling 4 GiB, PID ceiling 128, a 64 MiB
   noexec/nosuid tmpfs at `/tmp`, and no host mounts, devices or Docker socket.
   Fix cwd `/tmp`, locale C.UTF-8, TZ UTC, hash seed 0 and umask 077 in the image.
   These are proposed launch controls, not verified custody or WSL2 isolation.
6. Implement/validate the public-only host supervisor before any candidate use:
   60-second monotonic watchdog, separate byte captures capped at 16 MiB each,
   kill/remove/reap on timeout or overflow, no truncation accepted as success,
   empty stdin EOF unless explicit public input, exact argv/cwd/env allowlist and
   raw exit/signal/Docker failure taxonomy. Record container inspection, observed
   cgroup limits, image/command/input hashes, duration and output hashes. Test
   CPU/memory restrictions and cleanup with neutral probes; advertised Docker
   support is insufficient. Do not just timeout the CLI and leave its container.
7. Review verified public smoke evidence, cost and missing public-fixture approval
   before changing any gate. Do not create benchmark goldens or a comparator.

A local replay after those gates would use the same approved image digest and
supervisor, no rebuild or network at execution. There is intentionally no invented
image digest, build command claimed successful, or missing supervisor executable
presented as working. Current exact executable commands above are diagnostics;
the frozen launch/supervisor remains a reviewed construction plan.

Remaining nondeterminism includes kernel/WSL2/CPU allocation, timer jitter,
package indexes during unfrozen setup, interpreter/build provenance, image
architecture and service/model drift. Fix UTC/locale/hash seed but do not infer
equal hardware or byte identity from those settings. No model/API is involved
in this preparation. Standard free public-repo GitHub runners are an option only
after confirming $0 eligibility; no workflow is added or dispatched by this task.

## Verification evidence from this task

Executed in the existing Linux workspace at the specified source SHA, with
`UV_CACHE_DIR` set to a task-local cache, TZ UTC and hash seed 0. The temporary
controller used argv arrays, separate raw byte files, monotonic clocks and a new
process group; it was not installed as a benchmark runner. No dependencies were
synchronized/downloaded and no Docker image was built or published.

| Check | Result | Raw exit | Captured wall seconds |
|---|---|---:|---:|
| Selected CLI/JSON/JSONL/resource tests (`uv run --offline --no-sync pytest ...`) | 115 passed in pytest's 2.04s; stderr empty | 0 | 2.283673 |
| Neutral stdin/stdout/stderr capture | 19 stdout bytes, 20 stderr bytes, byte equality checked | 7, intentional | 0.008070 |
| Neutral five-second sleeper, 0.2-second watchdog | Timed out, process group killed/reaped; empty streams | -9 / SIGKILL | 0.200854 |
| Existing documented pipeline demo | 863 stdout bytes; native records/diagnostics; 200-byte runpy warning stderr | 0 | 0.142278 |
| Tracked lock lookup | No tracked lock; ignore rule confirmed | 1 / 128 | Not timed |

Selected-test stdout SHA-256:
`dd63f1301176cc222558391f1eb12e1fb2bbefcdafda4b2d1ae6d361fb32e9f2`.
Demo stdout SHA-256:
`a76be749d35e336e7fc95720eba9309ed83a0a9835a895d6731aaf6f50e74b4f`.
Demo stderr SHA-256:
`b32fa5119d5f634d16b797777218093575a0c739d80b6a4c50da9493e73a2362`.
These hashes identify captured diagnostic bytes, not benchmark expected outputs.
Raw evidence and exact argv records were retained in the task's scratch workspace;
the portable public capture recipe is above. The published replay recipe uses
uv's managed interpreter; the original neutral smoke used the existing controller
Python 3.12.14 directly. BENJAMIN replay is **not run here**.

Embedded shell blocks passed `bash -n`; embedded Python parsed and the published
capture recipe was executed with byte equality and exit 7 verified. Its first
attempt encountered the read-only default uv cache (exit 2); the reviewed recipe
now uses an explicit temporary cache and passed without dependency synchronization.

Not tested: full regression, clean install, committed-lock replay, immutable
Docker image, enforced equal worker limits, output-overflow supervisor, namespace
or filesystem isolation, actual candidate principal denial, independent recovery,
public benchmark correctness or any comparison. Existing examples/test fixtures
were not repurposed into a benchmark. No claim of Genia advantage is made.

## Custody, cost and next gate

Independent hidden storage, actual implementation identities denied storage and
administrator/control-plane access, second-custodian recoverable copy, signed
annex integrity/transfer records and independent oracle auditor remain missing.
The owner and independent administrator/custodian must establish and verify them;
Docker, WSL2, users or directories alone do not satisfy that gate. No annex,
hidden fixture, grading credential or expected hidden output was accessed,
generated, transferred, mounted or uploaded. Candidate containers/build contexts
were not created, so their hidden-data access cannot be claimed verified.

Cost: only existing workspace commands and connected repository operations were
used. No paid provisioning, larger runner, paid API invocation, extra subscription,
artifact service or billing modification was requested; no new Actions run was
dispatched. Account invoices, host electricity and the owner's existing service
charges were not inspected; do not certify invoice totals. The approved budget
remains $0 incremental spending, with a hard stop before any paid dependency.

Independent review: `/root/skeptical_readiness` independently confirmed the Git
lock absence and ignore rule, reviewed the executable plan and parsed its
controller/child code. Final verdict: **PASS for the reviewed executable plan**,
no blocking findings, with frozen runner construction still NO-GO. A misleading
path-privacy statement was corrected: cwd/cache paths can identify the local
operator and require sanitization before public sharing. Reviewer did not run
BENJAMIN, attest custody or execute benchmark code; smoke execution results are
the author's evidence above.

Gate recommendation: **GO only for owner review of the lock-provenance correction
and optional existing-environment public diagnostic replay; NO-GO for a frozen
public runner build until an approved committed lock/source pair exists.** Hidden
oracle/corpus/candidates/trials stay NO-GO independently of that correction.

Single next action: **owner resolves and approves the versioned public dependency
lock corresponding to the chosen source, preserving the BENJAMIN lock bytes and
provenance instead of silently regenerating them.** This unlocks the most immediate
progress toward a genuinely reproducible public-only image/replay; it does not
authorize the comparative experiment.
