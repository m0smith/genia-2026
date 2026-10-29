# #1299 deterministic R25 fixture admission preflight

Owner: authority conformance/test-runtime maintainer (m0smith accountable).
Branch: issue-1299-deterministic-fixture; base 79c073b556ad16343051d545d7928248a6d0f6b0.
Classification: required infrastructure for #1251/#1270; no release or language expansion.

## Scope lock
Repair only the shared r25-process-fifo-fail-stop fixture's admission ordering;
preserve its expected observations and prove terminal sends still reject. No
Process/Cell runtime, scheduler, oracle weakening, sleeps, retries, timeout
increases, capability changes, or unsupported reclassification. Historical
failures remain evidence: old966/34 and reviewed970/30 across1000 requests;
independent198/2 on each across200; prior full294PASS/1FAIL/749UNSUPPORTED.

## Authority and current implementation
STATE host-backed concurrency, RULES§10 and R25 contract§6.1/6.2/7 define FIFO
accepted messages, fail-stop discard and later-send rejection. Shared spec uses
refs/process_primitives plus existing private r25_concurrency settle fixture.
Python/C++ already implement these operations; an idle call after sends cannot
order earlier admission. No contract ambiguity or new runtime behavior needed.

## Portability analysis
- Zone: existing portable runtime observations, test-fixture repair.
- Core IR impact: none.
- Capability categories: existing refs/process_primitives; no additions.
- Shared spec: update admission ordering, unchanged expected stdout/stderr/exit.
- Python reference impact: no implementation changes; host-scheduling regression tests.
- Host adapter impact: none; existing fixture settle and Ref semantics suffice.
- Future hosts: same ordinary Ref handshake and existing capabilities; no scheduler assumptions.

## Executable conformance obligation
Portable authority is R25§6 and STATE; boundary is opaque handles/ordinary calls.
Shared FIFO/fail-stop case remains executable on both hosts. Post-failure rejection
uses host boundary checks because current Python/C++ normalized diagnostic wording
differs; no new universal exact text is invented. Capability claims unchanged.
Five authoritative documents and host docs inspected; only verified fixture
causality/evidence notes may change; no expansion of language truth.

## Test strategy and examples
Reproduce old source in bounded once-only batches on prior/reviewed binaries.
RED: host-scheduling regression drives boom handler to blocking Ref or terminal
failure before allowing root's later send; original shared source must fail.
GREEN: release an unset Ref only after all expected sends return; verify exact
[[1,2],true,false,true] and discarded3. Independent negative send after settled
failure must retain error/exit1. Stress corrected source in bounded batches with
all outcomes retained; full shared/conformance/CI handled by integration gate.

## Complexity and cross-file impact
Reveals existing causality using ordinary Ref; no new fixture API. Alternatives:
removing send3 weakens discard proof; waiting idle earlier loses queued-work
coverage; sleeps/retries prohibited. Files: shared case, Python host regression,
process evidence. Risk medium (hung incorrect handshake), bounded by existing
harness safety. No production timeout changes.

## Documentation/MCP/philosophy
MCP knowledge impact none: no language/profile/capability semantics change.
Preserve five authority documents' implemented scope and STATE word limit.
No book/cheatsheet runnable example changes. Strengthens trusted portability
infrastructure underpinning validated pipelines; minimal, explicit, host-neutral.

## Prompt plan / GO
User explicitly authorizes preflight→contract analysis→design→committed RED→
minimal repair→GREEN/stress→independent maintainability/audit→docs/distillation.
Temporary handoffs remain ignored; durable evidence here, never under docs/.
GO for this bounded contract-preserving repair; no main/#1270 merge authority.
