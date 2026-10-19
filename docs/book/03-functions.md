# Function declaration boundary

Concise implementation reference; `GENIA_STATE.md` section 3 is authoritative.

Ordinary unguarded identifier headers execute through the existing `IrFuncDef`
path. Explicit R20 `open` functions retain their implemented dispatch behavior.

Model B Slice A adds parsing/lowering: immutable bindings use
`IrImmutableBind`, guarded/pattern-headed declarations use `IrPatternFuncDef`,
and consecutive same-name closed clauses use one `IrClosedFuncDef`. These new
nodes other than `IrImmutableBind` reject execution with `model-b-not-implemented`,
before child effects. Slice B executes `IrImmutableBind` (`name =: expr`) as a fresh,
shallow-immutable binding; see `GENIA_STATE.md` section 3.
Pattern headers use R20 grammar, have no inline docstring position, and reject
arrows and grouped case bodies. Legacy identifier headers retain grouped bodies
and inline documentation. Comments/blank lines/per-clause annotations do not
split a closed group; unrelated statements and completed REPL submissions do.

Classification: Python-host Slice B immutable-binding execution (`name =: expr`) is implemented and covered by shared tests; closed/pattern declaration forms remain parser/lowering-only and are not runnable.
Default-open dispatch, cross-module linking changes and closed publication remain later slices. C++ support for the new declaration carriers is not claimed.

Historical ordinary `=` dotted targets remain literal binding names (including
function declaration targets), not property writes. New `=:` targets and new
pattern/guard declaration targets require simple names.
