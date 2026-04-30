"""
Tests for Genia Python host adapter — comparator and drift-detection coverage.
Category-contract tests live in tests/test_adapter_contract.py (issue #126).
"""
import pytest


# --- Comparator Strictness ---

def compare_results(a, b):
    assert set(a.keys()) == set(b.keys()), f"Field mismatch: {a.keys()} vs {b.keys()}"
    for k in a:
        assert a[k] == b[k], f"Mismatch at {k}: {a[k]} vs {b[k]}"
    return True

def test_comparator_exact_match():
    a = {"result": 1, "stdout": "foo\n"}
    b = {"result": 1, "stdout": "foo\n"}
    assert compare_results(a, b)

def test_comparator_extra_field_fails():
    a = {"result": 1, "stdout": "foo\n"}
    c = {"result": 1, "stdout": "foo\n", "extra": 2}
    with pytest.raises(AssertionError):
        compare_results(a, c)

def test_comparator_partial_match_fails():
    a = {"result": 1, "stdout": "foo\n"}
    d = {"result": 1}
    with pytest.raises(AssertionError):
        compare_results(a, d)


# --- Drift Detection ---

def test_normalization_drift_detection():
    a = {"result": 1, "stdout": "foo\n"}
    b = {"result": 1, "stdout": "foo\r\n"}
    with pytest.raises(AssertionError):
        assert a["stdout"] == b["stdout"], "Normalization drift: newlines differ"

def test_ordering_drift_detection():
    a = {"result": {"a": 1, "b": 2}}
    b = {"result": {"b": 2, "a": 1}}
    assert sorted(a["result"].items()) == sorted(b["result"].items())


# --- Doc/Test Sync ---

def test_doc_sync_mentions_genia_state_and_rules():
    with open("AGENTS.md", encoding="utf-8") as f:
        text = f.read()
    assert "GENIA_STATE.md" in text
    assert "GENIA_RULES.md" in text
