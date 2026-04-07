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


def test_cli_parse_type_errors_are_deterministic():
    env = make_global_env()
    with pytest.raises(TypeError, match="cli_parse expected a list of strings"):
        run_source('cli_parse([1])', env)
