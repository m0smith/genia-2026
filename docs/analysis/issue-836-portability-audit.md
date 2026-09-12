# Issue #836 — Skeptical Portability Audit

Verdict: **PASS**

Status: conformance-infrastructure audit; no language semantics changed and
`GENIA_STATE.md` remains unchanged.

## Evidence reviewed

- Eight new logical multi-file cases pass through the Python in-process path.
- The identical eight requests pass through the R16 Python subprocess adapter
  when both `open_functions` and `multi_file_eval` are `supported` (`pass=8`,
  all other outcomes zero).
- With either required capability absent or declared `unsupported`, all eight are classified
  `unsupported` before adapter invocation (`unsupported=8`, `pass=0`).
- The full Python subprocess parity test reports the traced count change from
  `695/677/18` to `703 total, 685 pass, 18 unsupported`, with zero fail,
  protocol error, crash, timeout, or invalid cases. The delta is exactly the
  eight new expressible cases; the existing 18 injected/debug fixtures remain
  unsupported.
- Focused loader, protocol, host-executor, Python-adapter, R20 shared/unit, and
  documentation tests pass after reconciliation (235 tests).

## Skeptical checks

- **Filesystem assumptions:** YAML contains logical relative paths and source
  only. Python materializes these privately; no temporary path is request or
  expected-result data.
- **Path leakage/traversal:** absolute, drive-like, backslash, empty-component,
  `.`/`..`, non-`.genia`, and duplicate paths are rejected before execution.
  New normalized diagnostics contain module identities, not temporary paths.
- **Ordering:** loader sorting affects only canonical transport. Import and
  contribution selection order remain source statements and have explicit
  order-independence evidence.
- **Dual path:** the in-process and external-host adapters consume the same
  normalized entry source/files; the protocol round-trip test compares the
  serialized fixture exactly.
- **Capability honesty:** every new case requires `open_functions`; unmet
  cases separately require `multi_file_eval`; unmet requirements are
  unsupported before request construction and never pass. Therefore an older
  protocol-v1 host never receives the new field merely because it implements
  R20 semantics.
- **Semantic isolation:** changes are confined to shared-spec loading,
  transport, Python fixture realization, evidence, tests, and docs. Parser,
  Core IR, evaluator, callable dispatch, and module export semantics are
  untouched.
- **R20 coverage:** disjoint base/contributions, import non-selection, explicit
  selection, both order independences, alias duplication, incompatible target,
  overlap ambiguity, alias/interface identity, lexical visibility, and consumer
  non-transitivity all have shared evidence. Exact error stderr is pinned.
- **Diagnostics:** compared errors are existing normalized Genia messages, not
  raw Python exception or filesystem text.
- **Documentation:** it states Python remains the only production host and R21
  remains blocked; it does not claim C++ readiness or filesystem semantics.

## Environment note

The mandated `uv run` could not download PyYAML because outbound package access
was unavailable. The already-provisioned Python environment ran the same tests
with `PYTHONPATH=src:.`. `pytest-xdist` was absent there, so full parallel
regression could not be completed; this environment limitation does not alter
the focused and full shared-path evidence above.

## Protocol reconciliation re-audit

The original audit incorrectly treated `open_functions` as sufficient to send
the new field even though the approved R16 v1 eval input was closed. The fix is
an explicitly documented optional v1 extension with an independent
`multi_file_eval` opt-in. Unknown input fields remain rejectable; no general
ignore rule was introduced. Capability selection now precedes request
construction, and focused tests prove that a host claiming only
`open_functions` receives `UNSUPPORTED` without invocation. This preserves old
v1 hosts, keeps all eight Python dual-path cases applicable, and changes no R20
language behavior. Re-audit verdict remains **PASS**.
