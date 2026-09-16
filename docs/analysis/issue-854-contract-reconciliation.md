# Issue #854 Contract Reconciliation — E21-2

Status: process artifact. Reviewed the approved
`docs/design/r21-numeric-source-portable-representation-contract.md` §4
against issue #854's scope.

Finding: no contract change is required. §4.1/§4.2 already fully specify
the Integer and Decimal tagged `IrLiteral` payload shapes and Decimal
canonicalization rule. The contract's §4 also already states unary minus
and `/` remain unaffected, matching this ticket's scope exactly.

One clarification recorded (not a contract change): the contract is silent
on evaluator compatibility because R21 is a source/Core-IR release and the
evaluator's runtime numeric materialization is R22's boundary. Per the
`GENIA_RULES.md`/`AGENTS.md` precedence rule that `GENIA_STATE.md` is final
authority for *implemented* behavior, and per issue #854's own instruction
("If evaluator assumptions break ... do not silently implement R22 runtime
semantics. Handle only compatibility legitimately inside the R21 Core-IR
boundary"), this ticket adds the smallest possible evaluator shim: unwrap
the new tagged payload back to the exact same `int`/`float` the evaluator
already produced before this ticket, with zero new runtime numeric kind,
arithmetic rule, or conversion semantic. This is compatibility work
strictly caused by E21-2's own payload-shape change, not new R22 behavior.

No contradiction found between `GENIA_STATE.md`, `GENIA_RULES.md`, and the
R21 contract for this slice. Proceeding to design.
