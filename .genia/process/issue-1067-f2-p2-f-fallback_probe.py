"""Throwaway measurement plugin: logs every successful fallback read with the running test id (not committed)."""
import json
import os

import genia.evaluator as evaluator
import genia.module_fallback as module_fallback

_original = module_fallback.temporary_compatibility_fallback_read
LOG = os.environ["FALLBACK_PROBE_LOG"]


def probe(env, name):
    """Delegate to the real fallback read and log each successful read with its test id."""
    found, value = _original(env, name)
    if found:
        unit = env.unit_scope()
        with open(LOG, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"test": os.environ.get("PYTEST_CURRENT_TEST", "?"), "module": unit.module_identity(), "name": name}) + "\n")
    return found, value


module_fallback.temporary_compatibility_fallback_read = probe
evaluator.temporary_compatibility_fallback_read = probe
