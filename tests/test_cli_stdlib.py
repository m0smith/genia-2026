import pytest

from genia import make_global_env, run_source


def test_argv_exposed_as_plain_string_list():
    env = make_global_env(cli_args=["input.txt", "--pretty"])
    assert run_source("argv()", env) == ["input.txt", "--pretty"]


def test_positional_pattern_matching_with_argv():
    env = make_global_env(cli_args=["in.txt", "out.txt"])
    source = """
main(args) =
  ([input]) -> ["one", input] |
  ([input, output]) -> ["two", input, output] |
  _ -> "usage"

main(argv())
"""
    assert run_source(source, env) == ["two", "in.txt", "out.txt"]


def test_cli_parse_empty():
    env = make_global_env()
    assert run_source("map_count(unwrap_or({}, first(cli_parse([]))))", env) == 0
    assert run_source("rest(cli_parse([]))", env) == [[]]


def test_cli_parse_long_boolean_flag():
    env = make_global_env()
    assert run_source('cli_flag?(unwrap_or({}, first(cli_parse(["--pretty"]))), "pretty")', env) is True


def test_cli_parse_long_option_equals():
    env = make_global_env()
    assert run_source('cli_option(unwrap_or({}, first(cli_parse(["--indent=4"]))), "indent")', env) == "4"


def test_cli_parse_long_option_with_next_value():
    env = make_global_env()
    assert run_source('cli_option(unwrap_or({}, first(cli_parse(["--indent", "2"]))), "indent")', env) == "2"


def test_cli_parse_grouped_short_flags():
    env = make_global_env()
    source = """
opts = unwrap_or({}, first(cli_parse(["-abc"])))
[cli_flag?(opts, "a"), cli_flag?(opts, "b"), cli_flag?(opts, "c")]
"""
    assert run_source(source, env) == [True, True, True]


def test_cli_parse_short_option_value():
    env = make_global_env()
    assert run_source('cli_option(unwrap_or({}, first(cli_parse(["-o", "file.txt"]))), "o")', env) == "file.txt"


def test_cli_parse_terminator():
    env = make_global_env()
    assert run_source('cli_flag?(unwrap_or({}, first(cli_parse(["--pretty", "--", "--raw", "input.txt"]))), "pretty")', env) is True
    assert run_source('rest(cli_parse(["--pretty", "--", "--raw", "input.txt"]))', env) == [["--raw", "input.txt"]]


def test_cli_parse_mixed_and_last_wins():
    env = make_global_env()
    assert run_source('cli_option(unwrap_or({}, first(cli_parse(["--indent=2", "in", "--indent", "4", "-p", "out"]))), "indent")', env) == "4"
    assert run_source('rest(cli_parse(["--indent=2", "in", "--indent", "4", "-p", "out"]))', env) == [["in"]]


def test_cli_helpers():
    env = make_global_env()
    source = """
opts = map_put(map_new(), "pretty", true)
opts2 = map_put(opts, "indent", "3")
[cli_flag?(opts2, "pretty"), cli_option(opts2, "indent"), cli_option_or(opts2, "missing", "2")]
"""
    assert run_source(source, env) == [True, "3", "2"]


def test_cli_parse_type_errors_are_deterministic():
    env = make_global_env()
    with pytest.raises(TypeError, match="cli_parse expected a list of strings"):
        run_source("cli_parse(1)", env)
    with pytest.raises(TypeError, match="cli_parse expected a list of strings"):
        run_source('cli_parse([1])', env)
    with pytest.raises(TypeError, match="cli_flag\\? expected a map as first argument"):
        run_source('cli_flag?([], "a")', env)


def test_cli_parse_with_minimal_spec_aliases_and_options():
    env = make_global_env()
    source = """
aliases = map_put(map_new(), "p", "pretty")
spec0 = map_put(map_new(), "flags", ["pretty"])
spec1 = map_put(spec0, "options", ["indent"])
spec = map_put(spec1, "aliases", aliases)
parsed = cli_parse(["-p", "--indent", "2", "input.txt"], spec)
opts = unwrap_or({}, first(parsed))
positionals = unwrap_or([], first(rest(parsed)))
[cli_flag?(opts, "pretty"), cli_option(opts, "indent"), positionals]
"""
    assert run_source(source, env) == [True, "2", ["input.txt"]]


def test_cli_parse_pattern_matching_over_positionals():
    env = make_global_env()
    source = """
spec = map_put(map_new(), "flags", ["pretty"])

run_parsed(parsed) =
  ([opts, [input]]) -> [cli_flag?(opts, "pretty"), input] |
  ([opts, [input, output]]) -> [cli_flag?(opts, "pretty"), input, output] |
  _ -> "usage"

run_parsed(cli_parse(["--pretty", "a.txt", "b.txt"], spec))
"""
    assert run_source(source, env) == [True, "a.txt", "b.txt"]
