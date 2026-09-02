from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.host_bridge import _wrap_python_host_callable
from genia.interpreter import run_source
from genia.native_test_runner import run_native_tests
from genia.utf8 import format_display
from genia.values import GeniaOptionErr, symbol


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/r13_validated_pipeline_proving_case.genia"
DOTENV = ROOT / "examples/r13_validated_pipeline_proving_case.env"
KEY = "R13_PROVING_KEY_SENTINEL_676"
PAYLOAD = "R13_PROVING_PAYLOAD_SENTINEL_676"
PURPOSE = "validated_pipeline_outbound"


def _env(*, environment=None, dotenv=None):
    environment_calls = []
    dotenv_calls = []

    def environment_snapshot():
        environment_calls.append("environment")
        return environment or {"METRICS_PORT": "9100"}

    def dotenv_snapshot(path):
        dotenv_calls.append(path)
        if dotenv is not None:
            return dotenv
        return DOTENV.read_bytes()

    env = make_global_env(
        [],
        environment_snapshot_provider=environment_snapshot,
        dotenv_snapshot_provider=dotenv_snapshot,
    )
    return env, environment_calls, dotenv_calls


def _load(env):
    return run_source(EXAMPLE.read_text(encoding="utf-8"), env, filename=str(EXAMPLE))


def _assert_no_sentinels(value):
    rendered = str(value)
    assert KEY not in rendered
    assert PAYLOAD not in rendered


def test_example_and_shared_inventory_exist():
    assert EXAMPLE.is_file()
    assert DOTENV.is_file()
    assert all(
        path.is_file()
        for path in (
            ROOT / "spec/cli/r13-validated-pipeline-proving-case.yaml",
            ROOT / "spec/eval/r13-validated-pipeline-qualified-ports.yaml",
            ROOT / "spec/flow/r13-validated-pipeline-flow.yaml",
            ROOT / "spec/error/r13-validated-pipeline-config-failure.yaml",
        )
    )


def test_example_returns_qualified_ports_clean_records_diagnostics_and_safe_secret():
    env, environment_calls, dotenv_calls = _env()

    result = _load(env)

    assert format_display(result.get("server_port")) == "some(8080)"
    assert format_display(result.get("database_port")) == "some(5432)"
    assert format_display(result.get("metrics_port")) == "some(9100)"
    assert format_display(result.get("clean")) == "[{id: 1, name: Ada}, {id: 2, name: Grace}]"
    assert [format_display(item.get("kind")) for item in result.get("diagnostics")] == [
        "skipped",
        "error",
    ]
    assert result.get("credential") == "<protected>"
    assert result.get("protected_match") is True
    assert environment_calls == ["environment"]
    assert dotenv_calls == ["examples/r13_validated_pipeline_proving_case.env"]
    _assert_no_sentinels(format_display(result))


def test_missing_malformed_and_template_mismatch_preserve_existing_outcomes():
    env, _, _ = _env()
    _load(env)
    empty = run_source("config_provider([]) |> unwrap_or(none)", env)
    malformed = run_source(
        'config_provider([{kind: quote(values), values: {SERVER_PORT: "not-int"}}]) |> unwrap_or(none)',
        env,
    )
    out_of_range = run_source(
        'config_provider([{kind: quote(values), values: {SERVER_PORT: "70000"}}]) |> unwrap_or(none)',
        env,
    )

    assert format_display(env.get("qualified_port")(empty, "SERVER_")) == 'none("config-missing")'
    assert "parse-error" in format_display(env.get("qualified_port")(malformed, "SERVER_"))
    assert format_display(env.get("qualified_port")(out_of_range, "SERVER_")) == 'none("refinement-mismatch")'


def test_matching_authority_reveals_and_attempts_once_only_at_injected_boundary():
    env, _, _ = _env()
    _load(env)
    provider = env.get("provider")
    audits = []
    calls = []
    env.set(
        "authority_fixture",
        create_declassification_authority(provider, [symbol(PURPOSE)], audits.append),
    )
    env.set(
        "outbound_fixture",
        _wrap_python_host_callable(
            "fixture",
            "r13_outbound",
            lambda *args: calls.append(args) or "accepted",
        ),
    )

    result = run_source(
        "authorized_outbound(authority_fixture, provider, fixture_records)", env
    )

    assert result == "accepted"
    assert len(calls) == 1
    assert calls[0][0:4] == (8080, 5432, 9100, PAYLOAD)
    assert calls[0][4] == [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Grace"}]
    assert len(audits) == 1 and audits[0]["success"] is True
    _assert_no_sentinels({k: v for k, v in audits[0].items() if k != "provider_identity"})


@pytest.mark.parametrize("mismatch", ["provider", "purpose"])
def test_authority_mismatch_is_non_revealing_and_prevents_outbound(mismatch):
    env, _, _ = _env()
    _load(env)
    provider = env.get("provider")
    other_env, _, _ = _env()
    _load(other_env)
    authority_provider = other_env.get("provider") if mismatch == "provider" else provider
    purpose = PURPOSE if mismatch == "provider" else "different_purpose"
    audits = []
    calls = []
    env.set(
        "authority_fixture",
        create_declassification_authority(authority_provider, [symbol(purpose)], audits.append),
    )
    env.set(
        "outbound_fixture",
        _wrap_python_host_callable(
            "fixture", "r13_outbound", lambda *_args: calls.append(True)
        ),
    )

    with pytest.raises(TypeError, match="does not permit protected value") as excinfo:
        run_source("authorized_outbound(authority_fixture, provider, fixture_records)", env)

    assert calls == []
    assert len(audits) == 1 and audits[0]["success"] is False
    _assert_no_sentinels(excinfo.value)
    _assert_no_sentinels(audits[0])


def test_provider_failure_and_protected_direct_submission_are_effect_free():
    calls = []
    failing = make_global_env(
        [],
        environment_snapshot_provider=lambda: (_ for _ in ()).throw(
            RuntimeError(f"raw host {KEY} {PAYLOAD}")
        ),
        dotenv_snapshot_provider=lambda _path: b"",
    )
    provider_result = run_source('config_standard({}, [], "fixture.env")', failing)
    assert isinstance(provider_result, GeniaOptionErr)
    assert str(provider_result.reason) == "config-provider-failure"
    _assert_no_sentinels(provider_result)

    env, _, _ = _env()
    _load(env)
    env.set(
        "rejecting_fixture",
        _wrap_python_host_callable(
            "fixture", "reject_protected", lambda *_args: calls.append(True)
        ),
    )
    with pytest.raises(TypeError, match="protected-value") as excinfo:
        run_source("rejecting_fixture(protected_credential(provider) |> unwrap_or(none))", env)
    assert calls == []
    _assert_no_sentinels(excinfo.value)


def test_native_genia_source_visible_composition_passes(capsys):
    fixture = ROOT / "tests/native/r13_validated_pipeline_proving_case.genia"

    exit_code = run_native_tests(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "[PASS] R13 qualified configuration composes with validated records\n"
        "Summary: total=1 passed=1 failed=0 errors=0\n"
    )
    assert captured.err == ""
