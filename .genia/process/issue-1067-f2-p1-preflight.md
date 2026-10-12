# F2 P1 planning pre-flight — issue #1067

Date: 2026-10-12. Owner: Codex, for maintainer review.
Branch: `issue-1067-f2-p1-design`; baseline: `b22027bedb0f233222218b4a8772a0a242fe32d5`.

## 1. Scope lock

Includes source inspection, consumer inventory, decision recommendations and a
design-only PR. Excludes test additions, implementation, isolation activation,
contract amendments, P2/P3, F3–F5 and merging. Classification: unnumbered R20
follow-up after R28 and before R29; scope repair supports reliable composition
of validated pipelines. This is the planning gate, not implementation approval.

## 2. Source of truth

STATE §§0, 4, 4.7, 7, 8, 9 and native-test/CLI sections govern current behavior;
RULES §§8–8.5 govern dispatch/modules; REPL README and README remain subordinate.
Read AGENTS, the four authority documents, run-change, roadmap-ticketing,
killer-workflow, release-roadmap, F2 P0 and R20 contracts; inspect #1067 comments
and merged #1204/#1206. P0 is proposed future behavior, not implemented truth.
Resolve D2b, reflection mechanism and fallback deadline through recommendations,
not by amending the approved proposal silently.

## 3. Maturity

N/A — design/process only. Current runtime maturity and host claims unchanged.

## 3a. Portability analysis

1. Authority/boundary: STATE for today; F2 P0 for the proposed lexical scope
   boundary. No observable portable change in this PR or intended P1.
2. Representation: existing lexical environments and ordinary callable values;
   no parser, AST, Core IR or protocol change proposed for P1.
3. Shared evidence: existing CLI/import/open/reflection cases must be retained;
   future P2/P3 semantic cases use R16 multi-file inputs. No specs added now.
4. Applicability: existing `multi_file_eval`, `open_functions`, `doc_help`,
   `cli_main`, `repl`, `cli_pipe_mode`; no new capability proposed.
5. Hosts: Python consumer preparation; C++ has unsupported modules/reflection,
   so no C++ implementation change now. Local checkout `8720440` is older
   evidence, not a claim about latest remote C++ main.
6. Capability/evidence impact: none now; later portable evidence must retain
   explicit C++ unsupported/gap reporting through existing R16 machinery.
7. Truth synchronization: none now; later behavioral phases synchronize STATE,
   RULES, REPL README, README, book/cheatsheets and applicable semantic guards.

## 4. Contract versus implementation

Python uses one runtime/entry root, module children and root-bound reflection.
P1 prepares access without separating those environments. P0 decisions D1/D3/D4
are settled; mechanism and D2/D2b finality remain for review. The prelude write
repair is already merged; do not repeat it. C++ module/reflection support is
outside its bounded floor. No new behavior is implemented by this plan.

## 5. Verification strategy

Design validation: source-reference/link checks, diff whitespace and existing
semantic-documentation guards. No new tests. Future P1: pin current REPL and
module-debugger output first, accessor/classification failures before their
implementation, then CLI/native/server/import/MCP regressions and both full
suite partitions. Future semantic phases require shared evidence first.

## 6. Examples

Design matrices use classified, non-executable call scenarios: `rows/0` versus
runtime `rows/1`, fixed/varargs selection and passing a reflective callable
between units. No runnable user-facing examples are changed.

## 7. Complexity

Revealing existing structure: distinguish entry, declaring unit and runtime
access. Reject a blanket replacement of root access or a new scope manager.
Reflection/shadowing activation stays outside behavior-preserving P1.

## 8. Cross-file and MCP impact

This change adds one durable design note and this process record outside docs.
Future affected files are inventoried in the note. Drift risk: medium for the
design, high for later migration. MCP knowledge impact: none now, because no
language fact, tool or implemented behavior changes. P2/P3 must reassess.

## 9. Philosophy

Minimalism, explicit behavior, pattern-first design and adapter boundaries:
YES. Approved infrastructure repair strengthens composition without new syntax.

## 10. Phase plan

Pre-flight → design-only PR → maintainer decisions. Stop there. Each later
authorized slice follows its own applicable contract/design, failing-test,
implementation, documentation, audit/distillation gates. Existing-behavior
characterization tests may pass initially; new accessor/host-injection contracts
need failing evidence before implementation. No tests or implementation now.

## 11. Host parity/conformance

Affected now: neither runtime. Intended P1: Python internals only, no portable
semantic change; C++ consumers retain their current claims. Later isolation and
reflection semantics must have shared evidence before host work. No new gap
entry is required for this design-only PR; existing unsupported areas remain.

## 12. GO / NO-GO

GO for this authorized planning/design PR; NO-GO for tests or implementation.
Maintainer review must decide D2/D2b, the reflection mechanism and the deadline
amendment before dependent phases. D1/D3/D4 and the merged prelude repair need
no renewed decision. Reviewer/decision date: pending.
