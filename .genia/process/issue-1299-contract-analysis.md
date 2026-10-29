# #1299 contract analysis

Existing R25§6.1/6.2 defines the behavior unchanged: send accepts an exact
message and returns nil; accepted messages run FIFO serially; a throwing
handler permanently fails, caches its error, discards later queued work and
rejects later sends. Ref unset reads block until a set (§4.2). Existing private
settling observes a terminal boundary (§7); it is not admission synchronization.

The fixture must establish acceptance of1,2,boom,3 before the boom handler can
throw. Its observations remain [[1,2],true,false,true], empty stderr, exit0.
A distinct post-terminal-send check must fail, with no extra callback effect.
No language contract, runtime API, syntax, capability or Core IR change follows.
No fairness or wall-clock timing requirement is added. Authoritative docs stay
within their current implemented scope; fixture evidence must not imply whole
R25 determinism or completed SliceD/E/R29 acceptance.
