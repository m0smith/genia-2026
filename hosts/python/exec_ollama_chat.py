"""Run the Ollama/Groq chat example with an authorized protected HTTP sink."""

from __future__ import annotations

import sys
from pathlib import Path

from genia import interpreter as genia_interpreter
from genia.builtins import make_global_env
from genia.configuration import create_declassification_authority
from genia.values import GeniaMap, GeniaOptionSome, symbol


EXAMPLE = Path(__file__).resolve().parents[2] / "examples/ollama_chat.genia"
PURPOSE = symbol("chat_outbound")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    env = make_global_env(cli_args=args)
    provider_result = env.get("config_standard")(GeniaMap(), [])
    if not isinstance(provider_result, GeniaOptionSome):
        sys.stderr.write("Error: unable to construct chat configuration provider\n")
        return 1

    provider = provider_result.value
    authority = GeniaOptionSome(
        create_declassification_authority(provider, [PURPOSE], lambda event: None)
    )
    genia_interpreter.run_source(
        EXAMPLE.read_text(encoding="utf-8"), env, filename=str(EXAMPLE)
    )

    try:
        env.get("run_chat")(args, provider, authority)
        return 0
    except Exception as error:  # noqa: BLE001 - command boundary normalization
        sys.stderr.write(f"Error: {error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
