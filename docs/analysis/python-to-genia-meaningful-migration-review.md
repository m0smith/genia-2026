# Python → Genia: Meaningful Migration Review

Status: **Analysis and planning only — non-authoritative.** Reviewed 2026-10-02
against `main` at `415ecc9` (R28 in progress; R39 planned, not active).
`GENIA_STATE.md` remains final authority for implemented behavior. Nothing
here implements, approves, or schedules behavior; every "should" below is a
recommendation that still needs the repository's pre-flight / contract /
design / failing-test / implementation / documentation / audit gates.

This review supersedes none of the historical inputs. It treats
`docs/analysis/python-code-reduction-review.md`,
`docs/strategy/r23-python-reduction-release.md`, and
`docs/analysis/r28-host-dependency-inventory.md` as non-authoritative and
re-checks their claims against the current tree (section 3.8).

## 0. Evidence basis and limits

Read in full: `docs/strategy/roadmap/{r39,sequence}.md`,
`docs/strategy/{release-roadmap,killer-workflow}.md`,
`docs/process/08-roadmap-ticketing.md`, `docs/strategy/r23-python-reduction-release.md`,
`docs/analysis/python-code-reduction-review.md`, `tools/spec_runner/{runner,comparator,capabilities,evidence,executor,host_executor,host_parity_gate,revision,reporter}.py`,
`tools/publish_wiki.sh`, and `hosts/python/AGENTS.md`.

Read in part (head plus targeted search of the rest): `tools/spec_runner/{loader,protocol}.py`,
`tools/{gen_function_docs,lint_doc,validate_llm_instructions,stage_docs_for_mkdocs}.py`,
`apps/mcp/mcp.genia`, `hosts/python/mcp_*.py`, and the Python-bearing steps of
`.github/workflows/*.yml`.

Read by section/targeted search rather than end to end (they are 900–6,500
lines each): `AGENTS.md`, `GENIA_STATE.md` (shared-conformance §1,
native-test boundaries §9, resource/file/JSON bridges, §9.40
`execution.process`, §9.41–9.42 MCP), `GENIA_RULES.md`, `GENIA_REPL_README.md`,
`README.md`, `docs/analysis/r28-host-dependency-inventory.md` (entries
H01–H07 in detail), `docs/architecture/{host-capability-taxonomy,external-process-execution}.md`,
`docs/strategy/roadmap/{r35-r37,r42,r30-r32,parking-lot,multi-host-conformance-policy}.md`,
and `docs/host-interop/capabilities.md`. Claims below that depend on unread
text are marked **unverified**.

Facts established by running code or counting files in this checkout:

- Loadable shared specs: 793 YAML files (`eval` 426, `error` 163, `flow` 59,
  `cli` 57, `ir` 46, `parse` 42). `spec/_holding/` (14) and `spec/flows/` (2)
  are not in `SPEC_CATEGORIES` and are not executed.
- `tools/spec_runner/*.py` is about 2,000 lines; `host_parity_gate.py` is 285.
- `tests/unit/` has 248 test files; `tests/spec/` 35; `tests/doc/` 22;
  `tests/native/` 15 native Genia test files.
- A heuristic import scan found 58 of the 248 unit files import only the
  top-level `genia` API (`make_global_env`/`run_source`) and no host, tool, or
  subprocess/threading/socket machinery; 152 import internals or host/tool
  code; 38 do neither. This is a *candidate pool for audit*, not a migration
  list: many of the 58 assert Python value types (`is True`,
  `format_debug`) and some already have shared-spec twins.
- Genia `json_encode` and Python `json.dumps(sort_keys=True, indent=2)` agree
  structurally on ASCII data but differ on non-ASCII (`é` versus `é`) and
  trailing newline (Python's encoder appends one). The current evidence documents are ASCII, so this has not
  bitten, but it is a concrete byte-parity hazard for any dual-run evidence
  comparison (section 3.1).
- Genia has no documented way for a program to set the process exit status;
  a returned `err(...)` exits 0 (`GENIA_STATE.md` Outcome section). A Genia
  gate therefore needs a host-edge mapping from report to exit status
  (section 3.2).

## 1. Executive conclusion

**Where Genia should replace Python.** Portable policy over structured data:
shared-spec envelope validation, capability applicability/filtering, expected
vs actual comparison, outcome classification, aggregation, deterministic
evidence and report construction, host-parity and known-gap policy, and
(later) documentation-metadata normalization/validation/grouping/rendering
and lint policy. The best proving cases are conformance specs, parity
evidence, release evidence, and documentation metadata, because each is a
real instance of the killer workflow: external records → parse → validate →
transform/filter → classify Outcome → aggregate → deterministic
output/diagnostics.

**Where Python should remain.** Everything that implements Genia itself
(lexer, parser, lowering, evaluator, runtime values, Python host adapter
internals), every privileged capability and OS mechanic (filesystem provider,
process launch/kill/reap, sockets/HTTP transport, clocks, Git revision
lookup), external-protocol adapters (E16-1 adapter process, Jupyter wire
protocol, MCP launch/bootstrap), and a deliberately small independent Python
conformance runner that can referee the Genia runner.

**Governing rule.**

> Genia owns portable policy, composition, validation, transformation,
> orchestration, comparison, aggregation, and reporting. Hosts own privileged
> capabilities, bootstrap, OS integration, external-protocol adapters, and the
> machinery required to implement Genia itself. Policy functions consume
> ordinary Genia values; the host edge supplies those values. A migration is
> justified by the policy it moves, never by the Python lines it removes.

The intended end state is a narrow, explicit Python reference host providing
capabilities to a project whose portable tooling is increasingly Genia — not
"no Python".

**Headline findings.**

1. `tools/spec_runner/host_parity_gate.py` should become part of the
   Genia-native R39 orchestration, and it is the best *first* R39 policy slice
   (pure, small, already differential-testable). R39 did not name it; this
   review's PR makes that explicit (section 9).
2. R39 remains the main migration release. No new release is needed. The
   pure-policy slices of R39 are separable from its I/O edges; that is the
   only structural nuance worth recording.
3. The old Python-reduction analysis is mostly stale or mis-framed. Genia
   wrappers over host primitives already landed for `cli_*`, `sum`, file, zip
   read/write, and web helpers, and that is the correct shape; the remaining
   "move to Genia" items either regress diagnostics (`sum`) or have negligible
   payoff (`entry_json`, `update_entry_bytes`).
4. The documentation tools split cleanly into host-side metadata acquisition
   and file writing versus portable normalization/rendering/lint policy, but
   moving them before R33 introspection and R35 storage would force one-off
   APIs or a regex re-implementation of source scanning.
5. The independent Python oracle is load-bearing. A Genia runner that runs on
   the Python host and judges the Python host shares failure modes with it; the
   oracle plus a negative-fixture corpus is what breaks that loop.

### Classification used throughout

| Class | Question | Default |
|---|---|---|
| A | Implements Genia itself? | KEEP IN HOST |
| B | Decides on portable Genia-domain data? | STRONG CANDIDATE → GENIA |
| C | Python only because a capability boundary is missing? | DO NOT add a one-off API; wait for the proper release |
| D | External tooling/protocol plumbing? | KEEP host mechanics; move only policy above them |

## 2. Inventory

Suitability is for *Genia ownership of the portable part*; "No" means the
host should keep it. Payoff and risk are technical, not ranked politically.

### 2.1 Shared spec runner and conformance tooling

| Artifact | Python responsibility today | Portable policy or host mechanic? | Suitability | Recommended disposition | Prerequisite | Payoff | Risk | Roadmap home |
|---|---|---|---|---|---|---|---|---|
| `spec_runner/loader.py` — validation half (most of its 436 lines: allowed top-level/input/expected keys per category, `requires` uniqueness/vocabulary, fixture allow-list, flow-terminal check, module-path normalization) | Reject malformed spec envelopes with messages | **Portable policy** (B) | **High** | MOVE to Genia as envelope validation over decoded spec values | Genia YAML profile parser (R39) *or* pre-decoded JSON fixtures for shadow work | High — canonical Outcome-aware validation of messy external records | Low–Med: diagnostic text must match for dual-run | R39 (E39-3) |
| `loader.py` — acquisition half (`yaml.safe_load`, Ruby YAML fallback via subprocess, `glob("*.yaml")`, `read_text`) | Bytes and YAML parsing | Host mechanic (C/D) | Low | KEEP in host for the oracle; Genia gets YAML via R39's own parser and bytes via R35 | R35 Store/Location; R39 YAML parser | — | Ambient filesystem if done early | R35 → R39 (E39-2, E39-4) |
| `comparator.py` (53 lines) | Field-wise compare, parse substring rule, IR equality | **Portable policy** (B) | **High** | MOVE; equality must use R18 portable equality | R18 ✓ | Med | Low | R39 (E39-7) |
| `capabilities.py` (vocabulary load, claim validation, `case_is_applicable`) | Applicability: empty `requires` → applicable; otherwise every name exactly `supported` | **Portable policy** (B); manifest *read* is host | **High** | MOVE the decision; manifest arrives as a value | R35 for reading `spec/manifest.json` | High — exact applicability semantics are the heart of R16 | Low | R39 (E39-5) |
| `host_executor.py` — request construction, `_cli_argv`, category→operation map, line-ending normalization, outcome→`ActualResult`, classification | Maps a spec to an E16-1 request and classifies the result | Mostly **portable policy**; the invocation call is host | **High** (policy) / Medium (invoke) | SPLIT: policy → Genia; invocation → approved execution boundary | `execution.process` ✓ (Python host) + R36; R28-H05 bootstrap | High | Med: preserves #965 cli-strip subtlety | R39 (E39-6, E39-7) |
| `protocol.py` — envelope shape validation, request build/encode/decode | Closed-shape validation of E16-1 messages | Portable policy (B) | Medium | MOVE validation later; keep Python implementation as oracle | R23 strict JSON ✓; R39 | Med | Med: byte framing | R39 |
| `protocol.py` — `run_adapter_request` (`subprocess.run`, timeout, kill/reap, stdout/stderr capture) | Process supervision | **Host mechanic** (D) | No | KEEP | — | — | — | stays; R36 provider beneath |
| `revision.py` (`git rev-parse HEAD`, `git cat-file -e`) | Revision identity | **Host mechanic** (D); the three-way classification is trivial policy | Low | KEEP; Genia receives revision facts as injected values | — | Low | Med if re-implemented | stays |
| `evidence.py` — `build_evidence`, count-sum invariant | Pure construction of the per-host evidence document | **Portable policy** (B) | **High** | MOVE construction; canonical-bytes rule must be specified first | R39 pre-flight defines canonical encoding | High (deterministic evidence is a stated R39 deliverable) | Med: `json_encode` ≠ `json.dumps` on non-ASCII/newline | R39 (E39-7) |
| `reporter.py` (109 lines of formatting) | Deterministic text report | Portable policy | Medium | MOVE with the runner | R39 | Low–Med | Low | R39 (E39-7) |
| `runner.py` — orchestration (mode selection, case loop, summary, evidence write) | Control flow over the above | Orchestration is portable; `ThreadPoolExecutor` fan-out and exit status are host | Medium–High | MOVE orchestration; keep concurrency/exit-status at the edge until R36 | R36; exit-status decision | High (it is the "runner as Genia program") | Med | R39 |
| **`host_parity_gate.py`** (285 lines) | Load two evidence docs + known-gaps manifest; classify per capability `PARITY_OK`/`KNOWN_GAP`/`UNDOCUMENTED_GAP`/`STALE_GAP`; evidence-failure counts; report; exit 0/1/2 | **Portable policy** (B); only three file reads and the exit status are host | **High** | **MOVE — first R39 policy slice**; keep Python gate as oracle | Pure core: none beyond R18/R23. Edge: R35 reads; exit-status mapping | **High** — closes the loop on C++ parity CI | Low–Med; CI-critical, so dual-run first | **R39 (named slice)** |
| `hosts/python/adapter.py`, `exec_*.py`, `ir_normalize.py` (397), `normalize.py`, `parse_adapter.py`, `protocol_adapter.py` | Run Genia on the Python runtime; normalize Python AST/IR to portable shapes; speak E16-1 | Implements/adapts Genia itself (A/D) | No | **KEEP** | — | — | Rewriting loses the independent reference | stays |
| `hosts/python/mcp_launch.py`, `mcp_host.py`, `mcp_parse_capability.py` | Revision identity, env allowlist, bootstrap, parser access | Host mechanics (A/D) | No | **KEEP** (already minimal; this is the model) | — | — | — | stays (R28) |
| `apps/mcp/mcp.genia` (473 lines) | Decode/validate/dispatch/compose/frame | Already Genia | — | Reference architecture (section 3.9) | — | — | — | R28 ✓ |

### 2.2 Documentation, release, and process tooling

| Artifact | Python responsibility today | Portable policy or host mechanic? | Suitability | Recommended disposition | Prerequisite | Payoff | Risk | Roadmap home |
|---|---|---|---|---|---|---|---|---|
| `gen_function_docs.py` — acquisition (`make_global_env`, `root().autoloads`, `GeniaFunctionGroup.params`, `public_host_builtin_docs`) | Introspects live Python runtime objects | Host mechanic / missing introspection boundary (C) | No (today) | KEEP; replace with a *host-emitted metadata record export* once an introspection surface exists | R33 tooling/introspection | — | One-off API if done early | R33 |
| `gen_function_docs.py` — `slug`, summary extraction, collision handling, sort, `render_index`/`render_page`/`render_nav_block`/`render_wiki`, `--check` diff | Pure string transformation over records | **Portable policy** (B) | **High** (after record export) | MOVE rendering/grouping/nav/`--check` policy; host keeps file writing | R33 record export + R35 writes | Med–High — documentation metadata is a named killer-workflow case; byte-identical output makes a clean dual-run | Med: records currently carry Python-object-derived `signatures` | R33 consumer, R35 for writes |
| `lint_doc.py` — rules DOC001–DOC007, section/HTML/table/fence rules (`lint_doc`, `parse_doc`) | Text rules over a docstring | **Portable policy** (B) | **High** (rules) | MOVE rules after source access is clean | R33 (docstrings as parsed metadata, not regex scans) | Med | Low–Med | R33 consumer |
| `lint_doc.py` — `_extract_docs_from_file`, `_public_bindings` (regex over `.genia` text), `_runtime_public_names` (Python introspection) | Finds docs/bindings by scanning source | **Source parsing by regex** — a shadow parser (C) | **Low** (as regex) | **DO NOT re-implement the regexes in Genia.** Wait for R33 parser/introspection access. Note `--public-names FILE` already exists as a decoupling seam | R33 | — | A second, divergent mini-parser | R33 |
| `stage_docs_for_mkdocs.py`, `publish_wiki.sh` | Copy/rewrite links; `git clone/commit/push` | Host/filesystem/Git mechanics (D) | No/Low | KEEP | — | — | — | stays |
| `validate_llm_instructions.py` (185) | Regex checks over agent-instruction files | Text policy, but not data-pipeline work | Low–Medium | **Classify only.** Do not build capabilities for it; revisit if R35 file reads and R33 text tooling make it fall out for free | R35 | Low | Low | Parking lot |
| CI inline `python3 - <<'PY'` in `docker-dev-environment.yml` ("Verify and report conformance counts") | Loads one evidence file, fails on non-zero failing counts | Portable policy, **duplicating** `host_parity_gate._FAILING_COUNT_FIELDS` | Medium | Fold into the parity/release-check policy rather than a second copy | R39 | Low | Low | R39 / release-check |
| `host-parity.yml` pipeline (python evidence → cpp evidence → gate) | Docker orchestration; evidence generation; gate | GitHub Actions + container mechanics are host; the gate is policy | — | KEEP the workflow; swap the gate step for the Genia gate only after dual-run | R39 | — | CI regression | R39 |
| Future release-check program | (does not exist) | Policy over evidence bundles | High | Parking-lot candidate; first consumer would be the parity gate | R35, R39 | High | Med | Parking lot → R39 follow-on |

### 2.3 Language implementation, capabilities, and sessions

| Artifact | Responsibility | Class | Suitability | Disposition | Roadmap home |
|---|---|---|---|---|---|
| `src/genia/{lexer,parser,lowering,evaluator,ir,optimizer,values,callable,pattern_match}.py`, `builtins.py` | Implements Genia | A | No | **KEEP.** A metacircular/self-hosted secondary implementation may be interesting later but must not replace the independent bootstrap/reference host without a separately approved gate | R41 (artifacts) at earliest |
| `process_capability.py`, `process_execution.py`, `process_transport.py` | `execution.process`: deadline, SIGKILL+reap, byte limits | D (OS enforcement) | No | **KEEP** (R28-H04) | stays |
| `http_transport.py`, `server_lifecycle.py`, `gemini_rest.py`, `host_bridge.py` | Sockets, HTTP, provider REST | D | No | **KEEP** | stays |
| `read_file`/`write_file`/`resource.*` Phase 1 fs bridge | Ambient filesystem access (Python-host-only, Experimental) | C | No | KEEP as is; **do not make new tooling depend on it as authority** — R35 supersedes with Store/Location | R35 |
| Native test kernel/runner/CLI (`test_kernel.py`, `native_test_runner.py`, `test_cli.py`) | Run `TestUnit`s, catch host exceptions, aggregate, format, exit codes | Host-bound (exception capture, exit codes); some aggregation is portable | Low | KEEP for now; revisit with portable lifecycle/R33 | R33 |
| Jupyter wire/protocol adapter (R42 E42-2) | ZeroMQ/Jupyter messages | D | No | **KEEP host tooling** | R42 |
| R42 interactive-session contract | Persistent bindings, per-submission observations, diagnostics, close | Portable contract, host implementation | — | Shared contract + shared evidence; Genia does not own transport | R42 |

## 3. Detailed findings by review area

### 3.1 Shared spec runner (reconciled with R39)

*Good Genia candidates* (class B): envelope validation, capability
applicability and filtering, expected/actual comparison, normalization
(`\r\n`→`\n`, cli trailing-newline strip), outcome classification
(`pass/fail/unsupported/protocol_error/crash/timeout/invalid`), aggregation
(counts-sum invariant), deterministic evidence/report construction, parity and
known-gap policy.

*Host responsibilities*: filesystem and YAML bytes acquisition, process
creation, timeout/kill/reap, transport framing, clock access, Git revision
lookup.

*R39 reconciliation.* The current R39 text already covers: baseline-first,
Genia-native YAML profile parser, envelope validation, R35 discovery, R36/
`execution.process` invocation, comparison/evidence/reporting, dual-run gate,
retained Python oracle, and the killer-workflow framing. No new release is
justified. Gaps the existing text did not state (and this PR's R39 edit now
does): (a) the **host parity gate and known-gap policy** are in scope;
(b) **revision classification** is consumed as injected host facts, not
re-implemented over Git; (c) the policy slices are pure functions over
ordinary Genia values and can be authored and shadow-tested before the I/O
edges exist, with only *authoritative cutover* waiting on R35/R36 and the
dual-run gate.

*Open hazards to resolve in R39 pre-flight, not here:*

- **Canonical evidence bytes.** `evidence.encode_evidence` is
  `json.dumps(..., sort_keys=True, indent=2) + "\n"`. Genia `json_encode`
  differs on non-ASCII escaping and the trailing newline (measured, section
  0). R39 must define the canonical byte form (or compare parsed values and
  separately specify bytes) before "byte-identical evidence" is a gate.
- **Self-referee risk.** A Genia runner executing on the Python host and
  judging the Python host can fail the same way the host does. The retained
  Python oracle and the C++ host's later ability to run the same runner are
  the independence story; see 3.2 and guardrails.
- **YAML profile fidelity.** PyYAML `safe_load` semantics (anchors, implicit
  typing such as `yes`/`1e3`/dates) are wider than a contracted profile. The
  profile parser must reject, not guess, what it does not support (R39 already
  says "explicit unsupported-feature handling").
- **Concurrency and exit status.** `--host-jobs` fan-out and the 0/1/2 exit
  mapping are not expressible from Genia today. Treat them as host-edge
  concerns, and do not add a Genia exit API only for this.

*Killer-workflow fit:* **strong** — shared specs are messy external records
that are parsed, validated, filtered by capability, executed through a host
boundary, Outcome-classified, aggregated, and rendered as deterministic
evidence. This is the proving case R39 already names.

### 3.2 Host parity gate — decision

**Yes: `host_parity_gate.py` should become part of the Genia-native R39
orchestration.** Reasons grounded in the code:

- Its inputs are structured, already-decoded JSON: two E16-7 evidence
  documents and `spec/known_host_gaps.json`, plus
  `spec/manifest.json`'s `optional_capabilities`.
- Its decisions are exactly class B: failing-count policy
  (`fail/protocol_error/crash/timeout/invalid` must be 0), per-capability
  parity classification, stale-gap detection, required-field and
  issue-reference validation of the manifest, and an explicit "C++ not
  evaluated" reason rule.
- Its output is a deterministic report plus a three-state status
  (OK / FAIL / tooling-error).
- It has no process, network, or clock dependency. Only three file reads and
  the exit status are host edge.
- It is already differentially testable: `tests/unit/test_host_parity_gate.py`
  (310 lines) builds fabricated evidence documents without a C++ build. Those
  documents are a ready-made shared corpus for dual-run.
- It is the smallest R39 slice with real stakes (CI parity for the C++ host),
  so it proves the shape before the larger runner moves.

Constraints: keep the Python gate authoritative and in CI until the Genia gate
agrees with it across the dual-run corpus; keep the Python gate afterwards as
the oracle (it is ~285 lines; carrying it costs little). Do not generalize the
gate beyond Python-vs-C++ in the first slice; a host-list generalization is a
design question for the pre-flight. The three-state exit status needs a
host-edge mapping decision; do not add a Genia exit API for it in isolation.

### 3.3 Native and shared test migration

Classification of Python tests (counts from the heuristic scan in section 0;
treat as indicative):

| Kind | Examples | Stays Python? |
|---|---|---|
| Portable Genia behavior asserted through the Python harness | `test_option`, `test_maps`, `test_lists_and_patterns`, `test_validate_record`/`_optional`/`_each`, `test_pipeline_operator`, `test_higher_order`, `test_none_aware_option_helpers_227`, many `test_r22_*`/`test_r23_*` | **No — audit for shared-spec or native twins** |
| Python internals | lexer/parser/AST/IR, `test_ir`, optimizer, `test_callable_runtime`, TCO, evaluator/host-bridge extraction | Yes |
| OS/transport/threading/security | 13 `test_execution_process_*` files, `test_http_transport`, loopback tests, `test_shell_stage`, `test_server_*` | Yes |
| Python adapters and exception normalization | `test_python_host_adapter`, `test_python_protocol_adapter_762`, diagnostic-normalization sweeps asserting no raw Python text | Yes |
| Tooling and doc sync | `tests/doc/*`, `test_spec_runner_*`, `test_host_parity_gate`, `test_lint_doc`, cheatsheet sidecar tests | Yes (until the corresponding tool moves) |
| Native-test stack internals | `test_native_test_*` | Yes |
| Release proving cases | `test_rN_*_proving_case`; many already have `tests/native/*.genia` and `tests/spec/` counterparts | Keep; check for twin coverage |

A subtlety: native Genia tests are Experimental and **Python-host-only**
(`GENIA_STATE.md` native-test boundary). A native test therefore does *not*
prove portability. The existing STATE rule — covered portable observable
behavior stays in shared specs and is not "moved" into native tests — stays
correct. The preferred venue for a portable observation is a shared spec
(stdout/stderr/exit_code, parse AST, or Core IR); a native test is the venue
for Genia-facing source-level behavior that is not (yet) portable or reads
better as assertions in Genia.

**Proposed durable rule (recommended, not adopted by this PR — it edits agent
governance and needs owner approval):**

> No new Python test may be the sole authority for behavior the Genia contract
> treats as portable when the same observation can reasonably be expressed as a
> shared semantic spec or, for Genia-facing but not-yet-portable behavior, a
> native Genia test. Python tests remain the home for Python internals, OS
> behavior, transport mechanics, Python exception normalization, Python
> adapters, subprocess/threading behavior, and host-specific security
> boundaries; such tests should say so in their module docstring. Migrate
> existing tests opportunistically: when a change touches a Python test whose
> only subject is portable behavior, add the shared-spec/native twin in the
> same change. Do not mass-migrate, and do not delete a Python test until its
> twin demonstrably covers the same observations.

Candidate homes if approved: the `TESTING RULE` section of `AGENTS.md` and
`docs/process/04-test.md`. If adopted, `tests/unit/test_llm_instructions.py`,
`tools/validate_llm_instructions.py`, and `tests/doc/test_semantic_doc_sync.py`
must be re-run in that change.

### 3.4 CI and release evidence

Where Python mainly loads, validates, compares, aggregates, or renders
structured evidence:

- `host_parity_gate` (host-parity.yml) — strong candidate (3.2).
- The inline conformance-count check in `docker-dev-environment.yml` —
  duplicates the gate's failing-count policy.
- `tools.spec_runner` summary/evidence production — R39 (3.1).

Where Python is orchestration or tooling that should stay host-side:
`pytest`, `ruff`, `mkdocs build`, `uv sync`, Docker/Actions plumbing,
`gen_function_docs.py --check` as a CI step, wiki publishing.

**Should Genia eventually own release-evidence orchestration? Yes, the policy
layer — later, and only after R39 proves the shape.** Do not move GitHub
Actions into Genia. Do not invent release-specific host APIs.

```text
host tools / CI
      |   (spec_runner, pytest, mkdocs, git, docker)
      v
structured evidence  (E16-7 JSON, known gaps, manifest, revision facts)
      |
      v
Genia release-check program   (validate, classify, aggregate)
      |
      v
deterministic Outcome / report
```

Wait for the storage and execution capabilities (R35 for evidence/report
I/O, `execution.process` + R36 where it must launch collectors) rather than
adding bespoke readers. It is a parking-lot candidate that R39's parity-gate
slice would promote by evidence.

### 3.5 Function documentation generation

*Host:* runtime metadata acquisition (`make_global_env`, autoload table,
`GeniaFunctionGroup.params`, `public_host_builtin_docs`) and filesystem writes
(`write_all`, pruning, `mkdocs.yml` nav splice, `.tmp/wiki`).

*Portable:* metadata normalization (`mstr`/`mlist`), summary extraction,
slug and collision policy, sort, grouping by category, Markdown for index and
pages, nav-block rendering, wiki mirror rendering, and the `--check` "would
regeneration change tracked files" decision.

The clean cut is a **record export**: the host emits JSON records
(`name, category, module, since, deprecated, stability, see_also,
signatures[], arities, doc_raw, source_kind`) and a Genia program renders. The
record currently contains `signatures` derived from Python objects, so the
record contract must be portable before anything moves. That is
introspection — R33's territory ("derived from implemented parser/Core-IR/
help/debugger truth") — and writing the outputs is R35's. Doing it earlier
means a one-off "dump docs metadata" API; doing it after gives a general
tooling surface that other consumers (editor help, R42 completion/inspection)
also use. Byte-identical Markdown makes dual-run trivial.

*Killer-workflow fit:* medium–high ("documentation metadata" records →
validate → group/sort → render → diagnostics).

### 3.6 Documentation linter

The rules (DOC001–DOC007: summary required/shape, allowed sections, no HTML,
no tables, behavior mention, example fence sanity) and coverage policy
(DOC008/DOC009) are portable text policy. The input side is not: docs are
found with regexes over `.genia` text (`_TRIPLE_DOC_RE`, `_BINDING_NAME_RE`,
`_TOPLEVEL_BINDING_RE`) and the public-name set comes from Python
introspection. Re-implementing those regexes in Genia would create a second,
divergent mini-parser. Recommendation: **wait for R33 parser/introspection
access**, then move the rules over parsed annotation/docstring records. The
existing `--public-names FILE` option shows the seam is already visible.

### 3.7 LLM instruction validation

`validate_llm_instructions.py` is regex text policy over a handful of files.
It is not a data pipeline and does not strengthen the killer workflow.
Classification: portable text policy, Low priority, **parking lot**. Do not
create language features to rewrite it. If R35 file reads and R33 text tooling
exist and it falls out as a trivial consumer, move it then.

### 3.8 Reconciling the old Python-reduction analysis with current `main`

The earlier review mixed two things: pure-Python deduplication (not a Python→
Genia question) and a handful of Python→Genia moves. Current-tree evidence:

| Old item | Current state | Verdict |
|---|---|---|
| #16 `cli_flag?`/`cli_option`/`cli_option_or` → `cli.genia` | Public functions exist in `cli.genia` as `cli_flag?(opts, name) = _cli_flag?(opts, name)` etc., calling host privates (`env.set("_cli_flag?", ...)`) | **Landed as a wrapper.** The host primitives remain, which is correct: they keep the `_ensure_*` diagnostics and the absent/present (`_UNSET`) semantics. Python lines were *not* reduced and should not be |
| #19 `sum` → `reduce` | `sum(xs) = _sum(xs)` in `math.genia` over `sum_fn` | **Rejected on diagnostics.** `sum_fn`'s "item N received <type> … use keep_some…" guidance is asserted by `tests/cases/option/error_sum_requires_plain_numbers.err` and `test_flow_unix_scenarios.py`. A `reduce` rewrite would regress it. Side finding: `sum_reduce` in `math.genia` has no references in `src/`, `tests/`, or `docs/` beyond its own definition (candidate cleanup, unverified beyond grep) |
| #24 `update_entry_bytes`, #26 `entry_json?` → Genia | Still host builtins (`update_entry_bytes_fn`, `entry_json_fn`) | **Valid but negligible.** ZIP entries are opaque host values; composing `entry_name`/`entry_bytes` in Genia saves ~11 Python lines and drops the callable/bytes checks. Not worth a batch; revisit only if the ZIP surface moves wholesale |
| File helpers | `read_file(path) = _read_file(path)`; `resource.genia` wraps host fs primitives with locked reason strings | **Already the right split.** Thin host primitive, Genia wrapper. R35 will redefine authority; do not touch before then |
| Web helpers | `web.genia` owns `route`/`get`/`post`/`find_route_handler` composition over `_serve_http`/`_http_send`/`_cors` | **Already the right split** |
| Items 1–15, 17–23, 25 (Python-to-Python dedup) | Not a Python→Genia question. Spot checks: `env.register_autoload(` still appears 234 times in `builtins.py` (item 2 not landed); the `except ImportError` fallback blocks named in items 1/5 are no longer present in `lowering.py`/`interpreter.py`/`callable.py`/`evaluator.py` | Out of scope here; the R23-numbering collision means `docs/strategy/r23-python-reduction-release.md` should stay marked non-adopted |

**Do not confuse** "public function implemented as a Genia wrapper" with
"host primitive no longer needed." A thin host primitive behind a Genia
wrapper is often the correct architecture, and counting its removal as
progress would incentivize diagnostic regressions. `builtins.py` and the
`src/genia/*.py` total (~24,700 lines) are not a metric for this effort.

### 3.9 MCP as the reference architecture

R28 demonstrates the intended split concretely (`apps/mcp/mcp.genia`,
`hosts/python/mcp_*.py`, ledger H01–H07, guarded by
`tests/unit/test_r28_mcp_architecture.py`):

| Genia (`mcp.genia`) | Host |
|---|---|
| decode, closed-schema validation (Templates from `json_schema`), method dispatch, result/error construction, JSON framing, stdout production | `contract_revision` identity (40-hex, validated), environment allowlist, launch, **parser access** passed as an explicit `host` argument, `execution.process` deadline/kill/reap/byte limits |

Notable properties worth generalizing: capabilities are passed as explicit
arguments (`serve(revision, host)`), never ambient bindings; the host supplies
the only non-derivable datum; an architecture test enforces that the program
does not drift back to Python; and gaps are recorded as evidence in a ledger
rather than becoming speculative APIs (H05 — no Genia-side bootstrap for an
`execution.process` capability — is also R39's invocation prerequisite, so it
should be solved once, generally).

**Recommendation:** capture this as a short general architecture principle for
future integrations ("Genia owns decode/validate/dispatch/compose/normalize;
the host supplies explicit, narrow capabilities as arguments; an
architecture test guards the boundary"). This PR records it in this analysis
and the guardrails; promoting it to a standalone `docs/architecture/` note is
a follow-up that does not need to block anything.

### 3.10 Jupyter (R42)

Preserve the layering in `roadmap/r42.md`:

```text
Jupyter wire/protocol adapter  (ZeroMQ, protocol library)   -- host tooling
        |
host-neutral interactive-session contract                    -- shared, portable
        |
Genia runtime
```

Do not rewrite transport in Genia. Portable session policy (persistent
bindings, per-submission result/stdout/stderr/diagnostics, failure survival,
close) is shared contract plus shared evidence; transport stays Python-host
tooling. R42 is independent of R39 and of R28; its value to this review is
that R33 tooling (and doc/lint tooling that wants parsed access) can reuse the
same interactive-session seam.

## 4. Killer-workflow assessment

| Proposed migration | Helps prove/strengthen *Outcome-aware validated data pipelines*? |
|---|---|
| Host parity gate | **Yes, strongly.** Structured evidence → validate → classify per capability → aggregate → deterministic report/diagnostics |
| Spec-runner policy (envelope validation, applicability, comparison, classification, aggregation, evidence) | **Yes, strongly.** Already framed as R39's proving case |
| Release-evidence program (post-R39) | **Yes.** Same shape over a wider evidence bundle; only worth doing once R39 proves it |
| Documentation metadata rendering | **Yes, moderately.** Records → validate → group/sort → render → diagnostics; also a clean byte-identical dual-run |
| Lint rules | **Partly.** Validation with diagnostics over records; input access depends on R33 |
| `validate_llm_instructions.py` | **No.** Text lint; park |
| `sum`/zip/cli wrapper moves | **No.** Line-count motivation only; rejected or already settled |
| Jupyter transport / process / network / clock / Git | **No.** Host mechanics; enablers, not workflow proofs |
| Kernel (lexer/parser/evaluator) | **No.** Implements Genia itself |

## 5. Immediate candidates (no new language capability)

1. **Roadmap and boundary clarification** — done in this PR: R39 names the
   host parity gate, known-gap policy, injected revision facts, and the
   pure-core/edge split; `sequence.md` records the boundary; R33 notes
   documentation-tooling consumers; the parking lot records the release-check
   candidate.
2. **Adopt the portable-behavior test rule** (section 3.3) — documentation/
   process only; requires owner approval because it edits agent governance.
3. **Test-migration audit** — an inventory of the ~58 candidate unit files
   with a shared-spec/native twin check per file (no migration in the
   audit). Start where twins likely exist (`validation-*`, `outcome-*`,
   `r22-*`/`r23-*` shared specs versus their unit tests). Opportunistic
   twins thereafter.
4. **Policy-core shadow work** in R39 pre-flight: pure Genia functions over
   decoded evidence/known-gap maps (the parity gate first), tested against the
   existing fabricated-evidence documents, with inputs injected as ordinary
   values. This introduces no new capability *if* it stays shadow
   (non-authoritative, no ambient file reads, no CI cutover). It is listed here
   as feasible, not as started: R39 is not active and still needs its own
   gates.
5. **Cheap hygiene observations** (not required by this review):
   the duplicated failing-count check in `docker-dev-environment.yml`;
   `sum_reduce` in `math.genia` appears unreferenced.

## 6. Roadmap candidates (existing homes only)

No new release is proposed. Everything maps onto existing releases.

| Work | Home | Notes |
|---|---|---|
| Record-export/introspection surface for docs and lint; docstrings as parsed metadata; deterministic source ranges | **R33** (consumer scope) | R33 is "derived from implemented parser/Core-IR/help/debugger truth"; documentation tooling is a candidate consumer, not a commitment |
| Store/Location/ResourceSnapshot for reading specs/evidence/manifest and writing generated output | **R35** | Replaces ambient `read_file`/`resource.*` Phase 1 as the authority for tooling |
| Bounded execution of adapters and collectors; child lifetime; normalized failures | **R36**, with `execution.process` (implemented, Python host) beneath it | Solve R28-H05 (bootstrap of a process capability from Genia) once, for both MCP and R39 |
| Genia YAML profile parser; envelope validation; filtering; comparison; evidence; **host parity gate**; dual-run gate; retained oracle | **R39** | Parity gate first; Genia runner becomes default only after dual-run |
| Interactive-session contract, Python REPL adoption, Jupyter kernel | **R42** | Independent branch; feeds R33 reuse |
| Release-check program over evidence bundles | **Parking lot → R39 follow-on** | Promote only on R39 evidence |
| Test-placement rule | Process (not a release) | Section 3.3 |

## 7. Keep in Python (host) — explicit list

So future agents do not re-propose these:

- Lexer, parser (and parser bootstrap), Core IR lowering, optimizer,
  evaluator, runtime value machinery, Python value/host representation, and
  Python host adapter internals (`hosts/python/*` normalization and protocol
  adapter).
- OS filesystem provider and `read_file`/`resource` Phase 1 bridge until R35.
- Raw process launch, supervision, deadline, kill/reap, byte limits
  (`process_*.py`).
- Sockets, HTTP server/client transport, provider REST adapters.
- Clocks and timers.
- Git/revision acquisition (`revision.py`, `mcp_launch.py` revision handling).
- Jupyter protocol adapter (ZeroMQ/protocol library).
- Python external-host adapter (`protocol_adapter.py`) and E16-1 subprocess
  runner (`run_adapter_request`).
- The independent Python conformance runner and host-parity gate, retained as
  a small oracle even after the Genia-native runner is primary. Its value is
  that the implementation under test is not its only referee; `loader.py`'s
  PyYAML path, `comparator.py`, `evidence.py`, and `host_parity_gate.py` are
  the load-bearing parts.
- GitHub Actions/Docker/`uv`/`pytest`/`mkdocs`/wiki publishing plumbing.
- Native-test kernel exception capture and exit codes (until portable
  lifecycle/R33 changes the picture).

## 8. Dependency graph

Hard dependencies (from the roadmap) are drawn with `==>`; sequence order or
soft reuse with `-->`.

```text
Completed foundations:
  R16 protocol/capabilities/evidence   R18 portable equality   R23 strict JSON
  execution.process (Python host, unnumbered, implemented)

R33 tooling/introspection  ----sequence---->  R35 storage/resources  ----sequence---->  R36 execution
       |                                           |                                         |
       |  (consumer: docs/lint record export)      |                                         |
       v                                           v                                         v
  docs/lint policy in Genia                R39 conformance migration  <==  R18 + R35 + R36
  (needs R33 export + R35 writes)                  |
                                                   |-- slice 1: parity gate (pure core shadow-able earlier)
                                                   |-- YAML profile parser, envelope validation, filtering
                                                   |-- discovery (R35), invocation (R36), evidence/report
                                                   '-- dual-run gate  ==>  default cutover; Python oracle retained
                                                   |
                                                   v
                                      release-check program (parking lot)

R28 MCP:   independent; supplies the host/Genia reference split and ledger entry H05
R42 sessions/Jupyter: independent branch off R26/R27; soft input to R33 reuse; not on the R39 path
R40, R41: orthogonal (R41 portable Core IR artifacts later strengthens the independent-oracle story)
```

Correction to a common shorthand: R39's stated roadmap dependencies are R18,
R35, and R36 — **not R33**. R33 precedes R35 in the schedule and is the hard
prerequisite only for the documentation/lint migrations.

## 9. Roadmap edits

*Made in this PR (planning-only; `GENIA_STATE.md` untouched):*

- `docs/strategy/roadmap/r39.md` — adds an explicit scope clarification:
  host parity gate and known-gap policy, injected revision facts, the
  pure-policy/I-O-edge split with shadow-before-cutover, negative fixtures in
  the dual-run corpus, and canonical-evidence-bytes as a pre-flight item.
- `docs/strategy/roadmap/sequence.md` — records the host/Genia boundary rule
  for the dogfooding arc, the corrected dependency note, and a pointer here.
- `docs/strategy/roadmap/r30-r32.md` — R33 candidate scope notes
  documentation-tooling record export/lint access as a possible consumer.
- `docs/strategy/roadmap/parking-lot.md` — records the release-check program
  candidate and the explicit non-plan for `validate_llm_instructions.py`.

*Proposed, deliberately not made (needs owner decision):* adding the test
placement rule to `AGENTS.md` and `docs/process/04-test.md`; promoting the
MCP split to a standalone `docs/architecture/` principle note.

## 10. Proposed issue list (per `docs/process/08-roadmap-ticketing.md`)

Applying the ticketing guide's final check (supports current/next roadmap
release? small enough for one process run? speculative features excluded?
docs protected from future claims?), only two items are ticket-ready; the rest
are listed so they are not lost, and **none are created by this PR**.

| # | Proposed item | Classification | Create now? | Reason |
|---|---|---|---|---|
| 1 | Adopt the portable-behavior test placement rule in `AGENTS.md` and `docs/process/04-test.md` | Required infrastructure (process) | Yes, after owner approval | Docs-only; protects every later release; no behavior claim |
| 2 | Inventory pure-portable Python unit tests and check shared-spec/native twin coverage (audit only) | Follow-up | Yes, after #1 | Bounded, no migration, feeds opportunistic twins |
| 3 | R39 pre-flight: dual-run harness baseline and parity-gate policy-core slice (incl. canonical evidence bytes and negative fixtures) | Follow-up (R39) | **No** — create with the R39 epic when R39 is scheduled | R39 is planned, not active |
| 4 | General bootstrap of an `execution.process` capability from Genia (R28-H05) | Required infrastructure | **No** — keep in the R28 ledger; promote via its own process | Shared prerequisite of R28 and R39; the ledger forbids ticketing from discovery alone |
| 5 | Documentation record export/introspection for `gen_function_docs`/`lint_doc` | Follow-up (R33) | **No** | Candidate consumer of an R33 surface not yet designed |
| 6 | Genia release-check program over evidence bundles | Parking lot | **No** | Needs R39 evidence |
| 7 | `validate_llm_instructions.py` in Genia | Parking lot | **No** | Not a killer-workflow case |
| 8 | Housekeeping: dedupe the CI inline count check; remove `sum_reduce` if confirmed unreferenced | Follow-up | Optional | Trivial; not a Python→Genia migration |

Ticket shape for items 1 and 2 (the remainder inherits the standard fields at
creation):

- **#1** Release target: none (process). Roadmap alignment: protects the
  killer-workflow dogfooding arc. Scope includes: rule text, placement in the
  two process surfaces, sync-test runs. Excludes: any test migration, any
  language/runtime change, `GENIA_STATE.md`. Acceptance: rule present and
  consistent across surfaces; `validate_llm_instructions.py`,
  `tests/unit/test_llm_instructions.py`, `tests/doc/test_semantic_doc_sync.py`
  pass. Non-goals: mandating retroactive migration. Drift risk: contradicting
  the STATE native-test boundary — mitigated by reusing its wording.
  Phases: docs.
- **#2** Release target: none. Scope includes: per-file table
  (portable? twin exists? asserts Python representation?), no code changes.
  Excludes: moving, deleting, or rewriting any test. Acceptance: table
  committed as a non-process artifact only if the repository's "no process
  artifact in `docs/` after merge" rule allows it, otherwise in the issue.
  Non-goals: line-count targets. Drift risk: treating the list as authority
  to delete tests. Phases: test (inventory).

## 11. Migration guardrails

1. **No one-off host APIs solely to rewrite Python.** Wait for the proper
   release (R33/R35/R36/R42) or leave the host mechanic alone.
2. **Do not degrade diagnostics silently.** A migration that changes an error
   message needs an explicit before/after review (the `sum` case).
3. **Do not move host privilege into ambient Genia state.** Capabilities are
   explicit arguments or provisioned authorities, never ambient bindings.
4. **Do not couple portable policy to Python objects.** Policy consumes
   ordinary Genia values (maps/lists/strings/Outcomes), not `GeniaFunctionGroup`,
   paths, handles, or exceptions.
5. **Preserve shared-spec evidence.** A migration may add shared evidence; it
   never removes or weakens existing evidence.
6. **Preserve the independent Python oracle.** The implementation under test
   must not be its only referee; include negative/malformed fixtures in
   dual-run corpora so both runners must agree on non-pass classifications.
7. **Dual-run before cutover.** The Genia tool and its Python counterpart
   consume the same corpus and must agree on classification, counts, and
   evidence before the Genia tool is default.
8. **Do not call something portable until shared evidence proves it.** A
   policy written in Genia that only runs on the Python host is Genia-owned,
   not yet proven portable.
9. **Do not recreate a parser in Genia to eliminate Python** (lint regexes,
   YAML via ad hoc string handling).
10. **A thin host primitive behind a Genia wrapper is not debt.** Do not count
    its removal as progress.
11. **No roadmap item implies implementation.** Placement is planning
    authority only; every slice still needs its gates.
12. **`GENIA_STATE.md` remains final authority.** This review and its roadmap
    edits describe no implemented behavior.

## 12. Unverified or open

- Twin coverage between the 58 candidate unit files and shared specs was not
  checked file by file.
- `sum_reduce` unreferenced status was established by search of `src/`,
  `tests/`, and `docs/` only.
- The C++ host's ability to run a Genia-native runner is not assessed; it
  lacks `import` and file IO today (genia-cpp README), so it cannot be the
  second referee in the near term.
- Whether the parity gate should generalize beyond two named hosts, and how a
  Genia program signals a three-state exit status, are R39 pre-flight design
  questions.
