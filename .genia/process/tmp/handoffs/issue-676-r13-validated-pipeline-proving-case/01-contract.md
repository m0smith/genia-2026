# Contract — issue #676 R13 validated-pipeline proving case

## 1. Purpose

Prove, without new semantics, that the implemented R13 configuration surface composes with Genia's Outcome-aware validated-data-pipeline workflow and the existing R10 protected outbound boundary.

## 2. Scope

Included:
- One offline executable application composition.
- One conventional provider with deterministic overrides, explicit arguments, environment, and `.env` sources.
- Qualified server, database, and third-domain `PORT` lookups.
- Explicit integer conversion and existing callable Template validation.
- Mixed valid/absent/invalid records aggregated by existing validation helpers.
- One protected credential passed only through a matching injected authority to one injected outbound fixture.
- Shared, native, and Python reference-host proving observations.

Excluded: every new API or semantic rule; networking and real credentials; retry, repair, fallback, agents, ambient state, or lifecycle injection.

## 3. Behavior

The application explicitly constructs one standard provider snapshot. Source precedence and acquisition use unchanged R13 behavior. Qualified views map logical `PORT` names to distinct physical keys. Each selected string is explicitly converted and validated by existing positive valid-port callable Templates.

Existing record validation consumes mixed records and returns the exact `collect_validated` shape with ordered `clean` records and ordered structured `diagnostics`.

Secret lookup returns an opaque protected credential. Authorized dispatch accepts an injected authority and outbound callable, declassifies immediately as an argument to that boundary, and invokes it no more than once with validated ports, the exact credential payload, and clean records.

The top-level example returns safe observations only: validated qualified port Outcomes, clean values, diagnostics, protected display, and successful protected matching. It does not return or print physical secret keys or payloads.

## 4. Semantics

- All construction, views, conversions, Templates, validation, matching, and Outcome propagation retain their existing semantics.
- Distinct prefixes make identically named logical `PORT` settings unambiguous.
- Missing lookup propagates `none("config-missing")`; malformed integer parsing and Template mismatch propagate their exact existing Outcomes.
- An invalid/absent record becomes the exact existing ordered diagnostic and is not submitted as clean data.
- Dispatch occurs only when configuration, credential, record aggregation, and authorization reach their existing success forms.
- A matching authority reveals one protected layer, records one audit event, and permits one outbound attempt.
- Authority/provider or purpose mismatch fails closed before the outbound call.

## 5. Failure

Provider acquisition failures, missing/malformed configuration, Template mismatch, protected direct-host submission, authority mismatch, and audit failure preserve existing errors/Outcomes. They cause no retry, repair, fallback, second declassification, second outbound attempt, partial provider, or sensitive rendering.

## 6. Invariants

- No new public value, callable, error shape, capability, syntax, annotation, parser rule, or Core IR node exists.
- Provider sources snapshot once; later source mutation is invisible.
- Qualified physical keys remain distinct even when logical names match.
- Outbound attempts are zero on failure and at most one on success.
- Successful dispatch performs exactly one authorized declassification and one audit event.
- Secret key, payload, `.env` content/path sentinels, and raw host details do not appear in results, diagnostics, exceptions, audit observations, or ordinary rendering.

## 7. Examples

Minimal: `server("PORT")`, `database("PORT")`, and `metrics("PORT")` yield three independently converted/validated Outcomes.

Real: mixed records are validated and collected, then only clean records plus the three valid ports and one credential revealed at the authorized fixture boundary are submitted once.

## 8. Non-goals

No configuration schema, implicit coercion, new pipeline helper, new diagnostics, model/HTTP behavior, credential policy, declassification API, networking, or lifecycle/provider injection.

## 9. Documentation

`GENIA_STATE.md` must record E13-6 as a composition/conformance proof and retain Experimental maturity, Python-only implementation, Partial shared/multi-host conformance, and explicit exclusions.

## 10. Final check

The contract is precise, testable, host-independent except for explicitly injected Python fixture verification, within preflight scope, and consistent with the approved R13 contract.
