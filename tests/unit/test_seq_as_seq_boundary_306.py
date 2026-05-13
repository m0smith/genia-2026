"""Unit tests for issue #306: explicit Seq-compatible boundary.

These tests verify the internal `_ensure_seq_compatible` boundary helper
that centralizes validation for the sequence helper family.

Contract invariants:
- list is accepted and returned unchanged
- GeniaFlow is accepted without consumption
- All other values raise TypeError with the Seq-compatible diagnostic
- The diagnostic names the helper and both accepted source kinds
"""
from __future__ import annotations

import pytest

from genia import make_global_env
from genia.values import GeniaFlow, GeniaMap  # noqa: F401 (GeniaMap used in test_rejects_map_value)


def _get_ensure_seq_compatible():
    """Obtain the internal _ensure_seq_compatible helper via internal_values."""
    env = make_global_env()
    root = env.root()
    fn = root.internal_values.get("_ensure_seq_compatible")
    assert fn is not None, (
        "_ensure_seq_compatible must be registered via env.set_internal — "
        "implementation missing for issue #306"
    )
    return fn


class TestEnsureSeqCompatibleExists:
    """The centralized boundary helper must exist as an internal builtin."""

    def test_ensure_seq_compatible_is_registered_as_internal(self):
        env = make_global_env()
        root = env.root()
        assert "_ensure_seq_compatible" in root.internal_values, (
            "_ensure_seq_compatible must be registered via env.set_internal"
        )

    def test_ensure_seq_compatible_is_callable(self):
        env = make_global_env()
        root = env.root()
        fn = root.internal_values.get("_ensure_seq_compatible")
        assert callable(fn), "_ensure_seq_compatible must be a callable"

    def test_ensure_seq_compatible_is_not_public(self):
        env = make_global_env()
        # Must not be accessible as a regular public name.
        with pytest.raises(NameError):
            env.get("_ensure_seq_compatible")


class TestEnsureSeqCompatibleAcceptsSeqValues:
    """Accepted source kinds: list and GeniaFlow."""

    def test_accepts_list_and_returns_it_unchanged(self):
        fn = _get_ensure_seq_compatible()
        source = [1, 2, 3]
        result = fn("each", source)
        assert result is source, "list must be returned as-is"

    def test_accepts_empty_list(self):
        fn = _get_ensure_seq_compatible()
        source = []
        result = fn("collect", source)
        assert result is source

    def test_accepts_flow_and_returns_it_unchanged(self):
        fn = _get_ensure_seq_compatible()

        def iterator():
            yield 1
            yield 2

        flow = GeniaFlow(iterator, label="test")
        result = fn("each", flow)
        assert result is flow, "GeniaFlow must be returned as-is"

    def test_accepting_flow_does_not_consume_it(self):
        fn = _get_ensure_seq_compatible()
        consumed = []

        def iterator():
            consumed.append("consumed")
            yield 1

        flow = GeniaFlow(iterator, label="test")
        fn("collect", flow)
        assert consumed == [], "accepting a Flow must not pull any items from it"


class TestEnsureSeqCompatibleRejectsNonSeqValues:
    """Rejected source kinds produce a deterministic Seq-compatible diagnostic."""

    @pytest.mark.parametrize(
        ("value", "expected_type"),
        [
            (42, "int"),
            (3.14, "float"),
            ("abc", "string"),
            (True, "bool"),
            (False, "bool"),
        ],
    )
    def test_rejects_scalar_with_seq_compatible_diagnostic(self, value, expected_type):
        fn = _get_ensure_seq_compatible()
        with pytest.raises(TypeError) as exc_info:
            fn("each", value)
        msg = str(exc_info.value)
        assert "each" in msg
        assert "Seq-compatible" in msg
        assert "list or Flow" in msg
        assert expected_type in msg

    def test_rejects_map_value(self):
        fn = _get_ensure_seq_compatible()
        with pytest.raises(TypeError) as exc_info:
            fn("collect", GeniaMap())
        msg = str(exc_info.value)
        assert "collect" in msg
        assert "Seq-compatible" in msg
        assert "map" in msg

    def test_diagnostic_names_the_caller_helper(self):
        fn = _get_ensure_seq_compatible()
        for helper in ("map", "filter", "take", "drop", "scan", "each", "collect", "run"):
            with pytest.raises(TypeError) as exc_info:
                fn(helper, 99)
            assert helper in str(exc_info.value)

    def test_diagnostic_mentions_both_accepted_kinds(self):
        fn = _get_ensure_seq_compatible()
        with pytest.raises(TypeError) as exc_info:
            fn("run", "bad-value")
        msg = str(exc_info.value)
        assert "list" in msg
        assert "Flow" in msg


class TestEnsureSeqCompatibleBoundaryInvariant:
    """Behavioral invariants that must hold after centralization."""

    def test_list_input_does_not_become_flow(self):
        fn = _get_ensure_seq_compatible()
        source = [1, 2, 3]
        result = fn("map", source)
        assert isinstance(result, list)
        assert not isinstance(result, GeniaFlow)

    def test_flow_input_does_not_become_list(self):
        fn = _get_ensure_seq_compatible()
        flow = GeniaFlow(lambda: iter([1, 2]), label="test")
        result = fn("scan", flow)
        assert isinstance(result, GeniaFlow)
        assert not isinstance(result, list)
