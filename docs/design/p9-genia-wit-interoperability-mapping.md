# P9 — Genia↔WIT Interoperability Mapping and Mismatch Table (Design Only)

Status: **Architecture/design proposal — non-authoritative, no implementation
authorized.** `GENIA_STATE.md` remains final authority for implemented
behavior. This document produces no WIT file, no adapter code, no component
build, no runtime code, no new provider, no test, and no Core IR/parser/AST
change. It answers Provider Composition work-ledger row **P9**: "Can the
resulting Genia model map to one actual WIT component without changing Genia
semantics?"

Scope authority: [issue #947](https://github.com/m0smith/genia-2026/issues/947).
Prerequisite reading this document assumes and does not repeat:
`docs/analysis/provider-composition-stage0.md` (P3/P4 frozen value-family
matrix, numeric admissibility summary, "Relationship to WIT" section),
`docs/analysis/provider-composition-preflight.md` (P0/P1/P2/P5/P6/P7),
`docs/design/p8-alternate-provider-substitution-proof-design.md`, and
`src/genia/retrieval.py`.

WIT is treated here exactly as `provider-composition-stage0.md` frames it:
mature interface/resource vocabulary, an adversarial architecture comparison,
a possible external component ABI, and a later language-neutrality proof —
**never** Genia's semantic authority. Nothing in this document redefines
Genia's Outcome, exact numerics, Flow, map/equality, representation, or
protected-value semantics to make a WIT mapping more convenient. Where a
mapping is lossy or not representable, this document says so plainly instead
of proposing a Genia semantic change to paper over it.

---

## 0. Summary of findings

- **Proof target:** `retrieve/4` (R12), reused unchanged from P8, per
  §2 below.
- **Toolchain feasibility:** `cargo`/`rustc` are present and `cargo search`
  successfully reaches the crates.io index through the environment's proxy;
  `wasm-tools`, `wasmtime-cli`, and `wit-bindgen-cli` are all published,
  current crates, but none is installed in this environment today. Full
  `cargo install` was **not** run in this design phase (out of scope per the
  issue); see §3 for the exact pinned plan the implementation phase should
  use, and the one open risk (build time/disk for a `cargo install` of a
  large Rust toolchain in a sandboxed, possibly time-limited environment).
- **Headline mismatches:** WIT has no arbitrary-precision numeric type at
  all, so Decimal/Rational/Integer must be lowered through explicit
  structural records rather than any WIT primitive numeric type — this is
  **adapted**, not direct, and never `f64`. Genia's ordered Map with R18 key
  identity has no WIT equivalent and requires a hand-designed ordered
  key/value record. Outcome carries strictly more structure than WIT
  `result<T, E>` (three tagged cases plus optional context, not two) and is
  mapped to an explicit `variant`, not `result`. Protected carriers,
  authorities, and provider capabilities are **intentionally-unsupported**
  as WIT payload types — they never cross as WIT values at all. Borrowed
  resources map to WIT `borrow<T>` with a **lossy** caveat: WIT's Canonical
  ABI enforces borrow non-escape only within one component-to-component
  call, not across Genia's own R14 scope/lifecycle boundaries, so a Genia
  borrow that would be legal under this WIT mapping is a strict subset of
  what P2's R14/R18 borrow model already permits.

---

## 1. Explicit Genia → WIT concept mapping

### 1.1 Semantic interface → WIT `interface`

Genia's "semantic interface" (`provider-composition-preflight.md`'s Terms
section: "a concern-sized behavioral contract... not a class, module path,
SDK object, or same-named function set") maps **directly** to a WIT
`interface`: a named collection of function signatures and shared type
definitions with no implementation. `retrieve/4`'s public shape —
`retrieve(provider, config, credential, authority) -> retriever` and
`retriever(handle, query, k) -> Outcome` — is exactly the shape a WIT
`interface` block exists to declare. No adapter is needed for the *interface
declaration* itself; the adapter work is entirely in the *value* mapping
(§1.3 onward), because WIT functions may only pass WIT-typed values, and
several Genia values crossing this boundary (protected credential,
authority, opaque handle) are not ordinary WIT-typed payloads at all — they
must be represented as resources or excluded entirely, per §1.7/§1.8.

**Mapping quality: direct** (interface *shape*), compounded by adapted/lossy
payload mappings (see below).

### 1.2 Exact interface identity/revision → WIT `world` / interface versioning

R12's actual compatibility mechanism (E12-4, traced in P8 design §5) is
**not** a public name+revision token — it is a private Python `object()`
identity minted at `GeniaIndexProvider` construction, copied into every
`GeniaIndexHandle` it produces, and copied again into any
`GeniaRetrieveProvider` built through `create_fixture_retrieve_provider`.
Compatibility is checked by three ordered exact guards: Python object
identity, then exact `space` string equality, then exact `dims` integer
equality (`retrieval.py:865-886`).

WIT's nearest concept is a `world` (a named, versioned collection of
imported/exported interfaces) plus package versioning (`namespace:pkg@X.Y.Z`
in the component model's semver-shaped package identity) or an interface's
own named identity within a package. This is **adapted**, not direct, for
two reasons:

1. **Semver vs. opaque exact identity.** `provider-composition-preflight.md`
   P5 already settled, independent of WIT, that Genia's general interface
   identity model is "exact nominal identity + exact opaque revision" and
   explicitly rejects SemVer inference ("SemVer has no semantic authority
   and ranges are not inferred"). WIT package versions are conventionally
   semver and many toolchains apply semver-range compatibility reasoning at
   the *tooling* level (even though the Component Model spec itself treats
   an exact version as an exact identity for linking purposes). A WIT
   mapping must pin one **exact** package version per interface revision and
   must not let any tooling-level semver-range convenience leak into what
   Genia treats as compatible. This is a process discipline the
   implementation phase must enforce (exact version pinning in the `.wit`
   package declaration), not a WIT type-system guarantee.
2. **Runtime object identity vs. static package identity.** R12's actual
   mechanism is a *runtime* value (a Python object minted per
   `GeniaIndexProvider` instance) that governs whether one specific
   `(index_provider, retrieve_provider, handle)` triple is compatible at
   call time — an instance-level check. A WIT `world`/package version is a
   *static*, compile/link-time identity shared by every instance of a given
   component. WIT's static versioning proves "this component implements
   interface X at revision Y" but cannot, by itself, express R12's
   additional *per-instance pairing* requirement (a specific retrieve
   provider is compatible only with index providers it was explicitly
   paired with, not with every index provider claiming the same
   space/dims). The WIT proof target (§2) must therefore represent
   E12-4's exact `space`/`dims` pairing as **data** carried alongside the
   resource handle (a record field), not rely on WIT's own versioning
   mechanism to express it — WIT versioning covers only the outer "this is
   the right `retrieve` interface shape" layer; the inner per-pairing
   compatibility check remains Genia-side runtime logic operating on
   ordinary WIT record fields, exactly as it already does in Python.

**Mapping quality: adapted.** WIT versioning covers the outer interface-shape
identity; the inner per-pairing compatibility identity must be carried as
explicit record data and checked by adapter logic, not inferred from WIT
type-level compatibility.

### 1.3 `ProviderBoundaryValue` → WIT `record` / `variant`

The frozen P4 model ("Genia value families, tagged Outcome, ordered
sequence/pair, ordered map entry sequence, represented value... recursively
subject to P3") maps onto WIT's `record` (fixed named fields), `variant`
(tagged union), `list<T>` (homogeneous sequence), and `tuple<...>` (fixed
heterogeneous sequence) primitives, but **only after** each individual value
family below is separately resolved — `ProviderBoundaryValue` is not one WIT
type, it is the *set of admissible WIT types* an adapter is permitted to
produce, exactly mirroring P4's own framing ("This is a semantic shape, not
a serialization format"). Concretely:

- Bool → WIT `bool` (direct)
- String → WIT `string` (direct, both are Unicode scalar sequences; WIT
  strings are UTF-8-validated Unicode scalar value sequences, matching
  Genia's own Unicode scalar sequence rule — no adapter needed)
- Symbol → **adapted**: WIT has no symbol/interned-atom primitive; represent
  as a `record { name: string }` (or a WIT `string` tagged as symbol by
  field name in the surrounding record) — never collapse to a bare `string`,
  which would erase the Symbol/String kind distinction P4 requires
  ("preserve exact Genia value family and variant... Bool versus Symbol
  versus String")
- List → WIT `list<T>` (direct for the container shape; admissibility of
  `T` recurses per P3)
- Pair → **adapted**: WIT has no 2-tuple-with-named-roles primitive matching
  Pair's `car`/`cdr` semantics exactly, but WIT `tuple<T, U>` is a faithful
  structural adapter (fixed two-element heterogeneous sequence); do not
  flatten to `list<T>`, which would erase the Pair/List kind distinction P3
  requires ("never silently flattened to a List")
- ordered Map → **adapted, no native equivalent** — see §1.4
- Outcome → **adapted, not `result<T, E>`** — see §1.5
- Represented value → **adapted** — see §1.7
- Protected carrier / authority / provider capability / live resource /
  Flow/Seq → **intentionally-unsupported as ordinary payload data** — see
  §1.6/§1.7/§1.9/§1.10 and the mismatch table

**Mapping quality: adapted (composite).** `ProviderBoundaryValue` as a whole
is not one WIT type; it is the recursively-applied union of the
per-family mappings below, each independently classified.

### 1.4 Outcome (`some`/`none`/`err`/context) → WIT `variant` (NOT `result<T, E>`)

This is the mapping the issue explicitly warns against assuming. Compared
carefully:

**WIT `result<T, E>`** has exactly two cases: `ok(T)` and `err(E)`. It
carries no third case and no separate optional-context field distinct from
the payload itself.

**Genia's Outcome** (per `GENIA_STATE.md` §2 and R18's "Outcomes" equality
section, both referenced throughout P3/P4) has **three** constructors, not
two:

- `some(value[, context])` — success, with an *optional secondary context*
  field independent of `value` itself
- `none(reason[, context])` — semantic absence, itself carrying a reason and
  optional context (not merely "no value" — R12's own
  `none("retrieval-no-results")` is a meaningful, named absence, distinct
  from failure)
- `err(reason[, context])` — recoverable failure, reason plus optional
  context

`retrieve/4` alone exercises all three: `some([{chunk, score}, ...])` on
success, `none("retrieval-no-results")` on a genuinely empty valid result,
and `err(reason, context)` for every recoverable failure family
(`retrieve-timeout`, `retrieve-rate-limited`, `retrieve-rejected`,
`retrieve-transport-failure`, `retrieve-response-invalid`,
`retrieve-capability-incompatible`, `retrieve-embedding-incompatible`). A
naive `result<T, E>` mapping would have to fold `none(...)` into either
`ok` or `err`, and either choice is a **semantic falsification**:

- folding `none(...)` into `ok(option<T>)` (i.e. `result<option<T>, E>`)
  loses `none`'s own `reason`/`context` fields (WIT's built-in `option<T>`
  carries no payload at all for its `none` case) — `retrieval-no-results`
  as a distinguishable reason would be silently dropped;
- folding `none(...)` into `err(E)` conflates semantic absence with failure,
  which R12's own contract and R18's Outcome-equality rules ("`some`,
  `none`, and `err` are never equal across constructor kinds merely because
  their contents resemble one another") explicitly treat as distinct.

**Selected adapter shape:** a WIT `variant` with three cases, each carrying
its own record:

```text
variant genia-outcome {
  outcome-some(outcome-some-payload),
  outcome-none(outcome-none-payload),
  outcome-err(outcome-err-payload),
}

record outcome-some-payload {
  value: retrieve-evidence-list,        // the interface's success payload type
  context: option<provider-boundary-value>,
}

record outcome-none-payload {
  reason: string,                       // Symbol-shaped reason, see note below
  context: option<provider-boundary-value>,
}

record outcome-err-payload {
  reason: string,
  context: option<provider-boundary-value>,
}
```

Illustrative WIT spelling only; the exact identifier/case-naming grammar is
implementation-phase work, not fixed here. `provider-boundary-value` above
stands for whatever recursive `variant`/`record` the implementation phase
defines for the smaller set of `context` shapes `retrieve/4` actually uses
(each `retrieve/4` context is a small closed map of already-admissible
leaves per the P8 design's §8 table — `timeout_ms: Integer`,
`retry_after_ms: option<Integer>`, `kind: Symbol`), not a fully general
recursive value type; a fully general `ProviderBoundaryValue` WIT type is
not required to prove this one interface and is not designed here.

`reason` fields are Genia Symbols in the runtime (`"retrieval-no-results"`,
`retrieve-timeout`, etc. are `GeniaSymbol`/string-literal reasons per
`retrieval.py`) — WIT has no symbol primitive (§1.3), so each `reason` is
represented as WIT `string` carrying the exact canonical reason spelling.
This is itself an **adapted** sub-mapping: it preserves the reason's exact
text but not Genia's Symbol-vs-String kind distinction at the WIT type
level — a deliberate, narrow exception noted here rather than hidden,
because a `reason` field's *closed* fixed vocabulary (the contract's exact
table of `retrieve-*` reasons) means kind confusion with an ordinary String
value is not observable in practice for this one field; a general-purpose
`ProviderBoundaryValue` Symbol mapping still uses the `record { name:
string }` form from §1.3, not this narrower shortcut.

**Mapping quality: adapted (three-case `variant`, not two-case `result`).**
Genia's Outcome genuinely carries more structure than `result<T, E>`; using
`result<T, E>` directly would be **lossy** (silently losing `none`'s
distinct meaning) and is explicitly rejected.

### 1.5 (duplicate heading avoided — see 1.4 for Outcome)

### 1.6 List/Pair/Map — ordered Map with R18 key identity

List and Pair are covered in §1.3. The Map case is the hardest structural
mismatch in this document.

**What R18 requires an ordered Map to preserve** (per
`docs/design/r18-portable-value-equality-contract.md` and P3/P4's Map row):

1. **Deterministic entry order** as constructed — "encode as an ordered
   entry sequence at the semantic layer, not a JSON object or host
   dictionary" (P4); R17/R18 fix replacement-preserves-position,
   removal-preserves-remaining-order, remove-then-reinsert-appends
   semantics that a *consumer* of a crossed Map must not silently violate
   by re-sorting or hash-reordering entries.
2. **Arbitrary legal key kinds**, not only strings: booleans, integers,
   non-NaN floats (including infinities), strings, symbols, recursively
   legal Pairs, recursively legal Lists, and represented values whose
   carried value is recursively legal (R18 "Legal map keys and key
   equivalence"). Notably this means Integer/Float/Bool/Pair/List keys are
   all legal — a Map is emphatically not a string-keyed record.
3. **R18 canonical key identity**, not host equality: Integer `1` and
   exactly-equal Decimal `1.0` are *the same key*; `0.0` and `-0.0` are the
   same key; `true`/`1` and `false`/`0` are *different* keys; NaN is
   illegal as a key. A structural re-derivation of "equal" from a generic
   WIT/host equality operator (for example naive floating-point `==`, or a
   host language's default hash-map key equality) would not reproduce this
   canonical-identity relation without an explicit adapter enforcing R18's
   rules.

**WIT has no native ordered, arbitrary-key-kind map type at all.** WIT's
closest built-in aggregate types are `record` (fixed named string-literal
fields, known at compile time — cannot represent a runtime-variable key
set), and `list<tuple<K, V>>` (an ordered sequence of key/value pairs,
which *can* preserve order and arbitrary key kinds structurally, but
carries **no** enforced key-uniqueness, no canonical-identity dedup, and no
built-in equality operator at all — WIT types have no methods).

**Explicit adapter design (this document's answer to the issue's
requirement to "design an explicit adapter representation"):**

```text
record genia-map-entry {
  key: provider-boundary-value,     // pre-canonicalized per R18 before crossing
  value: provider-boundary-value,
}

type genia-ordered-map = list<genia-map-entry>
```

Constraints the adapter (not the WIT type system) must enforce, on both
sides of the boundary:

- **Construction-time canonicalization.** Before a Genia Map crosses
  outward, the host adapter iterates it in its existing deterministic R17
  order and emits one `genia-map-entry` per mapping, using each key's
  *canonical* R18 identity-preserving representation (for example, a
  Decimal key `1.0` and an Integer key `1` must, if such a mixed-kind Map
  legally exists, already be one entry under R18 dedup — the adapter must
  not invent a second entry merely because two host-side numeric objects
  differ). This canonicalization work already exists in the reference
  host's `equality.py` legal-key canonicalization helper (R18
  "Implementation design" → "Map-key canonicalization") — the WIT adapter
  reuses that existing canonical-identity computation, never a new
  independent equality rule.
- **Order preservation, not reconstruction.** The WIT-side consumer (a Rust
  component, in the P9 proof target) must treat `genia-ordered-map` as an
  ordered sequence and never re-sort, deduplicate by its own equality, or
  rebuild it into a language-native `HashMap`/`BTreeMap` if it intends to
  hand a Map back across the boundary unchanged — doing so would
  silently violate R17/R18 order guarantees. A component that only reads
  Map values (as `retrieve/4`'s proof target does — `config` is the only
  Map-shaped input, and it is read-only, never returned) does not need to
  preserve round-trip order fidelity for *returned* data, but the adapter
  design itself is written generally because a *different* future interface
  could return a Map.
- **Inbound duplicate-key rejection.** A `genia-ordered-map` list arriving
  from the WIT side (e.g. a hypothetical component-returned Map) must be
  rejected as boundary misuse if it contains two entries whose keys are
  R18-equal — WIT's `list<tuple<K,V>>` shape cannot enforce this
  uniqueness itself; the reference-host adapter must validate it explicitly
  before reconstructing a `GeniaMap`, exactly as P3's "Recursive
  admissibility rule" requires ("no borrowed carrier, local-only value...
  occurs anywhere in the graph" generalizes to "no duplicate-key violation
  of the owning Map contract").
- **Key legality re-validation.** Every `key` field must independently
  satisfy R18 legal-key-family membership (§ above) after crossing; an
  illegal key (for example a `provider-boundary-value` payload that
  happens to encode a Map, Outcome, or function-shaped value as a "key")
  must be rejected at the boundary, not silently accepted because WIT's
  type system permitted constructing the record.

`retrieve/4`'s own `config` parameter (`{id: String, timeout_ms: Integer}`)
is a small, fixed-shape Map in every call this proof exercises — it could
alternatively be represented as a plain WIT `record { id: string,
timeout-ms: u32 }` for this *specific* interface, sidestepping the general
ordered-map adapter entirely for this one field. The P9 proof target (§2)
uses the general `genia-ordered-map` adapter deliberately, even though the
narrower record shape would suffice for `config` alone, specifically to
exercise and validate the harder general mechanism this section designs,
since a future WIT-mapped interface with a genuinely dynamic-shaped Map
input will need it.

**Mapping quality: adapted, with real semantic risk.** WIT has no ordered
arbitrary-key-kind Map primitive; the `list<tuple<K,V>>` + explicit
canonicalization/uniqueness/order-preservation adapter above is necessary
and, if the three enforced constraints above are honored on both sides of
every crossing, sufficient to preserve R18 key identity and R17 order. The
semantic risk is that the *enforcement* lives entirely in adapter code on
both sides, not in the WIT type system — a WIT-side component author who
does not honor the order/uniqueness contract can silently produce a
type-checking-valid `genia-ordered-map` that violates R18/R17 semantics,
and the reference-host adapter is the only thing that can catch this (by
explicit re-validation on the way back in). This must be exercised as a
negative-test scenario in the implementation phase, not merely documented.

### 1.7 Represented values / protected values / semantic tokens

**Represented value (R9).** A represented value is an ordered facet stack
plus a carried value, both independently portable per P3/P4 ("Represented
values remain represented values... preserve the exact ordered facet stack
plus recursively portable carried value and portable facet metadata").
Maps onto an explicit adapted WIT `record`:

```text
record genia-represented-value {
  facets: list<facet-descriptor>,   // ordered, per R9 facet-order rule
  carried: provider-boundary-value, // recursively admissible per its own row
}
```

where `facet-descriptor` is itself a contract-defined WIT `record`/`variant`
naming the facet kind and its portable metadata — not defined generally
here, since `retrieve/4`'s only represented-value field (`chunk.meta`, an
R9 `json`-represented value copied unchanged from `chunk/2`) needs only the
`json` facet kind for this specific proof; a fully general facet catalog is
future work, consistent with P4's own "Provider-owned facet metadata needs
an owning contract" deferred note. **Mapping quality: adapted.**

**Protected value (R10 protected carrier).** P3/P4 state the rule precisely:
"Crossing is allowed only if the boundary can preserve the same opaque
protected carrier and all R10 sink/declassification rules without exposing
the payload... Transport must never become declassification. Otherwise
reject." For `retrieve/4` specifically, the `credential` argument is an
R10-protected value passed into `construct_retrieve` on the *reference-host
side only* — it is declassified immediately before the one transport
attempt (`retrieval.py:887`, `declassify(self._authority, self._credential)`
called host-side, inside `GeniaRetriever.__call__`) and the *already
declassified ordinary string* is what a realization's handler receives.

This has a direct consequence for the WIT proof target: **the protected
credential itself never needs to cross the WIT boundary as a protected
carrier at all**, because in every existing/traced R12 realization the
declassification happens in reference-host Python code, strictly before any
realization-specific call. If the WIT proof target represents an
alternate *realization* of `retrieve/4`'s handler (the natural choice, since
P8 already proves realization substitution at the handler level, and P9
should extend that exact seam — see §2), the WIT component receives only
the **already-declassified ordinary credential string** as an ordinary WIT
`string` parameter, exactly mirroring what the existing Python handler
signature already receives (`handler(config, backend_ref, query, k,
credential: str)` in `retrieval.py`/P8's design §2.1).

This is **not** a new credential-transport mechanism — it reuses R10's
existing just-in-time declassification boundary unchanged and simply
relocates *where the already-declassified value is consumed* (a WIT
component instead of a Python closure), which is exactly the kind of
"unchanged application logic, alternate realization" substitution P8/P9
exist to prove. If a future WIT interface needed the *protected carrier
itself* (not an already-declassified value) to cross into a component —
for example, to test whether a component-side adapter could itself perform
declassification — that is explicitly **out of scope** for this proof and
remains **not-representable-without-new-contract**: R10 defines no
cross-process/cross-component protected-carrier reconstruction, and P3/P4
say so explicitly ("Cross-process/cross-provider reconstruction or
credential transport is deferred; no rule is invented here"). This document
invents no such rule.

**Mapping quality:** ordinary already-declassified credential value —
**direct** (plain `string`). The protected carrier itself, as a *carrier* —
**intentionally-unsupported** as a WIT value; never invented here.

**Opaque semantic token (R18).** No current Genia value in `retrieve/4`'s
boundary is an opaque semantic token (P3/P4's token row is about future
values like `Revision`, "not current values" per stage0's closing note).
This document therefore does not need a concrete token adapter for the
proof target, but records the shape a future one would need: WIT `resource`
(§1.9) is the wrong target, because a token is not a live handle — it is
immutable and structurally comparable by its three hidden R18 identity
components without dereferencing anything live. The nearest adapted WIT
shape is an opaque `record` whose fields are the token's *hidden* R18
equality components spelled out as ordinary WIT fields — but R18 requires
those components to remain **hidden** from ordinary Genia source
("representation is not public... performs no... exposure of those hidden
components"). Materializing them as visible WIT record fields would leak
what R18 explicitly keeps opaque at the Genia language level, even if no
*Genia* source could observe the WIT-side fields directly (a determined
WIT-side component author still could). This is flagged as a genuine open
question for any future token-carrying interface, **not resolved here**
because no current interface needs it — see the mismatch table's `semantic
token` row and §6 open questions.

### 1.8 Live/owned/borrowed resources → WIT `resource`/`own<T>`/`borrow<T>`

R12's `GeniaIndexHandle` is exactly the concrete "opaque host-produced
handle" P0/P3 already identify as "an existing concrete precursor to a
component resource" (`provider-composition-stage0.md` P0 row). It is:

- **non-constructible** from Genia/WIT source (only the index provider
  mints one);
- **non-inspectable** (`__eq__`/`__hash__`/`__copy__`/`__deepcopy__` all
  raise `TypeError`; `__repr__` returns only the fixed string
  `<index-handle>`);
- **identity-bearing** per R18 ("Retrieval/index and other host handles" —
  "Local-only / non-transferable").

This maps **directly in shape, adapted in enforcement** onto WIT
`resource`/`own<T>`/`borrow<T>`:

```text
resource index-handle {
  // no exported methods needed for this proof; retrieve/4 only ever
  // passes a handle *into* the retrieve call, it never returns one
}
```

- The **owning** side (the reference-host Python process, which already
  holds the `GeniaIndexHandle`) passes the WIT component an `own<index-handle>`
  or `borrow<index-handle>` depending on whether the call needs the
  component to retain it past the call (`retrieve/4` never does — the
  handle is read-only and synchronous within one call, so `borrow<T>` is
  the correct choice per P2's own rule that a borrowed view is "usable
  only for a bounded call/scope").
- **This is P8's own scenario 2 ("Provider accepts borrowed resource")
  directly instantiated** using real WIT machinery instead of only Genia's
  own R14/R18 concepts: the Canonical ABI's `borrow<T>` **does** enforce,
  at the component-boundary level, that a borrowed resource handle is only
  valid for the duration of the export call that received it and traps if
  retained past that call's return — this is a genuinely useful,
  independently-enforced echo of P2's "borrow escape is prohibited
  initially" rule, at a different layer (component-call boundary rather
  than R14 scope boundary).
- **The lossy seam:** WIT's Canonical ABI borrow-lifetime enforcement is
  scoped to **one component-to-component call**, not to Genia's own R14
  scope/lifecycle model. P2's borrow rules are richer — they also cover
  closure capture, Flow emission, List/Map insertion, and multi-level
  parent/child scope structure, none of which WIT's borrow check knows
  about or enforces. A borrow that is valid under *WIT's* rule (contained
  within one call) is always valid under Genia's stricter R14 rule (P2's
  "bounded non-owning live value" is at least as strict as one call), so
  using WIT `borrow<T>` for this proof introduces no unsoundness — but WIT
  cannot express or enforce the *rest* of P2's escape-prohibition list
  (Flow capture, closure capture, Map/List insertion) on its own; those
  remain solely Genia-side responsibilities the adapter must still enforce
  independently before a value ever reaches the WIT call, exactly as it
  already must for the pure-Genia case.

**Feasibility test recommended for the implementation phase (not run here):**
implement `index-handle` as a WIT `resource` with zero methods, pass it as
`borrow<index-handle>` into a `retrieve` function, and confirm (a) a
component that tries to store the borrowed handle past the call traps per
the Canonical ABI's own enforcement, and (b) an `own<index-handle>` passed
by value transfers ownership exactly once and cannot be used again from the
donor side without a new explicit `own`. This is the "test at least one
identity-bearing mapping if feasible" instruction from the issue; it
requires the pinned toolchain from §3 and is implementation-phase work, not
performed in this design document.

**Mapping quality: adapted** (structurally close, real Canonical ABI borrow
enforcement is a genuine asset, but WIT's borrow rule is strictly narrower
than P2's full escape-prohibition list, so Genia-side enforcement remains
necessary regardless of the WIT mapping).

### 1.9 Provider capability / authority → never weakened for WIT convenience

Per PAI-7 ("capability, credential, and authority are distinct... binding
grants no authority") and the issue's explicit instruction, provider
capabilities and `GeniaDeclassificationAuthority` values are **not** WIT
payload types at all. Concretely for `retrieve/4`:

- `provider` (`GeniaRetrieveProvider`) is a Python-host-only capability
  object never observed by Genia source beyond opaque possession (P3's
  "Provider capabilities... Local-only / non-transferable" row). It is
  never lowered into a WIT value. The *choice* of which WIT component
  realizes `retrieve/4`'s handler is made exactly the way P8 design §6
  already establishes realization A/B is chosen — **at host-side
  construction time**, before any call, never by an ambient WIT
  registry/discovery mechanism and never inferred from a WIT `world`'s
  import graph functioning as a service locator. Concretely, the *host*
  decides, at Python-side bootstrap, which compiled `.wasm` component to
  instantiate and bind as the retrieve realization — this is the WIT-side
  analog of P8's "which Python handler was passed to
  `create_fixture_retrieve_provider`," and it happens in the same place:
  host bootstrap code, never Genia source, never resolvable from inside a
  running Genia program.
- `authority` (`GeniaDeclassificationAuthority`) never crosses either. As
  established in §1.7, declassification happens host-side before the WIT
  call; the WIT component receives only the already-declassified ordinary
  value.

**Mapping quality: intentionally-unsupported** (as WIT payload types) — not
a gap to fix, a deliberate exclusion matching R10/PAI-7 exactly.

### 1.10 Failure layering: keep four layers distinct, never collapse into one WIT `result`

`provider-composition-preflight.md` P6 already fixes three failure-owning
layers for same-process Genia calls (operation Outcome / composition-or-
runtime-misuse / R36 outer execution envelope). WIT/component-model
interop introduces a **fourth**, genuinely new layer that P6 did not need to
name because it predates any actual cross-process/cross-component boundary:

1. **L1 — Operation Outcome** (unchanged): `retrieve/4`'s own `some`/
   `none`/`err`, exactly as §1.4 maps it. Owned by the interface contract.
2. **L2 — Provider realization/adaptation failure** (unchanged from P6):
   missing/ambiguous/incompatible binding, resource expiry/escape, adapter
   pre-invocation validation. Still Genia/reference-host-side runtime
   misuse, never an Outcome. A WIT-specific instance of this layer is a
   **type/shape mismatch caught by adapter validation before the WIT call
   is even made** (for example, a Map crossing the boundary with a
   duplicate R18-equal key, per §1.6) — this is P6 Layer 2, just with a WIT
   adapter as one more place Layer-2 validation can happen, not a new
   layer.
3. **L3 — WIT/component transport/runtime failure** (**new, named here for
   the first time**): a component instantiation failure, a Canonical ABI
   trap (for example, a borrow-lifetime violation per §1.8, a lowering/
   lifting failure for a malformed WIT value, an out-of-fuel/resource-limit
   trap in a sandboxed Wasmtime instance, or a host-function call failure
   at the `wasmtime` embedding layer), or an uncaught Wasm trap/panic
   inside the component itself. This is **not** an operation Outcome
   (`err(...)`) and **not** P6's existing Layer 2 composition/binding
   misuse (which is about *Genia-level* binding validity, not Wasm runtime
   mechanics) — it needs its own name precisely because it did not exist
   before a real component boundary did. A component trap must be
   normalized at the WIT-adapter boundary into a non-sensitive, closed
   diagnostic (mirroring PAI-8 "normalize at the owner" and P6's existing
   "raw host/provider details never cross" rule) **before** it could ever
   be mistaken for an L1 `err(...)` — for example, `err("retrieve-transport-
   failure", {kind: quote(other)})` is the correct normalization *target*
   only if the failure genuinely originates from a realization's own logic
   behaving like a normal transport failure; a component *trap* (a Wasm-
   level fault distinct from the component's own logic returning a
   failure) is a strictly worse condition than an ordinary realization
   error and should be classified as its own L3 diagnostic category (for
   example a host-only, non-Genia-visible "component fault" event), not
   silently coerced into the same `err(...)` an ordinary Python handler
   exception already produces. This document does not fix an exact
   normalized reason vocabulary for L3 — that is implementation-phase work
   for whichever interface first needs it — but it fixes that L3 **must
   exist as its own named layer**, distinct from L1/L2, so a future
   implementation cannot quietly fold "the component crashed" and "the
   realization returned a normal failure" into the same observable shape.
4. **L4 — R36 execution envelope** (unchanged, still future/planned): the
   outer envelope for whether a *bounded computation* (potentially spanning
   multiple calls, potentially remote) launched/completed at all. A WIT
   component call inside one process is **not** automatically an R36
   execution — per P7 scenario 13, "Local vs R36-hosted provider... same
   semantic interface may be bound, but R36 remains explicit and adds its
   outer envelope; no transparent remoting." A same-process, same-machine
   `wasmtime` component instantiation is still L1-L3 only; L4 applies only
   if/when a future R36-mediated deployment places the component call
   itself behind R36's outer envelope (for example, the component running
   in a genuinely separate execution context R36 governs). This document
   introduces no R36 behavior and makes no claim that WIT component calls
   automatically become R36 executions.

**No collapsing.** A single WIT `result<T, E>` (rejected already in §1.4 for
even L1 alone) is doubly wrong here: it cannot express L1's own three-case
Outcome, and it must never be asked to also carry L2/L3/L4 failure meaning.
Each layer keeps its own owner and its own normalized observable shape; L3
is the one genuinely new layer this design introduces, and it is scoped
narrowly to "the Wasm/component runtime mechanics themselves misbehaved,"
never used as a catch-all for ordinary realization failures the interface
already has a vocabulary for.

### 1.11 Numeric kinds (Integer/Decimal/Rational/Float64) — never `f64` for Decimal/Rational

Restating the frozen P3/P4 rows in WIT terms, since this is the mismatch the
issue is most emphatic about:

**WIT's canonical ABI numeric primitives** are exactly the fixed-width set:
`u8`/`u16`/`u32`/`u64`, `s8`/`s16`/`s32`/`s64`, `f32`, `f64`. There is no
arbitrary-precision integer, no decimal, and no rational primitive of any
kind. This is stated plainly, not softened.

- **Integer** (arbitrary-precision, R17/R22 §1) → **adapted**: WIT has no
  primitive that can hold Genia's full arbitrary-precision Integer domain.
  A small Integer that fits a fixed-width WIT integer type could
  technically use `s64` (or `u64` for a known-non-negative domain), but
  this is only valid for the *subset* of Integer values that fit — using a
  fixed-width WIT integer as *the* representation for Genia Integer in
  general would silently truncate/overflow for anything outside that range,
  which P4 explicitly forbids ("never a fixed-width silent-truncation host
  integer"). The general, always-correct adapter represents Integer as an
  explicit sign-and-magnitude structural record over WIT primitives that
  are themselves always exact:
  ```text
  record genia-integer {
    negative: bool,
    magnitude-digits: list<u32>,   // base-2^32 limbs, big-endian or a fixed
                                    // documented limb order; exact choice is
                                    // implementation-phase, not fixed here
  }
  ```
  or equivalently a decimal-digit-string encoding (`string`, containing the
  exact canonical decimal digit spelling R23 already defines for *display*,
  reused here only as one possible lossless *transport* encoding, per P4's
  own allowance: "A future codec may choose to reuse R23's rendering text
  as one possible lossless encoding"). Either shape is **adapted**, never
  `s64`/`u64` alone as the general case. `retrieve/4`'s own Integer fields
  (`dims`, `k`, `timeout_ms`) are all contractually bounded to small
  ranges (`dims > 0` and equal to vector length; `k` in `1..1000`;
  `timeout_ms` in `1..300000`) and therefore fit safely in `u32` for *this
  specific proof target* — but this document does not generalize that
  narrow fact into "Integer maps to u32," because that would be false for
  Integer in general.
- **Decimal** (R22 §2, exact `coefficient * 10^exponent`) → **adapted, never
  `f64`**: represented as an explicit tagged record over the same exact
  arbitrary-precision Integer representation above:
  ```text
  record genia-decimal {
    coefficient: genia-integer,   // sign carried here, per R22 §2 canon
    exponent: s32,                // exponent magnitude is realistically
                                    // small; s32 is a pragmatic choice for
                                    // this proof, not a general guarantee
                                    // for every conceivable exponent value
  }
  ```
  This preserves R22 §2's exact canonical `(coefficient, exponent)` pair
  after canonicalization (trailing-zero-stripped coefficient, sign carried
  by coefficient, no negative-zero identity) exactly as P4 requires — "never
  a host `decimal.Decimal`/`float` standing in for this pair."
- **Rational** (R22 §3, exact reduced `numerator/denominator`) → **adapted,
  never `f64`, never a finite-Decimal intermediate**:
  ```text
  record genia-rational {
    numerator: genia-integer,     // sign carried here, per R22 §3 canon
    denominator: genia-integer,   // always positive and > 1 for a
                                    // surviving Rational
  }
  ```
  This preserves R22 §3's exact canonical gcd-reduced pair, including
  non-terminating rationals like `1/3`, which R23's own JSON boundary
  cannot represent losslessly but which this provider boundary explicitly
  does not inherit that restriction from (P3's Rational row: "R23 §4.3's
  rule... is a JSON-specific interoperability restriction, not a
  provider-boundary admissibility rule, and is not inherited here").
- **Float64** (R22 §4, one explicit IEEE-754 binary64 bit pattern) →
  **direct for the bit pattern itself, adapted for NaN/sign-of-zero
  fidelity**: WIT's `f64` *is* IEEE-754 binary64, so the underlying bit
  layout is the correct native target — no structural record is needed for
  the numeric payload itself. However, naively passing a WIT `f64` through
  some toolchains' default lowering/lifting can normalize NaN payloads or
  otherwise fail to guarantee sign-of-zero fidelity depending on the
  specific language runtime on the component side (this is a general
  IEEE-754-across-FFI concern, not specific to WIT); P4 requires bit-exact
  preservation "including the sign of zero... and, when present, NaN
  (presence only, no payload/sign guarantee)." For `retrieve/4` this
  concern is narrowed by the interface's own `_is_finite_score` rule
  (§ below): every Float64 that legally crosses this specific boundary is
  already required to be finite (`math.isfinite`), so NaN/infinity
  representability is **out of scope for this specific proof target** —
  `f64` alone is sufficient and direct for `retrieve/4`'s finite-score
  case. A future WIT-mapped interface that legally admits NaN/infinity as
  Float64 payloads (unlike `retrieve/4`) would need to re-examine
  sign-of-zero/NaN-presence fidelity across whatever specific
  language/toolchain implements that component, which is out of scope
  here.

**`retrieve/4`'s `score` field is the one field that exercises all four
kinds in one call** (`_is_finite_score` accepts `int`/`float`/
`GeniaDecimal`/`GeniaRational`, per P8 design §8's table). The WIT-side
representation is therefore a `variant`, not a single numeric type:

```text
variant genia-score {
  score-integer(genia-integer),
  score-decimal(genia-decimal),
  score-rational(genia-rational),
  score-float64(f64),
}
```

**Mapping quality: adapted for Integer/Decimal/Rational (structural record,
never a WIT numeric primitive standing in for the exact value); direct for
Float64's bit-pattern payload alone, narrowed to the finite-only case this
specific proof target legally admits.**

---

## 2. Selecting the WIT proof target

### 2.1 Decision: reuse `retrieve/4`, unchanged from P8

Per the issue's stated preference and `provider-composition-stage0.md`'s own
"Recommended first proof" text, this design reuses `retrieve/4` rather than
inventing a new interface. Justification, restated against WIT specifically
(not merely against P8's original reasons for picking `retrieve/4` over
`embed/4`/`index/4`/`rerank/4`, which still hold and are not repeated here):

- **It already has two real, independently-written realizations** (P8's
  realization A — list-backed, fixed order/score — and realization B —
  dict-backed, computed cosine similarity, `hosts/python/
  r12_retrieve_cosine_fixture.py`). A WIT proof needs exactly this: prove
  that a **third** realization, implemented as an actual compiled WIT
  component rather than a Python closure, can be substituted with
  unchanged application logic and unchanged observable Outcome-shape
  guarantees. This extends P8's already-proven substitution seam
  (host-side handler swap) one step further (component-boundary
  substitution) rather than inventing a new seam.
- **It exercises all four frozen numeric kinds in one field** (`score`),
  which is exactly the hardest numeric-mapping case per §1.11 — proving
  this interface proves the numeric adapter design against real
  reference-host-to-Wasm-and-back data, not only against the abstract P3/P4
  matrix.
- **It exercises E12-4's actual compatibility mechanism** (§1.2), which is
  the concrete case P5's "exact nominal identity + exact opaque revision"
  preflight decision needs a real interoperability test against — a WIT
  package/world boundary is a genuinely different kind of "revision" than
  Python's in-process `object()` identity, so this interface is a
  meaningfully harder test of P5 than a toy interface with no compatibility
  mechanism at all would be.
- **It exercises a live/owned/borrowed resource** (`GeniaIndexHandle`),
  which is the concrete case §1.8's `resource`/`borrow<T>` mapping needs to
  be tested against, and which P2 already names as "an existing concrete
  precursor to a component resource."
- **It exercises R10's just-in-time declassification boundary** (§1.7),
  proving that a credential need not cross into WIT-land as a protected
  carrier at all — a genuinely useful negative result (`retrieve/4` proves
  a WIT proof target does *not* need new credential-transport machinery),
  which a differently-shaped interface without any credential input could
  not demonstrate.
- It does **not** exercise Genia's ordered-Map-with-arbitrary-key-kinds
  mismatch (§1.6) as richly as it could — `retrieve/4`'s only Map input
  (`config`) is small and string-keyed in every existing fixture/test. This
  is the one genuine gap in reusing `retrieve/4` unchanged: the general
  ordered-Map adapter (§1.6) is *designed* against `retrieve/4`'s `config`
  field, but `config`'s actual shape in every current fixture does not
  itself force the adapter to prove non-string-key handling. The
  implementation phase should either (a) extend the WIT proof's test
  fixtures to include at least one Map input with a non-string legal key
  (for example, exercising `retrieve/4`'s `context` fields, several of
  which are small closed maps — `timeout_ms: Integer`, `retry_after_ms:
  option<Integer>` — which do already have non-string-shaped *values*, if
  not non-string *keys*), or (b) explicitly note in the implementation
  design that the general ordered-Map adapter's non-string-key behavior is
  proven only by construction/unit-level Genia-side tests of the adapter
  logic itself, not by this specific WIT interface's actual call traffic.
  This document flags the gap rather than silently declaring it covered.

**No alternative interface was selected instead.** `embed/4`/`index/4`/
`rerank/4` were already rejected by P8 for reasons (weak compatibility
surface, opaque-handle-only observable, no compatibility mechanism at all,
respectively) that apply identically to a WIT proof — a WIT mapping over
any of them would prove strictly less than `retrieve/4` does, for the same
reasons P8 already gives. No smaller interface exists in the current
codebase that would exercise more of §1's mapping surface with less
incidental infrastructure.

### 2.2 What the WIT proof target does and does not prove

Consistent with §2.4 of `provider-composition-preflight.md`'s P9 synthesis
("map one exact Genia interface/revision without making WIT identity
authoritative; preserve approved P3/P4 values and Outcomes; map owned
creation/borrow/expiry/cleanup without weakening R14; keep native/Wasm
objects private; preserve explicit authority/protection; distinguish
operation, component/transport, and R36 failures; reject incompatibility
before call; prove substitution against a non-WIT implementation; and
document mismatches rather than changing Genia. It need not initially prove
Flow/stream equivalence, transparent remoting, arbitrary module export, or a
registry"), the implementation phase's WIT proof should demonstrate:

- one exact `retrieve` WIT interface (§1.1/§1.2), pinned to one exact
  package version;
- a compiled `.wasm` component realizing that interface's handler shape
  (equivalent to P8's handler signature, minus the already-declassified
  credential and minus the never-crossing provider/authority values, per
  §1.9);
- the reference host (Python, via `wasmtime-py` or an equivalent embedding)
  instantiating that component and calling it exactly where realization
  A/B's handler is currently called, with **no change** to
  `GeniaRetriever.__call__`'s public contract, validation order, or
  Outcome-normalization logic — the WIT component is a **third realization
  option**, bound at host-construction time exactly like A/B, never a
  replacement for the fixed interface code;
- identical Outcome-shape observations to realization A/B for the same
  inputs, differing only in score/order content exactly as P8 already
  permits (§1.4's Outcome mapping applies once, at the boundary between
  the component's WIT-typed return and the existing `_FixtureRetrieveResult`
  wrapper the fixed interface code already expects — the component's WIT
  `genia-outcome` return is lowered back into that same existing wrapper
  shape, not into a new Genia value family);
- the three E12-4 compatibility guards (identity/space/dims) rejecting
  before any component call, exactly as P8 §10 already proves for
  A vs. B — proven again here for "component paired with wrong index
  provider," never relying on WIT's own type system to enforce this
  per-pairing check (§1.2);
- no provider-native/Wasm object leakage into any Genia-visible Outcome,
  `display`/`debug_repr` output, or diagnostic (mirroring P8 §11's
  leak-scan pattern, extended to also scan for Wasm/`wasmtime` object
  representations, linear-memory addresses, or component instance
  identifiers);
- one deliberately-broken component variant (a component that traps, or
  that returns a malformed WIT value) to exercise the new L3 layer (§1.10)
  distinctly from L1/L2, proving L3's normalized diagnostic never leaks raw
  Wasm trap text/instruction pointers/stack traces, mirroring PAI-8.

This document does **not** claim these are already proven — they are the
implementation phase's required proof obligations, traced from this
mapping, not results already achieved in this design-only phase.

---

## 3. Toolchain feasibility findings

### 3.1 What was checked in this design phase

Per the issue's explicit instruction, this phase performed only a
feasibility check, not a full install:

```text
$ which wasmtime wasm-tools wit-bindgen
(no output — none of the three is installed in this environment)

$ cargo --version
cargo 1.94.1 (29ea6fb6a 2026-03-24)

$ rustc --version
rustc 1.94.1 (e408947bf 2026-03-25)

$ cargo search wasm-tools 2>&1 | head -5
    Updating crates.io index
wasm-tools = "1.259.0"
wit-bindgen-cli = "0.62.0"
wit-component = "0.259.0"
wit-component-update = "0.205.0"
oxide-agent = "0.1.0"

$ cargo search wasmtime-cli 2>&1 | head -5
wasmtime-cli = "49.0.0-rc.1"
wasmtime-cli-flags = "49.0.0-rc.1"
kangarootwelve = "0.1.3"
...
```

### 3.2 Findings

- **A modern Rust toolchain (`cargo`/`rustc` 1.94.1) is already present** in
  this environment. This is sufficient to build the WIT/component-model
  toolchain from source via `cargo install`.
- **`cargo search` succeeds and reaches the live crates.io index through
  this environment's outbound proxy.** This is direct, positive evidence
  that `cargo install` of published crates is reachable over the network
  from this environment — the search query itself performs a real registry
  round trip and returned current, correctly-versioned results (`wasm-tools
  1.259.0`, `wit-bindgen-cli 0.62.0`, `wasmtime-cli 49.0.0-rc.1`), not
  cached or stale data. No proxy/network/registry failure was observed at
  any point in this check.
- **None of `wasmtime`, `wasm-tools`, or `wit-bindgen` is pre-installed** in
  this environment's `PATH`. All three would need to be installed in the
  implementation phase.
- **Full `cargo install` was deliberately not run** in this design phase,
  per the issue's explicit instruction ("Do NOT do a full `cargo install`
  yet... that's implementation-phase work and can take a long time"). This
  means build time, disk usage, and dependency-resolution success for the
  *actual* install are not yet empirically confirmed — only registry
  reachability is confirmed. This is the one honest residual risk this
  design phase leaves open (see §3.4).

### 3.3 Exact pinned-version plan for the implementation phase

Based on the versions `cargo search` returned (current as of this design
phase; the implementation phase should re-check for newer patch releases
before installing, but should pin an exact version rather than tracking
`latest`, consistent with P5's "exact nominal identity + exact opaque
revision" discipline applied to the toolchain itself):

```bash
# WIT tooling: parse/validate/print .wit, and embed a WIT world into a
# component (or resolve a component's own embedded world).
cargo install --locked wasm-tools --version 1.259.0

# WIT binding generation for Rust component implementations/guests.
cargo install --locked wit-bindgen-cli --version 0.62.0

# Component runtime: instantiate and call a compiled component from the
# reference host (Python) via a wasmtime embedding, or from the CLI for
# standalone verification.
cargo install --locked wasmtime-cli --version 49.0.0-rc.1
```

Notes for the implementation phase:

- `--locked` pins each crate's own dependency tree to its published
  `Cargo.lock`, avoiding incidental drift from an unrelated transitive
  dependency update between this design phase and the implementation
  phase's actual install.
- `wasmtime-cli` at `49.0.0-rc.1` is a release candidate at the time of
  this check; the implementation phase should re-run `cargo search
  wasmtime-cli` immediately before installing and prefer the first
  subsequent stable `49.x.y` release if one has shipped, to avoid pinning
  implementation work to a pre-release build. If no stable release exists
  yet, pinning the exact `49.0.0-rc.1` string (never a bare `49` or a
  semver range) is still consistent with this document's exact-pin
  discipline.
- For calling a compiled component from the Python reference host (the
  natural embedding point for a `retrieve/4` realization, per §2.2), the
  implementation phase will additionally need a Python-side Wasmtime
  embedding (for example the `wasmtime` PyPI package, which wraps the same
  underlying Wasmtime engine `wasmtime-cli` uses) — this was not checked in
  this design phase (no Python package installation was performed, per the
  "no implementation" scope) and should be verified for registry
  reachability (PyPI, via the same proxy) in the implementation phase
  before being assumed available.
- The implementation phase should record the *actual* installed versions
  (via `wasm-tools --version`, `wit-bindgen --version`, `wasmtime
  --version`) in its own commit/PR description once installed, rather than
  assuming these exact pinned versions installed byte-for-byte identically
  — a `cargo install` can still resolve slightly different transitive
  dependencies even with `--locked` if the upstream crate's own lockfile
  changes between this check and the actual install.

### 3.4 Explicit feasibility verdict

**Feasible, not yet fully confirmed.** Registry reachability is positively
confirmed (`cargo search` succeeded against the live index through the
proxy); a working Rust toolchain capable of building these crates from
source is already present. Nothing observed in this design phase indicates
network, sandbox, or registry blockage. The residual, explicitly-named risk
is that this design phase did not perform the actual `cargo install` (by the
issue's own instruction), so build time/disk footprint/transitive
dependency resolution for these specific crates in this specific sandboxed
environment remain unconfirmed until the implementation phase actually runs
the install. **This is not a BLOCKED verdict** — there is no evidence of
infeasibility, only an appropriately-scoped design-phase limit on how far
feasibility was verified. If the implementation phase's actual install
fails for a reason distinct from anything found here (for example, a
sandbox disk-quota or build-time-limit failure specific to compiling a
large Rust dependency graph), that is new evidence the implementation phase
must report honestly at that time, per the issue's own instruction to
report infeasibility honestly rather than fake a pass.

---

## 4. Mismatch table

Mapping-quality legend: **direct** (WIT already expresses the Genia
semantics with no adapter), **adapted** (WIT can express it faithfully
through an explicit, documented adapter shape), **lossy** (any WIT
representation loses or weakens a semantic guarantee Genia requires),
**not-representable** (no WIT construction preserves the semantics; the
value must not cross as WIT data), **intentionally-unsupported** (deliberately
excluded from crossing at all, per an existing Genia contract, not a WIT
limitation).

| Genia concept | WIT concept | Mapping quality | Adapter required | Semantic risk | Decision |
| --- | --- | --- | --- | --- | --- |
| Integer (arbitrary-precision) | no native equivalent; `s64`/`u64` are fixed-width | **adapted** | Yes — explicit sign+magnitude structural record (`genia-integer`) or canonical-digit-string encoding; never a bare fixed-width WIT integer as the general representation | Silent truncation/overflow if a fixed-width WIT integer is used directly for values outside its range | Use `genia-integer` record generally; `retrieve/4`'s specific contractually-bounded Integer fields (`dims`, `k`, `timeout_ms`) may pragmatically use `u32` for *this interface only*, never generalized to "Integer = u32" |
| Decimal (exact coefficient×10^exponent) | none; `f64` is the nearest primitive but wrong | **adapted, never `f64`** | Yes — explicit `genia-decimal { coefficient: genia-integer, exponent: s32 }` record | Substituting `f64` silently loses exactness and violates P4's explicit prohibition; a naive decimal-string encoding without a documented canonical form risks round-trip drift | Explicit tagged record over `genia-integer`; reject any `f64`-based shortcut outright |
| Rational (exact numerator/denominator) | none; `f64` is the nearest primitive but wrong | **adapted, never `f64`** | Yes — explicit `genia-rational { numerator: genia-integer, denominator: genia-integer }` record | Substituting `f64` or a finite-Decimal intermediate loses exactness for non-terminating rationals (e.g. `1/3`) | Explicit tagged record over `genia-integer`; reject `f64`/finite-Decimal shortcuts outright |
| Float64 (exact IEEE-754 binary64 bit pattern) | `f64` (also IEEE-754 binary64) | **direct** for the bit-pattern payload; narrowed to the finite-only case for `retrieve/4` | None beyond the `f64` primitive itself for the finite case this interface admits | Toolchain-dependent NaN-payload/sign-of-zero fidelity across some component-side languages is a general IEEE-754-FFI concern, out of scope because `retrieve/4`'s own `_is_finite_score` already excludes NaN/infinity from this specific boundary | Use bare `f64` for `retrieve/4`'s finite-only score case; re-examine NaN/sign-of-zero fidelity per-language if a future interface admits non-finite Float64 |
| ordered Map with R18 key identity | none; nearest built-ins are `record` (fixed string-literal fields) and `list<tuple<K,V>>` (ordered, arbitrary key/value, no enforced uniqueness/canonical-identity) | **adapted** | Yes — `type genia-ordered-map = list<genia-map-entry>` plus explicit host-side canonicalization (construction), order-preservation discipline (consumption), and duplicate-key/key-legality re-validation (every inbound crossing) | WIT's type system cannot itself enforce key uniqueness, canonical R18 identity, or order preservation — a type-valid `genia-ordered-map` can still violate R18/R17 semantics if a WIT-side component does not honor the adapter's documented discipline; enforcement is entirely adapter-code-side, not WIT-type-side | Use the `list<genia-map-entry>` adapter with mandatory host-side re-validation on every inbound crossing; treat this as the design's highest-risk mismatch and require an explicit negative-test scenario in the implementation phase |
| Outcome (`some`/`none`/`err` + context) | `result<T, E>` (two cases only) | **adapted** (three-case `variant`, not `result`) | Yes — explicit `genia-outcome` three-case `variant`, each case carrying its own record with an optional `context` field | Using `result<T, E>` directly is **lossy**: `none(reason, context)`'s distinct semantic-absence meaning and its own reason/context would have to be folded into either `ok` or `err`, both of which falsify R18's Outcome-equality rule that `some`/`none`/`err` never conflate | Never map Outcome to `result<T, E>`; use the three-case `variant` shape defined in §1.4 |
| represented value (R9 facet stack + carried value) | none; nearest is `record` | **adapted** | Yes — `genia-represented-value { facets: list<facet-descriptor>, carried: ... }`, facet catalog scoped per-interface (only `json` needed for `retrieve/4`'s `chunk.meta`) | A prematurely general facet catalog could imply facet kinds/metadata shapes not yet contract-approved; scope the catalog narrowly to what the proof target actually needs | Define only the facet kinds the proof target's fields actually use; do not invent a general facet catalog in this design |
| protected value (R10 protected carrier) | none; must never be a WIT payload type at all | **intentionally-unsupported** as a carrier; the already-declassified payload it protects, once declassified host-side, is **direct** (plain WIT primitive) | No adapter for the carrier itself — declassification happens host-side, before any WIT call, exactly as it already does for every existing R12 realization | Inventing a WIT-side protected-carrier crossing would require new credential-transport machinery R10 explicitly defers and this document explicitly declines to invent | Never cross the protected carrier itself; cross only the already-declassified ordinary value, exactly mirroring the existing Python handler signature |
| semantic token (R18 opaque token) | none; nearest is an opaque `record` of hidden fields — but that would expose what R18 keeps hidden | **not-representable without a new contract** (not needed for `retrieve/4`, no current value in this proof target is a token) | Not designed here — flagged as an open question for a future token-carrying interface | Materializing R18's three hidden equality components as visible WIT record fields would leak information R18 explicitly keeps opaque at the Genia language level | Do not design a token adapter in this document; defer to a future contract when a real token-carrying interface exists |
| live resource (R14/R18 identity-bearing handle, e.g. `GeniaIndexHandle`) | `resource` / `own<T>` | **adapted**, structurally close | Yes — a zero-method `resource index-handle {}`; ownership transfer rules mirrored from P2 | An owning-side implementation must not allow a WIT-side component to retain/leak the resource beyond the contract's own P2 ownership rules; WIT's `own<T>` transfer-once discipline is a reasonable structural match but must still be independently confirmed against P2's specific scenario matrix, not assumed automatically equivalent | Use `resource`/`own<T>` for owned handles; require the implementation phase's feasibility test (§1.8) before treating this as proven |
| borrow (R14/P2 bounded non-owning view) | `borrow<T>` | **adapted, lossy relative to the full P2 rule set** | Yes — pass `borrow<index-handle>` for `retrieve/4`'s read-only, single-call handle use | WIT's Canonical ABI borrow-lifetime enforcement covers only one component-to-component call; it does not know about or enforce P2's fuller escape-prohibition list (closure capture, Flow emission, List/Map insertion, multi-level scope structure) — those remain solely Genia-side adapter responsibilities regardless of the WIT mapping | Use `borrow<T>` for the call-scoped case `retrieve/4` needs; do not claim WIT's borrow check alone satisfies P2's full escape-prohibition list — Genia-side enforcement remains mandatory in addition |
| interface revision (E12-4 exact identity/compatibility) | `world`/package version | **adapted** | Yes — WIT package version covers only the outer interface-shape identity; E12-4's actual per-instance pairing compatibility (space/dims/identity) must still be carried as explicit record data and checked by adapter logic, not inferred from WIT version compatibility | Some WIT/component tooling applies semver-range reasoning at the tooling level even though the model treats exact versions as exact identities for linking; implementation-phase tooling configuration must pin exact versions and never let semver-range convenience leak into what Genia treats as compatible | Pin one exact WIT package version per interface revision; represent E12-4's per-pairing compatibility as ordinary record fields checked by adapter logic, never by WIT version matching alone |
| authority (R10 `GeniaDeclassificationAuthority`) | none; never a WIT payload type | **intentionally-unsupported** | No adapter — authority never crosses; declassification happens host-side before any WIT call | Any WIT-side authority crossing would weaken PAI-7's capability/credential/authority separation for the sake of WIT convenience, which the issue explicitly forbids | Never cross authority as a WIT value; keep all declassification host-side, exactly as today |
| provider realization failure (L1/L2 per P6) | `result<T, E>` in isolation would conflate this with L1 Outcome and with the new L3 layer | **adapted** (kept as its own layer, not a WIT type per se) | Yes — L2 failures are Genia/adapter-side pre-call validation (never reach the WIT call at all); they are not represented as any WIT value, they prevent the WIT call from happening | Treating a WIT type-level validation failure as though it were an L1 Outcome (`err(...)`) would conflate "the call could not even be attempted" with "the call was attempted and failed" | Keep L2 as pure pre-call Genia/adapter-side rejection; never represent it as a WIT `result`/`variant` case |
| WIT/component transport/runtime failure (new L3) | Canonical ABI traps, instantiation failures, lifting/lowering failures | **adapted** (newly named layer, no prior Genia equivalent) | Yes — a normalized, non-sensitive diagnostic distinct from both L1 `err(...)` and L2 misuse, defined in §1.10; exact vocabulary is implementation-phase work | Silently folding a Wasm-level trap into an ordinary L1 `err(...)` (as if it were merely "the realization failed normally") hides a strictly worse failure mode (the component crashed/misbehaved at the runtime level) behind the same shape an ordinary handler exception already produces | Define L3 as its own named, normalized diagnostic layer distinct from L1/L2/L4; never collapse into any of the other three |
| Flow/Seq | no attempted mapping in this proof; WIT 0.3's `stream<T>`/`future<T>` exist but are not used here | **intentionally excluded**, per the issue's own instruction | Not designed here | `retrieve/4` is synchronous and single-attempt; Flow/Seq's lazy pull/single-use/bounded-demand contract (per `provider-composition-stage0.md`'s own "Flow ↔ WIT `stream<T>`/`future<T>`" row: "Separate design for buffering, demand, cancellation, cleanup, and backpressure. No implicit equivalence.") is a materially harder, separately-scoped design problem that this proof target does not exercise at all | Excluded from this proof entirely; a future interface that genuinely streams evidence (unlike `retrieve/4`'s one-shot bounded-`k` result) would need its own separate Flow/`stream<T>` design, not an assumption carried over from this document |

---

## 5. House rules confirmed against this design

Restating each `stage0.md` house rule against this specific mapping, as P8's
design document did for its own scope:

1. **Providers are opaque capabilities, not class hierarchies.** A WIT
   component realizing `retrieve/4`'s handler is bound exactly like
   realization A/B — a third opaque realization option chosen at
   host-construction time, never a WIT-visible class hierarchy or registry.
2. **Explicit, not ambient.** §1.9/§2.2: which component is instantiated is
   a host-bootstrap-time decision, never an ambient WIT `world` import
   lookup or discovery mechanism.
3. **Construction/binding is inert.** Instantiating a Wasm component is
   itself not an "attempt" in R12's sense — it is analogous to constructing
   a `GeniaRetrieveProvider`, not calling it; the actual retrieval attempt
   remains the one explicit `GeniaRetriever.__call__` invocation, unchanged.
4. **Provider replacement requires semantic compatibility, not method-name
   matching.** §1.2/§2.2: the three E12-4 guards remain the compatibility
   check; WIT interface-shape matching is necessary but not sufficient —
   the per-pairing identity/space/dims check still runs as ordinary
   Genia-side logic regardless of WIT.
5. **Raw host errors never cross unnormalized.** §1.10 L3: Wasm traps are
   normalized before crossing into any Genia-visible diagnostic, mirroring
   PAI-8 exactly for the new component-transport case.
6. **Missing declared capability fails closed.** Unchanged: `construct_
   retrieve`'s existing `TypeError` guard on a non-`GeniaRetrieveProvider`
   value applies identically regardless of whether the eventual handler is
   Python or WIT-backed — the provider *object* Genia source holds is
   still the same opaque `GeniaRetrieveProvider` Python type either way;
   only what its `_handler` closure does internally changes (it may now
   call into a Wasmtime instance instead of pure Python).
7. **R20 open-function dispatch is not used for provider/realization
   selection.** No open function or multi-clause dispatch selects or
   invokes the WIT component anywhere in this mapping; selection remains
   fixed entirely at host-side construction, exactly as P8 §6 already
   establishes for A/B.

---

## 6. Open questions for the implementation phase

1. **Ordered-Map non-string-key coverage.** §2.1 flags that `retrieve/4`'s
   own `config` field never forces the general `genia-ordered-map` adapter
   to prove non-string-key handling through real call traffic. The
   implementation phase must decide whether to extend the proof's fixtures
   to exercise a non-string-keyed Map through the actual WIT boundary, or
   to explicitly scope that coverage to adapter-level unit tests instead
   and say so.
2. **L3 diagnostic vocabulary.** §1.10 fixes that L3 must exist as its own
   named layer but does not fix its exact normalized reason/context
   vocabulary (distinct from L1's existing `retrieve-*` reasons). The
   implementation phase must design this vocabulary, scoped narrowly to
   genuine component/runtime-level failures (traps, instantiation
   failures, lifting/lowering failures), never reused for ordinary
   realization-level failures L1 already names.
3. **Exact WIT identifier/record-field naming.** Every WIT snippet in this
   document (`genia-outcome`, `genia-decimal`, `genia-map-entry`, etc.) is
   illustrative of the required *shape*, not a locked grammar or final
   identifier spelling. The implementation phase owns the actual `.wit`
   file's naming, package path, and exact field ordering.
4. **Limb order / exact encoding for `genia-integer`.** §1.11 leaves the
   exact magnitude-digit limb order (or the alternative canonical-string
   encoding) as an implementation-phase choice, consistent with P4's own
   "concrete coefficient/exponent wire encoding is a later codec choice."
5. **Exponent width for `genia-decimal`.** §1.11's `exponent: s32` is a
   pragmatic choice for this proof target's realistic exponent magnitudes;
   it is not a general guarantee that every conceivable R22 Decimal
   exponent fits `s32`. The implementation phase should confirm this
   against R22 §11's resource-limit normalization rather than assume it.
6. **Opaque-token WIT shape.** §1.7 explicitly defers a semantic-token
   adapter design because no current `retrieve/4` value is a token. The
   first future interface that does carry a token (for example a planned
   Store `Revision`) will need to resolve the hidden-field-exposure tension
   this document raises but does not solve.
7. **`wasmtime`-Python-embedding registry reachability.** §3.3 notes the
   Python-side Wasmtime embedding package was not checked for PyPI
   reachability in this design phase (only the Rust-crate/crates.io path
   was checked). The implementation phase should verify this separately
   before assuming it is available.
8. **Toolchain version drift between this check and actual install.** §3.3
   already asks the implementation phase to re-verify exact versions
   immediately before installing rather than trusting this document's
   snapshot; this is restated here as a formal open item so it is not
   missed.
9. **Whether a stable `wasmtime-cli` has shipped past `49.0.0-rc.1`.** Noted
   in §3.3; the implementation phase should prefer a stable release if one
   exists by the time it installs.

---

## Non-goals

Restating explicitly, consistent with the issue's own Non-goals section:

- No implementation of the WIT interface, no adapter code, and no actual
  component build in this document.
- No Genia semantic change of any kind — Outcome, exact numerics, Flow,
  map/equality, representation, protected values, lifecycle, authority, and
  diagnostics are all used exactly as their existing approved contracts
  define them.
- No solving of any mismatch by changing Genia semantics; every lossy or
  not-representable mapping above is documented honestly rather than
  resolved by weakening a Genia guarantee.
- No claim that any mapping in this document has been executed against
  real WIT tooling — §3 confirms feasibility, not execution; §2.2's proof
  obligations are for the implementation phase, not results already
  achieved here.
- No R36 behavior introduced; §1.10's L4 layer is named for completeness
  only and remains exactly as unimplemented as it already was.
- No Flow/Seq/`stream<T>`/`future<T>` design, per the mismatch table's
  explicit exclusion.
