# F2 P1-G runtime consumers — issue #1067

Scope: Python documentation tools, restricted MCP runtime pruning, and Python
harness inspection ownership. Infrastructure preparation; no language semantics,
entry child, reflection binding, fallback, or new scopes are activated.

TEST: `8d60243` recorded four expected missing-accessor failures. The seam tests
supply a distinct runtime owner to detect accidental program-table pruning and
catalogue/metadata lookup through entry. This is a host test double, not a new
runtime topology. MCP pruning retains default-deny removal of unclassified names,
binding metadata, denied autoloads and trusted-autoload membership.

Implementation: `ebf2df2` references that gate. Documentation catalogue lookups
and linter public names use R. MCP prunes R values and autoloads. Runtime presence
assertions inspect R; module aliases/program assignments inspect E. Current E/R
identity and generated reference output are unchanged.

Verification: 224 fixture/Flow/runtime-presence checks passed; focused consumer,
module, documentation and MCP suites run separately. Generated reference --check
passed. Prelude documentation coverage: 24 files, 286 doc strings, zero errors or
warnings. Ruff passed for changed tooling and the new gate. An initial invocation
of lint_doc without --scan-dir exposed the existing missing-argument IndexError;
the supported CI invocation passed.

Residual survey: no Env .root() consumers remain in tools/ or hosts/. Remaining
raw env.values in tests are P1-B own-frame characterization, a runtime-local
host documentation registry variable, and an os.environ dictionary in the MCP
launcher. Host injections are coordinated with P1-E: the module counter is
runtime-public because module code intentionally consumes it; fixture/provider
and credential installation classifications remain explicit P1-E work.

No public metadata changed; STATE/book/cheatsheet/MCP knowledge synchronization
belongs to the integration owner. This record adds no implemented-isolation
claim. P2, P3 and F3–F5 remain gated; #1067 remains open. No PR merge authorized
by this slice.
