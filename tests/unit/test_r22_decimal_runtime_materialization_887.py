"""E22-1 (issue #887): exact Decimal runtime materialization.

Covers docs/design/r22-exact-numeric-runtime-contract.md section 2: Decimal
source materializes to a genuine arbitrary-precision GeniaDecimal runtime
value -- coefficient * 10**exponent over two arbitrary-precision ints --
never transiting host binary64, with canonical zero/trailing-zero-stripped
form and Decimal kind preserved even for mathematically integral values.
"""
from __future__ import annotations

import ast
import inspect

from src.genia.numeric_runtime import GeniaDecimal, make_decimal_from_payload
from src.genia.numeric_source import numeric_literal_runtime_value


def _run(src: str):
    from src.genia import make_global_env, run_source

    return run_source(src, make_global_env())


def test_equivalent_decimal_spellings_materialize_identically() -> None:
    """1.0, 1.00, and 10e-1 all denote the same canonical GeniaDecimal."""
    a = _run("1.0")
    b = _run("1.00")
    c = _run("10e-1")
    assert (a.coefficient, a.exponent) == (1, 0)
    assert (b.coefficient, b.exponent) == (1, 0)
    assert (c.coefficient, c.exponent) == (1, 0)
    assert a == b == c


def test_huge_exponent_preserves_exactness() -> None:
    # Coefficient deliberately does not end in "0" so canonicalization
    # leaves both fields untouched, isolating the exponent-magnitude case.
    value = make_decimal_from_payload("123456789012345678901234567891", "500")
    assert value.coefficient == 123456789012345678901234567891
    assert value.exponent == 500


def test_huge_negative_exponent_preserves_exactness() -> None:
    value = make_decimal_from_payload("123456789012345678901234567891", "-500")
    assert value.coefficient == 123456789012345678901234567891
    assert value.exponent == -500


def test_huge_coefficient_preserves_exactness() -> None:
    huge = "1" + "0" * 60 + "1"  # not a power of ten, so it survives canonicalization
    value = make_decimal_from_payload(huge, "0")
    assert value.coefficient == int(huge)
    assert value.exponent == 0


def test_zero_canonicalizes_to_zero_zero() -> None:
    value = make_decimal_from_payload("0", "7")
    assert (value.coefficient, value.exponent) == (0, 0)
    assert value.is_zero()


def test_trailing_zeros_stripped_with_exponent_adjustment() -> None:
    # 1500 * 10**-2 == 15 * 10**0, canonically coefficient=15 exponent=0
    value = make_decimal_from_payload("1500", "-2")
    assert (value.coefficient, value.exponent) == (15, 0)


def test_sign_carried_by_coefficient_no_negative_zero() -> None:
    negated = -make_decimal_from_payload("5", "-1")
    assert negated.coefficient == -5
    assert negated.exponent == -1
    zero = negated + make_decimal_from_payload("5", "-1")
    assert (zero.coefficient, zero.exponent) == (0, 0)


def test_decimal_kind_retained_for_integral_value() -> None:
    """1.0 stays Decimal, distinct in kind from Integer 1, though equal in value."""
    value = _run("1.0")
    assert isinstance(value, GeniaDecimal)
    assert value == 1
    assert type(value) is not int


def test_integer_source_remains_integer() -> None:
    assert type(_run("42")) is int
    assert type(_run("123456789012345678901234567890")) is int


def test_source_materialization_never_uses_host_float() -> None:
    """Decimal materialization must never call float(), even indirectly.

    Scans numeric_source.py and numeric_runtime.py (the whole
    materialization path) for any call to the builtin float().
    """
    import src.genia.numeric_runtime as runtime_module
    import src.genia.numeric_source as source_module

    for module in (source_module, runtime_module):
        tree = ast.parse(inspect.getsource(module))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "float"
        ]
        assert calls == [], f"{module.__name__} must never call float(): {calls}"


def test_runtime_value_decimal_and_integer_shim_replaced() -> None:
    assert numeric_literal_runtime_value({"kind": "integer", "digits": "7"}) == 7
    assert isinstance(numeric_literal_runtime_value({"kind": "integer", "digits": "7"}), int)

    decimal_value = numeric_literal_runtime_value(
        {"kind": "decimal", "coefficient": "7", "exponent": "-1"}
    )
    assert isinstance(decimal_value, GeniaDecimal)
    assert (decimal_value.coefficient, decimal_value.exponent) == (7, -1)
