# P9 slice A — WIT toolchain install, `.wit` authoring, and component build/validation

Status: **Infrastructure/build evidence, non-authoritative.** `GENIA_STATE.md`
remains final authority for implemented Genia behavior. This document adds
no Genia semantics, no runtime code, no Python adapter, and no round-trip
test — it is the reproducible-build record required by
[issue #949](https://github.com/m0smith/genia-2026/issues/949) (P9
implementation slice A), which implements the design in
`docs/design/p9-genia-wit-interoperability-mapping.md` (merged, commit
`ce3aa5b`, [issue #947](https://github.com/m0smith/genia-2026/issues/947)).

Slice B (Python-host adapter, round-trip tests against the real component
built here) is separately scoped future work; this document proves the WIT
authoring and component-build/validation mechanics only.

---

## 0. What this slice proves

- A pinned, real WIT/component-model toolchain (`wasm-tools`,
  `wit-bindgen-cli`, `wasmtime-cli`) installs and runs in this environment.
- A `.wit` package implementing the design doc's §1/§2/§4 mapping for the
  R12 `retrieve/4` proof target parses and round-trips through real
  `wasm-tools` tooling.
- A real, compiled `.wasm` **component** (not a bare core module) realizing
  that interface builds from a small Rust crate using `wit_bindgen::generate!`.
- That component validates (`wasm-tools validate`), its embedded interface
  matches the authored `.wit` (`wasm-tools component wit`), and it loads,
  instantiates, and returns correct, deterministic results for all three
  Outcome cases (`some`/`none`/`err`) under a real `wasmtime` invocation.

---

## 1. Toolchain install

### 1.1 Starting state

This environment ships a Rust toolchain already (`rustc`/`cargo` via
`rustup`). At the start of this slice:

```text
$ rustc --version
rustc 1.94.1 (e408947bf 2026-03-25)
$ cargo --version
cargo 1.94.1 (29ea6fb6a 2026-03-24)
```

### 1.2 Re-checking `wasmtime-cli`'s release status

Per the design doc's §3.3/§6.9 open item, this slice re-checked whether a
stable `wasmtime-cli` release had shipped past the release candidate found
during design:

```text
$ cargo search wasmtime-cli
wasmtime-cli = "49.0.0-rc.1"              # Command-line interface for Wasmtime
...
```

**No stable release exists past `49.0.0-rc.1` as of this slice (2026-09-19).**
Per the issue's own instruction ("If only an RC is available, install that
and note it explicitly as an RC"), this slice installs and pins the exact
release-candidate string `49.0.0-rc.1` — never a bare `49` or a semver
range, consistent with the design doc's exact-pin discipline (§1.2/§3.3).

### 1.3 `wasm-tools` and `wit-bindgen-cli`

```text
$ cargo install --locked wasm-tools --version 1.259.0
...
  Installing /root/.cargo/bin/wasm-tools
   Installed package `wasm-tools v1.259.0` (executable `wasm-tools`)

$ cargo install --locked wit-bindgen-cli --version 0.62.0
...
  Installing /root/.cargo/bin/wit-bindgen
   Installed package `wit-bindgen-cli v0.62.0` (executable `wit-bindgen`)
```

Both installed cleanly on the first attempt with the exact pinned design-doc
versions.

### 1.4 `wasmtime-cli` — rustc version blocker and resolution

The first `cargo install --locked wasmtime-cli --version 49.0.0-rc.1`
attempt failed — a genuine, precisely-diagnosed blocker, not a fabricated
one:

```text
$ cargo install --locked wasmtime-cli --version 49.0.0-rc.1
    Updating crates.io index
 Downloading crates ...
  Downloaded wasmtime-cli v49.0.0-rc.1
error: cannot install package `wasmtime-cli 49.0.0-rc.1`, it requires rustc 1.96.0 or newer, while the currently active rustc version is 1.94.1
`wasmtime-cli 47.0.4` supports rustc 1.94.0
```

This environment's Rust toolchain (`rustc 1.94.1`) was older than
`wasmtime-cli 49.0.0-rc.1`'s minimum supported Rust version (1.96.0).
Resolution: `rustup update stable`, which is an ordinary toolchain upgrade
available in this environment, not a design/sandbox workaround:

```text
$ rustup update stable
...
  stable-x86_64-unknown-linux-gnu updated - rustc 1.98.1 (48a229cea 2026-09-01) (from rustc 1.94.1 (e408947bf 2026-03-25))
```

With `rustc 1.98.1` (which also satisfies `wasm32-wasip2`'s MSRV, used
below), the pinned install then succeeded:

```text
$ cargo install --locked wasmtime-cli --version 49.0.0-rc.1
...
    Finished `release` profile [optimized] target(s) in 5m 40s
  Installing /root/.cargo/bin/wasmtime
   Installed package `wasmtime-cli v49.0.0-rc.1` (executable `wasmtime`)
```

### 1.5 Exact installed versions (final)

```text
$ wasm-tools --version
wasm-tools 1.259.0

$ wit-bindgen --version
wit-bindgen-cli 0.62.0

$ wasmtime --version
wasmtime 49.0.0-rc.1

$ rustc --version
rustc 1.98.1 (48a229cea 2026-09-01)

$ cargo --version
cargo 1.98.1 (797e8a9bc 2026-08-05)
```

`wasmtime-cli` remains at the release-candidate version `49.0.0-rc.1`,
explicitly noted as an RC, per the design doc's and issue's instruction —
this is not a stable release.

### 1.6 Required Wasm targets

```text
$ rustup target add wasm32-wasip2
$ rustup target add wasm32-wasip1
$ rustup target add wasm32-unknown-unknown
```

Only `wasm32-wasip2` is used for the final component build (§3); the other
two were explored and are documented as a rejected path in §3.1.

---

## 2. `.wit` file location and content

Location: `wit/genia-retrieve/world.wit` — a new top-level `wit/` directory,
kept clearly separate from `src/genia/` (the Python package) and from the
`hosts/rust/` directory (a currently-empty stub for a future Rust *host*,
not this WIT proof-of-concept component). No existing `wit/`-shaped
convention existed in this repository before this slice
(`find . -iname "*.wit" -o -iname "wit"` returned nothing beyond this
slice's own new files).

The file implements, package `genia:retrieve@0.1.0`, two interfaces:

- `types` — `genia-integer` (sign + base-2^32 magnitude limbs, little-endian
  limb order), `genia-decimal` (`coefficient: genia-integer, exponent: s32`),
  `genia-rational` (`numerator`/`denominator: genia-integer`), the
  four-case `genia-score` numeric variant, the narrow `context-value`
  leaf shapes, the `genia-ordered-map` adapter
  (`list<genia-map-entry>`), the three-case `genia-outcome` variant
  (`outcome-some`/`outcome-none`/`outcome-err`, never a two-case
  `result<T, E>`), the `evidence` record (`{chunk: string, score:
  genia-score}`), and `index-ref`.
- `retrieve` — one function, `retrieve(query-embedding: list<f64>, k: u32,
  index: index-ref, config: genia-ordered-map) -> genia-outcome`, exported
  by `world genia-retrieve-world`.

Every type/shape decision traces directly to the design doc's §1/§4; see the
inline doc comments in `wit/genia-retrieve/world.wit` itself for the exact
citation of each one. Two of the design doc's explicitly-open decisions
(§6) are resolved and documented in that file, restated here:

### 2.1 Index identity representation (design doc §6, open item; issue #949 step 2)

A live Python `GeniaIndexHandle` object cannot cross the Wasm boundary.
**Decision:** represent index identity as an explicit `index-ref` record —
an opaque `handle-id: u64` plus the exact `space`/`dims` pair E12-4's
per-pairing compatibility check needs (design doc §1.2) — never as a WIT
`resource`/`borrow<T>`.

**Rationale:** the design doc's §1.8 already classifies `resource`/
`borrow<T>` as the structurally correct *future* target, and separately
names its own feasibility test (host-owned resource, borrow-trap-on-escape,
single-transfer `own<T>`) as "recommended for the implementation phase,"
distinct in scope from proving the WIT/component mechanics work at all for
a first build. A host-owned *imported* `resource` requires the Wasmtime
host embedding to supply a real resource implementation for the guest to
borrow against — materially more machinery than this slice's first-component
goal needs. The `index-ref` record still carries exactly the data E12-4's
compatibility check needs, and the *identity* guard (object identity, the
first and strictest of E12-4's three ordered guards) remains host-side,
before this call is ever made, regardless of whether `index-ref` is a
record or a resource — the design doc's §1.2 requirement ("carried as
explicit record data and checked by adapter logic, not inferred from WIT
type-level compatibility") is satisfied either way. A future slice may add
the `resource`/`borrow<T>` feasibility test without changing this record's
data shape.

### 2.2 Ordered-Map non-string-key coverage (design doc §6.1, open item)

The design doc's own §2.1 flags that `retrieve/4`'s `config` field never
forces the general ordered-map adapter to prove non-string-key handling
through real call traffic. This slice's `map-value` variant supports both
`map-integer` and `map-string` keys/values (narrower than a fully general
recursive key family, but strictly wider than "string-keyed record only"),
and §4.3 below exercises a non-string-shaped map entry
(`{key: map-string("id"), value: map-string("fixture-1")}`) through the
actual compiled component's real call traffic — resolving the design doc's
open item (a) rather than (b): this slice extends the proof's fixtures to
exercise the ordered-map adapter through the WIT boundary itself, not only
through adapter-level unit tests. A fully general recursive
`provider-boundary-value` key family remains out of scope, per the design
doc's own narrow-scoping note.

---

## 3. Component build

### 3.1 Target selection: `wasm32-wasip2` over `wasm32-wasip1` + adapter

Two standard paths exist to produce a real Wasm **component** (not merely a
core module) from a `wit-bindgen`-generated Rust crate:

1. Build a core module for `wasm32-wasip1`, then run
   `wasm-tools component new` with a separately-obtained WASI Preview 1
   adapter module to lift it into a component.
2. Build directly for `wasm32-wasip2`, which Rust's standard library
   (tier-2, MSRV-gated — hence the rustc 1.98.1 requirement satisfied in
   §1.4) emits as a real Component-Model binary with no separate adapter
   step.

This slice tried (1) first and confirmed it produces a core module
(`wasm-tools validate` accepted it, but `file` reports plain
`WebAssembly (wasm) binary module version 0x1`, and its imports are bare
`wasi_snapshot_preview1.*` functions, not a component). It then used (2),
which is simpler, requires no extra adapter binary, and directly produces a
Component-Model-versioned binary (`file` reports
`WebAssembly (wasm) binary module version 0x1000d`, wasmtime's real
component version tag). `wasm32-wasip2` is the path this slice's final,
committed build uses.

### 3.2 Crate location

`wit/genia-retrieve-component/` — `Cargo.toml`, `Cargo.lock` (committed for
build reproducibility), and `src/lib.rs`. `crate-type = ["cdylib"]`, one
dependency: `wit-bindgen = "0.62.0"` (matching the installed
`wit-bindgen-cli` version exactly). `target/` is gitignored (ordinary build
output, reproducible from the commands below).

The crate's `src/lib.rs` calls
`wit_bindgen::generate!({ path: "../genia-retrieve", world:
"genia-retrieve-world" })`, then implements `exports::genia::retrieve::
retrieve::Guest::retrieve` with a small, fixed, deterministic three-document
fixture scored by dot product against the query embedding — explicitly not
a reimplementation of P8's cosine-similarity realization
(`hosts/python/r12_retrieve_cosine_fixture.py`), per issue #949's own
"you do not need to replicate P8's cosine-similarity logic exactly"
instruction. It also demonstrates all three Outcome cases: `err(...)` for
pre-call misuse (wrong `space`/`dims`/`k == 0`), `none("retrieve-no-results")`
for an all-zero query (a deterministic, meaningful "no relevant evidence"
case), and `some(...)` with ordered evidence otherwise.

### 3.3 Exact build commands

```bash
cd wit/genia-retrieve-component
rustup target add wasm32-wasip2   # if not already installed
cargo build --release --target wasm32-wasip2
```

Output:

```text
$ cargo build --release --target wasm32-wasip2
   Compiling wit-bindgen v0.62.0
   Compiling bitflags v2.13.2
   Compiling genia-retrieve-component v0.1.0 (…/wit/genia-retrieve-component)
    Finished `release` profile [optimized] target(s) in 1.38s
```

Result: `target/wasm32-wasip2/release/genia_retrieve_component.wasm`
(79493 bytes).

```text
$ file target/wasm32-wasip2/release/genia_retrieve_component.wasm
target/wasm32-wasip2/release/genia_retrieve_component.wasm: WebAssembly (wasm) binary module version 0x1000d
```

---

## 4. Validation

### 4.1 `wasm-tools validate`

```text
$ wasm-tools validate target/wasm32-wasip2/release/genia_retrieve_component.wasm
$ echo $?
0
```

No diagnostics; exit code 0.

### 4.2 `wasm-tools component wit` — confirms the compiled component's interface matches the authored `.wit`

```text
$ wasm-tools component wit target/wasm32-wasip2/release/genia_retrieve_component.wasm
package root:component;

world root {
  import genia:retrieve/types@0.1.0;
  import wasi:io/poll@0.2.9;
  import wasi:clocks/monotonic-clock@0.2.9;
  import wasi:io/error@0.2.9;
  import wasi:io/streams@0.2.9;
  import wasi:cli/stdout@0.2.9;
  import wasi:cli/stderr@0.2.9;
  import wasi:cli/stdin@0.2.9;
  import wasi:cli/environment@0.2.9;
  import wasi:cli/exit@0.2.9;
  import wasi:cli/terminal-input@0.2.9;
  import wasi:cli/terminal-output@0.2.9;
  import wasi:cli/terminal-stdin@0.2.9;
  import wasi:cli/terminal-stdout@0.2.9;
  import wasi:cli/terminal-stderr@0.2.9;

  export genia:retrieve/retrieve@0.1.0;
}
package genia:retrieve@0.1.0 {
  interface types {
    record genia-integer {
      negative: bool,
      magnitude-digits: list<u32>,
    }

    record genia-decimal {
      coefficient: genia-integer,
      exponent: s32,
    }

    record genia-rational {
      numerator: genia-integer,
      denominator: genia-integer,
    }

    variant genia-score {
      score-integer(genia-integer),
      score-decimal(genia-decimal),
      score-rational(genia-rational),
      score-float64(f64),
    }

    record evidence {
      chunk: string,
      score: genia-score,
    }

    variant context-value {
      context-integer(genia-integer),
      context-symbol(string),
    }

    record context-entry {
      key: string,
      value: context-value,
    }

    record outcome-context {
      entries: list<context-entry>,
    }

    record outcome-some-payload {
      value: list<evidence>,
      context: option<outcome-context>,
    }

    record outcome-none-payload {
      reason: string,
      context: option<outcome-context>,
    }

    record outcome-err-payload {
      reason: string,
      context: option<outcome-context>,
    }

    variant genia-outcome {
      outcome-some(outcome-some-payload),
      outcome-none(outcome-none-payload),
      outcome-err(outcome-err-payload),
    }

    variant map-value {
      map-integer(genia-integer),
      map-string(string),
    }

    record genia-map-entry {
      key: map-value,
      value: map-value,
    }

    type genia-ordered-map = list<genia-map-entry>;

    record index-ref {
      handle-id: u64,
      space: string,
      dims: u32,
    }
  }
  interface retrieve {
    use types.{genia-outcome, genia-ordered-map, index-ref};

    retrieve: func(query-embedding: list<f64>, k: u32, index: index-ref, config: genia-ordered-map) -> genia-outcome;
  }
}
```

(WASI CLI/IO imports beyond `genia:retrieve/types` are pulled in
automatically by `wasm32-wasip2`'s standard-library linkage — e.g. panic
formatting reaching `wasi:cli/stderr` — and are unrelated to this
interface; they are the host-side implementation's responsibility, not part
of the `retrieve`-shaped semantic interface this slice designs.)

Every field of `export genia:retrieve/retrieve@0.1.0` and its `types`
interface matches `wit/genia-retrieve/world.wit` exactly, field for field —
confirming the compiled component's real, embedded interface round-trips
losslessly against the authored source.

### 4.3 `wasmtime` instantiation and call smoke test

`wasmtime run --invoke` instantiates the component and calls its export
directly (no `wasi:cli/run` command interface is needed for a
library-style, non-command component). Five calls exercise all three
Outcome cases plus the ordered-Map adapter's non-string-key coverage
(§2.2):

```text
$ wasmtime run --invoke 'retrieve([1.0, 0.0, 0.0], 2, {handle-id: 1, space: "p9-fixture-space", dims: 3}, [])' target/wasm32-wasip2/release/genia_retrieve_component.wasm
outcome-some({value: [{chunk: "genia composes providers explicitly", score: score-float64(1)}, {chunk: "WIT records replace f64 for exact numerics", score: score-float64(0)}]})

$ wasmtime run --invoke 'retrieve([0.0, 0.0, 0.0], 2, {handle-id: 1, space: "p9-fixture-space", dims: 3}, [])' target/wasm32-wasip2/release/genia_retrieve_component.wasm
outcome-none({reason: "retrieve-no-results"})

$ wasmtime run --invoke 'retrieve([1.0, 0.0, 0.0], 2, {handle-id: 1, space: "wrong-space", dims: 3}, [])' target/wasm32-wasip2/release/genia_retrieve_component.wasm
outcome-err({reason: "retrieve-capability-incompatible"})

$ wasmtime run --invoke 'retrieve([1.0, 0.0, 0.0], 2, {handle-id: 1, space: "p9-fixture-space", dims: 5}, [])' target/wasm32-wasip2/release/genia_retrieve_component.wasm
outcome-err({reason: "retrieve-capability-incompatible"})

$ wasmtime run --invoke 'retrieve([1.0, 0.0, 0.0], 0, {handle-id: 1, space: "p9-fixture-space", dims: 3}, [])' target/wasm32-wasip2/release/genia_retrieve_component.wasm
outcome-err({reason: "retrieve-rejected"})

$ wasmtime run --invoke 'retrieve([0.5, 0.25, 0.75], 3, {handle-id: 42, space: "p9-fixture-space", dims: 3}, [{key: map-string("id"), value: map-string("fixture-1")}])' target/wasm32-wasip2/release/genia_retrieve_component.wasm
outcome-some({value: [{chunk: "Outcome is three cases, never result<T, E>", score: score-float64(0.75)}, {chunk: "genia composes providers explicitly", score: score-float64(0.5)}, {chunk: "WIT records replace f64 for exact numerics", score: score-float64(0.25)}]})
```

Each call exits 0. Observed results:

- All three `genia-outcome` cases (`outcome-some`, `outcome-none`,
  `outcome-err`) are produced correctly and distinctly, confirming the
  three-case `variant` (never `result<T, E>`) round-trips through a real
  Canonical ABI call.
- Ordering is deterministic and correct: for a query weighted toward one
  fixture axis, the matching document's evidence sorts first by score,
  descending, ties broken by fixture (insertion) order.
- `k` correctly bounds the returned evidence count (`k=2` returns 2 of 3;
  `k=3` returns all 3).
- The `genia-ordered-map` `config` parameter accepts and is read
  successfully with a non-string-shaped-value / string-key entry
  (`map-string("id") -> map-string("fixture-1")`), passed as real call
  traffic through the actual compiled component (§2.2).
- `index-ref`'s `space`/`dims` compatibility guards reject before any
  scoring happens (`retrieve-capability-incompatible`), and `k == 0` is
  rejected (`retrieve-rejected`) — both returned as this component's own
  `err(...)`, consistent with the design doc's L1/L2 layering discussion
  (§1.10) that a component's own pre-scoring validation is a legitimate
  place for such checks to live, distinct from the reference host's actual
  E12-4 identity guard, which stays host-side in any future adapter.

---

## 5. Reproduction from a clean checkout

```bash
# 1. Toolchain (see §1 for the rustc-version caveat)
rustup update stable   # ensures rustc >= 1.96.0 for wasmtime-cli 49.0.0-rc.1
rustup target add wasm32-wasip2
cargo install --locked wasm-tools --version 1.259.0
cargo install --locked wit-bindgen-cli --version 0.62.0
cargo install --locked wasmtime-cli --version 49.0.0-rc.1   # re-check for a
                                                              # stable release
                                                              # first; see §1.2

# 2. Validate the .wit source
wasm-tools component wit wit/genia-retrieve/world.wit

# 3. Build the component
cd wit/genia-retrieve-component
cargo build --release --target wasm32-wasip2

# 4. Validate the built component
wasm-tools validate target/wasm32-wasip2/release/genia_retrieve_component.wasm
wasm-tools component wit target/wasm32-wasip2/release/genia_retrieve_component.wasm

# 5. Smoke-test instantiation and a call
wasmtime run --invoke 'retrieve([1.0, 0.0, 0.0], 2, {handle-id: 1, space: "p9-fixture-space", dims: 3}, [])' target/wasm32-wasip2/release/genia_retrieve_component.wasm
```

---

## 6. Explicit non-goals (restated from issue #949)

- No Python-host adapter code (slice B).
- No round-trip test against the reference host (slice B).
- No change to `pyproject.toml` or any `uv`-managed Python dependency.
- No change to `src/genia/retrieval.py` or any other existing Genia runtime
  code.
- No Stage 0 provider-composition work-ledger row update (deferred until
  slice B completes the full proof).
- No Genia semantic change of any kind, consistent with the design doc's
  own non-goals.
