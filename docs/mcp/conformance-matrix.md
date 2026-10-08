# R28 MCP conformance and parity matrix (E28-5, extended by E28-6 amendment A5)

Status: **E28-5 evidence matrix** (issue #706, epic #700). `GENIA_STATE.md` is the final authority
for implemented behavior; the contract is `docs/design/r28-genia-mcp-contract-threat-model.md`
(sections cited as `C§`) with Clarifications A1–A5 (A5, the `2025-11-25` compatibility era, section 18). Design and classification:
`docs/design/r28-e28-5-conformance-matrix-design.md`. Findings: ledger
`docs/analysis/r28-host-dependency-inventory.md` (`[H##]`). **R28 is complete**: E28-6 (#707) delivered
the demo and the final release audit, which re-read every row below.

MCP is an adapter boundary over existing Genia semantics, not a second execution path. This matrix
separates **semantic parity** (direct Genia and MCP agree) from **adapter behavior** (envelope
instead of raw text), **transport behavior** (framing, lifecycle), **security policy**
(intentional denials) and **host implementation detail**. A difference the contract mandates is
never labeled a parity failure.

Scope: the Python reference host, local stdio, exactly `genia_capabilities`, `genia_parse`,
`genia_run`, and (amendment A6, section D9) `genia_language_profile`. No resources, no prompts, no Streamable HTTP, no C++ MCP, no MCP client in Genia, no
sandbox claim.

## How to read a row

- **Class:** P protocol conformance · A adapter/direct-host parity · S security/authority ·
  D deterministic · R resource/lifecycle · H host-specific implementation evidence · L documented
  limitation.
- **Direct** is direct Genia command-source evaluation (`run_source(..., filename="<command>")` in the
  default global environment, canonical debug renderer, captured streams). It is not the CLI `-c`
  stream, which dispatches `main` [H29]. **MCP** is the launcher over stdio.
- **Relationship:** `EXACT` (byte-for-byte equal), `CLOSED` (a fixed closed envelope, no source
  or host text), `DENIED` (policy restriction by contract), `DIFFERS-BY-CONTRACT`, `INVARIANT`
  (an invariant is asserted, not a specific race winner), `N/A`.
- **Status:** `PASS` (automated evidence passes) · `KNOWN LIMITATION` (documented and pinned, not
  parity) · `NOT APPLICABLE` (deferred or excluded by the contract).
- **Evidence** is `key::test`. Keys: `surface`, `run`, `security`, `lifecycle` =
  `tests/unit/test_r28_mcp_conformance_<key>.py` (E28-5); `e1` skeleton, `e2` parse, `e3run`, `e3sup`,
  `e3wrk`, `e4cfg`, `e4launch`, `e4life`, `arch`, `launcher`, `client` = the existing
  `tests/unit/test_r28_mcp_<name>.py` files (`skeleton`, `parse`, `run`, `run_supervisor`,
  `run_worker`, `stdio_config`, `stdio_launch`, `stdio_lifecycle`, `architecture`, `launcher`,
  `official_client`); E28-6 adds `demo`, `entry` and `gate` = `test_r28_mcp_demo.py`, `test_r28_mcp_entrypoint.py`, `test_r28_release_gate.py`; amendment A6 adds `lprofile` (`test_r28_mcp_language_profile.py`) and #1099 adds `lregistry` (`test_r28_mcp_language_registry.py`); amendment A5 adds `compat` (`test_r28_mcp_compat.py`, protocol), `compatconf` (`test_r28_mcp_compat_conformance.py`, both-era conformance) and `port` (`test_r28_mcp_portability.py`, macOS portability). `tests/unit/test_r28_mcp_conformance_matrix.py` fails if a cited test is missing.
- **Namespace:** wire tests marked *(ns)* run with the host's real namespace behavior **and** with
  `unshare` simulated as denied; the whole R28 suite can also be run denied with
  `GENIA_R28_TEST_DENY_NAMESPACE=1`. The namespace is defense in depth, never the security contract.

## D — Discovery, schemas, capabilities

| ID | Behavior | Class | Authority | Direct | MCP | Relationship | Evidence | Host limitations | Status |
|---|---|---|---|---|---|---|---|---|---|
| D1 | Exactly four tools, in contract order, stable across calls, no pagination | P | C§2.1, C§19 | n/a | `tools/list` = `genia_capabilities`, `genia_parse`, `genia_run`, `genia_language_profile` | EXACT | `surface::test_discovery_advertises_exactly_the_four_tools_in_contract_order` *(ns)*; `e1::test_tools_list_rejects_any_cursor_no_pagination_in_e28_1`; `client::test_the_official_client_completes_the_acceptance_scenario` | none | PASS |
| D2 | Descriptor key set and exact descriptions | P | C§2.1 (descriptions not normative) | n/a | `{name, description, inputSchema}` only; exact text | EXACT (drift detector) | `surface::test_every_descriptor_has_the_exact_key_set_description_and_closed_schema` *(ns)* | descriptions pinned as drift detectors, not contract text | PASS |
| D3 | Exact closed input schemas, no extra input property accepted | P | C§2.1–2.5 | n/a | `additionalProperties: false` everywhere; extra key → `-32602` | EXACT | `surface::test_every_descriptor_has_the_exact_key_set_description_and_closed_schema`; `surface::test_no_extra_input_property_is_accepted_by_any_tool` | none | PASS |
| D4 | No resources, no prompts, no other protocol surface | P | C§2.1, C§13 | n/a | `capabilities == {tools: {}}`; resources/prompts/completion/logging/sampling/roots/tasks → `-32601` | EXACT | `surface::test_server_capabilities_name_tools_only_so_resources_and_prompts_are_absent`; `surface::test_unadvertised_protocol_surface_is_method_not_found` | none | PASS |
| D5 | No fifth tool; no Python-host-only tool leakage | P | C§2.1, C§1.1, C§19 | n/a | 20 near-miss/host names → `-32602 Unknown tool`; tool literals live only in `mcp.genia` | EXACT | `surface::test_no_fifth_tool_and_no_host_only_tool_is_callable`; `surface::test_tool_names_exist_only_in_native_genia_not_in_python_host_modules`; `arch::test_no_python_module_defines_mcp_application_literals` | none | PASS |
| D6 | Tool list is identical on every session | D | C§7.1 | n/a | repeated and independent launches | EXACT | `surface::test_discovery_advertises_exactly_the_four_tools_in_contract_order`; `e1::test_tools_list_is_deterministic_across_calls` | none | PASS |
| D7 | `genia_capabilities` describes the implemented profile, claims no OS mechanism, identical with a granted or denied namespace | P / H | C§2.3, A1; E28-3 design §5 | n/a | `execution_profile` flags `false`; no namespace/sandbox/seccomp/rlimit wording | EXACT | `surface::test_capabilities_describe_the_implemented_profile_and_claim_no_os_isolation` *(ns)*; `surface::test_capabilities_are_byte_identical_whether_the_namespace_is_granted_or_denied`; `surface::test_capability_tools_agree_with_tools_list` | the OS layer is best effort and is intentionally absent from the response | PASS |
| D8 | `initialize` carrying the `2026-07-28` `_meta` stays `Method not found`; no session; later answers unchanged (the `2025-11-25` handshake is the K section) | P | C§7.1, A5.2 | n/a | `-32601` | EXACT | `surface::test_initialize_with_a_modern_meta_is_still_method_not_found_and_changes_nothing`; `compat::test_initialize_carrying_the_modern_meta_is_still_method_not_found` | none | PASS |
| D9 | `genia_language_profile` (amendment A6): fourth tool, no arguments (omitted or `{}`; any other `-32602`), closed descriptor, `genia.mcp.v1` envelope; states `if_expression=false`, `loops=false`, `recursion=true`, first-match patterns; the `gcd` and `factorial` examples evaluate to `6` and `120` under direct evaluation; byte-identical across calls, eras and namespace modes; native-only literals; MCP adapter text, not language semantics | P / D | C§19 | direct evaluation of each example | `result.language` | EXACT (drift detector) | `lprofile::test_tools_list_includes_the_profile_tool_in_contract_order` *(ns)*; `lprofile::test_capabilities_tools_agree_with_tools_list` *(ns)*; `lprofile::test_omitted_or_empty_arguments_are_accepted`; `lprofile::test_any_non_empty_or_non_object_arguments_are_invalid_params`; `lprofile::test_profile_states_pattern_matching_branching_and_no_if_or_loops`; `lprofile::test_every_profile_example_evaluates_as_documented_by_direct_evaluation`; `lprofile::test_the_absent_forms_really_are_absent_in_the_language`; `lprofile::test_profile_is_byte_identical_across_calls_and_namespace_modes`; `lprofile::test_the_profile_is_identical_in_both_protocol_eras` *(ns)*; `lprofile::test_the_tool_introduces_no_resources_or_prompts_surface`; `lprofile::test_the_profile_literals_live_only_in_native_genia` | the profile restates STATE; it is not parity evidence for any other host | PASS |
| D10 | A7/A8/A9/A10/A11 scoped discovery: closed static 15-fact catalogue (A8 appends `validated_data_pipelines` and adds `idioms.pipelines`; A9 appends `outcome_pipeline_propagation` and adds `idioms.outcomes`; A10 appends `flow_semantics` and adds `idioms.flow`; A11 corrects only the `idioms.outcomes` wording) with separate status/maturity, STATE mappings and bounded JSON; unchanged capabilities payload; plain file mode agrees | P / D | C§20, C§22, C§23, C§24, STATE§9.50 | registry evidence (STATE anchors, probes) | `language.discovery`, `language.idioms.outcomes`, `language.idioms.flow` | EXACT (drift detector) | `lprofile::test_discovery_is_the_exact_closed_scoped_catalogue`; `lprofile::test_discovery_fact_matches_the_golden_wire_snapshot`; `lregistry::test_wire_equals_the_registry_projection_and_the_golden_snapshot`; `lregistry::test_committed_generated_block_matches_a_fresh_projection`; `lprofile::test_discovery_plain_file_mode_matches_launcher_without_host_authority`; `lprofile::test_discovery_does_not_expand_capabilities_payload`; `lprofile::test_discovery_literals_remain_native_application_data`; `lprofile::test_profile_is_byte_identical_across_calls_and_namespace_modes`; `lprofile::test_the_profile_is_identical_in_both_protocol_eras` *(ns)*; `loutcomes::test_a9_outcomes_idiom_is_the_exact_contract_text`; `loutcomes::test_a9_new_fact_is_exact_and_closed`; `loutcomes::test_a9_discovery_grows_from_13_to_exactly_14_facts_with_the_new_fact_last`; `loutcomes::test_the_mcp_surface_stays_the_closed_four_tools_with_no_resources_or_prompts`; `loutcomes::test_a_direct_call_passes_the_outcome_itself_and_is_not_lifted`; `lflow::test_a10_flow_idiom_is_the_exact_contract_text`; `lflow::test_a10_new_fact_is_exact_and_closed`; `lflow::test_a10_discovery_grows_from_14_to_exactly_15_facts_with_the_new_fact_last`; `lflow::test_a_consumed_flow_cannot_be_consumed_again`; `lflow::test_take_does_not_over_pull_and_a_full_collect_pulls_everything`; `lflow::test_the_mcp_surface_stays_the_closed_four_tools_with_no_resources_or_prompts`; `labsence::test_a11_outcomes_idiom_is_the_exact_contract_text`; `labsence::test_a11_the_exception_is_stated_and_the_retired_phrase_is_gone`; `labsence::test_a_callee_with_a_none_pattern_receives_the_none`; `labsence::test_an_ordinary_callee_still_short_circuits_on_a_none_argument`; `labsence::test_a11_a10_flow_content_is_byte_identical` | curated, non-exhaustive; no new authentic client acceptance (acceptance runs 1-3 predate A9, A10, and A11) | PASS |

## P — `genia_parse`

| ID | Behavior | Class | Authority | Direct | MCP | Relationship | Evidence | Host limitations | Status |
|---|---|---|---|---|---|---|---|---|---|
| P1 | Valid sources parse to the existing normalized AST | A | C§2.4 | `parse_and_normalize` | `result.ast` | EXACT | `surface::test_valid_and_invalid_sources_match_the_existing_parse_surface_exactly` *(ns)*; `e2::test_parse_matches_the_existing_parse_surface` | none | PASS |
| P2 | Invalid sources are `parse_error` with an offset only | A / P | C§2.4, A2 | `SyntaxError` offset | `Genia source failed to parse at character offset N` | EXACT | `surface::test_valid_and_invalid_sources_match_the_existing_parse_surface_exactly`; `surface::test_syntax_errors_report_distinct_character_offsets_never_source_text` | none | PASS |
| P3 | Empty / whitespace / comment-only source is a successful empty program | A | C§2.4 | `ast == []` | `ast: []` | EXACT | `surface::test_empty_source_is_a_successful_empty_program` | none | PASS |
| P4 | Errors at multiple offsets; offsets count characters, not bytes | A | C§2.4 | direct offset | same offset | EXACT | `surface::test_syntax_errors_report_distinct_character_offsets_never_source_text`; `surface::test_offsets_are_characters_not_bytes` | none | PASS |
| P5 | UTF-8 string literals, mixed scripts, emoji | A | C§2.4 | direct AST | same AST | EXACT | `surface::test_unicode_string_literals_and_mixed_scripts_parse_like_the_direct_host` | none | PASS |
| P6 | Unicode **identifiers** are not accepted by the parser today; the adapter reproduces the failure | L | current parser | `SyntaxError` at the identifier | `parse_error` at the same offset | EXACT (failure parity) | `surface::test_unicode_identifiers_fail_identically_to_the_direct_parser` | parser limitation, not an MCP defect; no support invented | KNOWN LIMITATION |
| P7 | Invalid Unicode (lone surrogate escape, invalid UTF-8 bytes) is `-32700` at the JSON-RPC boundary; the stream continues | P | A2 | n/a | `-32700`, no id, next request served | EXACT | `surface::test_invalid_unicode_is_rejected_at_the_json_rpc_boundary_and_the_stream_continues`; `e2::test_invalid_unicode_is_a_protocol_parse_error_not_input_limit` | none | PASS |
| P8 | Source limit is 262,144 UTF-8 **bytes** (one below / exact / one above, multibyte) | R / P | C§2.4, C§5 | n/a | `input_limit` before parsing | CLOSED | `surface::test_source_limit_is_utf8_bytes_one_below_exact_and_one_above`; `e2::test_oversized_source_is_rejected_before_parsing` | none | PASS |
| P9 | Large exact integers stay exact JSON number tokens; no R9 range corruption | A | A3, [H22] | Python int | exact token, never string/float | EXACT | `surface::test_large_exact_integers_stay_exact_in_the_ast_and_never_pass_through_r9_json`; `e2::test_large_integer_is_an_exact_json_number_token_on_the_wire` | the normalized surface collapses unary/list/map nodes [H23] | PASS |
| P10 | Normalized AST is stable and deterministic (byte-identical frames across launches) | D | C§2.4 | n/a | identical | EXACT | `surface::test_parse_is_deterministic_across_calls_and_independent_launches` | none | PASS |
| P11 | Parsing never evaluates and acquires no authority; independent of run policy | S | C§2.4 | n/a | prohibited-looking source parses; no marker, no hang | EXACT | `surface::test_parsing_never_evaluates_or_acquires_authority`; `surface::test_parse_authority_is_independent_of_run_policy` | none | PASS |
| P12 | Diagnostics are bounded and never echo source | S | C§2.2, C§5 | n/a | fixed offset message | CLOSED | `surface::test_parse_failure_for_hostile_text_is_bounded_and_echo_free` | none | PASS |

## R — `genia_run` success and direct-host parity (V1)

The corpus (`CORPUS` in `run`) has 55 programs: literals, arithmetic, exact numerics beyond the R9
safe-integer range, collections, Unicode strings and map keys, functions and recursion, Outcome values
(`some`/`err`/`none`, validated records), pipelines and lazy Flow, program output, inert `argv()`/stdin.
For every program, rendered value, stdout and stderr must equal direct command-source evaluation
exactly, with the namespace granted and denied.

| ID | Behavior | Class | Authority | Direct | MCP | Relationship | Evidence | Host limitations | Status |
|---|---|---|---|---|---|---|---|---|---|
| R1–R8 | Literals, arithmetic, collections, functions, Outcomes, Flow/pipelines, Unicode strings, exact numerics | A | C§2.5 | command-source evaluation | `value.rendered`, `stdout`, `stderr` | EXACT | `run::test_mcp_equals_direct_command_source_evaluation_exactly` *(ns)*; `run::test_the_corpus_covers_every_required_semantic_class`; `e3run::test_run_matches_direct_command_mode_execution` | none | PASS |
| R9 | `main` is **not** dispatched by MCP; CLI `-c` mode dispatches it | A / L | C§2.5 vs STATE `-c` | library call: no dispatch; CLI `-c`: dispatches | not dispatched | DIFFERS-BY-CONTRACT | `run::test_main_is_not_dispatched_by_mcp_but_is_by_cli_command_mode`; `e3run::test_command_source_semantics_do_not_dispatch_main` | [H29] | KNOWN LIMITATION |
| R10 | Determinism across calls and launches; no state across calls | D | C§4 | n/a | identical envelopes | EXACT | `run::test_corpus_results_are_deterministic_across_calls_and_independent_launches`; `run::test_no_state_carries_between_calls_in_one_session`; `e3run::test_each_call_starts_from_a_fresh_runtime` | `rand`, time and callable addresses are not deterministic by Genia semantics and are excluded | PASS |
| R11 | An authority available to direct execution is denied by MCP: a **policy restriction**, not a semantic divergence | S / A | C§4 | `read_file` returns content | `policy_denied`, file never read | DENIED | `run::test_denied_authority_is_a_policy_restriction_not_a_semantic_difference` | none | PASS |

## C — Channel separation and framing

Cases: value only, stdout only, stderr only, value+stdout, value+stderr, all three, interleaved, JSON
on stdout, a JSON-RPC response lookalike with the request's own id, a request lookalike, a
`notifications/cancelled` lookalike for the running request (stdout and stderr), MCP method names,
5,000 newlines, CRLF/CR, U+2028/U+2029/U+0085, control characters, Unicode on both channels.

| ID | Behavior | Class | Authority | Direct | MCP | Relationship | Evidence | Host limitations | Status |
|---|---|---|---|---|---|---|---|---|---|
| C1–C9 | Value, stdout, stderr and exit code stay separate and equal the direct channels | P / A | C§2.5 | captured streams | `completed{value.rendered, stdout, stderr, exit_code: 0}` | EXACT | `run::test_channels_are_separate_and_match_direct_evaluation` *(ns)*; `e3run::test_value_stdout_and_stderr_are_distinct_channels` | none | PASS |
| C-F | Program output is data and never becomes framing: exactly one `\n`-terminated frame per request, no extra frame, a cancel lookalike does not cancel its own run | P | C§7.1 | n/a | one response frame per request | EXACT | `run::test_program_output_never_becomes_protocol_framing`; `run::test_session_stays_usable_after_hostile_output`; `client::test_the_official_client_completes_the_acceptance_scenario` | U+2028/U+2029/U+0085/DEL are legal raw in JSON and are not separators; framing is `\n` only; a client that splits on Unicode line separators would mis-frame (the official client does not: `framing` step) | PASS |
| C10 | UTF-16 surrogate `\u` escapes in program strings: a valid pair becomes the real scalar; a lone surrogate fails closed as `internal_error` | L | JSON boundary | keeps surrogate code units | merged scalar / `internal_error` | DIFFERS-BY-CONTRACT | `run::test_utf16_surrogate_escapes_are_a_documented_transcoding_limitation` | [H40]: Python-host string detail; no leak, fixed message | KNOWN LIMITATION |

## F — Failure envelopes

Every failure is the closed envelope: exactly `schema_version`, `status: "error"`, `result: null`,
an `error` with exactly `kind`, `message`, `phase`; `isError: true`; a fixed server-owned message;
no partial stdout, stderr or value; no Python class, traceback, host path, repository path, address
or source text; the server keeps serving.

| ID | Behavior | Class | Authority | Direct | MCP | Relationship | Evidence | Host limitations | Status |
|---|---|---|---|---|---|---|---|---|---|
| F1 | `parse_error` (phase `parse`, offset only) | P | C§2.2 | `SyntaxError` | closed envelope | CLOSED | `run::test_every_failure_class_is_the_closed_envelope_with_a_fixed_message` *(ns)* | none | PASS |
| F2 | `policy_denied` (phase `policy`) for file, import, shell stage | S | C§4 | authority available | closed envelope | DENIED | `run::test_every_failure_class_is_the_closed_envelope_with_a_fixed_message` *(ns)* | none | PASS |
| F3 | `runtime_error` (phase `execution`) for divide, unbound, `error(...)`, type error; earlier output dropped | P | C§2.5 | Python/Genia exception text | fixed message | CLOSED | `run::test_every_failure_class_is_the_closed_envelope_with_a_fixed_message` *(ns)*; `e3run::test_runtime_error_is_normalized_without_source_or_diagnostic_text` | none | PASS |
| F4 | `timeout` | R | C§5 | n/a | fixed message | CLOSED | `lifecycle::test_timeout_is_fixed_closed_partial_free_and_the_next_request_still_works` *(ns)*; `e3run::test_deadline_returns_timeout_and_reaps_the_worker` | wall-clock based | PASS |
| F5 | `cancelled` | R | C§5 | n/a | fixed message | CLOSED | `lifecycle::test_cancel_during_evaluation_returns_no_partial_data_and_removes_the_workdir` *(ns)*; `e3run::test_cancelled_envelope_carries_no_partial_data` | none | PASS |
| F6 | `result_limit` (channel, value, aggregate) | R | C§5 | n/a | two fixed messages | CLOSED | `run::test_every_failure_class_is_the_closed_envelope_with_a_fixed_message` *(ns)*; `run::test_aggregate_result_boundary_is_measured_on_the_encoded_envelope_bytes` | none | PASS |
| F7 | `input_limit` (phase `protocol`) | P | C§2.4 | n/a | fixed message, no worker | CLOSED | `run::test_every_failure_class_is_the_closed_envelope_with_a_fixed_message` *(ns)*; `e3run::test_source_over_the_limit_is_input_limit_and_never_reaches_a_worker` | none | PASS |
| F8 | `internal_error`: worker crash, garbage reply, non-zero exit, extra reply fields, all induced through the supervisor's own `worker_argv` seam (no production code weakened) | P | C§6 | n/a | fixed message, no worker text | CLOSED | `run::test_internal_error_is_fixed_and_leaks_nothing_of_the_worker`; `run::test_a_reply_with_extra_fields_cannot_smuggle_text_through_the_closed_envelope`; `e3sup::test_oversized_reply_is_killed_and_internal_error` | the substitute host mirrors `mcp_host.main` (`tests/fixtures/r28_substituted_host.py`) | PASS |
| F9 | Fixed server-owned messages, ASCII, far below the 65,536-byte diagnostic bound | P | C§2.2, C§5 | n/a | constants | EXACT | `run::test_every_failure_message_is_a_fixed_server_owned_string_within_the_diagnostic_bound` | none | PASS |
| F-S | The server keeps serving after every failure class | P | C§7.1 | n/a | next request answered | EXACT | `run::test_the_server_keeps_serving_after_every_failure_class` *(ns)* | none | PASS |

## L — Limits (UTF-8 bytes)

| ID | Behavior | Class | Authority | Direct | MCP | Relationship | Evidence | Host limitations | Status |
|---|---|---|---|---|---|---|---|---|---|
| L1 | Source 262,144 bytes: one below / exact / one above, multibyte (`run` and `parse`) | R | C§5 | n/a | below, exact run; above `input_limit` with no worker | CLOSED | `run::test_source_limit_for_run_is_utf8_bytes_one_below_exact_one_above`; `surface::test_source_limit_is_utf8_bytes_one_below_exact_and_one_above` | none | PASS |
| L2 | stdout 1,048,576 bytes: one below / exact / one above | R | C§5 | n/a | `result_limit` above | CLOSED | `run::test_stdout_boundary_in_bytes_ascii_below_exact_above`; `e3run::test_stdout_at_the_limit_succeeds_and_one_byte_over_is_result_limit` | none | PASS |
| L3 | stderr 1,048,576 bytes | R | C§5 | n/a | same | CLOSED | `run::test_stderr_boundary_in_bytes_ascii_below_exact_above` | none | PASS |
| L4 | Rendered value 1,048,576 bytes, quotes counted | R | C§5 | n/a | same | CLOSED | `run::test_value_boundary_counts_the_rendered_quotes_in_bytes_ascii` | none | PASS |
| L5 | Multibyte: 524,288 `é` = exactly 1 MiB on a channel; 524,287 `é` + quotes = exactly 1 MiB rendered; one more is over although far fewer characters than the limit | R | C§5 | n/a | bytes, not characters | CLOSED | `run::test_channel_limit_counts_utf8_bytes_not_characters`; `run::test_value_boundary_counts_utf8_bytes_not_characters` | none | PASS |
| L6 | Diagnostic 65,536 bytes: messages are fixed server strings, so the bound cannot be approached | R | C§5 | n/a | constant size regardless of input | N/A | `run::test_diagnostic_limit_does_not_apply_because_messages_are_fixed` | not a boundary that exists in practice | NOT APPLICABLE |
| L7 | Aggregate 3,276,800 bytes measured on the encoded envelope: one below / exact / one above | R | C§5 | n/a | `result_limit` above | CLOSED | `run::test_aggregate_result_boundary_is_measured_on_the_encoded_envelope_bytes` | none | PASS |
| L8 | Output is enforced incrementally: a runaway writer is stopped at the limit, long before the deadline; the stream drops partial data at once and never holds more than its limit | R | C§5 | n/a | `result_limit` in about 1.5 s | CLOSED | `run::test_runaway_output_is_stopped_at_the_limit_not_accumulated_until_the_deadline`; `run::test_bounded_stream_never_retains_more_than_its_limit_and_discards_on_overflow`; `e3sup::test_oversized_reply_is_killed_and_internal_error`; `e3sup::test_mux_applies_back_pressure_instead_of_unbounded_buffering` | rendering cannot be bounded incrementally [H30]: bounded by the deadline, `RLIMIT_AS` and a post check | PASS |
| L9 | Limits behave identically with the namespace granted or denied | H | E28-3 §5 | n/a | identical envelopes | EXACT | `run::test_namespace_mode_does_not_change_limit_behavior` | none | PASS |

## A — Authority denial

Each layer is a different claim and is tested separately. **static policy**: the raw parser AST is
rejected before anything runs (`policy_denied`). **unavailable binding**: the default-deny pruned
environment lacks the name. **runtime stub**: process creation, sockets and module loading are
stubbed in the worker. **host/OS**: rlimits and, where verified, a network namespace (defense in
depth; cited, not re-proved here). 55 attempts in `AUTHORITY` plus every one of the 39 denied names
and autoloads.

| ID | Authority | Class | Authority source | Layers asserted | Direct | MCP | Evidence | Host limitations | Status |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Filesystem read (file, zip, resource) | S | C§4 | static policy; pruned binding; runtime (policy off) | allowed | `policy_denied`, file never read | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | none | PASS |
| A2 | Filesystem write | S | C§4 | same; marker file proves no effect | allowed | `policy_denied`, marker absent | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | none | PASS |
| A3 | Environment | S | C§4 | same; the worker environment is a fixed allowlist with no `PATH`/`HOME` | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled`; `e3sup::test_worker_environment_is_a_fixed_minimal_allowlist` | Genia reaches the environment only through the R10/R13 configuration surface | PASS |
| A4 | Configuration (R10/R13 providers, `lifecycle_config`) | S | C§4 | same | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | none | PASS |
| A5 | Secrets | S | C§4 | same | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | none | PASS |
| A6 | Declassification | S | C§4, C§6 | same | privileged host operation | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | none | PASS |
| A7 | Outbound network / HTTP | S | C§4 | static policy (`http_operation`, `_http_send`, `import web`); pruned binding; network namespace where verified | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled`; `e3sup::test_network_namespace_is_used_only_when_verified_and_then_isolates`; `e3sup::test_namespace_wrapper_is_not_used_when_the_probe_fails` | the namespace is best effort | PASS |
| A8 | Server / listener | S | C§4 | static policy; pruned binding; annotation forms inert and open no listener | allowed | `policy_denied` / inert | `security::test_static_policy_denies_every_authority_at_the_wire`; `security::test_annotation_forms_are_inert_and_open_no_listener`; `e4launch::test_no_process_in_the_chain_holds_a_listening_socket`; `e4cfg::test_no_mcp_host_module_or_the_native_app_can_open_a_listener` | none | PASS |
| A9 | Socket | S | C§4 | **no Genia binding exists**; Python socket calls stubbed in the worker; namespace where verified | n/a | unavailable (`runtime_error`) | `security::test_authority_with_no_genia_binding_at_all_is_unavailable_not_stubbed`; `e3wrk::test_runtime_stubs_deny_process_creation_and_sockets_and_are_restored` | the stub is a backstop beneath policy and pruning | PASS |
| A10 | Shell stage `$(...)` | S | C§4, [H28] | static policy; runtime stub (no binding to prune); marker proves no effect | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled`; `e3wrk::test_runtime_process_creation_is_stubbed_even_without_policy` | none | PASS |
| A11 | External process (`execution.process`) | S | C§4 | static policy; pruned binding; runtime stub | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | `spawn` is an in-language Process (a worker-local thread), not a host process | PASS |
| A12 | `import` | S | C§4 | static policy; runtime stub of module loading | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | none | PASS |
| A13 | `load` | S | C§4 | no Genia binding exists (unavailable) | n/a | `runtime_error` | `security::test_authority_with_no_genia_binding_at_all_is_unavailable_not_stubbed` | none | PASS |
| A14 | stdin | S | C§4 | binding exists and is an immediate-EOF source (inert, not denied); terminal input is denied | EOF in tests | `[]`; `input`/`stdin_keys` `policy_denied` | `security::test_inert_bindings_are_available_but_grant_nothing`; `run::test_mcp_equals_direct_command_source_evaluation_exactly` | none | PASS |
| A15 | argv | S | C§4 | binding exists; empty list | `[]` | `[]` | `security::test_inert_bindings_are_available_but_grant_nothing` | none | PASS |
| A16 | Model provider | S | C§4 | static policy; pruned binding | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | none | PASS |
| A17 | Retrieval providers (`embed`, `retrieve`, `rerank`) | S | C§4 | same | allowed | `policy_denied` | `security::test_static_policy_denies_every_authority_at_the_wire` *(ns)*; `security::test_static_policy_rejects_the_raw_ast_before_any_evaluation`; `security::test_runtime_layer_alone_still_denies_when_policy_is_disabled` | none | PASS |
| A18 | Complete deny list: every denied binding and autoload is rejected statically **and** absent after pruning **and** unbound at runtime | S | [H24] | all three | n/a | n/a | `security::test_every_denied_binding_and_autoload_is_unavailable_after_pruning`; `security::test_every_denied_name_is_rejected_statically_and_unbound_at_runtime`; `e3wrk::test_every_binding_and_autoload_is_explicitly_classified` | a user definition that only *defines* a denied name is not rejected; any reference is | PASS |
| A19 | Indirection (`eval`, `lookup`) cannot reach a denied name | S | [H24] | static policy; pruned child environment | n/a | `policy_denied` / `runtime_error` | `security::test_static_policy_denies_every_authority_at_the_wire`; `security::test_authority_with_no_genia_binding_at_all_is_unavailable_not_stubbed`; `e3wrk::test_indirection_cannot_reach_prohibited_authority` | none | PASS |
| A20 | Outcomes identical with the namespace granted or denied | H | E28-3 §5 | wire | n/a | identical | `security::test_authority_outcomes_are_identical_with_the_namespace_granted_or_denied` | none | PASS |
| A21 | Host/OS defense in depth: rlimits (`FSIZE`=0, `CPU`, `NOFILE`, `CORE` on every platform; `AS` on Linux, absent on macOS by design; see section M) | H | E28-3 §5 | process limits | n/a | n/a | `e3wrk::test_worker_applies_process_limits` | not a sandbox | PASS |
| A22 | Process/network namespace: optional, verified once at host initialization, claimed nowhere | H | E28-3 §5, [H33] | probe | n/a | n/a | `e3run::test_isolation_probe_runs_once_during_initialization_before_readiness`; `e3run::test_denied_namespace_degrades_honestly_and_runs_still_work`; `e3run::test_hanging_probe_is_bounded_at_startup_and_runs_degrade_to_unwrapped_workers` | availability depends on the host; hardened CI hosts deny it [H35] | PASS |

## S — Protected values and redaction

MCP provisions no provider, so a protected carrier can only be reached by host injection. The tests
bind a carrier `CARRIER` (sentinel `SENTINEL-ZQ9-7731-PROTECTED`) through a test-only wrapper around
the **unmodified** production worker and drive the real native server, supervisor, policy and renderer.
The sentinel and its fragments (`SENTINEL`, `ZQ9`, `7731`) must not appear anywhere in the complete
response or in the raw stdout bytes of the session, for 61 programs.

| ID | Path | Class | Authority | Behavior | Evidence | Status |
|---|---|---|---|---|---|---|
| S1 | Final rendered value (bare, nested in lists, maps, Outcomes, lazy collect) | S | C§6 | `policy_denied`, fixed message, no partial data | `security::test_no_protected_fragment_appears_anywhere_in_the_response`; `security::test_protected_results_are_fixed_envelopes_with_no_partial_data`; `e3wrk::test_protected_carrier_in_the_result_is_policy_denied_with_no_partial_fields` | PASS |
| S2 | stdout (`print`, `write`, `log`, lists) | S | C§6 | runtime refusal, fixed `runtime_error` | `security::test_protected_results_are_fixed_envelopes_with_no_partial_data` | PASS |
| S3 | stderr | S | C§6 | runtime refusal, fixed `runtime_error` | `security::test_protected_results_are_fixed_envelopes_with_no_partial_data` | PASS |
| S4 | Error messages and diagnostics: the sentinel placed in the **source** is never echoed by `parse_error`, `policy_denied` or `runtime_error` | S | C§2.2, C§6 | fixed messages | `security::test_no_protected_fragment_appears_anywhere_in_the_response` | PASS |
| S5 | Exception normalization (`error(CARRIER)`, type errors, calls, assertions, failures after touching the carrier) | S | C§6 | fixed `runtime_error` | `security::test_no_protected_fragment_appears_anywhere_in_the_response`; `security::test_protected_results_are_fixed_envelopes_with_no_partial_data` | PASS |
| S6 | Declassification, representation and equality oracles | S | C§6 | refused; equality against the secret text is `false`; identity equality reveals nothing | `security::test_declassification_and_representation_attempts_do_not_reveal_anything` | PASS |
| S7 | Display and debug rendering | S | R10 | `"<protected>"` only | `security::test_the_substituted_worker_really_carries_a_protected_value`; `security::test_no_protected_fragment_appears_anywhere_in_the_response` | PASS |
| S8 | JSON encoding (`json_encode`, `json_stringify`, `json_pretty`) | S | R9/R10 | existing `protected-value` refusal Outcome | `security::test_serializers_refuse_a_protected_value_with_a_fixed_outcome` | PASS |
| S9 | Outcome values (`some`, `err`, `or_else`, `unwrap_or`) | S | C§6 | `policy_denied` | `security::test_protected_results_are_fixed_envelopes_with_no_partial_data` | PASS |
| S10 | Cancellation, timeout, channel-limit and aggregate-limit paths; internal-error worker text | S | C§5, C§6 | fixed envelopes, no sentinel in any byte | `security::test_protected_value_on_the_timeout_path_leaks_nothing`; `security::test_protected_value_on_the_cancellation_path_leaks_nothing`; `security::test_protected_value_on_the_result_limit_path_leaks_nothing`; `security::test_protected_value_on_the_aggregate_limit_path_leaks_nothing`; `run::test_internal_error_is_fixed_and_leaks_nothing_of_the_worker` | PASS |

## X — Cancellation

First terminal state wins. Races assert the invariant (exactly one whole terminal state, nothing
partial, nothing surviving), never a particular winner. Synchronization is the readiness barrier plus
bounded observable polling.

| ID | Case | Class | Evidence | Status |
|---|---|---|---|---|
| X1 | Cancel queued with the request | R | `lifecycle::test_cancel_queued_with_the_request_wins_and_the_worker_is_reaped` *(ns)*; `e3run::test_cancel_queued_with_the_request_cancels_without_a_surviving_worker` | PASS |
| X2 | Cancel during evaluation; no partial data; private directory removed | R | `lifecycle::test_cancel_during_evaluation_returns_no_partial_data_and_removes_the_workdir` *(ns)*; `e3run::test_cancel_immediately_after_worker_creation_cancels_and_reaps` | PASS |
| X3 | Wrong id, missing/null `requestId`, no params, string id for an integer request, cancel sent as a request | R | `lifecycle::test_a_cancel_that_does_not_name_the_running_request_is_ignored`; `e3run::test_cancel_for_another_request_id_is_ignored` | PASS |
| X4 | Cancel after completion is ignored; the server continues | R | `e3run::test_cancel_after_completion_is_ignored_and_the_server_continues`; `e3sup::test_finished_worker_result_wins_over_a_later_cancel` | PASS |
| X5 | Multiple cancellations: one `cancelled`, stale duplicates never cancel a later request | R | `lifecycle::test_duplicate_cancellations_cancel_exactly_once_and_never_a_later_request` | PASS |
| X6 | Cancel near the deadline: exactly one of `cancelled`/`timeout`, never both, never neither | R | `lifecycle::test_cancellation_near_the_deadline_yields_exactly_one_terminal_state` | PASS |
| X7 | Cancel near successful completion: whole success or fixed `cancelled` | R | `lifecycle::test_cancellation_near_successful_completion_yields_exactly_one_whole_terminal_state` | PASS |
| X8 | Subsequent request after cancellation works | R | `lifecycle::test_duplicate_cancellations_cancel_exactly_once_and_never_a_later_request`; `e3run::test_other_requests_during_a_run_are_answered_in_order_after_it` | PASS |
| X9 | Worker reaped (an unreaped zombie counts as alive); temp directory removed | R | `lifecycle::test_cancel_during_evaluation_returns_no_partial_data_and_removes_the_workdir`; `lifecycle::test_no_worker_remains_after_a_mixed_session_of_every_terminal_state`; `e3sup::test_cancel_during_bootstrap_cancels_and_reaps` | PASS |
| X10 | The official client's own abort cancels the run well inside the deadline | P | `client::test_the_official_client_matrix_covers_cancel_disconnect_and_relaunch` | PASS |

## T — Timeout

| ID | Case | Class | Evidence | Status |
|---|---|---|---|---|
| T1 | Fixed 5,000 ms deadline; response never earlier | R / D | `e3run::test_deadline_returns_timeout_and_reaps_the_worker`; `lifecycle::test_timeout_is_fixed_closed_partial_free_and_the_next_request_still_works` *(ns)*; `e3sup::test_default_deadline_is_the_fixed_5000_ms_profile_value` | PASS |
| T2 | The deadline starts at worker readiness, not at interpreter launch | R | `e3sup::test_deadline_is_measured_from_readiness_not_from_spawn`; `e3sup::test_slow_bootstrap_is_not_charged_against_the_execution_deadline`; `e3run::test_slow_worker_launch_is_not_charged_against_the_5000_ms_deadline` | PASS |
| T3 | Bootstrap has its own 30 s bound; a worker that never becomes ready is `internal_error` | R | `e3sup::test_worker_that_never_becomes_ready_is_internal_error_after_the_startup_limit` | PASS |
| T4 | Timeout kills and reaps the worker's process group (children die with it) | R | `e3sup::test_worker_children_die_with_the_worker`; `lifecycle::test_other_unbounded_programs_are_bounded_by_the_same_fixed_deadline` | PASS |
| T5 | No partial channel escapes; the next request still works | R | `lifecycle::test_timeout_is_fixed_closed_partial_free_and_the_next_request_still_works` *(ns)* | PASS |
| T6 | Busy loop, long sleep, unbounded Flow without output | R | `e3run::test_deadline_returns_timeout_and_reaps_the_worker`; `lifecycle::test_other_unbounded_programs_are_bounded_by_the_same_fixed_deadline` | PASS |
| T7 | Slow host load and namespace probing are not charged to a request | R / H | `e3sup::test_request_time_does_not_include_any_probe_work`; `e3run::test_isolation_probe_runs_once_during_initialization_before_readiness` | PASS |
| T8 | The 5,000 ms value was not changed to make any test pass | R | `e3sup::test_default_deadline_is_the_fixed_5000_ms_profile_value` | PASS |

## Y — Lifecycle and leaks

| ID | Event | Class | Evidence | Status |
|---|---|---|---|---|
| Y1 | Normal EOF: idle exit 0; in-flight run finishes, then exit | R | `e4life::test_closing_stdin_while_idle_exits_cleanly_and_leaves_nothing`; `e4life::test_closing_stdin_mid_run_lets_the_run_finish_then_exits` | PASS |
| Y2 | Client disconnect (both streams closed mid-run) | R | `e4life::test_a_client_that_closes_both_streams_mid_run_leaves_no_survivors`; `client::test_the_official_client_matrix_covers_cancel_disconnect_and_relaunch` | PASS |
| Y3 | SIGTERM / SIGINT to the client-launched process stop the whole chain and clean up | R | `e4life::test_a_signal_to_the_client_launched_process_stops_the_entire_chain_and_cleans_up` | PASS |
| Y4 | SIGHUP to the client-launched process: worker reaped and private directory removed (this row found [H41]) | R | `lifecycle::test_sighup_to_the_client_launched_process_stops_the_chain_and_cleans_up` | PASS |
| Y5 | Host SIGTERM mid-run: worker killed and reaped, directory removed | R | `lifecycle::test_sigterm_to_the_host_mid_run_reaps_the_worker_and_removes_its_directory` *(ns)*; `e4life::test_sigterm_to_the_host_reaps_the_worker_and_removes_its_directory` | PASS |
| Y6 | Worker cancellation, timeout and output overflow leave no worker and no directory | R | `lifecycle::test_cancel_during_evaluation_returns_no_partial_data_and_removes_the_workdir`; `lifecycle::test_timeout_is_fixed_closed_partial_free_and_the_next_request_still_works`; `lifecycle::test_overflow_kills_the_worker_and_removes_its_private_directory` | PASS |
| Y7 | Every terminal state in one session leaves no extra process | R | `lifecycle::test_no_worker_remains_after_a_mixed_session_of_every_terminal_state` | PASS |
| Y8 | Repeated launches; discover probe followed by session launch | R | `lifecycle::test_a_discover_probe_launch_followed_by_a_session_launch_leaves_nothing_behind`; `e4launch::test_a_client_can_launch_twice_in_a_row_and_get_the_same_answers`; `client::test_the_official_client_matrix_covers_cancel_disconnect_and_relaunch` | PASS |
| Y9 | Orphan backstop: a worker whose host was SIGKILLed ends itself after 8 s | R / H | `e4life::test_a_worker_with_no_supervisor_ends_itself_after_the_backstop` | PASS |
| Y10 | SIGKILL of the host may leave an **empty private temp directory** (not claimed otherwise) | L | `e4life::test_a_worker_with_no_supervisor_ends_itself_after_the_backstop` (documents the bound) | KNOWN LIMITATION |

## N — Namespace available / denied

| ID | Case | Evidence | Status |
|---|---|---|---|
| N1 | Every *(ns)* row above runs with the host's real namespace behavior and with `unshare` simulated as denied (a fake `unshare` that fails like a hardened CI host) | `run::test_namespace_mode_does_not_change_limit_behavior`; `surface::test_capabilities_are_byte_identical_whether_the_namespace_is_granted_or_denied`; `security::test_authority_outcomes_are_identical_with_the_namespace_granted_or_denied` | PASS |
| N2 | The whole R28 suite runs under `GENIA_R28_TEST_DENY_NAMESPACE=1` | recorded in the E28-5 report; the switch is `tests/fixtures/r28_mcp_helpers.py` | PASS |
| N3 | A failed probe means workers run without the namespace and nothing claims it | `e3run::test_denied_namespace_degrades_honestly_and_runs_still_work`; `e3sup::test_failed_probe_leaves_requests_working_without_a_namespace` | PASS |

## O — Official TypeScript client (SDK 2.2.0; negotiation `auto`, legacy/default, and a `2026-07-28` pin)

Credential-free; the command comes from the checked-in `.mcp.json`; harness `tools/mcp_acceptance/`;
CI job `mcp-client-acceptance`.

| ID | Step | Evidence | Status |
|---|---|---|---|
| O1–O12 | `discover`, `tools`, `schemas`, `capabilities`, `parse_invalid`, `parse_valid`, `parse_repair_run`, `run` (value/stdout/stderr/exit code distinct), `run_failing`, `framing` (hostile output incl. Unicode separators and a cancel lookalike), `authority` (8 denied authorities), `sequential` (12 calls), `cancel` (client abort), `disconnect` (no process survives), `relaunch` (clean shutdown) | `client::test_the_official_client_completes_the_acceptance_scenario`; `client::test_the_official_client_matrix_covers_cancel_disconnect_and_relaunch` | PASS |
| O-N | Negotiation modes, each recording the negotiated protocol version: SDK default and `legacy` connect with `2025-11-25` (via `initialize`); `auto` and `{pin: '2026-07-28'}` connect with `2026-07-28`; all list exactly the three tools | `client::test_version_negotiation_evidence_for_ledger_h36`; `client::test_the_official_client_completes_the_scenario_on_every_negotiation_path` | PASS |
| O-E | The complete acceptance scenario (discovery, parse, run, failures, authority, cancel, disconnect, relaunch) passes on the default `auto`, legacy, SDK-default, and pinned paths | `client::test_the_official_client_completes_the_acceptance_scenario`; `client::test_the_official_client_completes_the_scenario_on_every_negotiation_path` | PASS |

## Z — Limitations, deferrals, and items for E28-6

| ID | Item | Class | Evidence / record | Status |
|---|---|---|---|---|
| Z1 | The debug renderer shows Python-level text for callable values (`<function ... at 0x...>`, `GeniaFunctionGroup(...)`): it cannot expose a protected value, does not enter any deterministic comparison, and equals ordinary command mode | L | `security::test_callable_renderings_are_host_representations_and_never_carry_a_protected_value`; `security::test_callable_rendering_is_host_text_and_equals_ordinary_command_mode_shape`; ledger [H32] | KNOWN LIMITATION |
| Z2 | Clients that send `initialize` for a revision other than `2025-11-25` (for example `2025-06-18`) cannot connect: the closed two-version policy rejects them with `data.supported` | L | ledger [H36]; `compat::test_any_other_version_is_rejected_never_negotiated_down_and_leaves_the_state_new` | KNOWN LIMITATION |
| Z3 | VS Code / GitHub Copilot acceptance: run 1 (failed at `initialize`) and run 2 (failed at `genia_run` on macOS) are preserved; **run 3 passed** (authentic, macOS; manual, not in CI) | L | ledger [H39]; `docs/mcp/acceptance/vscode-copilot-evidence.md`; `gate::test_run_1_is_preserved_as_the_authentic_failure_that_triggered_amendment_a5`; `gate::test_run_3_is_the_authentic_passing_acceptance_run` | PASS |
| Z4 | Streamable HTTP parity | — | deferred by C§7 and C§9.3: no listener, no HTTP test | NOT APPLICABLE |
| Z5 | C++ MCP parity | — | no C++ MCP implementation or parity claim | NOT APPLICABLE |
| Z6 | Static boundaries: no Python MCP application architecture, no SDK dependency in the server, no listener, no machine-specific `.mcp.json` | P | `arch::test_no_python_module_defines_mcp_application_literals`; `arch::test_no_mcp_sdk_import_or_dependency`; `e4cfg::test_no_python_mcp_sdk_is_a_dependency`; `e4cfg::test_the_configuration_contains_no_secret_absolute_path_or_machine_detail`; `e4cfg::test_the_configuration_enables_no_http_transport` | PASS |

## K — The 2025-11-25 compatibility era (amendment A5, issue #707)

Pre-flight: `docs/design/r28-e28-6-protocol-compat-preflight.md`. Each row below is run in the compat era;
the `compatconf` rows run the same corpora as the modern rows and compare envelopes.

| ID | Behavior | Class | Evidence | Status |
|---|---|---|---|---|
| K1 | The exact `initialize` VS Code 1.138.0 sent (authentic run 1) now succeeds with exactly `{protocolVersion, capabilities: {tools: {}}, serverInfo}` and nothing for the notification | P | `compat::test_the_exact_vscode_initialize_from_the_first_authentic_run_now_succeeds`; `compat::test_initialize_result_is_exactly_version_tools_capability_and_identity` | PASS |
| K2 | Closed version policy: every other version (`2025-06-18`, `2025-03-26`, `2024-11-05`, `2026-07-28`, empty, garbage) is `-32602` with `data.supported`; never negotiated down; state stays NEW | P | `compat::test_any_other_version_is_rejected_never_negotiated_down_and_leaves_the_state_new` | PASS |
| K3 | Malformed, missing, non-object, unusable-id, and id-less `initialize` | P | `compat::test_a_malformed_initialize_is_invalid_params_and_leaves_the_state_new`; `compat::test_an_initialize_missing_a_required_member_is_invalid_params`; `compat::test_an_initialize_with_non_object_or_absent_params_is_invalid_params`; `compat::test_an_initialize_with_an_unusable_id_is_an_invalid_request`; `compat::test_initialize_without_an_id_is_a_notification_with_no_response_and_no_state_change` | PASS |
| K4 | One-bit state: pre-initialize requests `-32602`, duplicate `initialize` `-32600`, `notifications/initialized` silent and effect-free, state never survives a launch | P | `compat::test_requests_before_initialize_are_invalid_params_exactly_as_before_the_amendment`; `compat::test_after_initialize_the_requests_are_served_and_a_second_initialize_is_invalid`; `compat::test_the_initialized_notification_is_accepted_silently_in_every_state_and_changes_nothing`; `compat::test_the_state_is_per_process_and_never_survives_a_launch`; `compat::test_the_initialization_state_is_one_process_local_cell_in_native_genia` | PASS |
| K5 | `ping` is `{}` in every state; every other method (resources, prompts, completion, logging, tasks, roots, sampling, elicitation) is `-32601` | P | `compat::test_ping_answers_an_empty_result_in_every_state`; `compat::test_every_other_method_is_method_not_found_before_and_after_initialize` | PASS |
| K6 | Same tools (four since A6), identical descriptors and order, no resources, prompts, or pagination; compat tool results carry exactly `content`, `structuredContent`, `isError` | P | `compat::test_the_compat_era_lists_exactly_the_same_three_tools_with_identical_descriptors`; `compat::test_the_compat_era_advertises_no_resources_or_prompts_and_no_pagination`; `compat::test_a_compat_tools_call_result_has_exactly_content_structuredcontent_and_iserror` | PASS |
| K7 | `genia_capabilities` reports the serving era and is otherwise identical across eras | P | `compat::test_capabilities_report_the_serving_protocol_revision_and_are_otherwise_identical_across_eras` | PASS |
| K8 | Client capabilities (roots, sampling, elicitation, tasks, extensions) grant no authority: identical results for empty, VS Code, and maximal capabilities; the server sends nothing unsolicited; client values are never reflected | S | `compat::test_results_are_identical_whatever_capabilities_the_client_advertises`; `compat::test_the_server_never_sends_a_request_or_notification_to_a_client_that_advertises_everything`; `compat::test_client_supplied_values_are_validated_for_shape_and_never_reflected_or_stored`; `compat::test_the_native_program_names_no_server_to_client_method_or_client_capability_behavior`; `compatconf::test_advertising_every_client_capability_widens_no_authority` | PASS |
| K9 | Era selection and coexistence: the `_meta` version key always selects the modern path; modern errors and `-32022` unchanged | P | `compat::test_a_request_with_the_modern_meta_is_always_a_modern_request_even_after_initialize`; `compat::test_a_malformed_modern_meta_is_invalid_params_in_every_state`; `compat::test_the_modern_unsupported_version_error_is_unchanged`; `compatconf::test_both_eras_may_interleave_in_one_session_without_cross_effects` | PASS |
| K10 | Both eras converge on one execution model: identical run and parse envelopes over the shared corpora, all failure classes, channels, hostile output | A | `compatconf::test_run_envelopes_are_identical_in_both_eras`; `compatconf::test_parse_envelopes_are_identical_in_both_eras`; `compatconf::test_the_compat_corpus_covers_success_and_every_failure_class_it_names`; `compatconf::test_stdout_stderr_and_value_stay_separate_channels_in_the_compat_era`; `compatconf::test_hostile_program_output_is_data_never_protocol_framing_in_the_compat_era` | PASS |
| K11 | Authority denial in the compat era: every attempt in `AUTHORITY` is `policy_denied` with no effect | S | `compatconf::test_every_one_of_the_authority_attempts_is_policy_denied_in_the_compat_era` | PASS |
| K12 | Limits and protected values in the compat era | S | `compatconf::test_source_limit_is_in_utf8_bytes_in_the_compat_era`; `compatconf::test_output_limits_close_with_no_partial_data_in_the_compat_era`; `compatconf::test_protected_values_never_cross_the_wire_in_the_compat_era` | PASS |
| K13 | Timeout and cancellation (queued, mid-run, wrong id, duplicate) in the compat era, namespace granted and denied | R | `compatconf::test_timeout_is_the_same_closed_failure_and_the_session_survives_in_the_compat_era`; `compatconf::test_cancellation_mid_run_returns_no_partial_data_and_reaps_the_worker_in_the_compat_era`; `compatconf::test_a_cancel_queued_with_its_request_wins_in_the_compat_era` | PASS |
| K14 | Lifecycle in the compat era: disconnect after `initialize`, repeated connections, failed-then-good initialize, SIGTERM mid-run; no orphan workers, no stale state | R | `compatconf::test_a_client_disconnect_after_initialize_leaves_nothing_behind`; `compatconf::test_repeated_connections_each_start_new_and_are_independent`; `compatconf::test_a_failed_initialize_then_a_good_one_still_works_and_runs_cleanly`; `compatconf::test_sigterm_mid_run_in_a_compat_session_reaps_the_worker` | PASS |
| K15 | Architecture: no Python host module owns `initialize`, `ping`, protocol-version literals, or capability handling; the launcher is unchanged | P | `compat::test_no_python_host_module_gains_initialize_ping_or_any_protocol_version_literal`; `compat::test_the_launcher_and_host_are_unchanged_by_the_amendment` | PASS |

## M — Platform portability (macOS governed execution, ledger R28-H47)

Pre-flight: `docs/design/r28-e28-6-macos-execution-preflight.md`. Linux is verified in CI and macOS by the owner (not in CI).
The M1-M5 rows pass here on Linux by *simulation* (a kernel that rejects `RLIMIT_AS`, and the `ps`/`lsof` process backend run
on Linux); real macOS results are the owner's.

| ID | Behavior | Class | Evidence | Status |
|---|---|---|---|---|
| M1 | A kernel that rejects `RLIMIT_AS` (Darwin) does not break `genia_run`: completed, parse, policy, runtime, and channel outcomes are all served | H | `port::test_a_darwin_kernel_rejecting_the_address_space_bound_does_not_break_every_run`; `port::test_discovery_and_parse_working_while_every_run_fails_cannot_recur_on_a_darwin_like_host` | PASS (simulated) |
| M2 | Every other limit, and `RLIMIT_AS` on Linux, fails closed with `internal_error` (never runs without a bound) | S | `port::test_the_same_rejection_on_linux_fails_closed_for_every_run`; `port::test_a_rejected_portable_limit_fails_closed_on_every_platform`; `port::test_linux_still_applies_the_address_space_bound_and_fails_if_it_cannot` | PASS |
| M3 | The portable limits are still applied when `RLIMIT_AS` is rejected; one platform decision, one tolerated limit | S | `port::test_a_rejected_address_space_bound_on_darwin_does_not_skip_the_portable_limits`; `port::test_only_the_address_space_bound_is_tolerated_and_only_on_darwin` | PASS |
| M4 | The development diagnostic names an internal failure only on the worker's own stderr, only when asked, and never on the wire | S | `port::test_the_worker_names_an_internal_failure_on_its_own_stderr_only_when_asked`; `port::test_the_supervisor_never_forwards_the_diagnostic_switch_and_the_wire_stays_sanitized`; `port::test_the_probe_reproduces_the_production_path_and_localizes_a_failure` | PASS |
| M5 | The lifecycle observation backend (`ps`/`lsof` where there is no `/proc`) sees descendants, command lines, identities, zombies, working directories, the governed worker, and listeners; the lifecycle suite also runs on the `ps` backend | R | `port::test_the_backend_sees_descendants_their_command_lines_and_identities`; `port::test_the_backend_counts_an_unreaped_zombie_as_alive`; `port::test_the_backend_reads_a_processs_working_directory`; `port::test_the_backend_finds_the_governed_worker_of_a_live_session_and_proves_cleanup`; `port::test_the_backend_sees_no_listener_for_the_launcher_chain`; `port::test_the_default_backend_is_proc_where_it_exists_and_ps_otherwise` | PASS |
| M6 | Real macOS execution of the governed worker: the whole R28/MCP suite passes on a Mac (`1141 passed, 18 skipped, 0 failed` at `d0e4f2a4`; Linux-only namespace tests skip there), and authentic VS Code ran the canonical demo through `genia_run` (run 3) | R | ledger [H47], [H48]; `gate::test_run_3_is_the_authentic_passing_acceptance_run`; `port::test_the_governed_worker_is_recognized_by_its_command_line_on_every_platform`; `port::test_the_process_probe_reports_how_this_platform_shows_the_governed_worker` | PASS (owner-run, not in CI) |
| M8 | The launcher path decodes invalid UTF-8 as a `-32700` parse error under any locale's stdin handler; plain file mode depends on it (pinned for tests); the namespace probe never runs off Linux | S | `port::test_the_launcher_path_decodes_invalid_utf8_the_same_whatever_the_locales_stdin_handler_is`; `port::test_plain_file_mode_depends_on_the_locales_stdin_decoder_which_is_pinned_for_the_tests`; `port::test_the_namespace_probe_runs_only_on_linux` | PASS |
| M7 | macOS has no address-space bound and no network namespace (not claimed) | L | ledger [H47]; `docs/design/r28-e28-6-macos-execution-preflight.md` | KNOWN LIMITATION |

## E — E28-6 additions (demo, entrypoint, release gate)

| ID | Item | Class | Evidence | Status |
|---|---|---|---|---|
| E1 | The canonical validated-record demo: broken program → `parse_error` at the defect → repair → parse → run with value, stdout, stderr separate; equal to direct evaluation; deterministic; documented text equals the example files | A / P | `demo::test_the_documented_sources_are_exactly_the_example_programs`; `demo::test_the_broken_program_gets_a_structured_diagnostic_at_the_defect`; `demo::test_the_repaired_program_parses_runs_and_matches_direct_evaluation`; `demo::test_the_run_separates_value_stdout_and_stderr_as_documented`; `demo::test_the_whole_walkthrough_works_in_one_session` | PASS |
| E2 | The demo uses no authority the governed profile denies and the walkthrough needs no repository-internal knowledge | S | `demo::test_the_demo_uses_no_authority_the_governed_profile_denies`; `demo::test_the_walkthrough_is_self_contained_for_a_first_time_user` | PASS |
| E3 | `scripts/genia-mcp` starts the same launcher from any directory with no arguments and no stderr noise; packaging unchanged | H | `entry::test_the_entrypoint_works_from_any_working_directory`; `entry::test_the_entrypoint_takes_no_arguments`; `entry::test_packaging_is_unchanged_no_new_cli_command_and_no_published_package_claim` | PASS |
| E4 | Official MCP Inspector 2.9.0 (CLI): the default era connects (`2025-11-25`) and `--protocol-era auto` connects (`2026-07-28`); both listed exactly three tools (the surface before A6) and ran `genia_run` | P | manually executed (E28-6 audit and after amendment A5); not automated; web and terminal UIs not executed; recorded in ledger [H36] | KNOWN LIMITATION |
| E5 | The release-completion gate: no "R28 complete" claim unless the latest VS Code/Copilot run is executed, complete, secret-free, and `PASS` on a negotiation path the amended contract allows | P | `gate::test_no_authoritative_document_claims_r28_complete_unless_the_evidence_allows_it`; `gate::test_the_ledger_keeps_h39_and_h47_open_until_the_evidence_is_released`; `gate::test_an_executed_passing_run_is_complete_secret_free_and_consistent` | PASS |
| E6 | Authentic VS Code + GitHub Copilot run (contract section 12.2): run 3 passed (macOS; manual, not in CI) | P | ledger [H39]; `docs/mcp/acceptance/vscode-copilot-evidence.md` (`evidence run=3`); `gate::test_run_3_is_the_authentic_passing_acceptance_run` | PASS |
