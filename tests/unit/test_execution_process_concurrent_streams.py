"""FAILING-TEST PHASE — Group F: simultaneous stdout/stderr draining.

Catches a future implementation that reads stdout completely before
touching stderr (or vice versa). The fixture writes alternating chunks to
both streams, each larger than a typical OS pipe buffer (64 KiB) in total,
so a naive sequential drain would stall: the child blocks writing to
whichever stream isn't being read, and a reader that never gets around to
it hangs forever.

The test itself is bounded (`_launch` runs in a worker thread with a
generous join timeout) so a genuinely deadlocking implementation fails the
test with a clear "did not return in time" assertion instead of hanging
the whole CI job -- per the RED-phase reliability rules ("tests that can
leave children running after test failure" and "long sleeps" are both
things to avoid).

`execution.process` is NOT implemented yet; every test fails today with
`ModuleNotFoundError` -- the correct RED state for this phase.
"""

from __future__ import annotations

from tests.fixtures.process_fixtures import interleave_stdout_stderr

# Comfortably larger than a typical 64 KiB OS pipe buffer, but small enough
# to stay well under the 1,048,576-byte per-channel limit and keep the test
# fast and deterministic.
_CHUNK_SIZE = 8192
_CHUNK_COUNT = 40  # 8192 * 40 = 327,680 bytes per channel


def test_large_interleaved_stdout_and_stderr_does_not_deadlock():
    from tests.fixtures.execution_process_helpers import launch_bounded, process_transport_module

    module = process_transport_module()
    executable, *args = interleave_stdout_stderr(_CHUNK_SIZE, _CHUNK_COUNT)
    result = launch_bounded(executable, args, timeout_ms=10000)

    assert isinstance(result, module.ProcessTransportResult)
    assert result.exit_code == 0
    assert result.stdout == b"O" * (_CHUNK_SIZE * _CHUNK_COUNT)
    assert result.stderr == b"E" * (_CHUNK_SIZE * _CHUNK_COUNT)


def test_stdout_heavy_stderr_light_does_not_stall_on_stderr():
    """One channel dominates; a reader that fully drains the other channel
    to EOF before starting on this one would still deadlock once the
    dominant channel exceeds its OS pipe buffer while the child is also
    blocked trying to write the small amount to the other channel after it.
    """
    from tests.fixtures.process_fixtures import python_argv
    from tests.fixtures.execution_process_helpers import launch_bounded, process_transport_module

    module = process_transport_module()
    script = (
        "import sys\n"
        "out = sys.stdout.buffer\n"
        "err = sys.stderr.buffer\n"
        f"out.write(b'X' * {_CHUNK_SIZE * _CHUNK_COUNT}); out.flush()\n"
        "err.write(b'small'); err.flush()\n"
    )
    executable, *args = python_argv(script)
    result = launch_bounded(executable, args, timeout_ms=10000)

    assert isinstance(result, module.ProcessTransportResult)
    assert result.exit_code == 0
    assert result.stdout == b"X" * (_CHUNK_SIZE * _CHUNK_COUNT)
    assert result.stderr == b"small"
