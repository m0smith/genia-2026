# R24 C++ Minimal Host Pre-flight

Status: **Planning contract — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

Historical note: this contract was originally drafted as **R21-0** (issue
`m0smith/genia-2026#814`, "establish C++ minimal-host pre-flight"). Planning
issue `#845` decomposed the Exact Numeric Model into three numbered
releases (R21, R22, R23) and moved the C++ host to **R24**. Issue `#814`
was retitled to `R24-0` and closed as completed (PR `#815`) under the old
numbering; this file is the renumbering cleanup that old issue explicitly
deferred. The pre-flight intent, and every substantive rule below, is
unchanged by the renumbering.

This document defines the implementation discipline for the first real C++ host in `m0smith/genia-cpp`. It does not add language semantics, Core IR nodes, host capabilities, or C++ implementation behavior.

## Purpose

R24 should be an implementation exercise against already-approved portable semantics, not a venue for inventing new Genia behavior.

The C++ host MUST consume the authoritative contract from `genia-2026`, record the exact contract revision it implements, and stop rather than guess whenever the portable contract is ambiguous.

## Entry prerequisites

R24 semantic implementation MUST NOT begin until:

- R16 multi-host conformance infrastructure remains green and usable by an external host
- R17 numeric and ordered-map portability is complete
- R18 portable value equality is complete
- R19 Unicode and diagnostic portability is approved and complete
- R20 open functions / extensible pattern dispatch is approved and complete
- R21 (numeric source and portable representation), R22 (exact numeric runtime), and R23 (numeric representation and interchange) — the decomposed exact-numeric-model releases — are approved and complete before C++ numeric semantics are implemented
- the target `genia-2026` contract revision is pinned in `m0smith/genia-cpp`

**Status as of this refresh (2026-09-19): all of the above are satisfied.**
R16 through R23 each carry a recorded skeptical release-truth-audit PASS
(`docs/analysis/r16..r23-release-truth-audit.md`, `docs/releases/R16.md`
through `R23.md`), and `GENIA_STATE.md` §4 records each as complete. R23's
audit trail (`docs/analysis/r23-release-truth-audit.md`) shows two genuine
findings (E23-7, E23-9) caught and repaired before the third independent
audit (E23-11, `#939`) recorded PASS — this is the entry prerequisite
working as intended, not an open gap.

Toolchain/bootstrap work that does not interpret Genia semantics may proceed earlier, but MUST NOT claim host conformance.

## Post-R23 architecture note (P8/P9)

`P8` (alternate-provider substitution proof) and `P9` (Genia↔WIT
interoperability mapping and toolchain proof) landed after R23 as
Provider Composition work-ledger items (`docs/strategy/roadmap/
provider-composition.md`). Both are explicitly non-authoritative design
proofs that changed no Genia semantics and no Core IR. Neither expands or
narrows R24 scope: `provider-composition.md` states its track is relevant
to planned R32/R35/R36/R37 and does not change the numbering or scope of
other releases. R24's non-goals (below) are unaffected — WIT/provider
interoperability is explicitly **not** pulled forward into the minimal
C++ host merely because P8/P9 now exist.

## Repository boundary

Production C++ implementation belongs in `m0smith/genia-cpp`.

`genia-2026` remains authoritative for:

- language semantics
- Core IR contract
- shared spec cases
- host-adapter protocol
- capability names and meanings
- conformance evidence rules

The C++ repository may document implementation choices, but MUST NOT copy semantic documents in a way that can diverge into a competing source of truth.

## 1. Minimal capability floor

Before implementation, R24 MUST define a machine-checkable minimal capability set and the exact shared cases expected to be applicable.

Rules:

- capability support is evidence-based, never aspirational
- unsupported behavior MUST report `unsupported`; it MUST NOT be partially interpreted and counted as passing
- conformance claims MUST use exact applicable/pass/fail/unsupported counts
- capability growth happens only when implementation and shared evidence both exist
- mixed-capability categories MUST NOT be claimed wholesale merely because a subset passes

The first capability floor should remain deliberately capability-light and centered on parse, Core IR, eval, error, and minimal non-interactive CLI behavior.

**The pinned machine-readable declaration is `docs/design/r24/capability-floor.json`.** It distinguishes capabilities the generic `spec/manifest.json` marks `required` for any host from those it marks `optional` but that this pre-flight makes mandatory for R24 completion specifically (`open_functions` is the working example: optional in the generic manifest, mandatory here because R20 is an entry prerequisite).

## 2. Mandatory implementation layering

The semantic path MUST remain:

```text
source
  -> parser
  -> portable Core IR
  -> evaluator/runtime
  -> normalized host-adapter result
```

Rules:

- no parser-to-runtime semantic shortcuts
- no C++-only AST semantics that bypass portable Core IR
- no host-local optimized IR may appear in normalized portable IR evidence
- lowering must target only approved portable Core IR nodes and fields
- host optimization, if added later, occurs after portable lowering and must preserve observable behavior

Core IR is the portability firewall.

## 3. Prelude/bootstrap policy

The default rule is:

> Use the same Genia prelude in every host wherever feasible; native host code supplies primitives/capabilities, not duplicated public semantics.

Before implementation begins, classify each dependency needed by the minimal host as one of:

- portable Genia/prelude behavior
- required host primitive
- deferred/unsupported capability

Any public behavior implemented natively in C++ instead of through the shared prelude requires an explicit written justification and shared conformance evidence proving equivalence.

## 4. Native primitive boundary

R24 MUST publish the initial native primitive inventory in `m0smith/genia-cpp` before broad evaluator work.

**The pinned inventory for this refresh is `docs/design/r24/native-primitive-inventory.md`.**

The inventory MUST state for each primitive:

- why the primitive must be host-native
- its portable input/output contract
- normalized misuse/error behavior
- whether it is public, prelude-internal, or adapter-only

Native primitives MUST NOT silently add user-visible semantics absent from the authoritative Genia contract.

## 5. Diagnostic normalization boundary

C++ implementation/runtime/library exception text is never portable Genia diagnostic text by default.

The C++ host MUST normalize failures at the appropriate boundary before returning shared conformance results.

Forbidden as portable output unless explicitly contracted by R19:

- STL exception wording
- compiler/runtime-specific type names
- OS/library error strings
- filesystem/library implementation details
- demangled C++ symbols

R19 defines the portable Unicode/string and diagnostic surface. R21-R23 define Decimal/Rational/Float64 semantics and rendering. R24 implements both; it does not infer either from C++ defaults.

## 6. Vertical bootstrap suite

Before broad feature expansion, the C++ host MUST pass a deliberately small vertical slice proving the entire path:

```text
parse -> lower -> eval -> normalize -> generic R16 runner
```

The bootstrap suite MUST be selected from existing shared cases and MUST include representative coverage for:

- literals
- exact integer arithmetic
- list construction/use
- ordered-map behavior
- equality and legal-key behavior
- Outcome values
- lambda/function call
- pattern/case dispatch
- pipeline composition
- one deterministic runtime/error case
- one `-c` command-mode case
- one file-mode case (file mode is part of the declared floor — see capability floor)
- approved R20 function-group/open-function behavior before R24 completion

**The pinned case list is `docs/design/r24/bootstrap-cases.json`** (exact
existing `spec/*/*.yaml` case IDs, one file per category above, resolved
against this refresh's pinned `genia-2026` revision). Expansion happens in
small evidence-backed increments; the file documents how the inventory
grows without allowing capability claims ahead of evidence.

## 7. Dependency policy

Before semantic coding, `m0smith/genia-cpp` MUST document choices for at least:

- build system
- C++ language version
- package/dependency management
- unit-test framework
- formatting/linting
- JSON protocol handling
- arbitrary-precision integer representation
- Unicode support strategy
- ordered-map representation strategy

**The pinned decisions are `docs/design/r24/dependency-toolchain-policy.md`**, mirrored into `m0smith/genia-cpp/AGENTS.md`.

The Genia contract MUST NOT depend on those library choices. Libraries implement approved semantics; they do not define them.

## 8. Differential/conformance testing policy

Python is the reference host, but Python implementation source is not the specification.

Allowed:

- running both hosts through shared R16 conformance cases
- comparing normalized evidence
- using `GENIA_STATE.md`, `GENIA_RULES.md`, Core IR docs, approved design contracts, and shared specs as semantic sources

Forbidden:

- copying Python algorithms because their behavior is undocumented
- treating Python container/runtime/library defaults as Genia semantics
- reading Python implementation details to settle an ambiguous language question
- adding C++ behavior solely to mimic an uncovered Python accident

When reference-host behavior and written portable truth disagree, the discrepancy is an upstream contract/spec problem to resolve in `genia-2026`.

## 9. Ambiguity-stop rule

If C++ work encounters behavior that cannot be determined from the authoritative contract and applicable shared evidence:

1. stop the affected C++ semantic implementation
2. do not guess and do not copy Python internals
3. open/resolve the semantic question in `genia-2026`
4. update the appropriate contract/source-of-truth and shared evidence through the normal change gates
5. pin the resulting `genia-2026` revision
6. resume C++ implementation

No host-specific interpretation may become de facto Genia semantics merely because it was implemented first.

## 10. Work-unit discipline

R24 should progress as narrow vertical increments.

Each semantic increment should contain:

- exact capability/cases targeted
- contract references
- failing conformance evidence before implementation where practical
- minimal implementation
- conformance evidence after implementation
- capability declaration update only after evidence passes

Avoid repo-wide feature batches that combine parsing, evaluation, CLI, diagnostics, and unrelated runtime behavior in one implementation step.

## 11. Explicit non-goals for the minimal host

Unless the R24 roadmap is explicitly revised through its own gate, the first minimal C++ host does not need:

- pipe mode
- REPL
- Flow runtime parity
- refs/cells/processes/actors
- storage/resource IO beyond the minimal file-mode bootstrap required by R24
- external/distributed execution
- HTTP serving or outbound HTTP
- configuration/secret provider parity
- AI/retrieval provider capabilities
- WIT/provider interoperability (P8/P9 do not change this — see the post-R23 architecture note above)
- browser runtime
- host-specific interop convenience

These capabilities must not delay the first capability-light conforming host.

## 12. Completion evidence

R24 completion requires:

- exact pinned `genia-2026` contract revision
- declared C++ capability set
- exact applicable shared-case inventory
- deterministic R16 evidence from the generic external-host runner
- zero failed applicable cases for the claimed minimal capability set
- explicit unsupported counts/reasons for everything outside that set
- no unresolved semantic ambiguity discovered during implementation
- documentation in both repositories consistent with their authority boundaries

## Final go/no-go

**R24 SEMANTIC IMPLEMENTATION: GO**, as of this refresh (2026-09-19),
subject to the four mandatory entry artifacts pinned alongside this
document:

- `docs/design/r24/capability-floor.json`
- `docs/design/r24/bootstrap-cases.json`
- `docs/design/r24/native-primitive-inventory.md`
- `docs/design/r24/dependency-toolchain-policy.md`

R16-R23 are complete and audited, P8/P9 do not expand R24 scope, and
`m0smith/genia-cpp` has no C++ code yet — this GO authorizes drafting the
dependency-ordered E24 implementation ticket sequence
(`docs/strategy/roadmap/e24-issue-sequence.md`). It does **not** authorize
or constitute C++ semantic implementation itself, which begins only once
the first E24 ticket is picked up.

The governing rule is:

> C++ implements Genia. C++ does not decide what Genia means.
