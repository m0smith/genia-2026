"""Evaluator wiring for exact-numeric ordered comparison (issue #838 step 4).

Proves ``<``/``<=``/``>``/``>=`` are actually routed through
``genia.numeric_values.compare_numeric`` for source-reachable exact-numeric
values (Rational, produced by Integer/Integer division), not merely available
as a pure function. Direct-construction Decimal/Float64 coverage lives in
``tests/unit/test_numeric_equality_comparison.py`` since those types are not
yet reachable from ordinary Genia source (see
``src/genia/numeric_values.py``'s module docstring).

Contract: docs/design/exact-numeric-model-contract.md section 10.1/10.2.
"""

from __future__ import annotations


class TestRationalOrderingFromSource:
    def test_ordering_operators_use_mathematical_value(self, run):
        assert run("1 / 3 < 1 / 2") is True
        assert run("1 / 2 < 1 / 3") is False
        assert run("1 / 3 <= 2 / 6") is True
        assert run("1 / 2 > 1 / 3") is True
        assert run("1 / 3 >= 1 / 2") is False

    def test_integer_vs_rational_ordering_from_source(self, run):
        assert run("1 < (3 / 2)") is True
        assert run("(3 / 2) < 1") is False
        assert run("1 <= (2 / 2)") is True
        assert run("(2 / 2) >= 1") is True

    def test_plain_integer_ordering_is_unaffected(self, run):
        # Guards against a regression where the new dispatch would swallow
        # ordinary Integer/Integer comparisons it does not own.
        assert run("1 < 2") is True
        assert run("2 < 1") is False
        assert run("2 <= 2") is True
        assert run("3 >= 2") is True

    def test_plain_float_ordering_is_unaffected(self, run):
        assert run("1.5 < 2.5") is True
        assert run("2.5 < 1.5") is False


class TestBooleanOperandsAreNumericMisuseInComparison:
    def test_boolean_operand_raises_numeric_misuse(self, run):
        from genia.numeric_values import NumericMisuseError

        for source in ["true < (1 / 3)", "(1 / 3) < true", "false <= (1 / 2)"]:
            try:
                run(source)
            except NumericMisuseError:
                continue
            raise AssertionError(f"expected NumericMisuseError for {source!r}")
