# R19 Cross-Surface Host-Default Leak Audit (E19-4)

Status: **Audit complete.** This document records a deliberate sweep of
`src/genia/*.py` for host-specific wording, unreviewed UTF-8 decode
boundaries, and `format_debug`-bypassing renderers, beyond the two leaks
already fixed by E19-1 (`utf8_decode`'s raw `UnicodeDecodeError` text) and
E19-3 (`evaluator.py`'s pattern-match-miss `{args!r}`). It applies only the
already-approved U1/U2/U3 and diagnostic A/B/C rules — no new semantic rule
is invented here.

## 1. Method

- Grepped `src/genia/*.py` for `str(exc)`, `{exc}`/`{e}` interpolation,
  `type(exc).__name__`, and other exception-text interpolation into
  user-visible output (raised messages, emitted events, structured Outcome
  fields).
- Re-checked every UTF-8 decode boundary named in
  `docs/design/r19-portability-preflight.md` §6 as "likely later
  implementation surfaces" that E19-1 explicitly deferred:
  `src/genia/configuration.py`, `src/genia/evaluator.py` (subprocess stdout
  decode), `src/genia/gemini_rest.py`.
- Spot-checked whether any `format_debug`/`format_display` bypass (direct
  Python `repr`/`str` on a Genia runtime value) exists outside the one
  E19-3 already fixed.

## 2. Findings

### 2.1 `configuration.py`'s dotenv UTF-8 decode boundary — already compliant, no fix needed

`src/genia/configuration.py` (around line 318-321) decodes dotenv-source
bytes as UTF-8 and, on `UnicodeDecodeError`, returns a structured
`config-source-invalid` Outcome reason **without interpolating any part of
the exception** — the raw exception is discarded entirely, not even its
byte offset. This already fully satisfies U2 (no raw host decoder text
crosses the boundary) more strictly than `utf8_decode` did before E19-1.
**No action needed.**

### 2.2 `evaluator.py` subprocess stdout capture (`errors="replace"`) — reviewed, out of scope

`src/genia/evaluator.py:1155` decodes a spawned shell-pipeline subprocess's
stdout with `errors="replace"` (implicit U+FFFD replacement on malformed
bytes). This looks like a literal U2 violation ("no implicit U+FFFD
replacement... where an existing boundary claims to decode UTF-8"), but on
review it is **not the kind of boundary U2 targets**: U2 governs explicit
Genia-language bytes-to-string operations with a defined Outcome/diagnostic
shape (like `utf8_decode`, `json_decode`, the dotenv decode above) where a
caller can observe and handle malformed input as a first-class case.
Subprocess stdout capture is opaque external-process I/O integration — the
external process's output encoding is not controlled or declared by Genia,
and failing the entire shell-pipeline stage outright on any non-UTF-8 byte
from an arbitrary external command would be a substantial behavior/
robustness change unrelated to R19's approved scope (R19 does not add new
syntax or redesign the shell-pipeline feature). **Recorded as an explicit
follow-up candidate, not fixed here**: if a future release wants strict UTF-8
handling for shell-pipeline output, that is a deliberate design decision for
that feature's own gate, not an R19 mechanical fix.

### 2.3 `gemini_rest.py` — already compliant

`src/genia/gemini_rest.py:188` catches `(UnicodeDecodeError, json.JSONDecodeError, TypeError)` as part of a provider-response-parsing fallback and does not interpolate any exception text into portable output; it is entirely internal to model-provider response handling (R11/R12 territory), not a Genia-language string/diagnostic boundary. **No action needed.**

### 2.4 `host_bridge.py`'s Python-host-module exception wrapper — reviewed, explicitly out of scope by design

`src/genia/host_bridge.py:174` (`_wrap_python_host_callable`'s defensive
fallback, marked `# pragma: no cover`) does interpolate
`{type(exc).__name__}: {exc}` — a genuine Python exception class name and
message — into a `RuntimeError` raised from a called `python.*` host module
function. This is **not classified as an R19-in-scope leak**: the entire
`import python.*` host-module mechanism is an explicit, documented
host-interop escape hatch (distinct from the portable Genia language
surface), and its whole purpose is to let a Genia program call into
arbitrary Python code — a caller using it has already opted into
host-specific behavior. Treating its exception wording as portable Genia
diagnostic text would misrepresent what this surface is. **Recorded as a
follow-up candidate for whoever owns host-interop documentation** (confirm
`docs/host-interop/*` already says this boundary is host-specific by
design; if it doesn't say so explicitly, that's a docs gap, not a code
leak) rather than fixed here.

### 2.5 `builtins.py`'s `str(exc)` context-map fields (`read_file`, `write_file`, `zip_read`, `zip_write`, config-resource backends, `serve_http` handler errors) — reviewed, not an A/B-boundary leak

Roughly a dozen sites in `src/genia/builtins.py` put `str(exc)` into a
`"message"` or `"detail"` field of a structured Outcome/context `GeniaMap`
(e.g. `GeniaMap().put("source", "read_file").put("path", path).put("message",
str(exc))`). Checked against every `spec/error`/`spec/eval` case: **no
existing shared spec asserts the exact content of any of these
message/detail fields** — the portable, contract-relevant part of each
Outcome is its `source`/reason field (a fixed Genia-authored string like
`"read_file"`), and the `message`/`detail` field is explicitly incidental
host detail attached for human debugging, matching the contract's C
classification ("host-local/incidental diagnostic detail") which is
permitted to exist as long as it never becomes the asserted A/B-boundary
text. Since no shared spec pins this text, it has not (yet) become an
accidental A-class exact-text contract. **No action needed**, but flagged
for **E19-5/E19-6 documentation** to state explicitly (in `GENIA_STATE.md`
or the diagnostic-portability note) that these `message`/`detail` fields
are host-local debugging aids, not part of the portable diagnostic surface,
so a future contributor does not accidentally start asserting their exact
text in a new spec case.

### 2.6 `format_debug`/`format_display` bypass sweep

Grepped for direct `repr(`/`str(` calls on values passed through evaluator/
builtin diagnostic paths beyond the one E19-3 fixed
(`_format_args_for_diagnostic`). No further bypass found: `format_debug`'s
own fallback branch (`return repr(value)`) is intentional — it only fires
for host-internal wrapper types (e.g. `GeniaFlow`) that do not yet have a
dedicated Genia debug rendering, which is pre-existing behavior outside
E19-1/E19-3's approved scope to redesign.

## 3. Disposition summary

| Finding | Classification | Action |
|---|---|---|
| `configuration.py` dotenv UTF-8 decode | compliant | none |
| `evaluator.py` subprocess stdout `errors="replace"` | follow-up (design decision, not a mechanical R19 fix) | filed, not fixed |
| `gemini_rest.py` decode fallback | compliant | none |
| `host_bridge.py` python-host-module exception wrapper | follow-up (host-interop docs gap, not a code leak) | filed, not fixed |
| `builtins.py` `str(exc)` in `message`/`detail` context fields | compliant (class C, not asserted) | flagged for E19-5 documentation |
| `format_debug` fallback `repr()` for undocumented wrapper types | pre-existing, out of R19 scope | none |

No new runtime code change is made by E19-4. The two real leaks in the
codebase (E19-1's `utf8_decode`, E19-3's pattern-match-miss) were already
fixed in prior slices; this audit found no additional in-scope-fixable-now
leak that a small, minimal, already-approved-rule fix could close without
expanding R19's scope.
