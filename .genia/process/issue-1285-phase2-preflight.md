# #1285 — Phase 2 preflight and oracle stewardship

Status: **NON-AUTHORITATIVE / PREFLIGHT / NO-GO for fixture or oracle construction**.
Date: 2026-10-26. Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285).
Design: [draft #1286](https://github.com/m0smith/genia-2026/pull/1286), frozen
reference `4ee8713ecfa391e1a8f74610b2e1dcad745d0779`,
`.genia/process/issue-1285-product-value-design.md`, sections 1–6.
The current user instruction approves Phase 2 preflight subject to custody and
isolation, and explicitly requires another review before corpus generation.
The older design's pending Phase 2 authorization is superseded only to that extent.

This record supplies the execution plan, custody status, environment lock
specification, oracle construction specification, cost assessment and readiness
decision. It neither changes the benchmark nor claims any experimental result.
Python winning, parity and inconclusive evidence remain valid outcomes.

## 1. Scope and completed preflight

Classification: required infrastructure, release-independent; no R29 expansion.
Branch: `issue-1285-phase2-preflight`. Author: Codex, proposed steward only.
Owner: repository maintainer; operational appointments remain pending.

Includes: public planning, read-only capability checks, inventory and independent
skeptical readiness review. Excludes: hidden material creation or retrieval,
oracle implementation, competing programs, trials, language/runtime/MCP/CI edits,
release changes and merging #1286. No process artifact belongs in `docs/`.

Authority: current `AGENTS.md`, `GENIA_STATE.md` (final language authority),
`GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`; strategy references are
`killer-workflow.md`, `human-ai-shared-programming.md`, `release-roadmap.md`;
process references are `08-roadmap-ticketing.md`, `run-change.md` and the
change-preflight template. The current main was fetched and matched local HEAD:
`79c073b556ad16343051d545d7928248a6d0f6b0`; AGENTS Git blob
`b072beb55d22d5856d3d356d73c60704e04d197f`. Issue body/discussion and full
755-line design were inspected. No language capability is inferred from roadmap
or approved proposals. Core documents remain unchanged because behavior did not change.

Maturity: N/A, process only. Portable contract: unchanged. Python/C++ implementation:
unchanged. New benchmark/harness behavior: not implemented. MCP language-knowledge
impact: none; no new language fact or generated profile update. Complexity:
necessary study separation only. Philosophy: minimalism, explicit behavior,
pattern-first alignment and validated-pipeline priority preserved. Drift risk:
low for semantics, high for isolation and study validity. Examples in this record
are process specifications, not executable Genia examples.

Seven-field portability analysis: (1) authority is STATE, benchmark output is an
application contract; (2) boundary is JSONL bytes and process streams/status,
not Core IR; (3) existing CLI/JSON/resource tests are capability evidence only;
(4) applicability is the Python reference host for the Genia arm, with existing
`cli_file_mode`, `cli_command_mode`, `json_strict`, `json_compat`, `resource_io`;
(5) neither host changes and no new parity claim; (6) runtime gaps become honest
experiment failures, never unapproved fixes; (7) synchronize experiment records
only, leaving language docs/specs/book/cheatsheets/registry unchanged.

Test strategy: existing capability checks plus inventory, allocation arithmetic,
hashes, whitespace, scope and public-payload inspection. No new tests mirroring
this prose. Relevant invariants are no secrets, no hidden generation, no semantic
edits and no custody claim without evidence. Failure means stop the dependent
phase. Phases here: preflight documentation and requested independent review;
contract/RED/runtime implementation/distillation are inapplicable to unchanged
language behavior. Host-specific security verification is required later from
actual principals. Final gate: NO-GO, missing evidence listed below.

## 2. Execution plan and stopping conditions

All later steps are instructions for future authorized work, not completed work.

| Step | Responsible role | Dependency / action | Exit evidence and stop |
|---|---|---|---|
| P0 | Owner | Confirm exact design revision; adjudicate amendments below; appoint operator, second custodian and independent oracle auditor | Named acceptances and approved amendments; otherwise stop |
| P1 | Operator/security administrator | Provision separate steward storage, recovery custody and clean implementation environments under distinct access boundaries | Access matrix, denial tests and recovery proof; otherwise no annex transfer or hidden generation |
| P2 | Existing annex holder + steward + second custodian | Authenticate endpoints, transfer annex privately, verify byte hash and recovery | Signed restricted custody receipts matching published commitment; mismatch stops transfer/use |
| P3 | Operator | Build clean locked runtimes and documentation exports; verify equal limits and instrumented no-op subprocesses | Immutable image/dependency/model/docs/harness lock and replay logs; unresolved pins stop freeze |
| P4 | Owner + readiness reviewer | Review P0–P3 evidence, including amendments and independence declarations | Report GO/REVISE/NO-GO and STOP for review before any frozen corpus generation |
| P5 | Steward, only after separate review authorization | Construct exact 30 public/60 hidden invocations and independent expected results in approved storage | Complete coverage/envelope manifest; no competing implementation |
| P6 | Independent oracle auditor | Independently derive every expected result; inspect comparator, self-tests, hashes and security | All disagreements resolved against contract; otherwise no freeze |
| P7 | Owner | Review signed immutable bundle and approve challenge exposure separately | Stop; pilot/trials remain unauthorized in this task |

No step can be satisfied by a task checkbox alone. Revoked access, hash mismatch,
plausible leakage, undocumented environment change, oracle disagreement, missing
independent reviewer or resource inequality blocks the dependent phase. A leak
quarantines the matched block and preserves evidence; it is not repaired by asking
an agent to forget. No hidden-test feedback before immutable final submission.

### Contract preserved and amendments requiring approval

Preserve design section 1 exactly: argv launch vectors for file or `-` stdin;
UTF-8 and LF/CRLF physical-line rules; strict JSON with duplicate-name rejection;
missing/type/value field ordering; bool distinct from integer tokens; Unicode
scalar equality without normalization; valid-only first-accepted duplicate state;
accumulated diagnostics; exact report schema and ordered arrays; deterministic
results and fatal stream/exit predicates. Preserve Genia, Python stdlib and
Python+Pydantic arms, independent grading, fresh cross-agent comprehension,
requirement changes and two separate defect repairs. Correctness is a 100% hard
gate, not a weighted score. No benchmark simplification is proposed.

Clarifications to approve before freezing, without silently changing counts:

* A1: map the three public fatal invocations onto the listed failure conditions.
  They cannot each separately cover missing operand, extra operand, missing path,
  directory/unreadable source and invalid UTF-8. Preserve three/six counts; owner
  must approve the public/hidden coverage mapping, not infer one invocation has
  several independent exit observations.
* A2: precise byte-size boundary interpretation (physical line measured before or
  after CRLF stripping) and envelope checking of malformed/deep syntax. Retain
  1 MiB, 1,000 lines, 16 KiB/line, eight-container bounds and numeric token limits;
  approve a deterministic envelope checker rule before cases at those boundaries.
* A3: approve canonical expected-artifact serialization and provider model-drift
  response. Candidate comparison remains semantic, so serialization cannot become
  a new byte-format correctness demand. Model replacement never occurs silently.

The public contract contains fatal rules and Unicode/state rules; these proposed
clarifications are not concealed requirements or a replacement private annex.

## 3. Stewardship and custody record

### Actual state

A separate **public-only, non-authoritative planning workspace** was created
outside the semantics checkout. It contains inventory and public planning only.
This is organizational separation, **not secure isolation**. No restricted hidden
store was provisioned or verified. Current agents use the same UID and readable
workspace; a 0700 directory does not separate agents sharing that identity.
No private annex was requested, located, read, copied or transferred in this task.
No hidden fixtures, concealed scenarios or benchmark oracle code were generated.

| Role / control | Current status | Evidence required |
|---|---|---|
| Owner | Maintainer is decision owner | Operational appointments and budget approval |
| Oracle steward | Codex proposed; not provisioned | Distinct non-implementation principal/session and signed role exclusion |
| Second custodian | Unappointed | Independent principal, retained encrypted copy and verified recovery |
| Oracle auditor | Unappointed | Separate expectation derivation/review; no candidate authorship |
| Execution operator | Unappointed | Clean exports, countersigned limits/access evidence |
| Readiness reviewer | Separate agent reviewed evidence | Does not appoint a custodian or certify a future oracle |
| Restricted storage | Unestablished | Administrator-reviewed ACL/mount/credential boundary and audit logging |
| Annex transfer/integrity | Not performed | Authenticated chain and matching receipt; commitment alone is insufficient |

Public annex commitment copied from the design, **not verified against annex bytes**:
`929984f1bbba850de61a1c978149862c70e455c97eba25e93c742ec10cbd4055`.

### Proposed permissions and verification

Use an administrator-provisioned store outside public Git and every candidate
mount, history, backup, agent memory, transcript export and shared writable home.
Only steward writes hidden data; second custodian holds an independently
recoverable protected copy; auditor receives controlled read access; operator
runs grading without exposing hidden content. Implementers and blind maintenance
agents have no hidden read/list/write or credential access. Administrator access
is explicitly recorded and those administrators cannot perform blind trials.
Encryption at rest or a separate folder alone is not an access control proof.

Before receiving secrets, place a non-sensitive sentinel at the proposed boundary.
Using **each actual future implementation identity and filesystem/network policy**,
test direct reads/listing, parent traversal, shared mounts, symlinks, Git history,
backups, logs and access-token availability through the supported boundary.
Verify denied access and absence from allowlisted exports, and positive steward
access. Do not bypass restrictions, attempt credential extraction, or treat an
untested root/admin escape as a solved boundary. Retain principal, time, test,
policy revision and result privately; publish a sanitized pass/fail attestation.
Repeat after configuration/export changes. Same-UID local trials cannot attest
this boundary. Secure receiving storage must pass before the annex arrives.

### Secure transfer procedure and restricted receipt

1. Owner authenticates current holder, steward and second custodian through an
   existing trusted channel; verifies approved recipient public keys/endpoints.
2. Holder hashes the exact original annex bytes, compares the published commitment,
   encrypts to approved recipients and sends over approved authenticated private
   transport. Do not paste it into chat, Git, PRs or candidate-accessible storage.
3. Steward verifies signature/sender, decrypts only in verified restricted storage,
   checks byte length and SHA-256 against the commitment, then signs receipt.
4. Second custodian independently verifies its protected retained copy and a
   recovery read/hash; countersigns. No edits/newline normalization of original.
5. Store append-only custody events privately: artifact/version, bytes/hash,
   authenticated sender/recipient identifiers, role, UTC timestamp, key identifier,
   transport transaction ID, storage policy revision, access-test references,
   signed acknowledgments, recovery result, revocation/deletion events.
6. Publish only role-level attestation and integrity outcome. Credentials, private
   locations, identities/receipt details and concealed content remain restricted.
   If any receipt/hash/access proof is missing, custody stays NOT ESTABLISHED.

Hashes prove byte integrity, not sender identity, independence or confidentiality.
An independent subagent in this shared workspace is not a second custodian.

## 4. Environment lock specification

Observed inventory is **not a trial lock**; no clean image replay or resource
equivalence certification occurred. No environment will be silently substituted.

| Item | Observed exact value | Remaining lock obligation |
|---|---|---|
| Genia / Python reference host source | `79c073b556ad16343051d545d7928248a6d0f6b0` | Build immutable source artifact with toolchain/dependency hashes |
| Host package metadata | genia `0.1.14` | Metadata version alone cannot identify source |
| CPython | `3.12.14`, Clang `22.1.3` | Freeze interpreter artifact and build provenance |
| Interpreter SHA-256 | `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7` | Artifact replay remains unverified |
| Repository uv.lock SHA-256 | `c9543edd814d8ab75fc668908ca48cdfafe94d536a74e56266258a7f219e1ba7` | Lock does not include the complete Pydantic arm |
| Existing Genia venv | PyYAML `6.0.3`, pytest `9.1.1`, pytest-xdist `3.8.0` | Hash all installed artifacts; fresh offline replay pending |
| System Pydantic inventory | Pydantic `2.13.4`, pydantic-core `2.46.4` | Not installed in Genia venv; proposed baseline only, not approved trial lock |
| uv | `0.12.23` | Hash executable/build artifact |
| Codex CLI inventory | `0.159.2` | Not evidence of this chat backend or trial model |
| Codex model/reasoning | Unverified | Operator records explicit model ID/reasoning/client/config and service receipt |
| Claude Code/model/config | Unavailable in current PATH; unverified | Provision and lock client/model, permissions, hooks, plugins, tools, token accounting |
| OS/kernel/architecture | Debian `13.6` trixie; Linux `6.18.55`; x86_64 | OCI image digest/build recipe, base digest and OS package manifest missing |
| Harness | Not implemented | Pin source SHA, subprocess/comparator revisions and artifact hashes |

Do not claim exact provider weights are pinned by a model alias. Closest
reproducible setting is explicit model ID, reasoning configuration, CLI build,
sanitized effective settings, provider-returned identity, UTC run window and all
exposed sampling/seed settings (unsupported fields recorded unsupported).
If exact version pinning is unavailable, declare service drift as a limitation;
pause a matched block on observed drift/unavailability and obtain protocol review.
No invented exact model name or equivalence of reasoning budgets.

Before freeze create a hash-locked wheelhouse for each arm (including Pydantic,
pydantic-core, annotated-types, typing dependencies and every resolved transitive),
architecture/Python ABI tags, install command, packaging build tools and an
offline clean-install receipt. Use dependency names resolved from actual metadata,
not this illustrative list as a complete lock. Pin separate environments; never
fall back from missing Pydantic to stdlib or from a venv to system packages.

Harness lock includes argv arrays with shell disabled, cwd, input bytes, stdin
EOF, explicit env allowlist, locale, TZ=UTC, umask, clean writable tmp directory,
source/dependency/doc hashes, process-group cleanup, monotonic timing, separate
bounded byte capture and raw status. Resource policy is the design's two vCPU,
4 GiB per worker, 60-second invocation watchdog, 16 MiB each stdout/stderr.
Prove memory/CPU allocation, wall deadline, overflow classification and reaping
with neutral no-op/resource probes, equally for all runtimes; no solution code.
Primary tools are shell/editor/public runner; network off, no MCP/web/shared
memory/repository history. No unverified profile is called a sandbox.

Provide complete versioned local Genia authority/reference/tested examples/help,
Python language/stdlib docs and pinned Pydantic docs for its arm. Export by
allowlist, hash every document and inspect exports for benchmark design/history,
annex or prior solutions. Appropriate documentation access and equal resources
are specified but **not verified across future workers**. Instrumentation captures
checkpoints/usage/failures outside agent-readable storage. Pin analysis Python too.

## 5. Independent oracle construction specification

Construction remains blocked. No expected-result corpus or comparator exists.
The following preserves design section 2 rather than substituting an implementation.

| Family | Public | Hidden |
|---|---:|---:|
| Happy reporting/metadata | 4 | 8 |
| Malformed JSON/non-object roots | 5 | 10 |
| Fields/accumulated diagnostics | 7 | 14 |
| Duplicate/state interactions | 3 | 8 |
| Unicode/line framing | 4 | 8 |
| Empty/boundaries | 4 | 6 |
| Fatal CLI/input | 3 | 6 |
| Total invocations | 30 | 60 |

One invocation is one process execution. File/stdin occur in each data family,
with a valid paired file/stdin invocation in each partition. Three-repeat checks
on selected mixed/Unicode/empty invocations are operational repeats, not extra
independent samples. Metamorphic/self-tests are additional oracle validation,
not relabeled members of the 90-case frozen inventory. Full clause-to-case coverage
and numeric/size/depth envelope validation must pass before freeze.

Manifest schema specification: bundle schema_version/contract_revision/design SHA,
environment lock hash, harness/comparator SHA and signed freeze approval; entries
contain unique case_id, partition, family, clause IDs, mode, exact argv vector,
input byte length/SHA-256, environment profile, filesystem setup recipe/hash,
expected artifact hash or fatal predicate, generator revision/seed where used,
steward derivation reference, independent reviewer derivation reference and
approval timestamp. Expected outputs are strict language-neutral JSON documents;
fatal artifacts specify class, streams and numeric exit predicate. No candidate
module, evaluator, Genia validation helper or Pydantic model is oracle authority.
Record all input bytes, not text translated by the operator's platform.

Normative expectation method: write clause-indexed decision tables from design
section 1; steward derives line classification, ordered field diagnostics,
accepted-only duplicate state and exact integer summary arithmetic. A distinct
auditor independently hand-derives **every invocation's entire expected result**,
including large boundary cases via separately derived arithmetic/structural
proof and an independently authored checker. The auditor must not merely inspect
the steward's output first or run the three candidate programs. Retain both
derivations and resolve disagreements against written contract before freeze.
A second strict parser/manual token inspection cross-checks duplicate names,
Unicode scalars and integer/fraction/exponent classification. Same-language
oracle implementation is allowed; semantic independence must be demonstrated.

Comparator requirements: capture raw bytes/status; strict UTF-8; exactly one JSON
stdout document; reject duplicate object keys at any nesting, nonfinite numbers,
invalid scalar strings, extra documents and trailing non-whitespace. Validate
exact keys/types/ranges before recursive equality. Ignore object member order,
insignificant JSON whitespace and escaped-vs-literal scalar spelling. Preserve
array order, exact Unicode sequences and integer values/token types; bool is not
int. Never trim strings, normalize Unicode, coerce missing/null/numbers/strings,
unwrap double-encoded JSON or interpret Outcome/debug rendering.

Completed invocations require exit 0, empty stderr and full expected report;
recoverable data errors do not become fatal. Fatal input/usage cases require
empty stdout, ordinary status 1..125 and the precise design category line,
optionally followed by `: ` detail. A substring in a traceback is insufficient.
Signals, timeouts, output overflow and crashes cannot pass as fatal categories.
Use a non-root subject for unreadability checks and verify the intended denial.
Record exact raw statuses and streams regardless of normalization.

Self-test acceptance plan: equivalent key order/spacing/Unicode escapes pass;
independently authored wrong outputs with dropped diagnostics, reordered arrays,
wrong summary, bool-as-count, decimal-as-integer, duplicate output keys,
double-encoded document, debug none, extra stdout, unexpected stderr or wrong
exit status fail. Include fatal category near-miss/substring and signal rejection.
Audit comparator fail-closed behavior and its own induced-error handling.

Metamorphic plan: file/stdin and LF/CRLF equivalence; ignored metadata addition;
blank append changes only specified counters/diagnostic; adding a distinct valid
row changes only derived fields; permutations change source ordering and
first-accepted duplicate choice exactly as written. Properties supplement fixed
goldens. Repeats must be semantically identical; raw byte stability is separately
recorded, not a new correctness gate.

Freeze stores content-addressed input/expected bytes, canonical manifest,
comparator/harness/dependency/docs/image hashes and signed reviewer approvals in
immutable/versioned storage. Define canonical artifact serialization under A3;
hash exact stored bytes with SHA-256, independently recompute all hashes, and
keep the hidden manifest restricted. Publish only public-partition content and
sanitized freeze attestation; never hidden paths/seeds/content. Corrections create
a new version, retain original evidence and uniformly rescore every arm. Candidate
agreement alone never establishes oracle correctness.

## 6. Ownership, pilot, risk and cost

Human/external decisions: appoint independent principals and administrators;
approve storage/access, transfer endpoints, amendments, exact models and budget;
recruit six human participants and two scorers; adjudicate protocol/oracle disputes.
Automatable after authorization: inventory/hash generation, allowlist export
checks, clean-install replay, resource probes, capture/checkpointing, manifest
validation, comparator self-tests, deterministic grading and reporting. Human
comprehension cannot be substituted by agent scores. Signed independent review
is not replaced by automation.

Future minimal pilot: one Genia implementation by isolated Claude Code, one
stdlib implementation by isolated Codex, and one Pydantic implementation by a
separate Claude session. These are the three approved approaches, not two
language-only arms. Use original caps (initial 120 active/180 elapsed minutes,
80k input+output tokens); fresh comprehension 20 minutes, change 60/90 minutes
and 40k tokens, each of two repairs 45/60 minutes and 30k tokens. Stop at first
cap or submission. Downstream comparisons include only independently correct
snapshots and report attrition; no expert replacement. Pilot is feasibility and
instrumentation only, confounded by model assignment; no ADOPT inference.
Full six-block balanced-model replication requires separate approval, as does
pilot execution itself. No trials began here.

| Work | Revised person-days, planning only |
|---|---:|
| Security, custody and reproducible environment setup | 2–4 |
| Oracle and 90-invocation construction | 2–3 |
| Independent expectation/comparator verification | 2–3 |
| Pilot operation, instrumentation review and report | 1–2 |
| Six-block replication, maintenance/repair operation | 3–5 |
| Human recruitment, administration and dual scoring | 1–2 |
| Final independent replay/audit/report | 1–2 |
| Total | 12–21 |

Assumes an eight-hour person-day, available managed isolation/storage, cooperative
annex holder and model access. Procurement/identity setup/recruitment calendar
delays are additional and unbounded here. Setup+construction+verification+pilot
is 7–12 person-days, not a spending authorization. Prior 8–15 estimate understated
verified security and independent derivation work. Keep these human/operator
efforts separate from agent active time: complete pilot plus six blocks has up
to 101.5 aggregate capped agent hours, excluding provider outages/elapsed caps.
Human answer sessions total six participant-hours, plus recruitment/scoring.
Provider cost is unknown until models/rates/usage are pinned; archive dated rates
and billable input/output/cache use. No invented dollar budget or measured gain.

Risks: same-identity leakage (blocking); absent independent custody (blocking);
model/image/dependency drift (blocking); oracle shared conceptual error (independent
derivations); coverage ambiguities (A1–A3); model/arm confounding (pilot limitation);
small correlated sample and missing humans/costs (withhold positive value claim).
No requirement may be weakened to help Genia finish. CLI inability is evidence,
not permission to modify runtime or launch-recipe business logic.

## 7. Readiness evidence and independent skeptical review

Actual checks performed on 2026-10-26:

* Fetched default branch and PR ref; confirmed main and design SHAs above and
  unchanged current AGENTS. GitHub plugin also confirmed #1286 open/draft and
  fetched issue discussion. Shell `gh` API failed Forbidden; connector reads work.
* Existing capability check, no benchmark fixtures: `UV_CACHE_DIR=/workspace/work/uv-cache
  uv run --no-sync pytest -q tests/unit/test_cli_args.py
  tests/unit/test_json_representation_boundary.py tests/unit/test_json_stdlib.py
  tests/spec/test_parse_jsonl_record_shared_spec_389.py
  tests/unit/test_resource_io.py -k 'not zip'`: **115 passed in 2.26s**.
  This verifies selected existing building blocks, not complete benchmark
  composition, a fresh install, a new oracle or full runtime regression.
* Observed interpreter/package/OS/CLI versions and hashed interpreter, source
  documents and uv.lock into a local public-only inventory. No secret values or
  broad process-environment dump. Runtime network status reported current
  observations but policy state unknown; enforcement/isolation is not certified.
* Independent reviewer `/root/skeptical_readiness` inspected source refs, AGENTS,
  design and shared filesystem identity. Initial verdict **NO-GO**: same-UID
  access is not isolation; custodian/transfer/access-denial evidence is absent;
  package versions are not artifact locks; CLI version is not model identity.
  Reviewer did not access annex or hidden material and is not an appointed
  second custodian or future oracle auditor.
* Final independent document review: **PASS for public preflight/readiness
  documentation; NO-GO for construction**, with no blocking document finding.
  Reviewer confirmed the 30/60 allocation, three approaches, limits, normalization,
  complete independent expectation derivation and review-before-generation stop.
  A1 is a pending coverage allocation decision, not a claim that the design
  required every fatal subtype in the public partition. Publication success is
  established only by actual remote payload verification after this review.

**Decision: NO-GO for actual fixture and oracle construction.** Planning workspace,
contract trace, inventory and selected capability evidence are established.
Secure storage/isolation, independent custody/auditor appointment, annex transfer,
clean environment replay, exact trial models, equal limits/docs exports, completed
oracle audit and frozen corpus are unverified or absent. No generation is allowed
while these blockers remain. Even after they pass, report readiness and stop for
the requested review before corpus generation.

Single next action: **owner appoints the independent second custodian and oracle
auditor and assigns an administrator to provision the access-separated stewardship
boundary for verification**, without transmitting the annex into this workspace.
