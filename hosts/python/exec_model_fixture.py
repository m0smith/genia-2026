"""Dedicated subprocess runner for explicit R11 shared-spec fixture cases."""

from __future__ import annotations

import sys
from pathlib import Path

from genia.builtins import make_global_env
from genia.configuration import (
    construct_provider,
    create_declassification_authority,
    get_secret_configuration,
)
from genia import interpreter as genia_interpreter
from genia.model import create_fixture_model_provider
from genia.utf8 import format_debug
from genia.values import GeniaMap, GeniaOptionSome, symbol


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _build_env(*, stdin_data=None):
    env = make_global_env(stdin_data or [])
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
    def fixture_response(config, request, secret):
        output_kind = request.get("output").get("kind")
        text = "fixture reply"
        if output_kind == symbol("json"):
            text = "{" if config.get("id") == "fixture-malformed-json" else "7"
        response = _map(
            message=_map(
                role=symbol("assistant"),
                content=_map(kind=symbol("text"), text=text),
            ),
            finish_reason=symbol("stop"),
            usage=GeniaOptionSome(
                _map(input_tokens=2, output_tokens=3, total_tokens=5)
            ),
        )
        return GeniaOptionSome(response)
    model_provider = create_fixture_model_provider(fixture_response)
    env.set("model_provider_fixture", model_provider)
    env.set("model_credential_fixture", credential_result.value)
    env.set("model_authority_fixture", authority)
    return env


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 1:
        mode, value = "--command", args[0]
    elif len(args) == 2 and args[0] in ("--command", "--file", "--pipe"):
        mode, value = args
    else:
        raise SystemExit("expected source or --command/--file/--pipe VALUE")
    stdin_data = sys.stdin.read().splitlines() if mode == "--pipe" else []
    env = _build_env(stdin_data=stdin_data)
    source = Path(value).read_text(encoding="utf-8") if mode == "--file" else value
    filename = str(Path(value).resolve()) if mode == "--file" else "<shared-r11-model-fixture>"
    if mode == "--pipe":
        source = genia_interpreter._wrap_pipe_mode_expr(source)
        filename = "<pipe>"
    try:
        result = genia_interpreter.run_source(
            source, env, filename=filename
        )
        if result is not None:
            sys.stdout.write(format_debug(result) + "\n")
        return 0
    except Exception as error:  # noqa: BLE001 - command boundary normalization
        sys.stderr.write(f"Error: {error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
