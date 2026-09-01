from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.configuration import construct_provider
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome, GeniaProtected, GeniaSymbol


def _symbol(name: str) -> GeniaSymbol:
    return GeniaSymbol(name)


def _dotenv(path: str = "fixture.env", required: bool = True, **extra):
    descriptor = (
        GeniaMap()
        .put("kind", _symbol("dotenv"))
        .put("path", path)
        .put("required", required)
    )
    for key, value in extra.items():
        descriptor = descriptor.put(key, value)
    return descriptor


def _provider(content: bytes, *, path: str = "fixture.env"):
    calls = []

    def snapshot(requested_path: str) -> bytes:
        calls.append(requested_path)
        return content

    result = construct_provider([_dotenv(path)], lambda: {}, snapshot)
    return result, calls


def _context(index: int, stage: str) -> list[list[object]]:
    return [
        ["source_index", index],
        ["source_kind", _symbol("dotenv")],
        ["stage", _symbol(stage)],
    ]


def test_dotenv_accepts_the_complete_valid_grammar_and_exact_values():
    result, calls = _provider(
        b'\xef\xbb\xbf# heading\r\n'
        b'  \t# indented comment\n'
        b'ALPHA = plain value \t # comment\n'
        b'_EMPTY=\n'
        b'SINGLE=\' # = " \\ literal\' # comment\r\n'
        b'DOUBLE="slash\\\\ quote\\" lf\\n cr\\r tab\\t"\n'
        b'EMPTY_SINGLE=\'\'\n'
        b'EMPTY_DOUBLE=""\n'
        b'LAST=value'
    )

    assert isinstance(result, GeniaOptionSome)
    assert calls == ["fixture.env"]
    provider = result.value
    assert provider.lookup("ALPHA", None) == "plain value"
    assert provider.lookup("_EMPTY", None) == ""
    assert provider.lookup("SINGLE", None) == ' # = " \\ literal'
    assert provider.lookup("DOUBLE", None) == 'slash\\ quote" lf\n cr\r tab\t'
    assert provider.lookup("EMPTY_SINGLE", None) == ""
    assert provider.lookup("EMPTY_DOUBLE", None) == ""
    assert provider.lookup("LAST", None) == "value"


@pytest.mark.parametrize(
    "content",
    [
        b"A=1\rB=2",
        b"1A=value",
        b"A-B=value",
        b"A value",
        b"A=value#not-a-comment",
        b"A=unquoted\\value",
        b"A=unquoted'value",
        b'A=unquoted"value',
        b"A='unterminated",
        b"A='closed' trailing",
        b'A="unterminated',
        b'A="bad\\q"',
        b'A="closed" trailing',
        b'A="literal\nnewline"',
        b"A=value\nA=other",
        b"A=value\n\xef\xbb\xbfB=other",
        "A=value\u00a0#comment".encode(),
    ],
)
def test_dotenv_rejects_each_malformed_grammar_family_without_partial_provider(content):
    result, calls = _provider(content)

    assert calls == ["fixture.env"]
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "config-source-invalid"
    assert result.context.items() == _context(0, "parse")


def test_dotenv_rejects_invalid_utf8_at_decode_stage():
    result, _ = _provider(b"A=ok\nB=\xff")

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "config-source-invalid"
    assert result.context.items() == _context(0, "decode")


@pytest.mark.parametrize(
    "descriptor",
    [
        GeniaMap().put("kind", _symbol("dotenv")),
        _dotenv(path=""),
        _dotenv(path="SAFE\0PATH"),
        _dotenv(required=1),
        _dotenv(extra="value"),
    ],
)
def test_invalid_dotenv_descriptor_is_runtime_misuse_before_any_acquisition(descriptor):
    calls = []

    with pytest.raises(TypeError, match="config_provider expected a valid dotenv descriptor") as excinfo:
        construct_provider(
            [descriptor],
            lambda: calls.append("environment") or {},
            lambda path: calls.append(path) or b"",
        )

    assert calls == []
    assert "SAFE" not in str(excinfo.value)


def test_all_descriptors_validate_before_dotenv_or_environment_acquisition():
    calls = []
    invalid_literal = GeniaMap().put("kind", _symbol("values")).put("values", 1)

    with pytest.raises(TypeError):
        construct_provider(
            [_dotenv(), invalid_literal],
            lambda: calls.append("environment") or {},
            lambda path: calls.append(path) or b"A=1",
        )

    assert calls == []


def test_optional_and_required_missing_dotenv_are_distinct_and_keep_source_index():
    def missing(path: str) -> bytes:
        raise FileNotFoundError("RAW PATH MUST NOT LEAK")

    optional = construct_provider(
        [GeniaMap().put("kind", _symbol("values")).put("values", GeniaMap()), _dotenv(required=False)],
        lambda: {},
        missing,
    )
    required = construct_provider([_dotenv(required=True)], lambda: {}, missing)

    assert isinstance(optional, GeniaOptionSome)
    assert optional.value.lookup("ANY", None) is None
    assert isinstance(required, GeniaOptionErr)
    assert required.reason == "config-provider-failure"
    assert required.context.items() == _context(0, "acquire")
    assert "RAW PATH" not in format_debug(required)


def test_unavailable_and_host_read_failures_are_normalized_without_sentinels():
    unavailable = construct_provider([_dotenv(required=False)], lambda: {}, None)

    def failed(path: str) -> bytes:
        raise PermissionError("RAW_HOST_SENTINEL_673")

    read_failed = construct_provider([_dotenv("PATH_SENTINEL_673")], lambda: {}, failed)

    assert unavailable.reason == "config-source-unavailable"
    assert unavailable.context.items() == _context(0, "acquire")
    assert read_failed.reason == "config-provider-failure"
    assert read_failed.context.items() == _context(0, "acquire")
    rendered = format_debug(read_failed)
    assert "RAW_HOST_SENTINEL_673" not in rendered
    assert "PATH_SENTINEL_673" not in rendered


def test_non_bytes_capability_result_is_a_normalized_host_read_failure():
    result = construct_provider([_dotenv()], lambda: {}, lambda path: "A=value")

    assert result.reason == "config-provider-failure"
    assert result.context.items() == _context(0, "acquire")


def test_dotenv_sources_acquire_in_order_and_existing_precedence_is_unchanged():
    calls = []
    contents = {"first.env": b"PORT=9000", "second.env": b"PORT=8080"}

    def snapshot(path: str) -> bytes:
        calls.append(path)
        return contents[path]

    result = construct_provider(
        [_dotenv("first.env"), _dotenv("second.env")], lambda: {}, snapshot
    )

    assert calls == ["first.env", "second.env"]
    assert result.value.lookup("PORT", None) == "9000"


def test_default_python_capability_reads_once_and_provider_snapshot_ignores_mutation(tmp_path):
    path = tmp_path / "application.env"
    path.write_bytes(b"PORT=before")
    env = make_global_env([])
    source = f'config_provider([{{kind: quote(dotenv), path: "{path}", required: true}}]) |> unwrap_or(none)'
    provider = run_source(source, env)

    path.write_bytes(b"PORT=after")
    old_value = env.get("config_get")(provider, "PORT")
    new_provider = run_source(source, env)
    new_value = env.get("config_get")(new_provider, "PORT")

    assert old_value.value == "before"
    assert new_value.value == "after"


def test_dotenv_secret_acquisition_uses_existing_r10_protected_boundary(tmp_path):
    path = tmp_path / "secret.env"
    path.write_bytes(b"API_KEY=PAYLOAD_SENTINEL_673")
    result = run_source(
        f'''
        provider = config_provider([{{kind: quote(dotenv), path: "{path}", required: true}}]) |> unwrap_or(none)
        secret_get(provider, "API_KEY", quote(outbound)) |> unwrap_or(none)
        ''',
        make_global_env([]),
    )

    assert isinstance(result, GeniaProtected)
    assert format_display(result) == "<protected>"
    assert "PAYLOAD_SENTINEL_673" not in format_debug(result)


def test_parser_failure_diagnostics_recursively_exclude_path_key_value_and_content():
    sentinels = ["PATH_SENTINEL_673", "KEY_SENTINEL_673", "VALUE_SENTINEL_673"]
    content = b"KEY_SENTINEL_673=VALUE_SENTINEL_673\\invalid"
    result, _ = _provider(content, path=sentinels[0])

    assert result.reason == "config-source-invalid"
    rendered = format_debug(result)
    assert all(sentinel not in rendered for sentinel in sentinels)
