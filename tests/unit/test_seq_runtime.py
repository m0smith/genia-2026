import pytest

from genia import values


def test_genia_seq_reusable_source_can_be_consumed_multiple_times():
    seq = values.GeniaSeq.reusable(lambda: iter(["a", "b"]), label="letters")

    assert list(seq.consume()) == ["a", "b"]
    assert list(seq.consume()) == ["a", "b"]


def test_genia_seq_single_use_source_rejects_second_consume_with_flow_error():
    seq = values.GeniaSeq.single_use(lambda: iter([1, 2]), label="numbers")

    assert list(seq.consume()) == [1, 2]
    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        list(seq.consume())


def test_genia_flow_wraps_internal_seq_source_without_changing_public_behavior():
    seq = values.GeniaSeq.single_use(lambda: iter(["x"]), label="numbers")
    flow = values.GeniaFlow(seq)

    assert repr(flow) == "<flow numbers ready>"
    assert list(flow.consume()) == ["x"]
    assert repr(flow) == "<flow numbers consumed>"
    with pytest.raises(RuntimeError, match="Flow has already been consumed"):
        list(flow.consume())


def test_genia_flow_preserves_invalid_seq_source_diagnostic():
    seq = values.GeniaSeq.single_use(lambda: None, label="badflow")
    flow = values.GeniaFlow(seq)

    with pytest.raises(TypeError, match="Flow source badflow did not produce an iterable"):
        list(flow.consume())
