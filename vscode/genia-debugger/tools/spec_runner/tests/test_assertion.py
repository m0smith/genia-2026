import pytest
from tools.spec_runner import assertion

# --- Strengthen assertions for normalization and error shape ---
def test_exact_value_match():
    expected = {"Map": [["k", 1]]}
    actual = {"Map": [["k", 1]]}
    assertion.assert_normalized_equal(actual, expected)

def test_value_mismatch():
    expected = {"Map": [["k", 1]]}
    actual = {"Map": [["k", 2]]}
    with pytest.raises(AssertionError):
        assertion.assert_normalized_equal(actual, expected)

def test_error_shape_match():
    expected = {"kind": "ParseError", "category": "syntax", "message": "bad syntax", "location": {"line": 1, "column": 2}}
    actual = {"kind": "ParseError", "category": "syntax", "message": "bad syntax", "location": {"line": 1, "column": 2}}
    assertion.assert_normalized_equal(actual, expected)

def test_error_shape_missing_field():
    expected = {"kind": "ParseError", "category": "syntax", "message": "bad syntax", "location": {"line": 1, "column": 2}}
    actual = {"kind": "ParseError", "category": "syntax", "message": "bad syntax"}
    with pytest.raises(AssertionError):
        assertion.assert_normalized_equal(actual, expected)
