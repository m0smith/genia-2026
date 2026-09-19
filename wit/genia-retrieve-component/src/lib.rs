//! P9 slice A — minimal Wasm component realizing `genia:retrieve/retrieve`
//! (issue #949).
//!
//! Scope: this component proves the WIT/component *mechanics* (compile,
//! validate, instantiate, call) for the `retrieve/4`-shaped interface
//! designed in `docs/design/p9-genia-wit-interoperability-mapping.md`. Its
//! internal scoring logic is deliberately minimal and deterministic — a
//! fixed three-document fixture scored by dot product against the query
//! embedding — not a reimplementation of P8's cosine-similarity
//! realization (`hosts/python/r12_retrieve_cosine_fixture.py`), per
//! issue #949's explicit "you do not need to replicate P8's
//! cosine-similarity logic exactly" instruction.
//!
//! No Python adapter, no round-trip test, and no Genia-runtime code is
//! touched by this crate (issue #949 non-goals) — it is a standalone
//! Wasm component compiled and validated independently with `wasm-tools`
//! and `wasmtime`, per `docs/design/p9-wit-toolchain-build.md`.

#![no_std]
extern crate alloc;

use alloc::string::ToString;
use alloc::vec;
use alloc::vec::Vec;

wit_bindgen::generate!({
    path: "../genia-retrieve",
    world: "genia-retrieve-world",
});

use exports::genia::retrieve::retrieve::Guest;
use genia::retrieve::types::{
    Evidence, GeniaOrderedMap, GeniaOutcome, GeniaScore, IndexRef, OutcomeErrPayload,
    OutcomeNonePayload, OutcomeSomePayload,
};

/// Compatibility guards this component enforces before ever computing a
/// score, mirroring E12-4's exact ordered guards (design doc §1.2): the
/// reference host is solely responsible for the *identity* guard (it
/// never even calls this component for a mismatched `GeniaIndexProvider`
/// identity); this component independently re-checks the *data* guards
/// (`space`/`dims`) it was handed, because those are the only guards a
/// WIT record can carry as ordinary data (§1.2's documented split between
/// "outer WIT interface-shape identity" and "inner per-pairing data
/// checked by adapter logic").
const EXPECTED_SPACE: &str = "p9-fixture-space";
const EXPECTED_DIMS: u32 = 3;

/// Fixed, deterministic three-document fixture. Each document's vector is
/// a unit basis-ish vector in the fixture's 3-dimensional space, so the
/// dot-product score deterministically favors the axis the query weights
/// most heavily -- sufficient to prove ordering/score plumbing without
/// reimplementing P8's cosine-similarity logic.
const FIXTURE: [(&str, [f64; 3]); 3] = [
    ("genia composes providers explicitly", [1.0, 0.0, 0.0]),
    ("WIT records replace f64 for exact numerics", [0.0, 1.0, 0.0]),
    ("Outcome is three cases, never result<T, E>", [0.0, 0.0, 1.0]),
];

fn dot(a: &[f64], b: &[f64; 3]) -> f64 {
    a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
}

fn err(reason: &str) -> GeniaOutcome {
    GeniaOutcome::OutcomeErr(OutcomeErrPayload {
        reason: reason.to_string(),
        context: None,
    })
}

struct Component;

impl Guest for Component {
    fn retrieve(
        query_embedding: Vec<f64>,
        k: u32,
        index: IndexRef,
        _config: GeniaOrderedMap,
    ) -> GeniaOutcome {
        // Pre-call misuse validation (P6 Layer 2, restated for the WIT
        // component per design doc §1.10): shape/compatibility checks that
        // reject before any "attempt" is made, never surfaced as an L1
        // Outcome `err(...)` in the reference-host's own vocabulary -- this
        // component's own `err(...)` return here models what an L2
        // rejection would look like if it were expressed *inside* a
        // component response rather than short-circuited host-side before
        // the call; the reference-host adapter (slice B's job) is expected
        // to keep the real host-side E12-4 identity guard as the actual L2
        // gate and treat this component-side check only as defense in
        // depth.
        if index.dims != EXPECTED_DIMS {
            return err("retrieve-capability-incompatible");
        }
        if index.space != EXPECTED_SPACE {
            return err("retrieve-capability-incompatible");
        }
        if query_embedding.len() != EXPECTED_DIMS as usize {
            return err("retrieve-embedding-incompatible");
        }
        if k == 0 {
            return err("retrieve-rejected");
        }

        // Deterministic "no results" case: an all-zero query embedding
        // legitimately dot-products to zero against every fixture vector,
        // which this fixture treats as "genuinely no relevant evidence" --
        // exercising `none(...)`'s own distinct reason/meaning (design doc
        // §1.4), never folded into `err(...)`.
        if query_embedding.iter().all(|v| *v == 0.0) {
            return GeniaOutcome::OutcomeNone(OutcomeNonePayload {
                reason: "retrieve-no-results".to_string(),
                context: None,
            });
        }

        let mut scored: Vec<(f64, &str)> = FIXTURE
            .iter()
            .map(|(chunk, vector)| (dot(&query_embedding, vector), *chunk))
            .collect();
        // Stable sort: descending score, ties broken by fixture (insertion)
        // order -- deterministic ordered evidence, per R17/R18's order
        // discipline that the design doc's §1.6 ordered-Map adapter section
        // requires generally and this evidence list must not violate either.
        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());

        let limit = core::cmp::min(k as usize, scored.len());
        let evidence: Vec<Evidence> = scored[..limit]
            .iter()
            .map(|(score, chunk)| Evidence {
                chunk: chunk.to_string(),
                score: GeniaScore::ScoreFloat64(*score),
            })
            .collect();

        GeniaOutcome::OutcomeSome(OutcomeSomePayload {
            value: evidence,
            context: None,
        })
    }
}

export!(Component);

// Keep `vec!` reachable even if a future edit stops using it directly,
// avoiding an unused-import warning-as-error under this crate's `no_std`
// + `alloc` setup.
#[allow(dead_code)]
fn _unused() -> Vec<i32> {
    vec![]
}
