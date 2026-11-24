# R30 — Sheet Shaped Computation Contract

**Status: E30-0 candidate contract; D1–D7 direction approved by maintainer on 2026-11-24; exact text awaits independent review and acceptance. Not implemented.** GENIA_STATE.md remains the authority for implemented behavior.

Scope: [#1340](https://github.com/m0smith/genia-2026/issues/1340), [pre-flight](https://github.com/m0smith/genia-2026/issues/1340#issuecomment-7123534371), R29 accepted boundary, and the supported-host policy [#1341](https://github.com/m0smith/genia-2026/issues/1341). Baseline main: `3c5b7323f3e51c7411d1e75f2393feb45c92c6fe`. This document defines proposed observable behavior only, not implementation or executable tests.

## 1. Scope and invariants

R30 adds three ordinary fixed-arity callables: `column/2`, `with_column/3`, and `map2/3`. Columns are ordinary eager reusable Lists, not a new runtime value category. Existing `shape/1` suffices for Sheet shape observation; no new rank API. Sheets remain immutable, ordered, non-Seq, non-reactive values. No parser, Core IR, pipeline, numeric, equality, Outcome, or resource semantics change. Ordinary call, alias, module visibility and pipeline rules remain applicable; no special call syntax or new implicit conversion.

## 2. D1 — Extract a column

`column(name, sheet)` requires a Sheet and a legal column name under the existing Sheet/map-key identity contract. It returns a fresh reusable List of the exact stored cells in row order. No coercion, copying of cell payloads, unwrapping, callback, or mutation. An existing empty column yields an empty List. Missing names are misuse, not absence.

Proposed normalized TypeError diagnostics: non-Sheet: `column expected a Sheet`; missing name: `column could not find column`. Illegal names retain the existing Sheet name-validation errors. Missing-name diagnostics deliberately omit arbitrary user payloads.

## 3. D2 — Attach a computed column

`with_column(name, values, sheet)` accepts an explicit List, not a callable or Flow. It appends one new column after existing columns, retaining all existing names, cells, row count and order. It returns a new Sheet; no mutation, automatic replacement, padding, truncation, or recomputation. Names use existing legal-key equality; an equal existing name is rejected even if the supplied spelling or representation differs.

Validate in this order: Sheet input; legal name; duplicate name; List input; existing recursive authority-storage restriction; exact List length versus stored row count. Proposed TypeError diagnostics: `with_column expected a Sheet`; `with_column expected a new column name`; `with_column expected column values to be a List`; `declassification authority cannot be stored in a Sheet`; `with_column expected <expected> values; received <actual>` (decimal nonnegative counts only). Illegal names use existing Sheet name-validation errors. Reject before returning any result. New cells are retained exactly, subject to the existing protected-value and authority restrictions.

## 4. D3 — Pairwise List computation

`map2(f, xs, ys)` operates on two ordinary Lists, independent of Sheets. It returns a fresh List whose element at index i is the ordinary callback result for the exact pair of input elements at index i. Both Lists must have identical lengths; no shortest-input truncation, recycling, implicit Flow consumption, scalar lifting, or numeric coercion. Validate callable, first List, second List, then equal lengths before any callback. Proposed TypeError diagnostics: `map2 expected a function`; `map2 expected two Lists`; `map2 expected equal lengths; received <left> and <right>`. Empty equal Lists return an empty List without callbacks. Existing `zip` semantics remain unchanged.

## 5. D4 — Explicit lifting

No implicit broadcasting or fourth public callable is required. A caller can explicitly map a constant-producing function over an existing column, or over `rows(s)` when no column exists, to construct a same-length List. Alternatively a unary map can explicitly capture a scalar in its callback. Mapping over rows preserves the stored row count even for a zero-column Sheet. No requirement for a new repeat helper, scalar classification, rank inference or array operator overloading.

## 6. D5 — Empty shapes

A zero-row Sheet with a named column extracts an empty List. Attaching an empty List to a zero-row Sheet succeeds and preserves existing zero-row schema; nonempty input fails. For a zero-column Sheet with r retained rows, extraction of any name fails, and attaching a List of exactly r elements succeeds; no inference from the number of columns. A zero-row, zero-column Sheet accepts only an empty List. Existing `shape`, `select`, and `sheet_records` contracts remain unchanged.

## 7. D6 — Callback, value and failure boundaries

For map2, invoke f exactly once per pair, in ascending index order, using the existing raw ordinary-call semantics for collection callbacks so the arguments are exact values, including Outcome cells. Returned some/none/err values remain ordinary List elements; no automatic unwrap, discard, or propagation by map2. Runtime callback failures stop immediately, propagate through existing error rules, and return no partial List. Previously performed explicit callback effects are not rolled back. Do not require purity or add effect metadata. Sheet extraction and attachment have no callbacks. Preserve existing numeric operations and exact results, including rationals; map2 itself is not arithmetic.

Existing protected carriers remain opaque, never implicitly declassified, converted or rendered. Existing recursive protected and authority checks and sink restrictions apply; no new authority is conveyed by these operations. Normalized structural diagnostics must not reveal protected contents or arbitrary callback payloads. Sheet misuse diagnostics preserve their meaning through pipelines consistently with the existing Sheet boundary; callback errors retain existing governed error behavior. No new diagnostic framework.

## 8. D7 — Portable scope and supported-host delivery

All three operations are portable semantic contracts. Python delivery is Experimental in R30. C++ Sheet delivery remains scheduled for R31 under #1330, with owner genia-cpp host lane, exact affected cases, pinned/current-main evidence and removal when sheet_values is declared supported, applicable shared cases pass and parity is PARITY_OK. Sheet-specific cases use sheet_values; existing unrelated cases must not be hidden under this capability.

map2 is a general List helper, not Sheet-specific. Its standalone conformance must be independently accounted for and never require sheet_values. C++ map2 parity is scheduled under host-parity-inventory D-A for R33 (core stdlib), moving to R31 only if the R31 pre-flight demonstrates that map2 is an actual prerequisite of the sheet_values shared cases. Track it under #1018 as the inventory's umbrella for section B/C rows, unless the maintainer designates a dedicated issue, with separately identified map2 cases and evidence; do not report them as PASS on C++ before the host supports them. If an explicit temporary capability gap is required, it must be separately approved and tracked under the supported-host policy before merge; no invented capability flag or unsupported-as-pass classification. No permanent host-specific exception. Exact applicability mechanism and delivery evidence belong to later authorized phases; this contract does not change the registry.

## 9. Composition example (proposed, not runnable as current R30 behavior)

```genia
s = sheet([["qty", [2, 4]], ["price", [3, 1/2]]])
totals = map2((q, p) -> q * p, column("qty", s), column("price", s))
t = with_column("total", totals, s)
```

Expected totals: [6, 2]. The original Sheet is unchanged. A caller can use existing reduce and map to calculate each total's share of the sum, then attach the resulting List explicitly. No formula dependency graph or reactive updates.

## 10. Exclusions

No general array/rank system, broadcasting operators, reactive/formula graph, relational operations (R31), provider boundaries (R32), performance work (R34), implicit Sheet iteration, changes to existing zip, Model B expansion or general documentation cleanup. Existing R29 and R18 semantics remain intact.
