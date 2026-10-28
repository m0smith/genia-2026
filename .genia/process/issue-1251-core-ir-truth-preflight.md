# #1251 Core IR release-truth correction

Audit authority: d55524dff62c036951301143781e62eb5310ef68. This separate
documentation-only branch corrects stale architecture status, not runtime or
contract behavior. AGENTS and STATE were read first. STATE remains final
authority. Clarify its REPL sentence to say completed submissions end closed
groups: ordinary default-open groups do accumulate across submissions, as the
existing persistent-session cases and independent probes demonstrate. This
shortens STATE within its 43,000-word limit; no implemented behavior changes.

The architecture page still called C++ an R24 subset, external process execution
planned, Python the only executing host, and a second host/generic runner absent.
STATE sections 9.40 and host status, the capability matrix, host adapters and
the executed 1,044-case suites contradict those historical status statements.
Replace only those claims with bounded implemented support and explicit remaining
closed-function/ordinary-linking and universal-host limits. Do not imply every
Core IR node executes on C++ or that Slice D/E have landed.

Both hosts are described; neither implementation changes. No grammar, semantics,
shared oracle, capability, protocol/version, baseline or example changes. MCP
knowledge impact: none; the current generated profile already describes the
partial Model B/Python-versus-C++ boundary and gains no new fact from correcting
this stale architecture prose. The seven portability fields are unchanged:
authority STATE; representation Core IR; evidence full shared host suites;
applicability existing capability gates; claims bounded support; gaps existing
issue-backed limits; truth synchronization the architecture page and qualified
STATE sentence.

The descriptive reason for `default_open_functions` in known_host_gaps.json
also still described the RED-era nine failures as outstanding. Update only that
reason with the demonstrated passing pin, closed #55–#57, and explicitly open
#53/#54 acceptance criteria. Capability values, case lists and removal conditions
are unchanged; this is evidence/prose synchronization, never a waiver.

Validation: focused portability/documentation semantic synchronization and MCP
profile checks, plus independent review of the exact documentation delta.
No benchmark, runtime RED or new example is applicable. Reliability of the
validated-pipeline workflow is served by truthful host portability descriptions.
This change neither approves #1270 nor completes #1251 or authorizes R29.
