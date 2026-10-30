# Bounded adapter cancellation contract analysis

The synthetic10s diagnostic confirms that direct adapter termination leaves an
owned evaluator descendant alive after the request is classified TIMEOUT. This
is a conformance transport resource-ownership defect, independent of whether it
caused any original Genia timeout. Existing R16 wire envelopes, case selection,
normalizers/comparators, semantic observations, capability claims and request
deadlines remain unchanged. STATE stays final language authority.

On POSIX, one adapter request owns a fresh process group. On timeout or caller
cancellation, terminate that group and reap the direct adapter. Preserve partial
timeout diagnostics and the original classification/deadline. This bounds
same-group child work after cancellation; it is not a sandbox, does not cover
deliberately detached descendants and does not promise that this process can
reap grandchildren it does not own. No new Genia lifecycle/Process semantics or
general operating-system process-tree API is introduced. Existing non-POSIX
direct-process cancellation remains unchanged and is explicitly outside this
bounded correction. Successful requests retain current behavior.

Portability: host-neutral transport orchestration with POSIX realization;
Core IR none; protocol/capability vocabulary none; shared semantic specs
unchanged; Python/C++ request launches both use the existing generic path.
No host may fabricate semantic differences to fit this correction. Root docs
and MCP language profile require no new semantic fact. Tool documentation must
state the POSIX group boundary and limits honestly.

The original1+6timeouts remain retained and their original causal attribution
remains unresolved:291 targeted diagnostics pass, imposed CPU/concurrency
increases latency without reproducing10s failures. Historical memory events
cannot be linked to those requests. This correction addresses the demonstrated
surviving-child mechanism, not a fabricated complete historical root cause.
