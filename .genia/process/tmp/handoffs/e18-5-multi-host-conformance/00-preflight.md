# E18-5 Multi-host Equality Conformance Hardening — Pre-flight

ISSUE: #795
PARENT: #789
BLOCKED BY: #791, #792, #793, #794 — all merged (PRs #806, #807, #808, #809)
STATUS: pre-flight

---

## 0. BRANCH

Branch slug: `multi-host-equality-conformance`
Expected branch: `issue-795-multi-host-equality-conformance`
Base: `main` @ `bd24214`

---

## 1. SCOPE LOCK — evidence only

This ticket adds **no equality semantics**. Every case it adds must pass on the
current `main` before any source change, because the behavior is already
implemented by #791–#794. If a case fails, that is a semantic bug to investigate,
not a licence to change the contract.

### Includes

- shared cross-host cases covering every R18 family that is reachable from Genia
  source, at representative breadth
- regression evidence that the R18 cases pass through the **R16 generic host
  protocol** path, not only the in-process path
- explicit verification that `unsupported` is never counted as passing

### Excludes

- new equality semantics of any kind
- C++ host implementation
- new public capabilities unrelated to equality
- changes to the R16 protocol, capability vocabulary, or evidence schema
- authoritative release truth (#796) and the release audit (#797)

### If hardening reveals a genuine defect

Per the issue: fix the smallest necessary implementation defect under this issue
and document why. Do not silently alter the approved contract.

---

## 2. COVERAGE ASSESSMENT (performed before scoping)

R18 currently has 20 shared cases (17 `eval`, 3 `error`) plus 4 from #794.
Assessed per family named in the issue:

| Family | Current shared coverage | Gap |
|---|---|---|
| structural | boolean/number separation, kind separation, structural contents, NaN through containers | represented values, Pairs, Sheets not covered from source |
| numeric | exact bridge, signed zero, infinities, NaN | none |
| map/key | map equality, key equivalence, every-operation, 3 rejection cases | protected as a map **value** not covered |
| identity | identity-bearing equality | none |
| opaque token | **none** | see §3 — deliberate |
| protected | carrier identity, non-interference through containers | not covered through the *pattern* surface |
| pattern binding | cross-surface agreement | protected through duplicate bindings not covered |
| assertion | assert_eq one-relation, cross-kind rejection | none |

Measured on this base: represented values, Pairs, Sheets, protected-as-map-value,
and protected-through-duplicate-binding **all already behave correctly**. They are
unpinned, not broken. Pinning them is exactly this ticket's job — a future host
could plausibly get represented-facet identity or Pair-vs-List separation wrong,
and nothing currently detects that.

---

## 3. THE OPAQUE-TOKEN GAP IS DELIBERATE, NOT AN OMISSION

R18 exposes no way to mint or observe an opaque semantic token from Genia source.
A shared spec would therefore have to invent the public token surface that the
approved contract explicitly excludes.

This was already recorded by #793's audit and distillation. This ticket restates
it so the absence is not mistaken for a coverage gap by #797 or by a future host
implementer, and so nobody "fixes" it by adding token syntax.

The family remains covered by focused tests against the internal adapter, and
specified in prose for a future host to implement when a token type exists.

---

## 4. PORTABILITY ANALYSIS

All seven fields resolved; no `TBD`.

1. **Portability zone** — *shared conformance evidence*. This ticket adds no
   behavior; it makes existing portable behavior detectable by an external host.

2. **Core IR impact** — `none`. No `Ir*` node family added or changed; no source
   change to parser, AST, lowering, or evaluator is planned at all.

3. **Capability categories affected** — `none`. The added cases declare no
   `requires:`, so they belong to the base required-capability set every
   conforming host implements by definition. No capability is added to
   `spec/manifest.json` or `docs/host-interop/capabilities.md`.

4. **Shared spec impact** — the substance of this ticket: new `spec/eval/` cases
   for the gaps in §2. No new category, envelope field, or runner behavior.

5. **Python reference host impact** — expected to be **none**. The only files
   expected to change are `spec/`, `tests/`, and the protocol parity case count.
   Any source change would mean hardening found a real defect and must be
   justified in writing.

6. **Host adapter impact** — `none`. `hosts/python/adapter.py` and
   `protocol_adapter.py` are unchanged; the R16 protocol surface is untouched.

7. **Future host impact** — this is the ticket's whole purpose. After it, an
   independent host can consume the written R18 contract plus the shared cases
   and detect its own divergence in every source-reachable family, including the
   partial implementations most likely in practice: reusing host `==`, reusing a
   host hash map's key rules, or implementing `==` while leaving patterns and
   assertions on host equality.

---

## 5. TEST STRATEGY

Two kinds of evidence, deliberately distinct:

1. **Shared cases** — portable, host-neutral, consumed by any host.
2. **Protocol-path regression** — proof that the R18 cases pass through the R16
   generic host protocol (subprocess, JSON envelopes, capability negotiation),
   not only the in-process path. Without this, "portable evidence" is an
   untested claim about the transport.

The protocol-path check must also assert that R18 cases are **executed**, not
reported `unsupported`. A suite where every case is skipped would otherwise look
identical to a passing one — the exact failure mode the issue warns about.

Baseline: `main` @ `bd24214` — `-m "not loopback"` 2 failed / 4197 passed,
`-m loopback` 26 passed, shared specs 664/664, `ruff` clean.

---

## 6. COMPLEXITY CHECK

[x] Revealing structure — no new mechanism; it makes existing behavior
externally verifiable.

---

## 7. CROSS-FILE IMPACT

`spec/eval/*`, `tests/spec/*`, protocol parity case count, `GENIA_STATE.md` only
if a defect is found.

Risk of drift: [x] Low — evidence only.

---

## 8. DOC DISTILLATION CHECK

Creates process artifacts? YES. Adds design/architecture files? NO.
Doc drift risk: [x] Low.

---

## 9. PHILOSOPHY CHECK

- preserves minimalism? YES — no new surface
- avoids hidden behavior? YES — it exposes behavior to external verification
- keeps semantics out of host? YES
- aligns with pattern-matching-first? YES

---

## KILLER WORKFLOW ALIGNMENT

[x] Indirectly. Conformance evidence is what keeps validated-pipeline semantics
identical across hosts as Genia gains a second implementation.

---

## 10. PROMPT PLAN

Preflight → Contract → Design → Test (evidence) → Implementation (expected: none)
→ Docs → Audit → Distillation.

---

## FINAL GO / NO-GO

**YES.** All blockers merged.
