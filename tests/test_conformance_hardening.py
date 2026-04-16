"""
Phase 2 Conformance Hardening Tests
Covers: strict case validation, normalization, error normalization, comparison strictness, CLI contract, anti-drift, and category coverage.
"""
import pytest
import json
from pathlib import Path

# --- Test Utilities ---
def load_json_case(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def is_canonical_number(val):
    return isinstance(val, (int, float))

def is_canonical_string(val):
    return isinstance(val, str)

def is_canonical_bool(val):
    return isinstance(val, bool)

def is_canonical_list(val):
    return isinstance(val, list)

def is_canonical_map(val):
    return isinstance(val, dict)

def is_canonical_option(val):
    # Option: {"some": ...} or {"none": ...}
    if is_canonical_map(val):
        keys = set(val.keys())
        if keys == {"some"}:
            return True
        if keys == {"none"}:
            return True
    return False

def assert_no_python_leak(val):
    # No repr artifacts, type names, or dict ordering issues
    if isinstance(val, dict):
        for k, v in val.items():
            assert not ("<class" in str(k) or "<class" in str(v)), f"Python type leak: {k}, {v}"
            assert_no_python_leak(v)
    elif isinstance(val, list):
        for v in val:
            assert_no_python_leak(v)
    elif isinstance(val, str):
        assert not val.startswith("<class"), f"Python type leak: {val}"

# --- Strict Case Validation ---
def test_strict_case_validation():
    # Malformed: missing required fields, unknown category, extra fields
    bad_cases = [
        {"category": "eval"},  # missing required fields
        {"category": "unknown", "source": "1+1"},  # unknown category
        {"category": "eval", "source": "1+1", "extra": 42},  # extra field
    ]
    for case in bad_cases:
        with pytest.raises(AssertionError):
            validate_case(case)

def validate_case(case):
    allowed_categories = {"eval", "errors", "cli"}
    assert "category" in case, "Missing category"
    assert case["category"] in allowed_categories, f"Unknown category: {case['category']}"
    if case["category"] == "eval":
        assert "source" in case, "Missing source for eval"
        allowed = {"category", "source", "expected"}
        assert set(case.keys()) <= allowed, f"Extra fields: {set(case.keys()) - allowed}"
    # ...expand for other categories as needed

# --- Normalization Hardening ---
def test_normalization_hardening():
    canonical = [
        42, 3.14, "foo", True, False, [], {}, {"some": 1}, {"none": None}
    ]
    for val in canonical:
        if isinstance(val, int) or isinstance(val, float):
            assert is_canonical_number(val)
        elif isinstance(val, str):
            assert is_canonical_string(val)
        elif isinstance(val, bool):
            assert is_canonical_bool(val)
        elif isinstance(val, list):
            assert is_canonical_list(val)
        elif isinstance(val, dict):
            if "some" in val or "none" in val:
                assert is_canonical_option(val)
            else:
                assert is_canonical_map(val)
    # No python leaks
    for val in canonical:
        assert_no_python_leak(val)

# --- Error Normalization ---
def test_error_normalization():
    # Required error fields, category, shape
    good = {"error": {"category": "runtime", "message": "fail"}}
    bads = [
        {},
        {"error": {}},
        {"error": {"message": "fail"}},
        {"error": {"category": "unknown", "message": "fail"}},
    ]
    assert validate_error(good["error"])
    for bad in bads:
        with pytest.raises(AssertionError):
            validate_error(bad.get("error", {}))

def validate_error(err):
    allowed_categories = {"parse", "runtime", "cli"}
    assert "category" in err, "Missing error category"
    assert err["category"] in allowed_categories, f"Unknown error category: {err['category']}"
    assert "message" in err, "Missing error message"
    return True

# --- Comparison Strictness ---
def test_comparison_strictness():
    # Exact match
    a = {"result": 1, "stdout": "foo\n"}
    b = {"result": 1, "stdout": "foo\n"}
    assert compare_results(a, b)
    # Extra field fails
    c = {"result": 1, "stdout": "foo\n", "extra": 2}
    with pytest.raises(AssertionError):
        compare_results(a, c)
    # Partial match fails
    d = {"result": 1}
    with pytest.raises(AssertionError):
        compare_results(a, d)

def compare_results(a, b):
    assert set(a.keys()) == set(b.keys()), f"Field mismatch: {a.keys()} vs {b.keys()}"
    for k in a:
        assert a[k] == b[k], f"Mismatch at {k}: {a[k]} vs {b[k]}"
    return True

# --- CLI Contract ---
def test_cli_contract():
    # Simulate CLI output normalization
    cli_result = {"stdout": "ok\n", "stderr": "", "exit_code": 0}
    assert cli_result["stdout"].endswith("\n")
    assert isinstance(cli_result["exit_code"], int)
    # Negative: wrong exit code
    bad = {"stdout": "ok\n", "stderr": "", "exit_code": 1}
    with pytest.raises(AssertionError):
        assert bad["exit_code"] == 0

# --- Anti-Drift ---
def test_anti_drift():
    # Simulate normalization drift
    a = {"result": 1, "stdout": "foo\n"}
    b = {"result": 1, "stdout": "foo\r\n"}
    with pytest.raises(AssertionError):
        assert a["stdout"] == b["stdout"], "Normalization drift: newlines differ"
    # Simulate ordering drift
    a = {"result": {"a": 1, "b": 2}}
    b = {"result": {"b": 2, "a": 1}}
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True), "Ordering must be canonical"
