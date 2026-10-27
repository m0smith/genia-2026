# Deliberate C++ host-parity pin proposal

Status: prepared for review; not merge authorization.

- C++ repair PR: https://github.com/m0smith/genia-cpp/pull/58
- Exact C++ revision: `8b4f3178d77a0ea7da792bf090d3f53bb54ab9e7`.
- Prior workflow pin: `44456baea06b4bb7bdf727e39939dd7150261ee6`.
- Authority base: `aebaa9949fcdc8fa4fbe9abfdb175808f6982186`, the exact
  merge revision from failing host-parity workflow 40582524750.
- This isolated branch is stacked on that CI merge revision. It does not edit
  the Python Slice C branch and must not be merged independently into main
  ahead of the approved Slice C integration sequence.

Scope: change only the deliberate C++ workflow checkout pin and claims affected
by verified repairs in STATE, REPL README, README, function chapter and host
capability matrix. No Python production, language contract, shared expected
result, capability registry, comparator or known-gap changes.

Evidence: clean C++ CTest 4/4; exact suite 293 PASS / 0 FAIL / 751 UNSUPPORTED;
all other failure classes zero. Python protocol reference: 1026 PASS / 18
UNSUPPORTED; all failure classes zero. The unchanged local host-parity gate
actually runs and reports OK. Pinned C++ contract suite: 793 total / 261 PASS /
0 FAIL / 532 UNSUPPORTED; all other failure classes zero.

Pre-flight/portability scope is the authorized existing-contract repair in
C++ PR #58 (`.genia/process/issue-53-57-preflight.md`). This proposal changes no
semantics or MCP language knowledge; its profile generator check passes.
The authoritative docs' targeted checks pass: 244 passed / 34 skipped.
STATE remains at 42,996 words against its 43,000-word gate.

Before adopting the pin, obtain the independent C++ maintainability and
behavioral/documentation truth review, rerun final-head host-parity CI with this
explicit C++ SHA, verify that its gate step executes and passes, and retain
both hosts' evidence. Hosted final-head parity is pending; local gate success
is not represented as a completed hosted CI run. Keep #53-#57 open until their
acceptance conditions are independently evidenced. Do not merge #1270 or begin
R29 as part of this proposal.
