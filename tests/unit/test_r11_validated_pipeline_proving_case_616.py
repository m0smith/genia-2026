from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.interpreter import run_source
from genia.model import create_fixture_model_provider
from genia.native_test_runner import run_native_tests
from genia.utf8 import format_display
from genia.values import (
    GeniaMap,
    GeniaOptionErr,
    GeniaOptionSome,
    GeniaRepresented,
    make_none,
    symbol,
)


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/r11_validated_pipeline_proving_case.genia"
KEY = "R11_PIPELINE_KEY_SENTINEL_616"
PAYLOAD = "R11_PIPELINE_PAYLOAD_SENTINEL_616"


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _response(text):
    return _map(
        message=_map(
            role=symbol("assistant"),
            content=_map(kind=symbol("text"), text=text),
        ),
        finish_reason=symbol("stop"),
        usage=GeniaOptionSome(
            _map(input_tokens=4, output_tokens=3, total_tokens=7)
        ),
    )


def _env(handler, *, matching_authority=True):
    env = make_global_env([])
    provider = run_source(
        'config_provider([{kind: quote(values), values: {'
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)",
        env,
    )
    env.set("pipeline_config_provider_fixture", provider)
    credential = run_source(
        f'secret_get(pipeline_config_provider_fixture, "{KEY}", quote(model_call)) '
        "|> unwrap_or(none)",
        env,
    )
    authority_provider = provider
    if not matching_authority:
        authority_provider = run_source(
            'config_provider([{kind: quote(values), values: {OTHER: "x"}}]) '
            "|> unwrap_or(none)",
            env,
        )
    audits = []
    authority = create_declassification_authority(
        authority_provider, [symbol("model_call")], audits.append
    )
    fixture = create_fixture_model_provider(handler)
    env.set("model_provider_fixture", fixture)
    env.set("model_credential_fixture", credential)
    env.set("model_authority_fixture", authority)
    return env, fixture, audits


def _load(env):
    source = EXAMPLE.read_text(encoding="utf-8")
    return run_source(source, env, filename=str(EXAMPLE))


def _assert_no_sentinels(value):
    rendered = repr(value)
    assert KEY not in rendered
    assert PAYLOAD not in rendered


def test_example_and_shared_inventory_exist():
    assert EXAMPLE.is_file()
    assert all(path.is_file() for path in (
        ROOT / "spec/cli/r11-validated-pipeline-proving-case.yaml",
        ROOT / "spec/eval/r11-validated-pipeline-structured-success.yaml",
        ROOT / "spec/flow/r11-validated-pipeline-flow.yaml",
        ROOT / "spec/error/r11-validated-pipeline-structured-failure.yaml",
    ))


def test_mixed_records_produce_structured_clean_values_and_useful_diagnostics():
    env, fixture, audits = _env(
        lambda config, request, secret: GeniaOptionSome(
            _response('{"id":7,"label":"fixture"}')
        )
    )

    result = _load(env)

    clean = result.get("clean")
    diagnostics = result.get("diagnostics")
    assert fixture.attempt_count == 2
    assert len(audits) == 2 and all(event["success"] for event in audits)
    assert len(clean) == 2
    assert all(isinstance(value, GeniaRepresented) for value in clean)
    assert [value.value.get("label") for value in clean] == ["fixture", "fixture"]
    assert len(diagnostics) == 3
    assert [format_display(item.get("kind")) for item in diagnostics] == [
        "skipped",
        "error",
        "error",
    ]
    _assert_no_sentinels(result)
    _assert_no_sentinels(audits)


@pytest.mark.parametrize(
    "outcome",
    [
        make_none("model-no-response"),
        GeniaOptionErr("model-rejected", _map(kind=symbol("policy"))),
        GeniaOptionErr(
            "model-rate-limited",
            _map(retry_after_ms=make_none("model-retry-after-unavailable")),
        ),
        GeniaOptionErr("model-transport-failure", _map(kind=symbol("unavailable"))),
    ],
)
def test_normalized_model_failures_become_diagnostics_without_retry(outcome):
    env, fixture, audits = _env(lambda config, request, secret: outcome)

    result = _load(env)

    assert fixture.attempt_count == 2
    assert len(audits) == 2
    assert result.get("clean") == []
    assert len(result.get("diagnostics")) == 5
    _assert_no_sentinels(result)


@pytest.mark.parametrize("text", ["{", '{"id":"wrong","label":"fixture"}'])
def test_invalid_structured_output_is_normalized_once_per_valid_record(text):
    env, fixture, audits = _env(
        lambda config, request, secret: GeniaOptionSome(_response(text))
    )

    result = _load(env)

    assert fixture.attempt_count == 2
    assert len(audits) == 2
    assert result.get("clean") == []
    rendered = format_display(result.get("diagnostics"))
    assert "model-structured-output-invalid" in rendered
    _assert_no_sentinels(rendered)


def test_protected_boundary_failure_prevents_attempt_and_leaks_nothing():
    env, fixture, audits = _env(
        lambda config, request, secret: GeniaOptionSome(_response("{}")),
        matching_authority=False,
    )

    with pytest.raises(TypeError, match="does not permit protected value") as excinfo:
        _load(env)

    assert fixture.attempt_count == 0
    assert len(audits) == 1 and audits[0]["success"] is False
    _assert_no_sentinels(excinfo.value)
    _assert_no_sentinels(audits)


def test_raw_fixture_exception_normalizes_without_retry_or_leak():
    def fail(config, request, secret):
        raise RuntimeError(f"raw provider failure {KEY} {PAYLOAD}")

    env, fixture, audits = _env(fail)
    result = _load(env)

    assert fixture.attempt_count == 2
    assert len(audits) == 2
    assert result.get("clean") == []
    assert "model-transport-failure" in format_display(result.get("diagnostics"))
    _assert_no_sentinels(result)


def test_native_genia_source_visible_composition_passes(capsys):
    fixture = ROOT / "tests/native/r11_validated_pipeline_proving_case.genia"

    exit_code = run_native_tests(str(fixture))

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (
        "[PASS] R11 model-shaped Outcomes compose with validated JSONL records\n"
        "Summary: total=1 passed=1 failed=0 errors=0\n"
    )
    assert captured.err == ""
