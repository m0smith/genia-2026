"""Dedicated subprocess runner for explicit R11 shared-spec fixture cases."""

from __future__ import annotations

import sys

from genia.builtins import make_global_env
from genia.configuration import (
    construct_provider,
    create_declassification_authority,
    get_secret_configuration,
)
from genia.interpreter import run_source
from genia.model import create_fixture_model_provider
from genia.utf8 import format_debug
from genia.values import GeniaMap, GeniaOptionSome, symbol


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _build_env():
    env = make_global_env([])
    descriptor = _map(
        kind=symbol("values"),
        values=_map(R11_MODEL_FIXTURE_KEY="R11_MODEL_FIXTURE_PAYLOAD"),
    )
    provider_result = construct_provider([descriptor], None)
    assert isinstance(provider_result, GeniaOptionSome)
    config_provider = provider_result.value
    credential_result = get_secret_configuration(
        config_provider, "R11_MODEL_FIXTURE_KEY", symbol("model_call")
    )
    assert isinstance(credential_result, GeniaOptionSome)
    authority = create_declassification_authority(
        config_provider, [symbol("model_call")], lambda event: None
    )
    response = _map(
        message=_map(
            role=symbol("assistant"),
            content=_map(kind=symbol("text"), text="fixture reply"),
        ),
        finish_reason=symbol("stop"),
        usage=GeniaOptionSome(
            _map(input_tokens=2, output_tokens=3, total_tokens=5)
        ),
    )
    model_provider = create_fixture_model_provider(
        lambda config, request, secret: GeniaOptionSome(response)
    )
    env.set("model_provider_fixture", model_provider)
    env.set("model_credential_fixture", credential_result.value)
    env.set("model_authority_fixture", authority)
    return env


def main() -> int:
    source = sys.argv[1]
    env = _build_env()
    try:
        result = run_source(source, env, filename="<shared-r11-model-fixture>")
        if result is not None:
            sys.stdout.write(format_debug(result) + "\n")
        return 0
    except Exception as error:  # noqa: BLE001 - command boundary normalization
        sys.stderr.write(f"Error: {error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
