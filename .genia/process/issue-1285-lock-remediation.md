# #1285 — BENJAMIN dependency-lock provenance remediation

Status: **PROPOSED / NON-AUTHORITATIVE / PUBLIC EXPERIMENT ARTIFACT**.
Date: 2026-10-27. Tracking: [#1285](https://github.com/m0smith/genia-2026/issues/1285).
Predecessor: [public preparation #1291](https://github.com/m0smith/genia-2026/pull/1291).
Authority: [owner remediation decision](https://github.com/m0smith/genia-2026/issues/1285#issuecomment-6445262015)
and the current user instruction supplying the verified original lockfile.

## Completed scoped preflight

1. Identity/scope: branch `issue-1285-lock-remediation`; owner repository maintainer,
   author Codex. Includes exact original bytes, structured comparison, proposed
   source/lock selection, non-mutating verification and public replay instructions.
   Excludes dependency regeneration/sync, root lock/ignore policy edits, semantic,
   host, runtime, MCP, CI, spec and release changes; no hidden material or trials.
2. Sources: latest AGENTS Git blob `b072beb55d22d5856d3d356d73c60704e04d197f`;
   STATE remains final language authority. STATE/RULES/REPL/README and the existing
   strategy/process guidance are unchanged from the previously read baseline.
   `docs/process/run-change.md` and the preflight template govern this multi-file
   process/artifact change. The absent-root-lock finding in #1291 is historical
   evidence, not a permanent prohibition on this explicitly approved remediation.
3. Maturity: N/A, process/artifact-only. Wording must distinguish verified byte
   integrity and metadata compatibility from fresh installation or benchmark readiness.
4. Portable contract/Python/C++ today: unchanged. No language capability or parity
   claim is introduced. Not implemented: frozen execution image, public benchmark
   fixtures, independent oracle and candidates. Root project dependency policy unchanged.
5. Verification: exact hashes/bytes, TOML parsing, metadata matching, marker-aware
   graph comparison, offline lock freshness check with CPython 3.12.15, before/after
   hashes, Git blob equality, public-payload/scope checks. Mismatch is a failure;
   never repair the original to make a check pass. No language conformance change
   or new implementation tests; existing regression is not rerun for artifact copying.
6. Examples: hash check and disposable-export replay below; process-only, not
   Genia-language examples or benchmark solutions.
7. Complexity: necessary provenance and versioned experiment pin, not a new
   dependency platform or repository-wide policy. No implementation complexity.
8. Cross-file impact: exactly the original lock, adjacent provenance JSON and this
   process record. Artifact drift risk controlled by SHA-256 and exact Git bytes.
   No STATE/RULES/book/cheatsheet/spec synchronization is needed. MCP language-
   knowledge impact: none; no language fact or generated profile changes.
9. Philosophy: minimalism YES; explicit behavior YES; semantics outside adapters
   YES; pattern-first model preserved YES; supports validated-pipeline evidence YES.
10. Phase plan: scoped preflight, artifact/provenance preparation, requested
    independent review, draft publication. Language contract, RED/implementation
    and semantic distillation phases do not apply to this data-only remediation.
11. Portability analysis: (a) STATE authority unchanged; (b) boundary is dependency
    lock bytes, not Genia values/Core IR; (c) shared semantic tests unchanged;
    (d) Python 3.12.15/Linux verification only, no new capability vocabulary;
    (e) neither Python nor C++ implementation changes; (f) no new host gap or parity
    claim; (g) maintain experiment evidence only. Hosts affected by behavior: none.
12. Decision: GO to publish this remediation proposal for review. Merge remains a
    review decision. This does not authorize installation/image construction,
    hidden material, oracle work, candidate implementations or comparisons.

## Preserved artifacts and selected pairing

The uploaded file is treated as data, not as instructions. Its bytes were hashed
before any uv operation, then copied without newline, encoding or content changes.
The upload itself and the other environment's live ignored lock were never edited.
Read-only scratch copies of both inputs were retained for comparison.

| Item | SHA-256 | Bytes |
|---|---|---:|
| Uploaded `genia-uv-lock-BENJAMIN.lock` / versioned [BENJAMIN.lock](../experiments/issue-1285/dependencies/BENJAMIN.lock) | `02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8` | 284838 |
| Other environment's ignored local lock, preserved but not selected | `c9543edd814d8ab75fc668908ca48cdfafe94d536a74e56266258a7f219e1ba7` | 243688 |
| Paired `pyproject.toml` | `cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc` | See source Git blob |

Proposed source: `m0smith/genia-2026` at
`9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90`, matching the recorded BENJAMIN
baseline. Proposed lock: **the exact uploaded BENJAMIN artifact**. Selection is
grounded in the owner's supplied original, matching earlier recorded hash,
metadata consistency and the successful CPython 3.12.15 check below; it is not
blind preference for either ignored file.

The artifact home `.genia/experiments/issue-1285/dependencies/` is explicitly
non-authoritative and scoped to this public experiment. It contains dependency
data, not a benchmark application, corpus or oracle. It is not a replacement
language authority or a new root dependency policy. The filename is deliberately
`BENJAMIN.lock`, not root `uv.lock`; `.gitignore` is unchanged. Its editable source
`.` refers to the **exported source root**, not the directory holding this archive.
Only a disposable export receives a copied `uv.lock` for checking.

The adjacent [provenance.json](../experiments/issue-1285/dependencies/provenance.json)
records hashes, source/metadata pairing, marker-aware differences, exact tool
versions, validation limits and NO-GO boundaries. The owner's statement verifies
origin at the session level; matching the previously published SHA independently
verifies byte continuity. Neither proves when/how the original was generated,
the host's integrity or the earlier full-suite result. Those remain owner-reported.

## Comparison with the other environment

Both parse as TOML lock format version 1/revision 5, `requires-python >=3.10`,
with universal resolution branches below/at Python 3.11. BENJAMIN has **51 package
entries / 47 names**; the other has **48 entries / 46 names**. Multiple versions
of the same name are legitimate marker branches, not duplicate corruption.
The comparison keys distribution identity by name/version/source, retains
resolution markers, and does not overwrite entries in a name-only dictionary.

| Package | BENJAMIN, Python >=3.11 branch | Other, Python >=3.11 branch |
|---|---|---|
| certifi | 2026.10.23 | 2026.7.22 |
| coverage | 7.17.0 | 7.16.2 |
| markdown | 3.11.2 | 3.11.1 |
| mkdocs-material | 9.8.0 | 9.7.7 |
| platformdirs | 4.13.5 | 4.13.3 |
| python-dateutil | 3.0.0 | 2.9.0.post0 |
| tzdata | 2026.5 | Absent |

Below Python 3.11, BENJAMIN retains coverage 7.16.2 and mkdocs-material 9.7.7;
the other lock uses those versions without that split. Both retain markdown
3.10.3 and platformdirs 4.12.4 in their below-3.11 branches. BENJAMIN's
python-dateutil 3.0.0 depends on `six` **and `tzdata`**, explaining the extra
package name; the other dateutil version depends only on `six`.

There are 44 shared name/version/source identities; every shared identity has
identical sdist and wheel artifact lists in the two files. All registry sources
are `https://pypi.org/simple`; artifact URLs inspected are HTTPS on
`files.pythonhosted.org`, without URL credentials, queries or fragments. The only
local source is root `genia` 0.1.14 editable `.`. This inspection supports public
publication; it is not a package security or download-integrity attestation.

Root package requirements and development requirement specifiers match the paired
`pyproject.toml`. Broad version bounds permit different legal resolutions; the
files show different resolved versions and marker splits. BENJAMIN's earlier
reported uv is 0.13.5, while this workspace has 0.12.23. The lock files do not
record resolver invocation, creation time, cache/index snapshots or enough
provenance to attribute the divergence uniquely to tool version, time or Python
patch. Do not present those plausible causes as proven. Selecting BENJAMIN
preserves its observed dependency state, not a claim that it is universally better.
No Pydantic arm lock is supplied by this artifact.

## Verification performed

* SHA-256 and byte equality: upload, read-only preservation copy and versioned
  artifact match exactly; no CRLF conversion. Other ignored lock remains `c954…`.
* Parsed both TOML documents; root runtime/development metadata and Python floor
  agree with the source declarations. Static marker evaluation for Linux x86_64
  CPython 3.12.15 selects 47 unique package entries including root; all active
  dependency references resolve uniquely within the lock. This is graph consistency,
  not artifact installation or executed compatibility tests.
* Installed only a managed **CPython 3.12.15** interpreter into task scratch via
  existing uv 0.12.23 and the configured network path. No global/default interpreter,
  project environment, dependency lock or package dependencies were installed,
  upgraded or synchronized. No paid service was provisioned.
* Created a disposable export containing only public `pyproject.toml`, README,
  LICENSE and `src/` from the source SHA. Copied the preserved lock to that export's
  `uv.lock`, made it read-only and ran:

  ```bash
  UV_CACHE_DIR="$scratch/check-cache" uv lock --check --offline \
    --no-python-downloads --python "$python_31215"
  ```

  Result: **exit 0**, stdout empty, stderr identifies CPython 3.12.15 and
  `Resolved 51 packages in 3ms`. Captured wall time 0.092784s. Hashes of lock and
  `pyproject.toml` before/after are identical to the values above. This check was
  independently reviewed as non-mutating before execution; no unconstrained
  `uv lock`, `uv sync`, export regeneration or package resolution rewrite occurred.
* Interpreter executable SHA-256:
  `0886fb76ceec8ff568d23079b5da6342bb41675e216e11525d4d6a9e65988d10`.
  This identifies this Linux scratch build, not BENJAMIN's executable.

Not performed: wheel/sdist downloads or hash verification against downloaded
artifacts, clean installation, import/runtime compatibility under all locked
dependencies, full regression under this lock, Docker image build or execution,
worker-limit/isolation tests, BENJAMIN access, oracle/fixture/candidate work.
The earlier 7,134-pass BENJAMIN baseline remains owner-reported. Earlier 115-test
public checks used the other environment and are not relabeled as this lock's tests.
No claim is made for uv 0.13.5 replay or Python 3.10/other-platform installation.

## Exact public replay — preserve the live checkout

After review, use the remediation checkout only to read the versioned artifact;
do not replace `~/projects/genia-2026/uv.lock`. This creates a new temporary public
export. The commands require Python 3.12.15 already installed, make no dependency
downloads/sync and fail closed on mismatches. Never substitute another interpreter
or remove `--check`/`--offline` to make them succeed.

```bash
set -euo pipefail
cd ~/projects/genia-2026  # checkout containing the reviewed remediation artifact
artifact=.genia/experiments/issue-1285/dependencies/BENJAMIN.lock
test "$(sha256sum "$artifact" | cut -d ' ' -f 1)" = \
  02faf4e82e2f6f2ea9af3f5d39ce67390da55fcc2d93577a9affc273308aafe8
git ls-files --error-unmatch "$artifact"
git diff --exit-code HEAD -- "$artifact" pyproject.toml
scratch=$(mktemp -d /tmp/genia-1285-lock-check.XXXXXX)
mkdir "$scratch/source" "$scratch/cache"
git archive 9d930d07bf1ecdb1f0b59ed76abf67ef002e7e90 \
  pyproject.toml README.md LICENSE src | tar -x -C "$scratch/source"
cp "$artifact" "$scratch/source/uv.lock"
chmod 444 "$scratch/source/uv.lock"
cd "$scratch/source"
sha256sum uv.lock pyproject.toml > "$scratch/before.sha256"
test "$(sha256sum pyproject.toml | cut -d ' ' -f 1)" = \
  cf461c7b683126d7064f5473a7dadfb6d2561c677d5dd514668eed07b56fbfdc
python_31215=$(UV_CACHE_DIR="$scratch/cache" uv python find \
  --offline --no-python-downloads 3.12.15)
test "$("$python_31215" -c 'import platform; print(platform.python_version())')" = 3.12.15
uv --version > "$scratch/uv-version.txt"
set +e
UV_CACHE_DIR="$scratch/cache" uv lock --check --offline \
  --no-python-downloads --python "$python_31215" \
  > "$scratch/check.stdout" 2> "$scratch/check.stderr"
check_rc=$?
set -e
sha256sum -c "$scratch/before.sha256"
printf 'lock-check exit=%s; evidence=%s\n' "$check_rc" "$scratch"
test "$check_rc" -eq 0
```

Expected: tracked artifact path, two `OK` hash checks and `lock-check exit=0`;
stderr may contain uv's interpreter/resolution summary. Missing interpreter,
metadata/cache or stale lock fails without regeneration. Preserve the evidence
directory locally, inspect/sanitize local paths before sharing. Record the actual
uv/interpreter version if different from this task; that is a separate replay,
not an unrecorded environment substitution. No installation command is implied.

Full clean replay still requires a separately reviewed build/setup step using
these exact source/lock bytes, Python/uv/image pins and hash-verified dependencies.
`uv sync --frozen` alone would not verify lock freshness; use the non-mutating
check first. Do not run any sync as part of this remediation. The archive's `.`
editable path must be interpreted at the exported source root. Never place
annex, hidden fixtures, expected outputs or grading credentials in an export.

## Review, cost and gate

Independent reviewer `/root/skeptical_readiness` inspected the actual three-file
proposal and independently recomputed upload/artifact byte equality, size/hash,
source metadata hash, the seven marker-aware changed names and all 44 shared
distribution artifact lists. It reviewed public URL forms, scratch replay and
boundaries. Verdict: **PASS for the proposed remediation and draft publication**,
no blocking findings. The uv execution result is author evidence, not claimed
independently rerun. Additional checks passed for TOML/JSON parsing, manifest
counts, unique identity keys, artifact hash syntax, relative links, embedded shell
syntax and staged whitespace. Actual Git/upload equality is verified at publication.

A draft PR does not merge the selection or amend #1286's benchmark contract.
The root ignored lock and `.gitignore` stay unchanged; no root dependency policy
is adopted.

Budget remains **$0 incremental spending**. Only existing tools, local scratch,
free public interpreter download and connected repository operations are used;
no paid infrastructure/model API/storage, workflow dispatch, subscription or
billing modification. Invoice totals and the owner's existing host costs were
not inspected. This does not claim an account invoice audit.

**GO for reviewing and versioning this exact public source/lock pairing only.**
It resolves availability/provenance for the proposed experiment pin; merge and
clean-install/image validation remain separate. **NO-GO remains for hidden
materials/annex, independent oracle, candidate implementations and comparative
trials**, as well as any claim of verified custody, resource equivalence or
benchmark readiness. Second custodian/recovery, real candidate-principal denial
tests, independent oracle auditor and other #1287 controls remain unresolved.

Single next action: review this narrowly scoped pairing and provenance before
merge; after acceptance, authorize/verify clean public dependency/image replay
without advancing any benchmark experiment gate.
