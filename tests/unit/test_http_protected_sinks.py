import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.http_client import perform_http_send
from genia.http_transport import HttpTransportResponse
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import GeniaOptionNone, GeniaOptionSome, symbol

KEY_SENTINEL = "KEY_SENTINEL_625"
PAYLOAD_SENTINEL = "PAYLOAD_SENTINEL_625"
PURPOSE = "http_send"


def _provider_source() -> str:
    return (
        "config_provider([{kind: quote(values), values: {"
        f'{KEY_SENTINEL}: "{PAYLOAD_SENTINEL}"'
        "}}]) |> unwrap_or(none)"
    )


def _provider_and_token(env):
    return run_source(
        f"provider = {_provider_source()}\n"
        f'token = secret_get(provider, "{KEY_SENTINEL}", quote({PURPOSE})) |> unwrap_or(none)\n'
        "[provider, token]",
        env,
    )


def _invoke(fn, args):
    return fn(*args)


def _json_encode(value):
    return GeniaOptionSome("{}")


def test_http_operation_protected_header_survives_display_debug_and_json_attempt_sentinel_free():
    env = make_global_env([])
    result = run_source(
        f"provider = {_provider_source()}\n"
        f'token = secret_get(provider, "{KEY_SENTINEL}", quote({PURPOSE})) |> unwrap_or(none)\n'
        "operation = http_operation(quote(get), \"http://example.invalid\", \"/items\", "
        "{authorization: token}, {}, none(\"http-no-body\")) |> unwrap_or(none)\n"
        "encode_attempt = json_encode(operation)\n"
        "[display(operation), debug_repr(operation), display(encode_attempt), debug_repr(encode_attempt)]",
        env,
    )

    observed = "\n".join(result)
    assert "<protected>" in observed
    assert PAYLOAD_SENTINEL not in observed
    assert KEY_SENTINEL not in observed


def test_http_operation_protected_header_rejects_generic_representation_family_sentinel_free():
    env = make_global_env([])
    protected = run_source(
        f"provider = {_provider_source()}\n"
        f'token = secret_get(provider, "{KEY_SENTINEL}", quote({PURPOSE})) |> unwrap_or(none)\n'
        "operation = http_operation(quote(get), \"http://example.invalid\", \"/items\", "
        "{authorization: token}, {}, none(\"http-no-body\")) |> unwrap_or(none)\n"
        'operation("headers")("authorization")',
        env,
    )

    operations = (
        ("represent", ["secret", PAYLOAD_SENTINEL]),
        ("representation_match", ["secret", protected]),
        ("strip_representation", ["secret", protected]),
    )
    fresh_env = make_global_env([])
    for name, args in operations:
        with pytest.raises(TypeError) as excinfo:
            fresh_env.get(name)(*args)
        text = str(excinfo.value)
        assert text == f'{name} cannot use reserved protected facet "secret"'
        assert PAYLOAD_SENTINEL not in text
        assert KEY_SENTINEL not in text


def test_http_send_full_round_trip_reveals_credential_only_to_transport_sentinel_free():
    env = make_global_env([])
    provider, token = _provider_and_token(env)
    audit_events = []
    authority = create_declassification_authority(provider, [symbol(PURPOSE)], audit_events.append)

    env.set("token_fixture", token)
    operation = run_source(
        "http_operation(quote(get), \"http://example.invalid\", \"/items\", "
        "{authorization: token_fixture}, {}, none(\"http-no-body\")) |> unwrap_or(none)",
        env,
    )

    calls = []

    def fake_transport(request):
        calls.append(request)
        return HttpTransportResponse(status=200, headers={}, body=b"ok")

    result = perform_http_send(
        operation,
        GeniaOptionSome(authority),
        2000,
        json_encode=_json_encode,
        invoke=_invoke,
        transport=fake_transport,
    )

    assert isinstance(result, GeniaOptionSome)
    assert calls[0].headers["authorization"] == PAYLOAD_SENTINEL

    observed = "\n".join(
        [
            str(result.value),
            format_display(operation),
            format_debug(operation),
            repr(audit_events),
        ]
    )
    assert PAYLOAD_SENTINEL not in observed
    assert KEY_SENTINEL not in observed


@pytest.mark.parametrize(
    "case",
    ["mismatched_purpose", "mismatched_provider", "missing_authority"],
)
def test_http_send_unauthorized_protected_placement_fails_closed_sentinel_free(case):
    env = make_global_env([])
    provider, token = _provider_and_token(env)
    env.set("token_fixture", token)
    operation = run_source(
        "http_operation(quote(get), \"http://example.invalid\", \"/items\", "
        "{authorization: token_fixture}, {}, none(\"http-no-body\")) |> unwrap_or(none)",
        env,
    )

    if case == "mismatched_purpose":
        authority_arg = GeniaOptionSome(
            create_declassification_authority(provider, [symbol("different_purpose")], lambda e: None)
        )
    elif case == "mismatched_provider":
        other_provider, _ = _provider_and_token(make_global_env([]))
        authority_arg = GeniaOptionSome(
            create_declassification_authority(other_provider, [symbol(PURPOSE)], lambda e: None)
        )
    else:
        authority_arg = GeniaOptionNone("nil")

    def fake_transport(request):
        raise AssertionError("transport must not be called for unauthorized protected placement")

    with pytest.raises(TypeError) as excinfo:
        perform_http_send(
            operation,
            authority_arg,
            2000,
            json_encode=_json_encode,
            invoke=_invoke,
            transport=fake_transport,
        )

    text = str(excinfo.value)
    assert PAYLOAD_SENTINEL not in text
    assert KEY_SENTINEL not in text


def test_http_response_can_never_carry_protection():
    def fake_transport(request):
        return HttpTransportResponse(status=200, headers={"X-Test": "1"}, body=b"ok")

    env = make_global_env([])
    operation = run_source(
        'http_operation(quote(get), "http://example.invalid", "/items", {}, {}, none("http-no-body")) |> unwrap_or(none)',
        env,
    )

    result = perform_http_send(
        operation,
        GeniaOptionNone("nil"),
        2000,
        json_encode=_json_encode,
        invoke=_invoke,
        transport=fake_transport,
    )

    assert isinstance(result, GeniaOptionSome)
    assert "<protected>" not in format_display(result.value)
