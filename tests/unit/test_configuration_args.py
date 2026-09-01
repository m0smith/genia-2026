import pytest

from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome, GeniaSymbol


def _config_args(args):
    return make_global_env([]).get("config_args")(args)


def _map_items(value):
    assert isinstance(value, GeniaMap)
    return value.items()


def test_config_args_normalizes_explicit_arguments():
    cases = [
        ([], []),
        (["--"], []),
        (["--", "8080"], []),
        (["--port", "8080"], [("PORT", "8080")]),
        (
            ["--db-port", "5432", "--Db-Host2", "primary"],
            [("DB_PORT", "5432"), ("DB_HOST2", "primary")],
        ),
        (["--empty", "", "--option-looking", "--value"], [("EMPTY", ""), ("OPTION_LOOKING", "--value")]),
        (["--unknown9", "value", "--", "ignored", "--bad_name"], [("UNKNOWN9", "value")]),
    ]
    for args, expected in cases:
        result = _config_args(args)

        assert isinstance(result, GeniaOptionSome)
        descriptor = result.value
        assert isinstance(descriptor, GeniaMap)
        assert descriptor.get("kind") == GeniaSymbol("values")
        assert _map_items(descriptor.get("values")) == expected


def test_config_args_malformed_data_returns_exact_non_sensitive_error():
    cases = [
        ["position", "value"],
        ["--port"],
        ["--port=8080", "value"],
        ["-p", "8080"],
        ["--bad_name", "value"],
        ["--bad--name", "value"],
        ["--9port", "value"],
        ["--pórt", "value"],
        ["--port", "1", "--port", "2"],
        ["--Db-Port", "1", "--db-port", "2"],
    ]
    for args in cases:
        result = _config_args(args)

        assert isinstance(result, GeniaOptionErr)
        assert result.reason == "config-source-invalid"
        assert result.context.items() == [
            ("source_kind", GeniaSymbol("arguments")),
            ("stage", GeniaSymbol("parse")),
        ]
        rendered = repr(result)
        for sentinel in ("position", "port", "8080", "bad_name", "pórt", "Db-Port"):
            assert sentinel not in rendered


@pytest.mark.parametrize("args", [None, {}, "--port", ["--port", 8080]])
def test_config_args_type_misuse_raises_without_rejected_content(args):
    with pytest.raises(TypeError, match="config_args expected") as excinfo:
        _config_args(args)

    assert "8080" not in str(excinfo.value)


def test_config_args_snapshots_into_fresh_result_data():
    args = ["--port", "8080"]
    first = _config_args(args)
    args[:] = ["--port", "9090"]
    second = _config_args(args)

    assert first.value.get("values").get("PORT") == "8080"
    assert second.value.get("values").get("PORT") == "9090"
    assert first.value is not second.value
    assert first.value.get("values") is not second.value.get("values")


def test_config_args_is_an_ordinary_call_in_source():
    result = run_source(
        'config_args(["--server-port", "8080", "--", "input.jsonl"])',
        make_global_env([]),
    )

    assert isinstance(result, GeniaOptionSome)
    assert result.value.get("values").get("SERVER_PORT") == "8080"
