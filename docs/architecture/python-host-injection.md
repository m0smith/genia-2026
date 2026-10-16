# Python host injection classification

**PYTHON REFERENCE HOST:** these internal APIs record installation intent during
F2 P1. `GENIA_STATE.md` remains language authority. They add no Genia builtin,
syntax, trust grant, acquisition behavior or isolation mechanism.

`Env.set_host(name, value, visibility=...)` requires exactly `runtime-public`
or `entry-only`. It installs into the same supplied Env, using unchanged
`set` identity, assignability and binding-metadata rules. Invalid/missing classes
fail before installation. The separate `host_binding_visibility` table stores
names/classes only, never fixture payloads. Classification does not become
language metadata and does not relocate either class during P1.

`set_host_internal` records on runtime's `host_internal_visibility` while keeping
the existing trusted-code access restriction. `register_host_autoload` records
each `(name, arity)` on runtime's `host_autoload_visibility`, preserving lazy
file evaluation, trust flags, registration order and deduplication. Low-level
`set`, `set_internal` and `register_autoload` remain available; ordinary lexical
definitions/parameters use `set` and require no host class.

## Reviewed installation sources

| Source | Class/ownership |
|---|---|
| Builtin installation, standard sinks/input/argv | runtime-public in the existing root |
| Trusted internal helpers and prelude autoload registrations | runtime-public ownership; existing trust restrictions remain |
| Constructor input/configuration/output callbacks and debug fields | captured runtime capability/state, not new lexical names |
| Native fixtures and `test` registrar | entry-only; installed in the registered entry scope E (F2/P2-C) |
| Model/grounding/concurrency fixture adapters | entry-only; explicit offline provider/authority/test helper values, installed in E |
| Python program fixtures | entry-only; installed in E on `make_program_env` paths |
| Module test's explicit `counter` callback | runtime-public: deliberately supplied module-visible capability |
| Custom harness autoload registrations | runtime-public on runtime, evaluated only on demand |

The reviewed installed-name/arity/path enumeration is
`tests/data/p1_host_binding_inventory.json`. Equality checks compare the actual
installed bindings, trusted internals and autoloads with this reviewed inventory;
new names require explicit review rather than automatically becoming public.

`tests/unit/test_host_binding_classification_p1_e.py` checks API validation,
identity/metadata/assignment compatibility, exact inventory, dynamic native and
adapter fixtures, trusted internal access, and maintained installer/harness
source sites. Its AST guard rejects low-level host installations through the
maintained `env`/`root` integration pattern; the protected MCP worker's generated
bootstrap is checked separately. This is a regression/process guard over those
sources, not a security boundary or proof about third-party host integrations.

R10 protected-carrier, sink and explicit-authority behavior is unchanged.
Classifying an authority or credential does not reveal it or mint authority.

## F2/P2-C/D placement and consumers (Python reference host)

`make_program_env(...)` builds R, runs optional `prepare(runtime)` host work (for
example MCP pruning) while R has no entry, then registers E with
`Env.create_entry_scope()` and returns E. After registration `set_host` places
`entry-only` bindings in E from any Env of the execution, and rejects
`runtime-public` installs, `set_host_internal`, `register_host_autoload` and an
`entry-only` install of a runtime-owned name (ValueError). Before registration
(caller-created roots) both classes install in the supplied Env as before.
Runtime-owned names (bound or internal runtime names, registered autoloads, every
top-level declaration of an autoload-target prelude file, snapshotted before
pruning) written by the entry unit bind in R; a pruned name is rejected instead
of recreated. The entry scope records a runtime-owned name once its binding operation succeeds; a rejected binding (collision, non-assignable, pruned) is never recorded. Annotation processing runs after the binding, so an annotation error (for example `@doc 1` on a new clause) can raise with the binding and its record already in place; declarations are not transactional.

**P2-D consumers.** The evaluator resolves identifiers through one helper; a
runtime `doc`/`meta`/`help` (marked by `Env.SCOPE_BINDER_ATTR`, value-based, never by
name) is returned bound to the evaluating Env and cached per Env, so lookup starts at
the evaluating frame and module code cannot name E bindings; the help catalogue and
output sink stay runtime-owned (`runtime_scope()`), and host `Env.get` still returns
the raw root-bound callable. `empty_env()` is based on R, so E bindings are not
implicitly visible to `eval` (supply them with `define`). Inside `eval`, `GeniaMetaEnv.lookup`
binds a raw `doc`/`meta`/`help` to the meta frame it was read in (names from `define`/`extend`);
an already-bound reflective callable transferred in keeps its captured scope, and there is no fallback. REPL `:env`, debugger
globals (`inspection_globals_scope()`), CLI `main` dispatch and native-test
discovery read the entry scope plus its declared runtime-owned names via
`Env.inspection_bindings()`/`Env.binding_owner()`; debug hooks and mode live on R once
E is registered (`Env.debug_state_scope()`); error and test-report sinks read R.

## Module reads of entry names (Python reference host only)

A module free-name read follows the module chain, then the runtime scope (including trusted
internals and one autoload retry) in `Evaluator._resolve_identifier`; when that misses, the ordinary
`Undefined name` `NameError` is raised. There is no module-to-entry compatibility path: the
F2/P2-E fallback (`module_fallback.py`, its per-execution event set and `GENIA_STRICT_MODULE_SCOPE`
switch) was removed under #1230. Entry-declared runtime-owned names are written through to R and stay visible
to modules and the prelude (STATE section 9, until the separately gated shadowing decision); all other
entry bindings stay in E. Caller-created roots register no entry. No other host implements this.
