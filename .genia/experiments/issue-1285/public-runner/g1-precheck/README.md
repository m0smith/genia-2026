[Iteration-2 hygiene and qualifications](hygiene.md) supersede unsupported timestamp
and provenance assertions below; G1 remains BLOCKED.

# G1 immutable Debian closure — public precheck, iteration 1

**BLOCKED, 2026-11-07 UTC.** This bounded lane follows the
[maintainer's G1/G3 authorization](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6702416476)
at accepted frontend `fd74a5830c76373d724bbd40a603ea85870f0aca`.
It adds evidence only; it does not change any artifact pin or language behavior.

The fresh request to
`https://snapshot.debian.org/archive/debian/20261021T000000Z/dists/trixie/InRelease`
using inherited proxy and CA failed at HTTPS CONNECT with **HTTP 403**, curl
exit 56. [Headers](snapshot.headers) and [stderr](snapshot.stderr) preserve the
failure; no Debian response body or metadata was received. No retry via another
origin, mirror, relay, live apt or proxy bypass was attempted. The fresh managed
[status projection](environment-status.json) is current/enforced, restricted,
revision 1, and excludes `snapshot.debian.org`; startup-policy agreement was asserted but
its projection was not retained in that iteration.

[receipt.json](receipt.json) records the command, hashes and static preservation
checks. The unchanged manifest contains 87 unique base packages and proposed
Git/Tini/procps/lsof roots. This count is a recheck of the accepted inventory,
not a new extraction or signed snapshot compatibility proof. Signed Release,
Packages hash chain, full `.deb` dependency hashes and compatibility of every
base package remain **UNVERIFIED**. `closure_complete=false` stays unchanged.

## Exact environment-operator action

In the managed environment settings for this executor configuration, preserve
the existing configuration and add the exact outbound HTTPS host
`snapshot.debian.org` to allowed hosts. Save/apply through the supported
environment configuration flow. Do not disable restrictions or alter supplied
proxy/CA variables. Confirm a fresh `environment_status` reports
`observations_current=true`, `network_policy.state=enforced` and
`effective_allowed_hosts` includes that host before a fresh connection to the
same immutable URL. If a later response redirects elsewhere, review that actual
host separately; no blanket wildcard or alternate-origin authorization follows.
No policy update was made in this lane.

After operator action, the next bounded G1 step is signed metadata acquisition
and verification from the same frozen snapshot, then exact dependency closure
and Debian-version-order comparison for all 87 base entries. Missing candidates,
downgrades or required upgrades STOP for explicit old/new/hash/reason review.
No existing pin may be silently replaced. Request independent Claude Code
review of this exact evidence commit; review is pending, not self-approved.

## Scope and validation

The existing scoped infrastructure preflight applies: no Python/C++ semantics,
Core IR, capability vocabulary, host parity, shared conformance, MCP knowledge,
or example changes. The four authority documents remain accurate and unchanged.
This is a failed-access evidence phase, not new implementation, so no runtime
regression or image tests were run. Branch guard, JSON parsing, evidence hashes,
unchanged-pin equality, unique inventory count and whitespace checks apply.

No image/container construction, run or export, CI dispatch, hidden material,
oracle, competitor implementation, benchmark trial, merge, issue closure or R29
work. Incremental spending is $0; usage/review effort are unmeasured. G3 remains
independent; neither lane waives strict two-independent-build OCI manifest,
config, layer and canonical-archive equality or later target/resource/reaping,
G2/G5, custody and benchmark gates.
