# #1250 registration preparation / validation hardening

PROPOSED_NOT_APPROVED. Author Codex. Starting head d3bf5b73; same PR #1318 branch
and base 9f96c6d9. Preflight: issue #1250 comment 6744494522; authorization
6744296276; independent build-correction approval review 5828336713 only.

Scope: close negative packaging/evidence tests, enforce future approval evidence,
prepare separate registration/activation patch, bounded local packaging tests.
No activation, acceptance, CI, semantic/oracle/host change, merge or closure.
Read latest AGENTS (e913e9d0), material STATE/RULES/REPL README/README, full two
reviews, ledger, backend/frontend/runner/tests and maintained-code/process rules.

Portability: Python-only tooling; C++ unaffected; portable contract unchanged;
Core IR unchanged; capabilities unchanged; shared semantic specs inapplicable
(host-local packaging/evidence tests); no host gap. MCP knowledge unchanged.
Maturity process-only. Core invariants: unchanged evidence/sentinel, strict
runtime/build freeze and artifact hashes, one input set for both frozen subjects,
real editable installation, fail-closed metadata and approval qualification.
No root semantic-doc changes needed. Preserve explicit authority/minimalism;
no new language semantics; supports authorized #1250/R29 prerequisite tooling.

Design: retain existing packaging path. Harden RECORD parsing/content validation
before modification and verify installed hashes/sizes afterwards. Add deterministic
injection tests at actual backend/frontend/provision wrapper boundaries and a
small real local-wheel hash-rejection test. Real successful packaging stays a
bounded preparation integration, never acceptance.

Future approval boundary: an explicit read-only validator requires a complete,
manifest-verified, exact-source, exact-proposal cold-cache evidence bundle with
successful non-skipped integration outcomes for both registered subjects, runtime
and build identities, editable RECORD validation, fresh private environments/cache,
retained commands/output and provenance. Old local evidence cannot silently
qualify future changed source or a different environment class. Normal unit runs
may omit integration; explicit approval validation must reject omissions.
Do not invoke the future approval-validation CLI in this task; unit-test the
validator and collect local preparation evidence only.

Registration JSON and an exact future activation patch stay separate/inactive.
The patch must wire the mandatory evidence validator before provisioning, using
an explicitly supplied evidence bundle, approved manifest digest, environment
class and exact provisioning-source identity. No active registration or sentinel
changes now. No proposal/status flag alone can activate execution. Any workflow
wiring remains separately reviewed in that future patch, not applied here.

Risks: bespoke metadata frontend and self-attested local evidence; hashes do not
prove an independent/hosted run. Reviewer must anchor bundle digest and intended
environment class externally. Rollback these preparation commits only, leaving
prior draft blocked and historical/additive evidence intact. Independent review
pending; GO preparation only, NO-GO activation. Test/implementation/docs phases
are explicitly authorized by the user; independent review is the stop gate.
