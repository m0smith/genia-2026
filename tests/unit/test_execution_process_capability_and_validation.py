"""FAILING-TEST PHASE — Group A: capability and request-shape validation.

Targets the anticipated `genia.process_execution.perform_process_execution`
composition boundary (`docs/design/execution-process-design.md` §6/§13),
mirroring the existing `construct_model`/`perform_http_send` misuse-boundary
pattern (`src/genia/model.py`, `src/genia/http_client.py`).

`execution.process` is NOT implemented yet (PR #977 contract, PR #978
design). Every test below imports the not-yet-existing
`genia.process_execution` module inside the test body (via
`tests.fixtures.execution_process_helpers`), so each one fails today with a
clean, individually attributable `ModuleNotFoundError` propagating out of
the `pytest.raises(...)` block (it does not match `TypeError`, so it is
re-raised as the visible test failure) until the implementation phase
creates that module. This is the intended RED state for this phase — see
`docs/design/execution-process-design.md` §13/§24.

Do not add `genia/process_execution.py` to make these pass in this phase.
"""

from __future__ import annotations

import pytest

from genia.values import GeniaMap, symbol
from tests.fixtures.execution_process_helpers import (
    make_capability,
    make_request,
    not_a_capability_examples,
    refusing_launcher,
    valid_request,
)


def _perform(capability, request):
    from tests.fixtures.execution_process_helpers import process_execution_module

    module = process_execution_module()
    return module.perform_process_execution(capability, request)


# --- Invalid capability (contract §4: "not an opaque provisioned process
# capability is runtime misuse") -------------------------------------------


@pytest.mark.parametrize("label, value", not_a_capability_examples())
def test_non_capability_first_argument_is_rejected_as_misuse(label, value):
    with pytest.raises(TypeError):
        _perform(value, valid_request())


# --- Request shape -----------------------------------------------------


def _closed_map(**fields) -> GeniaMap:
    result = GeniaMap()
    for key, value in fields.items():
        result = result.put(key, value)
    return result


@pytest.mark.parametrize(
    "label, request_value",
    [
        ("missing_executable", _closed_map(args=[], timeout_ms=1000)),
        ("missing_args", _closed_map(executable=symbol("x"), timeout_ms=1000)),
        ("missing_timeout_ms", _closed_map(executable=symbol("x"), args=[])),
        (
            "extra_key",
            _closed_map(executable=symbol("x"), args=[], timeout_ms=1000, cwd="/tmp"),
        ),
        ("wrong_request_type_string", "not-a-request-map"),
        ("wrong_request_type_list", [symbol("x"), [], 1000]),
        ("wrong_request_type_none", None),
    ],
)
def test_request_shape_is_rejected_as_misuse(label, request_value):
    capability = make_capability(launcher=refusing_launcher())
    with pytest.raises(TypeError):
        _perform(capability, request_value)


# --- executable ----------------------------------------------------------


@pytest.mark.parametrize(
    "label, executable_value",
    [
        ("string_not_symbol", "fixture_target"),
        ("integer", 42),
        ("empty_symbol", symbol("")),
        ("map", GeniaMap()),
        ("list", []),
        ("none", None),
        ("boolean", True),
    ],
)
def test_executable_field_rejects_non_symbol_shapes(label, executable_value):
    capability = make_capability(launcher=refusing_launcher())
    request = make_request(executable=executable_value, args=[], timeout_ms=1000)
    with pytest.raises(TypeError):
        _perform(capability, request)


# --- args ------------------------------------------------------------


@pytest.mark.parametrize(
    "label, args_value",
    [
        ("non_list_string", "a b c"),
        ("non_list_map", GeniaMap()),
        ("non_list_none", None),
        ("non_string_member_int", ["a", 1, "c"]),
        ("non_string_member_symbol", ["a", symbol("b")]),
        ("mixed_types", [1, "two", GeniaMap()]),
        ("nul_byte_in_element", ["has\x00nul"]),
    ],
)
def test_args_field_rejects_invalid_element_shapes(label, args_value):
    capability = make_capability(launcher=refusing_launcher())
    request = make_request(executable=symbol("fixture_target"), args=args_value, timeout_ms=1000)
    with pytest.raises(TypeError):
        _perform(capability, request)


def test_empty_args_list_is_valid_shape_and_reaches_resolution():
    """Empty `args` must never itself be rejected as a shape error.

    An unbound symbol is a *recoverable* Outcome (`err(...)`), not a raised
    exception (contract §6/§12), so once implemented this must return
    `err("process-executable-unavailable", {executable})`, never raise a
    `TypeError` about the args list. Today this fails while constructing
    the fixture capability with a clean `ModuleNotFoundError` from the
    not-yet-existing `genia.process_capability` -- proving nothing exists
    yet, the correct RED signal for this phase.
    """
    from genia.values import GeniaOptionErr

    capability = make_capability(launcher=refusing_launcher())
    request = make_request(executable=symbol("unbound_symbol_empty_args"), args=[], timeout_ms=1000)
    result = _perform(capability, request)
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "process-executable-unavailable"


# --- timeout_ms ------------------------------------------------------


@pytest.mark.parametrize(
    "label, timeout_value",
    [
        ("zero", 0),
        ("above_max", 300001),
        ("negative", -1),
        ("string", "1000"),
        ("boolean_true", True),
        ("boolean_false", False),
        ("float", 1000.5),
    ],
)
def test_timeout_ms_out_of_range_or_wrong_type_is_misuse(label, timeout_value):
    """Establish the PORTABLE contract (integer, `1..300000`), including that
    booleans are rejected even though Python's `bool` subtypes `int`
    (contract §8: "Boolean values are rejected even on hosts where a
    boolean is represented as an integer subtype").
    """
    capability = make_capability(launcher=refusing_launcher())
    request = make_request(
        executable=symbol("unbound_symbol_for_timeout_test"), args=[], timeout_ms=timeout_value
    )
    with pytest.raises(TypeError):
        _perform(capability, request)


@pytest.mark.parametrize("label, timeout_value", [("min_boundary", 1), ("max_boundary", 300000)])
def test_timeout_ms_boundary_values_are_valid_shape(label, timeout_value):
    """`1` and `300000` are the inclusive boundary of the valid range and
    must never be rejected as misuse: once implemented this must return
    `err("process-executable-unavailable", ...)` for this unbound symbol,
    never raise `TypeError` about `timeout_ms`. Today it fails with a clean
    `ModuleNotFoundError` while constructing the fixture capability.
    """
    from genia.values import GeniaOptionErr

    capability = make_capability(launcher=refusing_launcher())
    request = make_request(
        executable=symbol("unbound_symbol_for_timeout_boundary_test"),
        args=[],
        timeout_ms=timeout_value,
    )
    result = _perform(capability, request)
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "process-executable-unavailable"


def test_decimal_and_rational_timeout_values_are_rejected_not_coerced():
    """`timeout_ms` is a plain Integer (contract §8); Decimal/Rational values
    must not be silently coerced to an integer millisecond count.
    """
    from genia.builtins import make_global_env
    from genia.interpreter import run_source

    env = make_global_env([])
    decimal_value = run_source("1000.0", env)
    rational_value = run_source("1000 / 3", env)

    capability = make_capability(launcher=refusing_launcher())
    for value in (decimal_value, rational_value):
        request = make_request(
            executable=symbol("unbound_symbol_for_numeric_timeout_test"),
            args=[],
            timeout_ms=value,
        )
        with pytest.raises(TypeError):
            _perform(capability, request)
