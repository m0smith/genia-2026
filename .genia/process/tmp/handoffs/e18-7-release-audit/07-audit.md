# E18-7 — R18 Release-wide Skeptical Audit

ISSUE: #797
EPIC: #789
BRANCH: `issue-797-r18-skeptical-audit`
BASE: `main` @ `10b4e14`

Audited on the assumption that something is wrong until evidence proves
otherwise. The implementers' own expectations — including those recorded in the
six prior slice audits — are not treated as evidence.

---

## 1. VERDICT

**PASS.**

---

## 2. THE THREE DECISIVE CHECKS

Most of this audit re-verified claims. Three checks were designed to *find*
problems rather than confirm absence, and are reported first because they are the
ones that could have failed.

### 2.1 Host leakage — the unclassified terminal

The R18 relation ends in an unclassified terminal that compares unknown host
objects by identity. Every prior audit recorded the same open worry: identity is
a safe answer, but it could silently hide a real Genia value that was never
classified. Reading the code cannot settle this, because the question is which
values *actually arrive* there.

The terminal was therefore instrumented and the entire suite re-run:

- **4202 pytest tests** plus **668 shared spec cases**
- terminal reached **4 times**, all by `_HostObjectClaimingEquality`

That class is the deliberate fixture in `test_r18_structural_numeric_equality_791.py`
whose whole purpose is to prove the terminal never consults host `__eq__`. So the
only values reaching the terminal are the ones placed there on purpose to test it.

**No value reachable from Genia source lands in the unclassified terminal.** The
instrumentation was removed and the tree verified clean.

### 2.2 Protected-data non-interference

Treated as a security review. 29 observables were probed adversarially, each
comparing an **equal-payload** carrier pair against a **different-payload** pair;
any observable able to distinguish them is an oracle regardless of what it
returns:

equality and inequality through eleven container shapes (bare, list, deep list,
Pair head, Pair tail, `some`, `some` context, `err` context, map value, map in
list, nested Outcome/map/list); host `__eq__`; `display`; `debug_repr`; hashing;
map-key rejection text; canonical-key rejection text; Sheet column-name rejection
text; `json_encode`; and error text from four arbitrary misuse expressions.

**No observable can distinguish the pairs, and the payload sentinel appears in no
output or message.** Carriers remain unhashable, so a host set or dict cannot
become an oracle either.

### 2.3 Documented legal-key family versus implementation

The documented family was checked against `canonical_map_key` across 26 value
families: all **9** documented-legal families are accepted, all **17**
documented-illegal families are rejected. The documentation describes the
implementation exactly — neither wider nor narrower.

---

## 3. AUDITED AREAS

### Approved contract

`docs/design/r18-portable-value-equality-contract.md` was re-read against the
landed behavior. Every family, the numeric matrix, purity, map equality, the
legal-key relation, surface reconciliation, and the protected boundary are
implemented as approved. No approved decision was quietly altered; the one
contract amendment (#794's Sheet column-name legality) is recorded in writing
with its justification, and is a narrowing forced by the governing rule rather
than a design change.

### Implementation paths

`src/` changes across the whole release are six files: `equality.py` (new),
`evaluator.py`, `values.py`, `pattern_match.py`, `builtins.py`, `sheet.py`.
`hosts/` and `spec/manifest.json` are untouched. `parser.py`, `ir.py`,
`lowering.py`, `ast_nodes.py`, and `optimizer.py` are untouched, confirming the
no-Core-IR-change claim independently of the documentation that asserts it.

No new `env.set` line was added to `builtins.py` across the release, confirming
no new public builtin.

### Numeric edge cases

18 adversarial cases beyond the contract matrix, all correct: `2**53` and
`2**53+1` against the same float; `10**400` against `inf` and `-inf`; integer `0`
against `-0.0`; `True` against `1.0`; `False` against `-0.0`; subnormal `5e-324`
against itself and against `0.0`; `int(1e308)` against `1e308`; booleans inside
lists and inside canonical keys; NaN nested in a list.

The int/float bridge converts the float upward and never narrows an
arbitrary-precision integer, which is what makes the `2**53+1` and `10**400`
cases come out right.

### Map equality, key equivalence, legal-key rejection

Verified: mapping equality independent of insertion history; key identity equal
to `==`; `true`/`1` and `false`/`0` distinct; `1`/`1.0` and `0.0`/`-0.0`
identical; rejection of NaN and nested NaN on **every** map operation rather than
only insertion.

### Identity-bearing behavior

Verified identity-only comparison with no dereference, invocation, advance, or
state inspection, including that `ModuleValue`'s host dataclass equality — which
compares its whole export table — is overridden.

### Opaque-token design boundary

No token value, token-domain declaration, minting API, syntax, storage, or
`Revision` exists in `src/`. No comparator, protocol, registry, or dispatch
mechanism was added anywhere; every textual match for "comparator" in
`equality.py` is a comment asserting its absence. The family is exercised only by
a test-only fixture, including a hostile fixture offering its own `__eq__` that
the engine correctly ignores.

The absence of opaque-token shared specs was re-confirmed as **required**, not
missing: R18 exposes no way to mint or observe a token from Genia source, so a
shared case would have to introduce the public surface the approved contract
excludes.

### Literal patterns, duplicate bindings, `assert_eq`, representations, Outcomes, Sheets, callable/runtime values

All route through the one relation, verified by the cross-surface agreement case
that compares the same operands through `==`, literal patterns, duplicate
bindings, and the meta-circular evaluator and requires identical rows.

### Documentation truth

`GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`,
`AGENTS.md`, both roadmap surfaces, the releases index, `HOST_PORTING_GUIDE.md`,
the R17 and R18 release pages, and the R18 design record were cross-checked
against each other and against the runtime. The R18 release page's two executable
examples were run, not transcribed. No document over-claims, and the five
non-claims (no C++ host, no overloadable `==`, no token surface, no `Revision`,
map order unchanged) appear in both the final authority and the release page.

### R17 non-regression

Arbitrary-precision integer arithmetic and every ordered-map rule verified
unchanged, directly and through the R17 shared cases.

### R16 conformance integration

All 24 R18 cases pass through the R16 generic host protocol with zero reported
`unsupported`. The full-suite `unsupported` count stayed at 18 across the release,
confirming no R18 case fell into the unexpressible-fixture bucket.

### R20 / open-functions boundary

R18 added no dispatch, overload, registration, or extension mechanism. `==`
remains non-overloadable, and the opaque-token family is explicitly closed to
comparator extension while open to domain extension — which is what preserves the
boundary R20 will later work within.

### Future C++ implementability

A host can implement conforming equality from the written contract plus the 24
shared cases without reading Python source. The cases are constructed to detect
the three partial implementations most likely in practice: reusing host `==`,
reusing a host hash map's key rules, and implementing `==` while leaving patterns
and assertions on host equality. The one host-specific element — testing booleans
before integers — is a defence against a Python accident, and the rule it
implements is written host-neutrally. `HOST_PORTING_GUIDE.md` now states the trap
directly.

---

## 4. FINDINGS

**No defects found.** No source change was required by this audit.

Prior-slice obligations, all discharged:

| Obligation | From | Status |
|---|---|---|
| no semantic site decides map sameness with host `==` | #792 | discharged by #794's post-change sweep; re-confirmed |
| no source-reachable value reaches the unclassified terminal | #791/#793 | **discharged by §2.1** |
| a future structural Genia value must not be callable | #793 | re-verified: no structural kind is callable |
| no runtime class has a side-effecting `__getattr__` | #793 | re-verified: none |
| fix `sheet.py::_freeze_column_name` | #792 | fixed in #794 |
| flip release status lines after PASS | #796 | done in this issue |

---

## 5. VALIDATION

- full regression `-m "not loopback"`: **2 failed / 4202 passed**
- `-m loopback`: 26 passed
- shared spec suite: `total=668 passed=668 failed=0 invalid=0`
- documentation + style: 225 passed
- `mkdocs build --strict`: built
- `ruff check .`: clean

The 2 failures are `tests/unit/test_native_test_runner.py`'s unreadable-file
cases. They were measured on `main` at `5c00e76` **before any R18 work began**
and are unchanged: this environment runs as root, so `chmod 000` does not
restrict access. They are environmental, pre-date the release, and are not
dismissed as unrelated without that proof.

---

## 6. VERDICT

**PASS.** R18 may be recorded complete.
