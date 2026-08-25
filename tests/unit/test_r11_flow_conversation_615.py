from pathlib import Path

import pytest

from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.interpreter import run_source
from genia.model import create_fixture_model_provider
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionSome, symbol


ROOT = Path(__file__).resolve().parents[2]
APPLICATION = ROOT / "examples/r11_flow_conversation.genia"


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _response(text="fixture reply"):
    return _map(
        message=_map(
            role=symbol("assistant"),
            content=_map(kind=symbol("text"), text=text),
        ),
        finish_reason=symbol("stop"),
        usage=GeniaOptionSome(
            _map(input_tokens=2, output_tokens=3, total_tokens=5)
        ),
    )


def _env(handler):
    env = make_global_env([])
    provider = run_source(
        'config_provider([{kind: quote(values), values: {KEY: "secret"}}]) '
        "|> unwrap_or(none)",
        env,
    )
    env.set("provider_fixture", provider)
    credential = run_source(
        'secret_get(provider_fixture, "KEY", quote(model_call)) |> unwrap_or(none)',
        env,
    )
    fixture = create_fixture_model_provider(handler)
    authority = create_declassification_authority(
        provider, [symbol("model_call")], lambda event: None
    )
    env.set("model_provider_fixture", fixture)
    env.set("model_credential_fixture", credential)
    env.set("model_authority_fixture", authority)
    return env, fixture


def _source(expression):
    application = APPLICATION.read_text(encoding="utf-8")
    return application + "\n" + expression


MODEL_AND_PROMPT = """
m = model(model_provider_fixture, {id: "fixture-text", timeout_ms: 1000}, model_credential_fixture, model_authority_fixture)
prompt = (messages) -> {messages: messages, output: {kind: quote(text)}}
step = (state, input) -> conversation_step(m, prompt, state, input)
message = (text) -> {kind: quote(message), message: {role: quote(user), content: {kind: quote(text), text: text}}}
"""


def test_application_module_exists_before_conversation_contract_can_pass():
    assert APPLICATION.is_file()


def test_list_and_flow_sources_produce_equal_exact_state_sequences():
    env, fixture = _env(lambda config, request, secret: GeniaOptionSome(_response()))
    result = run_source(
        _source(
            MODEL_AND_PROMPT
            + """
inputs = [message("one"), message("two"), {kind: quote(stop), reason: "done"}, message("ignored")]
list_states = scan(step, conversation_initial_state, inputs)
flow_states = inputs |> lines |> scan(step, conversation_initial_state) |> collect
[list_states == flow_states, list_states]
"""
        ),
        env,
    )
    assert result[0] is True
    assert fixture.attempt_count == 4
    states = result[1]
    assert len(states) == 4
    assert states[1].get("turn") == 2
    assert states[2].get("status") == symbol("stopped")
    assert states[2] == states[3]


def test_failed_model_outcome_appends_no_assistant_and_later_input_is_inert():
    outcome = GeniaOptionErr("model-timeout", _map(timeout_ms=1000))
    env, fixture = _env(lambda config, request, secret: outcome)
    result = run_source(
        _source(
            MODEL_AND_PROMPT
            + 'scan(step, conversation_initial_state, [message("one"), message("ignored")])'
        ),
        env,
    )
    assert fixture.attempt_count == 1
    assert result[0].get("status") == symbol("failed")
    assert result[0].get("turn") == 1
    assert len(result[0].get("messages")) == 1
    assert result[0] == result[1]


def test_lazy_flow_attempts_only_for_consumed_active_messages():
    env, fixture = _env(lambda config, request, secret: GeniaOptionSome(_response()))
    run_source(
        _source(
            MODEL_AND_PROMPT
            + 'states = [message("one"), message("two")] |> lines |> scan(step, conversation_initial_state)'
        ),
        env,
    )
    assert fixture.attempt_count == 0

    env, fixture = _env(lambda config, request, secret: GeniaOptionSome(_response()))
    result = run_source(
        _source(
            MODEL_AND_PROMPT
            + '[message("one"), message("two")] |> lines |> scan(step, conversation_initial_state) |> take(1) |> collect'
        ),
        env,
    )
    assert len(result) == 1
    assert fixture.attempt_count == 1


def test_distinct_deterministic_fixture_producers_are_source_independent():
    expression = _source(
        MODEL_AND_PROMPT
        + '[message("same")] |> scan(step, conversation_initial_state)'
    )
    observed = []
    for _ in range(2):
        env, fixture = _env(
            lambda config, request, secret: GeniaOptionSome(_response("same reply"))
        )
        observed.append(run_source(expression, env))
        assert fixture.attempt_count == 1
    assert observed[0] == observed[1]
