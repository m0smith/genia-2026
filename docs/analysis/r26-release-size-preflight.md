# R26 Release-Size Preflight — C++ REPL and Data Bridges

Status: **Planning/architecture record. Non-authoritative.** This document
changes no Genia language or runtime behavior and implements nothing.
`GENIA_STATE.md` remains final authority for implemented behavior. Roadmap
documents remain planning authority for sequencing; this document evaluates
them but does not replace or edit them.

Scope of this document: a skeptical preflight of the planned release
**R26 — C++ REPL and Data Bridges**. It asks whether R26 is one coherent,
correctly sized release or a thematic bundle that should be decomposed before
implementation begins. It is preflight/architecture work only. It includes no
R26 implementation, no `genia-cpp` changes, no capability additions or
renames, no roadmap edits or renumbering, and no implementation tickets.

Historical baseline: this preflight was originally performed against
`main` at `ab19233` (merge of PR #995, the R25 preflight), while R24 was
still in progress. That historical baseline matters because the detailed
inventory and line references below were derived before R24's final merge.

**Current status after R24 completion:** R24 is now merged and authoritative.
`GENIA_STATE.md` records the C++ host as the bounded R24 production host,
and `docs/strategy/release-roadmap.md` marks R24 complete. The merged R24
completion chain is:

- `m0smith/genia-cpp` PR #19 — E24-7 final hardening;
- `m0smith/genia-cpp` PR #20 — E24-8 C++ completion state;
- `m0smith/genia-2026` PR #998 — authoritative R24 truth synchronization.

The final R24 evidence is pinned to Genia revision
`a2229cb9b079a379a5eeae76a618fe69a2bd6daa`: 755 total cases, 141 passed,
614 unsupported, and zero fail/protocol-error/crash/timeout/invalid results.

This status refresh does **not** change the preflight's architectural findings.
Where the analysis below says that R24 had already consumed part of the
historical R26 surface, read that against the now-completed R24 boundary.
The original analysis did not inspect or modify `m0smith/genia-cpp`; its R24
claims were derived from the pinned acceptance evidence in `genia-2026`.

The R25 preflight (`docs/analysis/r25-release-size-preflight.md`) remains the
structural precedent this document follows.

Unless explicitly refreshed above, detailed line references and historical
inventory statements remain relative to `ab19233` and are approximate where
marked `~`.

---

## 1) Executive finding

**R26 as written is not one release. It is four semantic tracks with four
different maturity levels, sharing a title:**

| Track | Portable contract today | Shared evidence today | Extra blockers |
|---|---|---|---|
| **REPL** | Essentially no portable contract | No shared-evidence route at all | — |
| **Bytes/UTF-8** | Small and mostly contracted | Already partly consumed by R24 | — |
| **Strict JSON** | Real, substantial portable contract | Strict-boundary evidence exists | Many unpinned details; several reference-host defects; partly consumed by R24 |
| **ZIP** | Named, but not contracted | None | Split eager/Flow surfaces, raw filesystem authority, and unresolved archive semantics |

Grouping the four under one release label and one capability name
(`bytes_json_zip`) repeats the pattern the exact-numeric postmortem warned
about. In that case, one gate hid several subsystems with independent failure
models.

There are three concrete problems:

1. **REPL is not a data bridge.** It shares no semantic dependency, no
   evidence mechanism and no failure model with Bytes, JSON or ZIP. Its only
   shared dependency is "a working C++ evaluator," which R24 already
   provides. Its blocker is different: there is no portable REPL contract,
   and the R16 runner cannot express a REPL case today.
2. **ZIP is disproportionately different.** It has:
   - raw filesystem path authority;
   - two different read surfaces: eager `zip_entries(path)` and lazy
     Flow-returning `zip_read(path)`; the latter intersects R27 while the
     former shows that ZIP is not categorically blocked on Flow;
   - archive and compression semantics that no contract fixes;
   - security and resource exhaustion questions (path traversal, archive
     bombs, duplicate names);
   - a documented `zip_write(entries, path)` order that does not work in the
     reference host;
   - zero shared cases.

   Grouping ZIP with JSON hides all of this.
3. **R24 has already eaten part of R26, but silently.** Neither the roadmap
   nor the capability vocabulary records it:
   - R24's E24-3 bootstrap evidence requires a C++ Bytes value and native
     `utf8_encode`.
   - E24-7's acceptance evidence requires a scalar-numeric slice of the
     *language-contract* `json_encode`/`json_decode`, plus the R9
     `represent`/`representation_match` carrier.

   This happens while `bytes_json_zip` stays "explicitly out of R24 scope."
   It works only because **no shared case anywhere declares
   `requires: [bytes_json_zip]`**.

**Semantic verdict: SPLIT. Roadmap action for now: RESTRUCTURE without renumbering.**

The REPL, portable data-boundary, and ZIP concerns are separate semantic
tracks. That architectural split does not require assigning new release
numbers today.

- Keep the `R26` number and position for the data-boundary work; renumber nothing.
- Re-scope R26's headline to **C++ Data Bridges: Bytes/UTF-8 and strict JSON**.
- Deliver R26 as an explicit epic sequence, `E26-0` … `E26-6` (§12), gated
  on a first contract/evidence reconciliation step.
- **Remove ZIP from R26.** Defer it to a later, contract-first placement
  whose design explicitly reconciles the eager `zip_entries` surface, the
  Flow-based `zip_read`/Flow-input `zip_write` surface, and R35 resource
  semantics.
- **Remove REPL from R26's completion gate.** Treat it as a separate,
  contract-first portability track. Its final roadmap home is deliberately
  **TBD**; this preflight does not assign it to R33 or any new number.

A semantic SPLIT **is** recommended; a numbered split is not yet required.
Renumbering R27–R41 would disturb R28's existing issue set (#700–#707) and
the settled R37–R41 sequence. Preserve numbering until the maintainer makes
a separate roadmap-placement decision for REPL and ZIP (§12, §15).

---

## 2) Current R26 scope inventory

Roadmap text (`docs/strategy/roadmap/r25-r29.md`, R26 entry):

> Status: Planned, not active. Depends on R24; bridge tracks remain separately
> gated. Theme: extend the minimal host with interactive evaluation and
> deterministic data boundaries. Candidate scope retains the prior plan: REPL
> behavior plus promoted bytes/UTF-8, strict JSON, and ZIP boundaries;
> duplicate-key rejection, JSON safe ranges, Unicode validation, nesting
> limits, deterministic output, normalized Outcomes/errors, and R16
> capability-tagged evidence. Explicit non-goals: pipe/Flow and HTTP serving.

Every area the wording could reasonably reach, classified:

| Area | Authoritative behavior (where) | Capability | Shared evidence | R24 overlap | Classification |
|---|---|---|---|---|---|
| **REPL loop** (start, submission, echo, error recovery, `:help`/`:env`/`:quit`) | Thin. `GENIA_STATE.md` ~L305-310 gives only the start-up line (mode selection). `GENIA_REPL_README.md` ~L773-779 (commands listed only), ~L847 (no automatic `main`), ~L438 (stdout/stderr split). `GENIA_STATE.md` ~L2918-2925 (absence display) | `repl` (optional; **no `capabilities.md` entry**) | **None.** `GENIA_STATE.md` ~L144: "REPL mode is not included in shared executable spec coverage." | None; explicitly out of R24 scope (`capability-floor.json`) | **Independent sibling track; remove from R26; roadmap placement TBD; contract/evidence gap** |
| **Bytes value** (opaque, structural equality, not a map key, `<bytes N>` display) | `GENIA_STATE.md` ~L708-711, ~L2363-2366, ~L3071; R18 contract (bytes → byte sequence; not keyable) | `bytes_json_zip` (bundled) | Equality only: 5 R18 cases, no `requires:`. Nothing on display or key rejection | **Yes, partly.** The bootstrap case `r18-structural-equality-bytes-and-lists.yaml` requires a C++ Bytes value and structural equality | **Partly completed by R24; remainder is definitely R26** |
| **`utf8_encode`** | `GENIA_STATE.md` ~L3041-3042; R19 §3.2 | `bytes_json_zip` | `r19-unicode-utf8-encode-decode-roundtrip.yaml` plus the R18 cases | **Yes.** `GENIA_STATE.md` §0 records "native map_*/utf8_encode functions" (E24-3) | **Already completed by R24** (for well-formed input) |
| **`utf8_decode`, strict** | `GENIA_STATE.md` ~L2508-2513 (R19 U2): message `utf8_decode invalid UTF-8 at byte offset N`, no U+FFFD replacement | `bytes_json_zip` | Round trip only. **No malformed-input case exists, and none can be written today**: Genia source has no way to build arbitrary bytes | Not listed as implemented in C++ | **Definitely R26; contract/evidence gap for malformed input** |
| **Strict JSON decode** (`json_decode`) | `GENIA_STATE.md` ~L3045-3046, ~L3078-3084; R9 contract; R23 §4-§6; `capabilities.md` marks it **`language contract`** | `bytes_json_zip` (in name only; no case uses it) | `json-representation-{decode,errors,number-boundaries}.yaml`, `error-json-decode-input-type.yaml`, one R23 round-trip case; all ungated | **Scalar numeric slice only** (E24-7) | **Definitely R26** (everything past E24-7's numeric slice) |
| **Strict JSON encode** (`json_encode`) | Same sections; "two-space indentation, sorted object member names, preserved list order, direct Unicode scalars" | same | `json-representation-encode.yaml` plus five R23 numeric-encode cases; ungated | **Scalar numeric slice only** (E24-7) | **Definitely R26** (everything past E24-7's numeric slice) |
| **JSON duplicate keys, 128-container nesting, safe integer range, Unicode scalar validation** | `GENIA_STATE.md` ~L3080-3083 | same | Duplicates and range are asserted by reason only. **No nesting, Unicode, `invalid_json_utf8` or `cause` case** | Integer range and Decimal stability are touched only via encode | **Definitely R26; partial evidence gap** |
| **Compatibility JSON** (`json_parse`, `json_stringify`, `json_pretty`) | `GENIA_STATE.md` ~L3048-3051, ~L3075-3076; R23 §6 (numeric reconciliation only); `capabilities.md` marks it **`Python-host-only`** | `bytes_json_zip` | `parse-jsonl-record-json-parse-regression.yaml` (ungated) | None | **Contract gap first.** Portable or not? Then an R26 epic, or an explicit Python-host-only gate |
| **`parse_jsonl_record`** | `GENIA_STATE.md` ~L3095-3103 (Experimental) | none | 7 eval cases plus 1 error case, ungated | None | **R26 candidate epic.** Direct killer-workflow value, but it rides on the compatibility-JSON decision |
| **`json_schema` / Template-to-schema** | R9 E9-6 / R15 | none | ~15 cases, ungated | None; Templates are not in C++ | **Out of R26.** Depends on the C++ Template runtime, which is not scheduled in R24–R27 |
| **R9 representation facet** (`represent`, `representation_match("json")`) | R9 contract | none | many cases | **Implicitly required by E24-7** (round-trip case) but not inventoried in any E24 ticket or `native-primitive-inventory.md` | **Prerequisite.** Must be settled by R24 or explicitly inherited by R26 |
| **Numeric JSON boundary** (R23) | R23 contract §4-§5 | none | 6 × `r23-json-*.yaml` | **Targeted by E24-7** | **Already completed by R24** (once E24-7 lands) |
| **ZIP archive** (`zip_read`, `zip_write`, `zip_entries`, `entry_*`) | `GENIA_STATE.md` ~L3054-3073, ~L3115-3118; `capabilities.md` (`zip.entries`, `zip.write`: **Python-host-only**; `zip.write` misfiled under "Callable Invocation"; **no `zip_read` entry**) | `bytes_json_zip` | **Zero archive-ZIP cases** (`flow-zip-*` is the unrelated Flow `zip` combinator) | None | **Should move to a later release; contract/evidence gap** |
| **Nesting and resource limits** | JSON: 128 containers (strict only). Not specified: decode exponent bound, integer digit bound, compatibility depth, ZIP sizes/ratios | — | None | None | **Contract gap (§10)** |
| **Deterministic output** | JSON encode layout (partly pinned); REPL echo (Python-only); ZIP write (unspecified, not deterministic in Python) | — | 1 encode-layout case | R23 canonical numeric text (E24-7) | **Split per track (§10)** |
| **Normalized failures** | JSON reasons plus context fields (pinned); UTF-8 decode message (pinned); ZIP (inconsistent `none` versus raise); REPL (Python-only) | — | Partial | R24 E24-5 diagnostic boundary (prerequisite) | **Per-track; E24-5 is a prerequisite** |
| **Pipe mode, Flow** | — | `cli_pipe_mode`, `flow_phase_1` | many (ungated) | none | **Out of scope** (R27) |

---

## 3) R24 overlap matrix (JSON and Bytes)

"R24 implemented?" means *obliged by R24's pinned acceptance evidence*. The
two relevant pins are:

- E24-3: `r18-structural-equality-bytes-and-lists.yaml`;
- E24-7: `spec/eval/r22-*.yaml` plus 11 R23 cases, 6 of them
  `r23-json-*.yaml`.

| Concern | R24 implemented? | Portable contract exists? | Shared evidence? | R26 work remaining? |
|---|---|---|---|---|
| Bytes value plus structural equality | **Yes** (E24-3 bootstrap) | Yes (R18) | Yes | None beyond regression |
| `utf8_encode`, well-formed input | **Yes** (E24-3) | Yes (R19 §3.2) | Yes | Type-misuse diagnostic |
| `utf8_decode`, well-formed input | No (not listed) | Yes | Round trip only | Implement |
| `utf8_decode`, malformed input | No | Yes (message pinned in `GENIA_STATE.md`) | **No, and not writable today** | Implement, plus an evidence-route decision (§16) |
| Bytes display `<bytes N>`; Bytes rejected as a map key | No | Display: `N` unspecified. Key rejection: yes (R18), message unspecified | No | Contract `N`; pin messages; add cases |
| `json_encode` of numeric scalars (Integer/Decimal/Rational/Float64) | **Targeted** (E24-7, 5 encode cases) | Yes (R23 §4) | Yes | Signed zero, exponent-form Float64, Integer range on encode |
| `json_decode` of a fraction token → exact Decimal | **Targeted** (1 round-trip case) | Yes (R23 §5) | Partial | Unstable, underflow, `1E2`, `-0` cases |
| Safe-integer range on decode | **No.** `json-representation-number-boundaries.yaml` is *not* in E24-7's list, even though an E24-7 case says it "mirrors" it | Yes | Yes (boundaries and errors cases) | Implement |
| R9 `json` facet carrier (`represent`/`representation_match`) | **Implicitly yes** (needed by the round-trip case); not inventoried | Yes (R9) | Yes | Confirm at R24 audit; otherwise it is R26's first prerequisite |
| Objects and arrays (decode and encode) | No | Yes | Yes | **R26 core** |
| Strings, escapes, Unicode scalars, surrogate pairs and lone surrogates | No | "Unicode scalar" only | Non-ASCII passthrough only | **R26 core, plus contract gaps** (escape set, lone versus paired surrogates) |
| Duplicate names → `duplicate_json_key` (plus `key` context) | No | Yes | Reason only | R26 plus a context case |
| Nesting ≤ 128 → `json_nesting_too_deep` | No | Yes (strict) | **No** | R26 plus boundary cases (128 and 129) |
| Bytes input, `invalid_json_utf8`, BOM | No | UTF-8 yes; BOM no | No | R26 plus a BOM decision |
| Encode layout (indent, separators, empty containers, final newline) | No | Partial | 1 case | Pin separators, empty containers, escaping |
| Key sort basis | No | "sorted" only | ASCII only | **Contract gap.** The reference host sorts by code point; not stated |
| Parse `line`/`column` | No | "1-based" only | **Yes, Python-derived** (`column: 2` for `"{bad}"` in 2 shared cases) | **Contract gap.** Define the unit (code point or byte) and the error position |
| Diagnostic reasons and context (`kind`, `operation`, `status`, `reason`, `cause`, `value_type`) | Reason symbol only (via R23 cases) | Reasons yes; `cause` yes; the `value_type` vocabulary is **not** closed | Partial | R26 plus a `value_type` vocabulary decision |
| Protected-value rejection on encode | No | Yes (`GENIA_RULES.md` ~L697) | No | R26 |
| Compatibility `json_parse` / `json_stringify` / `json_pretty` | No | Numeric only (R23 §6); otherwise Python-host-only | 1 ungated case | **Decision first** (§8) |
| `parse_jsonl_record` | No | Yes (Experimental) | 8 ungated cases | Depends on the compatibility decision |
| `json_schema` | No | Yes | ~15 ungated cases | **Out of R26** (needs the Template runtime) |

**Precise answer to "has R24 already eaten part of R26?"** Yes, in two narrow
places:

- **Bytes:** the value, structural equality, and `utf8_encode` for
  well-formed input.
- **JSON:** the **scalar numeric** codec path of the language-contract
  `json_encode`/`json_decode`. That means R23 canonical numeric text, the
  `stable_json_decimal` check, Rational termination, Float64 finite
  spelling, and lexical fraction→Decimal decode. It also takes along the R9
  facet carrier and Outcome error shape needed to observe them.

R24 did **not** take on structured JSON (objects, arrays, strings), limits,
Unicode validation, Bytes input, layout, compatibility JSON, or anything ZIP.

**Roadmap-staleness risk.** R26's wording ("strict JSON … JSON safe ranges …
deterministic output") would lead an implementer to *re-own* numeric JSON. It
could even rebuild the codec around a different number path. R26's contract
must say:

- numeric JSON is **inherited from E24-7 as a fixed dependency**;
- R26 widens the codec **around** that numeric path;
- R26 must not re-derive or replace that path.

This matches R23 §6 ("reuse common lexical numeric conversion machinery").

**Dependency-policy consequence.** `docs/design/r24/dependency-toolchain-policy.md`
limits `nlohmann/json` to the E16-1 adapter transport. It also forbids using
any library to decide Genia-visible behavior. So R26's structured JSON codec
is a **native C++ implementation**. That is a real, medium-sized
implementation unit, not glue code.

---

## 4) Portable semantic dependency map

**Portable semantic dependencies.** These are frozen or already contracted,
and are consumed, not reopened:

| Dependency | Source | Consumed by |
|---|---|---|
| Unicode scalar strings, UTF-8 as the explicit encoding, no U+FFFD replacement, no host decoder text | R19 (U1/U2) | Bytes/UTF-8, JSON strings, (ZIP names) |
| Bytes value semantics: opaque, structural equality, non-keyable | R18 | Bytes/UTF-8, JSON Bytes input, (ZIP payloads) |
| Canonical numeric rendering; JSON numeric boundary | R23 (landing in C++ via E24-7) | JSON |
| Ordered maps; insertion order versus sorted encode | R17 | JSON |
| Outcome `some`/`none`/`err` with context maps | R9-era, R24 E24-4 | JSON, (ZIP), (REPL echo) |
| Representation facets (`represent`) | R9 | JSON |
| Portable diagnostics / leak discipline | R19, R24 E24-5 | all |
| CLI stdout/stderr/exit-code discipline; value display (`format_display` / `format_debug` equivalents) | `GENIA_STATE.md` CLI section; R23 display | REPL |
| Flow (lazy, single-use) | `flow_phase_1`, R27 for C++ | **ZIP (`zip_read`, `zip_write` of a Flow)** |
| Resource / filesystem authority | `resource_io` today; R35 (Store/Location) later | **ZIP** |

**Host implementation dependencies.** These are C++ mechanics and must never
become Genia semantics:

| Track | Host mechanics |
|---|---|
| REPL | line reader, tty detection, prompt I/O, (optional) history/editing, interrupt handling |
| Bytes/UTF-8 | byte buffer type; in-house UTF-8 validator (already required by R24's source decoding) |
| JSON | native incremental lexer/parser with a depth counter; exact number-token capture; deterministic writer; no delegation to `nlohmann/json` |
| ZIP | archive reader/writer; DEFLATE (a new third-party dependency or an in-house inflate, which requires a dependency-policy amendment); filesystem access |

**The actual dependency shape.** The shape below is corrected from the
brief's hypothesis. The hypothesis puts REPL beside a "data bridges" bundle.
The evidence says the bundle itself is not flat.

```text
R24 (numeric JSON path, Bytes value, utf8_encode, Outcome, facets, diagnostics)
 │
 ├─► REPL ............................ needs only R24's evaluator + display;
 │                                     blocked on its own contract + runner work
 │
 ├─► Bytes/UTF-8 completion ─┐
 │                           ├─► strict JSON decode (Bytes input) ─► strict JSON encode
 │   (independent of JSON    │                                         │
 │    except JSON's Bytes    │                                         ▼
 │    input path)            └───────────────────────────────► compatibility JSON / JSONL
 │                                                              (after portability decision)
 │
 └─► ZIP (contract-first, later)
       ├─► eager `zip_entries` path can exist without Flow
       ├─► `zip_read` / Flow-input `zip_write` consume R27 Flow
       └─► raw path authority must reconcile with R35 resource semantics
           (also needs Bytes/UTF-8 and, for `entry_json`, JSON)
```

**Independence claims:**

- REPL is independent of all bridge tracks.
- Bytes/UTF-8 is independent of JSON, except that JSON's Bytes-input path
  consumes it.
- Strict JSON decode and encode are separable. Encode needs no parser; decode
  needs no writer.
- ZIP is not categorically blocked on Flow because `zip_entries(path)` is
  eager, but the current public ZIP family also includes Flow-based
  `zip_read` and Flow-input `zip_write`, while all ZIP path authority remains
  unreconciled with R35. Treating that mixed family as one R26 capability
  would either narrow the public surface arbitrarily or pull later concerns
  forward.

**R25 independence, verified.** No R26 track consumes Ref, Cell, Process,
threads, mailboxes or any R25 surface:

- JSON and Bytes are pure value functions.
- The REPL is a single-threaded read–eval–print loop.
- ZIP is file I/O.

R26 does **not** depend on R25. The roadmap's "mostly independent" is, on the
evidence, fully independent for the restructured R26.

---

## 5) Capability / evidence analysis

### 5a) Is `bytes_json_zip` too coarse?

**Yes.** It is historical bundling, not one independently claimable surface.
Three independent defects:

1. **It mixes portability classes inside one name.** In `capabilities.md`:
   - `json.decode` and `json.encode` are `language contract`, meaning *all*
     hosts must implement them.
   - `utf8_*`, `json.parse`, `json.stringify`, `zip.entries` and `zip.write`
     are `Python-host-only`.

   A single R16 claim cannot mean both "mandatory" and "optional." Also,
   `HOST_CAPABILITY_MATRIX.md` marks the whole row `Python-host-only`, which
   contradicts the `language contract` entries.
2. **No shared case requires it.** The only `requires:` values in the corpus
   are `open_functions` (29) and `multi_file_eval` (8). So:
   - declaring `bytes_json_zip: supported` gates nothing and proves nothing;
   - declaring it `unsupported` exempts nothing;
   - every JSON, Bytes, compatibility-JSON, JSONL and `json_schema` case is
     applicable to **any** host that runs core eval.

   R24 already relies on this. It implements parts of the bundle under
   `core_ir_eval` evidence while `bytes_json_zip` is formally out of scope.
3. **It forces all-or-nothing.** A host could truthfully support Bytes plus
   UTF-8 plus strict JSON but not ZIP. That is exactly the state this
   preflight recommends for C++ after R26. Today such a host can only:
   - claim `bytes_json_zip` falsely; or
   - leave it `unsupported` while passing most of its surface; or
   - use per-case adapter `unsupported` self-reports that the vocabulary
     cannot explain.

**This is a capability-contract issue to resolve before R26 implementation**
(§16, item 1). This preflight does not create or rename anything.

The decision has two parts:

- **(a) Retro-gate.** Either retro-gate the Python-host-only surfaces
  (compatibility JSON, JSONL, ZIP) with `requires:` under a narrower name, or
  reclassify strict JSON and Bytes as core.
- **(b) Replace the bundle.** Replace the bundle with names matching claimable
  surfaces. For illustration only: bytes/UTF-8, strict JSON, compatibility
  JSON, ZIP archive.

`docs/architecture/executable-semantic-conformance.md` already states the
rule: add a capability only for "a genuinely new independently claimable host
surface." The bundle fails that test in the opposite direction, because it
fuses several such surfaces.

### 5b) Is REPL independently represented?

**By name only.** `repl` exists as an optional manifest capability and a
matrix row. However:

- it has **no `capabilities.md` entry**, and neither do `cli_file_mode`,
  `cli_command_mode` or `cli_pipe_mode`;
- `HOST_INTEROP.md` ~L384 lists REPL under "Current required modes," which
  contradicts the manifest's "optional";
- the Python protocol adapter self-declares `repl: supported` with no shared
  evidence;
- `e24-issue-sequence.md`'s parking-lot pointer for REPL refers to an entry
  that does not exist in `parking-lot.md`.

**No REPL case can exist today.** The block is not only a missing file.
Three layers reject it:

- the loader (`tools/spec_runner/loader.py`) only accepts
  `file`/`command`/`test`/pipe CLI shapes;
- the host executor cannot build an empty argv;
- the Python adapter rejects `argv: []`.

The protocol's `cli` wire shape (`argv` plus a whole-stdin string, one
`{stdout, stderr, exit_code}` result) could carry a **scripted, non-tty,
whole-session** REPL case. It cannot express tty behavior, per-submission
interleaving or interrupts.

### 5c) A related finding outside R26 scope

`cli_pipe_mode` is optional, yet ~20 `spec/cli/*pipe*` cases carry no
`requires:`. The same happens for `model_deterministic_fixture` cases. It is
the same ungated-optional-capability pattern as 5a.

It matters to R26 only as a precedent. Any REPL cases R26 or R33 adds **must**
carry `requires: [repl]` so they do not become core-eval obligations.

---

## 6) REPL-versus-data-bridge cohesion analysis (special question A)

**REPL is not part of "data bridges."**

| Property | REPL | Data bridges |
|---|---|---|
| Boundary kind | Interactive CLI front end (process I/O, session) | Pure value functions (Bytes, JSON), plus file I/O (ZIP) |
| Semantic dependencies | Evaluator, display rendering, CLI stream discipline | R18, R19, R23, R9 facets, Outcome |
| Evidence route | Requires R16 runner/loader/adapter work; tty not expressible | Ordinary `eval`/`error` cases (already used) |
| Failure model | Error → `Error: …` on stderr, **session continues, exit 0** (Python-only behavior) | Outcome `err`/`none` values, or raised misuse errors |
| Killer-workflow value | None directly (developer ergonomics) | JSON/JSONL directly (record parsing) |
| Contract maturity | Almost none (see gaps below) | JSON substantial; Bytes small |

**REPL is not "just another CLI front end" either.** The reference host shows
REPL-specific behavior that no authoritative document fixes:

- it echoes `none("nil")`, whereas command and file mode suppress it (the
  suppression has shared evidence in `spec/cli/command_mode_basic.yaml`);
- the session continues after an error, and the exit code is always 0;
- `stdin` and `argv()` are empty;
- the submission-continuation heuristics are unbalanced brackets, or a
  trailing `=`, `|`, `->` or `?`;
- the prompts are `>>> ` and `... ` on stdout, and there is a banner;
- EOF silently discards an unfinished buffer;
- `:env` dumps the host's whole root environment, builtins included;
- Ctrl-C is unhandled.

Relatedly, `print` returns its last argument, which contradicts
`capabilities.md`'s `io.stdout` "output: `none("nil")`." That changes what a
REPL echoes.

Porting any of this to C++ without first writing a contract is precisely the
"copy Python behavior into the C++ plan" failure the brief forbids, and the
same failure the R25 preflight identified for Actor.

**Conclusion.** REPL shares no implementation, evidence or failure-model
dependency with Bytes, JSON or ZIP that justifies one release. Its natural
cohort is **R33 — Developer Experience and Language Tooling**, which is
already scoped as "make ordinary Genia development pleasant without creating
an editor-local language definition." R33 would own:

- the REPL contract: submission unit, echo rule, error-recovery rule,
  commands, exit code;
- its evidence route.

A C++ REPL then becomes a small host realization of that contract.

---

## 7) Bytes/UTF-8 analysis

- **Authority:** R18 (equality; not keyable), R19 U1/U2 (scalar strings;
  strict UTF-8; no U+FFFD replacement; no host text),
  `GENIA_STATE.md` ~L2511 (exact `utf8_decode` message with first invalid
  byte offset).
- **R24 overlap:** the value, equality and `utf8_encode` are already obliged
  by E24-3. The in-house UTF-8 validator is already required for source,
  stdin and argv decoding (`native-primitive-inventory.md`). That is the
  mechanism `utf8_decode` needs, so implementation cost is low.
- **Remaining R26 work:**
  - `utf8_decode`, both well-formed and malformed;
  - type-misuse diagnostics;
  - `<bytes N>` display;
  - map-key rejection diagnostics.
- **Contract gaps:**
  - which offset is reported for overlong, surrogate-encoding (`ED A0..`),
    greater-than-U+10FFFF and truncated sequences (today this is defined only
    by Python's `UnicodeDecodeError.start`);
  - what `N` in `<bytes N>` means;
  - the map-key rejection message (Python leaks the class name `GeniaBytes`);
  - lone-surrogate `\uD800` source escapes. The lexer accepts them and they
    later leak Python codec text, which contradicts R19's "an
    already-constructed Genia string cannot contain an invalid Unicode
    scalar."
  - `capabilities.md` still documents the errors as Python `TypeError` /
    `ValueError` classes rather than R19's message.
- **Evidence ambiguity stop.** Malformed-UTF-8 shared evidence is
  **impossible without new surface**, because Genia source cannot build
  arbitrary bytes. The routes are:
  - a portable byte-construction function, which is new language surface and
    needs its own contract;
  - a `resource_io`-gated fixture file;
  - an explicit, documented narrowing of the portable claim to well-formed
    input, with malformed behavior proven host-locally.

  This must be decided in E26-0. Host-local tests must not quietly stand in
  for it.
- **Security and resources:** none beyond linear-time validation.
- **Size:** **small.**
- **Killer-workflow value:** supporting only. It enables `json_decode(bytes)`
  and future resource or HTTP bodies.

---

## 8) JSON analysis

The strict boundary (`json_decode`/`json_encode`) is the one R26 track with a
**real, substantial portable contract**. Its sources:

- `GENIA_STATE.md` ~L3078-3084 fixes the value mapping, facet placement,
  limits (safe integers, 128 containers, no duplicates, Unicode scalars),
  reasons, context fields and deterministic output;
- R23 fixes the numeric path.

It also has direct killer-workflow value.

It is still **medium-to-large**, not small:

1. **It needs a native codec.** Dependency policy forbids delegating to
   `nlohmann/json`.
2. **Many observable details are fixed only by Python internals:**
   - key-sort basis (the reference host uses code point order, not UTF-16);
   - string escape set (controls as `\uXXXX`; `/`, DEL and U+2028 unescaped);
   - separators and empty-container layout;
   - BOM rejection;
   - `line`/`column` units and error position. These are *already asserted*
     in two shared cases with a Python-scanner-derived `column: 2`;
   - which error wins when several apply (scanner-hook order versus
     post-walk order);
   - the `value_type` vocabulary;
   - compatibility-surface duplicate, depth and NaN behavior.
3. **The reference host has live defects that break the portable contract**
   (found by probing during this preflight; not fixed here):
   - `json_decode("1e999999999")` does not terminate in practical time. There
     is no exponent bound, and `stable_json_decimal` materializes `10**exp`.
     This is a resource-exhaustion defect.
   - `json_decode` of a 5000-digit integer leaks Python's
     "Exceeds the limit (4300 digits)…" and exits 1, which violates R23 §8.
   - `json_encode(quote(a))` reports `value_type: "GeniaSymbol"`. This is a
     Python class-name leak of the same class E23-6 and E23-8 repaired.
   - Compatibility `json_parse("NaN")` / `Infinity` produce Float64 non-finite
     values, which contradicts the spirit of R23 §5-§6.
   - Compatibility `json_parse` of 5000-deep input leaks Python recursion
     text.
   - Compatibility `json_parse("\"\\ud800\"")` builds a lone-surrogate string
     that later leaks codec text.

   If C++ implements "the contract" while Python still has these defects,
   cross-host disagreement will be resolved by argument rather than by
   evidence. **These must be repaired in the reference host, or the contract
   must be clarified, before the corresponding C++ epic.** This is the
   ambiguity-stop rule, and the exact-numeric precedent.
4. **Compatibility JSON (`json_parse`/`json_stringify`/`json_pretty`,
   `parse_jsonl_record`) is a separate decision.** It is:
   - documented `Python-host-only`;
   - reconciled only numerically by R23;
   - different in failure shape (`none` versus `err`);
   - carrying Python `exc.msg` text in its context `message` field;
   - unlimited.

   Yet its cases run ungated. R26 must first decide whether it is portable:
   - **If portable:** it needs its own contract for failure shape, limits and
     message removal, then its own epic.
   - **If not portable:** its cases must be gated before any C++ host claims
     core eval.

   `parse_jsonl_record` is the most killer-workflow-relevant item in all of
   R26, and it rides on this decision.
5. **`json_schema` is not an R26 item.** It depends on the Template runtime,
   which no C++ release through R27 schedules.

**Size:**

- strict decode: medium;
- strict encode: small-medium;
- compatibility plus JSONL: small-medium, contract-heavy;
- together: **medium-large**.

---

## 9) ZIP analysis (special question B)

**ZIP is disproportionately different, and grouping it with JSON obscures
that.**

- **Surface.** `zip_read(path) -> Flow | none`, `zip_write(path, flow_or_list)`
  (plus a stage form), `zip_entries(path) -> list`, and
  `entry_name`/`entry_bytes`/`set_entry_bytes`/`update_entry_bytes`/`entry_json`.
  All take **raw host filesystem paths**. All are `Python-host-only`.
  `zip_read` has no `capabilities.md` entry, and `zip.write` is misfiled.
- **Documented behavior contradicts the reference host.** The documented
  `zip_write(entries, path)` order is implemented by a helper that is **never
  registered**. The public 2-arity form is the prelude's path-first form, so
  `zip_write(entries, path)` returns
  `none("zip-write-error", {expected: "string_path", …})`.
  `capabilities.md` documents `TypeError`/`RuntimeError` for it, but the real
  behavior is `none(...)`.
- **Inconsistent failure model:**
  - `zip_read` returns `none("file-not-found" | "zip-read-error", …)`;
  - `zip_entries` **raises**;
  - OSError contexts carry Python errno text;
  - read errors that happen later, during lazy Flow iteration (CRC mismatch,
    encrypted entries, file deleted), are uncaught.
- **No archive contract at all:**
  - entry-name rules (separators, `..`, absolute paths, backslashes,
    encoding);
  - directory entries (silently skipped);
  - duplicate names (read yields the last entry's payload for every
    duplicate; write allows duplicates);
  - compression method (the writer uses STORED; the reader accepts whatever
    Python does);
  - timestamps (current local time, so written archives are not
    deterministic);
  - ZIP64 and encryption;
  - overwrite semantics;
  - resource limits (entries are read fully into memory; no size, count or
    ratio bound; no archive-bomb guard);
  - rendering (`<zip-entry 'name' N>` uses Python `repr` quoting).
- **Cross-release dependencies:**
  - **Flow** (`zip_read` and a Flow-consuming `zip_write`): Flow is an R26
    non-goal and belongs to R27.
  - **Filesystem authority:** this is `resource_io` today and the R35
    Store/Location model later. R35 deliberately rejects "OS path/full URI
    semantics," yet ZIP's contract is built on raw OS paths.
  - **The dependency policy:** a DEFLATE implementation is either a new
    third-party dependency or an in-house inflate. Both need a policy
    amendment, and neither was contemplated by R24's policy.
- **Evidence:** zero archive-ZIP shared cases. Honest cases need fixture
  archives, and so a fixture/provisioning mechanism. That is the same gap
  `execution_process` documents.
- **Killer-workflow value:** low. It has one example
  (`examples/zip_json_puzzle.genia`) and no JSONL/CSV-in-ZIP workflow
  contract.
- **Size:**
  - **large inside R26**, because the current ZIP family mixes eager archive
    access, Flow-based archive access, compression policy, raw path authority,
    and an uncontracted failure/resource model;
  - **release-threatening** if attempted as one R26 claim, because an
    implementer must either narrow the public ZIP family, pull Flow concerns
    forward, or let host/archive-library defaults define semantics;
  - once separately contracted with its eager/Flow split and R35 authority
    relationship explicit, **medium**.

**Recommendation:** remove ZIP from R26 entirely. Record it as a
contract-first candidate whose eventual placement explicitly accounts for
R27 Flow where applicable and R35 resource authority. The exact roadmap home
is a separate decision.

In the meantime, the reference-host documentation contradictions
(`zip_write` argument order, error classes, misfiled entry) are worth a
narrow documentation/implementation repair in `genia-2026`, independent of
any C++ work.

---

## 10) Resource, security and failure boundary analysis

| Concern | REPL | Bytes/UTF-8 | Strict JSON | Compatibility JSON | ZIP |
|---|---|---|---|---|---|
| Input size / time bound | n/a | linear validation | **Unbounded decode exponent (live hang); integer digit bound uncontracted** | none | **none (full in-memory read; no ratio bound)** |
| Depth bound | n/a | n/a | 128 containers (contracted, **no shared case**) | **none (Python recursion leak)** | n/a |
| Authority | process stdin/stdout only | none | none | none | **raw filesystem read/write; overwrite** |
| Path / security | n/a | n/a | n/a | n/a | **traversal, absolute names, duplicate names uncontracted** |
| Failure shape | stderr `Error: …`, continue, exit 0 (Python-only) | raise (R19 message) | `err(reason, ctx)`, pinned reasons | `none(reason, ctx)` with host text | mixed `none` and raise, host text |
| Determinism | echo format, prompts (Python-only) | total | layout partly pinned | pinned layout | **writes are not deterministic** |
| Locale / platform | tty detection varies by OS | none | none, if codec is native | none | **path separators, name encodings, filesystem case sensitivity** |

The strict-JSON resource defects are **portable-contract defects**. They are
not C++ concerns. They belong in E26-0, as a contract clarification (maximum
exponent magnitude and digit count, with a pinned reason) plus a reference-host
repair.

---

## 11) Release-size assessment

| Track | Size | Why |
|---|---|---|
| REPL (C++ realization only, given a contract) | small | line loop over the existing evaluator |
| REPL contract plus R16 evidence route | medium | new CLI case shape (empty argv plus scripted stdin), loader/executor/adapter changes, `capabilities.md` entry, and several unpinned behavior decisions |
| Bytes/UTF-8 remainder | small | validator already exists for source decoding |
| Strict JSON decode | medium | native parser, limits, Unicode, Bytes input, facets, diagnostics |
| Strict JSON encode | small-medium | deterministic writer; escape and sort basis first |
| Compatibility JSON plus `parse_jsonl_record` | small-medium | decision-heavy; small code once decided |
| `json_schema` | out of R26 | Template runtime dependency |
| ZIP | large inside R26 (release-threatening if forced) | Flow, authority, compression dependency, security, zero contract |
| Capability reconciliation (`bytes_json_zip`) | small-medium | vocabulary plus retro-gating many cases; cross-cutting |

**Overall:**

- **As written**, R26 is **large, trending release-threatening**. It has:
  - four semantic domains;
  - one fused capability;
  - five distinct failure models;
  - two tracks (REPL, ZIP) with no portable contract;
  - one track (ZIP) needing a post-R26 release;
  - live reference-host defects in the one well-contracted track.
- **Restructured** as in §12, R26 is **medium**. Seven epics, each small or
  medium, with one coherent headline claim.

**Comparison with R24 and R25:**

- **Numeric-gate postmortem.** R26-as-written has the same structural fault:
  one release label over several subsystems with independent failure
  models. The postmortem's warning rule applies directly: *"If one
  implementation PR begins changing more than one semantic subsystem plus its
  tests/documentation, stop and reassess."* A "C++ REPL and Data Bridges" PR
  series would cross four.
- **R24.** Even pre-decomposed into eight epics, R24 produced roughly one
  repair per landed epic. `bootstrap-cases.json` alone was re-pinned three
  times, because cases silently required out-of-slice machinery. R26 has the
  same trap in stronger form:
  - JSON cases silently require the facet carrier, Outcome patterns and
    Templates;
  - the capability that should gate them gates nothing.
- **R25 preflight.** R25's fault was one out-of-place subsystem (Actor) that
  would have set portable semantics by implementation precedent. R26 has
  **two** such subsystems:
  - **REPL:** porting Python's echo, continuation and error-recovery behavior
    would make it the REPL contract by precedent.
  - **ZIP:** porting Python's STORED/local-time/no-limit archive behavior
    would make it the archive contract by precedent.

  The remedy is the same: extract them, and make contract-first placement a
  separate decision.
- **Native-primitive burden.** R26 is lower than R24 for Bytes and JSON: the
  UTF-8 validator and numeric path already exist. It is **higher** than R24
  for ZIP, which needs a new compression dependency class.

---

## 12) Recommended decomposition

**Semantic verdict: SPLIT. Roadmap action for now: RESTRUCTURE without renumbering.**

- Keep `R26` as the data-boundary release, with its number and position.
- Narrow its headline claim to **"The C++ host provides the portable
  Bytes/UTF-8 and strict JSON data boundaries with evidence-backed capability
  claims."**
- Extract ZIP.
- Take REPL out of R26's completion gate.

**Evidence-derived epic order:**

| Epic | Scope | Size | Gate |
|---|---|---|---|
| **E26-0** | Contract / evidence reconciliation (`genia-2026` only). See the item list below the table. | small-medium | Must close before any `genia-cpp` R26 code |
| **E26-1** | Bytes/UTF-8 completion in C++: `utf8_decode` (well-formed; malformed per the E26-0 decision), `<bytes N>` display, key rejection, misuse diagnostics | small | E26-0 |
| **E26-2** | Strict JSON decode: the native parser wrapped around the E24-7 numeric path. Objects and arrays, strings and Unicode scalars, surrogate pairs, duplicates, 128-depth limit, safe range, String and Bytes input, `json` facet, pinned reasons and context, `line`/`column` per E26-0 | medium | E26-0, E26-1 (Bytes input) |
| **E26-3** | Strict JSON encode: deterministic writer (indent, separators, empty containers, sort basis, escape set), limits, protected values, `value_type` vocabulary | small-medium | E26-0 (independent of E26-2 in code; ordered after it for audit cohesion) |
| **E26-4** | Compatibility JSON plus `parse_jsonl_record`, **only if E26-0 decides they are portable**; otherwise this epic reduces to confirming that the gating landed | small-medium | E26-0, E26-2, E26-3 |
| **E26-5** | Adversarial hardening: resource bounds (exponent/digits/depth), diagnostic-leak sweep, as E24-5 did | small | E26-2..4 |
| **E26-6** | Truth sync plus skeptical release audit against merged `main` | small | all |

**E26-0 items:**

1. **Decide the capability model.** Either:
   - retro-gate Python-host-only JSON/JSONL/ZIP cases, or reclassify strict
     JSON and Bytes as core; or
   - propose replacing `bytes_json_zip` with names matching claimable
     surfaces.

   Resolve the matrix-versus-`capabilities.md` contradiction.
2. **Pin the strict-JSON details:**
   - key-sort basis;
   - escape set;
   - separators and empty containers;
   - BOM handling;
   - `line`/`column` unit and error position;
   - error precedence;
   - `value_type` vocabulary;
   - decode exponent and digit bounds with a reason.
3. **Repair or clarify the reference-host defects in §8.3.**
4. **Decide compatibility-JSON portability.**
5. **Decide the malformed-UTF-8 evidence route.**
6. **Record the inheritance.** Numeric JSON and the R9 facet carrier are
   inherited from E24-7 and are not re-owned.
7. **Add the missing shared cases before C++ work begins.** In particular:
   nesting 128 and 129, lone and paired surrogates, `invalid_json_utf8`, the
   duplicate `key` context, the `cause` field, and layout details.

**Rules carried over from R24 and R25:**

- No capability is declared `supported` until its gated shared cases pass.
- Host-local unit tests are implementation evidence only.
- A case that silently needs out-of-slice machinery (Templates,
  Flow, `resource_io`) is re-gated or replaced. It is never implemented
  "while we're here."

**Extracted tracks (no renumbering yet):**

- **REPL.** Remove it from R26's completion gate and treat it as a separate
  portability track. Its final numbered home is **TBD**. Before any C++ REPL
  implementation, define the REPL contract (submission unit, echo rule
  including `none` display, error recovery and exit code, commands,
  stdin/argv inside the REPL, EOF and interrupt) and add an R16 evidence route
  (for example, scripted-stdin CLI evidence gated by `requires: [repl]`).
  A later roadmap decision can place that track in R33, a small standalone
  release, or another justified slot; this preflight intentionally does not
  decide that placement.
- **ZIP.** Remove it from R26. Record it as a contract-first candidate that
  explicitly separates eager `zip_entries` from Flow-based `zip_read` /
  Flow-input `zip_write`, reconciles raw path authority with R35, and performs
  its own dependency-policy review for compression. Placement is a later
  roadmap decision.
- **`json_schema`.** Out of R26. It follows whichever future release brings
  Templates to C++.

**Why semantic SPLIT does not require immediate renumbering:**

- REPL, the portable data boundary, and ZIP are independent semantic tracks,
  so the architecture is a split.
- Assigning new numbers today would push R27–R41 and churn R28's existing
  issue set (#700–#707, E28-*), before REPL's eventual home has even been
  decided.
- Therefore keep numbering stable now and make placement a separate roadmap
  decision after this analysis is accepted.
- A hypothetical numbered SPLIT shape, for the record only:
  - R26 = data bridges;
  - R27 = C++ REPL;
  - R28 = Flow, pipe mode, HTTP (former R27);
  - … every later release +1 through R42;
  - with ZIP still needing a post-Flow slot.

  That is strictly more disruptive for the same semantic outcome.

---

## 13) Smallest first R26 slice

**E26-1 — C++ Bytes/UTF-8 completion**, preceded by the Bytes/UTF-8 items of
E26-0 only.

- **Headline claim:** "The C++ host's `utf8_decode`, Bytes display, and Bytes
  map-key rejection match the portable R18/R19 contract, completing the Bytes
  surface whose value and `utf8_encode` R24 already established."
- **Prerequisites:**
  - R24 complete and audited, including E24-5's diagnostic boundary;
  - the E26-0 decisions on (a) the malformed-UTF-8 evidence route and (b) the
    meaning of `<bytes N>` plus the pinned misuse and key messages;
  - the capability decision for how Bytes cases are gated or classified.
- **Exclusions:**
  - no JSON of any kind;
  - no ZIP, `resource_io` or HTTP bodies;
  - no new byte-construction language surface unless E26-0 separately
    approves it;
  - no REPL;
  - no capability claim beyond what E26-0 authorizes.
- **Bounded surface:** `utf8_encode` (regression), `utf8_decode`, Bytes
  display, Bytes equality (regression), and Bytes key rejection.
- **Shared executable proof:**
  - existing: `r19-unicode-utf8-encode-decode-roundtrip.yaml` and the five
    R18 Bytes cases;
  - new, from E26-0: display, key-rejection and misuse cases;
  - malformed-input cases, if E26-0 finds a route. Otherwise the claim is
    explicitly narrowed to well-formed input.
- **Implementation-independent semantics:** every observation traces to R18,
  R19 or `GENIA_STATE.md`, not to `builtins.py`.
- **Completion criteria:**
  - all applicable cases pass via `tools/spec_runner --host`, with 0 fail and
    0 crash;
  - no host decoder or class-name text in any diagnostic;
  - the capability declaration matches the E26-0 vocabulary exactly.
- **Skeptical audit gate:** an independent audit against merged `genia-cpp`
  `main` and the pinned `genia-2026` revision.

**Dependence on R25: none.** E26-1 uses no concurrency, state primitives or
R25 capabilities. It can begin as soon as R24 truth is settled, whether R25
is started, in progress or complete.

---

## 14) Explicit non-goals

This preflight does not, and R26 planning built on it must not:

- implement any R26 behavior, or modify `m0smith/genia-cpp`;
- begin R27 (Flow, pipe mode, HTTP) or R33;
- modify, re-scope or re-pin R24 work (the R24 observations in §3 and §5 are
  findings for the maintainer, not edits);
- change Genia runtime semantics, `GENIA_STATE.md`, or parser/AST/Core IR
  behavior;
- add, rename or remove capabilities (§5 records concerns only);
- create shared specs, implementation tests or implementation tickets;
- repair the reference-host defects found in §8.3 and §9 (they are recorded
  as follow-ups);
- edit or renumber the roadmap;
- merge anything.

---

## 15) Risks and regret checks

- **Keeping R26 as written:**
  - ZIP either stalls R26 on R27 or ships a Flow-less ZIP that diverges from
    the reference host.
  - REPL gets defined by porting Python.
  - `bytes_json_zip` gets claimed dishonestly.
  - This recreates the R24 repair-churn pattern across four subsystems at
    once.
- **Splitting into numbered releases:** renumbering churn through R41 and
  R28's issue set, for no semantic gain over re-homing.
- **Skipping E26-0:** the C++ JSON codec would bake in whichever
  sort, escape, column and precedence choices its author makes. Then either
  Python (the reference) or C++ looks "wrong" with no contract to decide.
  The live Python hang and leaks would surface first as mysterious cross-host
  failures.
- **Leaving capability gating untouched:** a post-R24 C++ host faces every
  ungated JSON, JSONL, `json_schema`, model-fixture and pipe-mode case as a
  core-eval obligation. It can only self-report per-case `unsupported`, which
  the vocabulary cannot explain.

  The same exposure may already affect R24's own completion gate ("every
  applicable shared case in the declared minimal capability set"). That is
  flagged for the R24 audit, not acted on here.
- **Prematurely assigning REPL to R33:** R33 currently focuses on formatter,
  editor diagnostics, navigation and related tooling; it does not yet claim
  REPL portability. Assigning REPL there in this preflight would turn an
  adjacency into a roadmap decision. Keep placement TBD until separately
  approved.
- **Deferring ZIP:** the Python-only ZIP example stays Python-only for
  longer. This is low regret given its killer-workflow weight and its current
  documentation contradictions.
- **Re-owning numeric JSON in R26:** duplicated or divergent numeric paths.
  This is mitigated by E26-0 item 6.

---

## 16) Required follow-up contracts

1. **Capability vocabulary decision (highest priority, cross-cutting):**
   - replace or split `bytes_json_zip`;
   - retro-gate or reclassify the ungated JSON, JSONL and Bytes cases (and,
     by the same precedent, `cli_pipe_mode` and `model_deterministic_fixture`
     cases);
   - add `capabilities.md` entries for `repl` and the CLI modes;
   - reconcile `HOST_CAPABILITY_MATRIX.md` with the `language contract`
     entries and with `HOST_INTEROP.md`'s "required" REPL listing.
2. **Strict JSON detail contract:**
   - key-sort basis;
   - escape set;
   - layout;
   - BOM;
   - `line`/`column` semantics;
   - error precedence;
   - `value_type` vocabulary;
   - decode exponent and digit bounds with a reason;
   - explicit inheritance of the E24-7 numeric path.
3. **Reference-host repairs:**
   - the unbounded-exponent hang;
   - the >4300-digit leak;
   - the `GeniaSymbol` leak;
   - compatibility NaN/Infinity, depth and lone-surrogate behavior;
   - the lone-surrogate source-escape contradiction with R19.
4. **Compatibility JSON / JSONL portability decision:** failure shape, limits,
   and removal of host `message` text, or explicit Python-host-only gating.
5. **Malformed-UTF-8 evidence route:** byte-construction surface, a
   `resource_io` fixture, or an explicitly narrowed claim. Also pin the
   offset semantics.
6. **REPL contract, for its later separately approved roadmap home:**
   - submission unit;
   - echo rule;
   - error recovery and exit code;
   - commands;
   - stdin/argv inside the REPL;
   - EOF and interrupt;
   - the `print` return-value contradiction;
   - the R16 scripted-session case shape plus the loader/adapter changes.
7. **ZIP contract, contract-first, with R27/R35 relationships explicit:**
   - entry names and traversal;
   - duplicates;
   - directories;
   - compression;
   - timestamps and determinism;
   - limits;
   - authority (R35 alignment);
   - one failure model;
   - the dependency-policy amendment for DEFLATE;
   - repair of the documented `zip_write` argument-order and error-class
     contradictions.
8. **Stale-reference cleanup:**
   - `e24-issue-sequence.md`'s nonexistent parking-lot REPL entry;
   - the "6" versus actual 11 `r22-*.yaml` count in E24-7 and the obligation
     map;
   - pre-R23 "binary64" wording in `GENIA_RULES.md` ~L1274,
     `capabilities.md` ~L571 and the R9 contract.

---

## 17) Stop gate

This preflight stops here.

- No R26 implementation has started.
- `m0smith/genia-cpp` has not been read or modified.
- No R24, R25, R27 or R33 work has been touched.
- No Genia runtime, parser or Core IR behavior has changed.
- No capability has been added or renamed.
- No specs, tests or tickets have been created.
- The roadmap is unedited.
- Nothing has been merged.
- `GENIA_STATE.md` is unchanged.

`docs/analysis/` is not staged by `tools/stage_docs_for_mkdocs.py`, so no
published-doc synchronization is required.

---

## 18) Direct answer to the central question

**Is "C++ REPL and Data Bridges" one coherent, realistically sized release?**

**No. It is a thematic bundle.** It contains:

- a REPL with no portable contract or evidence route;
- a small Bytes/UTF-8 remainder;
- a well-contracted but detail-heavy strict JSON boundary with live
  reference-host defects;
- an uncontracted ZIP family spanning eager and Flow-based access plus raw
  filesystem authority.

These share a title and one fused capability name, not dependencies, failure
models or evidence.

**Would beginning R26 as currently written risk repeating R24's
oversized-release problem?**

**Yes, and in a worse form than R25 did.** It reproduces the
multi-subsystem-gate fault the exact-numeric postmortem diagnosed: four
subsystems, five failure models. Beyond size, it adds three risks R24 did not
have:

1. **Two tracks would set portable semantics by C++ precedent:**
   - REPL echo, continuation and error recovery;
   - ZIP archive behavior.
2. **One track spans later concerns.** ZIP has an eager `zip_entries` path,
   but the same public family also includes Flow-based `zip_read` / Flow-input
   `zip_write` and raw path authority that must reconcile with R35.
3. **Its only capability name gates nothing.** Every "evidence-backed
   capability claim" R26 promises would be unfalsifiable until the vocabulary
   is fixed.

It also partly duplicates work R24's E24-3 and E24-7 already own, because the
roadmap does not record that overlap.

**The fix is cheap and needs no renumbering:**

- keep R26 as a medium, epic-sequenced **Bytes/UTF-8 plus strict JSON**
  release, gated on an E26-0 contract/evidence reconciliation;
- remove REPL from R26 and leave its final roadmap home TBD pending a
  separate contract/placement decision;
- defer ZIP to a contract-first slot whose eventual placement explicitly
  accounts for its eager/Flow split and R35 authority model.
