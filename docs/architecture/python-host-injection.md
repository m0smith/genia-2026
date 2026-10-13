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
| Native fixtures and `test` registrar | entry-only, still in the shared root |
| Model/grounding/concurrency fixture adapters | entry-only; explicit offline provider/authority/test helper values |
| Python program fixtures | entry-only, preserving current physical placement |
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
P2 placement/visibility, module fallback and evaluation-bound reflection remain
separately gated and are not activated by these bookkeeping APIs.
