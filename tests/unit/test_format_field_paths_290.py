import io

import pytest

from genia import make_global_env, run_source
from genia._format_engine import (
    TemplatePlaceholder,
    parse_format_template,
    resolve_format_placeholder,
)
from genia.values import GeniaMap


def _env():
    stdout = io.StringIO()
    stderr = io.StringIO()
    return make_global_env(stdout_stream=stdout, stderr_stream=stderr), stdout, stderr


def _map(**entries):
    result = GeniaMap()
    for key, value in entries.items():
        result = result.put(key, value)
    return result


def test_format_field_path_parser_accepts_dot_separated_named_fields():
    assert parse_format_template("{user.name}") == [
        TemplatePlaceholder("user.name", None)
    ]
    assert parse_format_template("{user.address.city:?}") == [
        TemplatePlaceholder("user.address.city", "?")
    ]


@pytest.mark.parametrize(
    "template",
    [
        "{}",
        "{.name}",
        "{name.}",
        "{user..name}",
        "{user-name}",
        "{user name}",
        "{user.name()}",
        "{user[0]}",
        "{0.name}",
    ],
)
def test_format_field_path_parser_rejects_invalid_or_unsupported_paths(template):
    with pytest.raises(ValueError, match="format invalid placeholder"):
        parse_format_template(template)


def test_format_field_path_resolver_resolves_nested_map_fields():
    values = _map(
        user=_map(
            name="Ada",
            address=_map(city="Bountiful", state="UT"),
        )
    )

    assert resolve_format_placeholder(values, "user.name") == "Ada"
    assert resolve_format_placeholder(values, "user.address.city") == "Bountiful"


def test_format_field_path_resolver_reports_missing_top_level_path():
    with pytest.raises(ValueError, match="format missing field: user\\.name"):
        resolve_format_placeholder(GeniaMap(), "user.name")


def test_format_field_path_resolver_reports_missing_nested_path():
    values = _map(user=GeniaMap())

    with pytest.raises(ValueError, match="format missing field: user\\.name"):
        resolve_format_placeholder(values, "user.name")


def test_format_field_path_resolver_reports_non_map_intermediate():
    values = _map(user="Ada")

    with pytest.raises(
        TypeError,
        match="format expected a map while resolving placeholder path: user\\.name",
    ):
        resolve_format_placeholder(values, "user.name")


def test_format_field_path_runtime_resolves_one_level_nested_field():
    env, _, _ = _env()
    result = run_source('format("name:{user.name}", {user:{name:"Ada"}})', env)

    assert result == "name:Ada"


def test_format_field_path_runtime_resolves_multi_level_nested_field():
    env, _, _ = _env()
    result = run_source(
        'format("city:{user.address.city}", '
        '{user:{address:{city:"Bountiful"}}})',
        env,
    )

    assert result == "city:Bountiful"


def test_format_field_path_runtime_mixes_top_level_nested_and_repeated_fields():
    env, _, _ = _env()
    result = run_source(
        'format("{label}:{user.name}/{user.name}", '
        '{label:"student", user:{name:"Ada"}})',
        env,
    )

    assert result == "student:Ada/Ada"


def test_format_field_path_runtime_applies_existing_specs_to_resolved_value():
    env, _, _ = _env()
    debug = run_source('format("{user.name:?}", {user:{name:"Ada"}})', env)
    env2, _, _ = _env()
    padded = run_source('format("{user.score:03}", {user:{score:7}})', env2)

    assert debug == '"Ada"'
    assert padded == "007"
