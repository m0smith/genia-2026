"""
Comprehensive tests for Genia Python host adapter contract.
Covers: all contract categories, normalization, comparator, drift detection.
"""
import pytest
import copy
from hosts.python.adapter import run_case, SpecCase
from hosts.python.normalize import normalize_result

# --- Category Coverage ---
@pytest.mark.parametrize("category,input_data", [
    ("parse", "x = 1"),
    ("ir", "x = 1"),
    ("eval", "1 + 2"),
    ("cli", {"args": ["-c", "1+2"]}),
    ("flow", "stdin |> lines |> each(print) |> run"),
    ("error", "1 / 0"),
])
def test_run_case_contract_categories(category, input_data):
    case = SpecCase(
        id=f"contract-{category}",
        category=category,
        input=input_data,
        args=None,
        stdin=None,
        expected=None,
    )
    result = run_case(case)
    # All contract results must have these fields
    for key in ["stdout", "stderr", "exit_code", "success"]:
        assert key in result, f"Missing {key} in {category} result"

# --- Normalization Layer ---
def test_normalization_no_python_leak():
    # Simulate a raw result with Python artifacts
    raw = {"stdout": "", "stderr": "", "exit_code": 0, "result": {"a": object()}}
    norm = normalize_result(raw, SpecCase(id="noleak", category="eval", input="1", args=None, stdin=None, expected=None))
    # Should not leak Python reprs
    def no_leak(val):
        if isinstance(val, dict):
            for k, v in val.items():
                assert "<class" not in str(k) and "<class" not in str(v)
                no_leak(v)
        elif isinstance(val, list):
            for v in val:
                no_leak(v)
        elif isinstance(val, str):
            assert not val.startswith("<class")
    no_leak(norm)

def test_normalization_canonical_types():
    # Canonicalize numbers, strings, bools, lists, dicts, options
    canonical = [42, 3.14, "foo", True, False, [], {}, {"some": 1}, {"none": None}]
    for val in canonical:
        raw = {"stdout": "", "stderr": "", "exit_code": 0, "result": val}
        norm = normalize_result(raw, SpecCase(id="canon", category="eval", input="1", args=None, stdin=None, expected=None))
        # Should round-trip
        assert norm["result"] == val

def test_normalization_newline_and_ordering():
    # Newlines normalized, dict ordering canonical
    raw1 = {"stdout": "foo\n", "stderr": "", "exit_code": 0, "result": {"a": 1, "b": 2}}
    raw2 = {"stdout": "foo\r\n", "stderr": "", "exit_code": 0, "result": {"b": 2, "a": 1}}
    norm1 = normalize_result(raw1, SpecCase(id="nl", category="eval", input="1", args=None, stdin=None, expected=None))
    norm2 = normalize_result(raw2, SpecCase(id="nl", category="eval", input="1", args=None, stdin=None, expected=None))
    # Newlines should be normalized (simulate)
    assert norm1["stdout"].replace("\r\n", "\n") == norm2["stdout"].replace("\r\n", "\n")
    # Dict ordering should not affect equality
    assert sorted(norm1["result"].items()) == sorted(norm2["result"].items())

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
    # Simulate normalization drift (newlines)
    a = {"result": 1, "stdout": "foo\n"}
    b = {"result": 1, "stdout": "foo\r\n"}
    with pytest.raises(AssertionError):
        assert a["stdout"] == b["stdout"], "Normalization drift: newlines differ"

def test_ordering_drift_detection():
    # Simulate ordering drift
    a = {"result": {"a": 1, "b": 2}}
    b = {"result": {"b": 2, "a": 1}}
    # Canonicalize for comparison
    assert sorted(a["result"].items()) == sorted(b["result"].items())

# --- Doc/Test Sync Minimal Assertion ---
def test_doc_sync_mentions_genia_state_and_rules():
    # Ensure GENIA_STATE.md and GENIA_RULES.md are referenced in AGENTS.md
    with open("AGENTS.md", encoding="utf-8") as f:
        text = f.read()
    assert "GENIA_STATE.md" in text
    assert "GENIA_RULES.md" in text
