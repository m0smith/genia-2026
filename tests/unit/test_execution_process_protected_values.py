"""FAILING-TEST PHASE — Group B: protected-value rejection.

Reuses the repository's existing R10 protected-value sentinel pattern
(`tests/unit/test_protected_sinks.py`'s `_env_with_protected`) rather than
inventing new taint machinery, per
`docs/design/execution-process-design.md` §12: "Reuse, do not reinvent:
`src/genia/configuration.py`'s existing `contains_protected`/
`reject_protected`."

Targets the anticipated `genia.process_execution.perform_process_execution`
boundary. `execution.process` is NOT implemented yet, so every test here
fails today with `ModuleNotFoundError` from the not-yet-existing
`genia.process_execution` module -- the correct RED state for this phase.

Do not add `genia/process_execution.py`, and do not build a second
protected-value/taint mechanism, to make these pass.
"""

from __future__ import annotations

import pytest

from genia.builtins import make_global_env
from genia.interpreter import run_source
from genia.values import symbol
from tests.fixtures.execution_process_helpers import (
    make_capability,
    make_request,
    refusing_launcher,
)


KEY = "EXECUTION_PROCESS_PROTECTED_KEY_SENTINEL_978"
PAYLOAD = "EXECUTION_PROCESS_PROTECTED_PAYLOAD_SENTINEL_978"
PURPOSE = "EXECUTION_PROCESS_PROTECTED_PURPOSE_SENTINEL_978"


def _protected_sentinel():
    """Build one `GeniaProtected` sentinel value via the real R10 machinery
    (config_provider + secret_get), exactly like
    `test_protected_sinks.py::_env_with_protected`.
    """
    env = make_global_env([])
    protected = run_source(
        "provider = config_provider([{kind: quote(values), values: {"
        f'{KEY}: "{PAYLOAD}"'
        "}}]) |> unwrap_or(none)\n"
        f'secret_get(provider, "{KEY}", quote({PURPOSE})) |> unwrap_or(none)',
        env,
    )
    return protected


def _assert_no_sentinel(text) -> None:
    rendered = str(text)
    assert PAYLOAD not in rendered
    assert KEY not in rendered
    assert PURPOSE not in rendered


def _perform(capability, request):
    from tests.fixtures.execution_process_helpers import process_execution_module

    module = process_execution_module()
    return module.perform_process_execution(capability, request)


def test_protected_executable_is_rejected_before_any_provider_effect():
    protected = _protected_sentinel()
    capability = make_capability(launcher=refusing_launcher())
    request = make_request(executable=protected, args=[], timeout_ms=1000)

    with pytest.raises(TypeError) as excinfo:
        _perform(capability, request)

    _assert_no_sentinel(excinfo.value)


def test_protected_value_in_args_element_is_rejected_before_any_provider_effect():
    protected = _protected_sentinel()
    capability = make_capability(launcher=refusing_launcher())
    request = make_request(
        executable=symbol("fixture_target"), args=["safe", protected], timeout_ms=1000
    )

    with pytest.raises(TypeError) as excinfo:
        _perform(capability, request)

    _assert_no_sentinel(excinfo.value)


def test_protected_value_nested_inside_a_list_element_is_rejected_recursively():
    """Recursive rejection must not assume the closed request's shallow shape
    -- prove it against a defense-in-depth nested structure even though the
    closed request normally limits nesting (contract §13, "Recursive
    request validation ... where applicable").
    """
    protected = _protected_sentinel()
    capability = make_capability(launcher=refusing_launcher())
    # args is contractually a flat list of strings; a misuse-shaped nested
    # list is exactly the adversarial case a recursive scan must still catch
    # rather than crashing on or silently accepting.
    request = make_request(
        executable=symbol("fixture_target"), args=["safe", [protected]], timeout_ms=1000
    )

    with pytest.raises(TypeError) as excinfo:
        _perform(capability, request)

    _assert_no_sentinel(excinfo.value)


def test_protected_leaf_never_reaches_the_launcher():
    """The launcher must never be invoked for a request carrying a protected
    leaf -- proves rejection happens strictly before any provider effect,
    not merely before a *successful* provider effect.
    """
    from tests.fixtures.execution_process_helpers import recording_launcher

    protected = _protected_sentinel()
    launcher = recording_launcher(result=None)
    capability = make_capability(
        bindings={"fixture_target": "irrelevant-native-target"}, launcher=launcher
    )
    request = make_request(executable=protected, args=[], timeout_ms=1000)

    with pytest.raises(TypeError):
        _perform(capability, request)

    assert launcher.calls == []


def test_protected_capability_authority_argument_is_not_accepted():
    """V1 has no authority argument and no declassification sink (contract
    §13): calling `execution.process` with a third argument at all -- even
    a plausible-looking declassification authority -- must be rejected,
    not silently accepted as an extension point.
    """
    protected = _protected_sentinel()
    capability = make_capability(launcher=refusing_launcher())
    request = make_request(executable=symbol("fixture_target"), args=[], timeout_ms=1000)

    from tests.fixtures.execution_process_helpers import process_execution_module

    module = process_execution_module()
    with pytest.raises(TypeError):
        module.perform_process_execution(capability, request, protected)
