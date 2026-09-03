# Post-R13 Configuration Follow-ups

Status: **Parking lot / non-authoritative**

This note captures candidate follow-up work only. It does not define implemented
Genia behavior and carries no release number. If this conflicts with
`GENIA_STATE.md`, `GENIA_STATE.md` wins. Each candidate below requires its own
contract, design, failing-tests, implementation, documentation, audit, and
distillation gates before implementation, exactly as R13 did.

## Why this exists

R13 (Configuration Resolution Ergonomics) is release-complete through E13-8. It
delivered explicit providers, immutable snapshots, qualified `config_view` and
`secret_view` callables, a narrow `config_args` CLI source, an exact-path `.env`
source, and `config_standard` conventional composition, all while preserving
R10 protected-value semantics.

R13 deliberately deferred a set of items to keep its surface small and truthful.
Some of those deferrals are genuine ergonomic gaps that real applications will
hit soon; some are deliberate exclusions that should stay out unless concrete
usage proves them necessary; and one is a cross-cutting maturity gap that gates
the whole configuration family. This note preserves that triage so the items are
not silently lost and each is picked up, or explicitly declined, on purpose.

Every candidate names the specific R13 non-goal or "not implemented" note it
relaxes, so the boundary being moved is explicit.

## Candidates to preserve

### Priority 1 — genuine ergonomic gaps

**C-1. Lifecycle/provider binding.**

Relaxes the R13 non-goal: *"lifecycle binding, provider injection."*

Today the provider is threaded by hand through every `config_view` and
`secret_view` construction. Bind an explicitly constructed provider through an
application or pipeline lifecycle so participating stages can construct
qualified views without repeatedly passing the provider. Multiple lifecycles
may coexist on each pipeline element; configuration binding must compose with
them and must not become ambient process state or bare-name lookup.

Proposed home: the planned R14 Composable HTTP Lifecycles epic (#619), which
already says it consumes R13 configuration ergonomics. E14-0 must explicitly
assign this behavior to an R14 issue or defer it to a separate gated follow-up;
the current R14 issue list must not leave it implicit between lifecycle scope
and protected HTTP credential work.

**C-2. Explicit typed/schema-mapped access.**

Relaxes the R13 non-goals: *"configuration schemas"* and *"implicit conversion,
or coercion."*

All values resolve as strings inside Outcomes, so application code hand-threads
`parse_int` plus a callable Template per numeric setting, as demonstrated by the
E13-6 proving case. Add an explicit, opt-in schema that maps keys to callable
Templates once, reusing R10 conversion and callable-Template validation. It must
stay explicit: no implicit coercion. This relaxes only the schema exclusion, not
the implicit-conversion exclusion.

C-2 and C-8 may share one schema representation, but they remain independently
promotable contract decisions. Typed access must not silently imply rejection of
unknown options, and unknown-option validation must not require typed access.

**C-3. Richer CLI grammar, with boolean flags first.**

Relaxes the R13 non-goals: *"boolean flags, short or grouped options"* and the
`--name=value` and underscore exclusions in E13-2.

`config_args` accepts only `--name value` long pairs. Real CLIs need at least
boolean flags; `--name=value` and short/grouped options are secondary. R13
explicitly declined to invent a boolean encoding, so that encoding is the first
contract question. Keep the single normalized key space shared by CLI, `.env`,
environment, and literal sources.

### Priority 2 — cross-cutting maturity gap

**C-4. Second-host conformance for the configuration family.**

Relaxes the standing *"Python is the only implemented host; shared/multi-host
conformance remains Partial"* status shared by R10 through R13.

The configuration and secret APIs are Experimental in part because only the
Python reference host implements the environment, `.env`, and snapshot
capabilities. Proving a second host against the shared spec is the gate for any
future Stable configuration-surface claim. It does not block separately gated
ergonomic follow-ups from remaining Experimental.

This work depends first on a generic multi-host spec runner. The current runner
routes shared cases only through the Python adapter. Runner infrastructure and a
second-host implementation therefore require explicit planning before
configuration-family conformance can be claimed. This is not a configuration
feature and must not be hidden inside one of the ergonomic candidates.

### Priority 3 — deliberate exclusions; add only on proven demand

These were excluded on principle, not by oversight. Each carries footguns R13
was right to avoid, and each needs a strong, concrete use case plus its own
contract gate before promotion. Do not promote an item merely because it appears
here.

**C-5. `.env` expansion features.**

Examples include `.env.local` or profile cascades, upward directory discovery,
interpolation, expansion, command substitution, multiline values, and
watch/refresh behavior. This relaxes the E13-3 exclusions. The footgun surface is
high; promote one narrow behavior at a time, never as a bundle.

**C-6. Member/dot access over views, such as `server.PORT`.**

Relaxes the R13 non-goal *"`server.PORT` or broader named access."* It was
deferred to preserve zero new syntax. The roadmap warns that this must not be
approved merely by appearing in discussion. It needs evidence that the callable
form, `server("PORT")`, is a real friction point and must pass the Core Surface
Freeze and normal semantic gates.

**C-7. Structured configuration files and remote secret stores.**

Examples include YAML, TOML, or JSON files, remote vaults, rotation, and
authentication/authorization. This relaxes the corresponding R13 non-goals. It
has the largest scope and is furthest from Genia's current validated-data-
pipeline wedge; keep it parked unless an application concretely requires it.

**C-8. Unknown-option/schema-driven validation and diagnostics.**

The CLI source accepts unknown valid names silently. An opt-in, schema-driven
unknown-option rejection could share a schema representation with C-2, while
remaining a separate contract and promotion decision. This relaxes the R13
non-goal *"unknown-option validation."*

## What this should not become

- A second configuration model or competing provider/precedence mechanism.
- Ambient or dynamic bare-name lookup, or implicit environment fallback.
- Any weakening of R10 protected carriers, sinks, authority, audit, or
  declassification.
- A reason to reopen R13 completion status; these are additive follow-ups.
- A bundle; each candidate is a separate contract and phase workflow.

## Related areas

- `docs/design/r13-configuration-resolution-contract.md` — delivered R13
  boundary and non-goals.
- `docs/strategy/r13-configuration-resolution-ergonomics.md` — original R13
  direction, including the deferred lifecycle-binding idea.
- `docs/releases/R13.md` — implemented-truth account.
- `docs/strategy/release-roadmap.md` — planned R14 Composable HTTP Lifecycles
  epic (#619) and issue path.
- `docs/parking-lot/lifecycle-future-ideas.md` — historical lifecycle promotion
  pointer.
- `docs/host-interop/HOST_INTEROP.md` and
  `docs/host-interop/HOST_CAPABILITY_MATRIX.md` — current single-host runner and
  configuration-capability status relevant to C-4.

## Promotion trigger

Promote a candidate out of this note when:

- a concrete application, not discussion alone, hits the named gap;
- an approved contract preserves R10 protection, explicit precedence and
  snapshot semantics, and the single normalized key space;
- the candidate has an explicit release/issue owner and complete phase workflow;
  and
- for Priority 3 items, the use case justifies the footgun surface introduced.
