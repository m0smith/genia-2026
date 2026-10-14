"""Temporary module-to-entry read compatibility fallback (F2/P2-E, issue #1230).

PYTHON REFERENCE HOST ONLY. This is not language semantics and is not part of the
portable contract; it exists so P2 can ship without silently breaking programs that
read an entry-program name from module code. Removal (P3) is deleting this module,
its single call in `Evaluator._resolve_identifier`, the two `Env` class attributes and
the R-construction capture in `make_global_env`; no name-resolution rule depends on it.
Contract: docs/design/f2-module-entry-scope-isolation-contract.md section 11 and 16.3.
"""

from __future__ import annotations

import sys
from typing import Any

FALLBACK_MARKER = "TEMPORARY COMPATIBILITY FALLBACK"
TRACKING_ISSUE = "#1230"


def temporary_compatibility_fallback_read(env: Any, name: str) -> tuple[bool, Any]:
    """TEMPORARY COMPATIBILITY FALLBACK: resolve a missed free name to an entry binding.

    Called only by the evaluator's identifier resolution after normal lookup (module
    chain, runtime, trusted internals) and one autoload retry have failed. Returns
    `(True, value)` when all of these hold, else `(False, None)` and the caller
    re-raises the ordinary undefined-name error:

    - an entry scope is registered and `name` is bound in that entry scope itself
      (entry-declared runtime-owned names live in R and never reach this path);
    - the evaluating frame's declaring unit is a module (including an R20 contribution
      clause, attributed to its declaring module), never the entry or the prelude;
    - strict mode (captured once when R was built) is off.

    Records the distinct (canonical module identity, name) pair on R's per-execution
    event set and, for a new pair, writes one value-free warning line. Never called for
    writes, reflection, exports, metacircular `eval`, host `Env.get` or inspection.
    """
    runtime = env.runtime_scope()
    entry = runtime._entry
    if entry is None or runtime.strict_module_scope or name not in entry.values:
        return False, None
    unit = env.unit_scope()
    if unit is runtime or unit is entry or unit.module_id is None:
        return False, None
    pair = (unit.module_identity(), name)
    events = runtime.fallback_events
    if events is not None and pair not in events:
        events.add(pair)
        _warn(runtime, pair)
    return True, entry.values[name]


def _warn(runtime: Any, pair: tuple[str, str]) -> None:
    """Write one warning naming the module and name only (no value, path or detail)."""
    module, name = pair
    line = (
        f"warning: {FALLBACK_MARKER}: module '{module}' resolved entry-program name "
        f"'{name}'; this will become an undefined-name error (tracking {TRACKING_ISSUE})\n"
    )
    sink = runtime.values.get("stderr")
    if sink is not None and hasattr(sink, "write_text"):
        sink.write_text(line)
        return
    try:
        sys.stderr.write(line)
        sys.stderr.flush()
    except BrokenPipeError:
        return
