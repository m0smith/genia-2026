"""FAILING-TEST PHASE — Group E: exact byte capture.

Targets `genia.process_transport.launch_process`. Proves stdout/stderr are
captured as exact, undecoded bytes (contract §10: "It does not decode
them"), including non-UTF-8 sequences and empty channels -- never text,
never line-ending normalization.

`execution.process` is NOT implemented yet; every test fails today with
`ModuleNotFoundError` -- the correct RED state for this phase.
"""

from __future__ import annotations

import pytest

from tests.fixtures.process_fixtures import (
    write_both_exact,
    write_stderr_exact,
    write_stdout_exact,
)


def _launch(argv: list[str], timeout_ms: int = 5000):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    executable, *args = argv
    return module.launch_process(executable, args, timeout_ms)


@pytest.mark.parametrize(
    "label, payload",
    [
        ("empty", b""),
        ("ascii", b"hello, world"),
        ("newlines_not_normalized", b"line1\r\nline2\nline3\r"),
        ("arbitrary_binary", bytes(range(256))),
        ("non_utf8", b"\xff\xfe\x00\x80\x81\xc0\xc1"),
        ("nul_bytes", b"before\x00after"),
    ],
)
def test_stdout_only_is_captured_byte_exact(label, payload):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_stdout_exact(payload))

    assert isinstance(result, module.ProcessTransportResult)
    assert result.stdout == payload
    assert result.stderr == b""
    assert isinstance(result.stdout, bytes)


@pytest.mark.parametrize(
    "label, payload",
    [
        ("empty", b""),
        ("ascii", b"an error occurred"),
        ("arbitrary_binary", bytes(range(256))),
        ("non_utf8", b"\xff\xfe\x00\x80\x81\xc0\xc1"),
    ],
)
def test_stderr_only_is_captured_byte_exact(label, payload):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_stderr_exact(payload))

    assert isinstance(result, module.ProcessTransportResult)
    assert result.stderr == payload
    assert result.stdout == b""


def test_both_channels_captured_independently_and_byte_exact():
    stdout_payload = b"STDOUT:" + bytes(range(0, 128))
    stderr_payload = b"STDERR:" + bytes(range(128, 256))
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_both_exact(stdout_payload, stderr_payload))

    assert isinstance(result, module.ProcessTransportResult)
    assert result.stdout == stdout_payload
    assert result.stderr == stderr_payload


def test_both_channels_empty_is_a_successful_empty_result():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_both_exact(b"", b""))

    assert isinstance(result, module.ProcessTransportResult)
    assert result.stdout == b""
    assert result.stderr == b""


def test_captured_output_type_is_bytes_not_str():
    """The contract's `ProcessResult.stdout`/`stderr` are `bytes` (contract
    §10/§11), not decoded text. At the Python-transport layer this must
    already be `bytes`, never a `str` produced by an implicit UTF-8 decode
    (contrast the shell stage's `errors="replace"` decoding, explicitly not
    the model to follow -- design §9).
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(write_stdout_exact(b"not decoded"))

    assert isinstance(result, module.ProcessTransportResult)
    assert type(result.stdout) is bytes
    assert type(result.stderr) is bytes
