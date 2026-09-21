"""FAILING-TEST PHASE — Group G: independent 1,048,576-byte output limits.

Targets `genia.process_transport.launch_process`. Each channel has an
independent fixed maximum of exactly `1,048,576` bytes (contract §10): a
channel of exactly that size succeeds; one more byte is overflow. The
contract deliberately omits which channel overflowed from the error
context ("so simultaneous or closely ordered writes cannot produce
host-dependent classification") -- these tests do not assert a
channel-specific field.

`execution.process` is NOT implemented yet; every test fails today with
`ModuleNotFoundError` -- the correct RED state for this phase.
"""

from __future__ import annotations

from tests.fixtures.process_fixtures import OUTPUT_LIMIT_BYTES, write_forever, write_n_bytes


def _launch(argv: list[str], timeout_ms: int = 15000):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    executable, *args = argv
    return module.launch_process(executable, args, timeout_ms)


def test_stdout_exactly_at_limit_succeeds():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_n_bytes("stdout", OUTPUT_LIMIT_BYTES))

    assert isinstance(result, module.ProcessTransportResult)
    assert len(result.stdout) == OUTPUT_LIMIT_BYTES


def test_stdout_one_byte_over_limit_fails_with_output_limit():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_n_bytes("stdout", OUTPUT_LIMIT_BYTES + 1))

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "output-limit"


def test_stderr_exactly_at_limit_succeeds():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_n_bytes("stderr", OUTPUT_LIMIT_BYTES))

    assert isinstance(result, module.ProcessTransportResult)
    assert len(result.stderr) == OUTPUT_LIMIT_BYTES


def test_stderr_one_byte_over_limit_fails_with_output_limit():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_n_bytes("stderr", OUTPUT_LIMIT_BYTES + 1))

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "output-limit"


def test_stdout_at_limit_with_small_stderr_succeeds_limits_are_independent():
    from tests.fixtures.process_fixtures import python_argv

    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    script = (
        "import sys\n"
        f"sys.stdout.buffer.write(b'A' * {OUTPUT_LIMIT_BYTES}); sys.stdout.buffer.flush()\n"
        "sys.stderr.buffer.write(b'small'); sys.stderr.buffer.flush()\n"
    )
    result = _launch(python_argv(script))

    assert isinstance(result, module.ProcessTransportResult)
    assert len(result.stdout) == OUTPUT_LIMIT_BYTES
    assert result.stderr == b"small"


def test_stderr_at_limit_with_small_stdout_succeeds_limits_are_independent():
    from tests.fixtures.process_fixtures import python_argv

    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    script = (
        "import sys\n"
        "sys.stdout.buffer.write(b'small'); sys.stdout.buffer.flush()\n"
        f"sys.stderr.buffer.write(b'B' * {OUTPUT_LIMIT_BYTES}); sys.stderr.buffer.flush()\n"
    )
    result = _launch(python_argv(script))

    assert isinstance(result, module.ProcessTransportResult)
    assert result.stdout == b"small"
    assert len(result.stderr) == OUTPUT_LIMIT_BYTES


def test_overflow_result_carries_no_partial_output():
    """Contract §10: partial output is discarded on overflow and never
    enters the error context -- proven by asserting the failure value
    carries no stdout/stderr-shaped payload at all, not merely that it's
    "short".
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_n_bytes("stdout", OUTPUT_LIMIT_BYTES + 1))

    assert isinstance(result, module.ProcessTransportFailure)
    assert not hasattr(result, "stdout")
    assert not hasattr(result, "stderr")


def test_endless_stdout_writer_is_detected_incrementally_not_buffered_fully():
    """Memory-boundedness proof: the child never stops writing on its own,
    so the only way `launch_process` can ever return is by checking the
    1,048,576-byte limit incrementally while draining and killing the
    child as soon as it is crossed. A "read until EOF, then check length"
    implementation can never reach EOF here and would hang (caught by the
    bounded wait in `_launch_bounded`) or grow memory without bound trying
    to buffer an endless stream.
    """
    from tests.fixtures.execution_process_helpers import launch_bounded, process_transport_module

    module = process_transport_module()
    executable, *args = write_forever("stdout")
    result = launch_bounded(executable, args, timeout_ms=60000)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "output-limit"


def test_endless_stderr_writer_is_detected_incrementally_not_buffered_fully():
    from tests.fixtures.execution_process_helpers import launch_bounded, process_transport_module

    module = process_transport_module()
    executable, *args = write_forever("stderr")
    result = launch_bounded(executable, args, timeout_ms=60000)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "output-limit"


def test_overflow_failure_context_does_not_identify_which_channel():
    """Contract §10 deliberately omits a channel name from the output-limit
    error context "so simultaneous or closely ordered writes cannot
    produce host-dependent classification" -- this must hold whether
    stdout or stderr is the one that overflowed.
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    stdout_overflow = _launch(write_n_bytes("stdout", OUTPUT_LIMIT_BYTES + 1))
    stderr_overflow = _launch(write_n_bytes("stderr", OUTPUT_LIMIT_BYTES + 1))

    for result in (stdout_overflow, stderr_overflow):
        assert isinstance(result, module.ProcessTransportFailure)
        assert result.kind == "output-limit"
        rendered = repr(result)
        assert "stdout" not in rendered.lower()
        assert "stderr" not in rendered.lower()
