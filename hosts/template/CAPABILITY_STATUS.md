# Capability Status

Capability names are authoritative in `docs/host-interop/capabilities.md`. Do not invent capability names — use only names listed there.

This file tracks the implementation status of each host capability for this host. Update it as implementation progresses.

| Capability | Status | Notes |
|---|---|---|
| io.stdout | Not Implemented | TODO |
| io.stderr | Not Implemented | TODO |
| io.stdin | Not Implemented | TODO |
| time.sleep | Not Implemented | TODO |
| random.rng | Not Implemented | TODO |
| random.rand | Not Implemented | TODO |
| random.rand-int | Not Implemented | TODO |
| random.rand-seeded | Not Implemented | TODO |
| random.rand-int-seeded | Not Implemented | TODO |
| http.serve | Not Implemented | TODO |
| process.spawn | Not Implemented | TODO |
| process.send | Not Implemented | TODO |
| process.alive | Not Implemented | TODO |
| process.failed | Not Implemented | TODO |
| process.error | Not Implemented | TODO |
| ref.create | Not Implemented | TODO |
| ref.get | Not Implemented | TODO |
| ref.set | Not Implemented | TODO |
| ref.update | Not Implemented | TODO |
| cell.create | Not Implemented | TODO |
| cell.send | Not Implemented | TODO |
| cell.get | Not Implemented | TODO |
| cell.restart | Not Implemented | TODO |
| bytes.utf8-encode | Not Implemented | TODO |
| bytes.utf8-decode | Not Implemented | TODO |
| json.parse | Not Implemented | TODO |
| json.stringify | Not Implemented | TODO |
| zip.entries | Not Implemented | TODO |
| zip.write | Not Implemented | TODO |

---

Status must be updated as implementation progresses. Do not mark Implemented until code, tests, and spec coverage all exist.

When a capability is ready, also update `docs/host-interop/HOST_CAPABILITY_MATRIX.md` for this host's row.
