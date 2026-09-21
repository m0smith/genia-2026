"""FAILING-TEST PHASE — Group D: normal exit behavior (0 and nonzero).

Targets the anticipated `genia.process_transport.launch_process` Python
host adapter (`docs/design/execution-process-design.md` §13), mirroring
how `test_http_transport.py` exercises `send_http_request` directly at the
Python level using deterministic fixtures instead of Genia source.

The single most important assertion in this file: a child that exits
nonzero is STILL a successful attempt (`ProcessTransportResult`), never a
`ProcessTransportFailure`. This directly guards against
`subprocess.run(..., check=True)` (or `check_call`/`check_output`) ever
slipping into the implementation, since those raise `CalledProcessError`
on nonzero exit by default (design §10).

`execution.process` is NOT implemented yet, so every test fails today with
`ModuleNotFoundError` from the not-yet-existing `genia.process_transport`
-- the correct RED state for this phase. Do not add
`genia/process_transport.py` to make these pass.
"""

from __future__ import annotations

import pytest

from tests.fixtures.process_fixtures import exit_with, nonexistent_target_path


def _launch(argv: list[str], timeout_ms: int = 5000):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    executable, *args = argv
    return module.launch_process(executable, args, timeout_ms)


def test_exit_zero_with_no_output_is_a_successful_result():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(exit_with(0))

    assert isinstance(result, module.ProcessTransportResult)
    assert result.exit_code == 0
    assert result.stdout == b""
    assert result.stderr == b""


@pytest.mark.parametrize("code", [1, 2, 17, 127, 255])
def test_nonzero_exit_is_still_a_successful_result_not_a_failure(code):
    """This is the single most explicit RED test for exit-code handling:
    nonzero exit must be `ProcessTransportResult`, never
    `ProcessTransportFailure` and never a raised exception of any kind.
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(exit_with(code))

    assert isinstance(result, module.ProcessTransportResult), (
        f"exit code {code} must normalize to ProcessTransportResult, "
        f"not {type(result).__name__} -- a subprocess.run(..., check=True)-style "
        "implementation would turn this into a CalledProcessError/Failure instead"
    )
    assert result.exit_code == code


def test_nonzero_exit_does_not_raise_calledprocesserror():
    """Directly guards against `subprocess.run(..., check=True)`,
    `subprocess.check_call`, and `subprocess.check_output` -- all of which
    raise `CalledProcessError` by default on nonzero exit (design §10,
    explicitly forbidden Python APIs).
    """
    import subprocess

    try:
        _launch(exit_with(3))
    except subprocess.CalledProcessError:
        pytest.fail(
            "launch_process must never let a subprocess.CalledProcessError "
            "escape -- nonzero exit is data (ProcessTransportResult), not a "
            "raised exception (design §10)"
        )
    except ModuleNotFoundError:
        # Expected in this phase: genia.process_transport does not exist yet.
        raise


def test_exit_code_is_normalized_into_the_portable_range():
    """`exit_code` must be a non-negative Integer in `0..4294967295`
    (contract §11) -- proven here against the boundary value `0` and a
    representative mid-range value; the transport layer must not leak a
    raw platform-signed byte or signal-encoded status.
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = _launch(exit_with(0))
    assert isinstance(result, module.ProcessTransportResult)
    assert isinstance(result.exit_code, int)
    assert 0 <= result.exit_code <= 4294967295


def test_launch_failure_for_a_target_that_does_not_exist():
    """Resolution succeeds at the capability layer (out of scope here); the
    OS-level launch itself fails because the bound native target does not
    exist. This must normalize to a `ProcessTransportFailure(kind="launch")`
    -- never raise a raw `FileNotFoundError`/`OSError`.
    """
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    result = module.launch_process(nonexistent_target_path(), [], 1000)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "launch"
