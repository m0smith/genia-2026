# Host Capability Registry Contract

**Status:** Partial — Python is the reference host. Future hosts are planned or scaffolded only. This registry documents capabilities that are implemented in the Python reference host. No other host is implemented in the current phase.

This document is the authoritative reference for host capability names, Genia surface, input/output shapes, normalized error behavior, and portability status for each host capability.

A host capability is a named, host-backed service exposed to Genia programs through the runtime substrate — not through language semantics or Core IR. Adding, removing, or renaming a capability requires updating this document, `HOST_CAPABILITY_MATRIX.md`, `GENIA_STATE.md`, and relevant tests.

---

## Portability Status Terms

| Term | Meaning |
|---|---|
| `language contract` | All hosts must implement this capability. It is part of the shared portable contract. |
| `Python-host-only` | Implemented in the Python reference host only. Not part of the shared portable contract. Future hosts may implement it. |
| `not implemented` | Not implemented in any host in the current phase. |

---

## Capability Groups

### Group: I/O Substrate

Capabilities connecting Genia programs to the host I/O streams. These are `language contract` capabilities — all hosts must provide them.

#### `io.stdout`

- **name:** `io.stdout`
- **genia_surface:** `stdout` (runtime value), `print(value)`, `write(stdout, value)`, `writeln(stdout, value)`, `flush(stdout)`
- **input:** any display-formattable Genia value
- **output:** `none("nil")` (side effect: text written to host stdout stream)
- **errors:**
  - `RuntimeError` — broken pipe in file/command/pipe execution mode; treated as normal downstream termination, not surfaced as a traceback
- **portability:** `language contract`
- **notes:** `stdout` is a first-class runtime capability value, not a string. `print(value)` writes display-formatted output plus a trailing newline. Flow-driven stdout writes use the same quiet broken-pipe path.

#### `io.stderr`

- **name:** `io.stderr`
- **genia_surface:** `stderr` (runtime value), `log(value)`, `write(stderr, value)`, `writeln(stderr, value)`, `flush(stderr)`
- **input:** any display-formattable Genia value
- **output:** `none("nil")` (side effect: text written to host stderr stream)
- **errors:**
  - none raised — broken pipe on stderr is absorbed best-effort without recursive noisy failures
- **portability:** `language contract`
- **notes:** `log(value)` writes display-formatted output plus a trailing newline to stderr. REPL diagnostics and command/file diagnostics go to stderr.

#### `io.stdin`

- **name:** `io.stdin`
- **genia_surface:** `stdin` (runtime value), used as a Flow source via `stdin |> lines`
- **input:** none (stdin is a source, not a sink)
- **output:** `Flow` — lazy, pull-based, single-use sequence of string lines when used via `stdin |> lines`
- **errors:**
  - `RuntimeError("Flow has already been consumed")` — on second consumption of the same stdin flow
- **portability:** `language contract`
- **notes:** Binding `stdin` into a flow must not force a full stdin read up front. `stdin()` (call form) returns a cached list of full stdin lines and is a separate compatibility surface. The primary source behavior is `stdin |> lines`.

---

### Group: Time / Sleep

#### `time.sleep`

- **name:** `time.sleep`
- **genia_surface:** `sleep(ms)`
- **input:** `ms` — Number (non-negative)
- **output:** `none("nil")` (side effect: host thread blocks for `ms` milliseconds)
- **errors:**
  - `TypeError` — when `ms` is not numeric
  - `ValueError` — when `ms < 0`
- **portability:** `Python-host-only`
- **notes:** Blocking primitive only. Does not introduce a scheduler, async/await surface, or event loop.

---

### Group: Randomness

Explicit seeded randomness is state-threaded and deterministic; the same seed yields the same sequence on the Python reference host. Convenience forms use the host RNG and are not deterministic.

#### `random.rng`

- **name:** `random.rng`
- **genia_surface:** `rng(seed)`
- **input:** `seed` — Number (non-negative integer)
- **output:** opaque RNG state value
- **errors:**
  - `TypeError` — when `seed` is not an integer
  - `ValueError` — when `seed < 0`
- **portability:** `Python-host-only`
- **notes:** The same seed must yield the same sequence. The Python reference host uses a fixed 32-bit LCG. The opaque RNG state value is not a plain Genia data type and must not be inspected directly.

#### `random.rand`

- **name:** `random.rand`
- **genia_surface:** `rand()`
- **input:** none
- **output:** Number (float in `[0, 1)`)
- **errors:** none defined
- **portability:** `Python-host-only`
- **notes:** Uses host RNG; sequence is not deterministic. Convenience form only.

#### `random.rand-int`

- **name:** `random.rand-int`
- **genia_surface:** `rand_int(n)`
- **input:** `n` — Number (positive integer)
- **output:** Number (integer in `[0, n)`)
- **errors:**
  - `TypeError` — when `n` is not an integer
  - `ValueError` — when `n <= 0`
- **portability:** `Python-host-only`
- **notes:** Uses host RNG; sequence is not deterministic. Convenience form only.

#### `random.rand-seeded`

- **name:** `random.rand-seeded`
- **genia_surface:** `rand(rng_state)`
- **input:** `rng_state` — opaque RNG state value (from `rng(seed)` or a prior `rand(rng_state)` call)
- **output:** List — `[next_rng_state, float]` where float is in `[0, 1)`
- **errors:**
  - `TypeError` — when `rng_state` is not a valid RNG state value
- **portability:** `Python-host-only`
- **notes:** Deterministic and state-threaded. The same state must always produce the same next state and the same float value.

#### `random.rand-int-seeded`

- **name:** `random.rand-int-seeded`
- **genia_surface:** `rand_int(rng_state, n)`
- **input:** `rng_state` — opaque RNG state value; `n` — Number (positive integer)
- **output:** List — `[next_rng_state, int]` where int is in `[0, n)`
- **errors:**
  - `TypeError` — when `rng_state` is not a valid RNG state value
  - `TypeError` — when `n` is not an integer
  - `ValueError` — when `n <= 0`
- **portability:** `Python-host-only`
- **notes:** Deterministic and state-threaded. Uses the same LCG sequence as `random.rand-seeded`.

---

### Group: HTTP Serving

#### `http.serve`

- **name:** `http.serve`
- **genia_surface:** `import web` then `web/serve_http(config, handler)`
- **input:** `config` — Map; `handler` — Function with shape `(request_map) -> response_map`
- **output:** none (blocking; does not return while server is running)
- **errors:**
  - invalid handler return value is normalized to a `500 internal server error` response (not a language-level error)
- **portability:** `Python-host-only`
- **notes:** Synchronous and blocking only. Request map fields: `method`, `path`, `query`, `headers`, `body`, `raw_body`, `client`. Response map fields: `status`, `headers`, `body`. Current limitations: exact-path routing only, no middleware, no path params, no streaming request/response bodies, no websockets, no async support. Higher-level routing helpers (`get`, `post`, `route_request`, `ok_text`, `json`) are prelude-backed wrappers.

---

### Group: Process / Mailbox

Host-backed concurrency substrate. Processes are fail-stop: handler exceptions cache an error string, exit the worker, and cause future `send` calls to raise.

#### `process.spawn`

- **name:** `process.spawn`
- **genia_surface:** `spawn(handler)`
- **input:** `handler` — Function (receives messages sent to the process)
- **output:** opaque Process handle value
- **errors:**
  - `TypeError` — when `handler` is not callable
- **portability:** `Python-host-only`
- **notes:** Creates a host-thread worker with a FIFO mailbox. One handler invocation runs at a time per process.

#### `process.send`

- **name:** `process.send`
- **genia_surface:** `send(process, message)`
- **input:** `process` — Process handle value; `message` — any Genia value
- **output:** `none("nil")` (side effect: message enqueued in process mailbox)
- **errors:**
  - `RuntimeError` — when the target process has already failed
- **portability:** `Python-host-only`
- **notes:** Mailbox is FIFO per process. Messages are delivered in the order sent.

#### `process.alive`

- **name:** `process.alive`
- **genia_surface:** `process_alive?(process)`
- **input:** `process` — Process handle value
- **output:** Boolean
- **errors:** none defined
- **portability:** `Python-host-only`

#### `process.failed`

- **name:** `process.failed`
- **genia_surface:** `process_failed?(process)`
- **input:** `process` — Process handle value
- **output:** Boolean
- **errors:** none defined
- **portability:** `Python-host-only`

#### `process.error`

- **name:** `process.error`
- **genia_surface:** `process_error(process)`
- **input:** `process` — Process handle value
- **output:** `some(error_string)` when the process has failed; `none("nil")` otherwise
- **errors:** none defined
- **portability:** `Python-host-only`

---

### Group: Refs / Cells

Host-backed synchronized state substrate.

#### `ref.create`

- **name:** `ref.create`
- **genia_surface:** `ref(initial_value)`
- **input:** `initial_value` — any Genia value
- **output:** opaque Ref value
- **errors:** none defined
- **portability:** `Python-host-only`
- **notes:** Refs are synchronized host objects. The opaque Ref value is not a plain Genia data type.

#### `ref.get`

- **name:** `ref.get`
- **genia_surface:** `ref_get(ref_value)`
- **input:** `ref_value` — Ref value
- **output:** the current stored Genia value
- **errors:**
  - `TypeError` — when the argument is not a Ref value
- **portability:** `Python-host-only`

#### `ref.set`

- **name:** `ref.set`
- **genia_surface:** `ref_set(ref_value, new_value)`
- **input:** `ref_value` — Ref value; `new_value` — any Genia value
- **output:** `none("nil")` (side effect: stored value updated)
- **errors:**
  - `TypeError` — when the first argument is not a Ref value
- **portability:** `Python-host-only`

#### `ref.update`

- **name:** `ref.update`
- **genia_surface:** `ref_update(ref_value, f)`
- **input:** `ref_value` — Ref value; `f` — Function with shape `(current_value) -> new_value`
- **output:** `none("nil")` (side effect: stored value replaced by `f(current_value)`)
- **errors:**
  - `TypeError` — when the first argument is not a Ref value
  - `TypeError` — when `f` is not callable
- **portability:** `Python-host-only`

#### `cell.create`

- **name:** `cell.create`
- **genia_surface:** `cell(initial_state)`, `cell_with_state(ref_value)`
- **input:** `initial_state` — any Genia value (for `cell`); `ref_value` — Ref value (for `cell_with_state`)
- **output:** opaque Cell value
- **errors:** none defined
- **portability:** `Python-host-only`
- **notes:** Cells queue asynchronous updates serialized one at a time. Cells are fail-stop: failed updates preserve the last successful state, cache an error string, and mark the cell failed.

#### `cell.send`

- **name:** `cell.send`
- **genia_surface:** `cell_send(cell, update_fn)`
- **input:** `cell` — Cell value; `update_fn` — Function with shape `(current_state) -> next_state`
- **output:** `none("nil")` (update is asynchronous; side effect: update enqueued)
- **errors:**
  - `RuntimeError` — when the cell has already failed
- **portability:** `Python-host-only`
- **notes:** Failed updates preserve the last successful state. Nested `cell_send` calls issued during an update are staged and committed only if that update succeeds.

#### `cell.get`

- **name:** `cell.get`
- **genia_surface:** `cell_get(cell)`, `cell_state(cell)`
- **input:** `cell` — Cell value
- **output:** the last successful state Genia value
- **errors:**
  - `RuntimeError` — when the cell has already failed
- **portability:** `Python-host-only`

#### `cell.restart`

- **name:** `cell.restart`
- **genia_surface:** `restart_cell(cell, new_state)`
- **input:** `cell` — Cell value; `new_state` — any Genia value
- **output:** `none("nil")` (side effect: failure cleared, state replaced, queued pre-restart updates discarded)
- **errors:** none defined
- **portability:** `Python-host-only`

---

### Group: Bytes / JSON / ZIP Bridge

Host-backed bridge for binary data, JSON serialization, and ZIP archive access.

#### `bytes.utf8-encode`

- **name:** `bytes.utf8-encode`
- **genia_surface:** `utf8_encode(string)`
- **input:** String
- **output:** opaque Bytes wrapper value
- **errors:**
  - `TypeError` — when the argument is not a String
- **portability:** `Python-host-only`
- **notes:** The opaque Bytes wrapper value is not a plain Genia data type (not a list or string).

#### `bytes.utf8-decode`

- **name:** `bytes.utf8-decode`
- **genia_surface:** `utf8_decode(bytes)`
- **input:** opaque Bytes wrapper value
- **output:** String
- **errors:**
  - `ValueError` — for invalid UTF-8 byte sequences
  - `TypeError` — when the argument is not a Bytes wrapper value
- **portability:** `Python-host-only`

#### `json.parse`

- **name:** `json.parse`
- **genia_surface:** `json_parse(string)`
- **input:** String
- **output:** parsed Genia value on success; `none("json-parse-error", context)` on failure (structured absence — not a raised exception)
- **errors:** none raised — parse failures return `none("json-parse-error", context)` as structured absence
- **portability:** `Python-host-only`
- **notes:** JSON objects become runtime Map values (same family as `map_new`/`map_put`). Failures are returned as structured absence, not exceptions.

#### `json.stringify`

- **name:** `json.stringify`
- **genia_surface:** `json_stringify(value)`, `json_pretty(value)` (compatibility alias)
- **input:** any Genia value representable as JSON (Number, String, Boolean, List, Map, `none("nil")`)
- **output:** String on success; `none("json-stringify-error", context)` on failure (structured absence — not a raised exception)
- **errors:** none raised — stringify failures return `none("json-stringify-error", context)` as structured absence
- **portability:** `Python-host-only`
- **notes:** Current output format uses 2-space indentation and sorted keys. `json_pretty` is a compatibility alias for `json_stringify`.

#### `zip.entries`

- **name:** `zip.entries`
- **genia_surface:** `zip_entries(path)`
- **input:** String (file path)
- **output:** List of opaque Zip entry wrapper values (in archive order; eager list, not a lazy Flow)
- **errors:**
  - `FileNotFoundError` — when `path` does not exist or is not accessible
- **portability:** `Python-host-only`
- **notes:** Each entry is an opaque Zip entry wrapper value. Entry accessors: `entry_name`, `entry_bytes`, `set_entry_bytes`, `update_entry_bytes`, `entry_json`. Returns an eager list in the current phase.

### Group: Callable Invocation

Capabilities for invoking Genia callables with explicit control over none-propagation behavior.

#### `fn.apply-raw`

- **name:** `fn.apply-raw`
- **genia_surface:** `apply_raw(f, args)`
- **input:** `f` — any Genia callable; `args` — a Genia list of positional argument values
- **output:** whatever `f` returns when called with the elements of `args`
- **errors:**
  - `TypeError` with message `"apply_raw expected a list as second argument, received <type>"` — when `args` is not a Python list (covers: string, int, bool, map, and any other non-list value)
  - dispatch error from `invoke_callable` — when `f` is not callable or arity does not match
  - any exception raised inside `f` body — propagates unchanged through `apply_raw`
- **portability:** `language contract`
- **notes:** Calls `f` with `args` elements as positional arguments while skipping the automatic `none(...)` short-circuit. `none(...)` values inside `args` are delivered to `f` unchanged — the function body executes. The return value of `f` is returned as-is without coercion or wrapping. `apply_raw` itself is subject to ordinary none-propagation: if `args` is `none(...)` the call short-circuits before `apply_raw` runs. This is the public equivalent of the internal `_invoke_raw_from_builtin` used by `reduce`, `map`, and `filter`.

#### `zip.write`

- **name:** `zip.write`
- **genia_surface:** `zip_write(entries, path)`, `zip_write(path, entries)` (pipeline-friendly form)
- **input:** List of opaque Zip entry wrapper values; String (output file path)
- **output:** String (the output path written)
- **errors:**
  - `TypeError` — when entries is not a list of Zip entry wrapper values
  - `RuntimeError` — on write failure (e.g., permission denied or disk error)
- **portability:** `Python-host-only`
- **notes:** Preserves entry order. Accepts both argument orderings for pipeline compatibility with `|>`.
