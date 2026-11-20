# #1285 — validated CI-results product-value benchmark design

Status: **PROPOSED / DESIGN ONLY / NON-AUTHORITATIVE**, revision 1.
No fixtures, oracle, challenge solutions, runtime changes, or experiment runs are
authorized by this document. Date: 2026-10-25. Owner: repository maintainer;
design author: Codex. Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285).

Research question: **Can humans and AI agents produce, understand, verify, debug,
and maintain this validated-data pipeline more effectively in Genia than in
Python?** A Python win, parity, or an inconclusive result is a valid outcome.
This tests one local CI-result reporting workload and its development workflow;
it cannot establish general language superiority, human-only productivity,
production readiness, C++ parity, or large-scale streaming performance.

## 0. Pre-flight, authority, evidence and placement

### Scope and source record

Classification: required infrastructure, release-independent product validation,
following #1226 and #1224. No R29 blocker, release expansion, feature ticket,
CI change, or permanent agent-policy gate. Branch:
`issue-1285-product-value-design`. This is the user-authorized DESIGN phase only.

Default branch `main` inspected through GitHub at
`79c073b556ad16343051d545d7928248a6d0f6b0`. Latest AGENTS blob:
`b072beb55d22d5856d3d356d73c60704e04d197f`. Local checkout and all ten named
instruction/source files below have matching Git blob hashes with the remote
default-branch copies; shell fetch was unavailable, so the connector supplied
current remote evidence. This source baseline is a proposed runtime pin, to be
confirmed and built before trial preregistration, never silently moved mid-study.

Read in precedence: [STATE](../../GENIA_STATE.md), [RULES](../../GENIA_RULES.md),
[REPL README](../../GENIA_REPL_README.md), [README](../../README.md), then
[killer workflow](../../docs/strategy/killer-workflow.md),
[Human–AI strategy](../../docs/strategy/human-ai-shared-programming.md),
[roadmap](../../docs/strategy/release-roadmap.md),
[ticketing](../../docs/process/08-roadmap-ticketing.md),
[run-change](../../docs/process/run-change.md), the pre-flight template, and
[execution-realization direction](../../docs/architecture/execution-realization.md).
Reviewed issue bodies and every returned comment for #1285, #1226 and #1224;
also the non-authoritative #1226 product-value review. Strategy and proposed
application lifecycle/default-open work confer no implemented capability.

Maturity: N/A, process/design only. Genia validation/JSON helpers used as feasibility
evidence are Experimental; Seq/Flow shared evidence remains partial. No semantic
contract or implementation/example changes: STATE, RULES, book, cheatsheets,
specs, capability registry and generated MCP profile require no change. MCP
language-knowledge impact: none; the benchmark specifies an application task,
not new Genia facts. This scope-specific rationale avoids changing implemented
authority merely to describe a proposal.

### Completed pre-flight fields

Includes: functional contract, corpus/oracle design, isolated agent protocol,
measurements, skeptical review, approval sequence and handoff. Excludes: all
three solutions, test fixtures, oracle code, parser/evaluator/runtime/MCP changes,
mandatory workflow changes and feature-ticket creation. Process-only minimal
examples are prose acceptance designs, not runnable Genia examples. Complexity:
necessary independent comparison and isolation, no implementation machinery yet.
Philosophy: minimalism YES; explicit behavior YES; semantics outside host adapters
YES; pattern-first alignment YES; validated-pipeline relevance YES. Cross-file
semantic drift risk low, experiment validity risk material. Future behavior
implementation phases are skipped because they are not authorized.

Portability analysis (seven fields):

1. Authority/boundary: STATE governs Genia; this proposal governs benchmark
   application output only. It creates no portable language behavior.
2. Representation: raw JSONL bytes in, ordinary JSON document plus subprocess
   status/streams out. No Core IR or runtime value change.
3. Executable evidence: existing CLI, JSON, JSONL and resource tests, identified
   below; future benchmark cases live separately and never become Genia specs.
4. Applicability: Python reference host only for the Genia arm. Existing capability
   vocabulary includes `cli_file_mode`, `cli_command_mode`, `json_strict`,
   `json_compat`, `resource_io`; no new capability or conformance registry.
   Pipe mode and MCP are not the benchmark execution interface.
5. Claims/evidence: Python-host feasibility only. C++ not affected, no parity
   claim. Required file/stdin composition is still for future implementations to
   satisfy; building blocks do not prove the complete benchmark works.
6. Gaps: report a benchmark capability/integration failure honestly. Do not add
   known-host-gap entries, relabel required cases, or repair the runtime here.
7. Synchronization: update the experiment's versioned design and evidence after
   each approved phase. Authoritative language documents change only in a
   separately approved language task, never to accommodate a benchmark outcome.

GO for draft design publication; no claim of implementation or oracle approval.
No public binding is added, so maintained-code coverage is unaffected.

### What the earlier evidence does and does not establish

[#1226 review](https://github.com/m0smith/genia-2026/issues/1226#issuecomment-6295790055)
reported a seven-line Genia feasibility slice and discovery friction, without a
Python head-to-head or CLI/file/stdin execution. The
[16-row follow-up](https://github.com/m0smith/genia-2026/issues/1226#issuecomment-6297347220)
reports initial accepted suites parser/网络/memory/storage/integration/build/lint,
status counts 3/2/2, total 1,801,222 ms; changed counts 2/1/2 and total 600,221 ms.
It corrected integer validation (bool/float/string rejection) and the point at
which duplicate identifiers are reserved. Null/debug rendering and a nil
short-circuit required care. Those are reported historical results, not runs
performed for #1285. The downloadable original artifact is not in the repository
or supplied here: its exact bytes/hashes could not be audited, so it is not our
frozen corpus, oracle, training solution, or quantitative baseline.

Earlier prototypes were iteratively corrected by informed authors, evaluated
in-memory through MCP, and compared with Python references; independent effort,
cross-language CLI assertions, Genia defect repair and human comprehension were
not established. A separate rounding mismatch (`1.234` vs `1.235`) in the pilot
warns against inferring full equivalence from a small successful subset. Comments
and slices are correlated task families, not independent replications. #1226 is
closed in current metadata although older comments say keep open; do not reopen
it or extend its temporary reminder as part of this task.

### Verified capability boundary

LANGUAGE CONTRACT: current STATE anchors `state:execution-model`,
`state:outcome-propagation`, and its Bytes/JSON/ZIP bridge section govern the
building blocks, not this benchmark's business rules.

PYTHON REFERENCE HOST: file/command `main(argv())`, stdin adapted through `lines`,
`read_file`/resource text IO, strict JSON encoding/decoding and compatibility JSONL
exist. `parse_jsonl_record` has blank/non-object/error Outcomes; strict decoding
returns an outer JSON representation and rejects duplicate object names.
Compatibility JSONL and strict JSON have different acceptance/error boundaries.
`json_encode` returns an Outcome containing pretty, sorted-key JSON text; returning
that text as a final CLI value is not equivalent to writing raw JSON. An ordinary
`err(...)` is data and can exit 0; it is not an OS failure signal. MCP `genia_run`
is source-only, no stdin/file/import authority and no main dispatch; it cannot
substitute for the subprocess/file/stdin tests. No new exit API is assumed.

Existing executable evidence selected for read-only verification:
`tests/unit/test_cli_args.py`, `test_json_representation_boundary.py`,
`test_json_stdlib.py`, `test_resource_io.py` (excluding ZIP), and
`tests/spec/test_parse_jsonl_record_shared_spec_389.py`. Exact command/results
are recorded in the publication handoff. This is a capability check, not a
benchmark trial or a competing solution. Do not claim a full runtime regression.

### Artifact homes

This single design/process record belongs in `.genia/process/`, following
AGENTS' rule that no process artifact lives in `docs/` after merge. No change to
the old #1226 report is necessary; it describes its dated evidence honestly.
Recommend a separate, non-authoritative experiment repository named
`genia-product-value-experiment` (proposed name, not created), with `design/`,
`public/`, `oracle/`, `runs/`, `reports/` and environment locks. It must say STATE
is Genia's authority. Benchmark applications, external comparisons, corpus and
oracle do not belong in this semantics repository. Hidden cases, change and
mutation keys remain in steward-only storage outside either public Git history
until evaluation closes. Each agent gets a separate export, not a shared repo.

## 1. Benchmark specification: CI-results JSONL, v1

### Interface and realistic scope

Each arm supplies an argv-vector launch recipe, called `RUN` here, using its
normal runtime, with exactly one input operand: `RUN PATH` or `RUN -` for stdin.
No operand/extra operand is a usage failure. No implicit discovery, globbing,
network access, environment config, multi-file concatenation, or stdout path
option. A real file named with spaces/Unicode is required; harness uses argv
arrays, never shell interpolation. A path beginning with `-` can be passed with
an explicit relative prefix. Native command prefixes may differ, task semantics
may not. Recipe contains no validation, parsing, aggregation, output decoding,
or result-dependent exit translation. No custom Python solution hidden behind
the Genia launch recipe. Existing documented host IO is allowed; domain logic
must be Genia. Pydantic arm must actually use Pydantic for record validation;
auxiliary CLI/JSON work can use stdlib. Stdlib arm has no third-party imports.

Input is a finite UTF-8 file/stream, at most 1 MiB and 1,000 physical lines;
each physical line at most 16 KiB; no line exceeds eight nested JSON containers.
LF and CRLF are equivalent separators. Last unterminated nonempty line counts;
a trailing separator creates no extra line. Zero bytes has zero lines. A lone
CR is ordinary line content, not a separator. Remove a CR only immediately
before a separating LF. Do not treat Unicode line/paragraph separators inside
JSON strings as physical record separators. Invalid UTF-8 is a fatal input
failure; BOM is not stripped (a BOM-containing record is invalid_json).

Numbers in corpus inputs have safe integer tokens within ±9007199254740991;
fractional or exponent-form tokens (including `1e0`) have at most six fractional digits, at most fifteen significant
digits and optional exponent -3..3, and magnitude within the safe range. These
limits bound the corpus domain, not additional validator rules. Required integer
fields still reject fractional/exponent spellings even if mathematically whole.
Outside-envelope resource/numeric inputs are unscored, not silently passing;
the steward checks envelope membership before freezing. These limits avoid
testing competing arbitrary-precision libraries rather than CI reporting.
Malformed syntax and NaN/Infinity spellings remain required negative cases.

### Parsing, validation and duplicate semantics

Process every physical line in source order; continue after recoverable errors.
Whitespace-only means only spaces, tabs and CR after separator removal: emit one
`blank_line` skipped diagnostic. Otherwise parse exactly one strict JSON value;
reject trailing data, duplicate object member names at any level, nonfinite
numbers, unescaped controls and unpaired surrogate escapes as `invalid_json`.
Valid JSON whose root is not an object produces `not_object`. Parse failures and
non-objects each yield one diagnostic, no field validation.

An object must contain the following required fields. Missing and explicit null
are distinct: missing -> `missing`; null -> `type`. No type coercion/defaults.
Ignore extra fields after JSON parsing; output only the three validated fields.
Ignoring evolving CI producer metadata is intentional, not a schema error.

| Field | Type | Valid values | Code after type success |
|---|---|---|---|
| suite | JSON string | at least one Unicode scalar; no trimming/case-folding/normalization | `value` for empty |
| status | JSON string | exactly `pass`, `fail`, `skip` | `value` for other string |
| duration_ms | JSON integer token, bool excluded | 0..86400000 inclusive | `value` outside range |

`0`, `-0` are integer tokens; `1.0`, `1e0`, true and "1" are not. All applicable
field diagnostics accumulate in the fixed order suite/status/duration_ms. For
each field, emit exactly one of missing/type/value or no diagnostic. Schema-invalid
objects do not participate in duplicate detection. A schema-valid suite already
accepted earlier produces one `duplicate_suite` diagnostic, field suite. First
accepted occurrence wins; invalid rows never reserve an identifier. Identifier
equality is exact Unicode scalar sequence, case-sensitive; composed/decomposed
forms and whitespace differences remain distinct. Duplicates are per invocation.

### Output, diagnostics and status

Completed processing writes exactly one raw JSON object to stdout, with no
prefix, debug echo, enclosing JSON-string layer or second document. Whitespace
and object-key order are not semantic; arrays are ordered. Success stderr must
be empty. No host exception text or input record is copied into recoverable
diagnostics. The exact top-level keys are `schema_version`, `accepted`,
`diagnostics`, `summary`; schema_version is the string `ci-results.v1`.

`accepted`: array of objects with exactly suite/status/duration_ms, in source
order. `diagnostics`: array of objects with exactly `line` (one-based physical
line), `field` (string), `code` (string). Use field `""` for blank_line,
invalid_json and not_object. All other fields are the field names above.
Diagnostic order: physical line ascending, then the fixed field order above;
parse/blank/non-object and duplicate diagnostics are exclusive for their rows.
No native Pydantic/Genia error wording is required; applications map to this
small, useful common vocabulary. Source location + field + code identify the
problem without copying entire potentially large records.

`summary` has exactly:

- `lines`: physical line count, `accepted`: accepted row count,
  `rejected`: count of nonblank rows with at least one error,
  `skipped`: blank-line count. Invariant lines = accepted + rejected + skipped.
- `by_status`: exactly pass/fail/skip integer counts over accepted rows, including
  zero counts; `total_duration_ms`: sum over accepted rows, including skip rows.
- `failing_suites`: accepted fail suite names in source order, not locale sort.

The summary uses integer arithmetic; maximum sum 86,400,000,000 remains safe.
Empty input has empty arrays, all counters zero and all three status keys zero.
No JSON null or optional field is needed in the v1 output. Actual input null is
still tested. A Genia `none("nil")` must never be normalized to JSON null or
treated as a missing output key. Outcome wrappers, symbols, `<map N>`, or pretty
debug maps are invalid wire output, regardless of apparent meaning.

| Process condition | Exit expectation | stdout | stderr |
|---|---|---|---|
| Completed, including rejected data / failed CI suites / blanks / empty input | exactly 0 | one valid complete document | empty |
| Missing/unreadable input, invalid UTF-8, invalid argv | ordinary nonzero 1..125 | empty | diagnostic category `ci-results: input` or `ci-results: usage` respectively |
| Signal, crash, watchdog kill, output overflow | recorded failure taxonomy | captured, never accepted as complete | captured |

The same nonzero predicate applies to all arms; exact raw statuses remain
recorded. Do not require a nonexistent Genia exit constructor or treat data-level
err as fatal. This is a reporting processor, not a CI pass/fail gate. Fatal stderr
must contain a line exactly `ci-results: input` for input failures or
`ci-results: usage` for argv failures, optionally followed by `: ` and useful
detail on that same line. Additional native diagnostics are allowed and recorded;
the required category is matched mechanically, never inferred from exception
wording. Applications may explicitly emit the category before their native
failure path. Normal complete documents are compared mechanically. Fatal
stream/read errors require no partial report; implementations may buffer this
bounded workload. Streaming memory complexity, broken-pipe semantics and Windows
support are documented operational observations, outside the v1 hard gate.

## 2. Corpus and independent oracle design

### Corpus partition and manifest (to be built only after approval)

Proposed immutable v1 inventory: 30 public and 60 hidden invocations, paired
across all arms. A case is one process execution, not one assertion or one row.
Public/hidden partition is fixed before implementation; hidden variants test
disclosed semantics only. Each manifest entry has case_id, partition, contract
clause IDs, input SHA-256/byte length, mode file/stdin, exact argv operands,
environment profile, expected document SHA-256 or fatal predicate, generator
version/seed if applicable, steward/reviewer identities and approval timestamp.
Each input is stored as bytes; expected document as strict JSON; fatal cases
store expected class, streams predicate and reproducible sandbox setup.
Output hashes use canonical oracle serialization only for artifact integrity;
candidate outputs are compared by semantic normalization below.

| Case family | Public | Hidden | Required coverage |
|---|---:|---:|---|
| Happy reporting and metadata | 4 | 8 | all statuses, ignored extras, accepted/fail ordering, integer sums |
| Malformed JSON and non-object roots | 5 | 10 | trailing text, truncation, duplicate keys, scalars/arrays/null, NaN/Infinity |
| Fields and accumulated diagnostics | 7 | 14 | each missing/type/value, bool vs int, fraction/exponent, null, mixed errors |
| Duplicate/state interactions | 3 | 8 | valid→valid, invalid→valid, valid→invalid, multiple invalid same suite |
| Unicode and line framing | 4 | 8 | emoji/CJK, escaped/literal equality, NFC/NFD difference, CRLF, U+2028, no final LF |
| Empty and boundaries | 4 | 6 | zero bytes, blank-only, zero/max duration, just outside, max lines/line/total sizes |
| Fatal CLI and input | 3 | 6 | missing operand/path, extra operand, directory/unreadable source, invalid UTF-8 |
| Total | 30 | 60 | file and stdin represented in every data family |

Case construction must include a valid file/stdin paired case in public and
hidden sets and three-repeat determinism checks on selected mixed, Unicode and
empty cases (repeats are operational checks, not inflated sample size). Nested
duplicate-key, reversed map insertion and field validation precedence are hidden
interactions. Do not reuse #1226's now-public change/corpus as concealed evidence.
Final exact cases/expected bytes are a Phase 2 deliverable, not claimed frozen
now. Freeze input bytes, expected outputs, generator seed/version, comparator,
launcher policy, design and environment images under a version/hash manifest.
No live CI/private data. Replacing a mistaken case requires a new version and
rescoring every arm; never repair the oracle to match one implementation.

### Oracle independence and normalization

An oracle steward who will not implement any arm constructs expected results
from section 1, before seeing candidate code. A distinct auditor hand-derives
every expected output and checks the manifest. Use a small language-independent
decision table/manual derivation as normative truth. A future comparator may
use an ordinary JSON library (including Python stdlib), but imports no candidate
modules, Genia evaluator, validation helpers, or Pydantic models. Oracle language
choice is not semantic independence by itself. A second JSON parser/independent
manual review cross-checks duplicate-key, Unicode and number-token fixtures.
Any disagreement blocks freeze until resolved in the written specification.

Comparator design: capture raw process bytes/status; require strict UTF-8 output;
parse the entire stdout as exactly one JSON document with duplicate-key and
nonfinite rejection; validate exact keys and JSON types (bool is not int), schema
version, integer counts and bounds. Compare recursive objects ignoring key
order/insignificant JSON whitespace and escaped-vs-literal Unicode spelling.
Compare arrays and scalar strings exactly, integers exactly; never coerce strings,
floats, booleans, missing keys or null. Do not sort arrays, trim string contents,
NFC-normalize Unicode, evaluate Genia expressions, unwrap JSON strings, or strip
Outcome constructors. Require the expected stream/status predicate separately.
Repeated candidate output must be semantically identical; also record raw byte
stability as an operational measure (not a whitespace-style preference).

Oracle tests planned for Phase 2: independently authored wrong-output examples
(dropped diagnostic, reordered accepted array, bool count, duplicate output key,
double-encoded JSON, debug none, wrong status, extra stdout) must fail; equivalent
key orders/escapes/pretty spacing must pass. Metamorphic checks complement fixed
goldens: file/stdin equivalence; CRLF/LF equivalence; ignored-metadata addition;
appending a blank changes only skipped/lines and its diagnostic; distinct valid
row changes only expected counts/sum/order; permutations affect first-wins and
source order as specified. These properties are not substitutes for goldens.

No agent self-grade establishes correctness. Public checks are available locally;
hidden grader gives no results or case-level feedback until a phase's final
snapshot is immutable. First public-pass time is provisional; independently
verified completion time is defined in section 4. One final hidden submission
per phase prevents hill climbing. An oracle dispute is decided by the auditor
against the frozen spec, applied uniformly, and logged with all old results.

## 3. Agent execution, fresh handoffs and concealment

### Roles, environment and tools

Primary assignments requested: isolated Claude Code → Genia/Python reference host;
Codex → Python stdlib; separate Claude Code session → Python+Pydantic. These
three alone confound model with arm; label them a feasibility pilot. Designers,
oracle stewards and anyone who saw hidden artifacts cannot implement or perform
blind maintenance/repair. Use a separate human execution operator and independent
auditor. No coaching, shared chat, candidate cross-access or shared writable home.

Proposed common platform: Linux x86_64, UTF-8 locale, UTC, two vCPU, 4 GiB per
worker, same filesystem and CPU allocation, one worker at a time or isolated
dedicated resources. Pin exact Python version, Genia SHA, Pydantic v2 wheel and
transitive dependency hashes, agent CLI builds, model identifiers/reasoning
settings, image digest, OS/kernel and documentation snapshot hashes. Exact
versions must be resolved by the operator before freeze; no invented model
availability/version claim. Provision runtimes before the timed task; measure
cold install/dependency setup separately from implementation effort. Each graded
invocation: 60 s wall watchdog, 4 GiB memory, 16 MiB each stdout/stderr cap; these
are safety bounds, not a speed competition. Preflight native launch and inputs
on all arms before task exposure. Capability failures stay outcomes, not repairs
to Genia during a trial.

Primary tool policy: identical shell/editor/file access and local public-test
runner; network off, no MCP for any arm, no web/search/repository issue history,
no unrelated repos/global memories. This measures CLI-assisted development;
Genia's documented CLI fallback makes MCP absence an explicit stratum, not a
language limitation. An optional separately preregistered tooling stratum can
enable Genia's four documented MCP tools and equivalent Python execution tools;
never pool it into the primary comparison. MCP cannot replace real CLI tests.

Each arm receives the SAME application contract (section 1 without design,
history, scores, future change or mutation details), public cases/check command,
output schema, resource/time limits, dependency policy, submission format and
neutral instructions. Also provide complete accurate versioned language docs:
Genia source-of-truth chain, function reference, tested examples and local help;
Python stdlib/language docs; Pydantic arm additionally its pinned API docs. These
are language-appropriate resources, not equal page counts. No tailored solution
outline, earlier prototype, oracle code or handpicked trick is included. Record
doc searches/reads and first successful use; do not give Genia private tutoring.
Use a documentation export allowlist, not a clone containing design/issue/annex
history. Genia runtime source needed for installation may be executable but
design/hidden artifacts must be absent from every readable filesystem.

### Prompt and time sequence

Initial prompt template (arm substitution only): “Implement ci-results.v1 using
[ARM] and the supplied contract/public acceptance cases. Use only permitted
dependencies/tools. Do not modify the runtime or tests supplied by the operator.
Keep your own tests separate. Return source, exact argv launch recipe, dependency
manifest, concise usage and any incomplete requirements. Public tests do not
constitute independent final approval. Stop when submitting or when budget ends.”

Each initial attempt: 120 active wall minutes, 180 elapsed minutes hard cap and
80,000 model input+output tokens as a second cap (cache usage recorded separately,
same counting rule across clients). Stop at the first exhausted cap; no automatic
extensions. Reading docs, tool waits and local verification count toward active
time. Active time is elapsed task time minus only operator-confirmed provider or
infrastructure outages; report raw elapsed alongside it. No human coding help.
Clarification requests go to the operator; substantive answers become neutral
numbered errata delivered to all arms at the same stage. Log receipt and downtime.

At submission freeze source SHA, launch recipe, dependency hashes, local tests,
transcript/event log and the agent's explicit incompleteness statement. The
independent grader evaluates hidden cases after snapshots close. Keep every
attempt, including empty/incomplete ones. Agents cannot resubmit after hidden
feedback. The initial mandatory three sessions are one block; no inference from
one Genia-vs-Python observation alone.

### Maintenance and diagnosis sequence

1. Grade initial snapshots. Only independently correct snapshots enter the
   primary maintenance comparison. If one arm fails, report end-to-end attrition;
   do not silently replace it with an expert solution. Conditional maintenance
   results must say “among successful initial attempts.” A separate seeded-code
   study would need its own approval and may not be pooled.
2. Fresh agents, no original author or chat, receive only another author's frozen
   source, launch docs, base contract and public tests. Before any change reveal,
   take 20 minutes to explain validation order, duplicates, line numbering,
   reporting and error status, with predicted behavior for operator-specified
   public examples. Grade against an answer key made by the independent auditor.
3. Reveal the identical concealed requirement and its public acceptance cases to
   every maintenance agent simultaneously (or by isolated scheduled blocks).
   Budget: 60 active minutes, 90 elapsed, 40,000 tokens, same stop rules. Grade all
   original and change cases; freeze independent correctness/regressions.
4. For every verified changed snapshot, steward creates two independent mutant
   forks, each with one semantically comparable defect; no combined defect.
   Prove each mutation's failing signature and unrelated passing cases; auditor
   signs comparability. Different fresh agents get the full changed contract,
   public tests and one symptom, but neither clean source nor private diff.
   Budget per defect: 45 active minutes, 60 elapsed, 30,000 tokens. Require a
   causal explanation before editing; timestamp diagnosis and final repair.
   Grade the full original+change suite, including the specific defect cases.
5. Freeze all results before revealing hidden cases, mutations or other arms.

The steward-only change/defect design is committed by SHA-256:
`929984f1bbba850de61a1c978149862c70e455c97eba25e93c742ec10cbd4055`.
Owner receives the separate annex; it is not committed to this public PR.
Restricted-storage transfer, access attestation and independent approval are
required before trials. This commitment freezes the design text, not nonexistent
fixtures. A fresh operator must certify exported workspaces cannot read this
conversation or the annex. A suspected leak quarantines the matched block and
is reported; never “unsee” a leaked requirement. Even maintenance agents do not
see the defect key. Publish the annex only after all trial outcomes are sealed.

### Replication and model rotation

Pilot is for feasibility and instrumentation, never a positive adoption claim.
Confirmatory proposal after separate approval: six blocks, each containing all
three arms, each fresh session and fixed independent sampling seed where exposed.
Three blocks assign Codex to Genia/Pydantic and Claude to stdlib; three assign
Claude to Genia/Pydantic and Codex to stdlib, so each arm has three sessions per
model. Randomize execution order within blocks and keep hidden corpus fixed.
Use fresh operators/agents for maintenance and repair, balanced 3/3 models per
arm and no same-author handoff. Eighteen initial sessions are still a small,
correlated sample. Same model version/settings remain pinned; an unavailable
model creates missing blocks, not an unrecorded substitution. Do not count cases,
tool calls, multiple slices or repeats as independent language trials.

## 4. Measurement rubric, stopping rules and decision policy

No weighted score can trade correctness away. Publish a vector of outcomes for
each arm and model stratum. Every measure has run_id, phase, snapshot, units,
collection source and missingness code. Operator logs monotonic start/end,
tool-call start/result, command exit class, edits and submission checkpoints;
provider usage exports are the cost authority. Retain sanitized transcripts with
restricted access until final release; no credentials or private/live CI inputs.

| Dimension | Objective definition and collection | Decision use |
|---|---|---|
| Correctness | Invocation pass = exact expected normalized document AND stream/status predicate; final gate = 100% public+hidden required cases, no timeout/crash, three-repeat semantic determinism | Hard gate per phase; report passed/total and family breakdown, never average away CLI failure |
| Initial productivity | For a correct FINAL submission, time from task delivery to earliest immutable checkpoint that later passes ALL public+hidden cases; operator independently replays timestamped source/recipe/dependency checkpoints after closing runs, with no feedback to agents | Primary effort endpoint; incorrect final submission -> no completion, right-censored at actual stop (at most budget), even if an earlier checkpoint passed; report that transient event descriptively and completion probability too |
| AI reliability | Failed execution = agent-initiated command intended to parse/run/test candidate that returns failure; classify syntax/API misuse, test assertion, wrong output, launch/dependency, infrastructure. Repair cycle = edit after an observed candidate failure followed by another verification command | Count commands and cycles separately; deliberate negative tests labeled and reported separately, not charged as unintended failure |
| Agent cost | Actual input/output/cached tokens, tool-call count by type, provider-reported billed units; estimate USD using archived dated per-model rates, include all repair/failed calls; record local compute separately if measured | Secondary; no price/token equivalence assumption; missing provider export is unknown, not zero |
| Maintainability | Fresh-agent comprehension score; active time to independently verified changed snapshot; old-case regressions; causal diagnosis time and repair time per mutation; new regression count | Full correctness gate on original+changed behavior, per-defect reporting; never count only patched symptom |
| Human comprehension | Six human reviewers, proficiency recorded; 20-minute review per arm split into 10-minute behavior and 10-minute defect tasks, six behavior points plus five defect points as specified below; answer key established before review | Record time and correct answers/11; balanced six-order assignment, anonymized labels/style, no author coaching; reviewer and code-source correlations retained |
| Operational usefulness | Clean install replay, file/stdin/path handling, exact stream/status checks, dependency count/pins/install minutes, reproducible launch, documented portability and diagnostic localization; error report identifies line/field/code for all expected data faults | Required CLI is hard-gated; dependency/setup/platform costs reported separately; unsupported platform is unsupported, not pass |

Human assignment is fixed by block identity before outcomes. Number reviewers
and confirmatory blocks 1..6. Reviewer r receives the clean initial source from
block r for each arm for the behavior task, and a changed mutant from block
(r mod 6)+1 for that arm for the defect task. Odd reviewers receive D1, even D2;
thus every arm has six clean-source reviews and three of each defect. If a
required source/mutant is absent, that cell is missing; do not choose a successful
replacement after seeing outcomes. Arm orders are the six permutations
G/S/P, G/P/S, S/G/P, S/P/G, P/G/S, P/S/G, assigned to reviewers 1..6; finish
the three clean tasks, then the three mutant tasks in reverse arm order. At most
one task session per reviewer per day; source IDs anonymous, no communication
between reviewers until all responses freeze. No reviewer sees clean and mutant
forms of the same source lineage.

Each behavior question is worth one point for exact behavior: (1) physical-line
and blank counting; (2) integer/bool/null distinction; (3) accumulated field-error
order; (4) invalid-first versus accepted-first duplicate handling; (5) report
counts/sum/failing-suite order; (6) completed-data versus fatal exit/stream
behavior. Operator supplies a concrete public example for each, identical across
arms. Five defect points, one each: causal source location; triggering input;
incorrect state/predicate mechanism; minimal semantically correct repair;
regression case protecting unaffected behavior. Auditor prepares exact answer
keys per frozen source before human exposure. Two independent scorers adjudicate
disagreements without language advocacy; retain both original scores.

Human review uses separate frozen clean/mutant exports, no agent transcript,
language advocacy or mutation labels. Review language cannot be blinded; record
familiarity and stratify novice/experienced.
AI comprehension is a separate endpoint, never a substitute for human data.
If humans are unavailable, label that dimension unmeasured and withhold any
human–AI comprehension/value conclusion. No line-count/readability vote is used
as an effort proxy. LOC may be descriptive only.

Instrumentation checkpoints: archive code/tree plus recipe/dependency state
after each verification command and final submission (automatic read-only
snapshot outside agent workspace); log paused-time categories. Post-hoc replay
of earlier checkpoints uses only the frozen oracle/environment, starts from a
clean filesystem and cannot alter outcome or coach the agent. If checkpoints
are missing, earliest verified time is unknown; final-submission verification
still determines completion. Report operator grading/review minutes separately
and end-to-end total labor using this per-arm a, per-block b formula:
`L[a,b] = I + C + M + D1 + D2 + Hclean + Hmutant + O_specific + O_shared/3`.
I = initial verified effort, C = fresh-agent comprehension, M = requirement
change, D1/D2 = the two independent diagnosis+repair efforts. Each phase's effort
is actual active time through final submission, including work after an earlier
passing checkpoint. The phase qualifies as verified only when its final
submission passes; otherwise L is censored/incomplete, not an invented number.
Earliest verified checkpoint time is a separate productivity measure. Hclean/Hmutant are
actual reviewer minutes assigned to that source block (not reviewer identity),
including rubric scoring and adjudication. O_specific includes candidate-specific
verification, launch support and review; O_shared includes that block's shared
operator/grading administration. Count actual agent/human active minutes, not
the phase caps. Any coding assistance is both recorded and a protocol violation,
not silently credited as unaided productivity. Common oracle/environment setup
labor is reported once and also amortized equally over the 18 confirmatory
arm-runs in a separate total-cost sensitivity analysis. Pilot costs stay separate.
Sum person/agent minutes even when work overlaps, but report elapsed wall time
separately; do not sum overlapping wall intervals as elapsed time.

Outcome taxonomy: completed_correct; completed_incorrect; incomplete_budget;
timeout; crash; dependency_or_launch_failure; infrastructure_invalid;
protocol_or_leakage_invalid; measurement_missing. Record case-level and run-level
outcomes separately. Agent-introduced dependency/launch errors count against the
arm. Operator-provisioned environment/provider outages invalidate the entire
matched block for confirmatory inference: retain data and allow one whole-block
replacement with a fresh seed/session, preregistered before outcomes. A second
infrastructure-invalid block stops for repair/approval; no selective language-only
reruns. Runtime capability gaps count as inability to complete the task, not as
operator outages. Optional measurements missing -> NA with reason; no imputation
or invented zeroes. Wrong output is a failure even if the agent calls it complete.

Stopping: pilot one triple only; confirmatory six planned blocks only if approved;
each task stops at submission or first time/token cap; no stop-when-Genia-wins.
Report completion proportions with exact binomial intervals, paired block-level
effort differences and bootstrap intervals over whole blocks (not individual
cases), plus raw tables. For each baseline B separately, the paired labor
statistic is median over b of `L[G,b]/L[B,b]`, not ratio of marginal medians.
Use 10,000 bootstrap draws, Python `random.Random(20261025)` (MT19937, analysis
Python version pinned), resampling with `randrange(3)` three whole blocks
with replacement within each of the two assignment strata, combining the six
sampled blocks per draw; report the 2.5th/97.5th percentiles of that statistic
using linear interpolation between adjacent sorted draws at index (n-1)*p.
If any required L is missing/censored, no confirmatory ratio interval or ADOPT
claim is available; report available pairs descriptively plus completion and
censoring. Cost and human review-time ratios use the same paired median rule
against EACH baseline, with full phase costs and Hclean+Hmutant time respectively.
Human score comparison uses the median paired score difference against EACH
baseline. Noncompletion is censored, not a zero-time success or
an invented completion at cap. Include time-to-completion curves and a sensitivity
table charging the cap to incomplete attempts, clearly a bounded-loss metric.
Compare Genia separately to each Python baseline, by model as well as pooled;
intervals with six blocks are exploratory and not population guarantees.

Proposed practical decision thresholds, frozen BEFORE execution:

- **ADOPT for this workload** only if Genia passes every required case in all
  six initial, changed and repair runs per scenario; no lower observed completion
  rate than either baseline; median paired total verified labor at least 20%
  below EACH Python baseline (paired median ratio <=0.8), with block-resampling
  95% interval for each labor ratio wholly below 1; median paired human score
  difference >=0 against EACH baseline, review-time paired median ratio <=1.1
  against EACH baseline; full-agent-cost paired median ratio <=1.1 against EACH
  baseline; no operational
  blocker. Primary gain must have same direction in both model strata. Evaluate
  ratios only for verified matched pairs and also the full completion/censored
  analysis; survivor-only ratios cannot establish ADOPT.
- **DO NOT ADOPT for this workload** if both Python arms complete correctly in
  every block while Genia fails correctness/completion in at least two blocks,
  or Genia shows no >=20% labor gain against either baseline and is >=20% worse
  on labor or cost against both, with comparable completion. State whether the
  cause is host integration, discovery, model interaction or application logic.
- **REVISE / INCONCLUSIVE** otherwise, including missing human/cost evidence,
  invalid blocks, conflicting strata, missing matched maintenance trials, mixed
  baselines or wide intervals. Missing power is not evidence of equivalence.

These practical thresholds are owner-reviewable design choices, not existing
results or universal scientific cutoffs. No single aggregated winner score.
Report negative outcomes and tradeoffs even if a decision criterion is met.

## 5. Skeptical threats-to-validity review

| Threat | Control in this design | Remaining qualification |
|---|---|---|
| Selection bias | Real CI record validation, no arbitrary new feature demand, same schema/status/CLI for all; ignore ordinary metadata; independent review of requirements | Chosen killer workflow can favor Genia; one workload cannot establish general preference |
| Model capability/version | Fixed identities/settings, requested pilot labeled confounded, balanced six-block rotation, stratum results | Different clients/reasoning budgets and stochastic service drift remain |
| Prior Python familiarity | Fresh sessions, same docs access, record searches and hallucinated APIs; equal time policy | Training data exposure and human language proficiency cannot be equalized |
| Genia discoverability | Accurate complete local docs/help, no coaching; measure discovery effort, distinguish missing capability | Providing curated correct snapshots improves over uncontrolled real-world search; report that scope |
| MCP/tool access | Primary CLI-only policy for all; optional separate supported-tool stratum | CLI result does not generalize to an MCP-enabled workflow |
| Runtime/host differences | Same hardware/input/task, native launches, explicit host pin, install cost separate | Genia on Python vs Python is a platform/toolchain comparison; runtime overhead remains part of usefulness |
| Oracle coupling/error | Steward separate from competitors, independent goldens, second parser/manual audit, wrong-output checks and metamorphic review | Stewards can share conceptual mistakes; version changes and uniform rescore required |
| Hidden leakage | Restricted storage, no public annex/history, allowlisted exports/network off, access attestations, staged reveal | Designer/reviewer excluded from trials; any plausible leak invalidates block |
| Self-grading | Immutable submissions, independent grader, hidden feedback withheld | Public-pass behavior can optimize visible cases; hidden suite remains finite |
| Human bias | Anonymous labels, answer key, Latin-square order, proficiency strata, no authored-code review | Language syntax cannot be blinded; six humans is small and learning effects remain |
| Small/correlated samples | Unit = independently started session/block, exact intervals/raw data, no case-as-trial inflation | One pilot or six blocks has weak power; REVISE may be the only defensible result |
| Instrumentation overhead | Same event logger/checkpoint frequency, clock calibration and no-op overhead measured before trials, background capture outside workspace | Clients expose different token/tool events; timing includes waits and must be reported honestly |
| Maintenance selection | Record initial attrition and conditional results; no expert rescue in primary data | Maintenance sample may select easiest successful code; absent arms prevent end-to-end claim |
| Mutation equivalence | Single semantic defect per fork, private failing signature, independent comparability audit, separate times | A one-character bug can be easier in one code structure; number of edited lines is not equality |
| Time/cost thresholds | Preregister caps/rates/thresholds and all failures; no repeated hidden submissions | Proposed caps may be too tight/loose; pilot calibration changes require a new frozen protocol |

The experiment can disprove utility: Python can pass when Genia cannot, complete
faster with fewer repairs, cost less, or be better understood. A correctness-only
Genia success recreates #1226 feasibility, not a value demonstration. Before
oracle construction, a reviewer must try to construct cases that violate the
written rules or expose ambiguity; before adoption, a distinct auditor must
reproduce grading from raw bytes/process facts and challenge the verdict.

## 6. Subsequent phases, decisions, effort and acceptance trace

### Approval gates and dependencies

| Stage | Work after explicit approval | Exit evidence and stop |
|---|---|---|
| Phase 1 (this PR) | Design package and skeptical review only | Owner accepts/revises contract, rubric, isolation, annex and placement; stop before fixtures/oracle |
| Phase 2 | External experiment workspace; construct public/hidden fixtures, goldens/comparator and environment locks; no competing solution | Independent oracle audit, envelope/coverage checks, wrong-output rejection, hashes/access receipt; owner separately approves challenge exposure |
| Phase 3 | One isolated requested-assignment pilot triple | Immutable provenance, all failures, instrumentation audit; no adoption verdict; owner approves protocol revision or six-block replication |
| Phase 4 | Confirmatory initial blocks, fresh comprehension/change/repair and human review | Frozen outcomes, no hidden hints, stage-specific correctness, complete measurement table |
| Phase 5 | Independent replay/skeptical audit and evidence report | ADOPT/REVISE/DO NOT ADOPT for this workload; publish annex/corpus after closure, report qualifications; any language work needs separate normal gates |

No merge, fixture generation, oracle code, solution, runtime repair, CI edit or
new feature issue is implied by a draft PR. Future experiment gates apply to
this study only. Existing R33 discovery/tooling and R39 policy-tooling directions
are possible evidence destinations, not new tickets or expansion authorizations.

Estimated PLANNING effort, not observed performance: oracle/corpus and double
review 2–4 person-days; environment/isolation/logging 1–2; pilot operation and
review 1–2; replication, maintenance/repair and human coordination 3–5; audit
and report 1–2. Total 8–15 person-days, plus model runtime. Per complete block,
agent active caps sum to 3 × (120 + 20 + 60 + 2×45) = 870 min = 14.5 hours;
pilot plus six confirmatory blocks up to 101.5 aggregate agent hours if all
qualify for downstream phases (elapsed caps may be higher). Six reviewers ×
three 20-minute sessions = six human review hours, excluding setup/adjudication.
Tokens/cost are unknown until exact models/rates and observed usage exist.

### Unresolved decisions and assumptions

- Owner approves this precise workload/domain, fatal-status predicate, ignored
  metadata and practical 20%/10% decision thresholds. These are proposed choices.
- External repository/storage owner, second hidden-data custodian and actual
  independent oracle auditor are not appointed. No restricted transfer receipt
  exists yet; no implementation exposure may begin without one.
- Exact Python/Pydantic/model/client versions, available model rotation and
  stable hardware/image hashes must be pinned before oracle freeze. Design
  publication does not claim availability of future Claude/Codex sessions.
- Six human participants, proficiency balance and reviewer payment/time are
  unconfirmed. Without them the human comprehension endpoint stays unmeasured.
- Original #1226 downloadable source/corpus unavailable for byte-level audit;
  reported numbers above remain reported historical evidence only.
- Independent review findings and documentation verification are appended below;
  owner approval is a separate action. No experiment result is available.

### #1285 acceptance criteria trace

| Issue criterion | Phase 1 disposition / evidence | Deferred evidence |
|---|---|---|
| Frozen reviewable design, oracle/fixture schema, rubric, independent audit | Sections 1–5 and steward hash; revision becomes frozen only on acceptance | Phase 2 actual bytes, schema files and approved oracle |
| Same contract/tests, hidden adversarial cases, normalization | Sections 1–2; expected behavior independent of every arm | Frozen public/hidden cases and comparator audit |
| Real CLI/file/stdin, unsupported honest | Interface/status contract, paired cases, capability evidence | Every candidate's real subprocess evidence |
| Independent implementations and cross-agent change/repair | Section 3 with role exclusions, staged handoffs and secret commitment | Phases 3–4 runs and comparability review |
| Correctness/effort/review/operational measures | Section 4 definitions, missingness and hard gates | Measured results; no claim today |
| Independent oracle/no leaks/self-grading | Sections 2–3 and separate steward annex | Custodian receipt, access attestation and audit |
| Balanced verdict with negatives/existing roadmap homes | Section 4 preregistered policy, section 5 falsification and section 6 boundaries | Phase 5 evidence-based product verdict |
| No semantic/release/CI/agent-policy changes | Single process record; source authorities unchanged | Continue scope checks each approved stage |
| Accurate docs, STATE authority | Explicit proposal/host labels, pinned sources and historical limitations | Update external experiment docs after each approved phase |

The experiment-wide execution criteria are intentionally NOT checked complete by
a design-only task. Recommendation: **GO for independently reviewed oracle
construction only after owner approval**, subject to resolving Phase 2 ownership
and environment pins. **NO-GO for competing implementations or trial exposure**
until the oracle/access-control gate passes. Single next action: owner review
and explicit approval (or revision) of this design and private steward annex.

## 7. Design review and verification handoff

Independent reviewer: separate agent `/root/skeptical_design_review`, not the
design author; reviewed the public design, private annex, task request and AGENTS.
Initial verdict REVISE: concealed change reused prior public evidence; human
assignment/scoring needed precision; total-labor attribution and baseline
comparisons needed exact definitions. Smaller findings concerned oracle
disagreement wording, fatal-category subjectivity, exponent-token scope and
transient-checkpoint versus final correctness. Revisions replaced the concealed
change, pinned human source allocation/11-point scoring, defined labor and
stratified bootstrap statistics, and resolved all smaller findings. No private
change or mutation details are disclosed in this public review summary.

Final independent verdict: **GO for oracle construction after explicit owner
approval**, no remaining blocking design finding; **NO-GO for implementation or
trial exposure** until separate oracle/access approval. Reviewer confirmed the
private annex hash and absence of the obsolete hash. Qualifications: small
sample, CLI-only scope, unappointed custodians/humans, unpinned exact environment
and models, and no constructed/audited oracle. The reviewer edited nothing and
ran no fixtures, solutions or experimental tests. This is an independent design
review, not owner approval, runtime certification or a result of the experiment.

Verification on the matching baseline checkout:

```
UV_CACHE_DIR=/workspace/work/uv-cache uv run --no-sync pytest -q \
  tests/unit/test_cli_args.py \
  tests/unit/test_json_representation_boundary.py \
  tests/unit/test_json_stdlib.py \
  tests/spec/test_parse_jsonl_record_shared_spec_389.py \
  tests/unit/test_resource_io.py -k 'not zip'
```

Result: **115 passed in 3.78s**. Existing capability evidence only; no new tests
or benchmark cases. Ordinary uv sync initially failed on a read-only default
cache and then unavailable package-network access; the successful command used
the pre-existing locked environment without synchronization. No dependency or
runtime source was changed. This does not certify a fresh install or complete
benchmark composition.

Static design checks passed: ten relative file links resolve; private annex
SHA-256 matches the public commitment; obsolete commitment absent; proposed
public/hidden allocation totals 30/60; sections 0–7 present. Existing manifest
contains every capability name cited in the pre-flight. Staged `git diff --check`
passes. Scope review: exactly this new process Markdown file in the repository;
no implemented-truth, spec, CI, runtime, MCP or release files changed. No full
regression, strict site build, experiment result or oracle validation is claimed;
this process record is outside the published documentation site.

Publication authorization (2026-10-26): the owner explicitly approved publishing
only this public design as a draft PR targeting `m0smith/genia-2026:main` and
posting the public issue #1285 summary, after inspecting the exact payload.
The earlier automatic upload rejection prompted this explicit authorization;
it does not authorize fixtures, oracle construction or implementations. The
private annex remains separately preserved outside Git and is not part of the
upload. The public design contains only the commitment to that annex, not its
concealed requirement, mutation instructions or any hidden fixture contents.
Publication URLs and remote payload/scope verification belong in the PR/issue
handoff after publication; no later experimental phase has begun.
