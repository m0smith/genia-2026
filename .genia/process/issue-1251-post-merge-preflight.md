# #1251 post-merge verification: documentation pre-flight

Change: retire stale candidate/pending-repair wording after #1270 integration.
Classification: required infrastructure / documentation follow-up, no release expansion.
Branch: issue-1251-post-merge-verification. Owner: Codex verification;
m0smith accountable for semantic-foundation and R29 scope decisions.

## 1. Scope lock
Includes fresh merged-main verification, individual issue acceptance reconciliation,
and evidence-backed corrections to host integration documentation and the descriptive
default_open_functions gap reason. Excludes runtime/spec/capability changes, new
language behavior, test weakening, unrelated cleanup and R29 implementation.

## 2. Authority
STATE Model B declarations, functions/R20, modules and R25 runtime constraints;
RULES 8.5.1; REPL README and README partial Model B boundaries; approved Model B
contract/design; R25 section 6.2; host interoperability and development-container docs.
AGENTS and run-change govern workflow. Issue discussions supply acceptance evidence,
not semantics. No unresolved semantic choice is needed for these factual corrections.

## 3. Maturity
N/A process/docs-only. Python immutable/default-open execution remains partial;
C++ remains bounded; closed functions and ordinary module linking remain unimplemented.

## 3a. Portability analysis
- Portability zone: documentation of existing shared evidence and host limitations.
- Core IR impact: none.
- Capability categories affected: none; only existing gap reason prose changes.
- Shared spec impact: none; existing cases/oracles executed unchanged.
- Python reference host impact: none.
- Host adapter impact: none; selected C++ source and historical contract pin unchanged.
- Future host impact: none; no new requirement or capability claim.

## 4. Contract and implementation
Portable authority stays STATE and shared R16 cases. Python executes immutable
bindings and local ordinary default-open functions. C++ implements its declared
bounded R27 surface and reviewed local guard/capture corrections. Ordinary linking
and closed publication remain D/E obligations. No contract/design change is needed.

## 5. Verification strategy
Execute fresh full Python/C++ external-host conformance and known-gap parity at
09804b565a30c2995a7d045d74faf8e880994ff4 with C++1f338866. Preserve every actual
failure class; no retry-to-green. Inspect hosted checkout identity and results,
native C++ and Docker integration, Model B/R20/module/REPL/CLI/IR/Outcome/Flow,
docs/registry/profile/reference checks and normal10s bounded #1299 stress.
After prose correction rerun relevant doc/registry/generator/lint and staged
MkDocs checks; verify gap JSON differs only in its descriptive reason.

## 6. Examples
Minimal example: existing grouped-header capture returns [0,10]. Realistic example:
existing FIFO/fail-stop fixture returns [[1,2],true,false,true]. Both are existing
shared evidence, unchanged; no runnable documentation example is added or edited.

## 7. Complexity
No implementation complexity. Correct current statements while retaining historical
failed-run evidence; avoid adding an independent report under docs/.

## 8. Cross-file impact
Expected files: docs/host-interop/HOST_CAPABILITY_MATRIX.md,
docs/architecture/development-container.md, spec/known_host_gaps.json.
Risk: medium evidence/provenance drift; behavioral risk none.
Review STATE/RULES/REPL README/README/AGENTS, registry, reference, book,
cheatsheets and roadmap; do not rewrite unchanged semantics.
MCP language-knowledge impact: none. Repair changes fixture admission ordering,
not language facts/profile; generated-profile --check remains required.

## 9. Philosophy
Preserves minimalism: YES. Avoids hidden behavior: YES. Keeps semantics out of
adapters: YES. Pattern-matching-first: YES. Validated-pipeline priority: YES,
through required foundation verification; no new feature is proposed.

## 10. Phases
Pre-flight -> documentation -> audit -> distillation. Runtime contract/design,
failing-test and implementation phases are N/A: existing semantics and tests are
unchanged. User explicitly authorizes verification, necessary focused correction
PRs, publishing and criterion-satisfied individual closures. Handoffs are ignored
temporary artifacts; durable factual evidence remains in this process directory
and the issue report, never as process narrative under docs/.

## 11. Host parity
Affected executable hosts: none. Evidence covers Python and C++.
Portable semantics changed: NO. One host may merge first: N/A; no host code change.
Existing issue-backed gaps, capability values and removal conditions remain fixed.

## 12. Decision
GO for verification and bounded factual documentation correction only.
Closures depend on observed results and individual criteria. #1251/R29 remain
gated by D/E and explicit prerequisite/scope disposition. No assumption of release
acceptance follows from Slice C. Reviewer: Codex, 2026-10-30.
