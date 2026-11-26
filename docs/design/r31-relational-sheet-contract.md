# R31 — Relational Sheet Operations Contract

**Status: candidate contract; maintainer decisions M1–M7 recorded 2026-11-26; exact text awaits independent review and acceptance. Not implemented.** GENIA_STATE.md remains the authority for implemented behavior.

Scope: [#1346](https://github.com/m0smith/genia-2026/issues/1346), the [formal pre-flight](https://github.com/m0smith/genia-2026/issues/1346#issuecomment-7178710654), the [decision record](https://github.com/m0smith/genia-2026/issues/1346#issuecomment-7182982272), the R30 accepted boundary, and the supported-host policy [#1341](https://github.com/m0smith/genia-2026/issues/1341). Baseline main: `b759c20f97334da14d1b15bdf8a70b87d6e0d2c8`. This document defines proposed observable behavior only, not design, implementation or executable tests. The public names below are candidates that this contract proposes; accepting the contract accepts them.

## 1. Scope and invariants

R31 adds two ordinary fixed-arity callables over existing Sheets: `sort_rows/2` (stable, comparator-driven row ordering) and `inner_join/4` (single-key inner join). Grouping, aggregation and summarization are deferred (non-goals). Sheets remain immutable, ordered, eager, non-Seq values. No parser, Core IR, pipeline, numeric, equality, Outcome or resource semantics change. Ordinary call, alias, module visibility and pipeline rules apply. The Sheet is the last argument of each callable, so `s |> sort_rows(before)` calls `sort_rows(before, s)` and `left |> inner_join(lk, rk, right)` calls `inner_join(lk, rk, right, left)`.

Both names join the existing fixed-arity runtime-public Sheet builtin groups: user functions at other arities remain allowed, while same-arity definitions and entry runtime-name reservation behave exactly as for `where/2` and `column/2` (compare `spec/error/r30-sheet-reserved.yaml`). A program that today defines `sort_rows/2` or `inner_join/4` therefore changes meaning; no such definition exists in either repository.

Invariants: inputs are never mutated; each success returns a fresh Sheet; every result cell is the exact stored value (no coercion, unwrapping, payload copying or representation-facet change); output row and column order are fully determined by this contract; a failure returns no partial Sheet.

## 2. `sort_rows(before, sheet)`

Returns a new Sheet with the same column names, order and row count as `sheet`, whose rows are the input rows rearranged. `before(a, b)` is called with two rows, each a fresh List of `[name, cell]` pairs in column order, exactly as `rows/1` yields them and as `where` and `derive` callbacks receive them. It must return exactly `true` or `false`; `true` means row `a` must come before row `b`.

If `before` is a strict weak ordering over the input rows (irreflexive, transitive, with transitive incomparability), the result is the unique arrangement in which row `a` precedes row `b` whenever `before(a, b)` is `true`, and rows where neither `before(a, b)` nor `before(b, a)` is `true` keep their input relative order (stable). For any other comparator the result is an unspecified permutation of the input rows: every input row appears exactly once, hosts need not agree, and conformance evidence uses only strict weak orderings.

The callback is invoked only with rows of the input Sheet, through the same raw ordinary-call mechanism as the `where` predicate, so Outcome cells inside a row are delivered unchanged. It is not invoked for a Sheet of fewer than two rows and is invoked at least once for two or more rows. The number and order of invocations are unspecified and must not be relied on. Callback failures propagate under existing rules with no partial Sheet; previously performed callback effects are not rolled back. No purity or effect metadata is required. If the comparator fails or returns a non-boolean for only some pairs, whether the call fails is unspecified, and a failure is the one raised by a failing invocation. A comparator that fails, or returns a non-boolean, on every invocation always fails for two or more rows. Conformance evidence uses only comparators that are total strict weak orderings or that fail on every invocation, and asserts no callback effect count or order.

## 3. `inner_join(left_key, right_key, right, left)`

`left_key` names a column of `left`; `right_key` names a column of `right`. Names follow the existing Sheet column-name identity (equal under portable value equality), so a String name and a Symbol name never match one another.

Output columns, in order: every column of `left` with its name and cells, then every column of `right` except the `right_key` column, with its name and cells. The key column keeps the left name and the left row's key cell exactly, even where the matching right key cell is spelled differently. The right key column is not in the output.

Output rows: for each `left` row in input order, one output row for each `right` row in input order whose key cell matches (section 4). Duplicate keys therefore give the product of the matches. Rows without a match on the other side are dropped; nothing is padded. If either input has zero rows, the result has zero rows and the full output columns. The result is never a zero-column Sheet.

Validation, in this order, before any matching: both `left` and `right` are Sheets; the left key name is a legal column name and then resolves in `left`; the right key name is a legal column name and then resolves in `right`; no output column name repeats (no `right` column other than the right key may equal, under column-name identity, any `left` column, including the left key); every left key cell, in row order, then every right key cell, in row order, passes the key checks of section 4. These checks run in full regardless of row counts, so results never depend on which side is empty. A Sheet with zero columns has no key column and fails name resolution. Consequently a self-join of a Sheet that has any non-key column fails the distinct-names check.

## 4. Keys

Each key cell is checked in the order of section 3. The existing recursive protected-value detection runs first: a cell that contains a protected carrier at any depth fails with the protected-key message of section 6. Otherwise the cell must be legal. A key cell is legal exactly when it would be a legal map key under the existing portable value equality and exact-numeric key rules in GENIA_STATE.md (R18 legal key families, read together with the exact Decimal, Rational and integral-value key buckets). Outcomes (including `nil`), Maps, NaN-containing values and identity-bearing values are not legal. An illegal key cell fails the whole join; it never silently fails to match. Two legal key cells match exactly when they are equal under `==`: `1`, `1.0` and `float64(1.0)` match one another; `1/2`, `0.5` and `float64(0.5)` match one another; `true` does not match `1`. (NaN-containing keys cannot be built from Genia source today, so that rule has no source-level evidence.) No ordering, hashing order or host container semantics define the relation. A multi-column match is expressed by deriving one List-valued key column with existing operations; no native multi-key form exists.

## 5. Calls, `none`, Outcomes and protected values

Neither callable is none-aware. Under ordinary outer-call propagation, if any argument is `none(...)` the call returns the first such argument unchanged, in argument order, before validation, with no callback and no output. `some(...)` and `err(...)` arguments are not propagated; they fail validation as non-Sheets, non-callables or illegal key names. Outcome cells in non-key columns are carried unchanged and never unwrapped; an Outcome key cell is illegal. A comparator result that is an Outcome is not a boolean and fails.

Protected carriers remain opaque. They may be carried in non-key cells and are delivered inside rows to the comparator without declassification; a protected key cell is rejected (section 6). Neither operation adds authority-related behavior: results contain only cells of already-valid input Sheets, no additional detection pass and no new failure mode is added, no stronger detection claim is made than the existing Sheet storage rules provide, and the open follow-up #1343 is unaffected.

## 6. Failure

The new structural failures in the table below are marked, normalized `TypeError`s that opt out of generic pipeline error wrapping, like existing Sheet errors. Row indexes are zero-based and `<side>` is `left` or `right`. These new diagnostics never include column names, key values, cell payloads, runtime type names or host class names. Illegal or protected key *names* retain the existing Sheet name-validation errors exactly as `column/2` raises them today; those inherited texts are outside the marking and no-host-class-name guarantees above, and shared conformance asserts only that they fail.

| Cause | Message |
|---|---|
| `sort_rows`: non-Sheet | `sort_rows expected a Sheet` |
| `sort_rows`: non-callable (checked after the Sheet) | `sort_rows expected a function` |
| `sort_rows`: non-boolean comparator result | `sort_rows expected comparator to return boolean` |
| `inner_join`: either input not a Sheet | `inner_join expected two Sheets` |
| `inner_join`: illegal or protected key name | existing Sheet column-name validation errors (inherited; see above) |
| `inner_join`: missing left or right key column | `inner_join could not find left key column` / `inner_join could not find right key column` |
| `inner_join`: repeated output column name | `inner_join expected distinct output column names` |
| `inner_join`: protected key cell (checked first) | `protected-value: inner-join key at <side> row <r>` |
| `inner_join`: illegal key cell | `inner_join expected a legal key at <side> row <r>` |

Arity and callable arity errors follow existing ordinary-call rules: arity is checked only at invocation, so a comparator is never checked for a Sheet of fewer than two rows.

## 7. Empty shapes

`sort_rows` on a zero-row Sheet with columns returns a fresh zero-row Sheet with the same columns and invokes nothing; a one-row Sheet returns an equal fresh Sheet with no invocation. A zero-column Sheet with `r` rows presents `r` empty rows (`[]`) to the comparator and returns `r` rows and zero columns. `inner_join` behavior for empty inputs is in section 3.

## 8. Portable scope and supported-host delivery

Both operations are portable semantic contracts. Python delivery is Experimental. Relational shared specs are gated by a separate optional capability, provisionally `sheet_relational` (also requiring `sheet_values`), and never by `sheet_values` alone, so the 46 existing `sheet_values` cases and #1330's removal condition are unchanged. Delivery on `m0smith/genia-cpp` follows the supported-host policy: a documented, issue-backed temporary gap entry (reason "Python-first delivery of R31 relational operations"; owner genia-cpp Sheet lane; tracking #1330/#1346; affected tests the relational specs; evidence pinned and current-main; removal when genia-cpp declares `sheet_relational` supported, applicable specs pass and parity is `PARITY_OK`), targeted for removal within R31, with no automatic later-release fallback, no permanent exception and no unsupported-as-pass. The capability name and manifest mechanism are finalized in the test phase.

The shared specs for both operations must include outer-call `none` propagation (section 5). C++ relational operations are not accepted until the separately tracked C++ ordinary-call `none` divergence ([#1347](https://github.com/m0smith/genia-2026/issues/1347)) is resolved with shared conformance evidence. This contract adds no prerequisite to #1330 beyond those already approved for the 46 cases.

## 9. Examples (proposed; not runnable as current behavior)

Expected results were reproduced at `b759c20f` with a throwaway user-land reference of the semantics above. They are illustrations, not conformance tests. Classification: proposed, portable behavior, Experimental on the Python reference host.

```genia
left  = collect_sheet([{region: "west", total: 8.3}, {region: "east", total: 10.0}, {region: "north", total: 4.0}])
right = collect_sheet([{region: "east", manager: "Okafor"}, {region: "west", manager: "Ng"}, {region: "east", manager: "Park"}])
joined = left |> inner_join("region", "region", right)
render_csv(joined)
```
`"region,total,manager\nwest,8.3,Ng\neast,10.0,Okafor\neast,10.0,Park\n"`: left order, then right order; `north` has no match and is dropped; Decimals are exact; `left` and `right` are unchanged.

```genia
by_total_desc = (a, b) -> row_get(a, "total") > row_get(b, "total")
render_csv(joined |> sort_rows(by_total_desc))
```
`"region,total,manager\neast,10.0,Okafor\neast,10.0,Park\nwest,8.3,Ng\n"`: the two tied rows keep their input order.

Key spelling and empty results:
```genia
a = collect_sheet([{id: 1, a: "x"}, {id: 2, a: "y"}])
b = collect_sheet([{id: 1.0, b: "p"}, {id: 2.0, b: "q"}])
render_csv(inner_join("id", "id", b, a))                              # "id,a,b\n1,x,p\n2,y,q\n"
shape(inner_join("id", "id", collect_sheet([{id: 9, b: "q"}]), a))    # [[rows, 0], [columns, 3]]
```
A column name repeated across the inputs, such as joining two Sheets that both have a non-key `v`, fails with `inner_join expected distinct output column names`.

## 10. Documentation notes

When implemented, GENIA_STATE.md describes both operations as **Experimental** on the Python reference host with the C++ gap stated truthfully, and replaces the "Joins/grouping/sorting remain absent" sentence with the exact remaining absences (grouping and aggregation). GENIA_RULES.md section 22, GENIA_REPL_README.md and README.md follow. The MCP language profile gains an anchor and idioms for ordering and joining with their evidence (prospective: only after implementation is verified). Every implementation prompt must require synchronization of the four root documents, generated documentation, the MCP profile and registry, and shared conformance evidence.

## 11. Exclusions

Grouping, aggregation, summarization helpers; left, right or outer joins; multi-key and key-function joins; rename or suffix on collision; key-based `order_by` and any new ordering relation; a new total order; changes to `<` or equality; implicit Sheet and Seq conversion; lazy or reactive Sheets; SQL or a query DSL; a new runtime value type; new syntax or Core IR; performance guarantees; any change to R18, R29 or R30 semantics, Model B, authority detection (#1343) or the C++ `none` defect (#1347).

## 12. Observations later phases must be able to make

This lists observable behavior only; it contains no tests. Shared evidence must be able to observe: tie stability; `1`/`1.0` matching with the left spelling kept; `true` not matching `1`; the product of duplicate keys; zero rows on either side keeping the full schema, including an illegal key on the non-empty side; the distinct-names failure, including a collision with the left key; each step of the validation order; first-`none` propagation in each argument position; a non-callable rejected on a zero-row Sheet and a wrong-arity comparator accepted on zero- and one-row Sheets; a zero-column sort; an always-non-boolean comparator; Outcome cells carried unchanged; protected-key versus illegal-key precedence; that the new errors are not wrapped by the pipeline; a reserved-name case like `r30-sheet-reserved`; and the `sheet_relational` gap entry.

## 13. Final check

Precise and testable; defines behavior only, with no tests and no implementation detail; adds nothing beyond maintainer decisions M1–M7; consistent with GENIA_STATE.md, whose existing Sheet, R18 equality, exact-numeric key and ordinary-call `none` rules it reuses without change.
