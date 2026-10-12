# P1-E evidence — issue #1067

User authorizes B–H within the approved behavior-preserving P1 boundary.
Base: P1-F `5971a72`, stacked on B `add4055`; builtins edits serialized after F.
Red tests: `bdcf5da` (16 failures, missing classes/API/unclassified installers),
`78b0389` (2 failures/2 passes, source-derived family installer recognition),
`f72fe86` (unclassified harness guard). Implementations: `71dc70d`, `828faf0`,
`04418c2`, `274338e`. Legacy lexical APIs remain; host APIs require explicit
classes, preserve placement and metadata, and record names/classes only.

Reviewed enumeration: 241 bindings, 9 trusted internals, 234 autoload keys.
Builtin/runtime callbacks runtime-public; native/adapter/program fixtures
entry-only; module counter explicitly runtime-public; custom autoloads runtime
owned. Source guard covers maintained installers/harness patterns and the
protected generated worker bootstrap separately. See architecture note.

Focused evidence: 105 core/native/reflection/protection/doc-guard tests passed;
provider/protection family 320 passed with 4 loopback permission failures on
first run; those 4 passed with socket access (not a claim the original run was
green). Pipeline/IO 178 passed; tooling/module/host API 198 passed.
Ruff/whitespace clean; code documentation 0 errors after documenting changed
fixtures and removing exactly resolved debt entries. No protected-boundary,
runtime placement, callable identity, parser/IR, public capability or C++ change.

Final integrated validation and full partitions belong to H. Source/classification
and fixture migrations were committed in separate reviewed families rather than
renaming or replacing lexical binding behavior. No runtime values enter the
inventory/visibility records. No new public metadata; reference regeneration
should be unchanged. STATE synchronization is consolidated in H.
