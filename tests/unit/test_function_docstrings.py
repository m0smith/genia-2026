import pytest

from genia.ast_nodes import FuncDef
from genia.interpreter import Parser, lex
from genia import make_global_env, run_source


def test_parser_captures_named_function_docstring_metadata():
    src = 'inc(x) = "increment by one" x + 1\n'
    ast = Parser(lex(src), source=src, filename="doc.genia").parse_program()
    fn = ast[0]
    assert isinstance(fn, FuncDef)
    assert fn.docstring == "increment by one"


def test_help_displays_function_docstring_and_source_location():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = 'inc(x) = "increment by one" x + 1\nhelp("inc")\n'
    run_source(src, env, filename="doc.genia")
    out = "".join(outputs)
    assert "inc/1" in out
    assert "Defined at doc.genia:1" in out
    assert "increment by one" in out


def test_multiple_identical_docstrings_are_allowed():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = """
    echo() = "echo helper" nil
    echo(x) = "echo helper" x
    help("echo")
    """
    run_source(src, env, filename="echo.genia")
    out = "".join(outputs)
    assert "echo/0, 1" in out
    assert "echo helper" in out


def test_conflicting_docstrings_raise_clear_error():
    env = make_global_env([])
    src = """
    fn() = "first" nil
    fn(x) = "second" x
    """
    with pytest.raises(TypeError, match="Conflicting docstrings for function fn"):
        run_source(src, env)


def test_help_renders_markdown_docstring_with_normalized_whitespace():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = """
    sum(xs) = "# sum\\n\\nReturn total from `xs`.\\n\\n## Params\\n- xs: numbers\\n\\n\\n\\n## Examples\\n```genia\\nsum([]) -> 0\\n```" 0
    help("sum")
    """
    run_source(src, env, filename="sum.genia")
    out = "".join(outputs)
    assert "sum/1" in out
    assert "# sum" in out
    assert "Return total from `xs`." in out
    assert "## Params" in out
    assert "- xs: numbers" in out
    assert "```genia" in out
    assert "sum([]) -> 0" in out
    assert "\n\n\n" not in out


def test_help_undocumented_function_fallback():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source("sum(xs) = 0\nhelp(\"sum\")\n", env, filename="sum.genia")
    out = "".join(outputs)
    assert "sum/1" in out
    assert "No documentation available." in out


def test_help_overview_points_to_prelude_backed_public_surface():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source("help()\n", env, filename="help_overview.genia")
    out = "".join(outputs)
    assert "Most user-facing helpers live in autoloaded prelude modules." in out
    assert '`help("name")` autoloads a documented public helper' in out
    assert "Public family names below are derived from registered prelude autoloads." in out
    assert '`unwrap_or("?", record |> get("user") |> get("name"))` is preferred' in out
    assert "Public prelude families discovered from autoload registrations:" in out
    assert "cli_parse, cli_flag?, cli_option, cli_option_or" in out
    assert "Flow:" in out
    assert "keep_some" in out
    assert "keep_some_else" in out
    assert "lines" in out
    assert "collect" in out
    assert "run" in out
    assert "Map:" in out
    assert "map_put" in out
    assert "Ref:" in out
    assert "ref_update" in out
    assert "Process:" in out
    assert "spawn" in out
    assert "I/O:" in out
    assert "write, writeln, flush" in out
    assert "Syntax:" in out
    assert "match_branches" in out
    assert "Eval:" in out
    assert "empty_env, lookup, define, set, extend, eval" in out
    assert "\n    _map" not in out


def test_help_autoloads_option_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("get")\n', env, filename="help_option.genia")
    out = "".join(outputs)
    assert "get/2" in out
    assert "Canonical maybe-aware lookup helper" in out


def test_help_autoloads_string_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("parse_int")\n', env, filename="help_string.genia")
    out = "".join(outputs)
    assert "parse_int/1, 2" in out
    assert "Parse an integer from a string" in out


def test_help_autoloads_json_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("json_parse")\n', env, filename="help_json.genia")
    out = "".join(outputs)
    assert "json_parse/1" in out
    assert "Parse JSON text into Genia runtime data." in out


def test_help_autoloads_file_zip_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("zip_read")\n', env, filename="help_file_zip.genia")
    out = "".join(outputs)
    assert "zip_read/1" in out
    assert "Create a lazy Flow of zip entries" in out


def test_help_autoloads_map_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("map_put")\n', env, filename="help_map.genia")
    out = "".join(outputs)
    assert "map_put/3" in out
    assert "Return a new map with `key` set to `value`." in out


def test_help_autoloads_io_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("write")\n', env, filename="help_io.genia")
    out = "".join(outputs)
    assert "write/2" in out
    assert "without a trailing newline" in out


def test_help_autoloads_process_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("spawn")\n', env, filename="help_process.genia")
    out = "".join(outputs)
    assert "spawn/1" in out
    assert "host-thread mailbox worker" in out


def test_help_autoloads_eval_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("eval")\n', env, filename="help_eval.genia")
    out = "".join(outputs)
    assert "eval/2" in out
    assert "Evaluate a quoted Genia expression in a metacircular environment." in out


def test_help_autoloads_flow_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("lines")\n', env, filename="help_flow.genia")
    out = "".join(outputs)
    assert "lines/1" in out
    assert "Create a Flow from `stdin`" in out


def test_help_autoloads_keep_some_else_flow_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("keep_some_else")\n', env, filename="help_keep_some_else.genia")
    out = "".join(outputs)
    assert "keep_some_else/2, 3" in out
    assert "dead-letter routing for Flow pipelines" in out


def test_help_autoloads_keep_some_flow_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("keep_some")\n', env, filename="help_keep_some.genia")
    out = "".join(outputs)
    assert "keep_some/1, 2" in out
    assert "Keep only successful Option values from a flow." in out


def test_help_autoloads_rules_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("rules")\n', env, filename="help_rules.genia")
    out = "".join(outputs)
    assert "rules/0+" in out
    assert "Rule orchestration, defaulting, and contract validation live in prelude" in out


def test_help_autoloads_cli_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("cli_parse")\n', env, filename="help_cli.genia")
    out = "".join(outputs)
    assert "cli_parse/1, 2" in out
    assert "`argv()` remains the raw host-backed CLI primitive" in out


def test_help_autoloads_cli_helper_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("cli_option_or")\n', env, filename="help_cli_helper.genia")
    out = "".join(outputs)
    assert "cli_option_or/3" in out
    assert "Return a parsed option value or `default`" in out


def test_help_autoloads_syntax_wrapper_docstring():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("match_branches")\n', env, filename="help_syntax.genia")
    out = "".join(outputs)
    assert "match_branches/1" in out
    assert "quoted branch sequence of a match expression" in out


def test_help_for_host_primitive_name_points_back_to_public_surface():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("print")\n', env, filename="help_host.genia")
    out = "".join(outputs)
    assert "print" in out
    assert "host-backed runtime function" in out
    assert "public Genia/prelude functions" in out
    assert '`help("name")` for documented prelude helpers' in out


def test_help_for_missing_name_fails_gracefully():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source('help("definitely_missing_helper")\n', env, filename="help_missing.genia")
    out = "".join(outputs)

    assert "No public helper or runtime name found: definitely_missing_helper" in out
    assert "Use `help()` for the public surface overview." in out


def test_help_docstring_normalizes_triple_quote_wrappers_and_indentation():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = r'''
    sum(xs) = "\"\"\"\n        # sum\n\n          - xs: list of numbers\n    \"\"\"" 0
    help("sum")
    '''
    run_source(src, env, filename="sum.genia")
    out = "".join(outputs)
    assert "# sum" in out
    assert "- xs: list of numbers" in out


def test_triple_quoted_multiline_docstring_source_is_supported():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    src = '''
    inc(x) = """
    # inc

    Increment by one.
    """ x + 1
    help("inc")
    '''
    run_source(src, env, filename="inc.genia")
    out = "".join(outputs)
    assert "# inc" in out
    assert "Increment by one." in out


def test_docstring_function_body_supports_parenthesized_case_expression():
    src = '''
    wrap(n, size) = """
    # wrap
    """ (
      (n, size) ? n < 0 -> size - 1 |
      (n, size) ? n >= size -> 0 |
      (n, _) -> n
    )

    [wrap(-1, 8), wrap(8, 8), wrap(3, 8)]
    '''
    assert run_source(src, make_global_env([]), filename="wrap.genia") == [7, 0, 3]


def test_help_overview_includes_actor_family():
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source("help()\n", env, filename="help_actor_family.genia")
    out = "".join(outputs)
    assert "Actor:" in out
    assert "actor_send" in out


def test_help_overview_all_prelude_families_discovered():
    """Every prelude module produces a labeled family in help() overview."""
    outputs: list[str] = []
    env = make_global_env([], output_handler=outputs.append)
    run_source("help()\n", env, filename="help_all_families.genia")
    out = "".join(outputs)
    expected_families = [
        "Actor:", "AWK:", "Cell:", "CLI:", "Eval:", "File / zip:", "Flow:",
        "Function helpers:", "I/O:", "JSON:", "List:", "Map:", "Math:",
        "Option:", "Process:", "Random:", "Ref:", "Stream:", "String:",
        "Syntax:",
    ]
    for family in expected_families:
        assert family in out, f"Missing family: {family}"
