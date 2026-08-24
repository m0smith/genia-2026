from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.host_bridge import _wrap_python_host_callable
from genia.interpreter import run_source
from genia.utf8 import format_display
from genia.values import GeniaOptionErr, symbol


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "r10_validated_pipeline_proving_case.genia"
KEY = "R10_PROVING_KEY_SENTINEL_595"
PAYLOAD = "R10_PROVING_PAYLOAD_SENTINEL_595"
PURPOSE = "validated_pipeline_outbound"


def _load_example(env=None):
    active_env = env or make_global_env(environment_snapshot_provider=None)
    source = EXAMPLE.read_text(encoding="utf-8")
    result = run_source(source, active_env, filename=str(EXAMPLE))
    return active_env, result


def _assert_no_sentinels(value):
    rendered = str(value)
    assert KEY not in rendered
    assert PAYLOAD not in rendered


def test_example_runs_and_returns_validated_configuration_records_and_safe_observations():
    _env, result = _load_example()

    assert format_display(result.get("port")) == "some(8080)"
    assert format_display(result.get("endpoint")) == "some(https://fixture.invalid/v1)"
    assert format_display(result.get("clean")) == "[{id: 1, name: Ada}, {id: 2, name: Grace}]"
    diagnostics = result.get("diagnostics")
    assert len(diagnostics) == 2
    assert format_display(diagnostics[0].get("kind")) == "skipped"
    assert format_display(diagnostics[0].get("reason")) == "blank_line"
    assert format_display(diagnostics[1].get("kind")) == "error"
    assert format_display(diagnostics[1].get("reason")) == "record_validation_failed"
    assert result.get("credential") == "<protected>"
    assert result.get("protected_match") is True
    _assert_no_sentinels(format_display(result))


def test_example_missing_and_invalid_configuration_preserve_existing_outcomes():
    env, _ = _load_example()

    assert format_display(run_source("validated_port(config_provider([]) |> unwrap_or(none))", env)) == 'none("config-missing")'
    invalid = run_source(
        'validated_port(config_provider([{kind: quote(values), values: {PORT: "not-int"}}]) |> unwrap_or(none))',
        env,
    )
    out_of_range = run_source(
        'validated_port(config_provider([{kind: quote(values), values: {PORT: "70000"}}]) |> unwrap_or(none))',
        env,
    )

    assert format_display(invalid) == 'none("invalid-integer")'
    assert format_display(out_of_range) == 'none("refinement-mismatch")'
    _assert_no_sentinels([invalid, out_of_range])


def test_matching_authority_declassifies_at_fixture_boundary_and_returns_ordinary_receipt():
    env, _ = _load_example()
    provider = env.get("provider")
    events = []
    calls = []
    authority = create_declassification_authority(
        provider, [symbol(PURPOSE)], events.append
    )
    outbound = _wrap_python_host_callable(
        "fixture",
        "validated_outbound",
        lambda endpoint, port, credential, records: calls.append(
            [endpoint, port, credential, records]
        )
        or "accepted",
    )
    env.set("authority_fixture", authority)
    env.set("outbound_fixture", outbound)

    result = run_source(
        "authorized_outbound(authority_fixture, provider, fixture_records)", env
    )

    assert result == "accepted"
    assert len(calls) == 1
    assert calls[0][0:3] == ["https://fixture.invalid/v1", 8080, PAYLOAD]
    assert format_display(calls[0][3]) == "[{id: 1, name: Ada}, {id: 2, name: Grace}]"
    assert len(events) == 1 and events[0]["success"] is True
    _assert_no_sentinels({k: v for k, v in events[0].items() if k != "provider_identity"})


@pytest.mark.parametrize("mismatch", ["provider", "purpose"])
def test_authority_mismatch_is_non_revealing_and_prevents_outbound_call(mismatch):
    env, _ = _load_example()
    provider = env.get("provider")
    other_env, _ = _load_example()
    authority_provider = other_env.get("provider") if mismatch == "provider" else provider
    allowed_purpose = PURPOSE if mismatch == "provider" else "different_purpose"
    events = []
    calls = []
    authority = create_declassification_authority(
        authority_provider, [symbol(allowed_purpose)], events.append
    )
    env.set("authority_fixture", authority)
    env.set(
        "outbound_fixture",
        _wrap_python_host_callable(
            "fixture", "validated_outbound", lambda *_args: calls.append(True)
        ),
    )

    with pytest.raises(TypeError, match="does not permit protected value") as excinfo:
        run_source(
            "authorized_outbound(authority_fixture, provider, fixture_records)", env
        )

    assert calls == []
    assert len(events) == 1 and events[0]["success"] is False
    _assert_no_sentinels(excinfo.value)
    _assert_no_sentinels(events[0])


def test_protected_host_submission_and_provider_failure_are_effect_free_and_normalized():
    env, _ = _load_example()
    calls = []
    env.set(
        "rejecting_fixture",
        _wrap_python_host_callable(
            "fixture", "reject_protected", lambda *_args: calls.append(True)
        ),
    )

    with pytest.raises(TypeError, match="protected-value") as excinfo:
        run_source(
            'rejecting_fixture(secret_get(provider, "R10_PROVING_KEY_SENTINEL_595", quote(validated_pipeline_outbound)) |> unwrap_or(none))',
            env,
        )

    assert calls == []
    _assert_no_sentinels(excinfo.value)

    failing_env = make_global_env(
        environment_snapshot_provider=lambda: (_ for _ in ()).throw(
            RuntimeError(f"host failed with {KEY} and {PAYLOAD}")
        )
    )
    provider_result = run_source(
        "config_provider([{kind: quote(environment)}])", failing_env
    )
    assert isinstance(provider_result, GeniaOptionErr)
    assert str(provider_result.reason) == "config-provider-failure"
    assert provider_result.context.get("source_index") == 0
    _assert_no_sentinels(provider_result)
