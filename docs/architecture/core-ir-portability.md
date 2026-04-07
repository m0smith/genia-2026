# Core IR as the Portability Boundary

Genia's portability story should center on Core IR, not on any one host's parser classes or runtime objects.

Python is the current reference host.
This note explains why future hosts should align at the Core IR boundary.

## Why the Parser Is Not the Final Boundary

Different hosts may want different parser implementations:

- recursive descent
- parser combinators
- generated parser tooling
- hand-written tokenizer plus Pratt/precedence parser

Those internal choices are fine.
What must not drift is the meaning of the lowered program.

If two hosts parse the same surface program but lower it differently, they no longer implement the same language.

That is why surface AST shape alone is not enough.
The portable contract is the meaning after lowering into Genia's tiny Core IR.

## Why Shared Lowering Matters

Genia already relies on lowering for important language behavior.

Examples:

- explicit pipeline stage sequencing
- explicit Option constructor representation
- case/body normalization
- Core evaluator entry behavior

If lowering drifts, then evaluation drifts even when the evaluator looks "mostly the same."

Future hosts should therefore validate:

- parse behavior
- IR snapshots
- evaluated behavior after lowering

## Why Runtime Builtins Should Be Capability-Backed

Host resources are real, but they should stay at the edge.

Examples:

- stdin/stdout/stderr
- argv
- process/thread/mailbox substrate
- refs/synchronization
- bytes/json/zip bridges
- debugger transports

These are host responsibilities.
They should not become the place where public language semantics accumulate.

Instead:

- host code provides a small capability bridge
- public stdlib behavior prefers prelude/Genia code when feasible
- shared semantics live above the capability layer

This keeps the language more portable and makes future direct/native compilation easier.

## Why Shared Evaluation Semantics Matter

Hosts may use different execution strategies:

- direct interpreter
- bytecode VM
- compiled IR
- trampolined evaluator

Those choices are host-local.

Shared semantics still need to match for:

- value results
- stdout/stderr output
- CLI behavior
- Flow behavior
- normalized errors
- public prelude helper behavior

Core IR is the cleanest place to compare those behaviors.

## What Should Remain Host-Neutral

The following should stay host-neutral as Genia grows:

- Core IR meaning
- lowering semantics
- public prelude helper semantics
- shared error wording/prefixes relied on by docs/tests
- CLI mode contract
- Flow contract
- capability names and their Genia-level observable behavior

## Current Status

Implemented today:

- Python host/parser/lowering/evaluator
- documented Core IR portability direction
- shared spec scaffolding

Not implemented today:

- second host implementation
- generic multi-host spec runner implementation
- direct/native host

The portability boundary is therefore documented and scaffolded now, while Python remains the only working host.
