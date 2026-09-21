# Host Capability Taxonomy

Status: Architecture decision — planning only, non-authoritative. This document
does not add a capability or change implemented Genia behavior.
`GENIA_STATE.md` remains final authority.

## Decision

Classify a host capability on three independent dimensions. A registry entry,
host implementation, and program authority answer different questions; no one
label substitutes for the other two dimensions.

### Portability requirement

| Class | Meaning |
|---|---|
| **required** | Every conforming host for the applicable Genia surface realizes the Genia semantics. The host need not expose an equivalent operating-system primitive. |
| **optional** | Genia defines portable semantics, but a conforming host may report the capability unavailable or unsupported. |
| **host-specific** | The facility cannot honestly provide uniform portable semantics. Shell dialects, TTY facilities, and platform signal mechanisms are candidate examples, not claims of implementation. |

A future browser or WASM host, for example, could realize required Genia
`stdin` semantics without POSIX file descriptor 0. Portability specifies the
Genia observation, not the physical mechanism.

### Acquisition and authority

| Class | Meaning |
|---|---|
| **ambient** | The applicable Genia surface receives a required, low-risk facility without an explicit provider value. |
| **explicit provider/authority** | A host-variable, security-sensitive, restricted, or authority-bearing facility is supplied explicitly. |
| **internally mediated** | A host capability remains below a portable operation and has no public Genia value of its own. |

Implemented evidence validates the distinctions without changing it:

- `stdin`, `stdout`, and `stderr` remain ambient host-backed facilities.
  In particular, `stdin |> lines` remains a lazy, pull-based, single-use Flow;
  it is not converted into a provider object.
- configuration/secrets, model/retrieval providers, and HTTP authority show
  explicit provider or authority boundaries.
- the private Python-host `http.transport` capability shows internal mediation
  beneath `web.http_send`; a registry entry need not expose a provider object
  to ordinary source.

Therefore **host-backed does not imply explicit-provider**.

### Semantic surface

| Class | Meaning |
|---|---|
| **portable Genia semantics** | Hosts preserve one Genia-observable contract even when their mechanisms differ. |
| **provider-specific semantics** | The selected provider owns behavior that cannot be made uniform honestly. |
| **no public Genia surface** | The capability is private host substrate beneath another operation. |

Host backing does not make semantics host-specific. Conversely, a host support
declaration does not require a public capability value.

## Vocabulary

| Term | Question answered |
|---|---|
| **Capability name** | What semantic facility exists? |
| **Host support declaration** | Can this host implement it? |
| **Provider** | Which implementation or service has been supplied? |
| **Authority** | What protected or effectful operation is permitted? |
| **Operation** | What does the program request? |
| **Outcome** | What happened? |

These terms are related, not synonyms. R16's existing `supported` / `partial` /
`unsupported` declarations remain the sole host/conformance mechanism. They do
not grant program authority, and this taxonomy creates no second registry.

## Capability provisioning

Use **capability provisioning** for the policy step that turns available host
support into explicit program authority:

```text
host support declaration
        ↓
capability provisioning + policy
        ↓
explicit opaque program capability
        ↓
ordinary Genia operation
        ↓
Outcome
```

This is distinct from **execution realization**, which describes where and how
logical Genia computation runs. Provisioning does not imply a dependency-
injection framework, a global host object, `host.supports(...)`, or
`host.process(...)`.

## Planned application

The first planned application of the optional / explicit-provider / portable-
semantics category is external direct execution under `execution.process`.
See [External Process Execution Architecture](external-process-execution.md).
