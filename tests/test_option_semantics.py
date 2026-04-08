from genia import make_global_env, run_source
from genia.interpreter import GeniaOptionNone
from genia.utf8 import format_debug


def test_none_short_circuits_pipeline_and_preserves_reason():
    env = make_global_env([])
    src = """
    bump(x) = x + 1
    none("empty-list") |> bump
    """
    assert format_debug(run_source(src, env)) == 'none("empty-list")'


def test_none_argument_short_circuits_ordinary_calls_unless_pattern_matched():
    env = make_global_env([])
    src = """
    f(x) = x + 1
    g(x) =
      none("missing-key", info) -> info/key |
      _ -> "ok"

    [f(none("missing-key", {key: "name"})), g(none("missing-key", {key: "name"}))]
    """
    result = run_source(src, env)
    assert format_debug(result[0]) == 'none("missing-key", {key: "name"})'
    assert result[1] == "name"


def test_none_type_errors_use_structured_absence():
    env = make_global_env([])
    assert format_debug(run_source('some(2) + 3', env)) == 'none("type-error", {source: "+", left: "some", right: "int"})'


def test_run_source_normalizes_empty_program_result_to_none_value():
    env = make_global_env([])
    result = run_source("", env)
    assert isinstance(result, GeniaOptionNone)
    assert format_debug(result) == 'none("nil")'
