"""Existing GREEN construction guarantees for the Python-private E1 seam (#1250).

These are construction regressions, not lifecycle/publication or portability proof.
"""

import pytest

from genia.callable import GeniaClosedFunction
from genia.environment import Env
from tests.unit.model_b_slice_e1_support import record


def test_arity_index_and_record_closure_identity():
    scope = Env()
    records = [record(scope), record(scope, params=("x", "y"))]
    group = GeniaClosedFunction._from_records("f", records)
    assert group.sorted_arities() == [1, 2]
    assert group.is_simple
    assert group.get(1) is records[0] and group.get(2) is records[1]
    assert all(actual is expected for actual, expected in zip(group.records, records))
    assert all(actual.closure is scope for actual in group.records)
    assert scope.values == {}  # private construction publishes no binding


def test_one_shot_iterable_is_consumed_once():
    scope = Env()
    records = [record(scope), record(scope, params=("x", "y"))]
    seen = []

    def once():
        """Record each yield while supplying a one-shot generator to production."""
        for item in records:
            seen.append(item)
            yield item

    source = once()
    group = GeniaClosedFunction._from_records("f", source)
    assert len(seen) == 2 and all(a is b for a, b in zip(seen, records))
    assert list(source) == []
    assert group.get(1) is records[0] and group.get(2) is records[1]


def test_independent_containers_preserve_shared_records():
    scope = Env()
    records = [record(scope)]
    first = GeniaClosedFunction._from_records("f", records)
    second = GeniaClosedFunction._from_records("f", records)
    assert first is not second
    assert first.records is not second.records and first.records is not records
    assert first.functions is not second.functions
    records.append(record(scope, params=("x", "y")))
    assert len(first.records) == len(second.records) == 1
    assert first.get(1) is second.get(1) is records[0]


def test_duplicate_clause_rejection_reuses_existing_diagnostic():
    scope = Env()
    with pytest.raises(TypeError, match="^Duplicate function definition: f/1$"):
        GeniaClosedFunction._from_records("f", [record(scope), record(scope)])


@pytest.mark.parametrize("kind", ["list", "generator"])
def test_empty_input_is_rejected(kind):
    source = [] if kind == "list" else iter(())
    with pytest.raises(ValueError, match="^closed group requires at least one record$"):
        GeniaClosedFunction._from_records("f", source)


@pytest.mark.parametrize("invalid", [None, 1, "not-a-record"])
def test_invalid_record_element_is_rejected(invalid):
    with pytest.raises(TypeError, match="^closed group requires GeniaFunction records$"):
        GeniaClosedFunction._from_records("f", [record(Env()), invalid])
