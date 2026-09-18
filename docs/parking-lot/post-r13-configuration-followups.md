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
Two are security-critical gaps that block a launcher-free execution path for
protected outbound credentials; some are genuine ergonomic gaps that real
applications will hit soon; some are deliberate exclusions that should stay
out unless concrete usage proves them necessary; and one is a cross-cutting
maturity gap that gates the whole configuration family. This note preserves
that triage so the items are not silently lost and each is picked up, or
explicitly declined, on purpose.

Every candidate names the specific R13 non-goal or "not implemented" note it
relaxes, so the boundary being moved is explicit.

## Candidates to preserve

### Priority 1 — security-critical gaps

These are not ergonomic friction; they are the two gaps that currently force
any application needing a protected outbound credential (e.g. an HTTP
Authorization header) to bypass the normal `genia` execution path with a
host-specific launcher script. Both were surfaced concretely by the Groq
backend of the `ollama_chat` example, which currently requires
`python -m hosts.python.exec_ollama_chat --backend groq` instead of
`genia examples/ollama_chat.genia --backend groq`. They are listed together
because a fix for one does not substitute for the other, but each requires
its own contract and is independently gated.

**C-9. Secret-only provider keys / intrinsic secret classification.**

Not a relaxation of a stated R10 or R13 non-goal — it closes a gap neither
release scoped. `secret_get`/`secret_view` protect a value only at the call
site that retrieves it; nothing on the provider or key itself prevents the
same key from being read as plaintext through `config_get`/`config_view`
instead. Application code holding a provider can therefore bypass protected
handling entirely for a key that was only ever meant to be read as a secret.
Candidate: let provider construction (or a source descriptor) mark specific
keys secret-only, so `config_get`/`config_view` return a normalized error
for those keys instead of raw text. Must preserve R10's outer-`secret`
carrier semantics and add no new syntax, annotation, or Core IR; the
declaration is ordinary data passed to `config_provider`, not a language
feature.

**C-10. Execution-boundary declassification authority (remove the need for
host-specific launchers).**

Relaxes the R10 implementation note that *"CLI modes do not construct an
ambient provider. A future CLI integration may explicitly create and pass
one under its own ticket"* — extended here to cover authority, not just the
provider. Per R10, declassification authority is an opaque host capability
that Genia source cannot construct; something host-side must still mint it.
Today that minting only happens inside a bespoke Python launcher script
outside the normal `genia` command, which means: two backends of the same
example cannot share one invocation form; every application needing a
protected outbound sink needs its own launcher; credential policy is
scattered across ad hoc Python entry points; and the launcher has no
obligation to wire a real audit sink (the current example discards audit
events with `lambda event: None`).

Candidate: give the normal Genia execution boundary (the same boundary that
already constructs a provider under C-1/R14's `lifecycle_config`, or under a
future CLI-integration ticket) a way to also mint scoped declassification
authority for approved sinks, without exposing authority as an ordinary
source-visible value. At minimum the mechanism must:

- construct the configuration provider once per execution;
- acquire configured secrets as protected values;
- supply authority scoped to purpose and, ideally, destination — not just
  provider identity as today — so one authorized purpose cannot be reused
  against an unrelated destination;
- record non-sensitive audit events by default, not silently discard them;
- work consistently across file, command, pipe, test, and serve modes;
- avoid making all environment values implicitly authorized secrets.

Must not relax any R10 protected-carrier, sink, or declassification rule,
and must not make authority constructible from Genia source text. This is
the harder of the two gaps and needs its own contract before any
promotion; C-9 can be promoted independently and first.

### Priority 2 — genuine ergonomic gaps

**C-1. Lifecycle/provider binding — delivered by R14 issue #694 (E14-4).**

Relaxed the R13 non-goal: *"lifecycle binding, provider injection."*

`lifecycle_config(provider)` binds an explicitly constructed provider as
one reserved lifecycle peer, so participating stages read it through the
existing `lifecycle_context` accessor and construct qualified
`config_view`/`secret_view` values without repeatedly passing the provider
by hand. It composes with multiple peer lifecycles on the same scope and
remains one explicit, immutable, non-refreshable binding — not ambient
process state, not bare-name lookup, not dependency injection. See
`GENIA_STATE.md` section 9.11 and `docs/releases/R14.md` for the
implemented contract and a runnable example.

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

### Priority 3 — cross-cutting maturity gap

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

### Priority 4 — deliberate exclusions; add only on proven demand

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
- `docs/strategy/release-roadmap.md` — planned R14 Composable Lifecycles
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
- for Priority 4 items, the use case justifies the footgun surface introduced.
