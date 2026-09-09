# C++ Host Porting Readiness (genia-2026)

Status: **Superseded — kept for historical drafting evidence only.** This
analysis motivated the R16 Multi-Host Conformance Infrastructure release
(epic #756), which resolved "the one real blocker" this doc identifies:
`tools/spec_runner --host` now speaks a generic versioned subprocess
protocol (E16-1 through E16-7, issues #758-#764; contract at
`docs/design/r16-multi-host-conformance-infrastructure-contract.md`), and
[`m0smith/genia-cpp`](https://github.com/m0smith/genia-cpp) is bootstrapped
as the external C++ host repository (E16-6, issue #763). The remaining
"Technical decisions C++ will force immediately" below (integer semantics,
ordered-map representation, Unicode/float formatting, memory/lifecycle
model, error-text portability) are **not yet resolved** — those are R17
through R20 (`docs/strategy/roadmap/r16-r20.md`), not R16. Do not treat any
claim below about the runner itself as current; the rest is preserved as
the original technical motivation, not deleted.

Original review date: 2026-08-28. This repo is already unusually well set up for a second host: a full porting framework exists (`AGENTS.md` truth hierarchy, `docs/host-interop/HOST_PORTING_GUIDE.md`, `docs/host-interop/capabilities.md`, `docs/architecture/core-ir-portability.md`, a 577-case `spec/` conformance suite, and a `hosts/cpp/` directory already scaffolded from `hosts/template/` with `README.md`/`AGENTS.md`, both marked "planned, no implementation yet"). Most of what's left isn't process — it's a handful of concrete technical decisions the docs currently leave to "whatever Python does," plus one real infrastructure gap.

## The one real blocker: no multi-host spec runner

`tools/spec_runner` only knows how to drive `hosts/python/adapter.py` directly, in-process. `GENIA_STATE.md` says so explicitly: "No generic multi-host runner exists; all conformance is validated against the Python reference host." Without a subprocess-based adapter protocol (spec case in, normalized result out — e.g. JSON over stdin/stdout or a small CLI contract), a C++ host has no way to prove conformance except one-off comparison scripts. Worth building once, generically (not as a C++-only shim), since Node/Java/Rust/Go hosts (also scaffolded as placeholders under `hosts/`) will need the same thing.

## Technical decisions C++ will force immediately

- **Integer semantics.** Genia integers are Python's arbitrary-precision ints. Nothing in `GENIA_RULES.md`/`GENIA_STATE.md` states general arithmetic overflow behavior outside the JSON boundary (which caps at `±9007199254740991`, but that's JSON-specific, not the general integer type). Before writing C++ arithmetic this needs an explicit contract: a bignum library (GMP, Boost.Multiprecision) to match Python exactly, or a documented fixed-width decision with defined overflow behavior. Otherwise large-integer programs will silently diverge between hosts.

- **Ordered-map representation.** Genia maps are insertion-ordered (`map_items`/`map_keys`/`map_values` guarantee it), matching Python's dict. `std::unordered_map` doesn't preserve order — needs an order-preserving structure (vector + index, or a library like `tsl::ordered_map`).

- **Unicode/string model.** `src/genia/utf8.py`'s codepoint iteration, byte-boundary checks, and slicing assume Python's code-point-indexed `str`. C++ has no equivalent built in — needs a UTF-8-aware string type (ICU, or a hand-rolled codepoint iterator) that reproduces the exact boundary/slice semantics, since spec cases assert exact `stdout`.

- **Float formatting.** Spec cases compare `stdout` byte-for-byte, and Python's float repr (shortest round-trip) differs from C++'s default formatting (`printf`/`iostream`). Needs an exact, documented formatting spec both hosts implement identically.

- **Memory/lifecycle model for refs, cells, and processes.** These currently ride on Python's refcounting+GC plus threading. C++ needs an explicit choice — `shared_ptr` (watch for cycles in closures/cells), an arena, or a tracing GC — and a concurrency primitive mapping (`std::thread`/mutex/condvar) that preserves the lifecycle semantics in `src/genia/lifecycle_scope.py`/`lifecycle_plan.py`. Also: Python's GIL serializes a lot of "concurrent" behavior that a true-parallel C++ implementation won't get for free, so races never exercised by the Python host could surface for the first time in C++.

- **Error message text as a portability surface.** `spec/error`/`spec/eval` assert exact `stderr` strings. Every error message Python currently hand-formats needs to be reproduced character-for-character in C++. Worth considering pulling those message templates into a shared, language-neutral data file both hosts read from, rather than hand-duplicating strings in two codebases that will drift over time.

- **Equivalent libraries for JSON/regex/etc.**, chosen to match the already-spec'd limits (duplicate-key rejection, 128-container nesting cap, safe-integer range, etc.) rather than just "a JSON library" — a generic JSON lib won't enforce Genia's specific boundary rules out of the box.

## Practical sequencing

Start with the capability-light spec categories — `parse`, `ir`, `eval` — before `cli`/`flow`, since those don't need I/O capabilities and will surface the numeric/string/map decisions fastest. Then fill in `hosts/cpp/README.md`, `hosts/cpp/AGENTS.md`, and a copied `hosts/template/CAPABILITY_STATUS.md` with real (not TODO) setup/build/test/lint commands as work progresses, per the existing template — and keep `docs/host-interop/HOST_CAPABILITY_MATRIX.md` truthful as each capability actually lands (`Not Implemented` → `Implemented`, never marked early).

## Reference: minimal host requirements (already documented, restated for convenience)

Per `docs/host-interop/HOST_PORTING_GUIDE.md`, a minimal conforming host needs: lexer/parser for current surface syntax, lowering into the shared Core IR meaning, Core IR evaluation with current runtime semantics, file mode CLI, `-c` command mode, raw `argv()` access, prelude autoload/loading, `help(name)` support, and a way to participate in the shared spec runner contract. Everything else (`-p`/pipe mode, REPL, Flow phase 1, HTTP serving, host interop bridge, refs, process primitives, bytes/json/zip bridge, debugger stdio) is optional and must be marked honestly in the capability matrix rather than silently emulated.
