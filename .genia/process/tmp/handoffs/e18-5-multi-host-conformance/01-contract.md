# E18-5 Multi-host Equality Conformance Hardening — Contract

ISSUE: #795
STATUS: contract

Narrows the approved parent contract to the E18-5 scope. Behavior only.

---

## 1. PURPOSE

Make the R18 equality contract independently verifiable. After this ticket, a
host that has never read Python source can determine whether it conforms, for
every equality family reachable from Genia source.

---

## 2. THE DEFINING CONSTRAINT

**This ticket defines no behavior.** Everything it asserts is already required by
the approved R18 contract and already implemented by E18-1 through E18-4.

Consequently:

- every case added here must pass on the base commit, before any source change
- a failing case is evidence of an implementation defect, and the response is to
  fix the smallest necessary defect and document it — never to weaken the case or
  amend the approved contract

---

## 3. REQUIRED COVERAGE

Shared, host-neutral cases must exist for every R18 equality family that is
reachable from Genia source:

| Family | Must be covered by shared cases |
|---|---|
| exact numeric | boolean/number separation, int↔float bridge, signed zero, infinities, NaN |
| structural | kind separation, recursive contents, represented values, Pairs, Sheets |
| map equality and keys | mapping equality, key equivalence, every map operation, illegal-key rejection |
| identity-bearing | identity not contents, no dereference |
| protected | carrier identity, non-interference through containers, map values, and patterns |
| pattern binding | literal patterns and duplicate bindings agreeing with `==` |
| assertion | `assert_eq` succeeding and failing exactly as `==` decides |

### Opaque semantic tokens

Deliberately **not** covered by shared cases, and this is a requirement rather
than an omission: R18 exposes no way to mint or observe a token from Genia
source, so a shared case would have to introduce the public token surface the
approved contract excludes.

A conforming host is not expected to demonstrate token equality in R18. The
family is specified in prose for a future host to implement when a token type
exists.

---

## 4. EVIDENCE THROUGH THE GENERIC HOST PROTOCOL

Portable evidence that has only ever run in-process is an untested claim about
the transport. The R18 cases must therefore also be shown to pass through the
**R16 generic host protocol** path — subprocess execution, JSON request/response
envelopes, and capability negotiation.

### Unsupported must never count as passing

The evidence must distinguish "the host answered correctly" from "the host
declined the case". Specifically:

- every R18 case must be **executed** through the protocol path, not reported
  `unsupported`
- a run in which R18 cases were skipped must not be indistinguishable from a run
  in which they passed
- the outcome taxonomy stays exactly as R16 defined it; `unsupported`,
  `protocol_error`, `crash`, `timeout`, and `invalid` are never folded into
  `passed`

R18 cases declare no `requires:` capability list, so they belong to the base
required-capability set that every conforming host implements by definition.

---

## 5. INVARIANTS

1. No equality semantics are defined, changed, or extended by this ticket.
2. Every family in §3 reachable from source has shared coverage.
3. The opaque-token family has no shared coverage, by design.
4. R18 cases pass through the generic host protocol path, not only in-process.
5. R18 cases are executed rather than reported `unsupported`.
6. No outcome other than `pass` is counted as passing.
7. No new capability, spec category, envelope field, or protocol change.
8. No Core IR, parser, or public language surface change.
9. Any source change made under this ticket is a documented defect fix, minimal
   in scope, and does not alter the approved contract.

---

## 6. NON-GOALS

New equality semantics; C++ host implementation; new capabilities unrelated to
equality; changes to the R16 protocol, capability vocabulary, or evidence schema;
token syntax or minting; release truth (#796); release audit (#797).

---

## 7. DOC NOTES

If no defect is found, `GENIA_STATE.md` needs no behavioral change from this
ticket; conformance breadth is release-level wording owned by #796. Mark as
**partial** until E18-6.

---

## 8. FINAL CHECK

Precise and testable; no implementation detail; no scope expansion; consistent
with `GENIA_STATE.md` as final authority.
