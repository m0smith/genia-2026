# F2 P2-0 decision record — contract resolution (issue #1067)

Phase: **contract only.** The amended contract is
`docs/design/f2-module-entry-scope-isolation-contract.md` §16 (PROPOSED).
No runtime, test, STATE, RULES, REPL README or README change is made.
`GENIA_STATE.md` remains final authority and describes single-root behavior.
Pre-flight: `.genia/process/issue-1067-f2-p2-preflight.md` (CONDITIONAL GO).
Tracking: #1067; completion gates #1220, #1221; pre-flight PR #1223.

## Baseline confirmed

`origin/main` = `95c5bfb` (merge of #1223). P1 is on `main` (P1-H record present).
The pre-flight verdict is CONDITIONAL GO; #1220 and #1221 are open and are recorded
as P2 completion gates (contract §10, P1-H record, #1067 comment 6155448975). No
#1067 comment or later document supersedes the pre-flight; D2/D2b, the reflection
mechanism and the deadline unit were recommended but never ruled by the maintainer.

Independently re-verified (throwaway probes, not committed):

- 13 program-construction sites (6 in `interpreter.py`, 1 in `test_cli.py`, 6 in
  `hosts/python`); other `Env(` sites are R creation, the module Env, the
  metacircular base, evaluator frames, and two catalogue-only tools.
- Child `E = Env(R)`: entry `first/1`, `map/1`, `map_acc/3` land in E and shadow;
  `rows/0` hides R's `rows/1` (`No matching function: rows/1. Available: rows/0`);
  `log = 5` rebinds R; `entry_scope()` and `unit_scope()` both return R.
- Shared root: entry `first/1` or `map_acc/3` breaks the prelude's `map`
  (entry-to-prelude hijack), so "unchanged" in P2 preserves a failure for those names.
- Prelude: 319 declared top-level names; 217 autoload-registered; 102 unregistered in
  13 files; 241 builtins; no overlap; `main` and `test` are not runtime names.
- Running all entry source in a child scope (throwaway plugin): the metacircular
  unit tests pass; `help`/docstring tests and the module harness fail, as the
  pre-flight predicted.
- `_emit_error`, `_write_stdout/_write_stderr` read `env.values` of the supplied Env;
  `run_source` writes debug hooks/mode on the supplied Env; `mcp_worker` prunes then
  evaluates in the same Env; `mcp_host` runs the server program then `env.get("serve")`.
- Existing host-local switches are environment variables (`GENIA_DEBUG_OPT`,
  `GENIA_MCP_WORKER_DIAG`); `spec/known_host_gaps.json` is `host: cpp` capability scoped.

## Decisions

| Decision | Ruling (contract section) | Status |
|---|---|---|
| D1 collisions / write-through | Runtime-owned set = R keys, internal keys, autoload names, and a static manifest of every top-level prelude declaration (registered or not). Entry top-level operations on runtime-owned names bind in R exactly as today; all else binds in E. E records entry-declared runtime-owned names for host consumers. No per-arity machinery. (§16.1) | PROPOSED; approval needed |
| D2 reflection / help | Activate §7.1 evaluation-bound reflection in P2; catalogue/sink always R; fallback never applies; module reflection of E-resident entry names stops resolving. (§16.2) | PROPOSED; approval needed |
| D3 fallback / strict switch | Keep fallback; structural eligibility, no registry; `GENIA_STRICT_MODULE_SCOPE=1` makes a fallback read the ordinary `NameError`; one marker; hybrid deadline; no manifest or expiry check. (§16.3) | PROPOSED; deadline needs approval |
| D4 metacircular `eval` | `empty_env()` base is a child of R only; labeled observable change; no fallback. (§16.4) | PROPOSED; approval needed |
| D5 #1220 | Reads are legitimate; revised criteria: runtime accessor, source guard, real separated-scope tests. (§16.5) | PROPOSED; issue updated |
| D6 registration / tests | `create_entry_scope()` on R, one construction helper for 13 sites, `set_host` class routing, runtime-accessor sinks/debug state, non-aliased fixture, no suite-wide mode. (§16.6) | PROPOSED; approval needed |

### D1 — analysis

Current: one shared Env; entry declarations occupy the same binding the prelude
uses. Conflict: §9.1 rows 2–3 require "unchanged" while §4.1/§4.4 and row 4 imply
entry bindings are E-resident and unreachable by the prelude; a child E violates
rows 2–3 (probe). Alternatives: (A) write-through keyed on a complete runtime-owned
set (chosen); (B) write-through keyed on public surface only, making unregistered
helpers shadow in E — a visible change that contradicts the approved table and
pulls part of P3 forward; (C) autoload registry only — rejected, it misses 102
declared names (`map_acc`, `list?`, `get_or`, …); (D) start shadowing in P2 —
rejected, needs D2/D2b. Smallest coherent rule: A. Row 4 is reworded to "E-resident
entry binding"; names written through are R bindings by the P2 compatibility rule,
so row 4 and the new rule do not conflict. Residual (stated, removed in P3): an
entry declaration of a runtime-owned name is still visible to modules and the
prelude, including helper-name hijack and `internal_values` shadowing. This is the
approved P2 behavior, it is a closed enumerable set (not an open shared root), and
the module-to-entry read leak and the prelude-to-E write leak are removed for every
other name. Security: write-through confers no capability; MCP pruning runs on R
before E exists, and the static manifest is unaffected by pruning.

### D2 — analysis

Current: closures capture R; with E ≠ R, entry names are not found. Alternatives:
(a) evaluation-bound (chosen; D1 already approved, mechanism recommended in the P1
design §6); (b) interim "reflection binds E for everyone" — gives module code E
authority and contradicts §11.2.3. The only intentional behavior change besides
improvement (module-own `doc`) is that module reflection of E-resident entry names
stops working; this is already required by §11.2.3 and is now labeled. Mechanism
detail (value marking, helper for all identifier paths, identity) stays in the P1
design §6; a Core IR need would stop the work.

### D3 — analysis

Alternatives for the switch: CLI flag (forbidden, §15), API keyword (extra surface),
environment variable (chosen, precedent exists). Strict mode = P3 outcome, so it
cannot mask leakage or add a second failure mode; CI runs strict, fallback tests
clear it explicitly. Registry: known_host_gaps.json rejected (schema); the removal
issue + one STATE marker is the record. Rejected as unnecessary machinery: a
repository-program execution manifest and a date-expiry check (P1 design §7 items
beyond contract §11). Deadline: hybrid from the P1 design §7, decided for approval.

### D4 — analysis

`empty_env()` has no caller scope, so any E-visible base would hand module code
entry authority (§5). Restricting is therefore the only option without a further
mechanism. Cost: entry programs that eval quoted code naming an E-resident entry
function must `define` it. Repository evidence shows no such use; third-party use is
unknown. Alternative (evaluation-bound `empty_env`) recorded, not adopted.

### D5 — analysis and issue action

Target model: `make_global_env`'s `env` is R; `root()` on R is R. The reads are
legitimate and behavior-neutral to change. Original criterion 2 ("fail against the
old implementation") cannot hold on accessor spelling alone, so it is replaced by a
source guard plus real separated-scope tests with a non-aliasing control. #1220 is
kept open and its body updated with the revised criteria (original text preserved).

### D6 — analysis

Defaults preserve the 171 test files (caller-created roots keep entry == root).
Separation becomes real only at host entry points; therefore the construction
helper is the single enforcement point and the non-aliased fixture is the test-side
enforcement. A suite-wide mode would require rewriting five root-inspecting
harnesses without adding boundary coverage; rejected in favor of scoped fixtures.
Entry-only injection before E exists fails closed.

## P3 boundary

Deferred unchanged: D2 finality, D2b (per-arity shadowing), shadowing, `NameError`,
fallback and write-through removal, `internal_values` hardening. The P2 model is
coherent without them; no interim semantic rule was invented. Gate P2→P3 must have
D2/D2b ruled.

## Contract consistency audit (changes made for coherence)

| Statement | Conflict found | Resolution |
|---|---|---|
| §4.2 E "Contains", §4.4 | implied all entry names are E-resident | qualifier + definition of "entry binding" |
| §9.1 row 4 | "removed" vs write-through names living in R | reworded to E-resident bindings |
| §9.1 prose | mechanism unspecified | pointer to §16.1; D2b not needed in P2 |
| §6.1 | `entry-only` module reads | stated as fallback event / `NameError` |
| §8 table | discovery vs write-through; sink, debug state, `eval` rows absent | rows added/qualified |
| §10 P2 row | listed two effects only | all P2 observable changes listed |
| §10 #1220/#1221 paragraph | stale acceptance wording | points to §16.5/§16.6 |
| §11.2–11.5 | switch, registry, deadline unspecified; "module code" scope | resolved; prelude/R and `eval` excluded |
| §12 | write-through/construction not labeled host-only | labeled |
| §13, §14 | MCP/matrix/book obligations; deadline open question | added/pointed |

## Future failing-test requirements

| ID | Proves | Fails today / wrong accessor | Real separation | Location |
|---|---|---|---|---|
| T-D1a | four §9.0 collision rows identical with E registered, incl. `map_acc` | child E shadows/hides (probe) | yes | Python unit |
| T-D1b | non-runtime-owned entry name absent from R, invisible to prelude | shared root exposes it | yes | Python unit + native |
| T-D1c | manifest drift: every prelude top-level declaration ⊆ manifest ⊇ autoload names | registry-only derivation misses 102 | no | Python unit |
| T-D1d | main/test/serve/`:env` see entry-declared runtime-owned names | consumers handed R or bare E | yes | Python unit |
| T-D2 | reflection per §16.2 table, incl. `map(doc, names)`, transferred, user-rebound `doc`, module attempting E name, pruned catalogue | R-captured reflection misses entry names; E-for-all leaks to modules | yes | shared spec (evaluation scope) + Python unit |
| T-D3 | fallback eligibility, dedupe, no value/path text, strict → `NameError`, never for writes/reflection/exports/prelude/`eval`/runtime-owned | n/a (new) | yes | Python unit + native |
| T-D4 | `empty_env()` cannot read E-resident names from entry or module; `define` works | base child of root/E exposes them | yes | Python unit + native |
| T-D5 | source guard (`.root()` outside `environment.py`, `.autoloads` not via `runtime_scope()`); `help()` equal from E/M/R; control `E.autoloads == {}` | guard fails on `builtins.py` reads; lookup-scope catalogue empties help | yes | Python unit |
| T-D6a | `create_entry_scope()` semantics, second call raises, `set_host` routing, `entry-only` before registration raises | accessors alias R today | yes | Python unit |
| T-D6b | construction-site guard: no program evaluated outside the helper | raw `make_global_env` sites | n/a | Python unit |
| T-D6c | sinks/debug state/test list read on R/R/E under distinct E | `env.values` on E falls back to process streams; hooks on E only | yes | Python unit |
| T-D6d | MCP: prune R before E; E empty; denied names undefined; allowed run unchanged | prune of empty E | yes | Python unit (security) |
| T-D6e | #1221 wrong-accessor matrix, one test per boundary and accessor | stub-only today | yes | Python unit |

## Issues

- #1220: acceptance criteria revised per §16.5 (comment/body linked to the PR).
- #1221: confirmed to cover CLI `main`, native discovery, serve, `:env`, debugger,
  reflection/tooling and MCP pruning, collisions and forbidden visibility; §16.6
  adds the non-aliased fixture and wrong-accessor requirement. Body unchanged.
- Both stay open under #1067; neither is closed by this phase.

## Not yet done (requires approval, outside this phase)

Open the P2 tracking issue and the fallback-removal issue (contract §11.5); record
maintainer approval of §16 on #1067. Documentation obligations for each landing
slice: GENIA_STATE.md (net-small; margin about 135 words), RULES §8.2/§8.3, REPL
README, README if visible, host-interop, book eval chapter, composability matrix
test, semantic facts, MCP language profile impact answer, code-documentation
contract for changed bindings.
