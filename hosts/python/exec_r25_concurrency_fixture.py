"""Dedicated subprocess runner for deterministic R25 causal evidence."""

from __future__ import annotations

import sys

from genia import interpreter as genia_interpreter
from genia.builtins import make_global_env
from genia.utf8 import format_debug
from genia.values import r25_await_runtime_idle


def _build_env():
    env = make_global_env([])
    env.set("_r25_await_idle", r25_await_runtime_idle)
    return env


def main() -> int:
    args = sys.argv[1:]
    if len(args) != 1:
        raise SystemExit("expected source")
    try:
        result = genia_interpreter.run_source(
            args[0], _build_env(), filename="<shared-r25-concurrency-fixture>"
        )
        if result is not None:
            sys.stdout.write(format_debug(result) + "\n")
        return 0
    except Exception as error:  # noqa: BLE001 - command boundary normalization
        sys.stderr.write(f"Error: {error}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
