"""FAILING-TEST PHASE — Group J: failure normalization / non-leak.

Targets `genia.process_transport.launch_process` (raw host detail must
never cross the boundary) and `genia.process_execution.perform_process_execution`
(the closed reason/context taxonomy, contract §12). Uses deliberately
recognizable sentinel strings/paths and proves their absence from returned
context, diagnostics, and stderr -- the same non-leak proof style as
`tests/unit/test_protected_sinks.py` and `tests/unit/test_r11_model_fixture.py`
(`test_fixture_exception_becomes_non_sensitive_transport_failure_once`).

Does not assert Python exception class names as portable behavior (per
task instructions) -- only the closed `kind`/reason taxonomy.

`execution.process` is NOT implemented yet; every test fails today with
`ModuleNotFoundError` -- the correct RED state for this phase.
"""

from __future__ import annotations

from tests.fixtures.process_fixtures import sleep_ms, write_n_bytes


_LEAK_SENTINEL = "RAW_HOST_DETAIL_SENTINEL_978_MUST_NOT_CROSS_BOUNDARY"


def _launch(executable: str, args: list[str], timeout_ms: int):
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    return module.launch_process(executable, args, timeout_ms)


def _assert_no_leak(*objs) -> None:
    for obj in objs:
        rendered = repr(obj)
        assert _LEAK_SENTINEL not in rendered
        assert "Traceback" not in rendered
        assert "site-packages" not in rendered


def test_launch_failure_context_excludes_native_target_and_exception_text():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    sentinel_path = f"/nonexistent/{_LEAK_SENTINEL}"
    result = module.launch_process(sentinel_path, [], 1000)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "launch"
    _assert_no_leak(result)


def test_timeout_failure_context_excludes_raw_exception_text():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    executable, *args = sleep_ms(5000)
    result = module.launch_process(executable, args, 200)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "timeout"
    _assert_no_leak(result)


def test_output_limit_failure_context_excludes_raw_exception_text():
    from tests.fixtures.execution_process_helpers import process_transport_module

    module = process_transport_module()
    executable, *args = write_n_bytes("stdout", 1_048_577)
    result = module.launch_process(executable, args, 15000)

    assert isinstance(result, module.ProcessTransportFailure)
    assert result.kind == "output-limit"
    _assert_no_leak(result)


def test_unavailable_symbol_context_excludes_native_target_via_composition_boundary():
    """Exercised at the composition layer (`perform_process_execution`),
    since "unavailable" is a capability-resolution concept, not a
    transport-level one (contract §6).
    """
    from tests.fixtures.execution_process_helpers import (
        make_capability,
        make_request,
        process_execution_module,
        refusing_launcher,
    )
    from genia.values import symbol

    module = process_execution_module()
    capability = make_capability(
        bindings={f"bound_but_irrelevant_{_LEAK_SENTINEL}": "irrelevant-target"},
        launcher=refusing_launcher(),
    )
    request = make_request(
        executable=symbol("totally_unbound_symbol"), args=[], timeout_ms=1000
    )

    result = module.perform_process_execution(capability, request)

    assert result.reason == "process-executable-unavailable"
    _assert_no_leak(result.context)


def test_provider_failure_context_excludes_raw_exception_text_and_type_name():
    """A launcher that raises an arbitrary, recognizable Python exception
    (standing in for an unexpected host-level error) must normalize to
    `process-provider-failure` at the composition boundary, without the
    exception's message or class name crossing into the returned context.
    """
    from tests.fixtures.execution_process_helpers import (
        make_capability,
        make_request,
        process_execution_module,
    )
    from genia.values import symbol

    module = process_execution_module()

    class _VeryRecognizableHostException(RuntimeError):
        pass

    def _explode(*_args, **_kwargs):
        raise _VeryRecognizableHostException(
            f"host exploded: {_LEAK_SENTINEL} at /some/native/path"
        )

    capability = make_capability(
        bindings={"fixture_target": "opaque-native-target"}, launcher=_explode
    )
    request = make_request(executable=symbol("fixture_target"), args=[], timeout_ms=1000)

    result = module.perform_process_execution(capability, request)

    assert result.reason == "process-provider-failure"
    rendered = repr(result.context)
    assert _LEAK_SENTINEL not in rendered
    assert "_VeryRecognizableHostException" not in rendered
    assert "/some/native/path" not in rendered


def test_closed_failure_taxonomy_rows_use_only_approved_reason_strings():
    """No implementation may invent an eighth reason for a native error that
    fits an existing row (contract §12: "must not add a new reason for
    native errors that fit an existing row").
    """
    approved_reasons = {
        "process-unsupported",
        "process-unauthorized",
        "process-executable-unavailable",
        "process-launch-failure",
        "process-timeout",
        "process-output-limit",
        "process-provider-failure",
    }
    from tests.fixtures.execution_process_helpers import (
        make_capability,
        make_request,
        process_execution_module,
        refusing_launcher,
    )
    from genia.values import symbol

    module = process_execution_module()
    capability = make_capability(bindings={}, launcher=refusing_launcher())
    request = make_request(executable=symbol("anything"), args=[], timeout_ms=1000)

    result = module.perform_process_execution(capability, request)

    assert str(result.reason) in approved_reasons
