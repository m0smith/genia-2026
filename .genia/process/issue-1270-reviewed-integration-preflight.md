# Slice C reviewed-dependency integration pre-flight

## Identity and scope

Issue/parent: #1269 / #1270; truth-audit gate #1251. Owner: Codex, with
maintainer-controlled integration. Branch: issue-1270-reviewed-integration.
Authorization: the uploaded integration request explicitly authorizes preparing,
validating and integrating reviewed #1294 and the merged C++ #58 into #1270's
feature branch, respecting checks/protection. No merge of #1270 into main.

Includes reviewed documentation commit 51e7b8d76588e8c82198531b31d2e2b4495d26c5,
intentional C++ implementation pin 78e61181a2c9ce32c33060b936b662c2f65ab2f0,
host documentation alignment and fresh integration evidence. The Docker proof
workflow independently pins the old C++ host; synchronize that checkout too so
its unchanged full shared suite tests the same reviewed implementation.
Excludes runtime/optimizer changes, shared-oracle/capability/comparator changes,
the old proposal's MCP timing-test change, Slice D/E, lifecycle fixes and R29.

## Authority, maturity and implementation

Read latest AGENTS first; STATE is final authority, then RULES, REPL README,
README, shared specs, host-interop and architecture. Relevant boundaries are
STATE host status and function/REPL sections, RULES 8.5.1, R26 REPL contract,
R20 explicit-open contract, R16 protocol/conformance policy and maintained-code
documentation policy. Strategy: reliability of validated data-pipeline helpers.
Maturity remains Partial cross-host / bounded R27 C++; Python is the full-language
reference host. No semantic ambiguity or new contract is introduced here.

C++ #58 merged at 930ea94c0407ee3d150d131a05e1b5f27560e256, containing the
independently reviewed implementation pin above. Its ordinary header capture,
duplicate/alias rejection, inert inline metadata, fixed-arity accumulation,
semicolon REPL and parser-depth repair already implement existing contracts.
Default-open ordinary functions, immutable bindings and doc_help stay unsupported
in C++. Python Slice C behavior and optimizer remain unchanged.

## Portability analysis (all seven fields)

1. Authority/boundary: existing STATE/RULES/REPL contracts; E16 source-to-protocol
   observations and minimal portable Core IR; no alternate semantic authority.
2. Representation: unchanged shared YAML, protocol, diagnostics and normalization.
3. Shared evidence: full 1,044-case suite for each host at combined final HEAD;
   previous 293/751 C++ and 1,026/18 Python counts are comparison evidence only.
4. Applicability: unchanged spec/manifest.json vocabulary and requires gates.
5. Claims: no capability transition; legitimate unsupported cases remain explicit.
6. Gaps: existing issue-backed host gaps unchanged; no FAIL is reclassified.
7. Truth synchronization: STATE, REPL README, README, host matrix and function
   chapter reflect only verified bounded host behavior; evidence records exact
   revisions. MCP knowledge impact: none, no new language fact/profile member.

## Validation, examples and failure handling

Run full shared conformance, hosted Python/C++ parity with fresh evidence,
Python regression/unit tests including both socket partitions, maintained-code
coverage, strict docs/semantic sync, LLM checks, MCP acceptance and Docker proof.
Examples are existing shared cases, not new executable documentation: grouped
header capture and complete `1; 2` REPL submission (portable existing behavior).
Native deep-declaration probes are C++ host-only safety evidence.
Retain workflow URLs and both parity artifacts. Actual failure classes must be
zero. Investigate separate baseline failures and obtain explicit disposition;
do not alter unrelated behavior or tests to make integration green. Preserve
the distinction between unbaselined R28 SIGINT and baseline discovery-cleanup
observations. Keep STATE within 43,000 words.

## Complexity, philosophy, phase plan and GO

No runtime complexity; medium cross-file documentation/workflow drift risk.
Synchronize duplicate host checkout pins rather than introduce a new registry.
Preserves minimalism, explicit behavior, pattern matching and host boundaries;
strengthens reliability of the existing validated-pipeline workflow.
Phases: recorded pre-flight, focused pin/docs implementation, validation,
independent final-head review, then checked integration into #1270's feature
branch. Contract/design/RED phases are reused from reviewed dependencies: no
new behavior is implemented. Both hosts affected only through integration proof.
C++ is already merged; no temporary semantic gap is created by this ordering.
GO for the explicitly authorized integration, 2026-10-28. Independent truth audit
and required checks still gate acceptance. No self-approval, branch-protection
bypass, #1270 main merge, semantic-foundation completion or R29 authorization.
