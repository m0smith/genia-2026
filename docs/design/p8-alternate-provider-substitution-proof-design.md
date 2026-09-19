# P8 — Alternate Provider Realization Substitution: Design (Design Only)

Status: **Architecture/design proposal — non-authoritative, no implementation
authorized.** `GENIA_STATE.md` remains final authority for implemented
behavior. This document produces no runtime code, no new provider, no test,
and no Core IR/parser/AST change. It answers Provider Composition work-ledger
row **P8**: "What is the smallest proof of alternate provider realization with
unchanged application logic?"

Scope authority: [issue #943](https://github.com/m0smith/genia-2026/issues/943).
Prerequisite reading this document assumes and does not repeat:
`docs/analysis/provider-composition-stage0.md` (P3/P4 value-family matrix and
"Recommended first proof" section), `docs/analysis/provider-composition-preflight.md`
(P0/P1/P2/P5/P6/P7), `docs/releases/R12.md`, `docs/design/r12-retrieval-grounding-contract.md`,
and `src/genia/retrieval.py`.

This design changes no R12 contract semantics and weakens no R12 guarantee. A
later, separately gated implementation issue may only proceed after this
design is reviewed.

## 1. Interface selection

### 1.1 Candidates considered

R12 defines four provider-shaped capabilities in `src/genia/retrieval.py`:
`embed/4`, `index/4`, `retrieve/4`, `rerank/4`. Each currently has exactly one
realization: a deterministic Python-host fixture, injected explicitly through
`create_fixture_embed_provider`, `create_fixture_index_provider` +
`create_fixture_retrieve_provider` (paired), and `create_fixture_rerank_provider`.

| Candidate | Unrelated infrastructure needed | Compatibility-check surface | Numeric (P3/P4) exposure | Verdict |
| --- | --- | --- | --- | --- |
| `embed/4` | None extra; needs only a credential/authority/config. | Thin: `construct_embed` only does `isinstance(provider, GeniaEmbedProvider)` (source at `retrieval.py:423`). No paired compatibility-identity object exists for embed alone. | `_validate_embedding` (`retrieval.py:301`) restricts vector items to plain `int`/`float` only — it does **not** accept `GeniaDecimal`/`GeniaRational`. Exercises only Integer/Float64-shaped leaves, not the full four-kind numeric matrix. | Simplest data flow, but the *weakest* proof of E12-4-style compatibility checking — the one mechanism P8 most needs to exercise. |
| `index/4` | Needs an embedded corpus (so it depends on `embed/4`'s output shape) and produces an **opaque, non-inspectable handle** (`GeniaIndexHandle`, `retrieval.py:553`) that itself carries no further public observation to assert against in a proof — the handle cannot be compared, hashed, copied, or rendered beyond `<index-handle>`. A substitution proof over `index/4` alone has nothing further to observe except "did construction not raise," which is a weak proof surface. | Exact: mints one `object()` compatibility identity (`retrieval.py:602`) that must reappear unchanged on every handle it produces. | Corpus vectors go through the same `int`/`float`-only vector check as embed. | Requires standing up an embedded corpus as unrelated infrastructure merely to observe an opaque token; weakest observable-output surface. |
| `retrieve/4` | Needs one already-built `GeniaIndexProvider`+handle (reuses the existing fixture path for *that* half unmodified — retrieval does not need its own corpus-construction realization to vary) plus one query embedding. | Exact and richest: three independent guards in `GeniaRetriever.__call__` (`retrieval.py:865-886`) — private Python-identity compatibility match (`handle.__compatibility_identity is self._provider._compatibility_identity`), then exact `space` string equality, then exact `dims` integer equality, each producing a distinct normalized `err(...)` before any attempt. This is precisely R12's E12-4 mechanism the issue names. | `_is_finite_score` (`retrieval.py:29`) explicitly accepts `int`, `float`, `GeniaDecimal`, **and** `GeniaRational` as legal scores (all finite by construction per R22), alongside the query embedding's own finite-vector check. This is the **only** R12 boundary that exercises all four frozen P3/P4 numeric rows (Integer, Decimal, Rational, Float64) in one call, not just Integer/Float64. | **Selected** — see 1.2. |
| `rerank/4` | Needs a nonempty evidence list (so it also depends on chunk/evidence shapes) but has **no** paired compatibility-identity mechanism at all — `GeniaRerankProvider` (`retrieval.py:1181`) is validated only by `isinstance`. | None beyond `isinstance`. | Same finite-score numeric breadth as retrieve, but with no identity/compatibility mechanism to prove. | No compatibility surface to exercise; a substitution proof here would only show "same multiset in, reordered multiset out," missing the identity/revision half of P8's requirement entirely. |

### 1.2 Decision: `retrieve/4`

`retrieve/4` is the smallest interface that can genuinely demonstrate every
item the "Recommended first proof" section of `provider-composition-stage0.md`
requires in one call:

- **stable interface identity** — the Python nominal type `GeniaRetrieveProvider`
  plus its constructor-time pairing to one `GeniaIndexProvider`'s
  `_compatibility_identity`;
- **exact revision/compatibility** — the three ordered guards in
  `GeniaRetriever.__call__` (capability identity, then `space`, then `dims`),
  which is E12-4's actual compatibility mechanism, byte-for-byte;
- **explicit provider binding** — `construct_retrieve(provider, config,
  credential, authority)` (`retrieval.py:962`), an ordinary explicit call,
  never ambient;
- **two distinct realizations** — see §2;
- **identical portable observations where the contract requires them** —
  order, provenance, Outcome shape (§3);
- **no ambient provider discovery** — construction only ever captures
  already-built Python objects passed as ordinary arguments;
- **no provider-native value leakage** — `GeniaRetriever.__call__` normalizes
  every branch to `some/none/err` before returning (§7);
- **no change to R20 dispatch, R14 lifecycle, R18 equality, or Outcome
  semantics** — nothing in this design touches those modules.

It additionally exercises the *entire* frozen P3/P4 numeric matrix (all four
numeric kinds as scores) in one call, which is valuable evidence that the
numeric freeze genuinely composes with a real provider boundary rather than
only with the abstract matrix. `index/4` was rejected primarily because its
only observable output (the opaque handle) gives a substitution proof nothing
further to assert once compatibility identity is confirmed; `embed/4` and
`rerank/4` were rejected because neither exercises E12-4's actual paired
compatibility-identity mechanism, which is the specific thing P8 is meant to
prove generalizes. `retrieve/4` reuses the *existing* index/embed fixture path
unmodified for everything upstream of the call under test — it does not
require building two full corpora, only two `retrieve/4` handler realizations
behind one already-existing, unchanged index handle.

This choice is consistent with `provider-composition-stage0.md`'s own
"Recommended first proof" text, which names `retrieve/4`-shaped retrieval as
the model case, and with issue #943's own framing of `retrieve/4` as "a
strong candidate ... narrowest validation surface per R12's E12-4
compatibility checks" — confirmed here against the actual merged code rather
than assumed.

## 2. Realization A and Realization B

Both realizations are Python-host fixtures — R12 defines no non-Python host
today, so this proof stays within the Python reference host, per
`provider-composition-preflight.md` P7 scenario 12 ("Genia/Python/C++/WIT
implementation... each preserves the same interface/value/failure/authority/
resource contract"; only the Python case exists to test against here).

### 2.1 What is fixed across both realizations (the interface adapter)

The Python types `GeniaRetrieveProvider` and `GeniaRetriever`
(`retrieval.py:815`, `retrieval.py:848`) are the **interface**, not part of
either realization. They own: config/credential/authority capture, all input
validation, the three-guard compatibility check, R10 declassification timing,
the single-attempt call discipline, and Outcome normalization. Neither
realization may change, subclass, wrap, or bypass these types — doing so
would make this a "toy provider" invented from scratch, which the issue
explicitly forbids.

A realization is exactly one Python **handler** callable passed to
`create_fixture_retrieve_provider(index_provider, handler)`
(`retrieval.py:947`), with the exact signature
`handler(config: GeniaMap, backend_ref: Any, query: GeniaMap, k: int,
credential: str) -> GeniaOptionSome(_FixtureRetrieveResult(...)) |
GeniaOptionErr(...)`. This is already how R12 supports substitution today —
the opaque `GeniaRetrieveProvider` wrapper is identical Python code across
every existing test/example; only the injected handler closure varies
(compare `tests/unit/test_r12_retrieval_fixture.py`'s test-local handlers
against `hosts/python/exec_r12_grounded_fixture.py`'s handler — already two
independent handler bodies behind the same provider type, though neither was
built as a deliberate substitution proof). P8 formalizes and hardens that
existing pattern rather than inventing a new one.

### 2.2 Realization A — existing linear/order-preserving fixture

Path: the handler pattern already used by
`hosts/python/exec_r12_grounded_fixture.py:64-68` and by
`tests/unit/test_r12_retrieval_fixture.py`'s `_env` helper. `backend_ref` is
whatever the paired `GeniaIndexProvider`'s handler stored (a plain Python
list of the embedded corpus, or an equivalent container) — the handler over
this backend truncates to `k`, and returns a score for each surviving
`{chunk, score}` pair with **no computed relevance ranking**: order and score
are whatever the fixture author encoded (in the existing example, insertion
order with a constant `score: 1.0`). This is intentionally the "dumbest
correct" realization: it satisfies every contract obligation (order is
*a* best-first order, since R12 defines no required ranking function; scores
are finite; chunks trace exactly to indexed corpus entries) without
performing any vector math at all.

### 2.3 Realization B — independent cosine-similarity ranking fixture

Realization B must be a **genuinely distinct implementation path**, not a
relabeling of A's output. Its design:

- storage: the paired index handler for realization B stores the corpus in a
  different backend shape than realization A — for example a `dict` keyed by
  a synthetic integer id, rather than realization A's plain ordered `list` —
  so `backend_ref` is not structurally interchangeable between the two
  realizations (this is legal: `backend_ref` is private to the paired
  index/retrieve handler pair and is never observed by `GeniaRetriever` or by
  Genia source; only the paired handlers agree on its shape);
- ranking: realization B's retrieve handler computes an actual deterministic
  cosine similarity between the query vector and every stored vector using
  plain Python arithmetic (dot product over `zip`, magnitude via
  `math.sqrt(sum(x*x ...))`), sorts descending by that computed similarity
  with a stable, deterministic tie-break (original corpus insertion index),
  and returns the top `k` as `{chunk, score}` pairs where `score` is the
  computed cosine similarity itself — a real finite float, not a constant;
- this produces observably different `score` values and, for any corpus with
  more than one entry and a non-degenerate query, a potentially different
  output *order* than realization A, while remaining a valid best-first order
  under R12's own rule that "the list order, not score magnitude or
  direction, [is] the authoritative best-first retrieval order" — R12 defines
  no required ranking function or cross-realization score comparability
  (`docs/design/r12-retrieval-grounding-contract.md`, "Index handle and
  retrieved chunk" and "Replaceability" sections), so both A's fixed-order/
  fixed-score output and B's computed-order/computed-score output are
  independently contract-valid.

This is not a trivial wrapper: B does not call A, does not copy A's output,
and does not merely relabel a field. It is an independently written handler
implementing a different retrieval algorithm over a different backing data
structure, satisfying the same interface contract.

A future implementation issue could equally choose Euclidean-distance
ranking, or an alternate deterministic tie-break, as long as it remains
offline/deterministic per R12's "Deterministic test obligations" section;
this document fixes only the shape of the requirement (a distinct algorithm
and a distinct backend, both producing valid contract observations), not
literal source code.

## 3. What must be observably identical between A and B

Per the R12 contract and this design, the following must hold for both
realizations, for every legal input:

- **Outcome shape.** A valid nonempty result is `some([{chunk, score}, ...])`
  with each `chunk` exactly a valid R12 `chunk` value and each `score` a
  finite number (any of Integer/Decimal/Rational/Float64); a valid empty
  result is exactly `none("retrieval-no-results")`; every recoverable failure
  is exactly one of the `retrieve-*` reasons/contexts fixed by the contract's
  "Outcomes and errors" table. Neither realization may invent a new reason,
  omit a required context field, or return an Outcome shape the contract does
  not name.
- **Provenance exactness.** Every returned `chunk` must trace to an exact
  indexed corpus entry (`retrieval.py:927-936`'s `occurrence` lookup, which
  both realizations pass through unchanged — this logic lives in the fixed
  interface, not in either handler). Neither realization's handler may
  fabricate, mutate, or duplicate a chunk beyond what the shared interface
  code already permits/rejects.
- **Cardinality bound.** At most `k` results; `len(results) > k` is
  `retrieve-response-invalid` for both, enforced by the shared interface
  (`retrieval.py:913`), not by either handler.
- **Compatibility-check outcomes.** For a given `(index_provider,
  retrieve_provider, handle, query)` combination, whether the call proceeds
  past each of the three compatibility guards is fully determined by the
  fixed interface and the paired provider's compatibility identity/space/
  dims — **not** by which handler (A or B) is installed. Swapping A for B
  behind an already-validated pairing must not change whether a given
  input passes or fails compatibility; it may only change the *content* of a
  successful result.
- **Determinism for identical input.** Per the contract's "Deterministic test
  obligations" section, each realization must itself be deterministic (same
  input maps to the same output within one realization); this design does
  not require A and B to produce the *same* output as each other for the
  same input — see §4.
- **Single-attempt/no-retry discipline, R10 declassification timing, and
  authority/credential handling** — all owned by the shared
  `GeniaRetriever`/`declassify` call sequence (`retrieval.py:887-897`),
  identical regardless of handler.
- **Application call sites.** The Genia-source call shape
  `r = retrieve(provider, config, credential, authority); r(handle, query, k)`
  is byte-for-byte identical for A and B. Nothing in application source
  names, branches on, or inspects which realization is bound.

## 4. What may legitimately differ

- The concrete numeric `score` values returned (R12: "different... retrievers
  ... [need not] return identical vectors, scores, order, evidence, or
  answers" — Replaceability paragraph).
- The concrete output *order* among results that are equally valid
  "best-first" orders (R12 defines no canonical ranking function).
- The internal `backend_ref` Python shape/type (list vs dict vs anything
  else) — this is private to the matched handler pair and never crosses into
  a Genia value.
- Internal algorithm, data structures, and Python-level implementation detail
  of the handler function itself (this is precisely the point of the proof).
- Attempt latency/implementation complexity (not observed by the contract at
  all; R12 fixtures are synchronous and offline for both).

## 5. Interface identity / revision mechanism (traced from E12-4)

R12's compatibility mechanism, as implemented, is **not** a public interface-
identity token at the Genia source level — R12 predates the general P5
"exact nominal identity + exact opaque revision" model from
`provider-composition-preflight.md` and implements a narrower, domain-scoped
instance of the same idea entirely in the Python host:

1. **Minting.** `GeniaIndexProvider.__init__` (`retrieval.py:599-602`) mints
   one Python `object()` as `self._compatibility_identity` at construction
   time. This object has no structure; its only useful property is identity
   (`is`).
2. **Propagation to a handle.** Each successful index call embeds that exact
   object, plus the corpus's exact `space` string and `dims` integer, into
   the resulting `GeniaIndexHandle` (`retrieval.py:668-676`). The handle
   never exposes these fields to Genia source (name-mangled attributes,
   `__eq__`/`__hash__`/`__copy__` all raise).
3. **Pairing to a retrieve provider.** `create_fixture_retrieve_provider(
   index_provider, handler)` (`retrieval.py:947-955`) is the **only** way to
   construct a `GeniaRetrieveProvider`, and it always copies the exact same
   `index_provider._compatibility_identity` object into the new retrieve
   provider. There is no public constructor that lets a retrieve provider
   claim compatibility with an index provider it was not built from.
4. **Checking at call time.** `GeniaRetriever.__call__` compares
   `handle.__compatibility_identity is self._provider._compatibility_identity`
   (`retrieval.py:871-874`) — pure Python object identity, no structural or
   name-based matching, exactly matching P5's "no coercion/range" and PAI-5
   "exact semantic identity, never name-only duck typing." Space and
   dimension equality are checked as two further exact, independent string/
   integer comparisons immediately after.

For this proof, **realization identity is orthogonal to compatibility
identity.** The compatibility identity is a property of the
*(index_provider, retrieve_provider)* pairing at construction time, not of
which handler is installed in either provider. Realization A and realization
B both remain compatible with the *same already-built* index handle as long
as they are each paired, via `create_fixture_retrieve_provider`, with an
index provider sharing that handle's compatibility identity, exact `space`,
and exact `dims`. Concretely, the proof holds the index/embed side of the
pipeline fixed (produces one `GeniaIndexHandle` once) and swaps only which
retrieve-side handler is bound to a *newly paired* `GeniaRetrieveProvider`
sharing that same index provider's identity — this is precisely "alternate
provider realization with unchanged application logic," because the
application's `retrieve(...)` call site, its `handle`, and its `query` are
identical in both runs; only the explicit construction-time binding differs.

No R12 change is proposed to generalize this into the P5
name-plus-opaque-revision token model; that generalization, if ever pursued,
is separate, later, P8/P9-adjacent architecture work, not part of this proof.

## 6. Binding mechanism (traced, not invented)

Application (Genia source) code never selects a realization implicitly. The
existing, unchanged binding sequence is:

```text
provider = <host-constructed GeniaRetrieveProvider, already paired with one
            index provider's compatibility identity>
r = retrieve(provider, config, credential, authority)   -- construct_retrieve
some_result = r(handle, query_embedding, k)              -- GeniaRetriever.__call__
```

- `provider` is supplied as an ordinary ***explicit argument*** to `retrieve/4`
  — never looked up by name, imported ambiently, or resolved from a registry.
  This matches PAI-1/PAI-11 and P7's "explicit immutable binding" model at
  the smallest possible scale (one explicit value, not a whole-computation
  plan — P7's larger binding-plan machinery is out of scope for P8).
- Selecting realization A vs. B happens **only** at the point the *host*
  constructs the `GeniaRetrieveProvider` — i.e., which Python handler was
  passed to `create_fixture_retrieve_provider`. This call is host/test
  bootstrap code (see `provider-composition-preflight.md` P0's "Provider
  binding as attachment, not acquisition" and PAI-2 "inert
  construction/binding"), not Genia source, and not reachable from a running
  Genia program. This mirrors how `create_fixture_embed_provider`/
  `create_fixture_index_provider`/`create_fixture_rerank_provider` already
  work: the *only* place a realization choice is made is the one Python call
  that builds the provider object, before any Genia evaluation begins.
- Once a `GeniaRetrieveProvider` value exists, it is opaque: Genia source can
  pass it to `retrieve/4`, but cannot inspect, compare for realization
  identity, branch on, or otherwise observe which handler backs it.
- No R10 authority or credential selects a realization; those remain
  separate concerns (§7) that apply identically regardless of which
  realization is bound.
- No R20 open-function dispatch participates anywhere in this path — there is
  no open function or multi-clause dispatch on the provider at all; the
  provider is a plain explicit positional value passed once to
  `construct_retrieve` and once, indirectly, into one handler call. This
  satisfies PAI-13 and the preflight's explicit "R20 disambiguation" trap
  the issue calls out by name: nothing here chooses a realization by
  argument shape/pattern/guard at call time; the realization choice is fixed
  entirely at host-side construction, before any call happens.

## 7. Authority/config/credentials remain separate from the interface (R10 tie)

Nothing about this proof changes R10 composition. `construct_retrieve`
(`retrieval.py:962-978`) still separately validates: an opaque provider
capability (`isinstance(provider, GeniaRetrieveProvider)`), a closed ordinary
`config` map, one `GeniaProtected` `credential`, and one
`GeniaDeclassificationAuthority` scoped to `quote(retrieve_call)`. These four
inputs are independently supplied and independently validated — a valid
credential/authority pair does not imply a compatible provider, and a
compatible provider does not imply a valid credential/authority pair. Per
PAI-7, "capability, credential, and authority are distinct. Binding grants no
authority." This proof does not touch `configuration.py`'s
`declassify`/`GeniaDeclassificationAuthority` machinery at all — both
realizations are called via the exact same
`declassify(self._authority, self._credential)` call
(`retrieval.py:887`) immediately before the one attempt, regardless of which
handler executes next. Swapping the handler cannot change when or whether
declassification occurs, because that code lives in `GeniaRetriever`, not in
either realization.

## 8. How P3/P4 provider-boundary values cross for `retrieve/4`

Tracing every value that crosses the `retrieve/4` boundary against the frozen
`docs/analysis/provider-composition-stage0.md` value-family matrix:

| Value | Direction | P3/P4 row | Admissibility |
| --- | --- | --- | --- |
| `config` (`{id: String, timeout_ms: Integer}`) | in (construction) | String (**Portable**), Integer (**Portable**) | Clean; both portable per their rows. |
| `credential` | in (construction) | R10 protected carrier (**Conditional, fail closed**) | Clean; the carrier's opaque identity is preserved and only declassified just-in-time at an authorized sink per R10 — never an ordinary boundary payload. |
| `authority` | in (construction) | Not a P3/P4 row at all — Authorities are **Local-only / non-transferable** identity-bearing host capabilities, never boundary data. | Clean; it is a Python-host object passed by reference, never serialized or inspected by a handler. |
| `handle` (`GeniaIndexHandle`) | in (call) | "Retrieval/index and other host handles" (**Local-only / non-transferable**) | Clean; the handle itself never crosses into the handler's return value or into any Outcome — only its already-extracted `backend_ref`, `space`, and `dims` are used internally by the fixed interface code, and `backend_ref` is a private Python-host value the handler alone interprets, never observed as a Genia value. |
| `query` (`{text: String, embedding: {vector: [Number], dims: Integer, space: String}}`) | in (call) | Map (**Conditional**) containing String (**Portable**), List of Float64/Integer (**Conditional**, admissible per those rows so long as every item is finite — enforced by `_validate_query_embedding`), Integer (**Portable**), String (**Portable**) | Clean; every leaf independently satisfies its row; the recursive admissibility rule (P3 "Recursive admissibility rule") holds because every field passes its own row's condition. |
| `k` | in (call) | Integer (**Portable**) | Clean; bounded `1..1000`, never a Bool. |
| returned `chunk` (`{text: String, source: {...}, meta: R9 json-represented}`) | out | String (**Portable**); Map (**Conditional**); R9 represented value (**Conditional**) | Clean; `chunk.meta` is exactly the R9 `json`-represented value copied unchanged from the original document at `chunk/2` time — recursion into the represented value's carried JSON map/leaves is itself Portable per the JSON-domain rows. |
| returned `score` | out | **Integer / Decimal / Rational / Float64** rows (all four now **Portable/Conditional** per the frozen numeric matrix) | This is the one field in R12 that can legitimately be any of the four numeric kinds (`_is_finite_score` explicitly accepts `int`, `float`, `GeniaDecimal`, `GeniaRational`). Each crosses admissibly under its own row: Integer's exact value, Float64's exact bit pattern (including sign of zero; NaN is excluded here because `_is_finite_score` requires finiteness, and Float64 NaN is never "finite" under `math.isfinite`), Decimal's exact canonical `(coefficient, exponent)` pair, Rational's exact canonical `(numerator, denominator)` pair. None of R23's JSON-specific stability gates apply here — this is not a JSON boundary. |
| `some(...)` / `none("retrieval-no-results")` / `err(reason, context)` | out | Outcome / structural value rows (**Conditional**) | Clean; `reason` is always a fixed non-sensitive String literal from the contract's closed table, `context` is always a small closed Map of already-admissible leaves (`timeout_ms: Integer`, `retry_after_ms: Some(Integer)|None(...)`, `kind: Symbol`). |
| `_FixtureRetrieveResult` (private handler return wrapper) | internal only | Not a Genia value at all; a private Python host adapter type. | Never crosses into a Genia value — `GeniaRetriever.__call__` unwraps it (`retrieval.py:908`) and only its already-validated `.results` list, itself built entirely from the rows above, becomes the returned Outcome's payload. |

No cell here hits an unresolved P3/P4 gap. The one interesting composition —
a numeric leaf (`score`) genuinely varying across all four numeric kinds at
one boundary — is exactly the scenario the numeric admissibility summary in
`provider-composition-stage0.md` already covers ("Each numeric kind is an
ordinary structural leaf under the recursive admissibility rule").

## 9. How failures normalize

Both realizations share the exact same normalization code path in
`GeniaRetriever.__call__` (`retrieval.py:865-941`); a realization influences
*only* what its handler returns or raises, never how that return/exception is
turned into an Outcome:

- if the handler raises any Python exception, the interface catches it and
  returns exactly `err("retrieve-transport-failure", {kind: quote(other)})`
  — the raw exception type/message/traceback never crosses (`retrieval.py:
  898-901`);
- if the handler returns a `GeniaOptionErr` whose reason/context do not match
  one of the contract's fixed `retrieve-timeout` / `retrieve-rate-limited` /
  `retrieve-rejected` / `retrieve-transport-failure` shapes exactly, it is
  replaced with `retrieve-response-invalid` (`retrieval.py:902-905`) —
  a non-conforming realization cannot invent a new externally-visible reason;
- if the handler's success payload is malformed at any validated point
  (wrong wrapper type, non-list results, over-`k` results, a chunk that does
  not match `_valid_chunk`, a chunk that cannot be traced to the indexed
  corpus, a non-finite/incorrectly-typed score), the interface returns the
  matching `retrieve-response-invalid` variant with the exact `stage` named
  in the contract's context table — again entirely independent of which
  realization produced the malformed value;
- a genuinely empty valid result is `none("retrieval-no-results")`, never an
  error, for both realizations equally.

This means a later implementation issue can prove "normalized provider
failure" (one of the required negative scenarios, §10) using *either*
realization interchangeably, because the normalization logic being tested
lives entirely in the shared interface, not in the realization under test.

## 10. How compatibility is checked between realizations

"Compatibility" in R12's sense is a property of a *(index provider, retrieve
provider)* pairing, established once at `create_fixture_retrieve_provider`
time (§5) — it is unrelated to which handler either provider wraps.
Concretely, for this proof:

- realization A and realization B are each wrapped in their own
  `GeniaRetrieveProvider`, each paired via `create_fixture_retrieve_provider`
  to the *same* already-built `GeniaIndexProvider` (and therefore to the same
  compatibility identity, `space`, and `dims` as the one already-produced
  `GeniaIndexHandle`);
- both therefore pass all three compatibility guards against that one
  handle, because compatibility was established at pairing time, not at
  handler-invocation time;
- a genuinely **incompatible** provider (the negative scenario) is a
  `GeniaRetrieveProvider` paired to a *different* `GeniaIndexProvider`
  (different `object()` identity) — regardless of which handler (A's, B's,
  or a third) it wraps, it must fail the identity guard before either
  realization's handler is ever invoked;
- this cleanly separates "does realization B behave like a valid `retrieve/4`
  realization" (§3-§4, a per-realization property) from "is this specific
  provider instance compatible with this specific handle" (§5, a per-pairing
  property that never depends on the handler).

## 11. How no provider-specific value leaks

- **No host object identity leaks.** `GeniaIndexHandle`'s name-mangled
  fields, `_compatibility_identity` object, and `backend_ref` are never
  returned to Genia source, never included in an Outcome, and never
  observable via `display`/`debug_repr` beyond the fixed `<index-handle>`
  string (`retrieval.py:590-591`). Neither realization's handler receives or
  returns anything but `backend_ref` (opaque to Genia) and ordinary Genia
  values (`GeniaMap`/lists/strings/numbers/`_FixtureRetrieveResult`).
- **No realization-specific implementation detail is visible.** Application
  source cannot ask "which retrieve realization is this?" — there is no
  public predicate, field, or representation that exposes it. The only
  observable difference between A and B is the *content* of successful
  results (order/score), which the contract explicitly permits to vary
  (§4).
- **No R20 leakage.** Confirmed in §6: no open-function/multi-clause
  dispatch is involved in selecting or invoking either realization.
- **No cross-realization state leakage.** Each `GeniaRetrieveProvider`
  instance owns its own `_attempt_count` (`retrieval.py:818-831`); nothing
  is shared between A's and B's provider instances beyond the (intentionally
  shared) compatibility identity object from the common index provider.

## 12. Required negative-test scenarios this design supports

Each scenario below is producible using only the mechanisms traced above,
with no new mechanism invented:

| Scenario | How the design supports proving it |
| --- | --- |
| Wrong interface revision | R12 as implemented has no separate "revision" token beyond the compatibility identity itself (§5) — the nearest concrete case is binding a `GeniaRetrieveProvider` paired (via `create_fixture_retrieve_provider`) to a *different* `GeniaIndexProvider` than the one that produced the handle under test. This must fail `retrieve-capability-incompatible` before either realization's handler runs, for both A and B. |
| Incompatible provider | Same construction as above with mismatched `space` or `dims` instead of mismatched identity: pair a provider whose paired index config used a different `space` string (or corpus `dims`) than the handle under test, expecting `retrieve-embedding-incompatible` with `kind: quote(space)` or `quote(dimension)` respectively, for both A and B. |
| Ambiguous binding | R12 constructs exactly one `retrieve` callable per explicit `construct_retrieve` call; there is no registry or lookup to be ambiguous. The provable form here is at the *host bootstrap* level (outside Genia source): asserting that nothing in `retrieval.py` offers an implicit "current provider" or default-selection path — i.e., proving absence of ambiguity by exhaustively confirming every construction path requires an explicit `provider` argument, for both realizations equally. |
| Missing provider | Calling `retrieve(missing_or_wrong_type, config, credential, authority)` with a non-`GeniaRetrieveProvider` value (including `None`/nil) must raise the existing `TypeError` in `construct_retrieve` (`retrieval.py:968-971`) before any handler — provable identically regardless of which realization the *valid* comparison case uses. |
| Provider-native object leakage | Assert, for both A and B, that no `backend_ref`-shaped Python object, `_compatibility_identity` object, or raw handler-internal state ever appears in a returned Outcome, in `display`/`debug_repr` output, or in a raised diagnostic — a recursive leak scan matching R12's existing sentinel-scanning test pattern (see `docs/releases/R12.md`'s E12-7 description and existing `tests/unit/test_r12_retrieval_fixture.py`-style scans), run once per realization. |
| Local-only value crossing | Assert that passing the raw `GeniaIndexHandle`, the raw compatibility-identity object, or any other Local-only/non-transferable P3/P4 family value (§8) as if it were an ordinary boundary payload (for example, attempting to embed a handle inside `query`'s map) is rejected as runtime misuse before any handler runs, for both realizations. |
| Malformed numeric boundary value | Using realization B's real-valued cosine scores as the interesting case (since A's fixed `1.0` never exercises this), assert that a handler returning a non-finite score (e.g., a handler deliberately modified for the negative-test fixture to return `float("nan")` or `float("inf")`) is rejected as `retrieve-response-invalid` with `stage: quote(score)`, tying directly to the frozen P3/P4 Float64 row's "never the implicit target of a cross-kind numeric coercion" / finiteness requirement. A parallel case with a `GeniaDecimal`/`GeniaRational` score proves the row is exercised for the exact-numeric family too, not only Float64. |
| Normalized provider failure | For both A and B, install a handler variant that raises a plain Python `Exception` (a stand-in for an arbitrary host/library failure) and assert the caller observes only `err("retrieve-transport-failure", {kind: quote(other)})` with no exception text, per §9 — this is provable identically for either realization because the normalization code is shared, which is itself part of what this design is proving (realization swap does not change the failure-normalization contract). |

## 13. Application-facing logic: unchanged, confirmed

The complete Genia-source call sequence for this proof is:

```text
r = retrieve(retrieve_provider_fixture, {id: "...", timeout_ms: 1000},
             retrieve_credential_fixture, retrieve_authority_fixture)
r(index_handle_fixture, query_embedding_fixture, k)
```

This source text is identical whether `retrieve_provider_fixture` was built
from realization A's handler or realization B's handler — the only
difference is which Python object was passed to
`create_fixture_retrieve_provider` during host-side test/bootstrap setup,
strictly before any Genia evaluation begins. No branch, guard, pattern match,
or conditional in application source inspects, compares, or depends on
provider identity anywhere in this design. If a later implementation ever
needed such a branch, that would indicate this design was wrong and must be
revised before implementation proceeds, per the issue's explicit instruction.

## 14. House rules confirmed

Restating each `stage0.md` house rule against this specific design:

1. **Providers are opaque capabilities, not class hierarchies.** Both
   realizations are plain handler closures behind the one unchanged
   `GeniaRetrieveProvider` class; no subclassing or class hierarchy is
   introduced.
2. **Explicit, not ambient.** §6: the provider is always an explicit
   positional argument; no lookup/registry/current-provider state anywhere.
3. **Construction/binding is inert.** `create_fixture_retrieve_provider` and
   `construct_retrieve` perform no attempt, no IO, no declassification;
   confirmed unchanged in both existing call sites this design reuses.
4. **Provider replacement requires semantic compatibility, not method-name
   matching.** §10: compatibility is the exact identity/space/dims triple,
   never inferred from handler shape or naming.
5. **Raw host errors never cross unnormalized.** §9.
6. **Missing declared capability fails closed.** The "Missing provider"
   negative scenario in §12; `construct_retrieve` raises before any handler
   involvement.
7. **R20 open-function dispatch is not used for provider/realization
   selection.** §6, final bullet: confirmed no open function or dispatch
   participates in choosing or invoking either realization anywhere in this
   design.

## 15. Explicit non-goals

- No implementation, no new Python module, no new test file, no
  `GENIA_STATE.md` change.
- No change to `retrieval.py`'s public contract, error vocabulary, or
  validation order.
- No general P5 "name + opaque revision" token model, no P1 manifest, no P7
  binding-plan machinery — this proof deliberately stays at the smallest
  explicit-argument scale P7 itself identifies as "already proven and best
  inside programs."
- No claim that `embed/4`, `index/4`, or `rerank/4` need a second
  realization; this design is scoped to `retrieve/4` only, per "smallest
  proof."
- No WIT interoperability claim (P9 remains separate, later work).

## 16. Open questions for the implementation phase

1. **Negative-fixture wiring for malformed scores.** Realization B's handler
   is deterministic and always finite by construction; proving the
   "malformed numeric boundary value" scenario (§12) needs one additional,
   deliberately-broken handler variant (not a third "realization" in the
   substitution sense, purely a negative-test fixture). The implementation
   phase should decide whether this lives beside realization B in the same
   test module or as a clearly-separate negative-fixture-only file, so it is
   never mistaken for a third legitimate realization.
2. **Where realization B's handler code should live.** Options include a new
   Python-host-only fixture module analogous to
   `hosts/python/exec_r12_grounded_fixture.py`, or inline construction inside
   a new `tests/unit/test_r12_retrieve_alternate_realization.py`-shaped test
   module. This design does not require a public `create_*` factory for
   realization B beyond the existing `create_fixture_retrieve_provider`;
   the implementation phase should confirm no new public factory is
   actually needed before adding one.
3. **Exact negative-scenario test IDs and file layout** are implementation-
   phase decisions per normal `test` → `implementation` phase discipline;
   this design fixes only that each scenario in §12 is provable with the
   traced mechanisms, not its file/test-name shape.
4. **Whether E12-4's private `_handle_is_compatible_for_test`/
   `_backend_ref_for_test` helpers** (`retrieval.py:612-623`, already marked
   `_for_test`) should be reused directly by the implementation phase's
   negative tests, or whether the negative tests should instead exercise
   only the public `retrieve/4` Outcome surface end-to-end. This design
   traces both helpers as existing evidence of the compatibility mechanism
   but does not mandate which the implementation phase calls directly.
