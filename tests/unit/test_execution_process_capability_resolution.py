"""FAILING-TEST PHASE — Group C: capability resolution distinctions.

Proves four observably distinct outcomes stay distinct, per
`docs/design/execution-process-design.md` §5:

- unbound symbol -> `process-executable-unavailable`
- bound symbol, policy denies -> `process-unauthorized`
- bound + authorized, launcher reports a launch problem ->
  `process-launch-failure`
- (host-level "unsupported" belongs to the deferred provisioning
  boundary -- see the last test below, which documents that
  `execution.process` itself never emits `process-unsupported`.)

Only the smallest possible test-only fixture capability is built here
(via `tests.fixtures.execution_process_helpers.make_capability`, itself a
thin wrapper anticipating `genia.process_capability.create_process_capability`).
No production capability class is implemented in this file.

`execution.process` is NOT implemented yet, so every test fails today with
`ModuleNotFoundError` -- the correct RED state for this phase.
"""

from __future__ import annotations

from genia.values import GeniaOptionErr, symbol
from tests.fixtures.execution_process_helpers import (
    make_capability,
    make_request,
    recording_launcher,
    refusing_launcher,
)


def _perform(capability, request):
    from tests.fixtures.execution_process_helpers import process_execution_module

    module = process_execution_module()
    return module.perform_process_execution(capability, request)


def test_unbound_symbol_returns_unavailable_and_never_launches():
    capability = make_capability(bindings={}, launcher=refusing_launcher())
    request = make_request(executable=symbol("never_bound"), args=[], timeout_ms=1000)

    result = _perform(capability, request)

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "process-executable-unavailable"
    assert result.context.get("executable") == symbol("never_bound")


def test_bound_but_unauthorized_symbol_returns_unauthorized_and_never_launches():
    launcher = recording_launcher(result=None)
    capability = make_capability(
        bindings={"denied_target": "native-target-opaque"},
        authorized=lambda _symbol: False,
        launcher=launcher,
    )
    request = make_request(executable=symbol("denied_target"), args=[], timeout_ms=1000)

    result = _perform(capability, request)

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "process-unauthorized"
    assert result.context.get("operation") == symbol("execute")
    assert result.context.get("executable") == symbol("denied_target")
    assert launcher.calls == []


def test_unbound_and_unauthorized_are_distinct_reasons_not_collapsed():
    """The two failure modes must never share a reason string -- collapsing
    them would make it impossible for a caller to tell "no such symbol"
    apart from "known symbol, this capability may not use it".
    """
    unbound_capability = make_capability(bindings={}, launcher=refusing_launcher())
    unbound_result = _perform(
        unbound_capability,
        make_request(executable=symbol("collapse_check"), args=[], timeout_ms=1000),
    )

    unauthorized_capability = make_capability(
        bindings={"collapse_check": "native-target"},
        authorized=lambda _symbol: False,
        launcher=refusing_launcher(),
    )
    unauthorized_result = _perform(
        unauthorized_capability,
        make_request(executable=symbol("collapse_check"), args=[], timeout_ms=1000),
    )

    assert unbound_result.reason != unauthorized_result.reason
    assert {unbound_result.reason, unauthorized_result.reason} == {
        "process-executable-unavailable",
        "process-unauthorized",
    }


def test_bound_authorized_symbol_reaches_the_launcher_exactly_once():
    from tests.fixtures.process_fixtures import exit_with

    launcher = recording_launcher(result=None)
    capability = make_capability(
        bindings={"fixture_target": "opaque-native-target"}, launcher=launcher
    )
    request = make_request(
        executable=symbol("fixture_target"), args=exit_with(0)[1:], timeout_ms=1000
    )

    _perform(capability, request)

    assert len(launcher.calls) == 1


def test_launch_failure_from_the_launcher_normalizes_without_leaking_the_native_target():
    """Resolution succeeds (bound + authorized); the launcher itself reports
    it could not start the process. This must normalize to
    `process-launch-failure` carrying only the requested symbol -- never
    the private native target string the capability resolved to.
    """
    native_target_sentinel = "OPAQUE_NATIVE_TARGET_SENTINEL_978_DO_NOT_LEAK"

    def _fail_to_launch(*_args, **_kwargs):
        from tests.fixtures.execution_process_helpers import process_transport_module

        transport = process_transport_module()
        return transport.ProcessTransportFailure(kind="launch")

    capability = make_capability(
        bindings={"fixture_target": native_target_sentinel}, launcher=_fail_to_launch
    )
    request = make_request(executable=symbol("fixture_target"), args=[], timeout_ms=1000)

    result = _perform(capability, request)

    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "process-launch-failure"
    assert result.context.get("executable") == symbol("fixture_target")
    assert native_target_sentinel not in str(result.context)


def test_execution_process_itself_never_returns_process_unsupported():
    """Per contract §3/design §4: "unsupported is discovered during
    provisioning, not rediscovered by each call." Once a caller holds a
    valid `GeniaProcessCapability` at all, `execution.process` has no
    `process-unsupported` path of its own -- that reason belongs entirely
    to the deferred provisioning boundary this design does not implement.
    This test asserts the *symbol name* is never returned as
    `process-unsupported` from a resolvable capability, distinguishing it
    from `process-executable-unavailable`/`process-unauthorized`.
    """
    capability = make_capability(bindings={}, launcher=refusing_launcher())
    request = make_request(executable=symbol("anything"), args=[], timeout_ms=1000)

    result = _perform(capability, request)

    assert isinstance(result, GeniaOptionErr)
    assert result.reason != "process-unsupported"
