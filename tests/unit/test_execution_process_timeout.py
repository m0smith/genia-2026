"""FAILING-TEST PHASE — Group H: timeout.

Targets `genia.process_transport.launch_process`. Asserts observable
guarantees only (normalized failure, bounded return window, dead child
afterward) -- never exact millisecond precision, per design §8
("Conformance-testable without wall-clock fragility") and the RED-phase
reliability rule against "race-prone exact timing".

`execution.process` is NOT implemented yet; every test fails today with
`ModuleNotFoundError` -- the correct RED state for this phase.
"""

from __future__ import annotations

import time

from tests.fixtures.process_fixtures import sleep_ms

# A short configured timeout against a fixture that sleeps far longer,
# so the outcome is unambiguous without needing millisecond precision.
_SHORT_TIMEOUT_MS = 200
_LONG_SLEEP_MS = 5000
_GENEROUS_RETURN_WINDOW_SECONDS = 5  # generous multiple of _SHORT_TIMEOUT_MS


def _launch(argv: list[str], timeout_ms: int):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    executable, *args = argv
    return module.launch_process(executable, args, timeout_ms)


def test_minimum_practical_timeout_against_a_far_longer_sleep():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(sleep_ms(_LONG_SLEEP_MS), timeout_ms=1)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "timeout"


def test_ordinary_timeout_returns_within_a_bounded_window_not_the_full_sleep():
    """Behavioral, not millisecond-precise: the call must return well before
    the child's full 5-second sleep would otherwise complete.
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    started = time.monotonic()
    result = _launch(sleep_ms(_LONG_SLEEP_MS), timeout_ms=_SHORT_TIMEOUT_MS)
    elapsed = time.monotonic() - started

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "timeout"
    assert elapsed < _GENEROUS_RETURN_WINDOW_SECONDS, (
        f"timeout took {elapsed:.2f}s to return, expected well under "
        f"{_GENEROUS_RETURN_WINDOW_SECONDS}s for a {_SHORT_TIMEOUT_MS}ms configured timeout"
    )


def test_timeout_after_partial_stdout_discards_output_and_normalizes():
    """A child that writes some stdout and then hangs must still normalize
    to `process-timeout` with no partial output surfaced (contract §8:
    "Partial stdout and stderr are discarded on timeout").
    """
    from tests.fixtures.process_fixtures import python_argv
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    script = (
        "import sys, time\n"
        "sys.stdout.buffer.write(b'partial output before hang'); sys.stdout.buffer.flush()\n"
        "time.sleep(5)\n"
    )
    result = _launch(python_argv(script), timeout_ms=_SHORT_TIMEOUT_MS)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "timeout"
    assert not hasattr(result, "stdout")


def test_timeout_after_partial_stderr_discards_output_and_normalizes():
    from tests.fixtures.process_fixtures import python_argv
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    script = (
        "import sys, time\n"
        "sys.stderr.buffer.write(b'partial error before hang'); sys.stderr.buffer.flush()\n"
        "time.sleep(5)\n"
    )
    result = _launch(python_argv(script), timeout_ms=_SHORT_TIMEOUT_MS)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "timeout"
    assert not hasattr(result, "stderr")


def test_timeout_failure_context_carries_the_configured_timeout_ms():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(sleep_ms(_LONG_SLEEP_MS), timeout_ms=_SHORT_TIMEOUT_MS)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "timeout"
    # The Genia-level context is {timeout_ms}; at the transport layer the
    # equivalent value must be available for the normalization boundary
    # (genia.process_execution) to attach -- exposed here as a plain
    # attribute for the transport-level test.
    assert getattr(result, "timeout_ms", None) == _SHORT_TIMEOUT_MS


def test_timeout_never_raises_a_raw_timeout_exception():
    """`subprocess.run(..., timeout=...)` raises `subprocess.TimeoutExpired`
    by default -- this must be caught and normalized, never left to
    propagate as a raw Python exception across the boundary (design §11).
    """
    import subprocess

    try:
        _launch(sleep_ms(_LONG_SLEEP_MS), timeout_ms=_SHORT_TIMEOUT_MS)
    except subprocess.TimeoutExpired:
        import pytest

        pytest.fail(
            "launch_process must catch and normalize subprocess.TimeoutExpired "
            "into ProcessTransportFailure(kind='timeout'), never let it escape raw"
        )
