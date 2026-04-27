# Spec: Host Capability Registry Contract
# Issue #118 — Spec Phase

**Status:** Spec-only — no implementation, no design decisions.
**Branch:** docs/host-capability-registry-contract
**Authority:** GENIA_STATE.md is the final authority for all behavioral claims in this spec.

---

## 1. PURPOSE

This spec defines exactly what `docs/host-interop/capabilities.md` must contain.

A host capability is a named, host-backed service exposed to Genia programs through the runtime substrate — not through language semantics or Core IR.

This spec does not define:
- language behavior (that lives in GENIA_STATE.md and GENIA_RULES.md)
- Core IR nodes (that lives in docs/architecture/core-ir-portability.md)
- implementation strategy (that is a design-phase decision)
- whether a validation layer is added (that is a design-phase decision)

---

## 2. SCOPE (FROM PRE-FLIGHT)

### Included

- Define a minimal host capability registry contract in `docs/host-interop/capabilities.md`.
- Document each capability with: name, Genia surface, input shape, output shape, normalized error behavior, portability status.
- Cover the capability groups listed in §5.
- Update `docs/host-interop/HOST_CAPABILITY_MATRIX.md` to reference the new capability registry.
- Update `docs/host-interop/README.md` to point to the new document.
- Update `GENIA_STATE.md` §0 to record that a formal capability registry contract exists.

### Excluded

- Implementing new host capabilities.
- Adding Node.js, Java, Rust, Go, or C++ hosts.
- Redefining Genia language semantics.
- Changing Core IR.
- Building a generic multi-host capability conformance runner.
- Describing speculative or unimplemented capabilities as current.
- Deciding the validation layer design (that is the design phase).

---

## 3. CAPABILITY ENTRY REQUIREMENTS

Every entry in `capabilities.md` must declare exactly these fields:

| Field | Required | Description |
|---|---|---|
| `name` | YES | Canonical capability name. Dotted namespaced string. Stable. |
| `genia_surface` | YES | The Genia-visible name(s) through which this capability is accessed (function name, value name, or module path). |
| `input` | YES | Genia value types accepted at the host bridge boundary. Must use Genia type names only (not Python types). |
| `output` | YES | Genia value type returned by the host bridge. Must use Genia type names only. |
| `errors` | YES | Normalized error behaviors. Category (TypeError / ValueError / RuntimeError / FileNotFoundError), message prefix, and trigger condition. No Python exception names. |
| `portability` | YES | Exactly one of the status terms defined in §4. |
| `notes` | OPTIONAL | Short clarifying text. Must not contradict GENIA_STATE.md. |

A capability entry must not contain:
- Python implementation details (class names, module paths from `src/genia/`)
- Unimplemented behaviors described as current
- Language semantics that belong in GENIA_STATE.md

---

## 4. PORTABILITY VOCABULARY

`capabilities.md` must use exactly these portability status terms and no others:

| Term | Meaning |
|---|---|
| `language contract` | All hosts must implement this capability. It is part of the shared portable contract. |
| `Python-host-only` | Implemented only in the Python reference host. Not part of the shared portable contract. Future hosts may implement it. |
| `not implemented` | Not implemented in any host in the current phase. |

These terms must match the status column in `HOST_CAPABILITY_MATRIX.md`.

Prohibited phrasings: "will be implemented", "planned", "experimental" (without also giving portability status), "all hosts support" (unless `language contract` is accurate and verified against GENIA_STATE.md).

---

## 5. REQUIRED CAPABILITY GROUPS

`capabilities.md` must document every capability group and every individual capability listed below. All behavioral claims must be grounded in GENIA_STATE.md.

### 5.1 I/O Substrate

| Capability name | Portability |
|---|---|
| `io.stdout` | `language contract` |
| `io.stderr` | `language contract` |
| `io.stdin` | `language contract` |

### 5.2 Time / Sleep

| Capability name | Portability |
|---|---|
| `time.sleep` | `Python-host-only` |

### 5.3 Randomness

| Capability name | Portability |
|---|---|
| `random.rng` | `Python-host-only` |
| `random.rand` | `Python-host-only` |
| `random.rand-int` | `Python-host-only` |
| `random.rand-seeded` | `Python-host-only` |
| `random.rand-int-seeded` | `Python-host-only` |

### 5.4 HTTP Serving

| Capability name | Portability |
|---|---|
| `http.serve` | `Python-host-only` |

### 5.5 Process / Mailbox

| Capability name | Portability |
|---|---|
| `process.spawn` | `Python-host-only` |
| `process.send` | `Python-host-only` |
| `process.alive` | `Python-host-only` |
| `process.failed` | `Python-host-only` |
| `process.error` | `Python-host-only` |

### 5.6 Refs / Cells

| Capability name | Portability |
|---|---|
| `ref.create` | `Python-host-only` |
| `ref.get` | `Python-host-only` |
| `ref.set` | `Python-host-only` |
| `ref.update` | `Python-host-only` |
| `cell.create` | `Python-host-only` |
| `cell.send` | `Python-host-only` |
| `cell.get` | `Python-host-only` |
| `cell.restart` | `Python-host-only` |

### 5.7 Bytes / JSON / ZIP Bridge

| Capability name | Portability |
|---|---|
| `bytes.utf8-encode` | `Python-host-only` |
| `bytes.utf8-decode` | `Python-host-only` |
| `json.parse` | `Python-host-only` |
| `json.stringify` | `Python-host-only` |
| `zip.entries` | `Python-host-only` |
| `zip.write` | `Python-host-only` |

---

## 6. CAPABILITY CONTRACTS (EXACT)

Each sub-section below defines the exact contract that `capabilities.md` must record for that capability. All inputs, outputs, and errors are stated in Genia types only.

### 6.1 `io.stdout`

- **genia_surface:** `stdout` (runtime value); `print(value)`, `write(stdout, value)`, `writeln(stdout, value)`, `flush(stdout)`
- **input:** any Genia display-formattable value
- **output:** `none("nil")` (side effect: text written to host stdout stream)
- **errors:**
  - `RuntimeError` on broken pipe in file/command/pipe execution mode; this is normal downstream termination and must not surface as a traceback
- **portability:** `language contract`
- **notes:** `stdout` is a first-class runtime capability value, not a string. `print(value)` is sugar for writing a display-formatted value plus newline to stdout.

### 6.2 `io.stderr`

- **genia_surface:** `stderr` (runtime value); `log(value)`, `write(stderr, value)`, `writeln(stderr, value)`, `flush(stderr)`
- **input:** any Genia display-formattable value
- **output:** `none("nil")` (side effect: text written to host stderr stream)
- **errors:**
  - broken pipe on stderr must be handled best-effort without recursive noisy failures
- **portability:** `language contract`
- **notes:** `log(value)` is sugar for writing a display-formatted value plus newline to stderr.

### 6.3 `io.stdin`

- **genia_surface:** `stdin` (runtime value); used as a Flow source via `stdin |> lines`
- **input:** none (stdin is a source, not a sink)
- **output:** `Flow` (lazy single-use pull sequence of string lines) when used via `stdin |> lines`
- **errors:**
  - invalid second consumption: `RuntimeError("Flow has already been consumed")`
- **portability:** `language contract`
- **notes:** Binding `stdin` into a flow must not force a full stdin read up front. `stdin()` (call form) returns a cached list of full stdin lines and is a separate compatibility surface; the primary source behavior is `stdin |> lines`.

### 6.4 `time.sleep`

- **genia_surface:** `sleep(ms)`
- **input:** `ms` — Number (non-negative)
- **output:** `none("nil")` (side effect: host thread blocks for `ms` milliseconds)
- **errors:**
  - `TypeError` when `ms` is not numeric
  - `ValueError` when `ms < 0`
- **portability:** `Python-host-only`
- **notes:** Blocking primitive only. Does not introduce a scheduler or async/await surface.

### 6.5 `random.rng`

- **genia_surface:** `rng(seed)`
- **input:** `seed` — Number (non-negative integer)
- **output:** opaque RNG state value
- **errors:**
  - `TypeError` when `seed` is not an integer
  - `ValueError` when `seed < 0`
- **portability:** `Python-host-only`
- **notes:** The same seed must yield the same sequence. The current Python host uses a fixed 32-bit LCG. The opaque RNG state value is not a plain Genia data type.

### 6.6 `random.rand`

- **genia_surface:** `rand()`
- **input:** none
- **output:** Number (float in `[0, 1)`)
- **errors:** none defined
- **portability:** `Python-host-only`
- **notes:** Uses host-RNG; not deterministic. Convenience form only.

### 6.7 `random.rand-int`

- **genia_surface:** `rand_int(n)`
- **input:** `n` — Number (positive integer)
- **output:** Number (integer in `[0, n)`)
- **errors:**
  - `TypeError` when `n` is not an integer
  - `ValueError` when `n <= 0`
- **portability:** `Python-host-only`
- **notes:** Uses host-RNG; not deterministic. Convenience form only.

### 6.8 `random.rand-seeded`

- **genia_surface:** `rand(rng_state)`
- **input:** `rng_state` — opaque RNG state value (from `rng(seed)` or prior `rand(rng_state)`)
- **output:** List — `[next_rng_state, float]` where float is in `[0, 1)`
- **errors:**
  - `TypeError` when `rng_state` is not a valid RNG state value
- **portability:** `Python-host-only`
- **notes:** Deterministic and state-threaded. The same state must produce the same next state and float.

### 6.9 `random.rand-int-seeded`

- **genia_surface:** `rand_int(rng_state, n)`
- **input:** `rng_state` — opaque RNG state value; `n` — Number (positive integer)
- **output:** List — `[next_rng_state, int]` where int is in `[0, n)`
- **errors:**
  - `TypeError` when `rng_state` is not a valid RNG state value
  - `TypeError` when `n` is not an integer
  - `ValueError` when `n <= 0`
- **portability:** `Python-host-only`
- **notes:** Deterministic and state-threaded.

### 6.10 `http.serve`

- **genia_surface:** `import web` then `web/serve_http(config, handler)`
- **input:** `config` — Map; `handler` — Function `(request_map) -> response_map`
- **output:** none (blocking; does not return while server is running)
- **errors:**
  - invalid handler return is normalized to a `500 internal server error` response (not a language-level error)
- **portability:** `Python-host-only`
- **notes:** Synchronous/blocking only. Request map fields: `method`, `path`, `query`, `headers`, `body`, `raw_body`, `client`. Response map fields: `status`, `headers`, `body`. No middleware, path params, streaming, websockets, or async support.

### 6.11 `process.spawn`

- **genia_surface:** `spawn(handler)`
- **input:** `handler` — Function (message handler, receives messages sent to the process)
- **output:** opaque Process handle value
- **errors:**
  - `TypeError` when `handler` is not callable
- **portability:** `Python-host-only`
- **notes:** Creates a host-thread worker with FIFO mailbox. Processes are fail-stop: handler exceptions cache an error string, exit the worker, and cause future `send` calls to raise.

### 6.12 `process.send`

- **genia_surface:** `send(process, message)`
- **input:** `process` — Process handle value; `message` — any Genia value
- **output:** `none("nil")` (side effect: message enqueued in process mailbox)
- **errors:**
  - `RuntimeError` when the process has already failed
- **portability:** `Python-host-only`
- **notes:** Mailbox is FIFO per process. One handler invocation at a time per process.

### 6.13 `process.alive`

- **genia_surface:** `process_alive?(process)`
- **input:** `process` — Process handle value
- **output:** Boolean
- **errors:** none defined
- **portability:** `Python-host-only`

### 6.14 `process.failed`

- **genia_surface:** `process_failed?(process)`
- **input:** `process` — Process handle value
- **output:** Boolean
- **errors:** none defined
- **portability:** `Python-host-only`

### 6.15 `process.error`

- **genia_surface:** `process_error(process)`
- **input:** `process` — Process handle value
- **output:** `some(error_string)` when process has failed; `none("nil")` otherwise
- **errors:** none defined
- **portability:** `Python-host-only`

### 6.16 `ref.create`

- **genia_surface:** `ref(initial_value)`
- **input:** `initial_value` — any Genia value
- **output:** opaque Ref value
- **errors:** none defined
- **portability:** `Python-host-only`
- **notes:** Refs are synchronized host objects.

### 6.17 `ref.get`

- **genia_surface:** `ref_get(ref_value)`
- **input:** `ref_value` — Ref value
- **output:** the current stored Genia value
- **errors:**
  - `TypeError` when argument is not a Ref value
- **portability:** `Python-host-only`

### 6.18 `ref.set`

- **genia_surface:** `ref_set(ref_value, new_value)`
- **input:** `ref_value` — Ref value; `new_value` — any Genia value
- **output:** `none("nil")` (side effect: stored value updated)
- **errors:**
  - `TypeError` when first argument is not a Ref value
- **portability:** `Python-host-only`

### 6.19 `ref.update`

- **genia_surface:** `ref_update(ref_value, f)`
- **input:** `ref_value` — Ref value; `f` — Function `(current_value) -> new_value`
- **output:** `none("nil")` (side effect: stored value replaced by `f(current_value)`)
- **errors:**
  - `TypeError` when first argument is not a Ref value
  - `TypeError` when `f` is not callable
- **portability:** `Python-host-only`

### 6.20 `cell.create`

- **genia_surface:** `cell(initial_state)` / `cell_with_state(ref_value)`
- **input:** `initial_state` — any Genia value (for `cell`); `ref_value` — Ref value (for `cell_with_state`)
- **output:** opaque Cell value
- **errors:** none defined
- **portability:** `Python-host-only`
- **notes:** Cells queue asynchronous updates serialized one at a time. Cells are fail-stop.

### 6.21 `cell.send`

- **genia_surface:** `cell_send(cell, update_fn)`
- **input:** `cell` — Cell value; `update_fn` — Function `(current_state) -> next_state`
- **output:** `none("nil")` (update is asynchronous; side effect: update enqueued)
- **errors:**
  - `RuntimeError` when the cell has already failed
- **portability:** `Python-host-only`
- **notes:** Failed updates preserve last successful state. Nested `cell_send` calls issued during an update are staged and committed only if that update succeeds.

### 6.22 `cell.get`

- **genia_surface:** `cell_get(cell)` / `cell_state(cell)`
- **input:** `cell` — Cell value
- **output:** the last successful state Genia value
- **errors:**
  - `RuntimeError` when the cell has already failed
- **portability:** `Python-host-only`

### 6.23 `cell.restart`

- **genia_surface:** `restart_cell(cell, new_state)`
- **input:** `cell` — Cell value; `new_state` — any Genia value
- **output:** `none("nil")` (side effect: failure cleared, state replaced, queued pre-restart updates discarded)
- **errors:** none defined
- **portability:** `Python-host-only`

### 6.24 `bytes.utf8-encode`

- **genia_surface:** `utf8_encode(string)`
- **input:** String
- **output:** opaque Bytes wrapper value
- **errors:**
  - `TypeError` when argument is not a String
- **portability:** `Python-host-only`

### 6.25 `bytes.utf8-decode`

- **genia_surface:** `utf8_decode(bytes)`
- **input:** opaque Bytes wrapper value
- **output:** String
- **errors:**
  - `ValueError` for invalid UTF-8 byte sequences
  - `TypeError` when argument is not a Bytes value
- **portability:** `Python-host-only`

### 6.26 `json.parse`

- **genia_surface:** `json_parse(string)`
- **input:** String
- **output:** parsed Genia value (`none("json-parse-error", context)` on failure — this is NOT an error raise; it is a structured absence return)
- **errors:** none raised — failures return structured `none("json-parse-error", context)`, not exceptions
- **portability:** `Python-host-only`
- **notes:** JSON objects become runtime Map values (the same family as `map_new`/`map_put`). Internal bridge primitive is `_json_parse`; public surface is the prelude-backed `json_parse`.

### 6.27 `json.stringify`

- **genia_surface:** `json_stringify(value)` / `json_pretty(value)`
- **input:** any Genia value that can be represented as JSON (Number, String, Boolean, List, Map, `none("nil")`)
- **output:** String (`none("json-stringify-error", context)` on failure — structured absence, not an exception)
- **errors:** none raised — failures return structured `none("json-stringify-error", context)`, not exceptions
- **portability:** `Python-host-only`
- **notes:** Current output format: `indent=2`, sorted keys. `json_pretty` is a compatibility alias for `json_stringify`. Internal bridge primitive is `_json_stringify`.

### 6.28 `zip.entries`

- **genia_surface:** `zip_entries(path)`
- **input:** String (file path)
- **output:** List of opaque Zip entry wrapper values (in archive order; eager, not lazy)
- **errors:**
  - `FileNotFoundError` when `path` does not exist or is not accessible
- **portability:** `Python-host-only`
- **notes:** Returns an eager list in this phase, not a lazy Flow. Each entry exposes `entry_name`, `entry_bytes`, `set_entry_bytes`, `update_entry_bytes`, `entry_json`.

### 6.29 `zip.write`

- **genia_surface:** `zip_write(entries, path)` / `zip_write(path, entries)`
- **input:** List of opaque Zip entry wrapper values; String (output file path)
- **output:** String (the output path)
- **errors:**
  - `TypeError` when entries is not a list of Zip entry values
  - `FileNotFoundError` / `RuntimeError` on write failure
- **portability:** `Python-host-only`
- **notes:** Preserves entry order. Accepts both argument orderings for pipeline compatibility.

---

## 7. INVARIANTS

These are truths that must hold in the completed `capabilities.md`. These drive doc-sync tests.

1. Every capability listed in §5 has an entry in `capabilities.md`.
2. Every entry has all required fields from §3 present and non-empty.
3. Every `portability` value is exactly one of the three terms defined in §4.
4. No entry contains Python class names, Python module paths from `src/genia/`, or Python-specific exception type names.
5. No entry describes unimplemented behavior as implemented.
6. No entry claims any non-Python host implements a capability (all non-Python hosts are `not implemented` in the current phase).
7. Every `portability: language contract` capability is listed as `Implemented` in `HOST_CAPABILITY_MATRIX.md`.
8. Every `portability: Python-host-only` capability is listed as `Python-host-only` in `HOST_CAPABILITY_MATRIX.md`.
9. The document does not use prohibited phrasings from §4.
10. The document does not contain the words "will", "planned", "future", or "coming soon" in capability contract descriptions.
11. Structured absence (`none(reason, ctx)`) is used for expected-absent results; it is not conflated with error raises.
12. The document does not define or redefine language semantics (those belong in GENIA_STATE.md).

---

## 8. RELATED FILE UPDATE REQUIREMENTS

### 8.1 `GENIA_STATE.md` §0

Must add a sentence confirming that a formal host capability registry contract document exists at `docs/host-interop/capabilities.md` and that it is the authoritative reference for capability names, input/output shapes, error behavior, and portability status.

### 8.2 `docs/host-interop/HOST_CAPABILITY_MATRIX.md`

Must add a reference to `capabilities.md` in the opening section. The matrix rows must remain consistent with the portability status in `capabilities.md` (no conflicts allowed).

### 8.3 `docs/host-interop/README.md`

Must add `capabilities.md` to the "Start here" list with a one-line description: the formal per-capability contract reference.

---

## 9. NON-GOALS

- This spec does NOT define a validation layer. Whether a JSON schema, Python dataclass, or runtime checker is added is a design-phase decision.
- This spec does NOT add new capabilities. Only currently implemented capabilities are documented.
- This spec does NOT change any Python host runtime behavior.
- This spec does NOT add shared spec YAML cases.
- This spec does NOT define how future hosts implement capabilities.
- This spec does NOT introduce a new Genia language surface.
- `docs/contract/semantic_facts.json` and `tests/test_semantic_doc_sync.py` may not need to change; that is a design-phase determination.

---

## 10. DOC REQUIREMENTS

- `capabilities.md` must include a maturity notice: "Host capability registry contract is **partial** — Python is the reference host. Future hosts are planned/scaffolded only."
- The doc must label each capability group with its portability zone.
- Examples within the doc must be classified as **Valid** (directly tested), **Likely valid**, or **Illustrative**, consistent with README.md example classification conventions.
- The doc must not contain speculative features.

---

## 11. COMPLEXITY CHECK

[x] Minimal — reveals existing substrate structure without adding complexity.

This spec organizes boundaries that already exist implicitly. The risk zone is any validation layer added in the design phase; keep it tiny or defer it.

---

## 12. FINAL CHECK

- [x] No implementation details included
- [x] No scope expansion beyond pre-flight
- [x] All behavioral claims grounded in GENIA_STATE.md
- [x] All capability contracts grounded in GENIA_RULES.md and GENIA_REPL_README.md
- [x] Portability status for each capability matches current HOST_CAPABILITY_MATRIX.md
- [x] No Python host runtime files are changed by this spec
- [x] No shared spec YAML cases are added or modified by this spec
- [x] Structured absence (`none(...)`) is correctly distinguished from error raises in contracts
