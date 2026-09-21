"""Shared test-only helpers for `execution.process` failing-test-phase tests.

Two jobs:

1. Lazily import the not-yet-existing production modules named in
   `docs/design/execution-process-design.md` §13 (`genia.process_capability`,
   `genia.process_execution`, `genia.process_transport`). Each helper does
   its import *inside* the function body, on purpose: a test that calls one
   of these gets its own clean `ModuleNotFoundError` failure at test-run
   time instead of a whole-file pytest *collection* error. This keeps every
   RED test individually attributable to "the target module does not exist
   yet" rather than producing one opaque collection failure per file.

2. Provide small request/capability builders against the API these modules
   are anticipated to expose, so the tests read as ordinary behavioral
   tests rather than reflection gymnastics.

This file implements none of the forbidden production modules itself and
defines no portable Genia behavior. If the implementation phase settles on
different exact parameter names/order than anticipated here, the call
sites below (and the tests using them) will need light adjustment — the
*assertions* in the test files encode the portable observable contract from
`docs/design/execution-process-contract.md`, not this helper's incidental
shape.
"""

from __future__ import annotations

import os
import queue
import signal
import threading
from collections.abc import Callable
from typing import Any

from genia.values import GeniaMap, symbol


def process_capability_module():
    """Import `genia.process_capability` (anticipated; not yet implemented).

    Expected to raise `ModuleNotFoundError` until the implementation phase
    creates this module per `docs/design/execution-process-design.md` §13.
    """
    import genia.process_capability as module

    return module


def process_execution_module():
    """Import `genia.process_execution` (anticipated; not yet implemented)."""
    import genia.process_execution as module

    return module


def process_transport_module():
    """Import `genia.process_transport` (anticipated; not yet implemented)."""
    import genia.process_transport as module

    return module


def make_request(*, executable: Any, args: Any, timeout_ms: Any) -> GeniaMap:
    """Build a `{executable, args, timeout_ms}` map without assuming closedness
    (some misuse tests deliberately build non-closed/extra-key maps by hand
    instead of using this helper).
    """
    result = GeniaMap()
    result = result.put("executable", executable)
    result = result.put("args", args)
    result = result.put("timeout_ms", timeout_ms)
    return result


def valid_request(
    *, executable: Any = "fixture_target", args: Any = None, timeout_ms: Any = 5000
) -> GeniaMap:
    """A request that is shape-valid by construction, for tests that vary one field."""
    return make_request(
        executable=symbol(executable) if isinstance(executable, str) else executable,
        args=[] if args is None else args,
        timeout_ms=timeout_ms,
    )


def refusing_launcher():
    """A launcher that fails the test immediately if invoked.

    Use this when a test expects `perform_process_execution` to fail before
    ever reaching the launch attempt (e.g. misuse, protected-value
    rejection, unbound symbol, unauthorized symbol) — proving "zero
    provider attempts" (contract §5) directly rather than by inference.
    """

    def _refuse(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError(
            "launcher was invoked, but this test expects zero provider effects"
        )

    return _refuse


def recording_launcher(result: Any):
    """A launcher that always returns `result` and records every call it received."""
    calls: list[tuple[Any, ...]] = []

    def _launch(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        return result

    _launch.calls = calls  # type: ignore[attr-defined]
    return _launch


def make_capability(
    *,
    bindings: dict[str, Any] | None = None,
    authorized: Callable[[str], bool] | None = None,
    launcher: Callable[..., Any] | None = None,
):
    """Construct an opaque `GeniaProcessCapability` via the anticipated private
    factory `genia.process_capability.create_process_capability(bindings,
    authorized, launcher)` (`docs/design/execution-process-design.md` §4).

    `bindings`: symbol-name -> opaque native target (any Python value; the
    target is never Genia-visible).
    `authorized`: predicate over a bound symbol name; defaults to
    "authorize everything bound".
    `launcher`: callable used once resolution/authorization succeed;
    defaults to `refusing_launcher()` so a test that never expects a launch
    attempt fails loudly if one happens anyway.
    """
    module = process_capability_module()
    resolved_bindings = dict(bindings or {})
    resolved_authorized = authorized if authorized is not None else (lambda _symbol: True)
    resolved_launcher = launcher if launcher is not None else refusing_launcher()
    return module.create_process_capability(
        resolved_bindings, resolved_authorized, resolved_launcher
    )


def launch_bounded(
    executable: str,
    args: list[str],
    timeout_ms: int,
    *,
    wall_clock_bound_seconds: float = 15.0,
):
    """Run `genia.process_transport.launch_process` in a worker thread with a
    wall-clock bound, force-killing any captured child PID if the call is
    abandoned.

    Several tests in this failing-test phase deliberately drive fixtures
    that never stop on their own (an endless writer, a large interleaved
    stdout/stderr producer) to pressure a naive implementation into
    deadlocking or hanging. If `launch_process` itself hangs, this helper
    still returns within `wall_clock_bound_seconds` (raising
    `AssertionError`, which fails the test cleanly) instead of hanging the
    whole suite -- and it force-kills whatever child PID was captured via
    the anticipated `spawn_hook` injection seam, so a genuinely broken
    implementation does not leak a running child process past the failing
    test (see design §13/§20 for the anticipated `launch_process` shape;
    if the implementation phase names this injection seam differently,
    this helper's `spawn_hook=` call site needs matching adjustment).
    """
    module = process_transport_module()

    captured: dict[str, int] = {}

    def _spawn_hook(pid: int) -> None:
        captured["pid"] = pid

    result_queue: queue.Queue = queue.Queue(maxsize=1)

    def _run() -> None:
        try:
            result_queue.put(
                ("ok", module.launch_process(executable, args, timeout_ms, spawn_hook=_spawn_hook))
            )
        except BaseException as exc:  # noqa: BLE001 - forwarded to the main thread
            result_queue.put(("error", exc))

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    worker.join(timeout=wall_clock_bound_seconds)

    if worker.is_alive():
        pid = captured.get("pid")
        if pid is not None:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        raise AssertionError(
            f"launch_process did not return within {wall_clock_bound_seconds}s -- "
            "the worker thread and its captured child (if any) have been "
            "force-killed to avoid leaking a running process past this "
            "failing test, but this itself is evidence of a missing bounded-"
            "drain/timeout guarantee (design §9/§21)."
        )

    kind, payload = result_queue.get_nowait()
    if kind == "error":
        raise payload
    return payload


def not_a_capability_examples() -> list[tuple[str, Any]]:
    """Named non-capability values that must be rejected as misuse (Group A)."""
    from genia.values import GeniaMap as _Map

    return [
        ("map", _Map()),
        ("string", "not-a-capability"),
        ("symbol", symbol("not_a_capability")),
        ("integer", 42),
        ("list", []),
        ("none", None),
        ("callable", lambda *_a, **_kw: None),
    ]
