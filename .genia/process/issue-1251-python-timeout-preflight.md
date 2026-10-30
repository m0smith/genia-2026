# Python timeout investigation pre-flight (#1251/#1299)

Owner: Codex Worker A; independent documentation Worker B owns #1302.
Branch: issue-1251-python-timeout-investigation. Classification: required
infrastructure investigation; no language/release expansion. User explicitly
authorizes finite diagnostics, warranted focused remediation, independent review,
evidence publication and criterion-based decisions; no automatic issue closure.

1. Scope: preserve original1+6TIMEOUT results; discriminate CPU contention,
startup/evaluation cost and adapter/evaluator cancellation/reaping. Independent
#1302 review has separate ownership. Exclude R29, D/E implementation, oracle,
deadline, capability, baseline and failure-class changes.
2. Authority: STATE Model B/functions/R20 and R25 FIFO/fail-stop; RULES8.5.1;
REPL README/README supported surfaces; R16 protocol/evidence and R25section6.2;
run-change, test/audit/maintainability/portability and roadmap controls. No
ambiguous semantic decision is authorized through a host diagnostic.
3. Maturity: N/A infrastructure. Current partial Python/C++ scope stays fixed.
3a. Portability: zone host/tool orchestration; Core IR impact none; capability
categories none; shared specs unchanged and executed; Python adapter/runtime
unchanged during diagnostics; host adapter impact observational only; future
hosts inherit no new semantic requirement. Any production repair gets a bounded
additional contract/RED/design analysis once a cause is established.
4. Existing implementation: one adapter subprocess per canonical request;
Python eval can spawn a second interpreter. Timeout10s currently kills direct
adapter via subprocess.run; descendant ownership must be measured, not assumed.
5. Finite matrix is frozen in evidence/experiment-plan.json before execution:
291 targeted requests across isolated/scaling1,2,4,8/controlled2CPU-burner/recovery
phases; one full1044-case normal8-worker diagnostic;12startup/eval phase probes;
one synthetic10s transport lifecycle probe with15s child. All outcomes, wall/CPU
and cgroup counters retained. No failed request is retried/reclassified. Sample
counts do not change in response to results. Acceptance is separately reserved
for one full Python/C++ pair,200Python/1000C++fixture and8R20 requests after
cause/remediation, no unrelated CPU load, original10s, concurrency chosen once
from evidence and capped2. Finite success does not prove determinism.
6. Examples: original R20 linked-view20,000-tail-call and R25fixture unchanged.
Synthetic transport probe is infrastructure-only, never language conformance.
7. Complexity: diagnostics reuse canonical transport/comparator; optional
observation side channels never alter JSON/oracle. No replacement runner or
new semantic evidence mechanism. Avoid implementation until cause justified.
8. Cross-file impact: initially process evidence/support only; any warranted
orchestration correction is separate from #1302. Root authority, book,
cheatsheets, registry and profile need no expansion for mere resource findings.
MCP knowledge impact none unless a later justified semantic change is proposed.
9. Philosophy: minimalism/visible behavior/host boundary/pattern-first and
validated-pipeline foundation preserved. All YES; no feature proposed.
10. Phases: preflight->finite diagnostics->cause decision->bounded repair only
if warranted->RED/implementation/GREEN/docs->independent review/audit. This
pre-flight permits diagnosis, not guessed implementation. Existing historical
failures remain evidence even if later acceptance is green.
11. Host parity: Python/C++ executable semantics unchanged; final applicable
canonical parity remains required. No new gaps/downgrades. Merge-before-other
host N/A for observation/orchestration only.
12. GO for bounded investigation,2026-10-30. Stop if semantics, an oracle change,
deadline increase or new runtime behavior is required without separate analysis.
Main09804b/treef8a686c is frozen in /workspace/work/1251/main for measurements;
this branch records process/repair work and never modifies Worker B's checkout.
