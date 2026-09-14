# Issue #855 Preflight — E21-3 R21 Cross-Surface Conformance and Compatibility Hardening

Status: process artifact for issue #855 (E21-3). Not a source-of-truth
document; `GENIA_STATE.md` remains final authority. Records the preflight
review required by `docs/process/run-change.md` before the contract phase,
including an explicit codebase audit sweep since this is the ticket's
primary charter.

## Scope

Prove the merged E21-1 (#853) / E21-2 (#854) source/Core-IR boundary across
shared host-neutral evidence, and repair only compatibility defects
strictly inside that boundary. Hard stop rule: any defect requiring R22/R23
semantics must be recorded as a dependency, not repaired here.

## Audit sweep performed during preflight

Exhaustive grep across `src/genia/*.py`, `hosts/python/*.py`, and
`tools/spec_runner/*.py` for every remaining `IrLiteral` construction/
consumption site and every `float(` call reachable from numeric-literal
handling:

- `src/genia/evaluator.py` (2 sites), `src/genia/optimizer.py` (1 site),
  `src/genia/lowering.py` (1 construction site): all already updated by
  #854 to handle the tagged payload correctly (verified by #854's own
  audit). No remaining untagged-literal assumption found.
- `hosts/python/ir_normalize.py`: serializes `IrLiteral.value` as-is
  (dict or scalar) with no numeric-specific branching — already correct,
  no host binary-float construction, no change needed.
- `hosts/python/parse_adapter.py`: projects AST `Number.value` (the
  unchanged legacy int/float, not the Core IR payload) for the `parse`
  spec category — correctly out of scope for this ticket, since E21-1/
  E21-2 only retagged the *lowered Core IR* payload, not the AST
  projection used by parse-category specs.
- `hosts/python/protocol_adapter.py`, `hosts/python/exec_eval.py`: no
  `IrLiteral`/`float(` references at all — these delegate to the same
  in-process evaluator/lowering code path already covered above; no
  separate reimplementation exists to drift.
- `tools/spec_runner/*.py` (comparator, executor, host_executor,
  reporter, evidence): no numeric-specific special-casing; dict-vs-dict
  comparison already works generically for the tagged payload (proven by
  every R21 `ir`-category spec passing).

Conclusion: **no remaining defect found.** #854's implementation already
correctly threads the tagged payload through every consumer that exists in
the current codebase.

## `spec/manifest.json` capability/version truthfulness check

- R21 introduces no new required or optional capability; numeric literal
  lowering already lives entirely inside the existing `parser`,
  `ast_lowering`, and `core_ir_eval` required capabilities. No manifest
  capability-list change is truthful or necessary.
- `core_ir_version: "0.1.0"`: no test, doc, or process rule in this
  repository defines when this field must increment (grep confirms it has
  no reader anywhere in `tools/`, `tests/`, or `docs/` other than the
  manifest itself). Bumping it without a defined consumer or semantic
  would be inventing process, not truthfully recording one — left
  unchanged. This finding itself is the truthful manifest-handling
  verification the ticket asks for.

## Planned positive contribution

Since the audit found zero code defects, this ticket's positive
contribution is durable conformance *evidence*, mirroring the established
R18 precedent (`tests/spec/test_r18_conformance_protocol_evidence_795.py`):
a new `tests/spec/test_r21_conformance_protocol_evidence_855.py` that
explicitly asserts every R21-named spec (not just an aggregate pass count)
is present, executes to `pass` (never `unsupported`/`crash`/`timeout`) both
in-process and through the R16 subprocess protocol adapter. This closes the
gap between "the aggregate suite total happens to include R21 cases" and
"R21 conformance is specifically, durably proven" the same way R18's E18-5
did.

## PORTABILITY ANALYSIS (required, all seven fields)

1. **What portable boundary does this change touch?** None functionally —
   this ticket adds proving evidence over the already-landed E21-1/E21-2
   boundary; no source/parser/lowering/Core-IR code changes are made.

2. **Does this change alter the minimal portable Core IR node family?**
   No.

3. **Does this change require a host-native binary float?** No — no new
   production code is added; the new test only asserts existing pass/fail
   outcomes.

4. **Does this change require another host implementation to consult
   Python-specific behavior?** No — the new test itself proves the
   opposite: that the already-shared evidence is reproducible over the
   generic subprocess protocol.

5. **Does this change affect R16/R17/R18/R19/R20?** No behavioral change;
   it reuses R16's existing generic protocol/host-executor machinery
   exactly as R18's E18-5 already does, with zero change to that
   machinery itself.

6. **Is any part of this change host-local-only?** The new test file is
   ordinary Python reference-host test infrastructure, consistent with
   every other conformance-evidence test in `tests/spec/`.

7. **What new portable evidence must exist?** The new test itself *is*
   the durable evidence artifact — a named, always-run assertion that
   every R21 spec case passes through both execution paths, rather than
   evidence that could silently erode if a future case were marked
   `requires: [...]` an unsupported capability or renamed out of the
   aggregate count.

## Conclusion

Preflight, including the audit sweep, is complete. No contract change,
compatibility repair, or R22/R23 dependency was found necessary. Proceeding
to contract reconciliation and then straight to the conformance-evidence
test (no separate failing-implementation cycle is needed, since no defect
exists to fix — this is recorded explicitly rather than skipped, per
`docs/process/run-change.md`'s guidance to preserve process boundaries with
a named empty-phase commit when a phase correctly concludes no repository
content needs alteration).
