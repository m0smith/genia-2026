"""Dedicated subprocess runner for explicit deterministic R12 shared fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

from genia import interpreter as genia_interpreter
from genia.builtins import make_global_env
from genia.configuration import construct_provider, create_declassification_authority, get_secret_configuration
from genia.model import create_fixture_model_provider
from genia.retrieval import (
    create_fixture_embed_provider,
    create_fixture_index_provider,
    create_fixture_index_result,
    create_fixture_rerank_provider,
    create_fixture_rerank_result,
    create_fixture_retrieve_provider,
    create_fixture_retrieve_result,
)
from genia.utf8 import format_debug
from genia.values import GeniaMap, GeniaOptionSome, symbol


def _map(**values):
    result = GeniaMap()
    for key, value in values.items():
        result = result.put(key, value)
    return result


def _build_env(*, stdin_data=None, observations=None):
    env = make_global_env(stdin_data or [])
    observations = observations if observations is not None else {}
    observations.setdefault("audits", [])
    purposes = ("embed_call", "index_call", "retrieve_call", "rerank_call", "model_call")
    values = _map(**{f"R12_{purpose.upper()}": f"fixture-{purpose}" for purpose in purposes})
    provider_result = construct_provider([_map(kind=symbol("values"), values=values)], None)
    assert isinstance(provider_result, GeniaOptionSome)
    config_provider = provider_result.value
    for purpose in purposes:
        credential = get_secret_configuration(config_provider, f"R12_{purpose.upper()}", symbol(purpose))
        assert isinstance(credential, GeniaOptionSome)
        env.set(purpose.replace("_call", "_credential_fixture"), credential.value)
        env.set(
            purpose.replace("_call", "_authority_fixture"),
            create_declassification_authority(
                config_provider,
                [symbol(purpose)],
                lambda event, concern=purpose: observations["audits"].append((concern, event)),
            ),
        )

    def embed_response(_config, value, _secret):
        embedding = _map(vector=[1.0, 0.0], dims=2, space="fixture-space-v1")
        identity = value.get("text") if value.get("kind") == symbol("query") else value.get("chunk")
        key = "text" if value.get("kind") == symbol("query") else "chunk"
        return GeniaOptionSome(_map(**{key: identity, "embedding": embedding}))

    backend = []
    index_provider = create_fixture_index_provider(
        lambda _config, corpus, _secret: (backend.clear(), backend.extend(corpus), GeniaOptionSome(create_fixture_index_result(backend)))[2]
    )
    retrieve_provider = create_fixture_retrieve_provider(
        index_provider,
        lambda _config, stored, _query, k, _secret: GeniaOptionSome(
            create_fixture_retrieve_result([_map(chunk=item.get("chunk"), score=1.0) for item in stored[:k]])
        ),
    )
    rerank_provider = create_fixture_rerank_provider(
        lambda _config, _query, evidence, _secret: GeniaOptionSome(create_fixture_rerank_result(evidence))
    )
    model_provider = create_fixture_model_provider(
        lambda _config, _request, _secret: GeniaOptionSome(
            _map(
                message=_map(role=symbol("assistant"), content=_map(kind=symbol("text"), text="Ada wrote notes.")),
                finish_reason=symbol("stop"),
                usage=GeniaOptionSome(_map(input_tokens=3, output_tokens=3, total_tokens=6)),
            )
        )
    )
    env.set("embed_provider_fixture", create_fixture_embed_provider(embed_response))
    env.set("index_provider_fixture", index_provider)
    env.set("retrieve_provider_fixture", retrieve_provider)
    env.set("rerank_provider_fixture", rerank_provider)
    env.set("model_provider_fixture", model_provider)
    observations["providers"] = {
        "embed_call": env.get("embed_provider_fixture"),
        "index_call": index_provider,
        "retrieve_call": retrieve_provider,
        "rerank_call": rerank_provider,
        "model_call": model_provider,
    }
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
    source = Path(value).read_text(encoding="utf-8") if mode == "--file" else value
    filename = str(Path(value).resolve()) if mode == "--file" else "<shared-r12-grounded-fixture>"
    if mode == "--pipe":
        source = genia_interpreter._wrap_pipe_mode_expr(source)
        filename = "<pipe>"
    try:
        result = genia_interpreter.run_source(source, _build_env(stdin_data=stdin_data), filename=filename)
        if mode != "--pipe" and result is not None:
            sys.stdout.write(format_debug(result) + "\n")
        return 0
    except Exception as error:  # noqa: BLE001
        sys.stderr.write(f"Error: {error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
