"""Canonical documentation metadata for Python-host callable bindings.

Generated reference pages are consumers of this registry, never sources of truth.
Entries with ``stability == "internal"`` are trusted/runtime bridges and are not
part of the public function-documentation surface.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HostBuiltinDoc:
    name: str
    doc: str
    category: str
    stability: str
    signatures: tuple[str, ...]
    since: str | None = None
    deprecated: str | None = None
    see_also: tuple[str, ...] = ()


def _public(
    name: str,
    doc: str,
    category: str,
    *signatures: str,
    stability: str = "Stable",
    see_also: tuple[str, ...] = (),
) -> HostBuiltinDoc:
    return HostBuiltinDoc(name, doc, category, stability, tuple(signatures), see_also=see_also)


_PUBLIC_DOCS = (
    _public("Format", "Construct a tagged representation template.", "Value templates", "Format(template, tag)", stability="Experimental"),
    _public("apply_raw", "Call a function with a list of positional arguments without automatic absence propagation.", "Function helpers", "apply_raw(function, arguments)"),
    _public("argv", "Return the trailing command-line arguments as a list of strings.", "CLI", "argv()"),
    _public("assert_eq", "Assert that two values are equal.", "Testing", "assert_eq(actual, expected)", stability="Experimental"),
    _public("assert_true", "Assert that a value is true.", "Testing", "assert_true(value)", stability="Experimental"),
    _public("car", "Return the first value of a pair.", "Pairs", "car(pair)"),
    _public("cdr", "Return the second value of a pair.", "Pairs", "cdr(pair)"),
    _public("chunk", "Construct exact ordered chunks from a validated document and chunker callback.", "Retrieval", "chunk(chunker, document)", stability="Experimental"),
    _public("collect_sheet", "Collect homogeneous map records into an immutable Sheet.", "Sheets", "collect_sheet(records)", stability="Experimental"),
    _public("collect_validated", "Collect Outcome values into clean values and diagnostics.", "Validation", "collect_validated(results)", stability="Experimental"),
    _public("columns", "Return a Sheet's column names in deterministic order.", "Sheets", "columns(sheet)", stability="Experimental"),
    _public("config_args", "Normalize explicit program arguments into an R10 values-source descriptor.", "Configuration", "config_args(arguments)", stability="Experimental"),
    _public("config_get", "Read and validate one configuration value through a provider.", "Configuration", "config_get(provider, key)", stability="Experimental"),
    _public("config_get_or", "Read and validate one configuration value or use an explicit default.", "Configuration", "config_get_or(provider, key, default)", stability="Experimental"),
    _public("config_provider", "Construct an ordinary configuration provider from an explicit source.", "Configuration", "config_provider(source)", stability="Experimental"),
    _public("config_standard", "Construct the conventional ordered configuration provider snapshot.", "Configuration", "config_standard(overrides, arguments)", "config_standard(overrides, arguments, dotenv_path)", stability="Experimental"),
    _public("config_view", "Construct a qualified configuration lookup callable over an explicit provider.", "Configuration", "config_view(provider, prefix)", stability="Experimental"),
    _public("cons", "Construct a pair from two values.", "Pairs", "cons(first, second)"),
    _public("debug_repr", "Return the deterministic debug representation of a value.", "I/O", "debug_repr(value)"),
    _public("declassify", "Declassify a protected value with matching explicit authority.", "Configuration", "declassify(authority, value)", stability="Experimental"),
    _public("derive", "Return a Sheet with one derived column.", "Sheets", "derive(sheet, column, function)", stability="Experimental"),
    _public("display", "Return the display representation of a value.", "I/O", "display(value)"),
    _public("doc", "Return the canonical documentation string for a bound name.", "Documentation", "doc(name)"),
    _public("embed", "Construct an embedding callable through an explicit provider boundary.", "Retrieval", "embed(provider, config, credential, authority)", stability="Experimental"),
    _public("entry_bytes", "Return the bytes stored in a zip entry.", "File / zip", "entry_bytes(entry)"),
    _public("entry_json", "Return whether a zip entry name has a JSON suffix.", "File / zip", "entry_json(entry)"),
    _public("entry_name", "Return a zip entry's filename.", "File / zip", "entry_name(entry)"),
    _public("exact_shape_match", "Match a value against an exact shape template.", "Value templates", "exact_shape_match(shape, value)", stability="Experimental"),
    _public("force", "Force a delayed promise and return its value.", "Evaluation", "force(promise)"),
    _public("format_tag", "Return the tag of a representation template.", "Value templates", "format_tag(format)", stability="Experimental"),
    _public("format_template", "Return the inner template of a representation template.", "Value templates", "format_template(format)", stability="Experimental"),
    _public("help", "Show the public help overview or documentation for one bound name.", "Documentation", "help()", "help(name)"),
    _public("index", "Construct an opaque retrieval index through an explicit provider boundary.", "Retrieval", "index(provider, config, credential, authority)", stability="Experimental"),
    _public("input", "Read one line from standard input.", "I/O", "input()"),
    _public("lifecycle_child", "Run a child execution scope nested under an active parent scope handle.", "Lifecycle", "lifecycle_child(scope_handle, peers, work)", stability="Experimental"),
    _public("lifecycle_context", "Read inward-only lifecycle context exposed by an entered peer or an ancestor scope.", "Lifecycle", "lifecycle_context(scope_handle, name)", stability="Experimental"),
    _public("lifecycle_scope", "Run a fresh root execution scope through explicit peer definitions and one work callable.", "Lifecycle", "lifecycle_scope(peers, work)", stability="Experimental"),
    _public("log", "Write values to standard error with a trailing newline.", "I/O", "log(..values)"),
    _public("meta", "Return the metadata map for a bound name.", "Documentation", "meta(name)"),
    _public("model", "Construct a model callable through an explicit provider boundary.", "AI composition", "model(provider, config, credential, authority)", stability="Experimental"),
    _public("null?", "Return whether a value is the empty pair-list terminator.", "Pairs", "null?(value)"),
    _public("open_shape_match", "Match a value against an open shape template.", "Value templates", "open_shape_match(shape, value)", stability="Experimental"),
    _public("pair?", "Return whether a value is a pair.", "Pairs", "pair?(value)"),
    _public("print", "Write values to standard output with a trailing newline.", "I/O", "print(..values)"),
    _public("protected_match", "Match a value while preserving the protected carrier boundary.", "Configuration", "protected_match(template, value)", stability="Experimental"),
    _public("refinement_match", "Match a value against a refinement template.", "Value templates", "refinement_match(template, value)", stability="Experimental"),
    _public("render_csv", "Render an immutable Sheet as deterministic CSV text.", "Sheets", "render_csv(sheet)", stability="Experimental"),
    _public("represent", "Attach a first-class representation facet to a value.", "Value templates", "represent(format, value)", stability="Experimental"),
    _public("representation_match", "Match a represented value against a representation template.", "Value templates", "representation_match(template, value)", stability="Experimental"),
    _public("rerank", "Construct a provenance-preserving reranker through an explicit provider boundary.", "Retrieval", "rerank(provider, config, credential, authority)", stability="Experimental"),
    _public("retrieve", "Construct a retrieval callable through an explicit provider boundary.", "Retrieval", "retrieve(provider, config, credential, authority)", stability="Experimental"),
    _public("row_get", "Read one named value from a Sheet row representation.", "Sheets", "row_get(row, column)", stability="Experimental"),
    _public("rows", "Return a Sheet's rows as ordered name/value pairs.", "Sheets", "rows(sheet)", stability="Experimental"),
    _public("secret_get", "Read and validate one protected secret through a provider.", "Configuration", "secret_get(provider, key, authority)", stability="Experimental"),
    _public("secret_get_or", "Read and validate one protected secret or use an explicit protected default.", "Configuration", "secret_get_or(provider, key, default, authority)", stability="Experimental"),
    _public("secret_view", "Construct a qualified protected-secret lookup callable over an explicit provider.", "Configuration", "secret_view(provider, prefix, purpose)", stability="Experimental"),
    _public("select", "Return a Sheet containing selected columns.", "Sheets", "select(sheet, columns)", stability="Experimental"),
    _public("set_entry_bytes", "Return a zip entry with replacement bytes.", "File / zip", "set_entry_bytes(entry, bytes)"),
    _public("shape", "Return a Sheet's row and column counts.", "Sheets", "shape(sheet)", stability="Experimental"),
    _public("sheet", "Construct an immutable Sheet from ordered columns.", "Sheets", "sheet(columns)", stability="Experimental"),
    _public("sleep", "Block the Python reference host for a number of milliseconds.", "Simulation", "sleep(milliseconds)"),
    _public("stdin", "Return the Python-host standard-input source capability.", "I/O", "stdin()"),
    _public("strip_representation", "Remove one matching representation facet from a represented value.", "Value templates", "strip_representation(format, value)", stability="Experimental"),
    _public("update_entry_bytes", "Return a zip entry after applying a bytes updater.", "File / zip", "update_entry_bytes(entry, updater)"),
    _public("utf8_decode", "Decode a byte value as UTF-8 text.", "Encoding", "utf8_decode(bytes)"),
    _public("utf8_encode", "Encode a string as UTF-8 bytes.", "Encoding", "utf8_encode(text)"),
    _public("where", "Return a Sheet containing rows accepted by a predicate.", "Sheets", "where(sheet, predicate)", stability="Experimental"),
    _public("zip_entries", "Read a zip archive into a list of entry values.", "File / zip", "zip_entries(path)"),
)


_INTERNAL_NAMES = frozenset(
    """
_absence_context _absence_meta _absence_reason _actor_call_update
_actor_validate_effect _assemble_grounded_answer _assemble_grounded_context
_as_seq _byte_length _cell_alive? _cell_error _cell_failed? _cell_get
_cell_new _cell_send _cell_status _cell_stop _cell_with_state _clear_screen
_cli_chars _cli_flag? _cli_option _cli_option_or _cli_spec _cli_type_error
_cli_value_error _collect _concat _contains _cors _diagnostic_error
_diagnostic_skipped _each _ends_with _ensure_seq_compatible _err _evolve
_find _flat_map_some _flow? _flow_debug _flush _format _format_compose _get
_get? _is_empty _is_none? _is_some? _join _json_decode _json_encode
_json_parse _json_schema _json_stringify _keep_some _keep_some_else _lines
_lower _map_count _map_get _map_has? _map_items _map_new _map_put
_map_remove _map_some _merge _meta_define _meta_empty_env _meta_eval_error
_meta_extend _meta_host_apply _meta_lookup _meta_match_error
_meta_match_pattern_env _meta_set _move_cursor _none? _or_else
_or_else_with _pairs_error _parse_csv_row _parse_int _parse_jsonl_record
_pipe_run _process_alive? _process_error _process_failed? _rand _rand_int
_rand_int_seeded _rand_seeded _read_file _reduce_error _ref _ref_get
_ref_is_set _ref_set _ref_update _render_grid _resource_capabilities
_resource_copy _resource_delete _resource_discover _resource_meta
_resource_read_bytes _resource_read_text _resource_write_bytes
_resource_write_text _restart_cell _rng _rules_error _rules_kernel
_rules_prepare _run _scan _send _seq_reduce _seq_transform _seq_type_error
_serve_http _some _some? _spawn _split _split_whitespace _starts_with _sum
_syntax_error _syntax_self_evaluating _syntax_symbol_expr _tee _then_find
_then_first _then_get _then_nth _trim _trim_end _trim_start _unwrap_or
_upper _validate_each _validate_field _validate_optional _validate_record
_validate_required _with_headers _write _write_file _writeln _zip _zip_read
_zip_write
""".split()
)


_INTERNAL_DOCS = tuple(
    HostBuiltinDoc(name, "", "", "internal", ()) for name in sorted(_INTERNAL_NAMES)
)
_HOST_BUILTIN_DOCS = tuple(sorted((*_PUBLIC_DOCS, *_INTERNAL_DOCS), key=lambda entry: entry.name.lower()))
_BY_NAME = {entry.name: entry for entry in _HOST_BUILTIN_DOCS}

if len(_BY_NAME) != len(_HOST_BUILTIN_DOCS):
    raise ValueError("duplicate host builtin documentation registry name")


def host_builtin_docs() -> tuple[HostBuiltinDoc, ...]:
    return _HOST_BUILTIN_DOCS


def public_host_builtin_docs() -> tuple[HostBuiltinDoc, ...]:
    return tuple(entry for entry in _HOST_BUILTIN_DOCS if entry.stability != "internal")


def internal_host_builtin_names() -> frozenset[str]:
    return _INTERNAL_NAMES


def host_builtin_doc(name: str) -> HostBuiltinDoc:
    return _BY_NAME[name]
