# G1 evidence hygiene — iteration 2 (non-authoritative)

Codex; 2026-11-07 UTC. **G1 BLOCKED.** Implements only the bounded
[authorization](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6708635427)
and [G1 review](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6708311014)
of `8b62b58c28a5b0e90b4013788f08979bf5011cb1`. No acquisition was attempted.
This supplement qualifies historical assertions; original receipts and pins are
byte-preserved. Accepted frontend: `fd74a5830c76373d724bbd40a603ea85870f0aca`.

## Trust plan before any acquisition

Trust source is the already pinned official base platform manifest
`sha256:e8a38829209aea82774882e5157e1f7c3e8c8393ff53a697b3580896e57f345c`,
base Debian layer `sha256:f2be67225471500c788ce88c597eb5ea8336e912ad1ca4815650e0281afe2034`,
member `usr/share/keyrings/debian-archive-trixie-automatic.gpg`, supplied by
`debian-archive-keyring` **2025.1**. Use static tar member extraction only, never
execute or assemble a rootfs. The pinned registry base is the existing trust
assumption; this does not establish an independent Debian publisher attestation.
No live apt, keyserver, newly downloaded unverified key, or PATH-selected keyring.

Expected member SHA256:
`8dbd0029697f8c9b009eeb9a153c6536b62ca031fa0a5b4cec74e8d718fccef6`.
This hash and the following fingerprints were observed in the attached executor's
2025.1 package, **not yet independently extracted from the pinned layer**. Later,
separately authorized static acquisition must first verify the layer digest,
reject unsafe/duplicate member paths, extract this member, compare its hash and
fingerprints, and retain those receipts **before fetching snapshot metadata**.
Mismatch/absence STOPs for review; never silently substitute a keyring.

Accept only Debian Archive Automatic Signing Key (13/trixie), primary
`04B54C3CDCA79751B16BC6B5225629DF75B188BD`, signing subkey
`B8E5F13176D2A7A75220028078DBA3BC47EF2265`. Any different signer STOPs, even
if another key in a system keyring validates it. Record current key expiry and
revocation checks and any limitations of frozen key material; no ignored errors.
The observed key expires in 2035; no signature/key expiry waiver is authorized.

Proposed verifier is absolute `/usr/bin/gpg`; version and executable hash are in
[hygiene-provenance.json](hygiene-provenance.json). Require that version/hash or
separately review a replacement before acquisition. In an empty mode-0700 scratch
home, with the extracted keyring alone (absolute KEYRING and INPUT paths):

```sh
/usr/bin/gpg --no-options --homedir "$VERIFY_HOME" --batch --no-auto-key-retrieve --no-default-keyring --keyring "$KEYRING" --status-fd 1 --verify "$INPUT"
```

INPUT is retained raw InRelease. Retain exit code and status bytes; require exit 0,
VALIDSIG with the exact primary/subkey above and no BADSIG/ERRSIG/EXPKEYSIG/
EXPSIG/REVKEYSIG/NO_PUBKEY failures. An ownertrust warning alone is not signature
failure: trust is the explicit pinned-key allowlist. No fake clock or trust import.
Extract the clear-signed Release payload only after verification, retaining raw
InRelease and payload hashes. If detached Release.gpg is needed, STOP for the
separately authorized URL and use `--verify Release.gpg Release`. Verify signed
suite/codename/component/architecture, Release SHA256+size to Packages index,
and Packages SHA256+size to every selected .deb before considering a complete
closure. Compare all 87 base entries using Debian dpkg version ordering; missing,
downgraded or upgraded candidates require explicit old/new/hash/reason review.

## Frozen Release expiry policy

This design chooses **fail closed**. Record signed Date and Valid-Until, current
UTC observation and snapshot request time separately. Require Date <= observation
and unexpired Valid-Until at acquisition; missing/invalid/future/expired metadata
STOPs. Frozen snapshots may be expired: that is an unresolved acquisition blocker,
not permission to set Check-Valid-Until=false or ignore freshness. Any historical
freshness exception needs its own explicit maintainer decision and design delta
before use; signature checks remain mandatory. No expiry option was changed.

`candidate_snapshot_precedes_base_manifest_creation: true` in unchanged pins.json
is **UNVERIFIED**, not an accepted fact. The URL date proves neither the signed
Release date nor manifest creation. Later record signed Release Date, exact
base-config `created` bytes/hash and their comparison; config creation is registry
metadata, not a Debian-signed timestamp or proof of package compatibility. Never
use the retained boolean as a gate predicate. This qualification is the design
delta; original artifact identities and machine-readable pins remain unchanged.

## Sanitized provenance and byte fidelity

[hygiene-provenance.json](hygiene-provenance.json) records this session's variable
names only, standard CA paths and content hashes where readable, and a minimal
startup-policy membership projection. It cannot prove the original request's
proxy/CA inheritance or historical startup-policy agreement; those iteration-1
booleans remain assertions. No proxy URLs, credentials, full environment, policy
routes or raw configuration are published. No live policy/status probe or network
request was made. Current startup metadata is not live enforcement proof.

Decision: omit the environment identifier from all new evidence. Preserve the
original public environment-status.json unchanged because it is already published
and hash-linked; its identifier is not necessary to the conclusion, not a
credential, and is not repeated here. Redaction of historical bytes/history is a
separate maintainer decision, not accomplished by editing a receipt silently.

Original snapshot.headers (143 bytes) remains SHA256
`16b1bcbe30b6f0eb50da85542827c8cd8bec025726836068f31bec9882d28959`;
snapshot.stderr (47 bytes) remains
`115ac061d5c11b9f88bc706341277e549679986ec53ba237026722b790803312`.
The HTTP 403 CONNECT evidence keeps CRLF and the terminating blank line. For a
whole-history `git diff --check`, exclude **only** this raw protocol file and
separately check its hash/size; do not normalize its whitespace. The present delta
adds no raw headers and must pass unqualified `git diff --check`. Advertised
16-byte body text remains unknown; no body was received or retained.

## Residual blockers / stop

Operator alone owns exact-host snapshot.debian.org policy approval/application;
no change or bypass is authorized here. Fresh enforced policy evidence, separate
acquisition authorization, base-member trust-anchor equality, signed fresh
metadata, full closure and all-87 compatibility remain missing. G3 is independent.
BENJAMIN is permanently excluded from active venues and prerequisites; historical
provenance is archival only. G2/G5, custody, separate image authority and strict
two-independent-build OCI equality remain mandatory. No CI, container operation,
private material, policy/cgroup change, spend, merge, closure or R29 change.

Validation: JSON parsing, preserved-original-file equality, unchanged pins and
frontend/authority/source/test trees, original receipt hashes and diff whitespace
checks. No runtime tests are appropriate to this evidence-only delta. Existing
infrastructure preflight applies; no semantics, host parity, shared specs, capability
vocabulary or MCP knowledge change. KEEP these non-authoritative evidence records
for review; no authority-document edits. Independent delta review is requested
on the issue; this implementer does not self-approve. Stop after publication.
