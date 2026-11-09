# #1250 registration preparation / validation hardening

PROPOSED_NOT_APPROVED. Author Codex. Starting head d3bf5b73; same PR #1318 branch
and base 9f96c6d9. Preflight: issue #1250 comment 6744494522; authorization
6744296276; independent build-correction approval review 5828336713 only.

Scope: close negative packaging/evidence tests, enforce future approval evidence,
prepare separate registration/activation patch, bounded local packaging tests.
No activation, acceptance, CI, semantic/oracle/host change, merge or closure.
Read latest AGENTS (e913e9d0), material STATE/RULES/REPL README/README, full two
reviews, ledger, backend/frontend/runner/tests and maintained-code/process rules.

Portability: Python-only tooling; C++ unaffected; portable contract unchanged;
Core IR unchanged; capabilities unchanged; shared semantic specs inapplicable
(host-local packaging/evidence tests); no host gap. MCP knowledge unchanged.
Maturity process-only. Core invariants: unchanged evidence/sentinel, strict
runtime/build freeze and artifact hashes, one input set for both frozen subjects,
real editable installation, fail-closed metadata and approval qualification.
No root semantic-doc changes needed. Preserve explicit authority/minimalism;
no new language semantics; supports authorized #1250/R29 prerequisite tooling.

Design: retain existing packaging path. Harden RECORD parsing/content validation
before modification and verify installed hashes/sizes afterwards. Add deterministic
injection tests at actual backend/frontend/provision wrapper boundaries and a
small real local-wheel hash-rejection test. Real successful packaging stays a
bounded preparation integration, never acceptance.

Future approval boundary: an explicit read-only validator requires a complete,
manifest-verified, exact-source, exact-proposal cold-cache evidence bundle with
successful non-skipped integration outcomes for both registered subjects, runtime
and build identities, editable RECORD validation, fresh private environments/cache,
retained commands/output and provenance. Old local evidence cannot silently
qualify future changed source or a different environment class. Normal unit runs
may omit integration; explicit approval validation must reject omissions.
Do not invoke the future approval-validation CLI in this task; unit-test the
validator and collect local preparation evidence only.

Registration JSON and an exact future activation patch stay separate/inactive.
The patch must wire the mandatory evidence validator before provisioning, using
an explicitly supplied evidence bundle, approved manifest digest, environment
class and exact provisioning-source identity. No active registration or sentinel
changes now. No proposal/status flag alone can activate execution. Any workflow
wiring remains separately reviewed in that future patch, not applied here.

Risks: bespoke metadata frontend and self-attested local evidence; hashes do not
prove an independent/hosted run. Reviewer must anchor bundle digest and intended
environment class externally. Rollback these preparation commits only, leaving
prior draft blocked and historical/additive evidence intact. Independent review
pending; GO preparation only, NO-GO activation. Test/implementation/docs phases
are explicitly authorized by the user; independent review is the stop gate.


## Implemented validation hardening

The PEP 660 path is retained. Before frontend mutation, installed RECORD must
parse as nonempty, unique three-column CSV with its self-row, safe paths inside
the target venv, and exact SHA-256/size pairs. Console-script paths may climb
within that venv. Missing/malformed/ambiguous RECORD, hash/size corruption and
path escape reject before direct_url writes; verification repeats afterwards.
The evidenced uv scope uses SHA-256, so unsupported hash forms fail closed.
Editable wheel installation now uses a hash-recorded direct-file requirement as
well as the preinstall digest check, preventing silent postverification changes.
Missing dynamic requirements become explicit RuntimeError; backend-path stays
unsupported. Project-wide build contract and target freeze stay unchanged.

Deterministic tests cover: two real uv rejection cases (incorrect wheel hash and
valid-ZIP bytes changed after registration); post-build wheel modification;
backend build and editable-install failures through actual provision() ->
provision_locked() -> coordinator, with failure finalization; dynamic missing,
wrong-version and direct-URL requirements; unsupported backend-path values;
missing/malformed/duplicate/ambiguous/escaped RECORD and invalid hashes/sizes;
wrong Python/implementation/uv/OS/architecture; backend leakage in freeze; and
baseline/candidate dependency/inventory/subject mismatches at qualification.
Existing lock/evidence/config guards and positive handoff tests remain.

## Mandatory future validation boundary

`tools/issue_1250/approval_validation.py` implements an explicit, read-only CLI.
It cannot activate a baseline. It requires all arguments, especially an externally
reviewed manifest SHA and intended environment class; no env-var-only skip path:

```sh
uv run --no-sync python -m tools.issue_1250.approval_validation \
  --evidence <fresh-complete-bundle> \
  --manifest-sha256 <independently-reviewed-digest> \
  --environment-class github-hosted-ubuntu-24.04
```

This CLI was **not invoked** in this task. Its validator is tested directly;
local integration collection self-checks its own local schema/integrity only.
The required real integration still needs ISSUE1250_BUILD_INTEGRATION=1 for a
normal developer pytest selection. If absent/skipped there is no successful
fresh bundle, so explicit approval validation rejects it. Success requires:

1. Current #1250 tooling/tests source hashes and exact registration/runtime/build
   input identities. Any material code/test/proposal change requires a new run.
2. Complete manifest with no missing/extra files or symlinks, anchored to the
   caller's independently reviewed digest, plus a retained execution log.
3. PASS, zero skipped, the exact real integration node, and ordered UTC timestamps
   no more than 24 hours old (at most five minutes clock skew into the future).
4. Supported CPython 3.12.14, uv 0.13.5 with recorded binary hash, Linux x86_64,
   declared OS/interpreter provenance and the explicitly required environment class.
5. Both immutable subject SHA/tree identities, clean status, separate initially
   absent caches/venvs and the same run ID; exact 42-package freezes and seven
   backend distributions; all build/install/freeze command exits zero with logs.
6. Retained actual project source import, editable metadata/RECORD proof and each
   built wheel digest. Wheel bytes may differ by source path; their hashes are
   retained individually, not compared as identical.

The collector uses a fresh empty output directory, marks actual exceptions FAIL,
preserves them, and cannot self-report PASS with incomplete subject evidence.
No old evidence directory is overwritten. `local-debian-13` is explicitly
**not** `github-hosted-ubuntu-24.04`. Hosted qualification additionally requires
Ubuntu 24.04 and attempt-1 allowlisted Actions/image provenance. These are
self-attested artifacts; hashes establish integrity, not independent execution.
The reviewer must verify run/artifact provenance and approve the expected digest
outside the bundle. No author-produced report gives independent approval.

## Registration and unapplied activation proposal

`tools/issue_1250/registration-proposal.json` records the exact runtime lock,
42-package freeze, build evidence/requirements digests, full seven-package
inventory, Python/uv/platform scope, subject SHA/tree requirements, qualification
commands/evidence and rollback. Its status is PROPOSED_NOT_APPROVED. Active
registration.json and APPROVED_DEPENDENCIES = None are unchanged.

`tools/issue_1250/activation.proposed.patch` is an exact **unapplied wiring diff**
against this code. `git apply --check` passed; it was not applied. It proposes:

- A shared runtime evidence tuple in the provisioning wrapper, followed by a
  mandatory approved receipt and fresh exact-source hosted qualification check.
- A separate approved-qualification.json receipt deliberately left
  PENDING_INDEPENDENT_APPROVAL with null manifest digest.
- A workflow artifact-presence check and namespace propagation of the bundle
  path. No active .github file was changed and no workflow was dispatched.

**This is not a fully authorized/operational activation.** Even applying this
wiring proposal alone would fail on the pending receipt/missing hosted evidence.
Further independently reviewed work must select an explicitly authorized hosted
validation run/artifact, implement its pinned download/provenance verification,
provide an approved manifest receipt, and update activation-specific guard tests.
Changing run.py through activation changes the source fingerprint: collect fresh
qualification for that final code, not this earlier local bundle. Any actual
smoke/acceptance also requires separate exact-SHA authorization. No approval
receipt, artifact ID or hosted success is fabricated in this preparation.

Future validation environment setup must provide the pinned dev/test runner
without a live project build: copy the same immutable lock to its disposable
infrastructure checkout, sync --dev --locked --no-install-project --no-build,
then run the exact integration node with ISSUE1250_BUILD_INTEGRATION=1 and a new
output directory. The integration itself allocates separate empty subject caches
and installs the real editable projects. This bootstrap/download wiring is
future infrastructure work, not an added/dispatched workflow here.

## Executed tests and evidence

Preflight comment 6744494522 verified before implementation. Committed RED:
310ba993 and 33323498. Implementation bbe34efb references both. The first RED also
exposed an invalid-ZIP test-construction case; it was corrected to mutate a valid
wheel so the final real uv assertion specifically proves hash rejection. All
RED logs and intermediate passing preparation runs are retained.

Final bounded local command, from repository root:

```sh
ISSUE1250_BUILD_INTEGRATION=1 \
ISSUE1250_BUILD_EVIDENCE=/workspace/1250-registration-preparation/final-qualified-cold-validation \
UV_CACHE_DIR=/workspace/1250-registration-preparation/test-cache \
uv run --project /workspace/1250-proposed/subject --no-sync pytest -n 0 -q \
  tests/unit/test_issue_1250_acceptance_infrastructure.py \
  tests/unit/test_issue_1250_build_backend.py \
  tests/unit/test_issue_1250_validation_hardening.py \
  tests/unit/test_issue_1250_approval_validation.py
```

**127 passed in 16.57s; zero skipped.** Real baseline and candidate each used a
fresh private cache/venv, the unchanged lock and identical backend evidence;
both finish clean with exactly the proposed 42 non-editable packages. The root
bundle self-verifies as local only. This is Debian/Clang local packaging evidence,
not hosted CI, acceptance, an explanation of original failures or GREEN.

Other checks:

```sh
UV_CACHE_DIR=/workspace/1250-proposed/test-cache uv run --project /workspace/1250-proposed/subject --no-sync ruff check tools/issue_1250 tests/unit/test_issue_1250*.py
UV_CACHE_DIR=/workspace/1250-proposed/test-cache uv run --project /workspace/1250-proposed/subject --no-sync python -m tools.code_documentation --base-ref d3bf5b73
python3 -m compileall -q tools/issue_1250
git diff --check
git apply --check tools/issue_1250/activation.proposed.patch
```

Ruff passed; documentation checker: **10234 records / 2793 legacy gaps /
1 classification / 0 errors**. Compileall/whitespace/patch syntax checks passed.

Additive evidence: `tools/issue_1250/dependencies/registration-preparation-2026-11-09/`.
`local-cold-bundle.tar.gz` contains the complete 62-file local qualification plus
its manifest (extract into a fresh scratch directory); preparation-logs.tar.gz
retains RED and all interim/final command logs. validation.json retains command,
environment, source identities, subject results and hashes. No old fixture is
rewritten. Archives keep repetitive lock/log bytes without expanding the diff.

| Evidence | SHA-256 |
|---|---|
| Registration proposal | `daebb2c2383fe710126fd139a9d68da112c2c34b08cc35619cae1d1a23447c6c` |
| Unapplied activation patch | `3f3244842be8e130511cb593018acc8fb7776f02dd38af10d2781b4543dbd584` |
| Local qualification manifest | `8e3dd3efeedaea95ab7858b547cddc57d946c24e6b642d6cca3668f90924cfd1` |
| Local qualification archive | `98a636a40affe453d10b12c51d78cac46737bd74de27bc1d30dc02411629327b` |
| Evidence package manifest | `59fc68e1368de67515c176c46fcb9200f49c0572e067535bac5cc060fa3283f7` |

Runtime lock remains 2bb0f5f5a5b073539ba0df6e92820a461d3cfb5364ca8951a99717b3c684a8bf;
build evidence remains e1fae82b5e5358d7db86ede48903cda603eea0d26050de6827cf850e21a65404.
All exact per-wheel hashes/inventory remain in the unchanged backend proposal.

## Review, limits and rollback

Independent Claude review of this exact preparation change is pending. The earlier
build-backend approval (5828336713) is not baseline/activation approval. Review
actual code, tests, metadata, archived raw evidence and unapplied diff. Local
reports are self-attested; freshness expires and code changes invalidate them.
Hosted Ubuntu/GCC, namespaces and acceptance remain untested. Artifact availability,
new dependency behavior, source-path-specific wheels and unknown historical lock/
backend bytes remain limitations. No security or semantic clearance claimed.

Rollback preparation: revert these registration-hardening commits only; retain
both new archives, RED outcomes and all earlier evidence in the append-only
ledger. Rollback future activation: restore the sentinel to None, remove active
receipt/wiring in a reviewed revert, retain qualification/failure artifacts and
leave historical registration untouched. Never run the old live solver to relabel
old outcomes. No historical 22 failures, old digest/freeze/registration, previous
runtime/build fixtures/manifests, test oracles, workflow or authority docs changed.
No acceptance/G0/G1/G2/CI dispatch, merge, closure or executor-A/#1316 work.
Stop after the verified handoff; future activation requires separate authorization.
