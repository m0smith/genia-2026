# E18-3 Identity, Opaque Token, and Protected Equality — Pre-flight

ISSUE: #793
PARENT: #789
BLOCKED BY: #790 (merged), #791 (merged, PR #806); builds on #792 (merged, PR #807)
STATUS: pre-flight

---

## 0. BRANCH

Branch slug: `identity-token-protected-equality`
Expected branch: `issue-793-identity-token-protected-equality`
Base: `main` @ `7552a98`

---

## 1. SCOPE LOCK

### Includes

- identity equality for the approved identity-bearing runtime families, with no
  traversal of referenced state or configuration
- removal of the protected-payload-comparing host equality on `GeniaProtected`,
  so no internal host comparison can remain an oracle
- protected-carrier equality by carrier identity only, and protected
  non-interference across equality, inequality, nested structural comparison,
  containers, keys, and diagnostics
- the internal opaque semantic-token equality family: hidden domain identity,
  provenance identity, and semantic identity, compared as data with no issuer
  call and no comparator callback
- removal of the remaining E18-1 transitional branch
- shared and focused failing evidence before implementation

### Excludes

- any public token-domain syntax, token minting API, or public token value
- storage or `Revision` implementation
- making opaque tokens legal map keys (they stay non-keyable)
- user-defined equality callbacks or comparator registration
- `assert_eq`, literal patterns, duplicate bindings — #794
- C++ host

---

## 2. SOURCE OF TRUTH

Authoritative: `GENIA_STATE.md`, `GENIA_RULES.md`, `GENIA_REPL_README.md`,
`README.md`, `AGENTS.md`.

Additional: `docs/design/r18-portable-value-equality-contract.md` sections
"Identity-bearing runtime values", "Opaque semantic tokens", "Protected
carriers", "Protected-value non-interference", "Implementation design"; E18-0
design §3.5–§3.7; merged E18-1/E18-2 handoffs.

Note: `GENIA_STATE.md` currently states that "protected equality includes
provider identity, purpose, and carried-value equality". That is an accurate
description of today's behavior and becomes false when this issue lands, so this
issue must update it.

---

## 3. FEATURE MATURITY

Stage: [x] Partial (E18-3 slice). This slice is also a **security boundary**, not
only an equality feature.

---

## 3a. Portability Analysis

All seven fields resolved; no `TBD`.

1. **Portability zone** — *language semantics (portable contract)*, with a
   security guarantee attached. Which values compare by identity, and the rule
   that protected payloads are never compared, must hold on every host.

2. **Core IR impact** — `none`. No new or changed `Ir*` node family; no parser,
   AST, or lowering change.

3. **Capability categories affected** — `none`. The point of this slice is that
   equality contacts **no** capability: no issuer, provider, or authority is
   consulted, and no declassification occurs. `spec/manifest.json` is unchanged.

4. **Shared spec impact** — new `spec/eval/` cases proving identity semantics and
   protected non-interference from ordinary source. Opaque-token architecture is
   internal and is covered by focused tests, not by shared specs, because R18
   deliberately exposes no way to mint a token from source.

5. **Python reference host impact** — `src/genia/equality.py` gains identity,
   protected, and opaque-token branches and loses the last transitional branch;
   `src/genia/values.py` loses `GeniaProtected.__eq__`. Observable changes:
   independently acquired protected carriers holding equal payloads now compare
   unequal; identity-bearing values compare by identity rather than by host
   dataclass field comparison.

6. **Host adapter impact** — `none`.

7. **Future host impact** — significant. A host must not let its own object
   equality decide these families, and must never implement protected equality by
   comparing payloads. The written contract plus the new shared cases state this
   without reference to Python. The opaque-token family is specified so a future
   built-in **or user-defined** token domain can supply three immutable
   identities at mint time without ever registering comparator code — which is
   what keeps `==` non-overloadable while leaving the family extensible. No C++
   implementation is added.

---

## 4. CONTRACT vs IMPLEMENTATION

### Measured defect: `==` is a protected-payload oracle today

Measured on this base, from ordinary Genia source, with **no** declassification
authority:

```genia
provider = config_provider([{kind: quote(values),
  values: {A: "SAME_SECRET", B: "SAME_SECRET", C: "OTHER"}}]) |> unwrap_or(none)
a1 = secret_get(provider, "A", quote(use))
b  = secret_get(provider, "B", quote(use))
c  = secret_get(provider, "C", quote(use))

a1 == b        # true   <-- discloses that A and B hold the same secret
a1 == c        # false  <-- discloses that A and C differ
[a1] == [b]    # true   <-- leaks through containers
some(a1) == some(b)   # true
```

`GeniaProtected.__eq__` compares provider identity, purpose, **and the carried
payload**. So ordinary `==` lets unprivileged code test secret equality, and by
extension probe secrets against candidate values wherever a protected carrier can
be constructed from a guess. This is a security defect, not merely a portability
one.

Required after this slice: only carrier identity is observable. `a1 == a1` is
true; `a1 == b`, `a1 == c`, and even a second independent acquisition of the
*same* key are all false.

### Other current behavior

- identity-bearing values reach E18-1's transitional branch and are therefore
  still decided by host equality. For plain classes that is already identity, but
  `ModuleValue`, `GeniaPythonHandle`, `GeniaNamedPattern`, `GeniaFunction`, and
  `GeniaFunctionGroup` are host dataclasses whose generated equality compares
  fields — including, for `ModuleValue`, its whole export table.
- no opaque semantic token type exists, so the family has no implementation at
  all.

---

## 5. TEST STRATEGY

Core invariants: identity-only comparison with no state traversal; protected
equality by carrier identity only; protected payloads never compared and never
disclosed through any observable; opaque-token equality by three pre-established
identities with no issuer contact; equality purity preserved.

Security testing is adversarial, per the R18 contract's non-interference
section: attempt to derive payload information through direct equality,
inequality, nested structural comparison, Lists, Pairs, Outcomes, maps as values,
map keys, display/debug rendering, JSON encoding, and rejection diagnostics.

Uses the established sentinel-proof pattern from
`tests/unit/test_protected_configuration.py`.

Baseline: `main` @ `7552a98` — `-m "not loopback"` 2 failed / 4108 passed
(pre-existing root/`chmod 000` cases), `-m loopback` 26 passed, shared specs
657/657.

---

## 6. COMPLEXITY CHECK

[x] Revealing structure

Removing a payload-comparing host `__eq__` and naming the identity families
removes hidden behavior. The opaque-token adapter is the minimum needed to make
the fourth contract family real; it adds no public surface.

---

## 7. CROSS-FILE IMPACT

`src/genia/equality.py`, `src/genia/values.py`, new shared specs, new focused
tests, `GENIA_STATE.md` (protected-equality line and the E18-1/E18-2 deferred
list).

Risk of drift: [x] High — runtime identity plus a security boundary.

---

## 8. DOC DISTILLATION CHECK

Creates process artifacts? YES. Adds `docs/design`/`docs/architecture` files? NO.
Doc drift risk: [x] Medium — the protected-equality line in `GENIA_STATE.md` must
be corrected in this issue.

---

## 9. PHILOSOPHY CHECK

- preserves minimalism? YES — no public surface
- avoids hidden behavior? YES — removes a hidden payload oracle
- keeps semantics out of host? YES
- aligns with pattern-matching-first? YES

---

## KILLER WORKFLOW ALIGNMENT

[x] Indirectly. Validated pipelines carry credentials and protected
configuration alongside records. An equality relation that leaks payload
equality, or that compares a module's whole export table, undermines both the
security and the predictability of those pipelines.

---

## 10. PROMPT PLAN

Preflight → Contract → Design → Test (failing) → Implementation → Docs → Audit →
Distillation.

---

## FINAL GO / NO-GO

**YES.** Blockers merged.
