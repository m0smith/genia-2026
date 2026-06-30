# === GENIA PRE-FLIGHT ===

CHANGE NAME:
issue #510 r5-native-test-boundary

CHANGE SLUG:
issue-510-r5-native-test-boundary

Issue: #510  
Type: contract  
Release classification: R5 — Native Test Expansion / Pytest Migration Wave 1  
Branch: `contract/issue-510-r5-native-test-boundary`  
Handoff directory: `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/`

HARD STOP: Pre-flight only. Do not write contract, design, tests, implementation, docs sync, audit, or distillation.

---

## 0. BRANCH

Branch required: YES  
Branch type: contract  
Branch slug: `issue-510-r5-native-test-boundary`  
Expected branch: `contract/issue-510-r5-native-test-boundary`  
Base branch: `main`

Local verification required:

- Starting branch: TODO verify locally with `git branch --show-current`
- Working branch: `contract/issue-510-r5-native-test-boundary`
- Branch state: user report says branch was created from `main` and checked out
- Git status summary: TODO verify locally with `git status --short`

Rules:

- Do not work on `main`.
- Do not switch branches in this phase unless explicitly required by the process.
- Do not merge or rebase.
- Do not continue beyond pre-flight unless explicitly prompted.

---

## 1. SCOPE LOCK

Includes:

- Define the pre-flight scope for a future **contract** change named `issue #510 r5-native-test-boundary`.
- Classify this as explicit R5 work, even though the current active release is R4, because the user supplied an R5 issue/slug.
- Identify the boundary between:
  - Genia-native tests for Genia-facing behavior, and
  - Python pytest/shared semantic-spec tests for parser, IR, host/runtime, CLI harness, spec runner, and Python-specific internals.
- Identify authoritative files that must constrain the future contract.
- Identify likely docs and tests affected by a future native-test boundary contract.
- Preserve the R5 goal: move appropriate Genia-facing tests into Genia-native tests while keeping Python tests for Python host internals.
- Produce only `.genia/process/tmp/handoffs/issue-510-r5-native-test-boundary/00-preflight.md`.

Excludes:

- No contract writing beyond pre-flight findings.
- No implementation.
- No test migration.
- No new native-test behavior.
- No parser, IR, lowering, host adapter, CLI harness, spec runner, or runtime changes.
- No setup/teardown, fixture, parameterization, property-test, snapshot-test, parallel-test, or broad discovery feature work.
- No broad pytest migration.
- No multi-host native-test claims.
- No lifecycle-generalization work except where existing R4 native-test lifecycle facts constrain the boundary.
- No docs sync beyond writing this handoff artifact.
- No commit unless the local process explicitly requires pre-flight commits.

Release note:

- The current active release is R4 — Lifecycle Generalization.
- This change is R5 and therefore non-R4, but it is explicitly requested by the user.
- Proceeding through pre-flight is appropriate; later phases should continue only when explicitly prompted.

---

## 2. SOURCE OF TRUTH

Authoritative:

1. `GENIA_STATE.md` — final authority for implemented behavior
2. `GENIA_RULES.md`
3. `GENIA_REPL_README.md`
4. `README.md`
5. `spec/*`
6. `docs/host-interop/*`
7. `docs/architecture/*`
8. implementation under `src/*` and `hosts/*`
9. `docs/process/run-change.md` and related process docs

Additional relevant:

- `AGENTS.md`
- `docs/ai/LLM_CONTRACT.md`
- `docs/strategy/killer-workflow.md`
- `docs/strategy/release-roadmap.md`
- `docs/process/00-preflight.md`
- native-test implementation/tests, likely including:
  - `src/genia/test_kernel.py`
  - `src/genia/test_cli.py`
  - `tests/unit/test_native_test_kernel.py`
  - `tests/unit/test_native_test_cli.py`
  - native-test examples under `examples/`
  - shared CLI spec cases for selected native `--test` / `genia test` outcomes

Notes:

- `GENIA_STATE.md` wins if sources conflict.
- Strategy/roadmap docs are planning guides, not language contracts.
- Docs must describe only implemented, test-verified behavior.
- Contract phase must define behavior only; tests belong to the TEST phase.
- Python is currently the only implemented host and reference host.

---

## 3. FEATURE MATURITY

Stage:

- [x] Experimental
- [ ] Partial
- [ ] Stable

Doc wording:

- Native-test behavior should remain described as **Experimental** unless `GENIA_STATE.md` proves a narrower mature status.
- Python remains the reference host.
- Native tests complement pytest/specs; they do not replace all Python tests.
- The native-test boundary contract should avoid implying complete native-test coverage, full pytest migration, multi-host execution, lifecycle setup/teardown, fixtures, parameterization, snapshots, property testing, or parallel execution.

Current behavior to verify in authoritative docs and implementation:

- R2 introduced the minimal native test kernel and CLI entry point.
- R3 added `@test "description"` annotation-driven native test discovery for zero-argument functions, using the same native test kernel as legacy `test(name, body)` registrations.
- Shared CLI spec coverage includes selected native test-runner outcomes, but shared coverage is partial.
- R4 treats test lifecycle as the first implemented lifecycle consumer only as inert/descriptive plan/scope data, with no lifecycle runner, no setup/teardown execution, and no observable native-test behavior change.

---

## 3a. Portability Analysis

Portable contract candidates:

- Native tests are appropriate for Genia-facing behavior that can be expressed and verified in Genia source.
- Python pytest remains responsible for Python host internals, parser internals, IR normalization, host adapter behavior, CLI harness internals, spec runner implementation, and Python-specific exceptions/plumbing.
- Shared semantic specs remain authoritative for portable observable CLI/eval/flow/error/parse/IR behavior where covered.
- Native-test results exposed through CLI should stay deterministic and observable through stdout/stderr/exit-code where already covered.

Python reference host today:

- Python is the only implemented host.
- Native test execution is implemented in the Python reference host.
- Shared conformance currently runs against the Python reference host.

Host-specific concerns:

- The boundary contract must not require non-Python hosts to exist.
- The contract must not move host-adapter or parser/IR internals into Genia-native tests.
- If future hosts implement native tests, they must follow shared contract/spec behavior rather than redefining native-test semantics.

Portability risk:

- Risk: Medium.
- Reason: native tests are Genia-facing, but the current implementation is Python-hosted. Boundary wording must be explicit about portable behavior versus Python reference-host implementation.

---

## 4. CONTRACT vs IMPLEMENTATION

Portable contract:

- Native Genia tests should cover Genia-facing behavior: prelude helpers, Outcome helpers, validation helpers, Flow/Seq visible behavior, Sheet helper behavior, examples intended to be user-facing, and other behavior that can be written naturally in Genia.
- Native tests should validate behavior from the Genia user's perspective, not Python implementation details.
- Pytest/shared specs remain responsible for implementation and conformance surfaces that are not Genia-level source behavior.
- The native-test boundary should preserve deterministic naming, discovery, execution, result reporting, and diagnostics already documented as implemented.
- The boundary should explicitly state that native tests complement pytest/specs.

Python implementation today:

- Native test kernel and CLI are implemented in Python.
- Legacy `test(name, body)` and `@test "description"` named-function discovery are expected current behavior per R2/R3 roadmap/state alignment, subject to local verification.
- Shared CLI specs include selected native test-runner passing, runtime-erroring, and discovery-error outcomes.
- Python pytest remains necessary for host/runtime/parser/spec-runner internals.

Not implemented / out of contract for this issue:

- Full pytest migration.
- Multi-host native-test execution.
- Setup/teardown execution.
- General fixture system.
- Parameterized tests.
- Snapshot tests.
- Property tests.
- Parallel native-test execution.
- Arbitrary custom lifecycle execution.
- Native tests for parser/IR/host adapter internals.
- Native tests as replacement for shared semantic specs.

---

## 5. TEST STRATEGY

Core invariants:

- The contract distinguishes Genia-facing native-test candidates from pytest-only implementation/internal tests.
- The contract does not imply native tests replace pytest or shared specs.
- The contract does not describe unimplemented native-test features.
- The contract aligns with current `GENIA_STATE.md` native-test and shared-spec facts.
- The contract preserves R5 scope and does not accidentally pull in R4 lifecycle implementation.

Expected behavior:

- Future contract/docs should guide maintainers toward moving appropriate Genia-facing tests into native tests.
- Future contract/docs should keep parser, IR, host adapter, CLI harness, spec runner, and Python-specific exception/plumbing tests in pytest/shared specs.
- Native-test documentation should be explicit about Python reference-host status and experimental maturity.

Failure cases:

- Docs claim native tests are stable or complete without evidence.
- Docs imply native tests replace pytest.
- Docs imply setup/teardown, fixtures, parameterization, snapshots, property tests, parallelism, or multi-host support.
- Tests are migrated into native tests even though they assert Python internals.
- Shared specs are bypassed for portable observable behavior.
- R5 boundary work changes observable test behavior without test/design/implementation phases.

Test approach for later phases:

- CONTRACT phase: no tests.
- DESIGN phase: identify exact doc/test guardrails.
- TEST phase, if contract wording becomes protected semantic text:
  - update/add doc tests or semantic doc sync tests.
  - consider `docs/contract/semantic_facts.json` only if a protected semantic fact is introduced or changed.
- IMPLEMENTATION phase only if future tests expose missing behavior; this issue should likely be docs/contract-only unless the issue body says otherwise.
- Run targeted doc tests and native-test-related unit tests in later phases as appropriate.

---

## 6. EXAMPLES

Minimal:

- Native-test candidate:
  - A Genia source test for an Outcome helper, validation helper, Flow/Seq visible behavior, Sheet helper, or user-facing prelude utility.
- Pytest candidate:
  - A Python test for parser AST shape, IR normalization, host adapter plumbing, CLI harness internals, or spec runner implementation.

Real:

- Native Genia test:
  - A validated-pipeline example test that asserts user-facing Genia behavior.
- Pytest/shared spec:
  - A shared CLI spec that asserts `stdout`, `stderr`, and `exit_code` for selected native test-runner outcomes.
  - A pytest that asserts Python exception or adapter normalization behavior.

Do not add runnable examples in this phase.

---

## 7. COMPLEXITY CHECK

- [ ] Adding complexity
- [x] Revealing structure

Justification:

- This change should not add a new testing mechanism.
- It should reveal and document the correct boundary between existing native-test capability and existing pytest/spec responsibility.
- The boundary reduces future migration ambiguity and prevents LLMs from moving the wrong tests into native Genia tests.

Complexity risks:

- Over-defining a migration matrix too early.
- Turning a boundary contract into a broad pytest migration plan.
- Pulling lifecycle execution features into R5 prematurely.
- Blurring shared semantic specs versus native tests.

Mitigation:

- Keep contract wording narrow, maturity-labeled, and implementation-aligned.
- Use explicit “belongs in native tests” / “stays in pytest/shared specs” categories.
- Do not claim new behavior.

---

## 8. CROSS-FILE IMPACT

Files likely to change in later phases:

- `GENIA_STATE.md`
- `docs/strategy/release-roadmap.md` only if R5 positioning needs clarification
- README or testing docs only if public native-test guidance is currently incomplete or misleading
- relevant docs/book or docs/architecture testing/native-test sections, if present
- `docs/contract/semantic_facts.json` only if protected semantic facts are added/changed
- `tests/doc/test_semantic_doc_sync.py` only if semantic sync guardrails need updates
- native-test unit tests only if future phases change behavior

Files unlikely to change:

- parser/lexer/lowering/Core IR
- host adapters
- spec runner implementation
- flow runtime
- CLI harness internals
- prelude implementation

Risk of drift:

- [ ] Low
- [x] Medium
- [ ] High

Reason:

- This is mostly contract/docs boundary work, but it touches a historically drift-prone area: what native Genia tests cover versus what remains in pytest/shared specs.

---

## 9. DOC DISTILLATION CHECK

Creates process artifacts?

- [x] YES → run Doc Distillation later if artifacts are tracked or process requires cleanup
- [ ] NO

Adds docs/design or docs/architecture files?

- [ ] YES → classify KEEP / EXTRACT / DELETE
- [x] NO in pre-flight

Doc drift risk:

- [ ] Low
- [x] Medium
- [ ] High

Notes:

- Handoff files under `.genia/process/tmp/handoffs/...` are process artifacts.
- Later phases should ensure no temporary handoff artifacts are accidentally tracked unless the process explicitly requires it.
- Contract/docs wording must remain aligned with `GENIA_STATE.md` and roadmap status.

---

## 10. PHILOSOPHY CHECK

- preserves minimalism? YES
- avoids hidden behavior? YES
- keeps semantics out of host? YES, if the future contract labels Python reference-host details separately from portable native-test guidance
- aligns with pattern-matching-first? YES / N/A — this boundary protects Genia-facing tests without adding syntax or competing paradigms

Notes:

- This change should reduce ambiguity rather than add surface area.
- It should keep native tests focused on user-visible Genia behavior.
- It should prevent broad testing-framework creep.
- It should not redefine language semantics inside Python host tests.

---

## KILLER WORKFLOW ALIGNMENT

Does this change directly strengthen Outcome-aware validated data pipelines?

- [ ] Yes
- [x] Indirectly
- [ ] No

Explanation:

- R5 native-test boundary work indirectly strengthens the killer workflow by clarifying which Genia-facing data-pipeline behavior should be protected with native tests.
- Strong native tests are appropriate for Outcome helpers, validation helpers, Flow/Seq visible behavior, Sheet helper behavior, and examples intended to demonstrate validated data pipelines.
- The change does not add data-pipeline features directly; it improves test placement discipline so the pipeline surface can be protected without mixing in Python internals.

Improves:

- [x] Flow / Seq — by identifying visible behavior as native-test eligible
- [x] Outcome — by identifying helper behavior as native-test eligible
- [ ] record parsing
- [x] validation — by identifying validation helpers/examples as native-test eligible
- [x] diagnostics — by keeping user-facing diagnostics native-test eligible while host/internal formatting stays in pytest/specs as appropriate
- [x] Sheets — by identifying Sheet helper behavior as native-test eligible
- [x] CLI data processing — by preserving shared CLI specs for observable CLI outcomes
- [x] value templates for validation/contracts/shapes — indirectly, if future value-template behavior becomes Genia-facing and testable in native tests

Parking-lot check:

- Not parking lot because the user explicitly requested R5 native-test-boundary work and R5 is the planned release for making the native-test / pytest split explicit.

---

## 11. PROMPT PLAN

Pipeline:

- [x] Preflight — this file
- [ ] Contract — define the boundary text and authoritative categories
- [ ] Design — identify exact file edits and semantic guardrails
- [ ] Test — add doc/semantic guardrail tests if needed; add no implementation tests unless behavior changes
- [ ] Implementation — likely no-op unless the issue body requires behavior changes
- [ ] Docs — sync `GENIA_STATE.md` and any relevant docs to implemented/tested reality
- [ ] Audit — verify contract/docs/tests alignment and no scope expansion
- [ ] Distillation — remove/ignore process artifacts and keep durable docs only where appropriate

Recommended next phase:

- CONTRACT prompt.

Contract phase should:

- Read the same authoritative docs.
- Define exactly what belongs in native Genia tests versus pytest/shared specs.
- Avoid test implementation.
- Avoid changing behavior.
- Produce a contract artifact only.

---

## FINAL GO / NO-GO

Ready to proceed?

YES, for CONTRACT phase only.

Missing:

- Local branch/status verification.
- Issue body verification, if issue #510 has additional details not present in the handoff prompt.
- Local inspection of native-test files and docs to confirm current wording before contract is finalized.

Post-process command:

```bash
(export GIT_PAGER=cat; git status; git diff ; git log --oneline main..HEAD; cat ${HANDOFF_DIR}/*) | pbcopy
```
