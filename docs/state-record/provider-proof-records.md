# Provider-composition proof record

> **Non-authoritative provenance record.** This file preserves, verbatim and unedited, text that was displaced
> from `GENIA_STATE.md` during the #1099 distillation. It is audit material, not part of the truth hierarchy:
> it does not define Genia behavior, and `GENIA_STATE.md` governs. Start with the release, design, and reference
> documents; open this file only to see the exact displaced wording.
>
> Baseline: `GENIA_STATE.md` at `d401f322c692e8c3620509854065692c2605c61a`. Scope: Sections 9.38-9.39 (P8 and P9 proofs).
> Ledger: `docs/analysis/state-distillation-migration-map.json`.

## B276: baseline lines 5901-5914

Moved from GENIA_STATE.md@d401f322, lines 5901-5914 (ledger row B276, moved, sha256 7a91044b35c4bad8)

~~~~~markdown
## 9.38) Provider Composition P8 — retrieve/4 alternate-provider substitution proof (issue #945)

Implements the design in
`docs/design/p8-alternate-provider-substitution-proof-design.md` (issue
#943) as concrete runtime evidence. This is architecture-exploration work
(`docs/analysis/provider-composition-stage0.md`, `docs/analysis/
provider-composition-preflight.md`), **not** a new numbered release --
`retrieve/4`'s public contract, error vocabulary, and Outcome shape
(section 9's R12 entries above) are unchanged.

- **No `src/genia/retrieval.py` change.** `GeniaRetrieveProvider`,
  `GeniaRetriever`, and `create_fixture_retrieve_provider` are exactly as
  R12 (E12-4) left them. Both realizations below are plain Python handler
  closures installed through that unmodified factory.
~~~~~

## B277: baseline lines 5915-5977

Moved from GENIA_STATE.md@d401f322, lines 5915-5977 (ledger row B277, moved, sha256 6b9457028928f0c7)

~~~~~markdown
- **Realization A (existing pattern, reused unmodified).** The
  fixed-order/fixed-score list-backed handler pattern already used by
  `hosts/python/exec_r12_grounded_fixture.py` and
  `tests/unit/test_r12_retrieval_fixture.py`.
- **Realization B (new, issue #945): `hosts/python/
  r12_retrieve_cosine_fixture.py`.** A genuinely distinct implementation
  path: an id-keyed `dict` backend (not realization A's ordered `list`)
  plus a real, deterministic cosine-similarity ranking computed with plain
  Python arithmetic (`dot / (|q| * |s|)`), sorted descending with a
  deterministic index-based tie-break. `score` is the computed similarity
  itself, never a constant. It calls no code from realization A and adds
  no new Genia-visible surface, builtin, or factory.
- **Proof evidence:**
  `tests/unit/test_r12_retrieve_alternate_realization.py` (50 tests,
  parametrized over both realizations where applicable):
  - the identical Genia-source `retrieve(...)`/`r(handle, query, k)` call
    sequence produces a contract-conformant Outcome from either
    realization, with the only difference being which Python handler was
    passed to `create_fixture_retrieve_provider` at host-side bootstrap;
  - binding is explicit only (an unset provider name fails to resolve at
    all; two providers built side by side never cross-invoke each
    other's handler/attempt counter);
  - a retrieve provider paired, via the same unmodified
    `create_fixture_retrieve_provider`, to the same already-built index
    provider passes all three E12-4 compatibility guards
    (identity/space/dims) for either realization;
  - Outcome shape (cardinality bound, chunk provenance, finite score) is
    identical between realizations for the same corpus/query while
    *content* (order, score value) legitimately differs -- realization
    A's constant `1.0` score vs. realization B's genuine computed cosine
    similarity, and a query that lets B rank differently than A's fixed
    insertion order;
  - no provider-internal object (`_FixtureRetrieveResult`,
    `_FixtureIndexResult`, `GeniaIndexHandle`, the compatibility-identity
    `object()`, or a raw `dict`/`list` backend) is ever observable from a
    returned Outcome's `display`/`debug_repr`/`repr`;
  - a handler that raises normalizes to
    `err("retrieve-transport-failure", {kind: other})` with no exception
    text or type name, for both realizations;
  - all four P3/P4 numeric score kinds (Integer, `GeniaDecimal`,
    `GeniaRational`, Float64) and non-numeric chunk/meta evidence survive
    exactly through both realizations' shared normalization path;
  - R18 equality (`genia_equal`), R20 dispatch (`construct_retrieve`/
    `create_fixture_retrieve_provider` are plain Python functions, no
    open-function/dispatch mechanism referenced anywhere in
    `retrieval.py`), R14 lifecycle (confirmed absent from
    `retrieval.py`'s source -- `retrieve/4` never opens a lifecycle
    scope), and Outcome semantics (`some`/`none`/`err`) are all confirmed
    unchanged by this proof;
  - negative scenarios: wrong interface revision (mismatched `dims`),
    incompatible provider (mismatched `space`), incompatible index
    identity, missing/wrong-type provider (fails closed with `TypeError`
    before any handler), provider-internal object leakage, a Local-only
    `GeniaIndexHandle` embedded inside `query`'s map (rejected as misuse
    before any handler), a non-finite (`NaN`/`Infinity`/`-Infinity`)
    score (rejected `retrieve-response-invalid`/`stage: score`), and a
    normalized provider failure with no raw exception text -- each
    proven for both realizations.
  - "Ambiguous binding" is vacuously satisfied and documented as such,
    not forced: `retrieve/4` has no registry or name-lookup a binding
    could ever resolve ambiguously against, so no such scenario is
    constructible; the test instead proves two providers can coexist in
    one environment with zero cross-selection.
~~~~~

## B278: baseline lines 5978-5995

Moved from GENIA_STATE.md@d401f322, lines 5978-5995 (ledger row B278, moved, sha256 403a199061c8ff90)

~~~~~markdown
- **P3/P4 Decimal/Rational non-finite case: does not exist.**
  `GeniaDecimal`/`GeniaRational` (R22) are exact, arbitrary-precision, and
  have no NaN/Infinity representation, so `_is_finite_score` always
  accepts them; only Float64's `math.isfinite` boundary has a non-finite
  case to reject. Documented rather than faked with an artificial test.
- Per `docs/analysis/provider-composition-stage0.md`'s P8 row, this
  resolves P8: "smallest proof of alternate provider realization with
  unchanged application logic," per the row's own exit evidence (two
  realizations with identical portable observations and no
  provider-specific leakage), traced above.

Explicit limitations: this is not a general provider-registry, P5
"name + opaque revision" token, or P7 binding-plan proof -- it stays at
the single explicit-argument scale P8's design fixed. It makes no claim
about `embed/4`, `index/4`, or `rerank/4` needing a second realization.
It is not a new release and adds no new Genia-visible syntax, builtin, or
factory.

~~~~~

## B279: baseline lines 5996-6030

Moved from GENIA_STATE.md@d401f322, lines 5996-6030 (ledger row B279, moved, sha256 d25561ca25944975)

~~~~~markdown
## 9.39) Provider Composition P9 — Genia<->WIT interoperability proof (issues #947, #949, #951)

Implements the design in
`docs/design/p9-genia-wit-interoperability-mapping.md` (issue #947) as
concrete runtime evidence, across two implementation slices
(`docs/design/p9-wit-toolchain-build.md`, issue #949; this section, issue
#951). Like section 9.38, this is architecture-exploration work
(`docs/analysis/provider-composition-stage0.md`), **not** a new numbered
release -- `retrieve/4`'s public contract, error vocabulary, and Outcome
shape (section 9's R12 entries above) are unchanged, and no
`src/genia/retrieval.py` change was required or made.

- **Slice A (issue #949, infrastructure/build evidence): a real compiled,
  validated WIT component.** `wit/genia-retrieve/world.wit` authors
  package `genia:retrieve@0.1.0`: `genia-integer` (sign + base-2^32
  little-endian magnitude limbs), `genia-decimal`
  (`coefficient: genia-integer, exponent: s32`), `genia-rational`
  (`numerator`/`denominator: genia-integer`) -- never a bare fixed-width
  WIT integer or `f64` standing in for any of the three -- a four-case
  `genia-score` numeric variant, a three-case `genia-outcome` variant
  (`outcome-some`/`outcome-none`/`outcome-err`, never a two-case
  `result<T, E>`, per the design doc's explicit rejection of folding
  `none(...)` into either `ok` or `err`), a `genia-ordered-map` adapter
  (`list<genia-map-entry>` over a narrow `map-value` variant of
  Integer/String), and an `index-ref` record carrying E12-4's
  `handle-id`/`space`/`dims` compatibility data (a record, not a WIT
  `resource`, per that slice's documented decision). `wit/
  genia-retrieve-component/` is a small `#![no_std]` Rust crate
  (`wit-bindgen = "0.62.0"`) compiled for `wasm32-wasip2` into a real,
  `wasm-tools validate`-clean Component-Model binary (file version
  `0x1000d`, not a bare core module) whose embedded interface
  (`wasm-tools component wit`) matches the authored `.wit` field for
  field. Toolchain: `wasm-tools 1.259.0`, `wit-bindgen-cli 0.62.0`,
  `wasmtime-cli 49.0.0-rc.1` (explicitly noted as a release candidate --
  no stable release existed at build time), `rustc 1.98.1`.
~~~~~

## B280: baseline lines 6031-6111

Moved from GENIA_STATE.md@d401f322, lines 6031-6111 (ledger row B280, moved, sha256 5b0eea704b15da8d)

~~~~~markdown
- **Slice B (issue #951): a real Python-host adapter and round-trip
  proof, never a mock or simulation.** `hosts/python/
  wit_retrieve_adapter.py` -- a Python-host-only module, never reachable
  from Genia source and never registered in `genia.builtins`, matching
  `hosts/python/r12_retrieve_cosine_fixture.py`'s convention.
  - **Mechanism decision.** The `wasmtime` PyPI package (native Wasmtime
    embedding) was checked per the issue's explicit instruction:
    `uv pip install wasmtime` resolves and installs cleanly
    (`wasmtime==48.0.0`), but its public API in that version exposes only
    core-WebAssembly primitives (`Module`/`Instance`/`Linker`/`Store`) and
    no Component-Model-aware type at all, so it cannot instantiate or call
    a real `wasm32-wasip2` component. The adapter therefore shells out to
    a real `wasmtime run --invoke <component>.wasm <function>(<args>)`
    process (the same pinned `wasmtime-cli` binary slice A validated),
    which does support real component calls, and parses its deterministic
    `wasm-wave` textual output with a small hand-rolled recursive-descent
    parser scoped to this proof's known grammar. The `wasmtime` PyPI
    package is not added as a project dependency and is not used anywhere
    in the adapter or its tests.
  - **Component extension.** `retrieve`'s own slice-A fixture only ever
    emits `score-float64` and never returns a Map, so it alone cannot
    exercise Integer/Decimal/Rational or ordered-Map-as-output through a
    real call. Three pure identity round-trip exports were added to the
    same `.wit`/Rust crate for this reason alone --
    `echo-score`/`echo-outcome`/`echo-map` -- adding no scoring,
    validation, or new Genia semantics; `retrieve`'s own behavior,
    signature, and fixture are byte-for-byte unchanged from slice A.
  - **Conversions.** `GeniaDecimal`/`GeniaRational` (both plain
    arbitrary-precision Python `int` fields, per `src/genia/
    numeric_runtime.py`) convert to/from `genia-decimal`/`genia-rational`
    through the shared `genia-integer` sign+limb encoding with no float
    anywhere in the path; a `GeniaMap` converts to/from
    `genia-ordered-map` by iterating `GeniaMap.items()` (already R17/R18
    canonical-order- and identity-deduplicated by construction), rejecting
    any key/value kind this narrow interface's `map-value` variant does
    not admit (bool, and anything beyond Integer/String) as an L2
    pre-call misuse; `GeniaOptionSome`/`GeniaOptionNone`/`GeniaOptionErr`
    convert to/from the three-case `genia-outcome` variant, including
    `context` fields restricted to this interface's narrow closed
    Integer/Symbol leaf shapes per the design doc's §1.4 scoping.
  - **Failure layering.** L1 (an ordinary `some`/`none`/`err` Outcome) is
    always returned as a value, never raised. L2
    (`WitAdapterMisuseError`) rejects a value this boundary forbids
    crossing at all -- a protected carrier (`GeniaProtected`), a
    non-finite float, an unsupported map-key kind -- entirely on the
    Python side, before any `subprocess` call is made. L3
    (`WitComponentFaultError`) normalizes a genuine nonzero-exit
    `wasmtime` process failure (a missing export, a malformed invocation)
    into one of a closed set of `kind` strings, discarding all raw
    process stderr/backtrace/source-path text before the exception is
    ever raised or observed.
  - **Proof evidence:** `tests/unit/test_p9_wit_retrieve_roundtrip.py`
    (18 tests, every one calling the real compiled component through a
    real `wasmtime` subprocess, skipped rather than faked if the
    toolchain/component is unavailable):
    - a 37-digit `GeniaDecimal` and a full Integer/Decimal/Rational/
      Float64 sweep (including exact `1/3` and an Integer beyond 64 bits)
      round-trip through `echo-score` with zero precision loss;
    - a `GeniaMap` with a non-string (Integer) key round-trips through
      `echo-map` with R17 order and R18 replace-in-place key identity
      intact (a `put` that replaces an existing key does not grow the
      entry count or reorder it);
    - all three Outcome cases round-trip through `echo-outcome`,
      including `err`'s `context` map, and are confirmed pairwise
      distinct constructor kinds, never coerced into one another;
    - a real `retrieve` call (mirroring R12's `retrieve/4` handler shape,
      minus the already-declassified credential and never-crossing
      provider/authority values, per the design doc §1.7/§1.9) exercises
      `some`/`none`/`err` together against the compiled component's own
      fixed three-document fixture;
    - a protected carrier and a non-finite float are rejected by
      `WitAdapterMisuseError` with `subprocess.run` patched to fail the
      test if ever called, proving the L2 rejection happens strictly
      before any component call is attempted;
    - an invalid invocation (a nonexistent export name) raises a
      normalized `WitComponentFaultError` with `kind ==
      "invocation-invalid"`, confirmed to contain no raw Wasmtime process
      text (`wasmtime_internal_core`, `Stack backtrace`, `.rs:`,
      `libc_start`), and is confirmed observably distinct from an
      ordinary `retrieve` call returning `err("retrieve-rejected")` as a
      plain Outcome value.
~~~~~

## B281: baseline lines 6112-6126

Moved from GENIA_STATE.md@d401f322, lines 6112-6126 (ledger row B281, moved, sha256 6cc0f5ac10cfa825)

~~~~~markdown
- Per `docs/analysis/provider-composition-stage0.md`'s P9 row, this
  resolves P9: "map one exact Genia interface/revision without making WIT
  identity authoritative... preserve approved P3/P4 values and
  Outcomes... distinguish operation, component/transport, and R36
  failures... document mismatches rather than changing Genia," per the
  row's own exit evidence, traced above. Every mismatch the design doc
  documented as adapted/lossy by design (arbitrary-precision numerics as
  structural records rather than a WIT primitive, the ordered-map
  adapter's enforcement living entirely in adapter code, `borrow<T>`'s
  narrower per-call scope versus R14's full escape-prohibition list,
  protected carriers/authorities never crossing as WIT values) remains
  exactly as documented; this proof introduces no *new* undocumented
  lossy substitution -- Decimal/Rational never touch a host binary float
  anywhere in this path.

~~~~~

## B282: baseline lines 6127-6137

Moved from GENIA_STATE.md@d401f322, lines 6127-6137 (ledger row B282, moved, sha256 f49dbb7d75cd23b3)

~~~~~markdown
Explicit limitations: `index-ref` is a WIT `record`, not a `resource`/
`borrow<T>` -- the design doc's own named feasibility test for a
host-owned borrowed resource (§1.8) remains future, separately-scoped
work, not performed here. The general `genia-ordered-map` adapter is
exercised only against this interface's narrow `map-value` variant
(Integer/String), not a fully recursive legal-key family. No R36 outer
execution envelope is exercised or claimed (§1.10 L4) -- this is a
same-process, same-machine `wasmtime` component call. This is the last
row in the Stage 0 provider-composition work ledger; it is not a new
release and adds no new Genia-visible syntax, builtin, or factory.

~~~~~
