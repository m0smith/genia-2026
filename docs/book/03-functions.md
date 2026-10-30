# Function declaration boundary

Concise implementation reference; `GENIA_STATE.md` section 3 is authoritative.

Ordinary unguarded identifier headers execute through the existing `IrFuncDef`
path. Explicit R20 `open` functions retain their implemented dispatch behavior.

Model B declarations lower to three nodes: immutable bindings use
`IrImmutableBind`, guarded/pattern-headed declarations use `IrPatternFuncDef`,
and consecutive same-name closed clauses use one `IrClosedFuncDef`.
`IrClosedFuncDef` rejects execution with
`model-b-not-implemented` before child effects. `IrPatternFuncDef` executes on the
Python host as a default-open ordinary function clause: clauses of one name in one scope
accumulate in declaration order and the first matching clause runs; see
`GENIA_RULES.md` section 8.5.1. `IrImmutableBind`
(`name =: expr`) executes on the Python host as a fresh, shallow-immutable
binding; see `GENIA_STATE.md` section 3.
Pattern headers use R20 grammar, have no inline docstring position, and reject
arrows and grouped case bodies. Legacy identifier headers retain grouped bodies
and inline documentation. Comments/blank lines/per-clause annotations do not
split a closed group; unrelated statements and completed REPL submissions do.

Classification: Python-host `name =: expr` is implemented and covered by shared
tests; closed and pattern declarations only parse and lower and are not runnable.
Default-open dispatch, cross-module linking changes and closed publication are
not implemented. C++ support for these declarations is not claimed.

Historical ordinary `=` dotted targets remain literal binding names (including
function declaration targets), not property writes. New `=:` targets and new
pattern/guard declaration targets require simple names.

## Bounded C++ host compatibility

The C++ host repairs for genia-cpp #53–#57 preserve ordinary grouped-body header
capture, fixed-arity accumulation and duplicate rejection, and short inline
same-line docstrings as metadata. Explicit-open header capture retains its
separate R20 restriction. These repairs do not implement default-open ordinary
functions, `doc_help`, annotations, or cross-module linking in C++.
