# Bounded cancellation correction: GREEN and review

Committed RED0d5b77ec: timeout+caller-cancel FAIL, successful-request control
PASS,5.32s. Minimal implementation9c67cb67: original caller timeout/taxonomy/
partial diagnostics stay unchanged; POSIX starts a private adapter session and
kills its group on cancellation, reaping the direct adapter; non-POSIX retains
the original direct-process path; detached descendants are outside the guarantee.

Fresh focused protocol/newcleanup/Python-adapter selection:56PASS/4.04s.
Nearby host-executor/capability/evidence selection:55PASS/1.24s. Ruff changed
Python files:PASS. Maintained-code checker9970records/2793legacygaps/1exclusion/
0errors against main09804b; no baseline change. Registry/doc/portability
selection244PASS/34existing skips; profile generator--checkPASS; staged strict
MkDocsPASS8.80s; whitespacePASS. Existing skip markers/oracles/defaults unchanged.

Independent reviewer C authored no repair changes and inspected actual helper,
caller, RED test, contract/design and correctionb55eeb93. Scoped static
maintainability/behavior PASS at9c67cb; observed RED/GREEN logs independently
checked. Final docs/head and predeclared full acceptance remain separate gates.

Baseline investigation: frozen main09804b/f8a686c, Python3.12.14,2CPU quota,
8GiB memory limit.291targeted diagnostics PASS across finite isolated/scaling/
two-burner/recovery matrix. Full normal8-worker diagnostic1026PASS/18UNSUPPORTED,
all actual failure classes0; R20 request5.258s.9instrumented eval probes PASS;
3capability controls were malformed by diagnostic wrong sentinel and remain
3PROTOCOL_ERROR, not semantic conformance results. Synthetic child remains
live when canonical10s timeout returns10.009s and exits15.048s. These findings
demonstrate cancellation ownership, not the original7timeouts' root cause.

Resource-aware acceptance is chosen once at2workers, original10s deadline,
same oracles and all1044 cases, no other scheduled build/test workload: one full
Python/C++ pair,200Python and1000C++fixture requests,8R20 requests and both exact
postfailure-send negatives. No retry on a failing acceptance result. The old
1+6timeouts remain immutable evidence; finite success alone is not determinism.

Durable tool ownership limits are in tools/spec_runner/README.md; resource
envelope guidance in docs/process/run-change.md. No Genia syntax/runtime/CoreIR,
host capability, registry or five root-authority fact changed; no profile/book/
cheatsheet expansion is justified. A focused correction PR remains separate
from documentation#1302 and does not close #1251/#1299 or authorize R29.
