"""Restricted Genia profile for the MCP source-execution worker (R28 E28-3, issue #704).

Default-deny classification of every global binding and prelude autoload of the
Python reference host (ledger R28-H24), plus pre-execution policy inspection over
the **raw parser AST** (contract Clarification A4, ledger R28-H25). The shared
normalized parse surface is not used or expanded.

`ALLOWED_*` is the complete set that survives pruning; `DENIED_*` records the
authority-bearing names removed from the environment. A name in neither set is
removed as well (and the classification test fails), so a binding added to Genia
later never silently gains authority in the MCP profile. This module contains no
MCP protocol, tool, or envelope logic.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass

# Every authority-bearing global binding: file/zip/resource I/O, HTTP and server,
# external process execution, configuration/secret/declassification, model and
# retrieval providers, and stdin/terminal input.
DENIED_BINDINGS = frozenset(
    (
    '_cors', '_execution_process', '_http_send', '_read_file', '_resource_capabilities',
    '_resource_copy', '_resource_delete', '_resource_discover', '_resource_meta',
    '_resource_read_bytes', '_resource_read_text', '_resource_write_bytes',
    '_resource_write_text', '_serve_http', '_write_file', '_zip_read', '_zip_write',
    'config_args', 'config_get', 'config_get_or', 'config_provider', 'config_standard',
    'config_view', 'declassify', 'embed', 'http_operation', 'input', 'lifecycle_config',
    'model', 'rerank', 'retrieve', 'secret_get', 'secret_get_or', 'secret_view', 'stdin_keys',
    )
)

# Autoload entries (name, arity) that reach file authority.
DENIED_AUTOLOADS = frozenset(
    (
    ('read_file', 1), ('write_file', 2), ('zip_read', 1), ('zip_write', 1), ('zip_write', 2),
    )
)

ALLOWED_BINDINGS = frozenset(
    (
    'Format', '__r18_conformance_test_only_nan', '_absence_context', '_absence_meta',
    '_absence_reason', '_actor_call_update', '_actor_validate_effect',
    '_assemble_grounded_answer', '_assemble_grounded_context', '_byte_length', '_cell_alive?',
    '_cell_error', '_cell_failed?', '_cell_get', '_cell_new', '_cell_send', '_cell_status',
    '_cell_stop', '_cell_with_state', '_clear_screen', '_cli_chars', '_cli_flag?',
    '_cli_option', '_cli_option_or', '_cli_spec', '_cli_type_error', '_cli_value_error',
    '_concat', '_contains', '_diagnostic_error', '_diagnostic_skipped', '_ends_with', '_err',
    '_find', '_flat_map_some', '_flow?', '_flow_debug', '_flush', '_format', '_format_compose',
    '_get', '_get?', '_is_empty', '_is_none?', '_is_some?', '_join', '_json_decode',
    '_json_encode', '_json_parse', '_json_schema', '_json_stringify', '_keep_some',
    '_keep_some_else', '_lines', '_lower', '_map_count', '_map_get', '_map_has?', '_map_items',
    '_map_new', '_map_put', '_map_remove', '_map_some', '_merge', '_meta_define',
    '_meta_empty_env', '_meta_eval_error', '_meta_extend', '_meta_host_apply', '_meta_lookup',
    '_meta_match_error', '_meta_match_pattern_env', '_meta_set', '_move_cursor', '_none?',
    '_or_else', '_or_else_with', '_pairs_error', '_parse_csv_row', '_parse_int',
    '_parse_jsonl_record', '_pipe_run', '_process_alive?', '_process_error',
    '_process_failed?', '_rand', '_rand_int', '_rand_int_seeded', '_rand_seeded',
    '_reduce_error', '_ref', '_ref_get', '_ref_is_set', '_ref_set', '_ref_update',
    '_render_grid', '_restart_cell', '_rng', '_rules_error', '_rules_kernel', '_rules_prepare',
    '_send', '_send_annotated', '_seq_type_error', '_some', '_some?', '_spawn', '_split',
    '_split_whitespace', '_starts_with', '_sum', '_syntax_error', '_syntax_self_evaluating',
    '_syntax_symbol_expr', '_tee', '_then_find', '_then_first', '_then_get', '_then_nth',
    '_trim', '_trim_end', '_trim_start', '_unwrap_or', '_upper', '_validate_each',
    '_validate_field', '_validate_optional', '_validate_record', '_validate_required',
    '_with_headers', '_write', '_writeln', '_zip', 'accumulate', 'alternatives', 'apply_raw',
    'argv', 'assert_eq', 'assert_true', 'car', 'cdr', 'chunk', 'collect_sheet',
    'collect_validated', 'columns', 'cons', 'debug_repr', 'default_field', 'derive', 'display',
    'doc', 'e', 'entry_bytes', 'entry_json', 'entry_name', 'exact', 'exact_shape',
    'exact_shape_match', 'false', 'float64', 'force', 'format_tag', 'format_template', 'help',
    'index', 'lifecycle_child', 'lifecycle_context', 'lifecycle_repeat', 'lifecycle_scope',
    'log', 'meta', 'nil', 'none', 'null?', 'open_shape', 'open_shape_match', 'pair?', 'pi',
    'print', 'protected_match', 'rational', 'recursive_template', 'refinement',
    'refinement_match', 'render_csv', 'represent', 'representation_match', 'row_get', 'rows',
    'select', 'set_entry_bytes', 'shape', 'sheet', 'sleep', 'stderr', 'stdin', 'stdout',
    'strip_representation', 'template_description', 'template_schema', 'true',
    'update_entry_bytes', 'utf8_decode', 'utf8_encode', 'where', 'zip_entries',
    )
)

ALLOWED_AUTOLOADS = frozenset(
    (
    ('abs', 1), ('absence_context', 1), ('absence_meta', 1), ('absence_reason', 1),
    ('actor', 2), ('actor_alive?', 1), ('actor_call', 2), ('actor_error', 1),
    ('actor_failed?', 1), ('actor_restart', 2), ('actor_send', 2), ('actor_state', 1),
    ('actor_status', 1), ('actor_stop', 1), ('any?', 2), ('append', 2),
    ('application_expr?', 1), ('apply', 2), ('as_seq', 1), ('assignment_expr?', 1),
    ('assignment_name', 1), ('assignment_value', 1), ('awk_count', 2), ('awk_filter', 2),
    ('awk_map', 2), ('awkify', 2), ('block_expr?', 1), ('block_expressions', 1),
    ('branch_body', 1), ('branch_guard', 1), ('branch_has_guard?', 1), ('branch_pattern', 1),
    ('byte_length', 1), ('cell', 1), ('cell_alive?', 1), ('cell_error', 1),
    ('cell_failed?', 1), ('cell_get', 1), ('cell_send', 2), ('cell_state', 1),
    ('cell_status', 1), ('cell_stop', 1), ('cell_with_state', 1), ('clear_screen', 0),
    ('cli_flag?', 2), ('cli_option', 2), ('cli_option_or', 3), ('cli_parse', 1),
    ('cli_parse', 2), ('collect', 1), ('compose', 1), ('concat', 2), ('contains', 2),
    ('count', 1), ('dec', 1), ('define', 3), ('diagnostic_error', 4), ('diagnostic_field', 1),
    ('diagnostic_reason', 1), ('diagnostic_skipped', 4), ('drop', 2), ('each', 2),
    ('empty?', 1), ('empty_env', 0), ('ends_with', 2), ('err', 1), ('eval', 2), ('evolve', 2),
    ('extend', 3), ('fields', 1), ('filter', 2), ('find', 2), ('find_opt', 2), ('first', 1),
    ('first_opt', 1), ('flat_map_some', 2), ('flush', 1), ('format', 2), ('format_compose', 1),
    ('get', 2), ('get?', 2), ('head', 1), ('head', 2), ('inc', 1), ('inspect', 1),
    ('is_empty', 1), ('is_none?', 1), ('is_some?', 1), ('join', 2), ('json_decode', 1),
    ('json_encode', 1), ('json_parse', 1), ('json_pretty', 1), ('json_schema', 1),
    ('json_stringify', 1), ('keep_some', 1), ('keep_some', 2), ('keep_some_else', 2),
    ('keep_some_else', 3), ('lambda_body', 1), ('lambda_expr?', 1), ('lambda_params', 1),
    ('last', 1), ('length', 1), ('lines', 1), ('list', 0), ('lookup', 2), ('lower', 1),
    ('map', 2), ('map_count', 1), ('map_get', 2), ('map_has?', 2), ('map_item_key', 1),
    ('map_item_value', 1), ('map_items', 1), ('map_keys', 1), ('map_new', 0), ('map_put', 3),
    ('map_remove', 2), ('map_some', 2), ('map_values', 1), ('match_branches', 1),
    ('match_expr?', 1), ('max', 2), ('merge', 1), ('merge', 2), ('min', 2), ('mod', 2),
    ('move_cursor', 2), ('nil?', 1), ('none?', 1), ('nth', 2), ('nth_opt', 2), ('operands', 1),
    ('operator', 1), ('or_else', 2), ('or_else_with', 2), ('pairs', 2), ('parse_csv_row', 1),
    ('parse_csv_row', 2), ('parse_int', 1), ('parse_int', 2), ('parse_jsonl_record', 1),
    ('process_alive?', 1), ('quasiquoted_expr?', 1), ('quoted_expr?', 1), ('rand', 0),
    ('rand', 1), ('rand_flow', 1), ('rand_int', 1), ('rand_int', 2), ('rand_int_flow', 2),
    ('range', 1), ('range', 2), ('range', 3), ('reduce', 3), ('ref', 0), ('ref', 1),
    ('ref_get', 1), ('ref_is_set', 1), ('ref_set', 2), ('ref_update', 2), ('refine', 0),
    ('render_grid', 1), ('rest', 1), ('restart_cell', 2), ('reverse', 1), ('rng', 1),
    ('rule_ctx', 1), ('rule_emit', 1), ('rule_emit_many', 1), ('rule_halt', 0),
    ('rule_set', 1), ('rule_skip', 0), ('rule_step', 3), ('rules', 0), ('run', 1), ('scan', 2),
    ('scan', 3), ('self_evaluating?', 1), ('send', 2), ('set', 3), ('some', 1), ('some?', 1),
    ('spawn', 1), ('split', 2), ('split_whitespace', 1), ('starts_with', 2), ('step_ctx', 1),
    ('step_emit', 1), ('step_emit_many', 1), ('step_halt', 0), ('step_set', 1),
    ('step_skip', 0), ('step_step', 3), ('stream_cons', 2), ('stream_filter', 2),
    ('stream_head', 1), ('stream_map', 2), ('stream_tail', 1), ('stream_take', 2), ('sum', 1),
    ('symbol_expr?', 1), ('tagged_list?', 2), ('take', 2), ('tap', 2), ('tee', 1),
    ('text_of_quotation', 1), ('then_find', 2), ('then_first', 1), ('then_get', 2),
    ('then_nth', 2), ('trace', 2), ('trim', 1), ('trim_end', 1), ('trim_start', 1),
    ('unwrap_or', 2), ('upper', 1), ('validate_each', 2), ('validate_field', 4),
    ('validate_optional', 2), ('validate_optional', 3), ('validate_record', 2),
    ('validate_record', 3), ('validate_required', 2), ('write', 2), ('writeln', 2), ('zip', 1),
    ('zip', 2),
    )
)

# Names a source may not mention at all (policy layer). Conservative: a user
# definition that reuses one of these names is rejected too.
DENIED_NAMES = frozenset(DENIED_BINDINGS | {name for name, _arity in DENIED_AUTOLOADS})


def prune_environment(env) -> None:
    """Remove every binding and autoload that is not explicitly allowed."""
    for name in list(env.values):
        if name not in ALLOWED_BINDINGS:
            del env.values[name]
            env.binding_metadata.pop(name, None)
    root = env.root()
    for key in list(root.autoloads):
        if key not in ALLOWED_AUTOLOADS:
            del root.autoloads[key]
            root.trusted_autoloads.discard(key)


def policy_violation(nodes) -> bool:
    """True when the raw parser AST uses a prohibited form or name.

    Iterative (no recursion), so a deeply nested hostile tree cannot overflow the
    interpreter stack. Rejects any import (including packaged and host modules),
    shell stages, and any reference to a prohibited name.
    """
    stack = [nodes]
    while stack:
        item = stack.pop()
        if isinstance(item, (list, tuple)):
            stack.extend(item)
            continue
        if isinstance(item, dict):
            stack.extend(item.values())
            continue
        if not is_dataclass(item) or isinstance(item, type):
            continue
        kind = type(item).__name__
        if kind in ("ImportStmt", "ShellStage"):
            return True
        if kind == "Var" and getattr(item, "name", None) in DENIED_NAMES:
            return True
        for field in fields(item):
            if field.name == "span":
                continue
            value = getattr(item, field.name)
            if isinstance(value, str):
                continue
            stack.append(value)
    return False
