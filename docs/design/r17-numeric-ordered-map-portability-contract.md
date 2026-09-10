# R17 Numeric and Ordered-Map Portability Contract

Status: **Approved contract; shared evidence and authoritative documentation
landed through E17-2.** This document is a design aid, not language truth on
its own. `GENIA_STATE.md` remains final authority for implemented behavior.

See also `docs/strategy/roadmap/r16-r20.md` ("Release R17") for roadmap
positioning, and the R16 precedent
(`docs/design/r16-multi-host-conformance-infrastructure-contract.md`)
for the shared-spec-evidence pattern this document follows.

Epic: [#776](https://github.com/m0smith/genia-2026/issues/776).

---

## Purpose

Give a non-Python host (the future R20 C++ host) a written, executable
contract for two currently under-specified value-domain behaviors, so it
can choose a conforming implementation without reading Python source or
another host's implementation:

1. Integer arithmetic range and overflow behavior.
2. Map order guarantees across construction, mutation, removal,
   reinsertion, and iteration/accessors — explicitly distinguished from
   map equality and from JSON object-member-name ordering.

---

## Contract

### Integer arithmetic

- Genia integers (excluding booleans, per the language's existing
  established convention) are **arbitrary-precision**. Ordinary
  arithmetic — `+`, `-`, `*`, `%`, unary negation — and relational
  comparison (`<`, `<=`, `>`, `>=`) over two integers produce the exact
  mathematical result at any magnitude. No operation in this set
  overflows, wraps, saturates, or silently truncates. The only bound is
  host memory, which is not a language-observable limit.
- This is independent of, and does not change, the existing R9 JSON
  safe-integer domain restriction (`[-9007199254740991,
  9007199254740991]`), which continues to apply only at the
  `json_encode`/`json_decode` boundary.
- A conforming host **must not** narrow Genia integers to a fixed-width
  machine type (e.g. 32-bit or 64-bit signed integer) as an
  implementation shortcut.
- `/` (division) is out of scope: it already always produces a float on
  the Python reference host regardless of integer operands, which is
  R18-adjacent numeric-formatting territory, not touched here.

Verified current Python reference-host behavior (`uv run genia`):
`99999999999999999999999999999999 * 99999999999999999999999999999999`
returns the exact 68-digit product. Zero Python-host runtime-code change
is required to satisfy this contract.

### Map order

- `map_new()` returns an empty map with no entries and no order.
- A map's order is the sequence in which its *currently present* keys
  were first associated with a value.
- `map_put(map, key, value)` on a key **not** currently present (per
  `map_has?`) inserts a new entry at the end of the current order.
- `map_put(map, key, value)` on a key that **is** currently present
  replaces only the value; the key's position in the order is unchanged
  — it does not move.
- `map_remove(map, key)` removes the entry (if present) with no effect
  on the relative order of the remaining entries. Removing an absent key
  returns an unchanged map (existing persistent no-op behavior).
- Reinsertion: once a key has been removed it is no longer "present"; a
  later `map_put` for that key is an ordinary new-key insertion under
  the rule above — appended at the map's current end, not restored to
  any earlier position.
- Map literal construction produces the same order as the equivalent
  left-to-right sequence of `map_put` calls, including the same
  last-value-wins/position-of-first-occurrence rule when a literal
  repeats a key.
- `map_items`, `map_keys`, `map_values` return entries/keys/values in
  exactly this order.

Verified current Python reference-host behavior (`uv run genia`):
building `{a:1, b:2, c:3}` then replacing `"a"`'s value leaves
`map_keys` as `[a, b, c]`; removing `"b"` then re-`map_put`-ing `"b"`
gives `[a, c, b]`. Zero Python-host runtime-code change is required.

### Order is distinct from equality and from JSON sorting

- Map order is unrelated to `json_encode`'s existing sorted-object-
  member-name output (`GENIA_STATE.md` §JSON: "sorted object member
  names"), which is unchanged by this contract.
- Map order is unrelated to `MapPattern` structural matching, which
  matches by content, not order (unchanged).
- Map order is unrelated to map `==` equality. **Open question, not
  resolved by this contract:** verified empirically that two maps built
  independently with identical key/value content currently compare
  `false` under `==` (e.g. `map_put(map_new(), "x", 1) ==
  map_put(map_new(), "x", 1)` is `false`, while `a == a` is `true`),
  because `GeniaMap` (`src/genia/values.py`) defines no `__eq__` and
  falls back to Python object identity. Whether identity-based map
  equality is intentional language design or a latent gap is a broader
  language-semantics question outside R17's scope and is left for a
  separate, future gate.

---

## Non-goals

- Changing the R9 JSON safe-integer limit.
- Selecting a specific C++ bignum/container library.
- Any C++ host implementation (R20).
- Float, Unicode-string, or diagnostic-message portability (R18).
- Open functions / extensible pattern dispatch (R19).
- Changing map `==` equality semantics (see open question above).
- Changing `MapPattern` structural matching semantics.
- Changing `/` or any float-producing numeric behavior.
- Any new syntax, builtin function, Core IR node, or parser change.

---

## Shared-spec evidence (E17-1, issue #778)

Three new `spec/eval/*.yaml` cases make the contract executable, running
through the existing host-neutral `category: eval` envelope and
discovered automatically by `tools/spec_runner`:

- `integer-arithmetic-large-magnitude-no-overflow.yaml` — large-magnitude
  multiplication returns the exact unbounded product.
- `map-put-replace-existing-key-preserves-order.yaml` — replacing an
  existing key's value leaves its position unchanged.
- `map-remove-then-reinsert-appends-at-end.yaml` — removing a key then
  re-inserting it appends it at the current end.

All three are happy-path proofs; no new failure mode exists to test
(the contract's "what does NOT happen" section states no magnitude ever
overflows and no covered map operation ever fails). No `requires:`
capability tag is used — ordinary arithmetic and map operations are
unconditionally required host surface (`docs/host-interop/capabilities.md`
does not list them as optional), so a future non-Python host that
narrows integers or reorders map keys differently must fail these cases
outright rather than report them unsupported.

---

## What remains open after this document

- **E17-2** ([#779](https://github.com/m0smith/genia-2026/issues/779)) landed
  this contract's wording into `GENIA_STATE.md` and reviewed the other primary
  documentation for contradictions without duplicating the authoritative prose.
- **E17-3** ([#780](https://github.com/m0smith/genia-2026/issues/780)):
  skeptical release-truth audit, `docs/releases/R17.md`, and roadmap
  status update.
- The map `==` identity-equality open question above, which needs its
  own separately gated decision before any change.

---

## Non-Negotiable Rule reminder

Per `AGENTS.md`: `GENIA_STATE.md` remains the final authority. E17-2 records
the already-tested R17 contract there without changing runtime behavior.
