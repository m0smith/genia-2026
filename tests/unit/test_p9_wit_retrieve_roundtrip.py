"""P9 slice B -- real Python-host <-> compiled WIT component round-trip
proof (issue #951).

Scope authority: issue #951,
`docs/design/p9-genia-wit-interoperability-mapping.md` (design),
`docs/design/p9-wit-toolchain-build.md` (slice A build/validation
evidence). This module calls `hosts.python.wit_retrieve_adapter`, which
shells out to a real `wasmtime run --invoke` process against the real
compiled `wit/genia-retrieve-component` artifact -- never a mock or a
simulation of wasm-wave output. Every test in this module either performs
a genuine subprocess call to `wasmtime` or explicitly asserts that no such
call was made (the L2 misuse-rejection tests).

Tests are skipped, not failed, when `wasmtime` or the built component
artifact is unavailable in the running environment (mirroring the
`loopback` marker's environment-conditional pattern already used
elsewhere in this suite) -- this module never fabricates a pass by
mocking around a missing toolchain.
"""

from __future__ import annotations

import shutil

import pytest

from genia.numeric_runtime import GeniaDecimal, rational_from_integers
from genia.values import GeniaMap, GeniaOptionErr, GeniaOptionNone, GeniaOptionSome, GeniaProtected
from hosts.python.wit_retrieve_adapter import (
    IndexRef,
    WitAdapterMisuseError,
    WitComponentFaultError,
    _invoke,
    echo_map,
    echo_outcome,
    echo_score,
    find_component,
    retrieve,
)


def _component_path():
    try:
        return find_component()
    except FileNotFoundError:
        return None


_COMPONENT = _component_path()
_WASMTIME_MISSING = shutil.which("wasmtime") is None

pytestmark = pytest.mark.skipif(
    _COMPONENT is None or _WASMTIME_MISSING,
    reason=(
        "genia:retrieve WIT component or the wasmtime binary is unavailable; "
        "see docs/design/p9-wit-toolchain-build.md to build/install it"
    ),
)


# ---------------------------------------------------------------------------
# Exact numeric round trip -- zero precision loss across all four kinds
# ---------------------------------------------------------------------------


def test_decimal_round_trip_many_digits_zero_precision_loss():
    """A many-digit Decimal survives a real Canonical ABI call unchanged.

    This coefficient/exponent pair would visibly break under any float
    conversion anywhere in the adapter path (a Python float cannot
    represent this many significant digits exactly).
    """

    original = GeniaDecimal(123456789012345678901234567890123456789, -37)
    result = echo_score(_COMPONENT, original)
    assert isinstance(result, GeniaDecimal)
    assert result.coefficient == original.coefficient
    assert result.exponent == original.exponent
    assert result == original


def test_rational_one_third_round_trip_exact():
    """`1/3` survives exactly -- no finite-Decimal or float intermediate.

    R23's own JSON boundary cannot represent 1/3 losslessly; this
    provider boundary explicitly does not inherit that restriction
    (design doc section 1.11), so this is a meaningful proof, not a
    trivial one.
    """

    one_third = rational_from_integers(1, 3)
    result = echo_score(_COMPONENT, one_third)
    assert result == one_third
    assert result.numerator == 1
    assert result.denominator == 3


def test_integer_round_trip_beyond_64_bits():
    """An Integer far outside any fixed-width WIT primitive's range round-trips exactly."""

    original = -(2**200 + 999_999_999_999)
    result = echo_score(_COMPONENT, original)
    assert result == original
    assert isinstance(result, int)


def test_float64_round_trip_exact_bit_pattern():
    """A finite Float64 round-trips exactly (design doc section 1.11: `f64` is direct)."""

    original = 0.1 + 0.2  # a value with no short exact decimal spelling
    result = echo_score(_COMPONENT, original)
    assert isinstance(result, float)
    assert result == original


def test_numeric_exactness_all_four_kinds_in_one_sweep():
    values = [
        7,
        GeniaDecimal(31415926535897932384626433, -25),
        rational_from_integers(22, 7),
        2.718281828459045,
    ]
    for value in values:
        result = echo_score(_COMPONENT, value)
        assert result == value, f"round trip lost exactness for {value!r} -> {result!r}"


# ---------------------------------------------------------------------------
# Ordered Map with R18 key identity, including a non-string key
# ---------------------------------------------------------------------------


def test_ordered_map_round_trip_preserves_order_and_non_string_key():
    original = GeniaMap().put("id", "fixture-1").put(42, "answer-count").put("kind", "evidence")
    result = echo_map(_COMPONENT, original)
    assert isinstance(result, GeniaMap)
    assert result.items() == original.items()
    # Explicitly confirm the non-string (Integer) key survived as an
    # Integer, not coerced into a String.
    assert result.get(42) == "answer-count"


def test_ordered_map_round_trip_rejects_duplicate_key_reconstruction():
    """R18 identity: replacing a key in place must not create a duplicate entry."""

    original = GeniaMap().put(1, "first").put(2, "second").put(1, "first-replaced")
    assert original.count() == 2
    result = echo_map(_COMPONENT, original)
    assert result.count() == 2
    assert result.get(1) == "first-replaced"
    assert result.items() == original.items()


# ---------------------------------------------------------------------------
# All three Outcome cases, end to end through the adapter
# ---------------------------------------------------------------------------


def test_outcome_some_round_trip():
    original = GeniaOptionSome(
        [
            GeniaMap().put("chunk", "alpha").put("score", GeniaDecimal(125, -2)),
            GeniaMap().put("chunk", "beta").put("score", 3),
        ]
    )
    result = echo_outcome(_COMPONENT, original)
    assert isinstance(result, GeniaOptionSome)
    assert len(result.value) == 2
    assert result.value[0].get("chunk") == "alpha"
    assert result.value[0].get("score") == GeniaDecimal(125, -2)
    assert result.value[1].get("chunk") == "beta"
    assert result.value[1].get("score") == 3


def test_outcome_none_round_trip_distinct_reason():
    original = GeniaOptionNone("retrieve-no-results")
    result = echo_outcome(_COMPONENT, original)
    assert isinstance(result, GeniaOptionNone)
    assert result.reason == "retrieve-no-results"
    # None must never be observed as Err or as some(empty list) -- the
    # exact construct kind is preserved, per R18's "never equal across
    # constructor kinds" rule (design doc section 1.4).
    assert not isinstance(result, GeniaOptionErr)


def test_outcome_err_round_trip_with_context():
    original = GeniaOptionErr("retrieve-timeout", GeniaMap().put("timeout_ms", 500).put("kind", "timeout"))
    result = echo_outcome(_COMPONENT, original)
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "retrieve-timeout"
    assert result.context.get("timeout_ms") == 500
    assert result.context.get("kind") == "timeout"


def test_outcome_three_cases_are_never_equal_across_constructor_kinds():
    some_empty = echo_outcome(_COMPONENT, GeniaOptionSome([]))
    none_case = echo_outcome(_COMPONENT, GeniaOptionNone("retrieve-no-results"))
    err_case = echo_outcome(_COMPONENT, GeniaOptionErr("retrieve-rejected"))
    assert isinstance(some_empty, GeniaOptionSome)
    assert isinstance(none_case, GeniaOptionNone)
    assert isinstance(err_case, GeniaOptionErr)
    assert type(some_empty) is not type(none_case)
    assert type(none_case) is not type(err_case)


# ---------------------------------------------------------------------------
# retrieve/4-shaped real call, exercising all three Outcome cases together
# ---------------------------------------------------------------------------


def test_retrieve_real_call_some_none_err():
    index = IndexRef(1, "p9-fixture-space", 3)

    some_result = retrieve(_COMPONENT, [1.0, 0.0, 0.0], 2, index, GeniaMap())
    assert isinstance(some_result, GeniaOptionSome)
    assert len(some_result.value) == 2

    none_result = retrieve(_COMPONENT, [0.0, 0.0, 0.0], 2, index, GeniaMap())
    assert isinstance(none_result, GeniaOptionNone)
    assert none_result.reason == "retrieve-no-results"

    err_result = retrieve(_COMPONENT, [1.0, 0.0, 0.0], 0, index, GeniaMap())
    assert isinstance(err_result, GeniaOptionErr)
    assert err_result.reason == "retrieve-rejected"


# ---------------------------------------------------------------------------
# L2: invalid/local-only value rejected BEFORE any component call
# ---------------------------------------------------------------------------


def test_protected_carrier_rejected_before_any_component_call(monkeypatch):
    """A protected carrier must never cross the WIT boundary (design doc section 1.7).

    This must be rejected purely by the Python-side adapter, before a
    subprocess is ever spawned -- verified here by making `subprocess.run`
    fail loudly if the adapter ever tries to call it.
    """

    import subprocess

    def _fail_if_called(*_args, **_kwargs):
        raise AssertionError("subprocess.run must not be called for a rejected L2 misuse value")

    monkeypatch.setattr(subprocess, "run", _fail_if_called)

    protected = GeniaProtected("top-secret", object(), None)
    with pytest.raises(WitAdapterMisuseError):
        echo_score(_COMPONENT, protected)


def test_non_finite_float_rejected_before_any_component_call(monkeypatch):
    import math
    import subprocess

    def _fail_if_called(*_args, **_kwargs):
        raise AssertionError("subprocess.run must not be called for a rejected L2 misuse value")

    monkeypatch.setattr(subprocess, "run", _fail_if_called)

    with pytest.raises(WitAdapterMisuseError):
        echo_score(_COMPONENT, math.nan)
    with pytest.raises(WitAdapterMisuseError):
        echo_score(_COMPONENT, math.inf)


def test_unsupported_map_key_kind_rejected_before_any_component_call(monkeypatch):
    import subprocess

    def _fail_if_called(*_args, **_kwargs):
        raise AssertionError("subprocess.run must not be called for a rejected L2 misuse value")

    monkeypatch.setattr(subprocess, "run", _fail_if_called)

    illegal_map = GeniaMap().put(True, "bool-key-is-illegal-on-this-narrow-interface")
    with pytest.raises(WitAdapterMisuseError):
        echo_map(_COMPONENT, illegal_map)


# ---------------------------------------------------------------------------
# L3: a real WIT/component-layer failure, distinct from an ordinary
# operation-layer Outcome failure, with no raw process text leaking
# ---------------------------------------------------------------------------


def test_invalid_invocation_raises_normalized_component_fault_not_raw_text():
    with pytest.raises(WitComponentFaultError) as excinfo:
        _invoke(_COMPONENT, "this-export-does-not-exist", ["1"])
    fault = excinfo.value
    assert fault.kind == "invocation-invalid"
    # No raw wasmtime/Wasmtime process text (stderr, backtrace, source
    # file paths) may leak into the normalized diagnostic.
    rendered = str(fault)
    for leaking_marker in ("wasmtime_internal_core", "Stack backtrace", ".rs:", "libc_start"):
        assert leaking_marker not in rendered


def test_ordinary_outcome_err_is_not_a_component_fault():
    """An ordinary L1 `err(...)` Outcome must never be raised as an exception."""

    index = IndexRef(1, "p9-fixture-space", 3)
    result = retrieve(_COMPONENT, [1.0, 0.0, 0.0], 0, index, GeniaMap())
    assert isinstance(result, GeniaOptionErr)
    assert result.reason == "retrieve-rejected"


def test_component_fault_and_ordinary_err_are_distinct_paths():
    """A genuine component-layer failure and an ordinary Outcome err() are
    never observably confused with each other."""

    index = IndexRef(1, "p9-fixture-space", 3)
    ordinary_err = retrieve(_COMPONENT, [1.0, 0.0, 0.0], 0, index, GeniaMap())
    assert isinstance(ordinary_err, GeniaOptionErr)

    with pytest.raises(WitComponentFaultError):
        _invoke(_COMPONENT, "nonexistent-fn", ["1"])
