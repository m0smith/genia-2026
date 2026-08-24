import copy

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.host_bridge import _wrap_python_host_callable
from genia.interpreter import run_source
from genia.utf8 import format_debug, format_display
from genia.values import GeniaOptionErr, GeniaProcess, symbol


KEY = "DECLASSIFY_KEY_SENTINEL_593"
PAYLOAD = "DECLASSIFY_PAYLOAD_SENTINEL_593"
PURPOSE = "outbound_api"


def _provider_and_token(env, *, purpose=PURPOSE):
    return run_source(
        "provider = config_provider([{kind: quote(values), values: {"
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)\n"
        f'token = secret_get(provider, "{KEY}", quote({purpose})) |> unwrap_or(none)\n'
        "[provider, token]",
        env,
    )


def _assert_no_secret(value):
    text = str(value)
    assert KEY not in text
    assert PAYLOAD not in text


def test_matching_authority_reveals_once_and_records_non_sensitive_success():
    env = make_global_env([])
    provider, token = _provider_and_token(env)
    events = []
    authority = create_declassification_authority(
        provider, [symbol(PURPOSE)], events.append
    )
    env.set("authority_fixture", authority)
    env.set("token_fixture", token)

    result = run_source("declassify(authority_fixture, token_fixture)", env)

    assert result == PAYLOAD
    assert len(events) == 1
    assert events[0]["success"] is True
    assert events[0]["purpose"] == PURPOSE
    assert events[0]["provider_identity"] is provider._identity
    _assert_no_secret({k: v for k, v in events[0].items() if k != "provider_identity"})


@pytest.mark.parametrize("mismatch", ["provider", "purpose"])
def test_valid_but_mismatched_authority_fails_closed_and_audits(mismatch):
    env = make_global_env([])
    provider, token = _provider_and_token(env)
    events = []
    if mismatch == "provider":
        other_provider, _ = _provider_and_token(make_global_env([]))
        authority = create_declassification_authority(
            other_provider, [symbol(PURPOSE)], events.append
        )
    else:
        authority = create_declassification_authority(
            provider, [symbol("different_use")], events.append
        )
    env.set("authority_fixture", authority)
    env.set("token_fixture", token)

    with pytest.raises(TypeError, match="does not permit protected value") as excinfo:
        run_source("declassify(authority_fixture, token_fixture)", env)

    assert len(events) == 1 and events[0]["success"] is False
    _assert_no_secret(excinfo.value)
    _assert_no_secret(events[0])


def test_invalid_authority_and_non_protected_value_are_non_revealing_misuse():
    env = make_global_env([])
    provider, token = _provider_and_token(env)
    events = []
    authority = create_declassification_authority(
        provider, [symbol(PURPOSE)], events.append
    )
    env.set("token_fixture", token)
    env.set("authority_fixture", authority)

    with pytest.raises(TypeError, match="expected a declassification authority"):
        run_source('declassify("ordinary", token_fixture)', env)
    with pytest.raises(TypeError, match="expected a protected value") as excinfo:
        run_source('declassify(authority_fixture, "ordinary")', env)

    assert len(events) == 1 and events[0]["success"] is False
    _assert_no_secret(excinfo.value)


def test_authority_is_opaque_noncopyable_and_rejected_by_data_boundaries():
    env = make_global_env([])
    provider, _ = _provider_and_token(env)
    authority = create_declassification_authority(
        provider, [symbol(PURPOSE)], lambda event: None
    )
    env.set("authority_fixture", authority)

    assert format_display(authority) == "<declassification-authority>"
    assert format_debug(authority) == "<declassification-authority>"
    with pytest.raises(TypeError, match="cannot be copied"):
        copy.copy(authority)

    encoded = run_source("json_encode(authority_fixture)", env)
    assert isinstance(encoded, GeniaOptionErr)
    with pytest.raises(TypeError, match="authority"):
        run_source('sheet([["authority", [authority_fixture]]])', env)
    with pytest.raises(TypeError, match="authority"):
        _wrap_python_host_callable("fixture", "use", lambda value: value)(authority)

    process = GeniaProcess(lambda message: None)
    with pytest.raises(TypeError, match="authority"):
        process.send(authority)


def test_narrow_host_boundary_receives_only_explicitly_declassified_payload():
    env = make_global_env([])
    provider, token = _provider_and_token(env)
    events = []
    calls = []
    authority = create_declassification_authority(
        provider, [symbol(PURPOSE)], events.append
    )
    env.set("authority_fixture", authority)
    env.set("token_fixture", token)

    ordinary = run_source("declassify(authority_fixture, token_fixture)", env)
    result = _wrap_python_host_callable(
        "fixture", "authorized_call", lambda value: calls.append(value) or "ok"
    )(ordinary)

    assert result == "ok"
    assert calls == [PAYLOAD]
    assert len(events) == 1 and events[0]["success"] is True
